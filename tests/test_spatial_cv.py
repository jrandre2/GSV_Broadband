"""
Tests for spatial cross-validation.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.spatial_cv import SpatialCVManager, create_spatial_groups_simple


class TestSpatialCVManager:
    """Tests for SpatialCVManager class."""

    def test_init(self):
        """Test manager initialization."""
        manager = SpatialCVManager(n_groups=5)

        assert manager.n_groups == 5
        assert manager.method == 'kmeans'
        assert manager.spatial_groups is None

    def test_create_groups_from_coordinates(self):
        """Test group creation from coordinates."""
        manager = SpatialCVManager(n_groups=3)

        # Create sample coordinates
        latitudes = np.array([41.0, 41.1, 41.2, 42.0, 42.1, 42.2])
        longitudes = np.array([-96.0, -96.1, -96.2, -95.0, -95.1, -95.2])

        groups = manager.create_groups_from_coordinates(latitudes, longitudes)

        assert len(groups) == 6
        assert len(np.unique(groups)) <= 3
        assert manager.spatial_groups is not None

    def test_create_groups_from_zip_codes(self):
        """Test group creation from ZIP codes."""
        manager = SpatialCVManager(n_groups=5)

        zip_codes = ['68001', '68102', '68203', '68304', '68405']

        groups = manager.create_groups_from_zip_codes(zip_codes)

        assert len(groups) == 5
        assert manager.spatial_groups is not None

    def test_split_requires_groups(self):
        """Test that split requires groups to be created first."""
        manager = SpatialCVManager()

        X = np.random.rand(10, 5)
        y = np.random.rand(10)

        with pytest.raises(ValueError):
            list(manager.split(X, y))

    def test_split_generates_folds(self):
        """Test that split generates correct number of folds."""
        manager = SpatialCVManager(n_groups=2)

        # Create groups using digit_position=2
        # digits 0, 1 → group 0, digit 2 → group 1 (due to // 2 mapping)
        zip_codes = ['68001', '68002', '68101', '68102', '68201', '68202']
        manager.create_groups_from_zip_codes(zip_codes, digit_position=2)

        X = np.random.rand(6, 5)
        y = np.random.rand(6)

        folds = list(manager.split(X, y))

        assert len(folds) == 2
        for train_idx, test_idx in folds:
            assert len(train_idx) > 0
            assert len(test_idx) > 0

    def test_cross_validate(self, sample_panel_df):
        """Test cross-validation."""
        from sklearn.linear_model import Ridge

        manager = SpatialCVManager(n_groups=3)
        manager.spatial_groups = sample_panel_df['spatial_group'].values

        X = sample_panel_df[['edge_density', 'brightness']].values
        y = sample_panel_df['broadband_usage'].values

        model = Ridge(alpha=1.0)
        results = manager.cross_validate(model, X, y)

        assert 'mean' in results
        assert 'std' in results
        assert 'scores' in results
        assert len(results['scores']) == 3

    def test_compare_to_random_cv(self, sample_panel_df):
        """Test comparison with random CV."""
        from sklearn.linear_model import Ridge

        manager = SpatialCVManager(n_groups=3)
        manager.spatial_groups = sample_panel_df['spatial_group'].values

        X = sample_panel_df[['edge_density', 'brightness']].values
        y = sample_panel_df['broadband_usage'].values

        model = Ridge(alpha=1.0)
        comparison = manager.compare_to_random_cv(model, X, y)

        assert 'spatial_cv' in comparison
        assert 'random_cv' in comparison
        assert 'leakage' in comparison


class TestCreateSpatialGroupsSimple:
    """Tests for create_spatial_groups_simple function."""

    def test_simple_function(self):
        """Test the simple convenience function."""
        df = pd.DataFrame({
            'zip': ['68001', '68102', '68203', '68304', '68405'],
            'value': [1, 2, 3, 4, 5],
        })

        groups = create_spatial_groups_simple(df, zip_col='zip', n_groups=3)

        assert len(groups) == 5
