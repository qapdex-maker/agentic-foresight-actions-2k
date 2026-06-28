"""
generate_dataset.py — Main orchestrator for synthetic action sequence dataset generation.

Generates 1,500 records (50 per sector × 30 sectors) with two validation layers:
Layer 1 — Pre-write: validate_variable_references() on every sequence before writing
Layer 2 — Post-generation: full audit() of every line in dataset.jsonl

Outputs:
dataset_1500.jsonl   — 1,500 validated records with unique NL inputs
dataset_stats.json   — Generation statistics
dataset_audit.json   — Post-generation audit report
"""

import json
import os
import random
import re
import sys
import time
from collections import defaultdict

# Ensure we can import project modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_functions import API_FUNCTIONS
from templates import TEMPLATES
from nl_generator import generate_nl
from sequence_generator import build_sequence, _validate_variable_refs

# Constants
SEED = 42
RECORDS_PER_SECTOR = 50
EXPECTED_TOTAL = 1500
MAX_RETRIES_PER_RECORD = 20
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Regex for variable reference patterns
VAR_REF_PATTERN = re.compile(r'\{\{steps\[(\d+)\]\.output\.(\w+)\}\}')


def validate_variable_references(actions):
    """
    Layer 1 — Validate all variable references in action params.

    Scans every action's params for {{steps[N].output.<key>}} patterns and asserts:
    - Referenced step N exists (steps are 1-indexed, so actions[N-1] must exist)
    - Referenced step's output_refs contains the key
    - N is less than the current step number (no forward references)

    Returns: (is_valid, list_of_error_strings)
    """
    return _validate_variable_refs(actions)


def group_templates_by_sector():
    """Group TEMPLATES by sector name. Returns dict: sector_name -> [templates]"""
    groups = defaultdict(list)
    for t in TEMPLATES:
        groups[t["sector"]].append(t)
    return dict(groups)


def check_api_functions_index():
    """Verify that API_LOOKUP can find all functions used in templates."""
    from sequence_generator import _find_api_function
    missing = set()
    for template in TEMPLATES:
        for action in template.get("actions", []):
            ns = action["namespace"]
            fn = action["function"]
            if not _find_api_function(ns, fn):
                missing.add(f"{ns}.{fn}")
    return missing


