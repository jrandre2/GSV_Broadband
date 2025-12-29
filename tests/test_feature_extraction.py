"""
Tests for visual feature extraction.
"""

import pytest
import numpy as np
from pathlib import Path

import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.feature_extraction import VisualFeatureExtractor


class TestVisualFeatureExtractor:
    """Tests for VisualFeatureExtractor class."""

    def test_init(self):
        """Test extractor initialization."""
        extractor = VisualFeatureExtractor()

        assert extractor.n_features == 24
        assert len(extractor.feature_names) == 24
        assert 'edge_density' in extractor.feature_names
        assert 'brightness' in extractor.feature_names

    def test_feature_names_complete(self):
        """Test that all feature names are defined."""
        extractor = VisualFeatureExtractor()

        # Check infrastructure features
        assert len(extractor.INFRASTRUCTURE_FEATURES) == 15

        # Check color features
        assert len(extractor.COLOR_FEATURES) == 9

        # Check total
        assert len(extractor.feature_names) == 24

    def test_extract_single_image_invalid_path(self):
        """Test extraction with invalid image path."""
        extractor = VisualFeatureExtractor()

        features = extractor.extract_single_image('/nonexistent/path.jpg')

        assert features.shape == (24,)
        assert np.all(features == 0)

    def test_extract_zip_features_empty_dir(self, temp_data_dir):
        """Test extraction from empty directory."""
        extractor = VisualFeatureExtractor()

        empty_dir = temp_data_dir / 'empty'
        empty_dir.mkdir()

        features = extractor.extract_zip_features('00000', temp_data_dir)

        assert features.shape == (24,)
        assert np.all(features == 0)

    def test_extract_zip_features_with_images(self, temp_image_dir):
        """Test extraction from directory with images."""
        extractor = VisualFeatureExtractor()

        features = extractor.extract_zip_features('68001', temp_image_dir)

        assert features.shape == (24,)
        # Should have non-zero values from the dummy images
        assert not np.all(features == 0)

    def test_extract_batch(self, temp_image_dir):
        """Test batch extraction."""
        extractor = VisualFeatureExtractor()

        zip_codes = ['68001', '68002', '68003']
        features_matrix = extractor.extract_batch(zip_codes, temp_image_dir, verbose=False)

        assert features_matrix.shape == (3, 24)

    def test_max_images_limit(self):
        """Test that max_images_per_zip is respected."""
        extractor = VisualFeatureExtractor(max_images_per_zip=5)

        assert extractor.max_images_per_zip == 5
