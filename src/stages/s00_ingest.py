"""
Stage 00: Data Ingestion
========================

Load and validate raw data sources:
- Image manifest (nebraska_streetview_manifest.csv)
- Broadband labels with RUCA codes
- Study area ZIP codes

Output: data_work/data_raw.parquet
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    DATA_RAW_DIR, DATA_WORK_DIR, DIAGNOSTICS_DIR,
    MANIFEST_DIR, LABELS_DIR,
    OUTCOME_VAR, TREATMENT_VAR,
)
from src.utils.helpers import save_parquet, save_csv, ensure_dir, get_timestamp


# Required columns for validation
REQUIRED_MANIFEST_COLS = ['zip', 'lat', 'lon']
REQUIRED_LABEL_COLS = ['zip', 'broadband_usage', 'RUCA1']


def load_manifest(path: Path = None) -> pd.DataFrame:
    """Load and validate the image manifest."""
    if path is None:
        path = MANIFEST_DIR / 'nebraska_streetview_manifest.csv'

    print(f"   Loading manifest: {path}")
    df = pd.read_csv(path)

    # Standardize ZIP code format
    df['zip'] = df['zip'].astype(str).str.zfill(5)

    print(f"   Loaded {len(df)} image records")
    print(f"   Unique ZIP codes: {df['zip'].nunique()}")

    return df


def load_labels(path: Path = None) -> pd.DataFrame:
    """Load and validate broadband labels with RUCA codes."""
    if path is None:
        path = LABELS_DIR / 'broadband_labels_with_ruca.csv'

    print(f"   Loading labels: {path}")
    df = pd.read_csv(path)

    # Standardize ZIP code format
    df['zip'] = df['zip'].astype(str).str.zfill(5)

    # Validate required columns
    missing = set(REQUIRED_LABEL_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in labels: {missing}")

    print(f"   Loaded {len(df)} ZIP codes with labels")
    print(f"   Broadband usage range: {df['broadband_usage'].min():.2f} - {df['broadband_usage'].max():.2f}")
    print(f"   RUCA codes: {sorted(df['RUCA1'].unique())}")

    return df


def load_zip_list(path: Path = None) -> pd.DataFrame:
    """Load study area ZIP code list."""
    if path is None:
        path = MANIFEST_DIR / 'zip_east_264.csv'

    print(f"   Loading ZIP list: {path}")
    df = pd.read_csv(path)

    # Handle different column name possibilities
    zip_col = 'zip' if 'zip' in df.columns else df.columns[0]
    df['zip'] = df[zip_col].astype(str).str.zfill(5)

    print(f"   Study area: {len(df)} ZIP codes")

    return df[['zip']]


def merge_data(manifest_df: pd.DataFrame, labels_df: pd.DataFrame) -> pd.DataFrame:
    """Merge manifest with labels."""
    print("   Merging manifest with labels...")

    # Aggregate manifest to ZIP level
    zip_manifest = manifest_df.groupby('zip').agg({
        'lat': 'mean',
        'lon': 'mean',
    }).reset_index()
    zip_manifest.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
    zip_manifest['n_images'] = manifest_df.groupby('zip').size().values

    # Merge with labels
    merged = zip_manifest.merge(labels_df, on='zip', how='inner')

    print(f"   Merged dataset: {len(merged)} ZIP codes")
    print(f"   Coverage: {len(merged) / len(labels_df) * 100:.1f}% of labeled ZIPs")

    return merged


def generate_quality_report(df: pd.DataFrame, output_dir: Path):
    """Generate data quality report."""
    timestamp = get_timestamp()

    report = {
        'timestamp': timestamp,
        'n_rows': len(df),
        'n_columns': len(df.columns),
        'columns': list(df.columns),
        'missing_by_column': df.isna().sum().to_dict(),
        'dtypes': df.dtypes.astype(str).to_dict(),
    }

    # Save quality report
    report_df = pd.DataFrame([
        {'metric': 'n_rows', 'value': len(df)},
        {'metric': 'n_columns', 'value': len(df.columns)},
        {'metric': 'missing_total', 'value': df.isna().sum().sum()},
        {'metric': 'outcome_mean', 'value': df[OUTCOME_VAR].mean()},
        {'metric': 'outcome_std', 'value': df[OUTCOME_VAR].std()},
    ])

    ensure_dir(output_dir)
    save_csv(report_df, output_dir / f's00_ingest_quality_{timestamp}.csv')

    return report


def main(use_demo: bool = False) -> int:
    """
    Run Stage 00: Data Ingestion.

    Parameters
    ----------
    use_demo : bool
        Whether to use demo/sample data.

    Returns
    -------
    int
        Exit code (0 = success).
    """
    print("=" * 70)
    print("STAGE 00: DATA INGESTION")
    print("=" * 70)

    try:
        # Load data sources
        print("\n📂 Loading data sources...")
        manifest_df = load_manifest()
        labels_df = load_labels()

        # Merge data
        print("\n🔗 Merging datasets...")
        merged_df = merge_data(manifest_df, labels_df)

        # Generate quality report
        print("\n📊 Generating quality report...")
        ensure_dir(DIAGNOSTICS_DIR)
        generate_quality_report(merged_df, DIAGNOSTICS_DIR)

        # Save output
        print("\n💾 Saving output...")
        ensure_dir(DATA_WORK_DIR)
        output_path = DATA_WORK_DIR / 'data_raw.parquet'
        save_parquet(merged_df, output_path)
        print(f"   Saved: {output_path}")

        print("\n✅ Stage 00 complete!")
        print(f"   Output: {len(merged_df)} ZIP codes in data_raw.parquet")

        return 0

    except Exception as e:
        print(f"\n❌ Stage 00 failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
