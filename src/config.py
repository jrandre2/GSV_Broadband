"""
Centralized configuration for ML Vision Broadband CENTAUR pipeline.

This module contains all project-wide settings including:
- Path definitions
- Study parameters
- Feature extraction settings
- ML model configurations
- Cross-validation settings
"""

from pathlib import Path
from typing import Dict, List, Any

# =============================================================================
# PATH CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / 'data_raw'
DATA_WORK_DIR = PROJECT_ROOT / 'data_work'
MANUSCRIPT_DIR = PROJECT_ROOT / 'manuscript_quarto'
DOC_DIR = PROJECT_ROOT / 'doc'

# Subdirectories
MANIFEST_DIR = DATA_RAW_DIR / 'manifest'
LABELS_DIR = DATA_RAW_DIR / 'labels'
IMAGES_DIR = PROJECT_ROOT / 'archive' / 'images_legacy' / 'enhanced_processed' / 'images_enhanced_processed'
SPATIAL_DIR = DATA_RAW_DIR / 'spatial'

FEATURES_DIR = DATA_WORK_DIR / 'features'
MODELS_DIR = DATA_WORK_DIR / 'models'
DIAGNOSTICS_DIR = DATA_WORK_DIR / 'diagnostics'
QUALITY_DIR = DATA_WORK_DIR / 'quality'
CACHE_DIR = DATA_WORK_DIR / '.cache'

FIGURES_DIR = MANUSCRIPT_DIR / 'figures'

# =============================================================================
# STUDY PARAMETERS
# =============================================================================

STUDY_STATE = 'Nebraska'
N_ZIP_CODES = 264
N_ZIPS_WITH_IMAGES = 261

# Input file paths
STUDY_ZIP_LIST = MANIFEST_DIR / 'zip_east_264.csv'
MANIFEST_FILE = MANIFEST_DIR / 'nebraska_streetview_manifest.csv'
MANIFEST_JSON = MANIFEST_DIR / 'nebraska_streetview_manifest.json'
LABELS_FILE = LABELS_DIR / 'broadband_labels_with_ruca.csv'

# =============================================================================
# IMAGE COLLECTION PARAMETERS
# =============================================================================

BAG_POINTS_PER_ZIP = 50
IMAGE_HEADINGS: List[int] = [0, 90, 180, 270]  # Cardinal directions
IMAGE_SIZE = 640
IMAGES_PER_ZIP_MAX = 10  # Max images to use for feature extraction per ZIP

# Total images in dataset
TOTAL_IMAGES = 7619
AVG_IMAGES_PER_ZIP = 29.2

# =============================================================================
# FEATURE EXTRACTION CONFIGURATION
# =============================================================================

CNN_BACKBONE = 'efficientnet_b3_21k'

# Feature set configuration
N_VISUAL_FEATURES = 24
FEATURE_TYPES: Dict[str, int] = {
    'infrastructure': 15,  # Infrastructure-related visual features
    'color': 9,            # Color-based visual features
}

# Infrastructure feature names
INFRASTRUCTURE_FEATURES: List[str] = [
    'edge_density',
    'vertical_density',
    'horizontal_density',
    'infrastructure_ratio',
    'road_density',
    'building_density',
    'pole_density',
    'wire_density',
    'pavement_ratio',
    'structure_complexity',
    'urban_texture',
    'development_index',
    'infrastructure_continuity',
    'built_ratio',
    'openness',
]

# Color feature names
COLOR_FEATURES: List[str] = [
    'brightness',
    'saturation',
    'color_variance',
    'vegetation_ratio',
    'sky_ratio',
    'gray_ratio',
    'hue_diversity',
    'contrast',
    'colorfulness',
]

# All visual features
VISUAL_FEATURE_NAMES: List[str] = INFRASTRUCTURE_FEATURES + COLOR_FEATURES

# =============================================================================
# SPATIAL CROSS-VALIDATION CONFIGURATION
# =============================================================================

