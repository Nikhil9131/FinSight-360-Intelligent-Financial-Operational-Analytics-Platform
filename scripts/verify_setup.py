"""
FinSight 360 - Quick Connection & Environment Verification
===========================================================
Verifies that all core infrastructure is working:
  1. Python packages importable
  2. .env loaded correctly
  3. PostgreSQL connection alive
  4. Project directories exist

Usage:
    python scripts/verify_setup.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_mark(label: str, passed: bool, detail: str = ""):
    """Print a pass/fail check."""
    icon = "✓" if passed else "✗"
    msg = f"  [{icon}] {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return passed


def main():
    print("=" * 60)
    print("FinSight 360 — Environment Verification")
    print("=" * 60)
    all_ok = True

    # ── 1. Python version ──────────────────────────────────────
    print("\n1. Python Environment")
    v = sys.version_info
    all_ok &= check_mark(
        "Python version",
        v.major == 3 and v.minor >= 11,
        f"{v.major}.{v.minor}.{v.micro}"
    )

    # ── 2. Required packages ──────────────────────────────────
    print("\n2. Required Packages")
    packages = {
        "pandas": "pandas",
        "numpy": "numpy",
        "matplotlib": "matplotlib",
        "seaborn": "seaborn",
        "sklearn": "scikit-learn",
        "statsmodels": "statsmodels",
        "psycopg2": "psycopg2-binary",
        "sqlalchemy": "sqlalchemy",
        "dotenv": "python-dotenv",
        "openpyxl": "openpyxl",
        "loguru": "loguru",
        "fpdf2": "fpdf2",
        "pytest": "pytest",
        "requests": "requests",
    }
    for import_name, pip_name in packages.items():
        try:
            mod = __import__(import_name)
            ver = getattr(mod, "__version__", "OK")
            all_ok &= check_mark(pip_name, True, f"v{ver}")
        except ImportError:
            all_ok &= check_mark(pip_name, False, "NOT INSTALLED — run: pip install " + pip_name)

    # ── 3. Configuration ──────────────────────────────────────
    print("\n3. Configuration")
    env_file = PROJECT_ROOT / ".env"
    has_env = env_file.exists()
    all_ok &= check_mark(".env file exists", has_env,
                         str(env_file) if has_env else "Copy .env.example to .env")

    if has_env:
        from config.settings import get_settings
        settings = get_settings()
        all_ok &= check_mark("DB_HOST configured", bool(settings.DB_HOST), settings.DB_HOST)
        all_ok &= check_mark("DB_NAME configured", bool(settings.DB_NAME), settings.DB_NAME)
        all_ok &= check_mark("DB_PASSWORD set", bool(settings.DB_PASSWORD),
                             "***" if settings.DB_PASSWORD else "EMPTY — update .env")

    # ── 4. Database connection ────────────────────────────────
    print("\n4. Database Connection")
    if has_env:
        try:
            from src.utils.db_connector import test_connection
            connected = test_connection()
            all_ok &= check_mark("PostgreSQL connection", connected)
        except Exception as e:
            all_ok &= check_mark("PostgreSQL connection", False, str(e))
    else:
        check_mark("PostgreSQL connection", False, "Skipped — no .env file")

    # ── 5. Project directories ────────────────────────────────
    print("\n5. Project Directories")
    dirs_to_check = [
        "data/raw", "data/processed", "data/synthetic",
        "database/schema", "src/ingestion", "src/cleaning",
        "src/utils", "logs", "tests", "notebooks",
    ]
    for d in dirs_to_check:
        p = PROJECT_ROOT / d
        all_ok &= check_mark(d, p.is_dir())

    # ── Summary ───────────────────────────────────────────────
    print("\n" + "=" * 60)
    if all_ok:
        print("ALL CHECKS PASSED ✓ — Ready for Phase 3!")
    else:
        print("SOME CHECKS FAILED ✗ — Fix the issues above before proceeding.")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
