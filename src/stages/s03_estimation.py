"""
Stage 03: ML Model Estimation
=============================

Train machine learning models for broadband prediction:
- RUCA baseline (rural-urban typology only)
- Visual features only
- Combined two-stage model

Input: data_work/panel.parquet
Output: data_work/diagnostics/estimation_results.csv, data_work/models/
"""

import pandas as pd
import numpy as np
from pathlib import Path
import pickle
import sys
import json

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    DATA_WORK_DIR, DIAGNOSTICS_DIR, MODELS_DIR,
    OUTCOME_VAR, TREATMENT_VAR, VISUAL_FEATURE_NAMES,
    VISUAL_REGULARIZATION, RUCA_REGULARIZATION, RANDOM_STATE,
    LABELS_FILE, CONFERENCE_FEATURES_PATH, CONFERENCE_TEST_SIZE,
    CONFERENCE_SPLIT_SEED, ML_MODELS,
    TUNING_RF_PARAMS, TUNING_ET_PARAMS, TUNING_GB_PARAMS,
)
from src.utils.helpers import load_parquet, save_csv, ensure_dir, get_timestamp
from src.utils.spatial_cv import SpatialCVManager

from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.model_selection import train_test_split, GridSearchCV, KFold
from sklearn.linear_model import ElasticNet, LinearRegression
from sklearn.pipeline import make_pipeline


def get_visual_feature_cols(df: pd.DataFrame) -> list:
    """Detect visual feature columns from panel DataFrame."""
    prefixed = [c for c in df.columns if c.startswith(('infrastructure_', 'color_'))]
    named = [c for c in VISUAL_FEATURE_NAMES if c in df.columns]
    # Preserve order while avoiding duplicates.
    feature_cols = list(dict.fromkeys(prefixed + named))
    return feature_cols


def _get_one_hot_encoder() -> OneHotEncoder:
    """Build a version-safe one-hot encoder."""
    try:
        return OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown='ignore', sparse=False)


def get_specifications(df: pd.DataFrame) -> dict:
    """Get model specifications with detected feature columns."""
    visual_features = get_visual_feature_cols(df)

    return {
        'ruca_baseline': {
            'name': 'RUCA Baseline',
            'features': [TREATMENT_VAR],
            'model_class': Ridge,
            'model_params': {'alpha': RUCA_REGULARIZATION},
            'description': 'Rural-Urban typology only (baseline)',
        },
        'visual_only': {
            'name': 'Visual Features Only',
            'features': visual_features,
            'model_class': Ridge,
            'model_params': {'alpha': VISUAL_REGULARIZATION},
            'description': 'Computer vision features without RUCA',
        },
        'combined': {
            'name': 'Combined (Two-Stage)',
            'features': [TREATMENT_VAR] + visual_features,
            'model_class': Ridge,
            'model_params': {'alpha': VISUAL_REGULARIZATION},
            'two_stage': True,
            'description': 'RUCA baseline + visual residuals',
        },
        'random_forest': {
            'name': 'Random Forest',
            'features': visual_features,
            'model_class': RandomForestRegressor,
            'model_params': {'n_estimators': 100, 'random_state': RANDOM_STATE},
            'description': 'Random Forest on visual features',
        },
    }


def prepare_features(df: pd.DataFrame, feature_cols: list) -> np.ndarray:
    """Prepare feature matrix, handling missing values."""
    X = df[feature_cols].copy()
    X = X.fillna(0)
    return X.values


