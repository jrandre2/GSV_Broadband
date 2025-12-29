"""
Pytest configuration and fixtures for ML Vision Broadband tests.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add project root to path
import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_labels_df():
    """Create sample broadband labels DataFrame."""
    return pd.DataFrame({
        'zip': ['68001', '68002', '68003', '68004', '68005'],
        'broadband_usage': [0.45, 0.52, 0.38, 0.61, 0.33],
        'RUCA1': [1, 1, 4, 2, 10],
        'latitude': [41.2, 41.3, 41.1, 41.4, 41.0],
        'longitude': [-96.0, -96.1, -95.9, -96.2, -95.8],
    })


@pytest.fixture
def sample_features_df():
    """Create sample visual features DataFrame."""
    np.random.seed(42)
    n_samples = 5

    feature_names = [
        'edge_density', 'vertical_density', 'horizontal_density',
        'brightness', 'saturation', 'vegetation_ratio',
    ]

    data = {
        'zip': ['68001', '68002', '68003', '68004', '68005'],
    }

    for feat in feature_names:
        data[feat] = np.random.rand(n_samples) * 0.5

    return pd.DataFrame(data)


@pytest.fixture
def sample_panel_df(sample_labels_df, sample_features_df):
    """Create sample panel DataFrame."""
    panel = sample_labels_df.merge(sample_features_df, on='zip')
    panel['spatial_group'] = [0, 0, 1, 1, 2]
    panel['has_images'] = True
    panel['has_features'] = True
    return panel


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_image_dir(temp_data_dir):
    """Create temporary image directory with dummy images."""
    import cv2

    images_dir = temp_data_dir / 'images'

    # Create dummy images for a few ZIP codes
    for zip_code in ['68001', '68002', '68003']:
        zip_dir = images_dir / zip_code
        zip_dir.mkdir(parents=True)

        # Create 3 dummy images per ZIP
        for i in range(3):
            # Create a simple colored image
            img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            cv2.imwrite(str(zip_dir / f'image_{i}.jpg'), img)

    return images_dir
