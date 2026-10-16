"""
=============================================================
 RWANDA COST-OF-LIVING INTELLIGENCE PLATFORM
 STAGE 0: Data Exploration
 Purpose : Reveal the structure of CPI and EICV7 files so
           we can write the correct cleaning code in Stage 2.
 Run once : python 00_explore_data.py
=============================================================
"""

# ─────────────────────────────────────────────────────────────
# STAGE 1 — Import required packages
# ─────────────────────────────────────────────────────────────
import os
import sys
import pandas as pd

print("✓ Stage 1 complete — packages loaded")


# ─────────────────────────────────────────────────────────────
# STAGE 2 — Set file paths  ← EDIT THESE TWO LINES
# ─────────────────────────────────────────────────────────────
CPI_FILE   = r"C:\Users\user\OneDrive\Desktop\Hachaton. proposal\Datasets\CPI_time_series_August 2026.xls"
EICV7_DIR  = r"C:\Users\user\OneDrive\Desktop\Hachaton. proposal\Datasets\EICV7"

print("✓ Stage 2 complete — paths set")


# ─────────────────────────────────────────────────────────────
# STAGE 3 — Explore the CPI Excel file
# ─────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("STAGE 3 — CPI FILE EXPLORATION")
print("="*60)

if not os.path.exists(CPI_FILE):
    print(f"ERROR: CPI file not found at:\n  {CPI_FILE}")
    print("Check the path and try again.")
    sys.exit(1)

print(f"File size : {os.path.getsize(CPI_FILE)/(1024*1024):.1f} MB")

# List all sheets
try:
    xl = pd.ExcelFile(CPI_FILE, engine='xlrd')
except Exception:
    xl = pd.ExcelFile(CPI_FILE, engine='openpyxl')

print(f"Sheets ({len(xl.sheet_names)}) :")
for i, s in enumerate(xl.sheet_names):
    print(f"  [{i}]  {s}")

# Preview every sheet — first 6 rows, no header assumption
print("\n--- First 6 rows of each sheet ---")
for sheet in xl.sheet_names:
    print(f"\n>>> Sheet : '{sheet}'")
    try:
        df = pd.read_excel(CPI_FILE, sheet_name=sheet,
                           header=None, nrows=6)
        print(df.to_string(index=False))
        print(f"    (full sheet size will be shown below)")
    except Exception as e:
        print(f"    Could not read : {e}")

# Full row/column count per sheet
print("\n--- Full dimensions per sheet ---")
for sheet in xl.sheet_names:
    try:
        df = pd.read_excel(CPI_FILE, sheet_name=sheet, header=None)
        print(f"  '{sheet}' : {df.shape[0]} rows × {df.shape[1]} columns")
    except Exception as e:
        print(f"  '{sheet}' : error — {e}")

print("\n✓ Stage 3 complete — CPI explored")


# ─────────────────────────────────────────────────────────────
# STAGE 4 — Explore the EICV7 folder
# ─────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("STAGE 4 — EICV7 FOLDER EXPLORATION")
print("="*60)

if not os.path.exists(EICV7_DIR):
    print(f"ERROR: EICV7 folder not found at:\n  {EICV7_DIR}")
    sys.exit(1)

# List every file with size
all_files = []
for root, dirs, files in os.walk(EICV7_DIR):
    for f in files:
        full = os.path.join(root, f)
        size_mb = os.path.getsize(full) / (1024*1024)
        all_files.append((f, full, size_mb))

all_files.sort(key=lambda x: x[0])
print(f"Found {len(all_files)} files:\n")
for name, path, size in all_files:
    print(f"  {name:<60s}  {size:6.2f} MB")

# Files we specifically need
TARGET_KEYWORDS = [
    's01', 's5', 's7', 'household',
    's8a', 's8b', 's8c', 'expenditure', 'food',
    's10b', 'durable',
    's9d', 'financial',
    'poverty',
]

print("\n--- Attempting to peek inside .dta files ---")
for name, path, size in all_files:
    name_lower = name.lower()
    if not name_lower.endswith('.dta'):
        continue
    if not any(kw in name_lower for kw in TARGET_KEYWORDS):
        continue

    print(f"\n>>> {name}  ({size:.2f} MB)")
    try:
        # Read only first 3 rows to keep it fast
        itr = pd.read_stata(path, iterator=True)
        df  = itr.read(3)
        print(f"    Columns ({len(df.columns)}) :")
        for col in df.columns:
            sample = str(df[col].iloc[0]) if len(df) > 0 else "—"
            print(f"      {col:<35s}  e.g. {sample[:50]}")
    except Exception as e:
        print(f"    Could not read : {e}")

print("\n✓ Stage 4 complete — EICV7 explored")

print("\n" + "="*60)
print("ALL DONE — copy-paste this entire output to Claude")
print("="*60)