def _run_two_stage_cv(
    df: pd.DataFrame,
    visual_features: list,
    spatial_groups: np.ndarray,
) -> dict:
    """Run two-stage model with proper regularization for each stage.

    Stage 1: Fit RUCA with light regularization (α=1.0)
    Stage 2: Fit visual features on residuals with strong regularization (α=100)
    """
    from sklearn.model_selection import GroupKFold

    y = df[OUTCOME_VAR].values
    valid_mask = ~np.isnan(y)
    y = y[valid_mask]
    groups = spatial_groups[valid_mask]

    X_ruca = df[[TREATMENT_VAR]].values[valid_mask]
    X_visual = df[visual_features].fillna(0).values[valid_mask]

    gkf = GroupKFold(n_splits=5)
    scores = []

    for train_idx, test_idx in gkf.split(X_ruca, y, groups):
        # Stage 1: RUCA model
        ruca_model = Ridge(alpha=RUCA_REGULARIZATION)
        ruca_model.fit(X_ruca[train_idx], y[train_idx])
        residuals = y[train_idx] - ruca_model.predict(X_ruca[train_idx])

        # Stage 2: Visual model on residuals (with scaling)
        scaler = StandardScaler()
        X_visual_train_scaled = scaler.fit_transform(X_visual[train_idx])
        X_visual_test_scaled = scaler.transform(X_visual[test_idx])

        visual_model = Ridge(alpha=VISUAL_REGULARIZATION)
        visual_model.fit(X_visual_train_scaled, residuals)

        # Combined prediction
        preds = ruca_model.predict(X_ruca[test_idx]) + visual_model.predict(X_visual_test_scaled)
        scores.append(r2_score(y[test_idx], preds))

    return {'mean': np.mean(scores), 'std': np.std(scores)}


def run_specification(
    df: pd.DataFrame,
    spec_name: str,
    spec: dict,
    spatial_groups: np.ndarray,
) -> dict:
    """Run a single model specification with spatial CV."""
    print(f"\n   Running: {spec['name']}")

    # Check for two-stage specification
    if spec.get('two_stage', False):
        visual_features = get_visual_feature_cols(df)
        cv_results = _run_two_stage_cv(df, visual_features, spatial_groups)

        # Fit final two-stage model on all data
        y = df[OUTCOME_VAR].values
        valid_mask = ~np.isnan(y)
        y = y[valid_mask]

        X_ruca = df[[TREATMENT_VAR]].values[valid_mask]
        X_visual = df[visual_features].fillna(0).values[valid_mask]

        # Stage 1: RUCA
        ruca_model = Ridge(alpha=RUCA_REGULARIZATION)
        ruca_model.fit(X_ruca, y)
        residuals = y - ruca_model.predict(X_ruca)

        # Stage 2: Visual on residuals
        visual_scaler = StandardScaler()
        X_visual_scaled = visual_scaler.fit_transform(X_visual)
        visual_model = Ridge(alpha=VISUAL_REGULARIZATION)
        visual_model.fit(X_visual_scaled, residuals)

        y_pred = ruca_model.predict(X_ruca) + visual_model.predict(X_visual_scaled)
        train_r2 = r2_score(y, y_pred)

        # Store both models
        model = {'ruca_model': ruca_model, 'visual_model': visual_model}
        scaler = {'visual_scaler': visual_scaler}

        result = {
            'specification': spec_name,
            'name': spec['name'],
            'n_features': 1 + len(visual_features),
            'n_samples': len(y),
            'train_r2': train_r2,
            'cv_r2_mean': cv_results['mean'],
            'cv_r2_std': cv_results['std'],
            'rmse': np.sqrt(mean_squared_error(y, y_pred)),
            'mae': mean_absolute_error(y, y_pred),
        }

        print(f"      Train R²: {train_r2:.3f}")
        print(f"      CV R²:    {cv_results['mean']:.3f} ± {cv_results['std']:.3f}")

        return result, model, scaler

    # Standard single-model approach
    feature_cols = spec['features']
    X = prepare_features(df, feature_cols)
    y = df[OUTCOME_VAR].values

    # Handle missing outcome
    valid_mask = ~np.isnan(y)
    X = X[valid_mask]
    y = y[valid_mask]
    groups = spatial_groups[valid_mask]

    # Spatial cross-validation (scale within folds to avoid leakage)
    manager = SpatialCVManager(n_groups=5)
    manager.spatial_groups = groups

    cv_results = manager.cross_validate(
        spec['model_class'](**spec['model_params']),
        X, y,
        scale_features=True,
    )

    # Fit final model on all data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = spec['model_class'](**spec['model_params'])
    model.fit(X_scaled, y)
    y_pred = model.predict(X_scaled)
    train_r2 = r2_score(y, y_pred)

    result = {
        'specification': spec_name,
        'name': spec['name'],
        'n_features': len(feature_cols),
        'n_samples': len(y),
        'train_r2': train_r2,
        'cv_r2_mean': cv_results['mean'],
        'cv_r2_std': cv_results['std'],
        'rmse': np.sqrt(mean_squared_error(y, y_pred)),
        'mae': mean_absolute_error(y, y_pred),
    }

    print(f"      Train R²: {train_r2:.3f}")
    print(f"      CV R²:    {cv_results['mean']:.3f} ± {cv_results['std']:.3f}")

    return result, model, scaler