SPATIAL_CV_N_GROUPS = 5
SPATIAL_GROUPING_METHOD = 'contiguity_queen'  # Options: 'kmeans', 'balanced_kmeans', 'geographic_bands', 'longitude_bands', 'spatial_blocks', 'zip_digit', 'contiguity_queen'
SPATIAL_SENSITIVITY_METHODS = [
    'contiguity_queen',
    'kmeans',
    'balanced_kmeans',
    'geographic_bands',
    'longitude_bands',
    'spatial_blocks',
]
REPEATED_CV_N_SPLITS = 5
REPEATED_CV_N_REPEATS = 10
TUNING_INNER_FOLDS = 3
TUNING_RIDGE_ALPHAS = [0.1, 1.0, 10.0, 100.0]
TUNING_ENET_ALPHAS = [0.01, 0.1, 1.0, 10.0]
TUNING_ENET_L1_RATIOS = [0.1, 0.5, 0.9]
TUNING_RF_PARAMS = {
    'n_estimators': [200],
    'max_depth': [None, 10],
    'min_samples_leaf': [1, 5],
    'max_features': ['sqrt', 0.5],
}
TUNING_ET_PARAMS = {
    'n_estimators': [200],
    'max_depth': [None, 10],
    'min_samples_leaf': [1, 5],
    'max_features': ['sqrt', 0.5],
}
TUNING_GB_PARAMS = {
    'n_estimators': [100, 300],
    'learning_rate': [0.05, 0.1],
    'max_depth': [2, 3],
    'subsample': [1.0, 0.8],
}

# =============================================================================
# ML MODEL CONFIGURATION
# =============================================================================

# Regularization parameters (conservative for spatial validation)
VISUAL_REGULARIZATION = 100.0  # Strong regularization for visual features
RUCA_REGULARIZATION = 1.0      # Light regularization for RUCA baseline

# Model hyperparameters
ML_MODELS: Dict[str, Dict[str, Any]] = {
    'ridge': {
        'alpha': [0.1, 1.0, 10.0, 100.0],
        'fit_intercept': True,
    },
    'random_forest': {
        'n_estimators': 100,
        'max_depth': None,
        'random_state': 42,
    },
    'extra_trees': {
        'n_estimators': 100,
        'max_depth': None,
        'random_state': 42,
    },
    'gradient_boosting': {
        'n_estimators': 100,
        'learning_rate': 0.1,
        'max_depth': 3,
        'random_state': 42,
    },
}

# Random seed for reproducibility
RANDOM_STATE = 42

# =============================================================================
# TARGET AND TREATMENT VARIABLES
# =============================================================================

OUTCOME_VAR = 'broadband_usage'
TREATMENT_VAR = 'RUCA1'

# RUCA code definitions
RUCA_CATEGORIES: Dict[int, str] = {
    1: 'Metropolitan core',
    2: 'Metropolitan high commuting',
    3: 'Metropolitan low commuting',
    4: 'Micropolitan core',
    5: 'Micropolitan high commuting',
    6: 'Micropolitan low commuting',
    7: 'Small town core',
    8: 'Small town high commuting',
    9: 'Small town low commuting',
    10: 'Rural areas',
}

# RUCA groupings
RUCA_GROUPS: Dict[str, List[int]] = {
    'metropolitan': [1, 2, 3],
    'micropolitan': [4, 5, 6],
    'small_town': [7, 8, 9],
    'rural': [10],
}

# =============================================================================
# QA THRESHOLDS
# =============================================================================

QA_MAX_MISSING_PCT = 5.0      # Maximum allowed missing values (%)
QA_MIN_ROW_COUNT = 100        # Minimum rows for valid analysis
QA_MAX_DUPLICATE_PCT = 1.0    # Maximum duplicate rows (%)

# =============================================================================
# CACHING CONFIGURATION
# =============================================================================

CACHE_ENABLED = True
CACHE_MAX_AGE_HOURS = 24

# =============================================================================
# PARALLEL EXECUTION
# =============================================================================

PARALLEL_ENABLED = True
PARALLEL_MAX_WORKERS = 4

# =============================================================================
# OUTPUT FORMAT SETTINGS
# =============================================================================

PARQUET_COMPRESSION = 'snappy'
FLOAT_PRECISION = 6
SIGNIFICANCE_LEVEL = 0.05

# =============================================================================
# CONFERENCE REPRODUCTION SETTINGS
# =============================================================================

CONFERENCE_FEATURES_PATH = PROJECT_ROOT / 'data' / 'processed' / 'enhanced_all_features_20251228_124331.csv'
CONFERENCE_TEST_SIZE = 0.2
CONFERENCE_SPLIT_SEED = 42

# =============================================================================
# EXPECTED PERFORMANCE METRICS (from honest validation)
# =============================================================================

EXPECTED_METRICS: Dict[str, Dict[str, float]] = {
    'ruca_baseline': {
        'r2_cv': 0.110,
        'r2_std': 0.115,
    },
    'visual_only': {
        'r2_cv': 0.022,
        'r2_std': 0.131,
    },
    'combined': {
        'r2_cv': 0.116,
        'r2_std': 0.100,
    },
}
