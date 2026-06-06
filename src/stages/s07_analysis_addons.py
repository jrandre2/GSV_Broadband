"""
Stage 07: Analysis Add-ons
==========================

Run supplemental analyses requested by peer review:
- Holdout baselines for ACS and coordinates
- Image-count sensitivity (visual-only holdout)
- Fold-wise diagnostics for contiguity CV

Inputs: data_work/panel.parquet, data_work/data_linked.parquet,
        data_work/diagnostics/cap_sensitivity/*
Outputs: data_work/diagnostics/analysis_addons/*
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    DATA_RAW_DIR,
    DATA_WORK_DIR,
    DIAGNOSTICS_DIR,
    OUTCOME_VAR,
    TREATMENT_VAR,
    VISUAL_FEATURE_NAMES,
    VISUAL_REGULARIZATION,
    RUCA_REGULARIZATION,
    CONFERENCE_TEST_SIZE,
    CONFERENCE_SPLIT_SEED,
    SPATIAL_CV_N_GROUPS,
    SPATIAL_GROUPING_METHOD,
)
from src.utils.helpers import load_parquet, save_csv, ensure_dir
from src.utils.acs_data import ACS_FEATURE_NAMES
from src.utils.spatial_cv import SpatialCVManager
from src.stages import s03_estimation

from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


def _get_one_hot_encoder() -> OneHotEncoder:
    """Build a version-safe one-hot encoder."""
    try:
        return OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown='ignore', sparse=False)


def _ensure_zip_str(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['zip'] = df['zip'].astype(str).str.zfill(5)
    return df


def _select_visual_features(df: pd.DataFrame) -> list:
    prefixed = [c for c in df.columns if c.startswith(('infrastructure_', 'color_'))]
    named = [c for c in VISUAL_FEATURE_NAMES if c in df.columns]
    return sorted(set(prefixed + named))


def _compute_spatial_groups(df: pd.DataFrame) -> np.ndarray:
    """Compute spatial groups using the configured method."""
    manager = SpatialCVManager(n_groups=SPATIAL_CV_N_GROUPS, method=SPATIAL_GROUPING_METHOD)

    if SPATIAL_GROUPING_METHOD == 'zip_digit':
        return manager.create_groups_from_zip_codes(df['zip'])

    if SPATIAL_GROUPING_METHOD in ('contiguity_queen', 'contiguity_rook'):
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
            raise ValueError(f"Missing {len(missing)} ZCTAs in shapefile")
        gdf = gdf.set_index('ZCTA5CE20').loc[zcta_list].reset_index()
        contiguity = SPATIAL_GROUPING_METHOD.replace('contiguity_', '')
        return manager.create_groups_from_geodata(gdf, contiguity=contiguity)

    if 'latitude' not in df.columns or 'longitude' not in df.columns:
        raise ValueError("Missing latitude/longitude for spatial grouping")
    return manager.create_groups_from_coordinates(
        df['latitude'].values,
        df['longitude'].values,
    )


def _build_panel_from_features(linked_df: pd.DataFrame, features_df: pd.DataFrame) -> pd.DataFrame:
    feature_cols = _select_visual_features(features_df)
    features_clean = features_df[['zip'] + feature_cols].copy()
    merged = linked_df.merge(features_clean, on='zip', how='left')
    return merged


def _make_zip_split(zips: pd.Series) -> tuple[set, set]:
    zips = pd.Series(zips).astype(str).str.zfill(5).unique()
    train_zips, test_zips = train_test_split(
        zips,
        test_size=CONFERENCE_TEST_SIZE,
        random_state=CONFERENCE_SPLIT_SEED,
        shuffle=True,
    )
    return set(train_zips), set(test_zips)


def _split_by_zip(df: pd.DataFrame, train_zips: set, test_zips: set, feature_cols: list):
    df = df.copy()
    df = df.dropna(subset=[OUTCOME_VAR])
    train_mask = df['zip'].isin(train_zips)
    test_mask = df['zip'].isin(test_zips)

    X_train = df.loc[train_mask, feature_cols]
    X_test = df.loc[test_mask, feature_cols]
    y_train = df.loc[train_mask, OUTCOME_VAR]
    y_test = df.loc[test_mask, OUTCOME_VAR]

    return X_train, X_test, y_train, y_test


def run_holdout_acs_baselines(panel_df: pd.DataFrame, train_zips: set, test_zips: set) -> pd.DataFrame:
    """Run ACS/RUCA baselines on the fixed holdout split."""
    acs_path = DATA_RAW_DIR / 'acs' / 'acs_features.csv'
    if not acs_path.exists():
        print(f"   ACS data missing: {acs_path}")
        return pd.DataFrame()

    acs_df = pd.read_csv(acs_path)
    acs_df['zip'] = acs_df['zip'].astype(str).str.zfill(5)

    panel_df = _ensure_zip_str(panel_df)
    merged = panel_df.merge(acs_df, on='zip', how='left')

    available_acs = [c for c in ACS_FEATURE_NAMES if c in merged.columns]
    if not available_acs:
        print("   No ACS feature columns found after merge.")
        return pd.DataFrame()

    valid_mask = merged[available_acs].notna().all(axis=1)
    merged = merged.loc[valid_mask].copy()

    results = []

    # RUCA categorical baseline on ACS-complete sample
    ruca_model = make_pipeline(
        _get_one_hot_encoder(),
        Ridge(alpha=RUCA_REGULARIZATION),
    )
    X_train, X_test, y_train, y_test = _split_by_zip(
        merged, train_zips, test_zips, [TREATMENT_VAR]
    )
    results.append(
        s03_estimation._run_holdout_model(
            'ruca_categorical_holdout',
            ruca_model,
            X_train, X_test,
            y_train, y_test,
            feature_set='ruca_only',
            data_source='panel_acs',
            extra={'sample': 'acs_complete'},
        )
    )

    # ACS-only baseline
    acs_model = make_pipeline(
        StandardScaler(),
        Ridge(alpha=RUCA_REGULARIZATION),
    )
    X_train, X_test, y_train, y_test = _split_by_zip(
        merged, train_zips, test_zips, available_acs
    )
    results.append(
        s03_estimation._run_holdout_model(
            'acs_only_holdout',
            acs_model,
            X_train, X_test,
            y_train, y_test,
            feature_set='acs_only',
            data_source='panel_acs',
            extra={'sample': 'acs_complete', 'n_features': len(available_acs)},
        )
    )

    # ACS + RUCA combined
    combined_cols = [TREATMENT_VAR] + available_acs
    ruca_idx = [0]
    acs_idx = list(range(1, len(available_acs) + 1))
    combined_preprocessor = ColumnTransformer(
        transformers=[
            ('ruca', _get_one_hot_encoder(), ruca_idx),
            ('acs', StandardScaler(), acs_idx),
        ],
        remainder='drop',
    )
    combined_model = Pipeline([
        ('prep', combined_preprocessor),
        ('model', Ridge(alpha=RUCA_REGULARIZATION)),
    ])

    X_train, X_test, y_train, y_test = _split_by_zip(
        merged, train_zips, test_zips, combined_cols
    )
    results.append(
        s03_estimation._run_holdout_model(
            'acs_plus_ruca_holdout',
            combined_model,
            X_train, X_test,
            y_train, y_test,
            feature_set='acs_plus_ruca',
            data_source='panel_acs',
            extra={'sample': 'acs_complete', 'n_features': len(available_acs) + 1},
        )
    )

    return pd.DataFrame(results)


def run_coordinate_baselines(panel_df: pd.DataFrame, train_zips: set, test_zips: set) -> pd.DataFrame:
    """Run coordinate-only baselines (holdout + spatial CV)."""
    coord_cols = ['latitude', 'longitude']
    missing = [c for c in coord_cols if c not in panel_df.columns]
    if missing:
        print(f"   Missing coordinate columns: {missing}")
        return pd.DataFrame()

    panel_df = _ensure_zip_str(panel_df)
    panel_df = panel_df.dropna(subset=[OUTCOME_VAR])

    results = []
    coord_model = make_pipeline(
        StandardScaler(),
        Ridge(alpha=RUCA_REGULARIZATION),
    )

    # Holdout (lat/long)
    X_train, X_test, y_train, y_test = _split_by_zip(
        panel_df, train_zips, test_zips, coord_cols
    )
    results.append(
        s03_estimation._run_holdout_model(
            'coords_latlon_holdout',
            coord_model,
            X_train, X_test,
            y_train, y_test,
            feature_set='coords_latlon',
            data_source='panel',
        )
    )

    # Holdout (longitude only)
    X_train, X_test, y_train, y_test = _split_by_zip(
        panel_df, train_zips, test_zips, ['longitude']
    )
    results.append(
        s03_estimation._run_holdout_model(
            'coords_longitude_holdout',
            coord_model,
            X_train, X_test,
            y_train, y_test,
            feature_set='coords_longitude',
            data_source='panel',
        )
    )

    # Spatial CV (lat/long)
    groups = _compute_spatial_groups(panel_df)
    X = panel_df[coord_cols].values
    y = panel_df[OUTCOME_VAR].values
    manager = SpatialCVManager(n_groups=SPATIAL_CV_N_GROUPS)
    manager.spatial_groups = groups
    cv_results = manager.cross_validate(coord_model, X, y, scale_features=False)
    results.append({
        'specification': 'coords_latlon_spatial_cv',
        'feature_set': 'coords_latlon',
        'data_source': 'panel',
        'n_features': len(coord_cols),
        'n_samples': len(y),
        'cv_r2_mean': cv_results['mean'],
        'cv_r2_std': cv_results['std'],
    })

    # Spatial CV (longitude only)
    X_lon = panel_df[['longitude']].values
    cv_lon = manager.cross_validate(coord_model, X_lon, y, scale_features=False)
    results.append({
        'specification': 'coords_longitude_spatial_cv',
        'feature_set': 'coords_longitude',
        'data_source': 'panel',
        'n_features': 1,
        'n_samples': len(y),
        'cv_r2_mean': cv_lon['mean'],
        'cv_r2_std': cv_lon['std'],
    })

    return pd.DataFrame(results)


def run_fold_diagnostics(panel_df: pd.DataFrame) -> pd.DataFrame:
    """Compute fold-level diagnostics for the RUCA categorical model."""
    panel_df = panel_df.dropna(subset=[OUTCOME_VAR])
    groups = _compute_spatial_groups(panel_df)
    y = panel_df[OUTCOME_VAR].values
    X_ruca = panel_df[[TREATMENT_VAR]].values

    manager = SpatialCVManager(n_groups=SPATIAL_CV_N_GROUPS)
    manager.spatial_groups = groups

    model = make_pipeline(
        _get_one_hot_encoder(),
        Ridge(alpha=RUCA_REGULARIZATION),
    )

    records = []
    for train_idx, test_idx in manager.split(X_ruca, y):
        group_ids = np.unique(groups[test_idx])
        if len(group_ids) != 1:
            fold_id = int(group_ids[0])
        else:
            fold_id = int(group_ids[0])

        X_train, X_test = X_ruca[train_idx], X_ruca[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        bias = float(np.mean(y_pred - y_test))

        fold_df = panel_df.iloc[test_idx]
        records.append({
            'fold': fold_id + 1,
            'n_zctas': len(test_idx),
            'broadband_mean': float(np.mean(y_test)),
            'broadband_std': float(np.std(y_test)),
            'pred_mean': float(np.mean(y_pred)),
            'pred_std': float(np.std(y_pred)),
            'bias': bias,
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'ruca_1_3': int((fold_df[TREATMENT_VAR] <= 3).sum()),
            'ruca_4_6': int(((fold_df[TREATMENT_VAR] >= 4) & (fold_df[TREATMENT_VAR] <= 6)).sum()),
            'ruca_7_9': int(((fold_df[TREATMENT_VAR] >= 7) & (fold_df[TREATMENT_VAR] <= 9)).sum()),
            'ruca_10': int((fold_df[TREATMENT_VAR] == 10).sum()),
        })

    return pd.DataFrame(records)


def run_cap_sensitivity_holdout(linked_df: pd.DataFrame, train_zips: set, test_zips: set) -> pd.DataFrame:
    """Compute visual-only holdout metrics across image caps."""
    cap_root = DIAGNOSTICS_DIR / 'cap_sensitivity'
    if not cap_root.exists():
        print("   Cap sensitivity diagnostics not found.")
        return pd.DataFrame()

    linked_df = _ensure_zip_str(linked_df)

    results = []
    for cap_dir in sorted(cap_root.glob('max_images_*')):
        metadata_path = cap_dir / 'run_metadata.json'
        if not metadata_path.exists():
            continue

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        features_path = Path(metadata.get('features_file', ''))
        if not features_path.exists():
            print(f"   Missing features file for {cap_dir.name}: {features_path}")
            continue

        features_df = pd.read_csv(features_path)
        features_df['zip'] = features_df['zip'].astype(str).str.zfill(5)
        panel = _build_panel_from_features(linked_df, features_df)

        visual_features = _select_visual_features(panel)
        if not visual_features:
            continue

        panel = panel.dropna(subset=[OUTCOME_VAR])
        spatial_groups = _compute_spatial_groups(panel)

        X_train, X_test, y_train, y_test = _split_by_zip(
            panel, train_zips, test_zips, visual_features
        )
        visual_model = make_pipeline(
            StandardScaler(),
            Ridge(alpha=VISUAL_REGULARIZATION),
        )

        result = s03_estimation._run_holdout_model(
            'visual_only_holdout',
            visual_model,
            X_train, X_test,
            y_train, y_test,
            feature_set='visual_only',
            data_source='cap_sensitivity',
            extra={
                'max_images': metadata.get('label', cap_dir.name.replace('max_images_', '')),
                'features_file': str(features_path),
            },
        )

        X_all = panel[visual_features].fillna(0).values
        y_all = panel[OUTCOME_VAR].values
        valid_mask = ~np.isnan(y_all)
        manager = SpatialCVManager(n_groups=SPATIAL_CV_N_GROUPS)
        manager.spatial_groups = spatial_groups[valid_mask]
        cv_result = manager.cross_validate(
            Ridge(alpha=VISUAL_REGULARIZATION),
            X_all[valid_mask],
            y_all[valid_mask],
            scale_features=True,
        )
        result['spatial_cv_mean'] = cv_result['mean']
        result['spatial_cv_std'] = cv_result['std']
        results.append(result)

    return pd.DataFrame(results)


def build_cap_sensitivity_summary(holdout_df: pd.DataFrame) -> pd.DataFrame:
    """Join holdout metrics with spatial CV metrics from cap_sensitivity."""
    if holdout_df.empty:
        return pd.DataFrame()
    return holdout_df.copy()


def main() -> int:
    print("=" * 70)
    print("STAGE 07: ANALYSIS ADD-ONS")
    print("=" * 70)

    try:
        out_dir = DIAGNOSTICS_DIR / 'analysis_addons'
        ensure_dir(out_dir)

        print("\n📂 Loading panel data...")
        panel_path = DATA_WORK_DIR / 'panel.parquet'
        linked_path = DATA_WORK_DIR / 'data_linked.parquet'
        if not panel_path.exists() or not linked_path.exists():
            raise FileNotFoundError("Required panel or linked data missing. Run stages 01-02 first.")

        panel_df = load_parquet(panel_path)
        linked_df = load_parquet(linked_path)

        train_zips, test_zips = _make_zip_split(linked_df['zip'])

        if 'has_images' in linked_df.columns:
            linked_img = linked_df[linked_df['has_images']].copy()
            train_zips_img, test_zips_img = _make_zip_split(linked_img['zip'])
        else:
            linked_img = linked_df
            train_zips_img, test_zips_img = train_zips, test_zips

        if 'has_images' in panel_df.columns:
            panel_img = panel_df[panel_df['has_images']].copy()
        else:
            panel_img = panel_df

        # Holdout baselines (ACS/RUCA)
        print("\n📊 Running holdout baselines (ACS/RUCA)...")
        holdout_acs = run_holdout_acs_baselines(panel_df, train_zips, test_zips)
        if not holdout_acs.empty:
            save_csv(holdout_acs, out_dir / 'holdout_acs_baselines.csv')

        # Coordinate baselines
        print("\n📍 Running coordinate baselines...")
        coord_results = run_coordinate_baselines(panel_img, train_zips_img, test_zips_img)
        if not coord_results.empty:
            save_csv(coord_results, out_dir / 'coordinate_baselines.csv')

        # Fold diagnostics
        print("\n🧭 Computing fold-wise diagnostics...")
        fold_diag = run_fold_diagnostics(panel_img)
        if not fold_diag.empty:
            save_csv(fold_diag, out_dir / 'fold_diagnostics.csv')

        # Cap sensitivity holdout
        print("\n🖼️  Running image-count holdout sensitivity...")
        cap_holdout = run_cap_sensitivity_holdout(linked_img, train_zips_img, test_zips_img)
        if not cap_holdout.empty:
            save_csv(cap_holdout, out_dir / 'cap_sensitivity_holdout.csv')

            summary = build_cap_sensitivity_summary(cap_holdout)
            if not summary.empty:
                save_csv(summary, out_dir / 'cap_sensitivity_summary.csv')

        metadata = {
            'panel_path': str(panel_path),
            'linked_path': str(linked_path),
            'test_size': CONFERENCE_TEST_SIZE,
            'split_seed': CONFERENCE_SPLIT_SEED,
            'outputs': [
                str(out_dir / 'holdout_acs_baselines.csv'),
                str(out_dir / 'coordinate_baselines.csv'),
                str(out_dir / 'fold_diagnostics.csv'),
                str(out_dir / 'cap_sensitivity_holdout.csv'),
                str(out_dir / 'cap_sensitivity_summary.csv'),
            ],
        }
        with open(out_dir / 'run_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)

        print("\n✅ Stage 07 complete!")
        return 0

    except Exception as exc:
        print(f"\n❌ Stage 07 failed: {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