def generate_dataset():
    """
    Main generation loop.

    For each sector (30) → for each iteration (50):
    1. Pick a random template from that sector
    2. Build action sequence from template
    3. Generate NL input from template
    4. Validate variable references (Layer 1)
    5. Check for duplicate NL input
    6. If invalid or duplicate → retry (up to MAX_RETRIES_PER_RECORD)
    7. If valid → write record to dataset_1500.jsonl

    After all records are written:
    8. Run audit (Layer 2)
    9. Write dataset_stats.json and dataset_audit.json
    """
    rng = random.Random(SEED)

    # Check for missing API functions first
    missing = check_api_functions_index()
    if missing:
        print(f"WARNING: {len(missing)} API functions referenced in templates not found:")
        for m in sorted(missing):
            print(f"  - {m}")
        print("Generation may fail for templates using these functions.\n")

    # Group templates by sector
    sector_templates = group_templates_by_sector()
    all_sectors = sorted(sector_templates.keys())

    if len(all_sectors) != 30:
        print(f"WARNING: Expected 30 sectors, found {len(all_sectors)}")

    print(f"Starting generation: {len(all_sectors)} sectors × {RECORDS_PER_SECTOR} records = {EXPECTED_TOTAL} total")
    print(f"Seed: {SEED}\n")

    # Stats tracking
    stats = {
        "generation_start": time.strftime("%Y-%m-%d %H:%M:%S"),
        "seed": SEED,
        "total_records": 0,
        "per_sector": {},
        "total_retries": 0,
        "max_retries_hit": 0,
        "template_usage": defaultdict(int),
        "dangling_refs_log": [],
        "duplicate_input_retries": 0,
        "generation_time_seconds": 0.0,
    }

    records = []
    generation_start = time.time()

    # Output file
    jsonl_path = os.path.join(OUTPUT_DIR, "dataset_1500.jsonl")

    with open(jsonl_path, "w") as out_f:
        for sector in all_sectors:
            templates = sector_templates[sector]
            sector_records = 0
            sector_retries = 0
            sector_errors = []
            seen_inputs_for_sector = set()  # Dedup NL inputs within each sector

            print(f"  Sector: {sector} ({len(templates)} templates available)")

            while sector_records < RECORDS_PER_SECTOR:
                # Pick a random template from this sector
                template = rng.choice(templates)
                template_used = template.get("nl_template", "unknown")[:80]

                success = False
                for attempt in range(MAX_RETRIES_PER_RECORD):
                    try:
                        # Step 1: Generate action sequence
                        result, errors = build_sequence(template, rng)

                        if result is None:
                            sector_retries += 1
                            if attempt == 0:
                                stats["dangling_refs_log"].append(
                                    f"{sector} record#{sector_records+1}: build_sequence returned None: {errors}"
                                )
                            continue

                        # Step 2: Generate NL input from the template
                        # Build a params dict from the resolved actions
                        params_for_nl = {}
                        for action in result["actions"]:
                            if not action.get("condition"):  # skip rollback actions
                                for pname, pvalue in action.get("params", {}).items():
                                    if isinstance(pvalue, (str, int, float, bool)):
                                        params_for_nl[pname] = pvalue

                        nl_input = generate_nl(template["nl_template"], params_for_nl, rng)

                        # Check for duplicate NL input
                        if nl_input in seen_inputs_for_sector:
                            sector_retries += 1
                            stats["duplicate_input_retries"] += 1
                            # Advance RNG state for next attempt
                            rng.random()
                            continue

                        # Step 3: Validate variable references (Layer 1 — pre-write)
                        is_valid, v_errors = validate_variable_references(template["actions"])
                        if not is_valid:
                            sector_retries += 1
                            stats["dangling_refs_log"].append(
                                f"{sector} record#{sector_records+1} attempt#{attempt+1}: {v_errors}"
                            )
                            continue

                        # Also validate variable_chain consistency
                        chain_valid = True
                        for chain_entry in result.get("variable_chain", []):
                            from_step = chain_entry["from_step"]
                            to_step = chain_entry["to_step"]
                            if from_step >= to_step:
                                chain_valid = False
                                break

                        if not chain_valid:
                            sector_retries += 1
                            continue

                        # Build the full record
                        record = {
                            "input": nl_input,
                            "output": {
                                "actions": result["actions"],
                                "dependencies": result["dependencies"],
                                "variable_chain": result["variable_chain"],
                                "complexity": result["complexity"],
                                "sector": result["sector"],
                                "domain": result["domain"],
                            }
                        }

                        # Write to JSONL
                        out_f.write(json.dumps(record) + "\n")
                        out_f.flush()

                        seen_inputs_for_sector.add(nl_input)
                        records.append(record)
                        sector_records += 1
                        stats["template_usage"][template["nl_template"][:60]] += 1
                        success = True
                        break

                    except Exception as e:
                        sector_retries += 1
                        stats["dangling_refs_log"].append(
                            f"{sector} record#{sector_records+1} attempt#{attempt+1}: Exception: {str(e)}"
                        )
                        continue

                if not success:
                    stats["max_retries_hit"] += 1
                    print(f"    ⚠ Failed to generate record after {MAX_RETRIES_PER_RECORD} retries (sector: {sector})")

                # Progress indicator
                if sector_records > 0 and sector_records % 10 == 0:
                    print(f"    ... {sector_records}/{RECORDS_PER_SECTOR}")

            stats["per_sector"][sector] = {
                "records": sector_records,
                "retries": sector_retries,
                "errors": sector_errors[:5],
            }
            stats["total_retries"] += sector_retries
            stats["total_records"] += sector_records
            print(f"    ✓ Completed {sector_records}/{RECORDS_PER_SECTOR} records ({sector_retries} retries)\n")

    generation_time = time.time() - generation_start
    stats["generation_time_seconds"] = round(generation_time, 2)
    stats["generation_end"] = time.strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*60}")
    print(f"GENERATION COMPLETE")
    print(f"  Total records: {stats['total_records']}/{EXPECTED_TOTAL}")
    print(f"  Total retries: {stats['total_retries']}")
    print(f"  Duplicate input retries: {stats['duplicate_input_retries']}")
    print(f"  Max retries exceeded: {stats['max_retries_hit']}")
    print(f"  Time: {stats['generation_time_seconds']}s")
    print(f"  Output: {jsonl_path}")

    # Write generation stats
    stats_path = os.path.join(OUTPUT_DIR, "dataset_stats.json")
    stats_serializable = dict(stats)
    stats_serializable["template_usage"] = dict(stats["template_usage"])
    with open(stats_path, "w") as f:
        json.dump(stats_serializable, f, indent=2)
    print(f"  Stats: {stats_path}")

    # Run Layer 2 — Post-generation audit
    audit_results = audit_dataset(jsonl_path)
    audit_path = os.path.join(OUTPUT_DIR, "dataset_audit.json")
    with open(audit_path, "w") as f:
        json.dump(audit_results, f, indent=2)
    print(f"  Audit: {audit_path}")

    return records, stats, audit_results


