#!/usr/bin/env python3
"""
convert_scores.py — Zebronics Soundbar Finder
Reads Soundbar_Scores.xlsx and writes scores.json

Usage:
    python convert_scores.py

Run this every time you update the Excel scorecard, then commit both files.
"""

import json
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:
    sys.exit("❌  openpyxl not installed. Run:  pip install openpyxl")

EXCEL_FILE  = Path(__file__).parent / 'Soundbar_Scores.xlsx'
OUTPUT_FILE = Path(__file__).parent / 'scores.json'

# Column positions (1-indexed) — must match the Excel layout
# A=1 product_id, B=2 name, C=3 sep,
# D=4 studio, E=5 small, F=6 medium, G=7 large,
# H=8 sep,
# I=9 tv_small, J=10 tv_medium, K=11 tv_large, L=12 tv_xlarge,
# M=13 sep,
# N=14 movies, O=15 gaming, P=16 sports, Q=17 everyday, R=18 music

COL_ID       = 1
COL_ROOM     = (4, 5, 6, 7)    # studio, small, medium, large
COL_TV       = (9, 10, 11, 12) # tv_small, tv_medium, tv_large, tv_xlarge
COL_USE      = (14, 15, 16, 17, 18)  # movies, gaming, sports, everyday, music

ROOM_KEYS    = ['studio', 'small', 'medium', 'large']
TV_KEYS      = ['tv_small', 'tv_medium', 'tv_large', 'tv_xlarge']
USE_KEYS     = ['movies', 'gaming', 'sports', 'everyday', 'music']
DATA_START   = 3  # first data row (rows 1-2 are headers)


def safe_int(val):
    """Return int or 0 for empty / non-numeric cells."""
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def convert():
    if not EXCEL_FILE.exists():
        sys.exit(f"❌  {EXCEL_FILE} not found. Make sure it's in the same folder as this script.")

    wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
    ws = wb.active

    scores = {}
    skipped = []

    for row in ws.iter_rows(min_row=DATA_START, values_only=True):
        pid = str(row[COL_ID - 1] or '').strip()
        if not pid or pid.startswith('---'):
            continue  # skip separator or empty rows

        room_vals = [safe_int(row[c - 1]) for c in COL_ROOM]
        tv_vals   = [safe_int(row[c - 1]) for c in COL_TV]
        use_vals  = [safe_int(row[c - 1]) for c in COL_USE]

        # Warn on missing scores
        all_vals = room_vals + tv_vals + use_vals
        if all(v == 0 for v in all_vals):
            skipped.append(pid)
            continue

        scores[pid] = {
            'room': dict(zip(ROOM_KEYS, room_vals)),
            'tv':   dict(zip(TV_KEYS,   tv_vals)),
            'use':  dict(zip(USE_KEYS,  use_vals)),
        }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)

    print(f"✅  scores.json written — {len(scores)} products")
    if skipped:
        print(f"⚠️   Skipped (all zeros): {', '.join(skipped)}")

    # Sanity check: flag any score outside 1-5
    warnings = []
    for pid, dims in scores.items():
        for dim, vals in dims.items():
            for key, val in vals.items():
                if not (1 <= val <= 5):
                    warnings.append(f"  {pid} → {dim}.{key} = {val}  (expected 1–5)")
    if warnings:
        print("\n⚠️  Out-of-range scores (fix in Excel):")
        print('\n'.join(warnings))
    else:
        print("✓   All scores are in range 1–5")


if __name__ == '__main__':
    convert()
