"""
Stage 02: Panel Construction
============================

Extract computer vision features from images and construct
the analysis-ready panel dataset.

Input: data_work/data_linked.parquet, data_raw/images/
Output: data_work/panel.parquet, data_work/features/extracted_features.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    DATA_WORK_DIR, FEATURES_DIR, DIAGNOSTICS_DIR, IMAGES_DIR,
    N_VISUAL_FEATURES, VISUAL_FEATURE_NAMES, SPATIAL_CV_N_GROUPS,
    SPATIAL_GROUPING_METHOD,
)
from src.utils.helpers import load_parquet, save_parquet, save_csv, ensure_dir, get_timestamp
from src.utils.feature_extraction import VisualFeatureExtractor
from src.utils.spatial_cv import SpatialCVManager


def load_precomputed_features(features_dir: Path) -> pd.DataFrame:
    """Load precomputed features if available."""
    # Look for existing feature files
    feature_files = list(features_dir.glob("optimal_features*.csv"))
    if feature_files:
        # Use most recent
        latest = sorted(feature_files)[-1]
        print(f"   Found precomputed features: {latest.name}")
        df = pd.read_csv(latest)
        df['zip'] = df['zip'].astype(str).str.zfill(5)
        return df
    return None


def extract_features(
    df: pd.DataFrame,
    images_dir: Path,
    max_images: int = 10,
) -> pd.DataFrame:
    """Extract visual features for all ZIP codes."""
    print(f"   Extracting features from images ({max_images} per ZIP max)...")

    extractor = VisualFeatureExtractor(max_images_per_zip=max_images)

    # Extract features
    zip_codes = df['zip'].tolist()
    features_matrix = extractor.extract_batch(zip_codes, images_dir, verbose=True)

    # Create features DataFrame
    feature_cols = extractor.feature_names
    features_df = pd.DataFrame(features_matrix, columns=feature_cols)
    features_df['zip'] = zip_codes

    print(f"   Extracted {len(feature_cols)} features for {len(zip_codes)} ZIP codes")

    return features_df


def create_spatial_groups(df: pd.DataFrame) -> np.ndarray:
    """Create spatial groups for cross-validation."""
    print("   Creating spatial groups...")

    manager = SpatialCVManager(
        n_groups=SPATIAL_CV_N_GROUPS,
        method=SPATIAL_GROUPING_METHOD,
    )

    if SPATIAL_GROUPING_METHOD == 'zip_digit':
        groups = manager.create_groups_from_zip_codes(df['zip'])
    elif SPATIAL_GROUPING_METHOD in ('contiguity_queen', 'contiguity_rook'):
        try:
            import geopandas as gpd
        except Exception as exc:
            raise ImportError(f"geopandas required for contiguity grouping: {exc}")

        shp_path = Path('tl_2022_us_zcta520.shp')
        if not shp_path.exists():
            raise FileNotFoundError(f"Shapefile not found: {shp_path}")

        zcta_list = df['zip'].astype(str).str.zfill(5).tolist()
        gdf = gpd.read_file(shp_path)
        gdf['ZCTA5CE20'] = gdf['ZCTA5CE20'].astype(str).str.zfill(5)
        gdf = gdf[gdf['ZCTA5CE20'].isin(zcta_list)]
        if len(gdf) != len(zcta_list):
            missing = set(zcta_list) - set(gdf['ZCTA5CE20'])
            print(f"   Warning: missing {len(missing)} ZCTAs in shapefile; falling back to coordinates")
            if 'latitude' not in df.columns or 'longitude' not in df.columns:
                raise ValueError("Missing latitude/longitude for spatial grouping fallback")
            groups = manager.create_groups_from_coordinates(
                df['latitude'].values,
                df['longitude'].values,
            )
        else:
            gdf = gdf.set_index('ZCTA5CE20').loc[zcta_list].reset_index()
            contiguity = SPATIAL_GROUPING_METHOD.replace('contiguity_', '')
            groups = manager.create_groups_from_geodata(gdf, contiguity=contiguity)
    else:
        if 'latitude' not in df.columns or 'longitude' not in df.columns:
            raise ValueError("Missing latitude/longitude for spatial grouping")
        groups = manager.create_groups_from_coordinates(
            df['latitude'].values,
            df['longitude'].values,
        )

    return groups


def build_panel(
    linked_df: pd.DataFrame,
    features_df: pd.DataFrame,
) -> pd.DataFrame:
    """Build the final analysis panel."""
    print("   Building analysis panel...")

    # Keep prefixed features plus the OpenCV feature list, drop non-feature metadata.
    prefixed = [c for c in features_df.columns if c.startswith(('infrastructure_', 'color_'))]
    named = [c for c in VISUAL_FEATURE_NAMES if c in features_df.columns]
    feature_cols = sorted(set(prefixed + named))
    features_clean = features_df[['zip'] + feature_cols].copy()

    # Merge features with linked data
    panel = linked_df.merge(features_clean, on='zip', how='left')

    # Add spatial groups
    panel['spatial_group'] = create_spatial_groups(panel)

    # Add analysis flags - detect first feature column dynamically
    if feature_cols:
        panel['has_features'] = ~panel[feature_cols[0]].isna()
    else:
        panel['has_features'] = False

    n_complete = panel['has_features'].sum()
    print(f"   Panel: {len(panel)} ZIP codes, {n_complete} with complete features")

    return panel


def generate_panel_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Generate panel summary statistics."""
    summary = pd.DataFrame([
        {'metric': 'n_zip_codes', 'value': len(df)},
        {'metric': 'n_with_features', 'value': df['has_features'].sum()},
        {'metric': 'n_with_images', 'value': df['has_images'].sum()},
        {'metric': 'n_spatial_groups', 'value': df['spatial_group'].nunique()},
        {'metric': 'outcome_mean', 'value': df['broadband_usage'].mean()},
        {'metric': 'outcome_std', 'value': df['broadband_usage'].std()},
        {'metric': 'ruca_unique', 'value': df['RUCA1'].nunique()},
    ])
    return summary


