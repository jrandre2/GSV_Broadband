"""
Stage 01: Record Linkage
========================

Link images to ZIP codes and broadband labels.
Count images per ZIP and validate coverage.

Input: data_work/data_raw.parquet
Output: data_work/data_linked.parquet, diagnostics/linkage_summary.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    DATA_RAW_DIR, DATA_WORK_DIR, DIAGNOSTICS_DIR, IMAGES_DIR,
)
from src.utils.helpers import (
    load_parquet, save_parquet, save_csv, ensure_dir, get_timestamp
)


def count_images_per_zip(images_dir: Path) -> pd.DataFrame:
    """Count available images per ZIP code."""
    print(f"   Scanning image directory: {images_dir}")

    image_counts = []
    if images_dir.exists():
        for zip_dir in images_dir.iterdir():
            if zip_dir.is_dir():
                n_images = len(list(zip_dir.glob("*.jpg"))) + len(list(zip_dir.glob("*.png")))
                if n_images > 0:
                    image_counts.append({
                        'zip': zip_dir.name,
                        'n_images_available': n_images,
                        'has_images': True,
                    })

    df = pd.DataFrame(image_counts)
    if len(df) > 0:
        df['zip'] = df['zip'].astype(str).str.zfill(5)

    print(f"   Found images for {len(df)} ZIP codes")
    return df


def link_images_to_data(data_df: pd.DataFrame, image_counts: pd.DataFrame) -> pd.DataFrame:
    """Link image availability to data."""
    print("   Linking images to data...")

    # Merge image counts
    linked = data_df.merge(image_counts, on='zip', how='left')

    # Fill missing values
    linked['n_images_available'] = linked['n_images_available'].fillna(0).astype(int)
    linked['has_images'] = linked['has_images'].fillna(False)

    # Add link status
    linked['link_status'] = np.where(linked['has_images'], 'linked', 'no_images')

    n_linked = linked['has_images'].sum()
    print(f"   Linked {n_linked} of {len(linked)} ZIP codes ({n_linked/len(linked)*100:.1f}%)")

    return linked


def generate_linkage_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Generate linkage summary statistics."""
    summary = pd.DataFrame([
        {'metric': 'total_zip_codes', 'value': len(df)},
        {'metric': 'zips_with_images', 'value': df['has_images'].sum()},
        {'metric': 'zips_without_images', 'value': (~df['has_images']).sum()},
        {'metric': 'coverage_pct', 'value': df['has_images'].mean() * 100},
        {'metric': 'total_images', 'value': df['n_images_available'].sum()},
        {'metric': 'mean_images_per_zip', 'value': df.loc[df['has_images'], 'n_images_available'].mean()},
        {'metric': 'min_images_per_zip', 'value': df.loc[df['has_images'], 'n_images_available'].min()},
        {'metric': 'max_images_per_zip', 'value': df.loc[df['has_images'], 'n_images_available'].max()},
    ])
    return summary


def main() -> int:
    """Run Stage 01: Record Linkage."""
    print("=" * 70)
    print("STAGE 01: RECORD LINKAGE")
    print("=" * 70)

    try:
        # Load input data
        print("\n📂 Loading data_raw.parquet...")
        input_path = DATA_WORK_DIR / 'data_raw.parquet'
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}. Run stage 00 first.")
        data_df = load_parquet(input_path)
        print(f"   Loaded {len(data_df)} records")

        # Count images per ZIP
        print("\n📷 Counting images per ZIP...")
        image_counts = count_images_per_zip(IMAGES_DIR)

        # Link images to data
        print("\n🔗 Linking images to data...")
        linked_df = link_images_to_data(data_df, image_counts)

        # Generate summary
        print("\n📊 Generating linkage summary...")
        summary = generate_linkage_summary(linked_df)
        ensure_dir(DIAGNOSTICS_DIR)
        save_csv(summary, DIAGNOSTICS_DIR / 'linkage_summary.csv')

        # Print summary
        print("\n   Linkage Summary:")
        for _, row in summary.iterrows():
            print(f"      {row['metric']}: {row['value']:.2f}" if isinstance(row['value'], float)
                  else f"      {row['metric']}: {int(row['value'])}")

        # Save output
        print("\n💾 Saving output...")
        output_path = DATA_WORK_DIR / 'data_linked.parquet'
        save_parquet(linked_df, output_path)
        print(f"   Saved: {output_path}")

        print("\n✅ Stage 01 complete!")
        return 0

    except Exception as e:
        print(f"\n❌ Stage 01 failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
