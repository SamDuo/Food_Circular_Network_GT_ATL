"""
Rewrite AFCN org descriptions from first-person ("we / our / us / I / my")
to third-person ("they / their / them") so the directory reads as
journalism rather than self-promotion.

INPUT:   data/afcn_directory/clean_export.csv
OUTPUT:  data/afcn_directory/clean_export.csv      (in place; backed up)
         data/afcn_directory/clean_export.csv.bak  (one-shot backup)

After rewriting we re-run build_afcn_taxonomy.py so network/index.html
and network/force.html pick up the new prose.

USAGE:   python scripts/rewrite_descriptions.py
"""
import csv, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / "data" / "afcn_directory" / "clean_export.csv"
BAK  = SRC.with_suffix(".csv.bak")

# Word-boundary regex rules, applied in order. Contractions first so the
# bare pronouns don't eat them. Casing preserved by separate Up/Lower rules.
RULES = [
    (r"\bWe're\b",       "They're"),
    (r"\bwe're\b",       "they're"),
    (r"\bWe've\b",       "They've"),
    (r"\bwe've\b",       "they've"),
    (r"\bWe'll\b",       "They'll"),
    (r"\bwe'll\b",       "they'll"),
    (r"\bWe'd\b",        "They'd"),
    (r"\bwe'd\b",        "they'd"),
    (r"\bWe\b",          "They"),
    (r"\bwe\b",          "they"),
    (r"\bOur\b",         "Their"),
    (r"\bour\b",         "their"),
    (r"\bOurs\b",        "Theirs"),
    (r"\bours\b",        "theirs"),
    (r"\bOurselves\b",   "Themselves"),
    (r"\bourselves\b",   "themselves"),
    (r"\bUs\b",          "Them"),
    (r"\bus\b",          "them"),
    # First-person singular (founder bios). "I" → "they" reads fine here.
    (r"\bI'm\b",         "They're"),
    (r"\bi'm\b",         "they're"),
    (r"\bI've\b",        "They've"),
    (r"\bI'll\b",        "They'll"),
    (r"\bI'd\b",         "They'd"),
    (r"\bI\b",           "They"),
    (r"\bMyself\b",      "Themselves"),
    (r"\bmyself\b",      "themselves"),
    (r"\bMy\b",          "Their"),
    (r"\bmy\b",          "their"),
    (r"\bMine\b",        "Theirs"),
    (r"\bmine\b",        "theirs"),
    # "Me" is risky (proper-noun "Me" rare) — restrict to lowercase.
    (r"\bme\b",          "them"),
]
COMPILED = [(re.compile(p), r) for p, r in RULES]


def first_to_third(text: str) -> str:
    if not text:
        return text
    out = text
    for pat, rep in COMPILED:
        out = pat.sub(rep, out)
    # "they am" → "they are"  (rare but possible after I→They)
    out = re.sub(r"\bThey am\b", "They are", out)
    out = re.sub(r"\bthey am\b", "they are", out)
    # Smooth doubled spaces from edits
    out = re.sub(r" {2,}", " ", out)
    return out


def main():
    if not SRC.exists():
        print(f"Missing input: {SRC}", file=sys.stderr)
        sys.exit(1)

    if not BAK.exists():
        shutil.copy2(SRC, BAK)
        print(f"  · backed up original → {BAK.relative_to(ROOT)}")

    with open(SRC, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    rewritten = 0
    for r in rows:
        before = r.get("Description", "")
        if not before:
            continue
        after = first_to_third(before)
        if after != before:
            rewritten += 1
            r["Description"] = after

    with open(SRC, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  ✓ rewrote {rewritten:,} of {len(rows):,} descriptions to 3rd person")
    print(f"  ✓ wrote {SRC.relative_to(ROOT)}")

    print("\n→ Rebuilding taxonomy from rewritten data…")
    subprocess.run(
        [sys.executable, "-X", "utf8",
         str(ROOT / "scripts" / "build_afcn_taxonomy.py")],
        check=False
    )


if __name__ == "__main__":
    main()
