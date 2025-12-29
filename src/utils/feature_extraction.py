"""
Visual Feature Extraction for Street View Images
=================================================

Extracts 24 computer vision features from Google Street View images:
- 15 infrastructure-related features (edge density, structure complexity, etc.)
- 9 color-based features (brightness, vegetation ratio, sky ratio, etc.)

Based on the production_broadband_predictor.py implementation.
"""

import numpy as np
import cv2
from pathlib import Path
from typing import List, Optional, Tuple, Union
import warnings

warnings.filterwarnings('ignore')


class VisualFeatureExtractor:
    """
    Extract reliable visual features from street view images.

    Implements a consistent feature extraction pipeline for:
    - Single image feature extraction
    - ZIP-level aggregation (mean across images)

    Features are designed to capture infrastructure and environmental
    characteristics that may correlate with broadband availability.
    """

    # Feature name definitions
    INFRASTRUCTURE_FEATURES = [
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

    COLOR_FEATURES = [
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

    def __init__(self, max_images_per_zip: int = 10):
        """
        Initialize the feature extractor.

        Parameters
        ----------
        max_images_per_zip : int
            Maximum number of images to process per ZIP code for aggregation.
        """
        self.max_images_per_zip = max_images_per_zip
        self.feature_names = self.INFRASTRUCTURE_FEATURES + self.COLOR_FEATURES
        self.n_features = len(self.feature_names)

    def extract_single_image(self, img_path: Union[str, Path]) -> np.ndarray:
        """
        Extract all features from a single image.

        Parameters
        ----------
        img_path : str or Path
            Path to the image file.

        Returns
        -------
        np.ndarray
            Array of 24 features. Returns zeros if extraction fails.
        """
        try:
            img = cv2.imread(str(img_path))
            if img is None:
                return np.zeros(self.n_features)

            # Convert color spaces
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Extract infrastructure features
            infra_features = self._extract_infrastructure_features(img, hsv, gray)

            # Extract color features
            color_features = self._extract_color_features(img, hsv, gray)

            return np.concatenate([infra_features, color_features])

        except Exception as e:
            print(f"Warning: Failed to process {img_path}: {e}")
            return np.zeros(self.n_features)

    def _extract_infrastructure_features(
        self,
        img: np.ndarray,
        hsv: np.ndarray,
        gray: np.ndarray
    ) -> np.ndarray:
        """Extract 15 infrastructure-related features."""
        features = []

        # 1. Edge density using Canny
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        features.append(edge_density)

        # 2. Vertical edge density (poles/buildings proxy)
        vertical_edges = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        vertical_density = np.mean(np.abs(vertical_edges))
        features.append(vertical_density / 100)  # Normalize

        # 3. Horizontal edge density (road/horizon proxy)
        horizontal_edges = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        horizontal_density = np.mean(np.abs(horizontal_edges))
        features.append(horizontal_density / 100)  # Normalize

        # 4. Infrastructure ratio (gray/black low saturation)
        infra_mask = cv2.inRange(hsv, (0, 0, 0), (180, 50, 150))
        infrastructure_ratio = np.sum(infra_mask > 0) / infra_mask.size
        features.append(infrastructure_ratio)

        # 5. Road density (dark gray horizontal regions)
        road_mask = cv2.inRange(hsv, (0, 0, 40), (180, 50, 100))
        road_density = np.sum(road_mask > 0) / road_mask.size
        features.append(road_density)

        # 6. Building density (vertical structure proxy)
        building_density = edge_density * (1 - self._get_sky_ratio(hsv))
        features.append(building_density)

        # 7. Pole density (thin vertical lines)
        pole_mask = self._detect_poles(gray)
        pole_density = np.sum(pole_mask > 0) / pole_mask.size
        features.append(pole_density)

        # 8. Wire density (thin horizontal lines in upper image)
        wire_density = self._detect_wires(gray)
        features.append(wire_density)

        # 9. Pavement ratio (lower image gray regions)
        height = gray.shape[0]
        lower_half = hsv[height//2:, :, :]
        pave_mask = cv2.inRange(lower_half, (0, 0, 50), (180, 50, 150))
        pavement_ratio = np.sum(pave_mask > 0) / pave_mask.size
        features.append(pavement_ratio)

        # 10. Structure complexity (Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        structure_complexity = laplacian.var() / 10000  # Normalize
        features.append(structure_complexity)

        # 11. Urban texture (grayscale standard deviation)
        urban_texture = np.std(gray) / 100  # Normalize
        features.append(urban_texture)

        # 12. Development index (combination metric)
        development_index = (edge_density + infrastructure_ratio + building_density) / 3
        features.append(development_index)

        # 13. Infrastructure continuity (connected edge regions)
        n_labels, labels = cv2.connectedComponents(edges)
        infrastructure_continuity = np.log1p(n_labels) / 10  # Log-normalized
        features.append(infrastructure_continuity)

        # 14. Built ratio (non-sky, non-vegetation)
        sky_ratio = self._get_sky_ratio(hsv)
        veg_ratio = self._get_vegetation_ratio(hsv)
        built_ratio = max(0, 1 - sky_ratio - veg_ratio)
        features.append(built_ratio)

        # 15. Openness (inverse of edge density + structure)
        openness = 1 - (edge_density + structure_complexity) / 2
        features.append(max(0, openness))

        return np.array(features)

    def _extract_color_features(
        self,
        img: np.ndarray,
        hsv: np.ndarray,
        gray: np.ndarray
    ) -> np.ndarray:
        """Extract 9 color-based features."""
        features = []

        # 1. Brightness (V channel mean)
        brightness = np.mean(hsv[:, :, 2]) / 255
        features.append(brightness)

        # 2. Saturation (S channel mean)
        saturation = np.mean(hsv[:, :, 1]) / 255
        features.append(saturation)

        # 3. Color variance across RGB channels
        color_variance = np.var(img.reshape(-1, 3), axis=0).mean() / 10000
        features.append(color_variance)

        # 4. Vegetation ratio (green areas)
        vegetation_ratio = self._get_vegetation_ratio(hsv)
        features.append(vegetation_ratio)

        # 5. Sky ratio (blue high brightness areas)
        sky_ratio = self._get_sky_ratio(hsv)
        features.append(sky_ratio)

        # 6. Gray ratio (low saturation)
        gray_mask = cv2.inRange(hsv, (0, 0, 50), (180, 30, 200))
        gray_ratio = np.sum(gray_mask > 0) / gray_mask.size
        features.append(gray_ratio)

        # 7. Hue diversity (entropy of hue histogram)
        hue_hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        hue_hist = hue_hist / hue_hist.sum()
        hue_diversity = -np.sum(hue_hist * np.log2(hue_hist + 1e-7)) / np.log2(180)
        features.append(hue_diversity)

        # 8. Contrast (difference between max and min intensity)
        contrast = (np.percentile(gray, 95) - np.percentile(gray, 5)) / 255
        features.append(contrast)

        # 9. Colorfulness metric
        r, g, b = img[:, :, 2], img[:, :, 1], img[:, :, 0]
        rg = np.abs(r.astype(float) - g.astype(float))
        yb = np.abs(0.5 * (r.astype(float) + g.astype(float)) - b.astype(float))
        colorfulness = (np.std(rg) + np.std(yb)) / 500
        features.append(colorfulness)

        return np.array(features)

    def _get_vegetation_ratio(self, hsv: np.ndarray) -> float:
        """Calculate vegetation (green) ratio."""
        green_mask = cv2.inRange(hsv, (40, 40, 40), (80, 255, 255))
        return np.sum(green_mask > 0) / green_mask.size

    def _get_sky_ratio(self, hsv: np.ndarray) -> float:
        """Calculate sky (blue) ratio."""
        sky_mask = cv2.inRange(hsv, (100, 50, 100), (130, 255, 255))
        return np.sum(sky_mask > 0) / sky_mask.size

    def _detect_poles(self, gray: np.ndarray) -> np.ndarray:
        """Detect vertical pole-like structures."""
        # Use vertical Sobel with morphological operations
        vertical = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        vertical = np.abs(vertical).astype(np.uint8)
        _, thresh = cv2.threshold(vertical, 50, 255, cv2.THRESH_BINARY)

        # Morphological opening to isolate vertical lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 15))
        poles = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        return poles

    def _detect_wires(self, gray: np.ndarray) -> float:
        """Detect horizontal wire-like structures in upper image."""
        height = gray.shape[0]
        upper_third = gray[:height//3, :]

        horizontal = cv2.Sobel(upper_third, cv2.CV_64F, 0, 1, ksize=3)
        horizontal = np.abs(horizontal)

        # Detect thin horizontal lines
        wire_threshold = np.percentile(horizontal, 95)
        wire_density = np.sum(horizontal > wire_threshold) / horizontal.size
        return wire_density

    def extract_zip_features(
        self,
        zip_code: Union[str, int],
        image_base_path: Union[str, Path],
    ) -> np.ndarray:
        """
        Extract aggregated features for a ZIP code.

        Parameters
        ----------
        zip_code : str or int
            ZIP code to process.
        image_base_path : str or Path
            Base directory containing ZIP code subdirectories with images.

        Returns
        -------
        np.ndarray
            Mean features across all images in the ZIP code.
            Returns zeros if no images found.
        """
        zip_dir = Path(image_base_path) / str(zip_code)

        if not zip_dir.exists():
            return np.zeros(self.n_features)

        # Get all image files and sort by name for reproducible selection order
        # Filenames typically encode sample_id (e.g., "51040_00000_0.jpg") where
        # the middle number indicates building rank (lower = larger buildings)
        image_files = list(zip_dir.glob("*.jpg")) + list(zip_dir.glob("*.png"))
        image_files = sorted(image_files, key=lambda x: x.name)

        if len(image_files) == 0:
            return np.zeros(self.n_features)

        # Extract features from images (up to max_images_per_zip)
        # Selection is deterministic: first N images by sorted filename
        features_list = []
        for img_file in image_files[:self.max_images_per_zip]:
            features = self.extract_single_image(img_file)
            if not np.all(features == 0):  # Skip failed extractions
                features_list.append(features)

        if len(features_list) == 0:
            return np.zeros(self.n_features)

        # Return mean features across all images
        return np.mean(features_list, axis=0)

    def extract_batch(
        self,
        zip_codes: List[Union[str, int]],
        image_base_path: Union[str, Path],
        verbose: bool = True,
    ) -> np.ndarray:
        """
        Extract features for multiple ZIP codes.

        Parameters
        ----------
        zip_codes : list
            List of ZIP codes to process.
        image_base_path : str or Path
            Base directory containing ZIP code subdirectories.
        verbose : bool
            Whether to print progress.

        Returns
        -------
        np.ndarray
            Feature matrix of shape (n_zips, n_features).
        """
        features_matrix = []

        for i, zip_code in enumerate(zip_codes):
            if verbose and i % 50 == 0:
                print(f"   Processed {i}/{len(zip_codes)} ZIP codes...")

            features = self.extract_zip_features(zip_code, image_base_path)
            features_matrix.append(features)

        return np.array(features_matrix)
