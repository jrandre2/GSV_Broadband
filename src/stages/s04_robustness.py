"""
Stage 04: Robustness Checks
===========================

Run robustness analyses:
- Spatial CV vs Random CV comparison (leakage quantification)
- RUCA encoding comparisons (categorical vs ordinal)
- Feature ablation studies

Input: data_work/panel.parquet
Output: data_work/diagnostics/robustness_results.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
from collections import Counter

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    DATA_WORK_DIR, DATA_RAW_DIR, DIAGNOSTICS_DIR,
    OUTCOME_VAR, TREATMENT_VAR, VISUAL_FEATURE_NAMES,
    INFRASTRUCTURE_FEATURES, COLOR_FEATURES,
    VISUAL_REGULARIZATION, RUCA_REGULARIZATION,
    SPATIAL_CV_N_GROUPS, REPEATED_CV_N_SPLITS, REPEATED_CV_N_REPEATS,
    TUNING_INNER_FOLDS, TUNING_RIDGE_ALPHAS,
    TUNING_ENET_ALPHAS, TUNING_ENET_L1_RATIOS,
    TUNING_RF_PARAMS, TUNING_ET_PARAMS, TUNING_GB_PARAMS,
    RANDOM_STATE, SPATIAL_SENSITIVITY_METHODS,
)

# ACS feature names
ACS_FEATURE_NAMES = [
    'acs_median_income',
    'acs_pct_65_plus',
    'acs_pct_bachelors_plus',
    'acs_pct_owner_occupied',
    'acs_log_population',
]
from src.utils.helpers import load_parquet, save_csv, ensure_dir
from src.utils.spatial_cv import SpatialCVManager

from sklearn.linear_model import Ridge, ElasticNet
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import (
    cross_val_score,
    RepeatedKFold,
    GroupKFold,
    GridSearchCV,
)
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.metrics import r2_score
from scipy.stats import spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.impute import SimpleImputer


def _get_one_hot_encoder() -> OneHotEncoder:
    """Build a version-safe one-hot encoder."""
    try:
        return OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown='ignore', sparse=False)


def get_visual_feature_cols(df: pd.DataFrame) -> list:
    """Detect visual feature columns from the panel."""
    prefixed = [c for c in df.columns if c.startswith(('infrastructure_', 'color_'))]
    named = [c for c in VISUAL_FEATURE_NAMES if c in df.columns]
    feature_cols = list(dict.fromkeys(prefixed + named))
    return feature_cols


def _compute_spatial_groups(df: pd.DataFrame, method: str) -> np.ndarray:
    """Compute spatial groups using the requested method."""
    manager = SpatialCVManager(n_groups=SPATIAL_CV_N_GROUPS, method=method)

    if method == 'zip_digit':
        return manager.create_groups_from_zip_codes(df['zip'])

    if method in ('contiguity_queen', 'contiguity_rook'):
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
        contiguity = method.replace('contiguity_', '')
        return manager.create_groups_from_geodata(gdf, contiguity=contiguity)

    if 'latitude' not in df.columns or 'longitude' not in df.columns:
        raise ValueError("Missing latitude/longitude for spatial grouping")
    return manager.create_groups_from_coordinates(
        df['latitude'].values,
        df['longitude'].values,
    )


def run_spatial_group_sensitivity(df: pd.DataFrame, methods: list) -> pd.DataFrame:
    """Evaluate spatial CV sensitivity across grouping definitions."""
    print("\n   Running Spatial Grouping Sensitivity...")

    all_results = []
    for method in methods:
        print(f"\n   Sensitivity method: {method}")
        groups = _compute_spatial_groups(df, method)

        cv_result = compare_spatial_vs_random_cv(df, groups)
        if cv_result:
            cv_result['spatial_grouping_method'] = method
            all_results.append(cv_result)

        ruca_results = test_ruca_encodings(df, groups)
        for res in ruca_results:
            res['spatial_grouping_method'] = method
        all_results.extend(ruca_results)

        group_mean = test_ruca_group_mean_baseline(df, groups)
        if group_mean:
            group_mean['spatial_grouping_method'] = method
            all_results.append(group_mean)

        combined = run_combined_spatial_cv(df, groups)
        for res in combined:
            res['spatial_grouping_method'] = method
        all_results.extend(combined)

        late_fusion = run_late_fusion_spatial_cv(df, groups)
        if late_fusion:
            late_fusion['spatial_grouping_method'] = method
            all_results.append(late_fusion)

    results_df = pd.DataFrame(all_results)
    out_dir = DIAGNOSTICS_DIR / 'spatial_sensitivity'
    ensure_dir(out_dir)
    save_csv(results_df, out_dir / 'robustness_results.csv')

    keep_tests = [
        'ruca_categorical',
        'ruca1_ruca2_categorical',
        'ruca_group_mean',
        'combined_two_stage_spatial_cv',
        'late_fusion_spatial_cv',
        'spatial_vs_random_cv',
    ]
    summary = results_df[results_df['test'].isin(keep_tests)].copy()
    save_csv(summary, out_dir / 'spatial_sensitivity_summary.csv')

    return results_df


def _summarize_best_params(params_list: list) -> dict:
    """Summarize best params across outer folds."""
    if not params_list:
        return {}
    counts = Counter(tuple(sorted(params.items())) for params in params_list)
    best_items, best_count = counts.most_common(1)[0]
    return {
        'mode_params': dict(best_items),
        'mode_count': best_count,
        'n_folds': len(params_list),
    }


def _slice_rows(X, idx: np.ndarray):
    """Slice rows for numpy arrays or pandas DataFrames."""
    if hasattr(X, 'iloc'):
        return X.iloc[idx]
    return X[idx]


def _fit_group_grid_search(
    model,
    param_grid: dict,
    X_train: np.ndarray,
    y_train: np.ndarray,
    groups_train: np.ndarray,
):
    """Fit GridSearchCV with GroupKFold when possible."""
    unique_groups = np.unique(groups_train)
    if len(unique_groups) < 2:
        inner_cv = RepeatedKFold(n_splits=2, n_repeats=1, random_state=RANDOM_STATE)
        search = GridSearchCV(model, param_grid, cv=inner_cv, scoring='r2', n_jobs=-1)
        search.fit(X_train, y_train)
        return search

    inner_splits = min(TUNING_INNER_FOLDS, len(unique_groups))
    inner_cv = GroupKFold(n_splits=inner_splits)
    search = GridSearchCV(model, param_grid, cv=inner_cv, scoring='r2', n_jobs=-1)
    search.fit(X_train, y_train, groups=groups_train)
    return search


def _nested_group_tuning(
    model,
    param_grid: dict,
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    label: str,
) -> dict:
    """Run nested spatial CV with inner tuning."""
    outer_cv = GroupKFold(n_splits=SPATIAL_CV_N_GROUPS)
    scores = []
    best_params = []

    for train_idx, test_idx in outer_cv.split(X, y, groups=groups):
        X_train = _slice_rows(X, train_idx)
        X_test = _slice_rows(X, test_idx)
        y_train, y_test = y[train_idx], y[test_idx]
        groups_train = groups[train_idx]

        search = _fit_group_grid_search(model, param_grid, X_train, y_train, groups_train)
        best_model = search.best_estimator_
        y_pred = best_model.predict(X_test)

        scores.append(r2_score(y_test, y_pred))
        best_params.append(search.best_params_)

    summary = _summarize_best_params(best_params)
    result = {
        'test': label,
        'cv_r2_mean': float(np.mean(scores)),
        'cv_r2_std': float(np.std(scores)),
    }
    if summary:
        result['tuning_mode_params'] = json.dumps(summary['mode_params'], sort_keys=True)
        result['tuning_mode_count'] = summary['mode_count']
        result['tuning_outer_folds'] = summary['n_folds']

    return result


def _build_combined_preprocessor(visual_features: list, scale_visuals: bool = True) -> ColumnTransformer:
    """Create a preprocessing pipeline for one-stage combined models."""
    if scale_visuals:
        visual_transformer = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler()),
        ])
    else:
        visual_transformer = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
        ])
    return ColumnTransformer(
        [
            ('ruca', Pipeline([
                ('imputer', SimpleImputer(strategy='most_frequent')),
                ('onehot', _get_one_hot_encoder()),
            ]), [TREATMENT_VAR]),
            ('visual', visual_transformer, visual_features),
        ],
        remainder='drop',
    )


def compare_spatial_vs_random_cv(df: pd.DataFrame, spatial_groups: np.ndarray) -> dict:
    """Compare spatial CV to random CV to quantify leakage."""
    print("\n   Comparing Spatial vs Random CV...")

    visual_features = get_visual_feature_cols(df)
    if not visual_features:
        print("      Skipping: no visual feature columns detected.")
        return {}

    X = df[visual_features].fillna(0).values
    y = df[OUTCOME_VAR].values

    valid_mask = ~np.isnan(y)
    X = X[valid_mask]
    y = y[valid_mask]
    groups = spatial_groups[valid_mask]

    model = make_pipeline(
        StandardScaler(),
        Ridge(alpha=VISUAL_REGULARIZATION),
    )

    # Random CV
    random_scores = cross_val_score(model, X, y, cv=5, scoring='r2')

    # Spatial CV
    manager = SpatialCVManager(n_groups=SPATIAL_CV_N_GROUPS)
    manager.spatial_groups = groups
    spatial_results = manager.cross_validate(model, X, y, scale_features=False)

    leakage = np.mean(random_scores) - spatial_results['mean']

    result = {
        'test': 'spatial_vs_random_cv',
        'random_cv_mean': np.mean(random_scores),
        'random_cv_std': np.std(random_scores),
        'spatial_cv_mean': spatial_results['mean'],
        'spatial_cv_std': spatial_results['std'],
        'leakage': leakage,
        'leakage_pct': leakage / spatial_results['mean'] * 100 if spatial_results['mean'] != 0 else np.nan,
    }

    print(f"      Random CV:  {result['random_cv_mean']:.3f} ± {result['random_cv_std']:.3f}")
    print(f"      Spatial CV: {result['spatial_cv_mean']:.3f} ± {result['spatial_cv_std']:.3f}")
    print(f"      Leakage:    {result['leakage']:+.3f} ({result['leakage_pct']:.1f}%)")

    return result


def test_ruca_encodings(df: pd.DataFrame, spatial_groups: np.ndarray) -> list:
    """Test different RUCA encoding strategies."""
    print("\n   Testing RUCA Encoding Strategies...")

    y_all = df[OUTCOME_VAR].values
    valid_mask = ~np.isnan(y_all)
    y = y_all[valid_mask]
    groups = spatial_groups[valid_mask]

    results = []
    manager = SpatialCVManager(n_groups=SPATIAL_CV_N_GROUPS)
    manager.spatial_groups = groups
    model = Ridge(alpha=RUCA_REGULARIZATION)

    # 1. Ordinal encoding (1-10)
    X_ordinal = df[[TREATMENT_VAR]].values[valid_mask]
    cv_ordinal = manager.cross_validate(model, X_ordinal, y)
    results.append({
        'test': 'ruca_ordinal',
        'cv_r2_mean': cv_ordinal['mean'],
        'cv_r2_std': cv_ordinal['std'],
    })
    print(f"      Ordinal:     {cv_ordinal['mean']:.3f} ± {cv_ordinal['std']:.3f}")

    # 2. Categorical (one-hot) encoding
    cat_model = make_pipeline(
        _get_one_hot_encoder(),
        Ridge(alpha=RUCA_REGULARIZATION),
    )
    cv_cat = manager.cross_validate(cat_model, X_ordinal, y, scale_features=False)
    results.append({
        'test': 'ruca_categorical',
        'cv_r2_mean': cv_cat['mean'],
        'cv_r2_std': cv_cat['std'],
    })
    print(f"      Categorical: {cv_cat['mean']:.3f} ± {cv_cat['std']:.3f}")

    # 3. Grouped (metro/micro/small/rural)
    ruca_grouped = pd.cut(df[TREATMENT_VAR], bins=[0, 3, 6, 9, 10],
                          labels=['metro', 'micro', 'small', 'rural'])
    X_grouped = ruca_grouped.values.reshape(-1, 1)[valid_mask]
    grouped_model = make_pipeline(
        _get_one_hot_encoder(),
        Ridge(alpha=RUCA_REGULARIZATION),
    )
    cv_grouped = manager.cross_validate(grouped_model, X_grouped, y, scale_features=False)
    results.append({
        'test': 'ruca_grouped',
        'cv_r2_mean': cv_grouped['mean'],
        'cv_r2_std': cv_grouped['std'],
    })
    print(f"      Grouped:     {cv_grouped['mean']:.3f} ± {cv_grouped['std']:.3f}")

    # 4. Secondary RUCA2 (ordinal) and RUCA1+RUCA2 (categorical)
    if 'RUCA2' in df.columns:
        ruca2 = df['RUCA2'].values
        valid_ruca2 = valid_mask & ~np.isnan(ruca2)
        if valid_ruca2.any():
            y_ruca2 = y_all[valid_ruca2]
            groups_ruca2 = spatial_groups[valid_ruca2]
            X_ruca2 = ruca2[valid_ruca2].reshape(-1, 1)

            manager2 = SpatialCVManager(n_groups=SPATIAL_CV_N_GROUPS)
            manager2.spatial_groups = groups_ruca2
            cv_ruca2 = manager2.cross_validate(model, X_ruca2, y_ruca2)
            results.append({
                'test': 'ruca2_ordinal',
                'cv_r2_mean': cv_ruca2['mean'],
                'cv_r2_std': cv_ruca2['std'],
            })
            print(f"      RUCA2 Ordinal: {cv_ruca2['mean']:.3f} ± {cv_ruca2['std']:.3f}")

            X_both = df[[TREATMENT_VAR, 'RUCA2']].values[valid_ruca2]
            both_model = make_pipeline(
                _get_one_hot_encoder(),
                Ridge(alpha=RUCA_REGULARIZATION),
            )
            cv_both = manager2.cross_validate(both_model, X_both, y_ruca2, scale_features=False)
            results.append({
                'test': 'ruca1_ruca2_categorical',
                'cv_r2_mean': cv_both['mean'],
                'cv_r2_std': cv_both['std'],
            })
            print(f"      RUCA1+RUCA2:  {cv_both['mean']:.3f} ± {cv_both['std']:.3f}")

    return results


def test_ruca_group_mean_baseline(df: pd.DataFrame, spatial_groups: np.ndarray) -> dict:
    """Evaluate a RUCA group-mean baseline under spatial CV."""
    print("\n   Testing RUCA Group-Mean Baseline...")

    y_all = df[OUTCOME_VAR].values
    ruca = df[TREATMENT_VAR].values
    valid_mask = ~np.isnan(y_all)
    y = y_all[valid_mask]
    ruca = ruca[valid_mask]
    groups = spatial_groups[valid_mask]

    manager = SpatialCVManager(n_groups=SPATIAL_CV_N_GROUPS)
    manager.spatial_groups = groups

    scores = []
    for train_idx, test_idx in manager.split(ruca, y):
        y_train = y[train_idx]
        ruca_train = ruca[train_idx]
        ruca_test = ruca[test_idx]

        means = {}
        for code in np.unique(ruca_train):
            means[code] = float(np.mean(y_train[ruca_train == code]))
        fallback = float(np.mean(y_train))
        y_pred = np.array([means.get(code, fallback) for code in ruca_test])
        scores.append(r2_score(y[test_idx], y_pred))

    result = {
        'test': 'ruca_group_mean',
        'cv_r2_mean': float(np.mean(scores)),
        'cv_r2_std': float(np.std(scores)),
    }
    print(f"      Group-mean: {result['cv_r2_mean']:.3f} ± {result['cv_r2_std']:.3f}")
    return result


def run_late_fusion_spatial_cv(df: pd.DataFrame, spatial_groups: np.ndarray) -> dict:
    """Late-fusion (stacked) model using RUCA-only and visual-only predictions."""
    print("\n   Running Late-Fusion Spatial CV...")

    visual_features = get_visual_feature_cols(df)
    if not visual_features:
        print("      Skipping: no visual feature columns detected.")
        return {}

    y_all = df[OUTCOME_VAR].values
    valid_mask = ~np.isnan(y_all)
    y = y_all[valid_mask]
    groups = spatial_groups[valid_mask]

    X_ruca = df[[TREATMENT_VAR]].values[valid_mask]
    X_visual = df[visual_features].fillna(0).values[valid_mask]

    manager = SpatialCVManager(n_groups=SPATIAL_CV_N_GROUPS)
    manager.spatial_groups = groups

    scores = []
    for train_idx, test_idx in manager.split(X_ruca, y):
        X_ruca_train = X_ruca[train_idx]
        X_ruca_test = X_ruca[test_idx]
        X_visual_train = X_visual[train_idx]
        X_visual_test = X_visual[test_idx]
        y_train = y[train_idx]
        y_test = y[test_idx]

        ruca_model = make_pipeline(
            _get_one_hot_encoder(),
            Ridge(alpha=RUCA_REGULARIZATION),
        )
        visual_model = make_pipeline(
            StandardScaler(),
            Ridge(alpha=VISUAL_REGULARIZATION),
        )
        ruca_model.fit(X_ruca_train, y_train)
        visual_model.fit(X_visual_train, y_train)

        train_preds = np.column_stack([
            ruca_model.predict(X_ruca_train),
            visual_model.predict(X_visual_train),
        ])
        test_preds = np.column_stack([
            ruca_model.predict(X_ruca_test),
            visual_model.predict(X_visual_test),
        ])

        meta_model = Ridge(alpha=1.0)
        meta_model.fit(train_preds, y_train)
        y_pred = meta_model.predict(test_preds)
        scores.append(r2_score(y_test, y_pred))

    result = {
        'test': 'late_fusion_spatial_cv',
        'cv_r2_mean': float(np.mean(scores)),
        'cv_r2_std': float(np.std(scores)),
    }
    print(f"      Late-fusion: {result['cv_r2_mean']:.3f} ± {result['cv_r2_std']:.3f}")
    return result


def load_acs_features() -> pd.DataFrame:
    """Load ACS features from data_raw/acs/acs_features.csv."""
    acs_path = DATA_RAW_DIR / 'acs' / 'acs_features.csv'
    if not acs_path.exists():
        print(f"      ACS data not found at {acs_path}")
        return pd.DataFrame()
    df = pd.read_csv(acs_path)
    df['zip'] = df['zip'].astype(str).str.zfill(5)
    return df


def test_acs_baseline(df: pd.DataFrame, spatial_groups: np.ndarray) -> list:
    """Test ACS socioeconomic features as a baseline comparator to RUCA."""
    print("\n   Testing ACS Baseline...")

    acs_df = load_acs_features()
    if acs_df.empty:
        print("      Skipping: ACS data not available.")
        return []

    # Merge ACS with panel
    df = df.copy()
    df['zip'] = df['zip'].astype(str).str.zfill(5)
    merged = df.merge(acs_df, on='zip', how='left')

    # Check for available ACS features
    available_acs = [f for f in ACS_FEATURE_NAMES if f in merged.columns]
    if not available_acs:
        print("      Skipping: no ACS feature columns found after merge.")
        return []

    y_all = merged[OUTCOME_VAR].values
    valid_mask = ~np.isnan(y_all)

    # Also require non-null ACS values
    for f in available_acs:
        valid_mask &= ~merged[f].isna()

    if valid_mask.sum() < 50:
        print(f"      Skipping: insufficient valid rows ({valid_mask.sum()}).")
        return []

    y = y_all[valid_mask]
    groups = spatial_groups[valid_mask]

    X_acs = merged[available_acs].values[valid_mask]
    X_ruca = merged[[TREATMENT_VAR]].values[valid_mask]

    results = []
    manager = SpatialCVManager(n_groups=SPATIAL_CV_N_GROUPS)
    manager.spatial_groups = groups

    # 1. ACS-only (continuous features, standardized)
    acs_model = make_pipeline(
        StandardScaler(),
        Ridge(alpha=RUCA_REGULARIZATION),
    )
    cv_acs = manager.cross_validate(acs_model, X_acs, y, scale_features=False)
    results.append({
        'test': 'acs_only',
        'cv_r2_mean': cv_acs['mean'],
        'cv_r2_std': cv_acs['std'],
        'n_features': len(available_acs),
    })
    print(f"      ACS-only ({len(available_acs)} features): {cv_acs['mean']:.3f} +/- {cv_acs['std']:.3f}")

    # 2. RUCA categorical (for comparison on same sample)
    ruca_model = make_pipeline(
        _get_one_hot_encoder(),
        Ridge(alpha=RUCA_REGULARIZATION),
    )
    cv_ruca = manager.cross_validate(ruca_model, X_ruca, y, scale_features=False)
    results.append({
        'test': 'acs_sample_ruca_categorical',
        'cv_r2_mean': cv_ruca['mean'],
        'cv_r2_std': cv_ruca['std'],
    })
    print(f"      RUCA categorical (ACS sample): {cv_ruca['mean']:.3f} +/- {cv_ruca['std']:.3f}")

    # 3. ACS + RUCA combined
    X_combined = np.column_stack([X_ruca, X_acs])
    combined_preprocessor = ColumnTransformer(
        [
            ('ruca', _get_one_hot_encoder(), [0]),
            ('acs', StandardScaler(), list(range(1, len(available_acs) + 1))),
        ],
        remainder='drop',
    )
    combined_model = Pipeline([
        ('prep', combined_preprocessor),
        ('model', Ridge(alpha=RUCA_REGULARIZATION)),
    ])
    cv_combined = manager.cross_validate(combined_model, X_combined, y, scale_features=False)
    results.append({
        'test': 'acs_plus_ruca',
        'cv_r2_mean': cv_combined['mean'],
        'cv_r2_std': cv_combined['std'],
        'n_features': len(available_acs) + 1,
    })
    print(f"      ACS + RUCA: {cv_combined['mean']:.3f} +/- {cv_combined['std']:.3f}")

    return results


def run_block_diagnostics(df: pd.DataFrame) -> dict:
    """Compute block-level diagnostics for RUCA vs visual features."""
    print("\n   Running Block-Level Diagnostics...")

    visual_features = get_visual_feature_cols(df)
    if not visual_features:
        print("      Skipping: no visual feature columns detected.")
        return {}

    y = df[OUTCOME_VAR].values
    valid_mask = ~np.isnan(y)
    y = y[valid_mask]

    X_ruca = df[[TREATMENT_VAR]].values[valid_mask]
    X_visual = df[visual_features].fillna(0).values[valid_mask]

    ruca_model = make_pipeline(
        _get_one_hot_encoder(),
        Ridge(alpha=RUCA_REGULARIZATION),
    )
    visual_model = make_pipeline(
        StandardScaler(),
        Ridge(alpha=VISUAL_REGULARIZATION),
    )
    ruca_model.fit(X_ruca, y)
    visual_model.fit(X_visual, y)

    ruca_coefs = ruca_model.named_steps['ridge'].coef_
    visual_coefs = visual_model.named_steps['ridge'].coef_

    return {
        'test': 'combined_block_diagnostics',
        'ruca_coef_l2': float(np.linalg.norm(ruca_coefs)),
        'ruca_coef_l1': float(np.sum(np.abs(ruca_coefs))),
        'visual_coef_l2': float(np.linalg.norm(visual_coefs)),
        'visual_coef_l1': float(np.sum(np.abs(visual_coefs))),
    }

def run_feature_ablation(df: pd.DataFrame, spatial_groups: np.ndarray) -> list:
    """Run feature ablation studies."""
    print("\n   Running Feature Ablation...")

    visual_features = get_visual_feature_cols(df)
    if not visual_features:
        print("      Skipping: no visual feature columns detected.")
        return []

    y = df[OUTCOME_VAR].values
    valid_mask = ~np.isnan(y)
    y = y[valid_mask]
    groups = spatial_groups[valid_mask]

    results = []
    manager = SpatialCVManager(n_groups=SPATIAL_CV_N_GROUPS)
    manager.spatial_groups = groups
    model = make_pipeline(
        StandardScaler(),
        Ridge(alpha=VISUAL_REGULARIZATION),
    )

    # Define feature sets
    infra_features = list(dict.fromkeys(
        [c for c in INFRASTRUCTURE_FEATURES if c in visual_features]
        + [c for c in visual_features if c.startswith('infrastructure_')]
    ))
    color_features = list(dict.fromkeys(
        [c for c in COLOR_FEATURES if c in visual_features]
        + [c for c in visual_features if c.startswith('color_')]
    ))
    feature_sets = {
        'all_visual': visual_features,
        'infrastructure_only': infra_features,
        'color_only': color_features,
        'top_5': visual_features[:5],
        'top_10': visual_features[:10],
    }

    for name, features in feature_sets.items():
        # Handle missing features
        available = [f for f in features if f in df.columns]
        if not available:
            continue

        X = df[available].fillna(0).values[valid_mask]
        cv_result = manager.cross_validate(model, X, y, scale_features=False)
        results.append({
            'test': f'ablation_{name}',
            'n_features': len(available),
            'cv_r2_mean': cv_result['mean'],
            'cv_r2_std': cv_result['std'],
        })
        print(f"      {name} ({len(available)} features): {cv_result['mean']:.3f} ± {cv_result['std']:.3f}")

    return results


def _two_stage_r2(
    X_ruca_train: np.ndarray,
    X_visual_train: np.ndarray,
    y_train: np.ndarray,
    X_ruca_test: np.ndarray,
    X_visual_test: np.ndarray,
    y_test: np.ndarray,
) -> float:
    """Compute R2 for a two-stage RUCA + visual residual model."""
    ruca_model = Ridge(alpha=RUCA_REGULARIZATION)
    ruca_model.fit(X_ruca_train, y_train)
    residuals = y_train - ruca_model.predict(X_ruca_train)

    scaler = StandardScaler()
    X_visual_train_scaled = scaler.fit_transform(X_visual_train)
    X_visual_test_scaled = scaler.transform(X_visual_test)

    visual_model = Ridge(alpha=VISUAL_REGULARIZATION)
    visual_model.fit(X_visual_train_scaled, residuals)

    preds = ruca_model.predict(X_ruca_test) + visual_model.predict(X_visual_test_scaled)
    return r2_score(y_test, preds)


def run_repeated_cv(df: pd.DataFrame) -> list:
    """Run repeated random CV for key specifications."""
    print("\n   Running Repeated Random CV...")

    results = []
    visual_features = get_visual_feature_cols(df)

    y = df[OUTCOME_VAR].values
    valid_mask = ~np.isnan(y)
    y = y[valid_mask]

    X_ruca = df[[TREATMENT_VAR]].values[valid_mask]
    X_visual = df[visual_features].fillna(0).values[valid_mask] if visual_features else None

    rkf = RepeatedKFold(
        n_splits=REPEATED_CV_N_SPLITS,
        n_repeats=REPEATED_CV_N_REPEATS,
        random_state=RANDOM_STATE,
    )

    # RUCA ordinal
    ordinal_scores = cross_val_score(
        Ridge(alpha=RUCA_REGULARIZATION),
        X_ruca,
        y,
        cv=rkf,
        scoring='r2',
    )
    results.append({
        'test': 'repeated_cv_ruca_ordinal',
        'cv_r2_mean': np.mean(ordinal_scores),
        'cv_r2_std': np.std(ordinal_scores),
        'n_splits': REPEATED_CV_N_SPLITS,
        'n_repeats': REPEATED_CV_N_REPEATS,
    })
    print(f"      RUCA ordinal: {np.mean(ordinal_scores):.3f} ± {np.std(ordinal_scores):.3f}")

    # RUCA categorical (one-hot)
    cat_model = make_pipeline(
        _get_one_hot_encoder(),
        Ridge(alpha=RUCA_REGULARIZATION),
    )
    cat_scores = cross_val_score(
        cat_model,
        X_ruca,
        y,
        cv=rkf,
        scoring='r2',
    )
    results.append({
        'test': 'repeated_cv_ruca_categorical',
        'cv_r2_mean': np.mean(cat_scores),
        'cv_r2_std': np.std(cat_scores),
        'n_splits': REPEATED_CV_N_SPLITS,
        'n_repeats': REPEATED_CV_N_REPEATS,
    })
    print(f"      RUCA categorical: {np.mean(cat_scores):.3f} ± {np.std(cat_scores):.3f}")

    # Visual-only
    if X_visual is not None and X_visual.size:
        visual_model = make_pipeline(
            StandardScaler(),
            Ridge(alpha=VISUAL_REGULARIZATION),
        )
        visual_scores = cross_val_score(
            visual_model,
            X_visual,
            y,
            cv=rkf,
            scoring='r2',
        )
        results.append({
            'test': 'repeated_cv_visual_only',
            'cv_r2_mean': np.mean(visual_scores),
            'cv_r2_std': np.std(visual_scores),
            'n_splits': REPEATED_CV_N_SPLITS,
            'n_repeats': REPEATED_CV_N_REPEATS,
        })
        print(f"      Visual only: {np.mean(visual_scores):.3f} ± {np.std(visual_scores):.3f}")

        # Combined two-stage
        combined_scores = []
        for train_idx, test_idx in rkf.split(X_visual, y):
            r2 = _two_stage_r2(
                X_ruca[train_idx],
                X_visual[train_idx],
                y[train_idx],
                X_ruca[test_idx],
                X_visual[test_idx],
                y[test_idx],
            )
            combined_scores.append(r2)
        combined_scores = np.array(combined_scores)
        results.append({
            'test': 'repeated_cv_combined_two_stage',
            'cv_r2_mean': float(np.mean(combined_scores)),
            'cv_r2_std': float(np.std(combined_scores)),
            'n_splits': REPEATED_CV_N_SPLITS,
            'n_repeats': REPEATED_CV_N_REPEATS,
        })
        print(f"      Combined two-stage: {np.mean(combined_scores):.3f} ± {np.std(combined_scores):.3f}")
    else:
        print("      Skipping visual/combined repeated CV: no visual feature columns detected.")

    return results


def run_combined_spatial_cv(df: pd.DataFrame, spatial_groups: np.ndarray) -> list:
    """Run spatial CV for the two-stage combined model."""
    print("\n   Running Combined Two-Stage Spatial CV...")

    visual_features = get_visual_feature_cols(df)
    if not visual_features:
        print("      Skipping: no visual feature columns detected.")
        return []

    y = df[OUTCOME_VAR].values
    valid_mask = ~np.isnan(y)
    y = y[valid_mask]
    groups = spatial_groups[valid_mask]

    X_ruca = df[[TREATMENT_VAR]].values[valid_mask]
    X_visual = df[visual_features].fillna(0).values[valid_mask]

    gkf = GroupKFold(n_splits=SPATIAL_CV_N_GROUPS)
    scores = []
    for train_idx, test_idx in gkf.split(X_visual, y, groups=groups):
        scores.append(
            _two_stage_r2(
                X_ruca[train_idx],
                X_visual[train_idx],
                y[train_idx],
                X_ruca[test_idx],
                X_visual[test_idx],
                y[test_idx],
            )
        )

    scores = np.array(scores)
    result = {
        'test': 'combined_two_stage_spatial_cv',
        'cv_r2_mean': float(np.mean(scores)),
        'cv_r2_std': float(np.std(scores)),
    }
    print(f"      Combined two-stage spatial: {result['cv_r2_mean']:.3f} ± {result['cv_r2_std']:.3f}")
    return [result]


def run_tuned_models(df: pd.DataFrame, spatial_groups: np.ndarray) -> list:
    """Run nested spatial CV with hyperparameter tuning."""
    print("\n   Running Tuned Models (Nested Spatial CV)...")

    results = []
    visual_features = get_visual_feature_cols(df)

    y = df[OUTCOME_VAR].values
    valid_mask = ~np.isnan(y)
    y = y[valid_mask]
    groups = spatial_groups[valid_mask]

    X_ruca = df[[TREATMENT_VAR]].values[valid_mask]

    # RUCA ordinal ridge
    results.append(
        _nested_group_tuning(
            Ridge(),
            {'alpha': TUNING_RIDGE_ALPHAS},
            X_ruca,
            y,
            groups,
            label='tuned_ruca_ordinal_ridge',
        )
    )

    # RUCA categorical ridge
    results.append(
        _nested_group_tuning(
            make_pipeline(_get_one_hot_encoder(), Ridge()),
            {'ridge__alpha': TUNING_RIDGE_ALPHAS},
            X_ruca,
            y,
            groups,
            label='tuned_ruca_categorical_ridge',
        )
    )

    if not visual_features:
        print("      Skipping visual/combined tuning: no visual feature columns detected.")
        return results

    X_visual = df[visual_features].fillna(0).values[valid_mask]
    X_combined = df[[TREATMENT_VAR] + visual_features].iloc[np.where(valid_mask)[0]]

    # Visual ridge
    results.append(
        _nested_group_tuning(
            make_pipeline(StandardScaler(), Ridge()),
            {'ridge__alpha': TUNING_RIDGE_ALPHAS},
            X_visual,
            y,
            groups,
            label='tuned_visual_ridge',
        )
    )

    # Visual elastic net
    results.append(
        _nested_group_tuning(
            make_pipeline(StandardScaler(), ElasticNet(max_iter=10000, random_state=RANDOM_STATE)),
            {
                'elasticnet__alpha': TUNING_ENET_ALPHAS,
                'elasticnet__l1_ratio': TUNING_ENET_L1_RATIOS,
            },
            X_visual,
            y,
            groups,
            label='tuned_visual_elasticnet',
        )
    )

    # Combined one-stage ridge
    combined_preprocessor = _build_combined_preprocessor(visual_features, scale_visuals=True)
    results.append(
        _nested_group_tuning(
            Pipeline([
                ('prep', combined_preprocessor),
                ('model', Ridge()),
            ]),
            {'model__alpha': TUNING_RIDGE_ALPHAS},
            X_combined,
            y,
            groups,
            label='tuned_combined_one_stage_ridge',
        )
    )

    # Combined one-stage elastic net
    results.append(
        _nested_group_tuning(
            Pipeline([
                ('prep', combined_preprocessor),
                ('model', ElasticNet(max_iter=10000, random_state=RANDOM_STATE)),
            ]),
            {
                'model__alpha': TUNING_ENET_ALPHAS,
                'model__l1_ratio': TUNING_ENET_L1_RATIOS,
            },
            X_combined,
            y,
            groups,
            label='tuned_combined_one_stage_elasticnet',
        )
    )

    # Combined two-stage (tuned)
    outer_cv = GroupKFold(n_splits=SPATIAL_CV_N_GROUPS)
    combined_scores = []
    stage1_params = []
    stage2_params = []

    for train_idx, test_idx in outer_cv.split(X_visual, y, groups=groups):
        X_ruca_train, X_ruca_test = X_ruca[train_idx], X_ruca[test_idx]
        X_visual_train, X_visual_test = X_visual[train_idx], X_visual[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        groups_train = groups[train_idx]

        ruca_model = make_pipeline(_get_one_hot_encoder(), Ridge())
        ruca_search = _fit_group_grid_search(
            ruca_model,
            {'ridge__alpha': TUNING_RIDGE_ALPHAS},
            X_ruca_train,
            y_train,
            groups_train,
        )
        ruca_best = ruca_search.best_estimator_
        residuals = y_train - ruca_best.predict(X_ruca_train)
        stage1_params.append(ruca_search.best_params_)

        visual_model = make_pipeline(
            StandardScaler(),
            ElasticNet(max_iter=10000, random_state=RANDOM_STATE),
        )
        visual_search = _fit_group_grid_search(
            visual_model,
            {
                'elasticnet__alpha': TUNING_ENET_ALPHAS,
                'elasticnet__l1_ratio': TUNING_ENET_L1_RATIOS,
            },
            X_visual_train,
            residuals,
            groups_train,
        )
        visual_best = visual_search.best_estimator_
        stage2_params.append(visual_search.best_params_)

        preds = ruca_best.predict(X_ruca_test) + visual_best.predict(X_visual_test)
        combined_scores.append(r2_score(y_test, preds))

    stage1_summary = _summarize_best_params(stage1_params)
    stage2_summary = _summarize_best_params(stage2_params)
    combined_result = {
        'test': 'tuned_combined_two_stage',
        'cv_r2_mean': float(np.mean(combined_scores)),
        'cv_r2_std': float(np.std(combined_scores)),
    }
    if stage1_summary:
        combined_result['tuning_stage1_mode_params'] = json.dumps(
            stage1_summary['mode_params'], sort_keys=True
        )
        combined_result['tuning_stage1_mode_count'] = stage1_summary['mode_count']
    if stage2_summary:
        combined_result['tuning_stage2_mode_params'] = json.dumps(
            stage2_summary['mode_params'], sort_keys=True
        )
        combined_result['tuning_stage2_mode_count'] = stage2_summary['mode_count']
    combined_result['tuning_outer_folds'] = len(combined_scores)
    results.append(combined_result)

    return results


def run_tuned_tree_models(df: pd.DataFrame, spatial_groups: np.ndarray) -> list:
    """Run nested spatial CV for tuned tree ensembles."""
    print("\n   Running Tuned Tree Ensembles (Nested Spatial CV)...")

    results = []
    visual_features = get_visual_feature_cols(df)

    y = df[OUTCOME_VAR].values
    valid_mask = ~np.isnan(y)
    y = y[valid_mask]
    groups = spatial_groups[valid_mask]

    X_ruca = df[[TREATMENT_VAR]].values[valid_mask]

    tree_specs = [
        ('rf', RandomForestRegressor(random_state=RANDOM_STATE), TUNING_RF_PARAMS),
        ('extra_trees', ExtraTreesRegressor(random_state=RANDOM_STATE), TUNING_ET_PARAMS),
        ('gbrt', GradientBoostingRegressor(random_state=RANDOM_STATE), TUNING_GB_PARAMS),
    ]

    for prefix, base_model, param_grid in tree_specs:
        results.append(
            _nested_group_tuning(
                base_model,
                param_grid,
                X_ruca,
                y,
                groups,
                label=f'tuned_ruca_{prefix}',
            )
        )

    if not visual_features:
        print("      Skipping visual/combined tree tuning: no visual feature columns detected.")
        return results

    X_visual = df[visual_features].fillna(0).values[valid_mask]
    X_combined = df[[TREATMENT_VAR] + visual_features].iloc[np.where(valid_mask)[0]]
    combined_preprocessor = _build_combined_preprocessor(visual_features, scale_visuals=False)

    for prefix, base_model, param_grid in tree_specs:
        model_visual = type(base_model)(**base_model.get_params())
        results.append(
            _nested_group_tuning(
                model_visual,
                param_grid,
                X_visual,
                y,
                groups,
                label=f'tuned_visual_{prefix}',
            )
        )

        model_combined = type(base_model)(**base_model.get_params())
        results.append(
            _nested_group_tuning(
                Pipeline([
                    ('prep', combined_preprocessor),
                    ('model', model_combined),
                ]),
                {f'model__{k}': v for k, v in param_grid.items()},
                X_combined,
                y,
                groups,
                label=f'tuned_combined_one_stage_{prefix}',
            )
        )

    return results


def compute_fold_composition(df: pd.DataFrame, spatial_groups: np.ndarray) -> pd.DataFrame:
    """Compute fold composition statistics for spatial CV.

    Parameters
    ----------
    df : pd.DataFrame
        Panel data with OUTCOME_VAR and TREATMENT_VAR columns.
    spatial_groups : np.ndarray
        Spatial group assignments for each row.

    Returns
    -------
    pd.DataFrame
        DataFrame with fold-level statistics including n, broadband mean/std,
        and RUCA distribution.
    """
    print("\n   Computing Fold Composition...")

    df = df.copy()
    df['spatial_group'] = spatial_groups

    composition = []
    for fold in range(SPATIAL_CV_N_GROUPS):
        fold_mask = df['spatial_group'] == fold
        fold_df = df[fold_mask]

        composition.append({
            'fold': fold + 1,
            'n_zctas': len(fold_df),
            'broadband_mean': fold_df[OUTCOME_VAR].mean(),
            'broadband_std': fold_df[OUTCOME_VAR].std(),
            'ruca_1_3': (fold_df[TREATMENT_VAR] <= 3).sum(),  # Metro
            'ruca_4_6': ((fold_df[TREATMENT_VAR] >= 4) & (fold_df[TREATMENT_VAR] <= 6)).sum(),  # Micro
            'ruca_7_9': ((fold_df[TREATMENT_VAR] >= 7) & (fold_df[TREATMENT_VAR] <= 9)).sum(),  # Small town
            'ruca_10': (fold_df[TREATMENT_VAR] == 10).sum(),  # Rural
        })
        print(f"      Fold {fold + 1}: n={len(fold_df)}, "
              f"broadband={fold_df[OUTCOME_VAR].mean():.3f} ± {fold_df[OUTCOME_VAR].std():.3f}")

    return pd.DataFrame(composition)


def compute_policy_metrics(df: pd.DataFrame, spatial_groups: np.ndarray) -> list:
    """Compute policy-relevant metrics under spatial CV.

    Evaluates model performance for policy use cases:
    - Spearman rank correlation (ranking ability)
    - Precision@k for bottom quintile (triage)
    - Threshold classification (below median)

    Parameters
    ----------
    df : pd.DataFrame
        Panel data with OUTCOME_VAR and TREATMENT_VAR columns.
    spatial_groups : np.ndarray
        Spatial group assignments for each row.

    Returns
    -------
    list
        List of result dictionaries with policy metrics.
    """
    print("\n   Computing Policy-Relevant Metrics...")

    y_all = df[OUTCOME_VAR].values
    valid_mask = ~np.isnan(y_all)
    y = y_all[valid_mask]
    groups = spatial_groups[valid_mask]

    X_ruca = df[[TREATMENT_VAR]].values[valid_mask]

    results = []
    manager = SpatialCVManager(n_groups=SPATIAL_CV_N_GROUPS)
    manager.spatial_groups = groups

    # RUCA categorical model
    ruca_model = make_pipeline(
        _get_one_hot_encoder(),
        Ridge(alpha=RUCA_REGULARIZATION),
    )

    # Collect predictions across folds
    y_true_all = []
    y_pred_all = []

    for train_idx, test_idx in manager.split(X_ruca, y):
        X_train, X_test = X_ruca[train_idx], X_ruca[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        ruca_model.fit(X_train, y_train)
        y_pred = ruca_model.predict(X_test)

        y_true_all.extend(y_test)
        y_pred_all.extend(y_pred)

    y_true_all = np.array(y_true_all)
    y_pred_all = np.array(y_pred_all)

    # 1. Spearman rank correlation
    spearman_rho, spearman_p = spearmanr(y_true_all, y_pred_all)
    results.append({
        'test': 'policy_spearman_ruca',
        'spearman_rho': spearman_rho,
        'spearman_p': spearman_p,
    })
    print(f"      Spearman ρ (RUCA): {spearman_rho:.3f} (p={spearman_p:.3e})")

    # 2. Precision@k for bottom quintile (lowest 20% broadband)
    k = int(len(y_true_all) * 0.2)  # Bottom 20%
    actual_bottom_k = set(np.argsort(y_true_all)[:k])
    pred_bottom_k = set(np.argsort(y_pred_all)[:k])

    precision_at_k = len(actual_bottom_k & pred_bottom_k) / k
    recall_at_k = len(actual_bottom_k & pred_bottom_k) / len(actual_bottom_k)

    results.append({
        'test': 'policy_precision_at_20pct',
        'precision': precision_at_k,
        'recall': recall_at_k,
        'k': k,
    })
    print(f"      Precision@20% (bottom quintile): {precision_at_k:.3f}")
    print(f"      Recall@20%: {recall_at_k:.3f}")

    # 3. Threshold classification (below median = underserved)
    median_usage = np.median(y_true_all)
    actual_underserved = y_true_all < median_usage
    pred_underserved = y_pred_all < median_usage

    true_pos = np.sum(actual_underserved & pred_underserved)
    false_pos = np.sum(~actual_underserved & pred_underserved)
    false_neg = np.sum(actual_underserved & ~pred_underserved)
    true_neg = np.sum(~actual_underserved & ~pred_underserved)

    sensitivity = true_pos / (true_pos + false_neg) if (true_pos + false_neg) > 0 else 0
    specificity = true_neg / (true_neg + false_pos) if (true_neg + false_pos) > 0 else 0

    results.append({
        'test': 'policy_threshold_median',
        'sensitivity': sensitivity,
        'specificity': specificity,
        'threshold': median_usage,
    })
    print(f"      Threshold (below median): Sensitivity={sensitivity:.3f}, Specificity={specificity:.3f}")

    return results


def main(compare_cv: bool = True, spatial_sensitivity: bool = False) -> int:
    """Run Stage 04: Robustness Checks."""
    print("=" * 70)
    print("STAGE 04: ROBUSTNESS CHECKS")
    print("=" * 70)

    try:
        # Load panel data
        print("\n📂 Loading panel data...")
        input_path = DATA_WORK_DIR / 'panel.parquet'
        if not input_path.exists():
            raise FileNotFoundError(f"Input not found: {input_path}. Run stage 02 first.")
        panel_df = load_parquet(input_path)
        spatial_groups = panel_df['spatial_group'].values

        all_results = []

        # 1. Spatial vs Random CV comparison
        if compare_cv:
            cv_result = compare_spatial_vs_random_cv(panel_df, spatial_groups)
            if cv_result:
                all_results.append(cv_result)

        # 2. RUCA encoding tests
        ruca_results = test_ruca_encodings(panel_df, spatial_groups)
        all_results.extend(ruca_results)

        # 2b. RUCA group-mean baseline
        group_mean = test_ruca_group_mean_baseline(panel_df, spatial_groups)
        if group_mean:
            all_results.append(group_mean)

        # 3. Combined spatial CV (two-stage)
        combined_spatial = run_combined_spatial_cv(panel_df, spatial_groups)
        all_results.extend(combined_spatial)

        # 3b. Late-fusion stacked model
        late_fusion = run_late_fusion_spatial_cv(panel_df, spatial_groups)
        if late_fusion:
            all_results.append(late_fusion)

        # 4. Repeated random CV
        repeated_results = run_repeated_cv(panel_df)
        all_results.extend(repeated_results)

        # 5. Tuned models (nested spatial CV)
        tuned_results = run_tuned_models(panel_df, spatial_groups)
        all_results.extend(tuned_results)

        # 6. Tuned tree ensembles (nested spatial CV)
        tuned_tree_results = run_tuned_tree_models(panel_df, spatial_groups)
        all_results.extend(tuned_tree_results)

        # 7. Feature ablation
        ablation_results = run_feature_ablation(panel_df, spatial_groups)
        all_results.extend(ablation_results)

        # 8. Block-level diagnostics
        block_diag = run_block_diagnostics(panel_df)
        if block_diag:
            all_results.append(block_diag)

        # 9. ACS baseline comparison
        acs_results = test_acs_baseline(panel_df, spatial_groups)
        all_results.extend(acs_results)

        # 10. Fold composition (save to separate file)
        fold_composition = compute_fold_composition(panel_df, spatial_groups)
        save_csv(fold_composition, DIAGNOSTICS_DIR / 'fold_composition.csv')

        # 11. Policy-relevant metrics
        policy_results = compute_policy_metrics(panel_df, spatial_groups)
        all_results.extend(policy_results)

        # Save results
        print("\n💾 Saving robustness results...")
        results_df = pd.DataFrame(all_results)
        ensure_dir(DIAGNOSTICS_DIR)
        save_csv(results_df, DIAGNOSTICS_DIR / 'robustness_results.csv')

        # 12. Spatial grouping sensitivity
        if spatial_sensitivity:
            run_spatial_group_sensitivity(panel_df, SPATIAL_SENSITIVITY_METHODS)

        print("\n✅ Stage 04 complete!")
        return 0

    except Exception as e:
        print(f"\n❌ Stage 04 failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--compare-cv', action='store_true', default=True)
    parser.add_argument('--spatial-sensitivity', action='store_true', default=False,
                        help='Run sensitivity across spatial grouping methods')
    args = parser.parse_args()
    sys.exit(main(compare_cv=args.compare_cv, spatial_sensitivity=args.spatial_sensitivity))
