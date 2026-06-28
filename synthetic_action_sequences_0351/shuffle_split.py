#!/usr/bin/env python3
"""
Shuffle dataset_1500.jsonl thoroughly and split into train/validation/test sets (80/10/10).
"""
import json
import random
from collections import Counter

INPUT_FILE = "/app/synthetic_action_sequences_0351/dataset_1500.jsonl"
SEED = 42
TRAIN_RATIO, VAL_RATIO = 0.8, 0.1

# Step 1: Read all records
records = []
with open(INPUT_FILE, "r") as f:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        records.append(record)

print(f"=== STEP 1: Read {len(records)} records from {INPUT_FILE} ===")
assert len(records) == 1500, f"Expected 1500 records, got {len(records)}"

# Show original first 3 records (before shuffle)
print("Original first 3 records:")
for i in range(3):
    rec = records[i]
    print(f"  [{i}] sector={rec.get('sector','?')}, input={rec.get('input','')[:60]}...")

# Step 2: Shuffle thoroughly
rng = random.Random(SEED)
records_copy = list(records)  # keep original order for comparison
rng.shuffle(records)
print(f"\n=== STEP 2: Shuffled with random.Random({SEED}) ===")

# Verify shuffle changed order
changed = sum(1 for i in range(len(records)) if records[i] is not records_copy[i])
print(f"  Records in different position: {changed}/{len(records)}")

print("Shuffled first 3 records:")
for i in range(3):
    rec = records[i]
    print(f"  [{i}] sector={rec.get('sector','?')}, input={rec.get('input','')[:60]}...")

# Step 3: Split into train/val/test
n = len(records)
train_end = int(n * TRAIN_RATIO)  # 1200
val_end = train_end + int(n * VAL_RATIO)  # 1200 + 150 = 1350

train = records[:train_end]
val = records[train_end:val_end]
test = records[val_end:]

print(f"\n=== STEP 3: Split ===")
print(f"  Train: {len(train)} ({100*len(train)//n}%)")
print(f"  Val:   {len(val)} ({100*len(val)//n}%)")
print(f"  Test:  {len(test)} ({100*len(test)//n}%)")
print(f"  Sum:   {len(train) + len(val) + len(test)}")

assert len(train) == 1200, f"Train expected 1200, got {len(train)}"
assert len(val) == 150, f"Val expected 150, got {len(val)}"
assert len(test) == 150, f"Test expected 150, got {len(test)}"
assert len(train) + len(val) + len(test) == 1500, "Sums don't match 1500"

# Verify no overlap using serialized record identity
train_set = {json.dumps(r, sort_keys=True) for r in train}
val_set = {json.dumps(r, sort_keys=True) for r in val}
test_set = {json.dumps(r, sort_keys=True) for r in test}

assert train_set.isdisjoint(val_set), "OVERLAP between train and val!"
assert train_set.isdisjoint(test_set), "OVERLAP between train and test!"
assert val_set.isdisjoint(test_set), "OVERLAP between val and test!"
print("  ✅ No overlap between splits")

# Step 4: Write to separate files
OUTPUT_DIR = "/app/synthetic_action_sequences_0351"

for fname, split_records in [("dataset_train.jsonl", train),
                               ("dataset_val.jsonl", val),
                               ("dataset_test.jsonl", test)]:
    path = f"{OUTPUT_DIR}/{fname}"
    with open(path, "w") as f:
        for rec in split_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"  ✅ Written {len(split_records)} records to {path}")

print(f"\n=== STEP 4: Verify file line counts ===")
for fname in ["dataset_train.jsonl", "dataset_val.jsonl", "dataset_test.jsonl"]:
    path = f"{OUTPUT_DIR}/{fname}"
    with open(path) as f:
        count = sum(1 for line in f if line.strip())
    expected = {"dataset_train.jsonl": 1200, "dataset_val.jsonl": 150, "dataset_test.jsonl": 150}
    expected_count = expected[fname]
    status = "✅" if count == expected_count else "❌"
    print(f"  {status} {fname}: {count} lines (expected {expected_count})")

# Step 5: Summary - sector distribution per split
print(f"\n=== STEP 5: Sector Distribution ===")

for split_name, split_records in [("Train", train), ("Val", val), ("Test", test)]:
    sector_counts = Counter(r.get("sector", "UNKNOWN") for r in split_records)
    print(f"\n--- {split_name} ({len(split_records)} records, {len(sector_counts)} sectors) ---")
    for sector, count in sorted(sector_counts.items()):
        print(f"  {sector}: {count}")

print(f"\n=== First/Last Record Sector===")
for split_name, split_records in [("Train", train), ("Val", val), ("Test", test)]:
    print(f"  {split_name}: first={split_records[0].get('sector','?')}  last={split_records[-1].get('sector','?')}")

print(f"\n{'='*50}")
print("🎉 ALL DONE - Dataset shuffled and split successfully!")