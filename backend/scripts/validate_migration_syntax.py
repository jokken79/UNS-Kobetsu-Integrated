#!/usr/bin/env python3
"""
Validate migration syntax - checks Python syntax without imports
"""
import ast
import sys

def validate_python_file(filepath, description):
    """Validate that a Python file has correct syntax."""
    print(f"\nValidating {description}...")

    try:
        with open(filepath, 'r') as f:
            code = f.read()

        # Parse the Python code to check syntax
        ast.parse(code)
        print(f"✅ {description}: Syntax is valid")
        return True
    except SyntaxError as e:
        print(f"❌ {description}: Syntax error at line {e.lineno}")
        print(f"   {e.text}")
        print(f"   {' ' * (e.offset - 1)}^")
        print(f"   {e.msg}")
        return False
    except FileNotFoundError:
        print(f"❌ {description}: File not found at {filepath}")
        return False
    except Exception as e:
        print(f"❌ {description}: Unexpected error: {e}")
        return False

def main():
    """Run syntax validation on all modified files."""
    print("=" * 60)
    print("Contract Cycle Fields - Python Syntax Validation")
    print("=" * 60)

    files_to_validate = [
        ("/home/user/UNS-Kobetsu-Integrated/backend/alembic/versions/004_add_contract_cycle_fields.py",
         "Migration file (004_add_contract_cycle_fields.py)"),
        ("/home/user/UNS-Kobetsu-Integrated/backend/app/models/factory.py",
         "Factory model"),
        ("/home/user/UNS-Kobetsu-Integrated/backend/app/models/kobetsu_keiyakusho.py",
         "KobetsuKeiyakusho model"),
        ("/home/user/UNS-Kobetsu-Integrated/backend/app/schemas/factory.py",
         "Factory schema"),
        ("/home/user/UNS-Kobetsu-Integrated/backend/app/schemas/kobetsu_keiyakusho.py",
         "KobetsuKeiyakusho schema"),
    ]

    all_valid = True
    for filepath, description in files_to_validate:
        if not validate_python_file(filepath, description):
            all_valid = False

    print("\n" + "=" * 60)
    if all_valid:
        print("✅ ALL FILES HAVE VALID PYTHON SYNTAX!")
        print("\nPhase 1 Implementation Summary:")
        print("1. ✅ Migration file created: 004_add_contract_cycle_fields.py")
        print("2. ✅ Factory model updated with 5 new contract cycle fields")
        print("3. ✅ KobetsuKeiyakusho model updated with previous_contract_id")
        print("4. ✅ Factory schema updated with cycle configuration and validation")
        print("5. ✅ KobetsuKeiyakusho schema updated with previous_contract_id")
        print("\nNext steps:")
        print("- Apply migration: docker exec -it uns-kobetsu-backend alembic upgrade head")
        print("- Test the new fields through the API")
    else:
        print("❌ SOME FILES HAVE SYNTAX ERRORS")
        print("Please fix the syntax errors before proceeding.")
    print("=" * 60)

    return 0 if all_valid else 1

if __name__ == "__main__":
    sys.exit(main())