def save_model(model, scaler, spec_name: str, output_dir: Path):
    """Save trained model."""
    model_data = {
        'model': model,
        'scaler': scaler,
        'specification': spec_name,
    }
    output_path = output_dir / f'{spec_name}_model.pkl'
    with open(output_path, 'wb') as f:
        pickle.dump(model_data, f)
    return output_path


def _run_holdout_model(
    model_name: str,
    model,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    feature_set: str,
    data_source: str,
    extra: dict | None = None,
) -> dict:
    """Fit a model on a holdout split and return summary metrics."""
    model.fit(X_train, y_train)
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    n_features = X_train.shape[1]
    if hasattr(model, 'named_steps'):
        for step in model.named_steps.values():
            if hasattr(step, 'categories_'):
                n_features = int(sum(len(cats) for cats in step.categories_))
                break

    result = {
        'specification': model_name,
        'feature_set': feature_set,
        'data_source': data_source,
        'n_features': n_features,
        'n_samples': len(y_train) + len(y_test),
        'train_samples': len(y_train),
        'test_samples': len(y_test),
        'train_r2': r2_score(y_train, y_pred_train),
        'test_r2': r2_score(y_test, y_pred_test),
        'rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
        'mae': mean_absolute_error(y_test, y_pred_test),
    }
    if extra:
        result.update(extra)
    return result


def _tune_tree_model(model, param_grid: dict, X_train: pd.DataFrame, y_train: pd.Series):
    """Tune tree ensemble hyperparameters using CV on the training split."""
    n_splits = min(5, len(y_train))
    n_splits = max(2, n_splits)
    cv = KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    search = GridSearchCV(
        model,
        param_grid,
        cv=cv,
        scoring='r2',
        n_jobs=-1,
    )
    search.fit(X_train, y_train)
    return search.best_estimator_, search.best_params_


def _prepare_conference_split(df: pd.DataFrame, feature_cols: list, target_col: str) -> tuple:
    """Prepare a deterministic train/test split for conference reproduction."""
    X = df[feature_cols].fillna(0)
    y = df[target_col].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=CONFERENCE_TEST_SIZE, random_state=CONFERENCE_SPLIT_SEED
    )
    return X_train, X_test, y_train, y_test


def _load_conference_visual_features(precomputed_path: Path) -> pd.DataFrame:
    """Load precomputed visual features for the conference profile."""
    if not precomputed_path.exists():
        raise FileNotFoundError(f"Precomputed features not found: {precomputed_path}")
    df = pd.read_csv(precomputed_path)
    return df.dropna(subset=[OUTCOME_VAR])


def _load_conference_labels() -> pd.DataFrame:
    """Load broadband labels with RUCA codes for conference baselines."""
    if not LABELS_FILE.exists():
        raise FileNotFoundError(f"Labels file not found: {LABELS_FILE}")
    df = pd.read_csv(LABELS_FILE)
    return df.dropna(subset=[OUTCOME_VAR, TREATMENT_VAR])


