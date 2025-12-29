"""
Spatial Cross-Validation Manager
================================

Implements spatial cross-validation to prevent data leakage from
geographic proximity. Uses GroupKFold with spatially-defined groups
to ensure training and test sets are geographically separated.

Key features:
- Multiple grouping methods (k-means, geographic bands, ZIP digit)
- Leakage quantification by comparing spatial vs random CV
- Visualization of spatial groups

Based on spatial_cross_validation.py implementation.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
import warnings

warnings.filterwarnings('ignore')


class SpatialCVManager:
    """
    Manager for spatial cross-validation to prevent geographic data leakage.

    Uses GroupKFold with geographic groups to ensure proper separation
    between training and test sets, preventing spatial autocorrelation
    from inflating performance metrics.
    """

    def __init__(self, n_groups: int = 5, method: str = 'kmeans', random_state: int = 42):
        """
        Initialize the spatial CV manager.

        Parameters
        ----------
        n_groups : int
            Number of spatial groups for cross-validation.
        method : str
            Grouping method: 'kmeans', 'geographic_bands', 'longitude_bands',
            'spatial_blocks', 'zip_digit', 'contiguity_queen'.
        random_state : int
            Random seed for reproducibility.
        """
        self.n_groups = n_groups
        self.method = method
        self.random_state = random_state
        self.spatial_groups = None
        self.group_kfold = GroupKFold(n_splits=n_groups)

    def create_groups_from_coordinates(
        self,
        latitudes: np.ndarray,
        longitudes: np.ndarray,
    ) -> np.ndarray:
        """
        Create spatial groups from geographic coordinates.

        Parameters
        ----------
        latitudes : np.ndarray
            Array of latitude values.
        longitudes : np.ndarray
            Array of longitude values.

        Returns
        -------
        np.ndarray
            Array of group assignments (0 to n_groups-1).
        """
        coords = np.column_stack([longitudes, latitudes])

        if self.method == 'kmeans':
            kmeans = KMeans(
                n_clusters=self.n_groups,
                random_state=self.random_state,
                n_init=10
            )
            self.spatial_groups = kmeans.fit_predict(coords)

        elif self.method == 'geographic_bands':
            # Create latitude-based bands
            quantiles = np.quantile(latitudes, np.linspace(0, 1, self.n_groups + 1))
            self.spatial_groups = np.digitize(latitudes, quantiles) - 1
            self.spatial_groups = np.clip(self.spatial_groups, 0, self.n_groups - 1)

        elif self.method == 'longitude_bands':
            # Create longitude-based bands
            quantiles = np.quantile(longitudes, np.linspace(0, 1, self.n_groups + 1))
            self.spatial_groups = np.digitize(longitudes, quantiles) - 1
            self.spatial_groups = np.clip(self.spatial_groups, 0, self.n_groups - 1)
        elif self.method == 'spatial_blocks':
            coords = np.column_stack([longitudes, latitudes])
            x_min, x_max = coords[:, 0].min(), coords[:, 0].max()
            y_min, y_max = coords[:, 1].min(), coords[:, 1].max()

            n_side = int(np.ceil(np.sqrt(self.n_groups)))
            x_bins = np.linspace(x_min, x_max, n_side + 1)
            y_bins = np.linspace(y_min, y_max, n_side + 1)

            x_groups = np.digitize(coords[:, 0], x_bins) - 1
            y_groups = np.digitize(coords[:, 1], y_bins) - 1
            self.spatial_groups = (x_groups * n_side + y_groups).astype(int)
            self.spatial_groups = self.spatial_groups % self.n_groups

        else:
            raise ValueError(f"Unknown method: {self.method}")

        self._print_group_summary()
        return self.spatial_groups

    def create_groups_from_zip_codes(
        self,
        zip_codes: Union[List[str], np.ndarray, pd.Series],
        digit_position: int = 3,
    ) -> np.ndarray:
        """
        Create spatial groups based on ZIP code digits.

        Uses the nth digit of ZIP codes to create geographic groups,
        which provides a simple proxy for geographic location.

        Parameters
        ----------
        zip_codes : array-like
            Array of ZIP codes (as strings or integers).
        digit_position : int
            Position of digit to use (0-indexed). Default is 3 (4th digit).

        Returns
        -------
        np.ndarray
            Array of group assignments.
        """
        zip_strs = pd.Series(zip_codes).astype(str).str.zfill(5)
        digits = zip_strs.str[digit_position].astype(int)

        # Map digits to groups (combine adjacent digits to get ~5 groups)
        group_mapping = digits // 2  # 0-1 -> 0, 2-3 -> 1, etc.
        self.spatial_groups = group_mapping.values

        # Ensure we have the right number of groups
        unique_groups = np.unique(self.spatial_groups)
        if len(unique_groups) > self.n_groups:
            # Remap to fewer groups
            self.spatial_groups = self.spatial_groups % self.n_groups

        self._print_group_summary()
        return self.spatial_groups

    def create_groups_from_geodata(
        self,
        gdf,
        contiguity: str = 'queen',
    ) -> np.ndarray:
        """
        Create spatial groups using contiguity-constrained clustering.

        Parameters
        ----------
        gdf : GeoDataFrame
            GeoDataFrame with geometry aligned to the data order.
        contiguity : str
            'queen' (shared vertices/edges) or 'rook' (shared edges only).

        Returns
        -------
        np.ndarray
            Array of group assignments.
        """
        try:
            import geopandas as gpd  # noqa: F401
        except Exception as exc:
            raise ImportError(f"geopandas required for contiguity grouping: {exc}")

        contiguity = contiguity.lower()
        if contiguity not in ('queen', 'rook'):
            raise ValueError(f"Unknown contiguity type: {contiguity}")

        connectivity = self._build_contiguity_connectivity(gdf, contiguity)
        if connectivity is None:
            raise ValueError("Failed to build contiguity connectivity matrix")

        centroids = gdf.geometry.centroid
        coords = np.column_stack([centroids.x.values, centroids.y.values])

        cluster = AgglomerativeClustering(
            n_clusters=self.n_groups,
            linkage='ward',
            connectivity=connectivity,
        )
        self.spatial_groups = cluster.fit_predict(coords)
        self._print_group_summary()
        return self.spatial_groups

    def _build_contiguity_connectivity(self, gdf, contiguity: str):
        """Build a contiguity-based connectivity matrix.

        Queen contiguity: polygons are neighbors if they share any boundary
        (edge or vertex).

        Rook contiguity: polygons are neighbors only if they share an edge
        (not just a vertex point).
        """
        from scipy.sparse import coo_matrix
        from shapely.geometry import Point, MultiPoint

        geoms = gdf.geometry.reset_index(drop=True)
        sindex = gdf.sindex
        rows = []
        cols = []

        for i, geom in enumerate(geoms):
            if geom is None or geom.is_empty:
                continue
            candidates = list(sindex.intersection(geom.bounds))
            for j in candidates:
                if j <= i:
                    continue
                other = geoms.iloc[j]
                if other is None or other.is_empty:
                    continue

                # Check boundary intersection
                inter = geom.boundary.intersection(other.boundary)
                if inter.is_empty:
                    continue

                if contiguity == 'rook':
                    # Rook: require edge sharing (intersection must have length > 0)
                    # Point or MultiPoint intersections indicate vertex-only contact
                    if isinstance(inter, (Point, MultiPoint)):
                        continue
                    # For other geometry types, check if it has positive length
                    if hasattr(inter, 'length') and inter.length == 0:
                        continue
                # Queen: any boundary intersection counts (edge or vertex)

                rows.extend([i, j])
                cols.extend([j, i])

        if not rows:
            return None

        data = np.ones(len(rows), dtype=int)
        return coo_matrix((data, (rows, cols)), shape=(len(geoms), len(geoms)))

    def _print_group_summary(self):
        """Print summary of spatial groups."""
        unique, counts = np.unique(self.spatial_groups, return_counts=True)
        print(f"   Created {len(unique)} spatial groups:")
        for g, c in zip(unique, counts):
            print(f"      Group {g}: {c} samples")

    def split(self, X: np.ndarray, y: np.ndarray) -> Tuple:
        """
        Generate spatial cross-validation splits.

        Parameters
        ----------
        X : np.ndarray
            Feature matrix.
        y : np.ndarray
            Target array.

        Yields
        ------
        train_idx, test_idx : tuple of np.ndarray
            Indices for training and test sets.
        """
        if self.spatial_groups is None:
            raise ValueError("Must create spatial groups before splitting")

        for train_idx, test_idx in self.group_kfold.split(X, y, groups=self.spatial_groups):
            yield train_idx, test_idx

    def cross_validate(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        scale_features: bool = True,
    ) -> Dict:
        """
        Perform spatial cross-validation.

        Parameters
        ----------
        model : sklearn estimator
            Model to evaluate.
        X : np.ndarray
            Feature matrix.
        y : np.ndarray
            Target array.
        scale_features : bool
            Whether to scale features within each fold.

        Returns
        -------
        dict
            Cross-validation results with scores per fold and summary statistics.
        """
        if self.spatial_groups is None:
            raise ValueError("Must create spatial groups before cross-validation")

        cv_scores = []
        fold_details = []

        for fold, (train_idx, test_idx) in enumerate(self.split(X, y)):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            if scale_features:
                scaler = StandardScaler()
                X_train = scaler.fit_transform(X_train)
                X_test = scaler.transform(X_test)

            # Clone and fit model
            from sklearn.base import clone
            fold_model = clone(model)
            fold_model.fit(X_train, y_train)

            # Predict and score
            y_pred = fold_model.predict(X_test)
            r2 = r2_score(y_test, y_pred)
            cv_scores.append(r2)

            fold_details.append({
                'fold': fold + 1,
                'n_train': len(train_idx),
                'n_test': len(test_idx),
                'r2': r2,
            })

        return {
            'scores': cv_scores,
            'mean': np.mean(cv_scores),
            'std': np.std(cv_scores),
            'fold_details': fold_details,
        }

    def compare_to_random_cv(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        scale_features: bool = True,
    ) -> Dict:
        """
        Compare spatial CV to random CV to quantify data leakage.

        Parameters
        ----------
        model : sklearn estimator
            Model to evaluate.
        X : np.ndarray
            Feature matrix.
        y : np.ndarray
            Target array.
        scale_features : bool
            Whether to scale features.

        Returns
        -------
        dict
            Comparison results with leakage quantification.
        """
        # Spatial CV
        spatial_results = self.cross_validate(model, X, y, scale_features)

        # Random CV
        if scale_features:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
        else:
            X_scaled = X

        random_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='r2')

        leakage = np.mean(random_scores) - spatial_results['mean']

        return {
            'spatial_cv': {
                'mean': spatial_results['mean'],
                'std': spatial_results['std'],
            },
            'random_cv': {
                'mean': np.mean(random_scores),
                'std': np.std(random_scores),
            },
            'leakage': leakage,
            'leakage_pct': (leakage / spatial_results['mean'] * 100) if spatial_results['mean'] != 0 else np.inf,
        }

    def get_train_test_separation(self) -> float:
        """
        Calculate the spatial separation quality of the groups.

        Returns
        -------
        float
            Ratio of within-group pairs to total neighbor pairs.
            Lower is better (indicates less geographic overlap).
        """
        if self.spatial_groups is None:
            return np.nan

        # Simple metric: count transitions between groups
        n_transitions = np.sum(np.diff(self.spatial_groups) != 0)
        max_transitions = len(self.spatial_groups) - 1

        # Higher ratio = more transitions = better mixing
        return n_transitions / max_transitions if max_transitions > 0 else 0


def create_spatial_groups_simple(
    df: pd.DataFrame,
    zip_col: str = 'zip',
    n_groups: int = 5,
) -> np.ndarray:
    """
    Simple function to create spatial groups from a DataFrame with ZIP codes.

    Uses the 4th digit of ZIP codes to create geographic groupings.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing ZIP codes.
    zip_col : str
        Name of the ZIP code column.
    n_groups : int
        Target number of groups.

    Returns
    -------
    np.ndarray
        Array of group assignments.
    """
    manager = SpatialCVManager(n_groups=n_groups, method='zip_digit')
    return manager.create_groups_from_zip_codes(df[zip_col])
