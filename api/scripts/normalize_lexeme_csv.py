import csv
import sys
from pathlib import Path
from typing import List, Optional

CANDIDATE_DELIMITERS = [',', ';', '\t', '|']
CANDIDATE_ENCODINGS = ['utf-8-sig', 'utf-8', 'utf-16', 'utf-16-le', 'utf-16-be']


def read_rows_robust(in_p: Path) -> List[dict]:
    # Try multiple encodings and delimiters; return rows if header parsed and rows exist
    for enc in CANDIDATE_ENCODINGS:
        try:
            text = in_p.read_text(encoding=enc)
        except Exception:
            continue
        # Try csv.Sniffer first
        try:
            dialect = csv.Sniffer().sniff(text.splitlines()[0] + '\n' + (text.splitlines()[1] if len(text.splitlines()) > 1 else ''))
            delim_candidates = [dialect.delimiter]
        except Exception:
            delim_candidates = CANDIDATE_DELIMITERS
        for delim in delim_candidates:
            try:
                reader = csv.DictReader(text.splitlines(), delimiter=delim)
                rows = list(reader)
                if reader.fieldnames and len(rows) > 0:
                    return rows
            except Exception:
                continue
    # Fallback: try basic utf-8 comma
    try:
        with in_p.open('r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            return rows
    except Exception:
        return []


def normalize(in_path: str, out_path: str) -> None:
    in_p = Path(in_path)
    out_p = Path(out_path)

    rows = read_rows_robust(in_p)

    if not rows:
        print(f"⚠️ Could not parse rows from {in_p}. Check delimiter/encoding.")
        # Still write an empty normalized file with header for visibility
        with out_p.open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['lemma','pos','cefr_level','frequency_rank'])
            writer.writeheader()
        return

    # Detect columns (case-insensitive, allow spaces)
    def get(row, *candidates):
        for cand in candidates:
            for k in row.keys():
                if k is None:
                    continue
                if k.strip().lower() == cand.strip().lower():
                    return row[k]
        return None

    # Sort descending by frequency absolute ("Frq abs") if present, else stable
    def freq_value(row):
        val = get(row, 'Frq abs', 'freq abs', 'freq', 'frequency', 'count', 'freq_abs')
        try:
            return float(str(val).replace(',', '').strip()) if val not in (None, '') else 0.0
        except Exception:
            return 0.0

    rows_sorted = sorted(rows, key=freq_value, reverse=True)

    out_rows = []
    rank = 0
    for r in rows_sorted:
        lemma = get(r, 'Lemma', 'lemma', 'word')
        pos = get(r, 'POS', 'pos', 'part_of_speech')
        cefr = get(r, 'CEFR', 'cefr', 'cefr_level')
        if not lemma or str(lemma).strip() == '':
            continue
        rank += 1
        out_rows.append({
            'lemma': str(lemma).strip().lower(),
            'pos': (str(pos).strip().lower() if pos not in (None, '') else ''),
            'cefr_level': (str(cefr).strip().upper() if cefr not in (None, '') else ''),
            'frequency_rank': rank,
        })

    with out_p.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['lemma','pos','cefr_level','frequency_rank'])
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"✅ Normalized {len(out_rows)} rows -> {out_p}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python normalize_lexeme_csv.py <input.csv> <output.csv>')
        sys.exit(1)
    normalize(sys.argv[1], sys.argv[2])
