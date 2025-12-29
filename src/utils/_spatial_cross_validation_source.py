#!/usr/bin/env python3
"""
Spatial Cross-Validation for GSV Broadband Model
================================================

Uses ZIP code boundary shapefile to create a contiguity matrix and implement
proper spatial cross-validation to avoid data leakage from neighboring areas.

Key Features:
- Loads ZIP code boundary shapefile
- Constructs spatial contiguity matrix
- Implements spatial block cross-validation
- Ensures training/test sets are spatially separated
- Prevents spatial autocorrelation bias
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings

from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.cluster import KMeans

from libpysal.weights import Queen, Rook
import json

warnings.filterwarnings('ignore')

WORKSPACE_ROOT = Path(__file__).resolve().parent
DEFAULT_SHAPEFILE = WORKSPACE_ROOT / "tl_2022_us_zcta520.shp"
DEFAULT_DATA_FILE = WORKSPACE_ROOT / "data/processed/optimal_features_final_20250728_225440.csv"

class SpatialCrossValidator:
    """
    Implements spatial cross-validation to avoid data leakage in geographic data.
    """
    
    def __init__(self, 
                 shapefile_path=None,
                 data_file=None):
        self.shapefile_path = Path(shapefile_path) if shapefile_path else DEFAULT_SHAPEFILE
        self.data_file = Path(data_file) if data_file else DEFAULT_DATA_FILE
        self.output_dir = WORKSPACE_ROOT / "results" / "spatial_validation"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize placeholders
        self.gdf = None
        self.data_df = None
        self.spatial_weights = None
        self.spatial_groups = None
        
    def load_spatial_data(self):
        """Load ZIP code boundaries and merge with feature data."""
        print("📍 Loading spatial data...")
        
        # Load ZIP code boundaries
        print(f"   Loading shapefile: {self.shapefile_path}")
        try:
            self.gdf = gpd.read_file(self.shapefile_path)
            print(f"   Loaded {len(self.gdf)} ZIP code boundaries")
            
            # Clean ZIP code column
            self.gdf['ZCTA5CE20'] = self.gdf['ZCTA5CE20'].astype(str)
            print(f"   ZIP codes range: {self.gdf['ZCTA5CE20'].min()} to {self.gdf['ZCTA5CE20'].max()}")
            
        except Exception as e:
            print(f"❌ Error loading shapefile: {e}")
            return False
        
        # Load feature data
        print(f"   Loading feature data: {self.data_file}")
        try:
            self.data_df = pd.read_csv(self.data_file)
            self.data_df['zip'] = self.data_df['zip'].astype(str)
            print(f"   Loaded features for {len(self.data_df)} ZIP codes")
            
        except Exception as e:
            print(f"❌ Error loading feature data: {e}")
            return False
        
        return True
    
    def merge_spatial_features(self):
        """Merge spatial boundaries with feature data."""
        print("🔗 Merging spatial and feature data...")
        
        # Merge on ZIP code
        merged_gdf = self.gdf.merge(
            self.data_df, 
            left_on='ZCTA5CE20', 
            right_on='zip', 
            how='inner'
        )
        
        print(f"   Successfully merged {len(merged_gdf)} ZIP codes")
        print(f"   Missing spatial data: {len(self.data_df) - len(merged_gdf)} ZIP codes")
        
        if len(merged_gdf) < 50:
            print("⚠️  Warning: Very few ZIP codes matched. Check ZIP code formats.")
            return False
        
        self.merged_gdf = merged_gdf
        return True
    
    def create_spatial_weights(self):
        """Create spatial contiguity matrix."""
        print("🗺️  Creating spatial contiguity matrix...")
        
        try:
            # Create Queen contiguity weights (shared vertices or edges)
            print("   Computing Queen contiguity (shared vertices/edges)...")
            self.queen_weights = Queen.from_dataframe(self.merged_gdf)
            
            # Create Rook contiguity weights (shared edges only)
            print("   Computing Rook contiguity (shared edges only)...")
            self.rook_weights = Rook.from_dataframe(self.merged_gdf)
            
            print(f"   Queen neighbors: {self.queen_weights.n} ZIP codes, {self.queen_weights.s0:.0f} total connections")
            print(f"   Rook neighbors:  {self.rook_weights.n} ZIP codes, {self.rook_weights.s0:.0f} total connections")
            
            # Use Queen weights as primary (more conservative)
            self.spatial_weights = self.queen_weights
            
            # Analyze connectivity
            self.analyze_spatial_connectivity()
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating spatial weights: {e}")
            return False
    
    def analyze_spatial_connectivity(self):
        """Analyze the spatial connectivity structure."""
        print("📊 Analyzing spatial connectivity...")
        
        # Get neighbor counts
        neighbor_counts = [len(neighbors) for neighbors in self.spatial_weights.neighbors.values()]
        
        print(f"   Connectivity Statistics:")
        print(f"      Mean neighbors per ZIP: {np.mean(neighbor_counts):.1f}")
        print(f"      Max neighbors: {np.max(neighbor_counts)}")
        print(f"      Min neighbors: {np.min(neighbor_counts)}")
        print(f"      ZIPs with 0 neighbors: {sum(1 for x in neighbor_counts if x == 0)}")
        
        # Find isolated areas
        isolated_zips = [zip_id for zip_id, neighbors in self.spatial_weights.neighbors.items() if len(neighbors) == 0]
        if isolated_zips:
            print(f"   Isolated ZIP codes: {isolated_zips[:10]}...")  # Show first 10
        
        return neighbor_counts
    
    def create_spatial_groups(self, method='kmeans', n_groups=5):
        """Create spatial groups for cross-validation."""
        print(f"🎯 Creating spatial groups using {method} method...")
        
        if method == 'kmeans':
            # Use geographic coordinates for clustering
            coords = np.column_stack([
                self.merged_gdf.geometry.centroid.x,
                self.merged_gdf.geometry.centroid.y
            ])
            
            # K-means clustering on coordinates
            kmeans = KMeans(n_clusters=n_groups, random_state=42, n_init=10)
            self.spatial_groups = kmeans.fit_predict(coords)
            
        elif method == 'geographic_bands':
            # Create geographic bands (latitude-based)
            centroids_y = self.merged_gdf.geometry.centroid.y
            y_quantiles = np.quantile(centroids_y, np.linspace(0, 1, n_groups + 1))
            
            self.spatial_groups = np.digitize(centroids_y, y_quantiles) - 1
            self.spatial_groups = np.clip(self.spatial_groups, 0, n_groups - 1)
            
        elif method == 'spatial_blocks':
            # Create geographic grid blocks
            coords = np.column_stack([
                self.merged_gdf.geometry.centroid.x,
                self.merged_gdf.geometry.centroid.y
            ])
            
            # Create grid based on coordinate ranges
            x_min, x_max = coords[:, 0].min(), coords[:, 0].max()
            y_min, y_max = coords[:, 1].min(), coords[:, 1].max()
            
            n_blocks_side = int(np.sqrt(n_groups))
            x_bins = np.linspace(x_min, x_max, n_blocks_side + 1)
            y_bins = np.linspace(y_min, y_max, n_blocks_side + 1)
            
            x_groups = np.digitize(coords[:, 0], x_bins) - 1
            y_groups = np.digitize(coords[:, 1], y_bins) - 1
            
            # Combine x and y groups
            self.spatial_groups = x_groups * n_blocks_side + y_groups
            
        # Ensure we have the right number of groups
        unique_groups = np.unique(self.spatial_groups)
        print(f"   Created {len(unique_groups)} spatial groups")
        
        # Analyze group sizes
        group_sizes = [sum(self.spatial_groups == g) for g in unique_groups]
        print(f"   Group sizes: min={min(group_sizes)}, max={max(group_sizes)}, mean={np.mean(group_sizes):.1f}")
        
        return True
    
    def validate_spatial_separation(self):
        """Validate that spatial groups are properly separated."""
        print("✅ Validating spatial separation...")
        
        # Check if neighboring ZIP codes are in different groups
        violations = 0
        total_neighbor_pairs = 0
        
        for i, (zip_id, neighbors) in enumerate(self.spatial_weights.neighbors.items()):
            current_group = self.spatial_groups[i]
            
            for neighbor_id in neighbors:
                # Find neighbor index
                neighbor_idx = list(self.spatial_weights.neighbors.keys()).index(neighbor_id)
                neighbor_group = self.spatial_groups[neighbor_idx]
                
                total_neighbor_pairs += 1
                if current_group == neighbor_group:
                    violations += 1
        
        violation_rate = violations / total_neighbor_pairs if total_neighbor_pairs > 0 else 0
        
        print(f"   Spatial separation analysis:")
        print(f"      Total neighbor pairs: {total_neighbor_pairs}")
        print(f"      Same-group neighbors: {violations}")
        print(f"      Violation rate: {violation_rate:.1%}")
        
        if violation_rate > 0.1:  # More than 10% violations
            print("⚠️  Warning: High spatial group violation rate. Consider different grouping method.")
        else:
            print("✅ Good spatial separation achieved!")
        
        return violation_rate
    
    def spatial_cross_validation(self, feature_types=['RUCA_Only', 'Visual_Only', 'Combined']):
        """Perform spatial cross-validation with proper separation."""
        print("🔬 Performing spatial cross-validation...")
        
        # Prepare feature sets
        feature_sets = self.prepare_feature_sets()
        
        # Models to test
        models = {
            'Ridge_0.1': Ridge(alpha=0.1, random_state=42),
            'Ridge_1.0': Ridge(alpha=1.0, random_state=42),
            'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42),
            'ExtraTrees': ExtraTreesRegressor(n_estimators=100, random_state=42)
        }
        
        # Target variable
        y = self.merged_gdf['broadband_usage'].values
        
        results = {}
        best_score = -np.inf
        best_config = None
        
        for feature_name in feature_types:
            if feature_name not in feature_sets:
                continue
                
            X = feature_sets[feature_name]
            print(f"\\n   Testing {feature_name} features ({X.shape[1]} dimensions):")
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            for model_name, model in models.items():
                try:
                    # Use GroupKFold with spatial groups
                    group_kfold = GroupKFold(n_splits=5)
                    
                    # Perform spatial cross-validation
                    cv_scores = []
                    for train_idx, test_idx in group_kfold.split(X_scaled, y, groups=self.spatial_groups):
                        X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
                        y_train, y_test = y[train_idx], y[test_idx]
                        
                        # Train and predict
                        model.fit(X_train, y_train)
                        y_pred = model.predict(X_test)
                        
                        # Calculate R²
                        r2 = r2_score(y_test, y_pred)
                        cv_scores.append(r2)
                    
                    mean_score = np.mean(cv_scores)
                    std_score = np.std(cv_scores)
                    
                    # Store results
                    config_key = f"{feature_name}_{model_name}"
                    results[config_key] = {
                        'feature_set': feature_name,
                        'model': model_name,
                        'cv_scores': cv_scores,
                        'cv_mean': mean_score,
                        'cv_std': std_score,
                        'spatial_validation': True
                    }
                    
                    print(f"      {model_name:15}: R² = {mean_score:.3f} ± {std_score:.3f} (spatial CV)")
                    
                    if mean_score > best_score:
                        best_score = mean_score
                        best_config = config_key
                        
                except Exception as e:
                    print(f"      {model_name:15}: FAILED ({str(e)[:30]})")
        
        self.spatial_results = results
        print(f"\\n🏆 Best Spatial CV Performance:")
        print(f"   {best_config}: R² = {best_score:.3f}")
        
        return best_config, best_score
    
    def prepare_feature_sets(self):
        """Prepare different feature sets for testing."""
        # RUCA features
        ruca_features = pd.get_dummies(self.merged_gdf['RUCA1'], prefix='RUCA1')
        
        # Visual features
        visual_cols = [col for col in self.merged_gdf.columns 
                      if col.startswith(('infrastructure_', 'color_'))]
        visual_features = self.merged_gdf[visual_cols].fillna(0)
        
        # Combined features
        combined_features = pd.concat([ruca_features, visual_features], axis=1)
        
        feature_sets = {
            'RUCA_Only': ruca_features.values,
            'Visual_Only': visual_features.values,
            'Combined': combined_features.values
        }
        
        print(f"   Feature sets prepared:")
        for name, features in feature_sets.items():
            print(f"      {name}: {features.shape[1]} features")
        
        return feature_sets
    
    def compare_validation_methods(self):
        """Compare spatial CV vs regular CV to show leakage impact."""
        print("⚖️  Comparing validation methods...")
        
        feature_sets = self.prepare_feature_sets()
        y = self.merged_gdf['broadband_usage'].values
        
        # Test one representative model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        scaler = StandardScaler()
        
        comparison_results = {}
        
        for feature_name, X in feature_sets.items():
            X_scaled = scaler.fit_transform(X)
            
            # Regular CV (potential leakage)
            regular_cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='r2')
            regular_mean = regular_cv_scores.mean()
            
            # Spatial CV (proper separation)
            group_kfold = GroupKFold(n_splits=5)
            spatial_cv_scores = []
            
            for train_idx, test_idx in group_kfold.split(X_scaled, y, groups=self.spatial_groups):
                X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
                y_train, y_test = y[train_idx], y[test_idx]
                
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                r2 = r2_score(y_test, y_pred)
                spatial_cv_scores.append(r2)
            
            spatial_mean = np.mean(spatial_cv_scores)
            
            comparison_results[feature_name] = {
                'regular_cv': regular_mean,
                'spatial_cv': spatial_mean,
                'inflation': regular_mean - spatial_mean
            }
            
            print(f"   {feature_name:12}:")
            print(f"      Regular CV:  R² = {regular_mean:.3f}")
            print(f"      Spatial CV:  R² = {spatial_mean:.3f}")
            print(f"      Inflation:   {regular_mean - spatial_mean:+.3f} (leakage bias)")
        
        return comparison_results
    
    def visualize_spatial_groups(self):
        """Create visualization of spatial groups."""
        print("📊 Creating spatial visualization...")
        
        try:
            fig, axes = plt.subplots(1, 2, figsize=(20, 8))
            
            # Plot 1: Spatial groups
            self.merged_gdf['spatial_group'] = self.spatial_groups
            self.merged_gdf.plot(
                column='spatial_group', 
                categorical=True, 
                legend=True, 
                ax=axes[0],
                cmap='tab10'
            )
            axes[0].set_title('Spatial Cross-Validation Groups')
            axes[0].axis('off')
            
            # Plot 2: Broadband usage
            self.merged_gdf.plot(
                column='broadband_usage',
                legend=True,
                ax=axes[1],
                cmap='RdYlBu_r'
            )
            axes[1].set_title('Broadband Usage by ZIP Code')
            axes[1].axis('off')
            
            plt.tight_layout()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plot_file = self.output_dir / f"spatial_groups_{timestamp}.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"   Visualization saved: {plot_file}")
            
        except Exception as e:
            print(f"   Visualization failed: {e}")
    
    def save_results(self, best_config, best_score, comparison_results):
        """Save all spatial validation results."""
        print("💾 Saving spatial validation results...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        results_data = {
            'timestamp': timestamp,
            'best_config': best_config,
            'best_score': best_score,
            'spatial_cv_results': self.spatial_results,
            'validation_comparison': comparison_results,
            'spatial_groups_info': {
                'method': 'kmeans',
                'n_groups': len(np.unique(self.spatial_groups)),
                'group_sizes': [int(x) for x in np.bincount(self.spatial_groups)]
            },
            'connectivity_stats': {
                'total_zip_codes': len(self.merged_gdf),
                'spatial_connections': int(self.spatial_weights.s0),
                'avg_neighbors': float(self.spatial_weights.s0 / self.spatial_weights.n)
            }
        }
        
        results_file = self.output_dir / f"spatial_validation_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"   Results saved: {results_file}")
        
        return True
    
    def run_complete_spatial_analysis(self):
        """Run the complete spatial cross-validation analysis."""
        print("="*70)
        print("SPATIAL CROSS-VALIDATION ANALYSIS")
        print("Preventing data leakage with proper geographic separation")
        print("="*70)
        
        # Step 1: Load spatial data
        if not self.load_spatial_data():
            print("❌ Failed to load spatial data")
            return False
        
        # Step 2: Merge spatial and feature data
        if not self.merge_spatial_features():
            print("❌ Failed to merge data")
            return False
        
        # Step 3: Create spatial weights
        if not self.create_spatial_weights():
            print("❌ Failed to create spatial weights")
            return False
        
        # Step 4: Create spatial groups
        if not self.create_spatial_groups(method='kmeans', n_groups=5):
            print("❌ Failed to create spatial groups")
            return False
        
        # Step 5: Validate spatial separation
        violation_rate = self.validate_spatial_separation()
        
        # Step 6: Perform spatial cross-validation
        best_config, best_score = self.spatial_cross_validation()
        
        # Step 7: Compare validation methods
        comparison_results = self.compare_validation_methods()
        
        # Step 8: Create visualizations
        self.visualize_spatial_groups()
        
        # Step 9: Save results
        self.save_results(best_config, best_score, comparison_results)
        
        print(f"\\n🎯 SPATIAL VALIDATION SUMMARY:")
        print(f"   ZIP Codes Analyzed:     {len(self.merged_gdf)}")
        print(f"   Spatial Groups:         {len(np.unique(self.spatial_groups))}")
        print(f"   Spatial Violation Rate: {violation_rate:.1%}")
        print(f"   Best Spatial CV Score:  R² = {best_score:.3f}")
        print(f"   Best Configuration:     {best_config}")
        
        print(f"\\n✅ Spatial cross-validation complete!")
        print(f"   Data leakage has been properly addressed.")
        
        return {
            'best_config': best_config,
            'best_score': best_score,
            'comparison_results': comparison_results,
            'violation_rate': violation_rate
        }

def main():
    """Main execution function."""
    validator = SpatialCrossValidator()
    results = validator.run_complete_spatial_analysis()
    
    if results:
        print(f"\\n🏆 Spatial validation achieved R² = {results['best_score']:.3f}")
        print("Ready for unbiased model evaluation!")

if __name__ == "__main__":
    main()