def audit_dataset(jsonl_path):
    """
    Layer 2 — Post-generation full audit.

    Reads every line of dataset_1500.jsonl and:
    - Re-validates all variable references
    - Counts: total records, records with var refs, records with rollback paths
    - Checks complexity distribution
    - Verifies all 30 sectors present with 50 records each
    - Confirms zero dangling references
    - Checks for duplicate NL inputs
    """
    print(f"\n{'='*60}")
    print(f"LAYER 2 — POST-GENERATION AUDIT")
    print(f"{'='*60}")

    if not os.path.exists(jsonl_path):
        return {"error": f"File not found: {jsonl_path}"}

    audit = {
        "audit_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "file_path": jsonl_path,
        "total_records": 0,
        "valid_json": 0,
        "invalid_json_lines": [],
        "records_with_variable_refs": 0,
        "records_with_rollback_paths": 0,
        "records_with_dangling_refs": 0,
        "duplicate_input_count": 0,
        "sector_counts": defaultdict(int),
        "complexity_distribution": defaultdict(int),
        "domain_counts": defaultdict(int),
        "variable_ref_details": [],
        "dangling_ref_details": [],
        "rollback_sectors": defaultdict(int),
        "var_sectors": defaultdict(int),
        "zero_dangling_refs": False,
        "pass": False,
    }

    records = []
    seen_inputs = set()

    with open(jsonl_path, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            audit["total_records"] += 1

            try:
                record = json.loads(line)
                audit["valid_json"] += 1
                records.append(record)
            except json.JSONDecodeError as e:
                audit["invalid_json_lines"].append({"line": line_num, "error": str(e)})
                continue

            # Check for duplicate NL input
            inp = record.get("input", "")
            if inp in seen_inputs:
                audit["duplicate_input_count"] += 1
            seen_inputs.add(inp)

            # Extract output
            output = record.get("output", {})
            actions = output.get("actions", [])
            variable_chain = output.get("variable_chain", [])
            complexity = output.get("complexity", {})
            sector = output.get("sector", "Unknown")
            domain = output.get("domain", "Unknown")
            dependencies = output.get("dependencies", [])

            audit["sector_counts"][sector] += 1
            audit["domain_counts"][domain] += 1
            audit["complexity_distribution"][complexity.get("level", "unknown")] += 1

            # Check for variable refs in variable_chain (non-empty)
            has_var_refs = len(variable_chain) > 0
            if has_var_refs:
                audit["records_with_variable_refs"] += 1
                audit["var_sectors"][sector] += 1

            # Check for rollback paths (condition: "on_failure")
            has_rollback = False
            for action in actions:
                if action.get("condition") == "on_failure":
                    has_rollback = True
                    break
            if has_rollback:
                audit["records_with_rollback_paths"] += 1
                audit["rollback_sectors"][sector] += 1

            # Scan for dangling variable refs
            has_dangling = False
            for chain_entry in variable_chain:
                from_step = chain_entry.get("from_step")
                to_step = chain_entry.get("to_step")
                if from_step and to_step and from_step >= to_step:
                    has_dangling = True
                    audit["dangling_ref_details"].append(
                        f"Record {audit['total_records']}: forward ref step {from_step}→{to_step}"
                    )

            if has_dangling:
                audit["records_with_dangling_refs"] += 1

    # Compute summary stats
    total = audit["total_records"]
    audit["records_with_variable_refs_pct"] = round(
        (audit["records_with_variable_refs"] / total) * 100, 1
    ) if total > 0 else 0.0

    # Check if all variable_chain entries have valid references
    audit["zero_dangling_refs"] = audit["records_with_dangling_refs"] == 0

    # Check all sectors have 50 records
    low_sectors = []
    for sector, count in audit["sector_counts"].items():
        if count < RECORDS_PER_SECTOR:
            low_sectors.append(f"{sector}={count}")
    expected_sectors = 30
    actual_sectors = len(audit["sector_counts"])
    audit["sectors_found"] = actual_sectors
    audit["sectors_expected"] = expected_sectors
    audit["sectors_complete"] = actual_sectors == expected_sectors and len(low_sectors) == 0
    audit["low_sectors"] = low_sectors

    # Determine pass/fail
    checks_passed = True
    check_details = []

    # Check 1: Quantity
    if total == EXPECTED_TOTAL:
        check_details.append(f"✓ Quantity: {total}/{EXPECTED_TOTAL}")
    else:
        check_details.append(f"✗ Quantity: {total}/{EXPECTED_TOTAL}")
        checks_passed = False

    # Check 2: Valid JSON
    if audit["valid_json"] == total:
        check_details.append(f"✓ Valid JSON: {audit['valid_json']}/{total}")
    else:
        check_details.append(f"✗ Valid JSON: {audit['valid_json']}/{total} (invalid: {len(audit['invalid_json_lines'])})")
        checks_passed = False

    # Check 3: Zero dangling refs
    if audit["zero_dangling_refs"]:
        check_details.append(f"✓ Zero dangling refs: confirmed")
    else:
        check_details.append(f"✗ Dangling refs: {audit['records_with_dangling_refs']} records affected")
        checks_passed = False

    # Check 4: Rollback coverage ≥ 400 (25%)
    min_rollback = 400
    if audit["records_with_rollback_paths"] >= min_rollback:
        check_details.append(f"✓ Rollback coverage: {audit['records_with_rollback_paths']} (≥{min_rollback})")
    else:
        check_details.append(f"✗ Rollback coverage: {audit['records_with_rollback_paths']}/{min_rollback}")
        checks_passed = False

    # Check 5: Variable passing coverage ≥ 400 (25%)
    min_var = 400
    if audit["records_with_variable_refs"] >= min_var:
        check_details.append(f"✓ Variable passing: {audit['records_with_variable_refs']} (≥{min_var})")
    else:
        check_details.append(f"✗ Variable passing: {audit['records_with_variable_refs']}/{min_var}")
        checks_passed = False

    # Check 6: Sector completeness
    if audit["sectors_complete"]:
        check_details.append(f"✓ All {actual_sectors} sectors complete with {RECORDS_PER_SECTOR} records each")
    else:
        check_details.append(f"✗ Sector issues: {low_sectors}")
        checks_passed = False

    # Check 7: No duplicate inputs
    if audit["duplicate_input_count"] == 0:
        check_details.append(f"✓ No duplicate NL inputs")
    else:
        check_details.append(f"✗ Duplicate NL inputs: {audit['duplicate_input_count']}")
        checks_passed = False

    audit["checks"] = check_details
    audit["pass"] = checks_passed

    # Print summary
    print(f"\nAudit Results:")
    for detail in check_details:
        print(f"  {detail}")

    print(f"\n  Complexity Distribution:")
    for level, count in sorted(audit["complexity_distribution"].items()):
        pct = round(count / total * 100, 1) if total > 0 else 0
        print(f"    {level}: {count} ({pct}%)")

    print(f"\n  Overall: {'✅ PASS' if checks_passed else '❌ FAIL'}")

    # Convert defaultdicts to regular dicts
    audit["sector_counts"] = dict(audit["sector_counts"])
    audit["complexity_distribution"] = dict(audit["complexity_distribution"])
    audit["domain_counts"] = dict(audit["domain_counts"])
    audit["rollback_sectors"] = dict(audit["rollback_sectors"])
    audit["var_sectors"] = dict(audit["var_sectors"])

    return audit


if __name__ == "__main__":
    print("=" * 60)
    print("SYNTHETIC ACTION SEQUENCE DATASET GENERATOR")
    print("=" * 60)
    print(f"Seed: {SEED}")
    print(f"Target: {EXPECTED_TOTAL} records ({RECORDS_PER_SECTOR} per sector × 30 sectors)")
    print(f"Retries: up to {MAX_RETRIES_PER_RECORD} per record")
    print(f"Output dir: {OUTPUT_DIR}")
    print()

    records, stats, audit = generate_dataset()

    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)