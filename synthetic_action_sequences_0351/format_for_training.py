"""
format_for_training.py

Converts synthetic action sequence JSONL datasets (train/val/test) into
a standard chat format (OpenAI Messages) for LLM fine-tuning.

Output format per line:
{
  "messages": [
    {"role": "system", "content": "<system_prompt>"},
    {"role": "user", "content": "<NL task description>"},
    {"role": "assistant", "content": "<structured JSON action sequence>"}
  ]
}

Usage:
    python3 format_for_training.py \
        --input-train dataset_train.jsonl \
        --input-val dataset_val.jsonl \
        --input-test dataset_test.jsonl \
        --output-dir ./
"""

import json
import os
import sys
import argparse
from datetime import datetime

# ──────────────────────────────────────────────
# System Prompt
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are an autonomous infrastructure orchestration agent. Your job is to translate natural language task descriptions into precise, executable JSON action sequences.

## Core Principles

1. **Proactive orchestration** — Break down the user's request into a complete, ordered sequence of API actions. Each action must be explicit and independently verifiable. Do not leave steps implicit or assume the user will fill gaps.

2. **Variable tracking** — When one step produces a value (e.g., an instance ID, a bucket name, a security group ID) that a subsequent step needs, pass it explicitly via `{{steps[N].output.key}}` references. Every such dependency must be recorded in the `variable_chain` array, showing the source step, the target step, the specific key, and the resolved value.

3. **Rollback planning** — Any action that creates or modifies infrastructure must have a compensating rollback action (e.g., CreateInstance → TerminateInstance, CreateBucket → DeleteBucket). Rollback steps are separate actions with `"condition": "on_failure"` and a `triggers_from` field pointing to the step they protect. Rollbacks must depend on the same preconditions as their paired forward step.

4. **Dependency resolution** — The `depends_on` array for each action must list every step it directly depends on. Chain dependencies correctly: if step 3 depends on step 2, and step 2 depends on step 1, step 3 only lists `[2]` (not `[1, 2]`), unless it also references step 1's outputs directly.

5. **Output references** — Every action that produces a value used elsewhere must declare it in `output_refs`. Each ref includes a realistic placeholder value (e.g., an ARN, UUID, IP address).

## Output Format

Produce a JSON object with these top-level keys:
- `actions`: Array of action objects, each with `step` (1-indexed), `namespace`, `function`, `params`, `depends_on`, `output_refs`, and optionally `rollback_ref` / `condition` / `triggers_from`
- `dependencies`: Array of `{from, to}` edge objects (flat representation of the dependency graph)
- `variable_chain`: Array of `{from_step, from_key, from_value, to_step, to_param, to_value}` objects
- `complexity`: Object with `score` (integer), `level` ("simple"|"medium"|"complex"), and `factors` (breakdown)
- `sector`: The operational sector this sequence belongs to
- `domain`: The top-level domain

## Constraints

