"""
Fix template page setup to match original Excel.
The original uses scale: 96 instead of fitToPage.
"""
import openpyxl
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "excel"

# Template configurations matching original Excel
TEMPLATE_CONFIG = {
    "kobetsu_keiyakusho.xlsx": {"scale": 96, "orientation": "portrait"},
    "tsuchisho.xlsx": {"scale": 100, "orientation": "portrait"},
    "daicho.xlsx": {"scale": 100, "orientation": "portrait"},
    "hakenmoto_daicho.xlsx": {"scale": 100, "orientation": "portrait"},
    "shugyo_joken.xlsx": {"scale": 100, "orientation": "landscape"},
    "keiyakusho.xlsx": {"scale": 100, "orientation": "portrait"},
}


def fix_template(filename: str, config: dict):
    """Fix a single template's page setup."""
    filepath = TEMPLATE_DIR / filename
    if not filepath.exists():
        print(f"SKIP: {filename} not found")
        return

    print(f"Fixing {filename}...")
    wb = openpyxl.load_workbook(filepath)
    ws = wb.active

    # Get page setup
    ps = ws.page_setup

    # Print before
    print(f"  Before: scale={ps.scale}, fitToWidth={ps.fitToWidth}, fitToHeight={ps.fitToHeight}")

    # Fix settings - use scale instead of fitToPage
    ps.scale = config["scale"]
    ps.fitToWidth = 0  # Disable fitToWidth
    ps.fitToHeight = 0  # Disable fitToHeight
    ps.orientation = config["orientation"]
    ps.paperSize = 9  # A4

    # Also disable fitToPage in sheet properties if present
    if hasattr(ws.page_setup, 'fitToPage'):
        ws.page_setup.fitToPage = False

    # Set proper margins (in inches) - standard A4 margins
    ws.page_margins.left = 0.25
    ws.page_margins.right = 0.25
    ws.page_margins.top = 0.5
    ws.page_margins.bottom = 0.5
    ws.page_margins.header = 0.3
    ws.page_margins.footer = 0.3

    # Print after
    print(f"  After: scale={ps.scale}, fitToWidth={ps.fitToWidth}, fitToHeight={ps.fitToHeight}")

    wb.save(filepath)
    wb.close()
    print(f"  Saved {filename}")


def main():
    print("=" * 60)
    print("FIXING TEMPLATE PAGE SETUP")
    print("=" * 60)
    print(f"Template directory: {TEMPLATE_DIR}")
    print()

    for filename, config in TEMPLATE_CONFIG.items():
        fix_template(filename, config)
        print()

    print("=" * 60)
    print("DONE - Templates fixed")
    print("=" * 60)


if __name__ == "__main__":
    main()
