# Complex Template Expansion — 500 Highly Complex Records

## Goal
Create `complex_template_expansion.py` containing ~45 templates with 5–10+ steps each (across all 30 sectors), generate 500 records from them, then proportionally merge into existing train/val/test splits while preserving the 80/10/10 ratio.

## Research Summary
- `sequence_generator.py`'s `build_sequence()` handles any template with actions, `rollback_ref`, and `{{steps[N].output.<key>}}` patterns — it scales naturally to 8+ action steps
- `nl_generator.py`'s `generate_nl(template_str, params, rng)` handles NL generation for any template string with `{placeholders}`
- Complexity threshold for "complex" = step_count > 6 → score > 60 → level = "complex"
- Each 7+ step template with ≥3 rollback_refs and ≥4 variable passing hops automatically yields `level: "complex"`
- Available API functions: 95 across 5 domains with 33 rollback pairs
- The new script must import from `sequence_generator` and `nl_generator` (which import from `api_functions`)

## Approach
1. Write `complex_template_expansion.py` with ~45 complex templates (1-2 per sector), covering all 5 domains and 30 sectors
2. Each template: 5–10+ steps, ≥3 rollback_ref entries, ≥4 variable passing (`{{steps[].output.}}`) references
3. Templates use 3 expansion patterns:
   - **Prerequisite-chain** (small infra first → main service → monitoring → lifecycle)
   - **Deep pipeline** (create → verify → secondary ops → alerting → post-cleanup)
   - **Multi-level rollback** (3+ write ops with compensating actions at each stage)
4. Generation script: iterate templates, call `build_sequence_safe(t, rng, max_retries=20)`, generate NL via `generate_nl()`, validate, collect 500 records
5. Merge: add 400 → train, 50 → val, 50 → test (to maintain 80/10/10 of 2000 total)
6. Shuffle and validate final splits

## Subtasks
1. Create `complex_template_expansion.py` with ~45 complex templates (5–10+ steps each) across all 30 sectors, using only existing api_functions.py functions. Verify templates pass `_validate_variable_refs()`.
2. Add a `generate_complex_dataset()` function to the script that iterates all complex templates, runs `build_sequence_safe(t, rng, 20)`, generates NL, validates, and writes 500 records to `dataset_complex_500.jsonl`. Print generation stats.
3. Run the generation and verify ~500 highly complex records produced (complexity level="complex", 7+ steps, 3+ rollbacks, 4+ variable chains). Show 2 example records.
4. Write merge script that: reads existing train/val/test splits, reads complex_500, appends 400→train, 50→val, 50→test (shuffle appended portion with fresh seed). Verify counts: train=1600, val=200, test=200.
5. Final validation: run dataset_audit on all 3 merged splits (check dangling refs, rollback coverage, variable passing). Print final complexity distribution summary across all 2000 records.

## Deliverables
| File Path | Description |
|-----------|-------------|
| `/app/synthetic_action_sequences_0351/complex_template_expansion.py` | Script with ~45 complex templates + generation function |
| `/app/synthetic_action_sequences_0351/dataset_complex_500.jsonl` | 500 generated complex records |
| `/app/synthetic_action_sequences_0351/dataset_train.jsonl` | Updated: 1600 records (1200 original + 400 complex) |
| `/app/synthetic_action_sequences_0351/dataset_val.jsonl` | Updated: 200 records (150 original + 50 complex) |
| `/app/synthetic_action_sequences_0351/dataset_test.jsonl` | Updated: 200 records (150 original + 50 complex) |

## Evaluation Criteria
- `dataset_complex_500.jsonl` has exactly 500 records, all with complexity level = "complex"
- Every record has 7+ action steps, ≥3 rollback_ref entries, ≥4 variable passing patterns
- No dangling variable references (audit PASS)
- Final splits: train=1600, val=200, test=200 (2000 total, 80/10/10)
- Complexity distribution across all 2000 records shows significant complex proportion

## Notes
- Templates must use EXISTING api_functions.py functions only — no new API functions
- `rollback_ref` format: `{"namespace": "X", "function": "Y"}` — picks the rollback params from the API function definition
- Variable passing syntax: `{{steps[N].output.<key>}}` where N is 1-indexed and key exists in step N's `output_refs`
- After merge, do a final shuffled shuffle on each split to interleave complex with original records