"""
FinSight 360 - Synthetic Data Generation Script
=================================================
Entry point to generate all synthetic datasets for NovaTech Solutions.

Usage:
    python scripts/generate_synthetic_data.py
    python scripts/generate_synthetic_data.py --formats csv json xlsx
    python scripts/generate_synthetic_data.py --seed 123
"""

import sys
import argparse
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings
from src.data_generator import NovaTechDataGenerator
from src.utils.logger import get_logger

logger = get_logger("generate_data")


def main():
    parser = argparse.ArgumentParser(
        description="FinSight 360 - Generate synthetic business datasets"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--formats", nargs="+", default=["csv"],
        choices=["csv", "json", "xlsx"],
        help="Output file formats (default: csv)"
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Output directory (default: data/synthetic/)"
    )
    parser.add_argument(
        "--eda", action="store_true",
        help="Print EDA summary after generation"
    )
    args = parser.parse_args()

    settings = get_settings()
    output_dir = Path(args.output_dir) if args.output_dir else settings.DATA_SYNTHETIC_DIR

    start_time = time.time()

    # Generate all datasets
    generator = NovaTechDataGenerator(seed=args.seed)
    datasets = generator.generate_all()

    # Save to files
    saved = generator.save_all(datasets, output_dir, formats=args.formats)

    elapsed = time.time() - start_time

    # Summary
    print("\n" + "=" * 60)
    print("FILES SAVED")
    print("=" * 60)
    for filename, filepath in sorted(saved.items()):
        size_kb = filepath.stat().st_size / 1024
        print(f"  {filename:40s} {size_kb:>8.1f} KB")
    print(f"\n  Output directory: {output_dir}")
    print(f"  Time elapsed: {elapsed:.1f} seconds")
    print("=" * 60)

    # Optional EDA
    if args.eda:
        generator.print_eda_summary(datasets)

    # Also save a quick stats summary CSV
    stats = []
    for name, df in datasets.items():
        stats.append({
            "table": name,
            "rows": len(df),
            "columns": len(df.columns),
            "missing_values": int(df.isnull().sum().sum()),
            "missing_pct": round(df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100, 2),
            "duplicate_rows": int(df.duplicated().sum()),
        })

    import pandas as pd
    stats_df = pd.DataFrame(stats)
    stats_path = output_dir / "generation_stats.csv"
    stats_df.to_csv(stats_path, index=False)
    print(f"\n  Stats saved to: {stats_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