def main(recompute: bool = False, max_images: int = 10) -> int:
    """
    Run Stage 02: Panel Construction.

    Parameters
    ----------
    recompute : bool
        Force recomputation of features even if cached.
    max_images : int
        Maximum images per ZIP for feature extraction.
    """
    print("=" * 70)
    print("STAGE 02: PANEL CONSTRUCTION")
    print("=" * 70)

    try:
        # Load linked data
        print("\n📂 Loading linked data...")
        input_path = DATA_WORK_DIR / 'data_linked.parquet'
        if not input_path.exists():
            raise FileNotFoundError(f"Input not found: {input_path}. Run stage 01 first.")
        linked_df = load_parquet(input_path)
        print(f"   Loaded {len(linked_df)} records")

        # Check for precomputed features
        ensure_dir(FEATURES_DIR)
        features_df = None
        if not recompute:
            features_df = load_precomputed_features(FEATURES_DIR)

        # Extract features if needed
        if features_df is None:
            print("\n📷 Extracting visual features...")
            features_df = extract_features(linked_df, IMAGES_DIR, max_images)

            # Save extracted features
            timestamp = get_timestamp()
            save_csv(features_df, FEATURES_DIR / f'extracted_features_{timestamp}.csv')
        else:
            print("\n📂 Using precomputed features")

        # Build panel
        print("\n🔧 Building analysis panel...")
        panel_df = build_panel(linked_df, features_df)

        # Generate summary
        print("\n📊 Generating panel summary...")
        summary = generate_panel_summary(panel_df)
        ensure_dir(DIAGNOSTICS_DIR)
        save_csv(summary, DIAGNOSTICS_DIR / 'panel_summary.csv')

        print("\n   Panel Summary:")
        for _, row in summary.iterrows():
            val = row['value']
            print(f"      {row['metric']}: {val:.2f}" if isinstance(val, float) and val < 10
                  else f"      {row['metric']}: {int(val)}")

        # Save output
        print("\n💾 Saving output...")
        output_path = DATA_WORK_DIR / 'panel.parquet'
        save_parquet(panel_df, output_path)
        print(f"   Saved: {output_path}")

        print("\n✅ Stage 02 complete!")
        return 0

    except Exception as e:
        print(f"\n❌ Stage 02 failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--recompute', action='store_true')
    parser.add_argument('--max-images', type=int, default=10)
    args = parser.parse_args()
    sys.exit(main(recompute=args.recompute, max_images=args.max_images))