def run_conference_estimation(precomputed_path: Path = CONFERENCE_FEATURES_PATH) -> int:
    """Run conference reproduction models using holdout evaluation."""
    print("=" * 70)
    print("STAGE 03: CONFERENCE REPRODUCTION")
    print("=" * 70)

    try:
        results = []

        # RUCA-only baselines (labels file)
        labels_df = _load_conference_labels()
        X_train, X_test, y_train, y_test = _prepare_conference_split(
            labels_df, [TREATMENT_VAR], OUTCOME_VAR
        )

        results.append(
            _run_holdout_model(
                'ruca_baseline_linear',
                LinearRegression(),
                X_train, X_test, y_train, y_test,
                feature_set='ruca_only',
                data_source='labels',
            )
        )
        results.append(
            _run_holdout_model(
                'ruca_baseline_one_hot',
                make_pipeline(
                    _get_one_hot_encoder(),
                    Ridge(alpha=RUCA_REGULARIZATION),
                ),
                X_train, X_test, y_train, y_test,
                feature_set='ruca_only',
                data_source='labels',
            )
        )

        ensemble_models = {
            'ruca_baseline_random_forest': RandomForestRegressor(
                n_estimators=ML_MODELS['random_forest']['n_estimators'],
                max_depth=ML_MODELS['random_forest']['max_depth'],
                random_state=ML_MODELS['random_forest']['random_state'],
            ),
            'ruca_baseline_extra_trees': ExtraTreesRegressor(
                n_estimators=ML_MODELS['extra_trees']['n_estimators'],
                max_depth=ML_MODELS['extra_trees']['max_depth'],
                random_state=ML_MODELS['extra_trees']['random_state'],
            ),
            'ruca_baseline_gradient_boosting': GradientBoostingRegressor(
                n_estimators=ML_MODELS['gradient_boosting']['n_estimators'],
                learning_rate=ML_MODELS['gradient_boosting']['learning_rate'],
                max_depth=ML_MODELS['gradient_boosting']['max_depth'],
                random_state=ML_MODELS['gradient_boosting']['random_state'],
            ),
        }

        for name, model in ensemble_models.items():
            results.append(
                _run_holdout_model(
                    name,
                    model,
                    X_train, X_test, y_train, y_test,
                    feature_set='ruca_only',
                    data_source='labels',
                )
            )

        tuned_tree_specs = {
            'random_forest': (RandomForestRegressor(random_state=RANDOM_STATE), TUNING_RF_PARAMS),
            'extra_trees': (ExtraTreesRegressor(random_state=RANDOM_STATE), TUNING_ET_PARAMS),
            'gradient_boosting': (GradientBoostingRegressor(random_state=RANDOM_STATE), TUNING_GB_PARAMS),
        }
        for name, (model, grid) in tuned_tree_specs.items():
            tuned_model, best_params = _tune_tree_model(model, grid, X_train, y_train)
            results.append(
                _run_holdout_model(
                    f'ruca_baseline_{name}_tuned',
                    tuned_model,
                    X_train, X_test, y_train, y_test,
                    feature_set='ruca_only',
                    data_source='labels',
                    extra={'tuning_params': json.dumps(best_params, sort_keys=True)},
                )
            )

        # Visual + Combined models (precomputed features)
        visual_df = _load_conference_visual_features(precomputed_path)
        if TREATMENT_VAR not in visual_df.columns:
            visual_df['zip'] = visual_df['zip'].astype(str)
            labels_df['zip'] = labels_df['zip'].astype(str)
            visual_df = visual_df.merge(
                labels_df[['zip', TREATMENT_VAR]],
                on='zip',
                how='left',
            ).dropna(subset=[TREATMENT_VAR])
        non_feature_cols = {
            'zip', OUTCOME_VAR, 'ookla_download_mbps', 'ookla_upload_mbps',
            'ZIP_CODE', 'RUCA1', 'RUCA2',
        }
        visual_cols = [c for c in visual_df.columns if c not in non_feature_cols]

        # Visual-only
        X_train_v, X_test_v, y_train_v, y_test_v = _prepare_conference_split(
            visual_df, visual_cols, OUTCOME_VAR
        )
        visual_models = {
            'visual_extra_trees': ExtraTreesRegressor(
                n_estimators=ML_MODELS['extra_trees']['n_estimators'],
                max_depth=ML_MODELS['extra_trees']['max_depth'],
                random_state=ML_MODELS['extra_trees']['random_state'],
            ),
            'visual_random_forest': RandomForestRegressor(
                n_estimators=ML_MODELS['random_forest']['n_estimators'],
                max_depth=ML_MODELS['random_forest']['max_depth'],
                random_state=ML_MODELS['random_forest']['random_state'],
            ),
            'visual_gradient_boosting': GradientBoostingRegressor(
                n_estimators=ML_MODELS['gradient_boosting']['n_estimators'],
                learning_rate=ML_MODELS['gradient_boosting']['learning_rate'],
                max_depth=ML_MODELS['gradient_boosting']['max_depth'],
                random_state=ML_MODELS['gradient_boosting']['random_state'],
            ),
            'visual_elastic_net': make_pipeline(
                StandardScaler(),
                ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=RANDOM_STATE, max_iter=10000),
            ),
        }

        for name, model in visual_models.items():
            results.append(
                _run_holdout_model(
                    name,
                    model,
                    X_train_v, X_test_v, y_train_v, y_test_v,
                    feature_set='visual_only',
                    data_source='precomputed_features',
                )
            )

        for name, (model, grid) in tuned_tree_specs.items():
            tuned_model, best_params = _tune_tree_model(model, grid, X_train_v, y_train_v)
            results.append(
                _run_holdout_model(
                    f'visual_{name}_tuned',
                    tuned_model,
                    X_train_v, X_test_v, y_train_v, y_test_v,
                    feature_set='visual_only',
                    data_source='precomputed_features',
                    extra={'tuning_params': json.dumps(best_params, sort_keys=True)},
                )
            )

        # Combined features (visual + RUCA1)
        # Use ColumnTransformer to properly handle RUCA (categorical) vs visual (continuous)
        from sklearn.compose import ColumnTransformer

        combined_cols = visual_cols + [TREATMENT_VAR]
        X_train_c, X_test_c, y_train_c, y_test_c = _prepare_conference_split(
            visual_df, combined_cols, OUTCOME_VAR
        )

        # Get column indices for proper preprocessing
        ruca_idx = [combined_cols.index(TREATMENT_VAR)]
        visual_idx = [i for i, c in enumerate(combined_cols) if c != TREATMENT_VAR]

        # Preprocessor: one-hot encode RUCA, scale visual features
        combined_preprocessor = ColumnTransformer(
            transformers=[
                ('ruca', _get_one_hot_encoder(), ruca_idx),
                ('visual', StandardScaler(), visual_idx),
            ],
            remainder='drop',
        )

        combined_models = {
            'combined_extra_trees': ExtraTreesRegressor(
                n_estimators=ML_MODELS['extra_trees']['n_estimators'],
                max_depth=ML_MODELS['extra_trees']['max_depth'],
                random_state=ML_MODELS['extra_trees']['random_state'],
            ),
            'combined_random_forest': RandomForestRegressor(
                n_estimators=ML_MODELS['random_forest']['n_estimators'],
                max_depth=ML_MODELS['random_forest']['max_depth'],
                random_state=ML_MODELS['random_forest']['random_state'],
            ),
            'combined_gradient_boosting': GradientBoostingRegressor(
                n_estimators=ML_MODELS['gradient_boosting']['n_estimators'],
                learning_rate=ML_MODELS['gradient_boosting']['learning_rate'],
                max_depth=ML_MODELS['gradient_boosting']['max_depth'],
                random_state=ML_MODELS['gradient_boosting']['random_state'],
            ),
            # ElasticNet with proper RUCA encoding (one-hot + scaled visual)
            'combined_elastic_net': make_pipeline(
                combined_preprocessor,
                ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=RANDOM_STATE, max_iter=10000),
            ),
        }

        for name, model in combined_models.items():
            results.append(
                _run_holdout_model(
                    name,
                    model,
                    X_train_c, X_test_c, y_train_c, y_test_c,
                    feature_set='combined',
                    data_source='precomputed_features',
                )
            )

        for name, (model, grid) in tuned_tree_specs.items():
            tuned_model, best_params = _tune_tree_model(model, grid, X_train_c, y_train_c)
            results.append(
                _run_holdout_model(
                    f'combined_{name}_tuned',
                    tuned_model,
                    X_train_c, X_test_c, y_train_c, y_test_c,
                    feature_set='combined',
                    data_source='precomputed_features',
                    extra={'tuning_params': json.dumps(best_params, sort_keys=True)},
                )
            )

        results_df = pd.DataFrame(results)
        output_dir = DIAGNOSTICS_DIR / 'conference'
        ensure_dir(output_dir)
        save_csv(results_df, output_dir / 'estimation_results.csv')

        metadata = {
            'profile': 'conference',
            'precomputed_features': str(precomputed_path),
            'labels_file': str(LABELS_FILE),
            'test_size': CONFERENCE_TEST_SIZE,
            'split_seed': CONFERENCE_SPLIT_SEED,
            'timestamp': get_timestamp(),
            'n_visual_rows': len(visual_df),
            'n_label_rows': len(labels_df),
        }
        with open(output_dir / 'estimation_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"\n📄 Conference results saved: {output_dir / 'estimation_results.csv'}")
        return 0

    except Exception as e:
        print(f"\n❌ Conference estimation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main(models: list = None, run_all: bool = False, profile: str = 'default') -> int:
    """
    Run Stage 03: ML Model Estimation.

    Parameters
    ----------
    models : list
        List of model specifications to run.
    run_all : bool
        Run all specifications.
    """
    print("=" * 70)
    print("STAGE 03: ML MODEL ESTIMATION")
    print("=" * 70)

    try:
        if profile == 'conference':
            return run_conference_estimation()

        # Load panel data
        print("\n📂 Loading panel data...")
        input_path = DATA_WORK_DIR / 'panel.parquet'
        if not input_path.exists():
            raise FileNotFoundError(f"Input not found: {input_path}. Run stage 02 first.")
        panel_df = load_parquet(input_path)
        print(f"   Loaded {len(panel_df)} records")

        # Get spatial groups
        spatial_groups = panel_df['spatial_group'].values

        # Get specifications with detected feature columns
        SPECIFICATIONS = get_specifications(panel_df)
        visual_features = get_visual_feature_cols(panel_df)
        print(f"   Detected {len(visual_features)} visual feature columns")

        # Determine which specifications to run
        if run_all:
            specs_to_run = list(SPECIFICATIONS.keys())
        elif models:
            specs_to_run = [m for m in models if m in SPECIFICATIONS]
        else:
            specs_to_run = ['ruca_baseline', 'visual_only', 'combined']

        print(f"\n🤖 Running {len(specs_to_run)} model specifications...")

        # Run specifications
        results = []
        ensure_dir(MODELS_DIR)

        for spec_name in specs_to_run:
            spec = SPECIFICATIONS[spec_name]
            result, model, scaler = run_specification(
                panel_df, spec_name, spec, spatial_groups
            )
            results.append(result)

            # Save model
            model_path = save_model(model, scaler, spec_name, MODELS_DIR)
            print(f"      Model saved: {model_path.name}")

        # Save results
        print("\n💾 Saving estimation results...")
        results_df = pd.DataFrame(results)
        ensure_dir(DIAGNOSTICS_DIR)
        save_csv(results_df, DIAGNOSTICS_DIR / 'estimation_results.csv')

        # Print summary
        print("\n📊 Estimation Summary:")
        print("-" * 60)
        print(f"{'Specification':<20} {'Train R²':>10} {'CV R²':>15}")
        print("-" * 60)
        for r in results:
            cv_str = f"{r['cv_r2_mean']:.3f} ± {r['cv_r2_std']:.3f}"
            print(f"{r['specification']:<20} {r['train_r2']:>10.3f} {cv_str:>15}")
        print("-" * 60)

        print("\n✅ Stage 03 complete!")
        return 0

    except Exception as e:
        print(f"\n❌ Stage 03 failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--models', nargs='+')
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()
    sys.exit(main(models=args.models, run_all=args.all))
