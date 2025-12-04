"""Rename template files to safe romaji names."""
import os
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "excel"

# Mapping from patterns to new names
RENAME_MAP = {
    "DAICHO": "daicho.xlsx",
    "kobetsu": "kobetsu_keiyakusho.xlsx",
    "tsuchi": "tsuchisho.xlsx",
    "hakenmoto": "hakenmoto_daicho.xlsx",
    "shugyo": "shugyo_joken.xlsx",
    "keiyaku": "keiyakusho.xlsx",
}

def rename_templates():
    """Rename all templates to romaji names."""
    print(f"Template directory: {TEMPLATE_DIR}")

    for file in TEMPLATE_DIR.glob("*.xlsx"):
        old_name = file.name
        print(f"Found: {repr(old_name)}")

        # Check for DAICHO
        if "DAICHO" in old_name.upper():
            new_name = "daicho.xlsx"
        # Check file size to identify which document it is
        elif file.stat().st_size > 25000:  # ~28KB = DAICHO (already handled)
            continue
        elif file.stat().st_size > 16000 and file.stat().st_size < 17500:  # ~16.8KB = kobetsu
            new_name = "kobetsu_keiyakusho.xlsx"
        elif file.stat().st_size > 16000 and file.stat().st_size < 17000:  # ~16.5KB = keiyakusho
            new_name = "keiyakusho.xlsx"
        elif file.stat().st_size > 17000 and file.stat().st_size < 18000:  # ~17.4KB = hakenmoto
            new_name = "hakenmoto_daicho.xlsx"
        elif file.stat().st_size > 12000 and file.stat().st_size < 13000:  # ~12.4KB = tsuchisho
            new_name = "tsuchisho.xlsx"
        elif file.stat().st_size > 11000 and file.stat().st_size < 12000:  # ~11.2KB = shugyo
            new_name = "shugyo_joken.xlsx"
        else:
            print(f"  Unknown file size: {file.stat().st_size}")
            continue

        new_path = TEMPLATE_DIR / new_name
        if new_path.exists() and new_path != file:
            print(f"  Target exists, removing: {new_name}")
            new_path.unlink()

        print(f"  Renaming to: {new_name}")
        file.rename(new_path)

if __name__ == "__main__":
    rename_templates()

    print("\nFinal list:")
    for f in sorted(TEMPLATE_DIR.glob("*.xlsx")):
        print(f"  {f.name} ({f.stat().st_size / 1024:.1f} KB)")
