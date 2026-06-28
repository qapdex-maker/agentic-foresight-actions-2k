"""
train_lora.py

Standalone LoRA fine-tuning script using Hugging Face Transformers + PEFT.
Compatible with the Axolotl config above, but designed to run directly via:

    torchrun --nproc_per_node=1 train_lora.py

(allows easy debugging, modification, or integration into custom pipelines)

Requires:
    pip install transformers peft accelerate bitsandbytes datasets trl

Key design decisions:
  - Uses SFTTrainer from TRL (same trainer Axolotl uses internally)
  - Loads data from pre-formatted chat JSONL files (OpenAI Messages format)
  - Applies chat template via tokenizer.apply_chat_template()
  - Loss-masks user/system turns so training only happens on assistant tokens
  - Configures LoRA with r=32, alpha=16 targeting all linear layers
  - Sets sequence length to 8192 (headroom for long JSON action chains)
  - Saves merged adapter + tokenizer in the final output directory
"""

import json
import os
import sys
import argparse
from typing import Dict, List, Optional
from dataclasses import dataclass

import torch
from datasets import Dataset, load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    HfArgumentParser,
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    PeftModel,
)
from trl import SFTTrainer, DataCollatorForCompletionOnlyLM

# ───────────────────────────────────────────────────────
# Configuration
# ───────────────────────────────────────────────────────

@dataclass
class TrainConfig:
    """Training configuration — passed via CLI args or defaults."""
    # Model
    model_name: str = "NousResearch/Meta-Llama-3-8B-Instruct"
    output_dir: str = "./outputs/lora-out"
    
    # Data
    train_file: str = "chat_train.jsonl"
    val_file: str = "chat_val.jsonl"
    test_file: str = "chat_test.jsonl"
    
    # Sequence length
    max_seq_length: int = 8192
    
    # LoRA
    lora_r: int = 32
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    lora_target_modules: str = "all-linear"  # targets q,k,v,o,gate,up,down
    
    # Training
    per_device_train_batch_size: int = 2
    per_device_eval_batch_size: int = 2
    gradient_accumulation_steps: int = 4
    num_epochs: int = 3
    learning_rate: float = 2e-4
    warmup_ratio: float = 0.1
    weight_decay: float = 0.0
    max_grad_norm: float = 1.0
    lr_scheduler: str = "cosine"
    
    # Mixed precision
    bf16: bool = True
    tf32: bool = True
    
    # Memory
    gradient_checkpointing: bool = True
    load_in_8bit: bool = True
    
    # Eval & logging
    eval_steps: int = 100
    logging_steps: int = 10
    save_steps: int = 500
    save_total_limit: int = 2
    
    # Seed
    seed: int = 42


def parse_args() -> TrainConfig:
    """Parse CLI overrides with simple --key=value syntax."""
    config = TrainConfig()
    overrides = {}
    for arg in sys.argv[1:]:
        if arg.startswith("--"):
            key, _, val = arg.lstrip("--").partition("=")
            overrides[key] = val
    for key, val in overrides.items():
        if hasattr(config, key):
            typed_val = type(getattr(config, key))(val)
            setattr(config, key, typed_val)
    return config


# ───────────────────────────────────────────────────────
# Data Loading & Formatting
# ───────────────────────────────────────────────────────

def load_chat_jsonl(path: str) -> Dataset:
    """Load OpenAI Messages format JSONL into a HuggingFace Dataset."""
    records = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    
    # The dataset has {"messages": [...]} per row
    messages_list = [r["messages"] for r in records]
    dataset = Dataset.from_dict({"messages": messages_list})
    return dataset


def format_chat_template(example: Dict, tokenizer) -> Dict:
    """
    Convert OpenAI Messages format into tokenized inputs.
    We use apply_chat_template with add_generation_prompt=False and
    tokenize=True so user turns get loss-masked automatically by
    the SFTTrainer's DataCollatorForCompletionOnlyLM.
    
    Returns tokenized inputs.
    """
    # We return formatted text; the trainer handles tokenization internally.
    # SFTTrainer already knows how to handle 'messages' field with chat_template.
    return example


# ───────────────────────────────────────────────────────
# Model Setup
# ───────────────────────────────────────────────────────