- Step numbers are 1-indexed and sequential.
- Rollback steps are included in the actions array with their own step numbers.
- Every rollback step must have `"condition": "on_failure"` and `"triggers_from": [<original_step>]`.
- If a step has no dependencies, use `"depends_on": []`.
- Variable references in params use the `{{steps[N].output.key}}` syntax verbatim — do NOT resolve them to concrete values inside the params dict. The resolved value is recorded in the `variable_chain` instead.
- The `dependencies` array must include both regular dependency edges and rollback-trigger edges (with `"type": "rollback_trigger"`).
- Complexity score reflects the total number of steps, dependency edges, rollback actions, and variable passing links combined."""

# ──────────────────────────────────────────────
# Conversion Logic
# ──────────────────────────────────────────────

def format_output_json(record: dict) -> str:
    """
    Convert a record's output dict into a clean, deterministic JSON string.
    Uses a fixed sort order for keys and compact-but-readable formatting.
    """
    output = record["output"]

    # Build a cleaned copy in deterministic key order
    formatted = {
        "actions": output["actions"],
        "dependencies": output.get("dependencies", []),
        "variable_chain": output.get("variable_chain", []),
        "complexity": output.get("complexity", {}),
    }

    if "sector" in output:
        formatted["sector"] = output["sector"]
    if "domain" in output:
        formatted["domain"] = output["domain"]

    return json.dumps(formatted, indent=2, ensure_ascii=False)


def convert_record(record: dict, system_prompt: str = SYSTEM_PROMPT) -> dict:
    """
    Convert a single {input, output} record into the OpenAI Messages format.
    """
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": record["input"]},
            {"role": "assistant", "content": format_output_json(record)},
        ]
    }


def convert_file(
    input_path: str,
    output_path: str,
    system_prompt: str = SYSTEM_PROMPT,
) -> int:
    """
    Convert an entire JSONL file from {input, output} format to OpenAI Messages format.
    Returns the number of records converted.
    """
    count = 0
    with open(input_path, "r") as fin, open(output_path, "w") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            chat_record = convert_record(record, system_prompt)
            fout.write(json.dumps(chat_record, ensure_ascii=False) + "\n")
            count += 1
    return count


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert synthetic action sequence datasets to chat format for LLM fine-tuning."
    )
    parser.add_argument(
        "--input-train",
        default="dataset_train.jsonl",
        help="Path to the training JSONL file (input/output format).",
    )
    parser.add_argument(
        "--input-val",
        default="dataset_val.jsonl",
        help="Path to the validation JSONL file.",
    )
    parser.add_argument(
        "--input-test",
        default="dataset_test.jsonl",
        help="Path to the test JSONL file.",
    )
    parser.add_argument(
        "--output-dir",
        default="./",
        help="Directory to write the output chat-format JSONL files.",
    )
    parser.add_argument(
        "--train-prefix",
        default="chat_train",
        help="Output filename prefix for training set (e.g. 'chat_train' → chat_train.jsonl).",
    )
    parser.add_argument(
        "--val-prefix",
        default="chat_val",
        help="Output filename prefix for validation set.",
    )
    parser.add_argument(
        "--test-prefix",
        default="chat_test",
        help="Output filename prefix for test set.",
    )
    parser.add_argument(
        "--system-prompt",
        default=None,
        help="Optional custom system prompt file path (plain text). Overrides the default.",
    )
    args = parser.parse_args()

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Load custom system prompt if provided
    system_prompt = SYSTEM_PROMPT
    if args.system_prompt:
        with open(args.system_prompt, "r") as f:
            system_prompt = f.read().strip()

    # Verify input files exist
    for path, label in [
        (args.input_train, "train"),
        (args.input_val, "val"),
        (args.input_test, "test"),
    ]:
        if not os.path.exists(path):
            print(f"❌ {label} input not found: {path}")
            sys.exit(1)

    # Convert
    pairs = [
        (args.input_train, os.path.join(output_dir, f"{args.train_prefix}.jsonl"), "train"),
        (args.input_val, os.path.join(output_dir, f"{args.val_prefix}.jsonl"), "val"),
        (args.input_test, os.path.join(output_dir, f"{args.test_prefix}.jsonl"), "test"),
    ]

    total = 0
    for input_path, output_path, label in pairs:
        count = convert_file(input_path, output_path, system_prompt)
        total += count
        print(f"  {label:5s}  {input_path}  →  {output_path}  ({count} records)")

    print(f"\n✅ Converted {total} total records to chat format.")

    # Summary stats
    print(f"\nDataset sizes after conversion:")
    for _, output_path, label in pairs:
        with open(output_path) as f:
            n = sum(1 for _ in f)
        print(f"  {label:5s}  {output_path}  ({n} records)")

    print(f"\nSystem prompt length: {len(system_prompt)} characters")


if __name__ == "__main__":
    main()