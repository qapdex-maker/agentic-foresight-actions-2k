---
license: apache-2.0
task_categories:
- text-generation
- robotics
language:
- en
tags:
- agent
- agentic-foresight
- task-automation
- json-actions
- rollback-mechanisms
- multi-step-planning
size_categories:
- 1K<n<10K
---

# Agentic Foresight: 2K Multi-Step JSON Action & Rollback Dataset

## Dataset Description
This dataset contains **2,000 highly structured, synthetically generated input/output pairs** explicitly designed to train Large Language Models in **Agentic Foresight, Multi-Step Orchestration, and Sequential Task Automation**. 

Unlike standard tool-calling datasets that map a single prompt to a single API call, this dataset forces the model to act as a macro-orchestrator. It translates complex, abstract natural language goals into complete, execution-safe JSON action graphs.

### Key Features
- **Hierarchical Tool Decomposition:** Every natural language task is broken down into a multi-step sequence containing 3 to 12 precise execution blocks.
- **Complex Dependency Tracking (`depends_on_steps`):** Steps explicitly reference the results of previous actions, mapping dynamic execution pipelines without forward-reference paradoxes.
- **State-Aware Variable Passing:** Features an explicit `variable_chain` schema allowing steps to dynamically consume upstream payloads (e.g., `{{step_1.output.instance_id}}`).
- **Native Rollback & Compensating Actions:** 25% of the entire dataset features explicitly paired mitigation workflows (e.g., if a database creation fails at Step 3, the agent predicts immediate rollback functions like deleting temporary security groups created in Step 1).
- **Proactive Verification Gates:** Includes pre-checks and secondary post-verification checkpoints to teach models how to evaluate environmental state shifts *before* executing catastrophic actions.

---

## Dataset Structure

The dataset is partitioned into three distinct splits (80/10/10) following standard machine learning practices:
- `chat_train.jsonl` (1,600 records)
- `chat_val.jsonl` (200 records)
- `chat_test.jsonl` (200 records)

### Data Format
The files are pre-formatted using the universal **OpenAI Messages Format**, making them plug-and-play compatible with modern fine-tuning frameworks like **Axolotl, Hugging Face TRL, Unsloth, or Kaggle Notebooks**.

### JSON Schema Example
Each assistant turn features a strict JSON configuration optimized for zero dangling references:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "[Structured Agentic Foresight System Prompt...]"
    },
    {
      "role": "user",
      "content": "Deploy an updated frontend microservice build to our staging VPC, verify live status, and notify the team on Slack. If validation fails, tear down the build immediately."
    },
    {
      "role": "assistant",
      "content": "{\n  \"actions\": [...],\n  \"dependencies\": [...],\n  \"variable_chain\": {...}\n}"
    }
  ]
}
```

---

## Domain & Sector Coverage
The dataset spans **30 distinct sub-sectors** across 5 primary operational industries to guarantee absolute vocabulary and semantic robustness:
1. **Enterprise Operations & SaaS Orchestration** (DevOps pipelines, HR onboarding workflows, security patching).
2. **Financial Services & Legal Tech** (AML compliance, multi-currency invoicing, portfolio rebalancing).
3. **E-Commerce, Logistics & Supply Chain** (Inventory tracking, fleet monitoring, dynamic retail pricing).
4. **Healthcare & Bio-Informatics** (EMR synchronization, medical telemetry escalation, lab tracking).
5. **Smart Infrastructure & Hospitality** (HVAC energy optimization, automated guest turnaround, industrial maintenance).

## Intended Use & Fine-Tuning
This data was generated to bring advanced macro-planning capabilities to highly capable small open-source models (such as **Mistral-7B** or **Llama-3-8B**) without requiring expensive closed-source proprietary APIs. It is perfectly optimized for Parameter-Efficient Fine-Tuning (PEFT/LoRA) using loss-masking focused solely on the assistant's structured outputs.

## License
This dataset is published under the **Apache 2.0 License** and is completely free for academic, research, and commercial use. 

---
*Dataset compiled and contributed by [kun1gund3 / heyneo.com]. Powered by programmatic template architecture and deterministic multi-layered validation.*