def setup_model_and_tokenizer(config: TrainConfig):
    """Load base model with quantization and prepare for LoRA."""
    
    # BitsAndBytes config for 8-bit loading
    bnb_config = None
    if config.load_in_8bit:
        bnb_config = BitsAndBytesConfig(load_in_8bit=True)
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        config.model_name,
        trust_remote_code=False,
        use_fast=True,
    )
    
    # Set pad token — Llama 3 uses <|end_of_text|> as pad
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        config.model_name,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16 if config.bf16 else torch.float16,
        attn_implementation="flash_attention_2",
        trust_remote_code=False,
    )
    
    # Prepare for k-bit training
    model = prepare_model_for_kbit_training(model)
    
    # Enable gradient checkpointing
    if config.gradient_checkpointing:
        model.config.use_cache = False
        model.gradient_checkpointing_enable()
    
    # Configure LoRA
    peft_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=config.lora_target_modules,
        bias="none",
        task_type="CAUSAL_LM",
    )
    
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()
    
    return model, tokenizer


# ───────────────────────────────────────────────────────
# Response Template for Loss Masking
# ───────────────────────────────────────────────────────

def setup_response_template(tokenizer):
    """
    Create a response template for DataCollatorForCompletionOnlyLM.
    This ensures loss is only computed on assistant responses, not user/system prompts.
    
    We need to find the assistant header token sequence in the tokenized chat template.
    For llama3 chat template, the assistant turn starts with:
        <|start_header_id|>assistant<|end_header_id|>
    
    But since the exact tokenization depends on the tokenizer, we use
    the SFTTrainer's built-in formatting_func + response_template.
    """
    # The tokenized version of "<|start_header_id|>assistant<|end_header_id|>\n\n"
    response_template = tokenizer.encode(
        "<|start_header_id|>assistant<|end_header_id|>\n\n",
        add_special_tokens=False,
    )
    return response_template


# ───────────────────────────────────────────────────────
# Main Training Loop
# ───────────────────────────────────────────────────────

def main():
    config = parse_args()
    
    print("=" * 60)
    print("ACTION SEQUENCE LoRA FINE-TUNING")
    print("=" * 60)
    print(f"Model: {config.model_name}")
    print(f"LoRA: r={config.lora_r}, alpha={config.lora_alpha}")
    print(f"Sequence length: {config.max_seq_length}")
    print(f"Effective batch size: {config.per_device_train_batch_size * config.gradient_accumulation_steps}")
    print(f"Epochs: {config.num_epochs}")
    print()
    
    # Load datasets
    print("[1/5] Loading datasets...")
    train_dataset = load_chat_jsonl(config.train_file)
    val_dataset = load_chat_jsonl(config.val_file)
    print(f"  Train: {len(train_dataset)} records")
    print(f"  Val:   {len(val_dataset)} records")
    
    # Setup model
    print("[2/5] Loading model + tokenizer...")
    model, tokenizer = setup_model_and_tokenizer(config)
    
    # Setup response template for loss masking
    # This tells the trainer: only compute loss on tokens AFTER the assistant header
    response_template = setup_response_template(tokenizer)
    collator = DataCollatorForCompletionOnlyLM(
        response_template=response_template,
        tokenizer=tokenizer,
    )
    
    # Training args
    print("[3/5] Configuring training...")
    training_args = TrainingArguments(
        output_dir=config.output_dir,
        per_device_train_batch_size=config.per_device_train_batch_size,
        per_device_eval_batch_size=config.per_device_eval_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        num_train_epochs=config.num_epochs,
        learning_rate=config.learning_rate,
        warmup_ratio=config.warmup_ratio,
        weight_decay=config.weight_decay,
        max_grad_norm=config.max_grad_norm,
        lr_scheduler_type=config.lr_scheduler,
        logging_steps=config.logging_steps,
        eval_steps=config.eval_steps,
        save_steps=config.save_steps,
        save_total_limit=config.save_total_limit,
        eval_strategy="steps",
        bf16=config.bf16,
        tf32=config.tf32,
        gradient_checkpointing=config.gradient_checkpointing,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        ddp_find_unused_parameters=False,
        report_to="none",
        seed=config.seed,
        dataloader_num_workers=2,
        remove_unused_columns=False,
    )
    
    # Trainer
    print("[4/5] Initializing SFTTrainer...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=collator,
        max_seq_length=config.max_seq_length,
        dataset_text_field="messages",
        packing=False,
    )
    
    # Train
    print("[5/5] Starting training...")
    print()
    trainer.train()
    
    # Save
    print("\nSaving final adapter...")
    trainer.save_model(config.output_dir)
    tokenizer.save_pretrained(config.output_dir)
    
    print(f"\n✅ Training complete! Adapter saved to: {config.output_dir}")
    print("\nTo merge and export for inference:")
    print(f"  python merge_lora.py --base-model={config.model_name} --adapter={config.output_dir} --output=./merged_model")
    
    # Final eval
    print("\nFinal validation metrics:")
    eval_results = trainer.evaluate()
    for key, val in eval_results.items():
        print(f"  {key}: {val:.4f}")


if __name__ == "__main__":
    main()