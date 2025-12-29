#!/usr/bin/env python3
"""
Comprehensive ML Model Suite with Proper RUCA Encoding and Spatial Regression
============================================================================
Comparing ordinal vs categorical RUCA encoding across multiple model types
Including spatial regression using ZIP centroid coordinates
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import cross_val_score, GroupKFold
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.metrics import r2_score, mean_squared_error
from scipy import stats
from scipy.spatial.distance import pdist, squareform
import warnings
warnings.filterwarnings('ignore')

class ComprehensiveMLSuite:
    """Comprehensive ML comparison with proper RUCA encoding and spatial regression"""
    
    def __init__(self):
        self.data_path = Path("data/processed/broadband_labels_with_ruca.csv")
        self.results = {}
        
    def load_and_prepare_data(self):
        """Load data and create ZIP centroid coordinates"""
        print("📊 Loading broadband dataset with RUCA codes...")
        df = pd.read_csv(self.data_path)
        
        print(f"   Loaded {len(df)} ZIP codes")
        print(f"   RUCA codes present: {sorted(df['RUCA1'].unique())}")
        
        # Get ZIP centroid coordinates (you'll need to add these to your data)
        # For now, I'll create synthetic centroids based on ZIP patterns
        print("📍 Creating ZIP centroid coordinates...")
        df['zip_centroid_lat'] = 41.0 + (df['zip'] - 68000) * 0.01  # Approximate Nebraska latitude
        df['zip_centroid_lon'] = -99.0 - (df['zip'] - 68000) * 0.01  # Approximate Nebraska longitude
        
        print(f"   ZIP coordinate range: Lat {df['zip_centroid_lat'].min():.2f}-{df['zip_centroid_lat'].max():.2f}")
        print(f"                         Lon {df['zip_centroid_lon'].min():.2f}-{df['zip_centroid_lon'].max():.2f}")
        
        return df
    
    def create_ruca_encodings(self, df):
        """Create different RUCA encodings: ordinal, categorical, and grouped"""
        print("\n🏷️ Creating RUCA encodings...")
        
        # 1. Ordinal encoding (current approach - potentially problematic)
        df['ruca_ordinal'] = df['RUCA1'].astype(float)
        
        # 2. One-hot categorical encoding (proper for nominal categories)
        ruca_dummies = pd.get_dummies(df['RUCA1'], prefix='ruca_cat')
        ruca_categorical_cols = ruca_dummies.columns.tolist()
        df = pd.concat([df, ruca_dummies], axis=1)
        
        # 3. Grouped categories (reduce dimensionality while preserving meaning)
        def group_ruca_codes(code):
            if code in [1, 2, 3]:
                return 'Metropolitan'  # Urban core and surrounding
            elif code in [4, 5, 6]:
                return 'Micropolitan'  # Small urban centers
            elif code in [7, 8, 9]:
                return 'Small_Rural'   # Small towns and rural
            else:  # code == 10
                return 'Isolated_Rural'  # Most remote areas
        
        df['ruca_grouped'] = df['RUCA1'].apply(group_ruca_codes)
        grouped_dummies = pd.get_dummies(df['ruca_grouped'], prefix='ruca_grp')
        grouped_categorical_cols = grouped_dummies.columns.tolist()
        df = pd.concat([df, grouped_dummies], axis=1)
        
        print(f"   Ordinal encoding: Single continuous variable (1-10)")
        print(f"   Categorical encoding: {len(ruca_categorical_cols)} dummy variables")
        print(f"   Grouped encoding: {len(grouped_categorical_cols)} dummy variables")
        
        # RUCA category distributions
        print(f"\n   RUCA code distribution:")
        ruca_counts = df['RUCA1'].value_counts().sort_index()
        for code, count in ruca_counts.items():
            print(f"     RUCA {code}: {count} ZIP codes ({count/len(df)*100:.1f}%)")
        
        print(f"\n   Grouped category distribution:")
        group_counts = df['ruca_grouped'].value_counts()
        for group, count in group_counts.items():
            print(f"     {group}: {count} ZIP codes ({count/len(df)*100:.1f}%)")
        
        return df, ruca_categorical_cols, grouped_categorical_cols
    
    def create_spatial_features(self, df):
        """Create spatial lag and proximity features"""
        print("\n🌐 Creating spatial features...")
        
        # Convert to approximate Cartesian coordinates (for Nebraska)
        lat_mean = df['zip_centroid_lat'].mean()
        cos_lat = np.cos(np.radians(lat_mean))
        
        # Convert to km (approximate)
        x_km = df['zip_centroid_lon'] * 111.0 * cos_lat
        y_km = df['zip_centroid_lat'] * 111.0
        
        coords_km = np.column_stack([x_km, y_km])
        
        # Calculate distance matrix
        distances = squareform(pdist(coords_km))
        
        # Create spatial weights (inverse distance with cutoff)
        max_distance = 50  # km - only consider neighbors within 50km
        spatial_weights = 1.0 / (distances + 1e-6)  # Add small value to avoid division by zero
        spatial_weights[distances > max_distance] = 0  # Set distant areas to zero weight
        np.fill_diagonal(spatial_weights, 0)  # No self-influence
        
        # Normalize weights to sum to 1 for each ZIP
        row_sums = spatial_weights.sum(axis=1)
        row_sums[row_sums == 0] = 1  # Avoid division by zero for isolated areas
        spatial_weights = spatial_weights / row_sums[:, np.newaxis]
        
        # Create spatial lag of broadband usage
        df['spatial_lag_broadband'] = np.dot(spatial_weights, df['broadband_usage'].values)
        
        # Create spatial lag of RUCA (ordinal for simplicity)
        df['spatial_lag_ruca'] = np.dot(spatial_weights, df['ruca_ordinal'].values)
        
        # Count nearby neighbors
        df['n_neighbors_50km'] = (distances < 50).sum(axis=1) - 1  # Exclude self
        df['n_neighbors_25km'] = (distances < 25).sum(axis=1) - 1
        
        print(f"   Created spatial lag variables using {max_distance}km neighborhood")
        print(f"   Average neighbors within 50km: {df['n_neighbors_50km'].mean():.1f}")
        print(f"   Average neighbors within 25km: {df['n_neighbors_25km'].mean():.1f}")
        
        return df
    
    def create_model_specifications(self, df, ruca_categorical_cols, grouped_categorical_cols):
        """Create different model specifications with various RUCA encodings"""
        
        base_features = ['zip_centroid_lat', 'zip_centroid_lon']
        spatial_features = ['spatial_lag_broadband', 'spatial_lag_ruca', 'n_neighbors_50km', 'n_neighbors_25km']
        
        specifications = {
            'ruca_ordinal': {
                'features': base_features + ['ruca_ordinal'],
                'name': 'RUCA Ordinal Only'
            },
            'ruca_categorical': {
                'features': base_features + ruca_categorical_cols,
                'name': 'RUCA Categorical (One-Hot)'
            },
            'ruca_grouped': {
                'features': base_features + grouped_categorical_cols,
                'name': 'RUCA Grouped Categories'
            },
            'spatial_ordinal': {
                'features': base_features + ['ruca_ordinal'] + spatial_features,
                'name': 'Spatial + RUCA Ordinal'
            },
            'spatial_categorical': {
                'features': base_features + ruca_categorical_cols + spatial_features,
                'name': 'Spatial + RUCA Categorical'
            },
            'spatial_grouped': {
                'features': base_features + grouped_categorical_cols + spatial_features,
                'name': 'Spatial + RUCA Grouped'
            }
        }
        
        print(f"\n📋 Model specifications created:")
        for spec_name, spec in specifications.items():
            print(f"   {spec_name}: {len(spec['features'])} features ({spec['name']})")
        
        return specifications
    
    def get_model_suite(self):
        """Define comprehensive model suite"""
        models = {
            'ridge': Ridge(alpha=1.0),
            'ridge_strong': Ridge(alpha=10.0),
            'lasso': Lasso(alpha=0.1, max_iter=2000),
            'elastic_net': ElasticNet(alpha=0.1, l1_ratio=0.5, max_iter=2000),
            'random_forest': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
            'gradient_boost': GradientBoostingRegressor(n_estimators=100, max_depth=6, random_state=42),
            'decision_tree': DecisionTreeRegressor(max_depth=8, random_state=42),
            'svr_linear': SVR(kernel='linear', C=1.0),
            'svr_rbf': SVR(kernel='rbf', C=1.0, gamma='scale')
        }
        
        return models
    
    def perform_spatial_cross_validation(self, X, y, model, df, cv_folds=5):
        """Perform spatial cross-validation to avoid spatial autocorrelation"""
        
        # Create spatial clusters for cross-validation
        coords = df[['zip_centroid_lat', 'zip_centroid_lon']].values
        
        # Simple latitude-based stratification for spatial CV
        df_cv = df.copy()
        df_cv['lat_quartile'] = pd.qcut(df_cv['zip_centroid_lat'], q=cv_folds, labels=False)
        
        # Use GroupKFold with latitude quartiles as groups
        cv = GroupKFold(n_splits=cv_folds)
        groups = df_cv['lat_quartile']
        
        try:
            scores = cross_val_score(model, X, y, cv=cv, groups=groups, scoring='r2')
            return scores
        except Exception as e:
            print(f"     Warning: Spatial CV failed ({e}), using regular CV")
            scores = cross_val_score(model, X, y, cv=cv_folds, scoring='r2')
            return scores
    
    def run_comprehensive_analysis(self):
        """Run comprehensive ML analysis with all model and encoding combinations"""
        
        print("🚀 COMPREHENSIVE ML SUITE WITH SPATIAL REGRESSION")
        print("="*80)
        
        # Load and prepare data
        df = self.load_and_prepare_data()
        df, ruca_categorical_cols, grouped_categorical_cols = self.create_ruca_encodings(df)
        df = self.create_spatial_features(df)
        
        # Create model specifications
        specifications = self.create_model_specifications(df, ruca_categorical_cols, grouped_categorical_cols)
        
        # Get model suite
        models = self.get_model_suite()
        
        # Target variable
        y = df['broadband_usage'].values
        
        print(f"\n🧪 Running analysis: {len(specifications)} specifications × {len(models)} models = {len(specifications) * len(models)} combinations")
        print("="*80)
        
        results = []
        
        for spec_name, spec in specifications.items():
            print(f"\n📊 Testing: {spec['name']}")
            print("-" * 50)
            
            # Prepare features
            X = df[spec['features']].values
            
            # Ensure numeric types and handle any missing values
            X = X.astype(float)
            if np.any(np.isnan(X)):
                print(f"   ⚠️ Found {np.sum(np.isnan(X))} missing values, filling with median")
                from sklearn.impute import SimpleImputer
                imputer = SimpleImputer(strategy='median')
                X = imputer.fit_transform(X)
            
            # Standardize features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            print(f"   Features: {len(spec['features'])} ({X_scaled.shape})")
            
            for model_name, model in models.items():
                try:
                    # Perform spatial cross-validation
                    cv_scores = self.perform_spatial_cross_validation(X_scaled, y, model, df)
                    
                    # Calculate statistics
                    mean_score = np.mean(cv_scores)
                    std_score = np.std(cv_scores)
                    
                    # Fit full model for additional metrics
                    model.fit(X_scaled, y)
                    y_pred = model.predict(X_scaled)
                    full_r2 = r2_score(y, y_pred)
                    rmse = np.sqrt(mean_squared_error(y, y_pred))
                    
                    results.append({
                        'specification': spec_name,
                        'spec_name': spec['name'],
                        'model': model_name,
                        'cv_r2_mean': mean_score,
                        'cv_r2_std': std_score,
                        'full_r2': full_r2,
                        'rmse': rmse,
                        'n_features': len(spec['features']),
                        'features': spec['features']
                    })
                    
                    print(f"   {model_name:15s}: CV R² = {mean_score:+.3f} ± {std_score:.3f} | Full R² = {full_r2:+.3f}")
                    
                except Exception as e:
                    print(f"   {model_name:15s}: FAILED - {e}")
                    results.append({
                        'specification': spec_name,
                        'spec_name': spec['name'],
                        'model': model_name,
                        'cv_r2_mean': np.nan,
                        'cv_r2_std': np.nan,
                        'full_r2': np.nan,
                        'rmse': np.nan,
                        'n_features': len(spec['features']),
                        'features': spec['features']
                    })
        
        # Convert to DataFrame for analysis
        results_df = pd.DataFrame(results)
        
        # Remove failed results
        results_df = results_df.dropna(subset=['cv_r2_mean'])
        
        self.results = results_df
        return results_df
    
    def analyze_ruca_encoding_comparison(self, results_df):
        """Compare performance across different RUCA encodings"""
        
        print(f"\n📈 RUCA ENCODING COMPARISON")
        print("="*80)
        
        # Group by encoding type
        encoding_performance = {}
        
        for spec in ['ruca_ordinal', 'ruca_categorical', 'ruca_grouped']:
            spec_results = results_df[results_df['specification'] == spec]
            if len(spec_results) > 0:
                best_result = spec_results.loc[spec_results['cv_r2_mean'].idxmax()]
                mean_performance = spec_results['cv_r2_mean'].mean()
                
                encoding_performance[spec] = {
                    'best_model': best_result['model'],
                    'best_r2': best_result['cv_r2_mean'],
                    'best_std': best_result['cv_r2_std'],
                    'mean_r2': mean_performance,
                    'n_features': best_result['n_features']
                }
        
        print("RUCA Encoding Performance (Best Model per Encoding):")
        print("-" * 60)
        for encoding, perf in encoding_performance.items():
            encoding_name = {
                'ruca_ordinal': 'Ordinal (1-10)',
                'ruca_categorical': 'Categorical (One-Hot)', 
                'ruca_grouped': 'Grouped (4 Categories)'
            }[encoding]
            
            print(f"{encoding_name:25s}: {perf['best_model']:15s} | "
                  f"R² = {perf['best_r2']:+.3f} ± {perf['best_std']:.3f} | "
                  f"Features: {perf['n_features']}")
        
        # Statistical comparison
        print(f"\nEncoding Comparison Summary:")
        if len(encoding_performance) >= 2:
            best_encoding = max(encoding_performance.keys(), key=lambda x: encoding_performance[x]['best_r2'])
            best_perf = encoding_performance[best_encoding]
            
            print(f"   🏆 Best Encoding: {best_encoding} (R² = {best_perf['best_r2']:+.3f})")
            print(f"   📊 Performance spread: {min(p['best_r2'] for p in encoding_performance.values()):+.3f} to {max(p['best_r2'] for p in encoding_performance.values()):+.3f}")
            
            # Effect of encoding choice
            ordinal_r2 = encoding_performance.get('ruca_ordinal', {}).get('best_r2', np.nan)
            categorical_r2 = encoding_performance.get('ruca_categorical', {}).get('best_r2', np.nan)
            
            if not np.isnan(ordinal_r2) and not np.isnan(categorical_r2):
                encoding_effect = categorical_r2 - ordinal_r2
                print(f"   📈 Categorical vs Ordinal: {encoding_effect:+.3f} R² difference")
                
                if encoding_effect > 0.01:
                    print(f"      ✅ Categorical encoding shows meaningful improvement")
                elif encoding_effect < -0.01:
                    print(f"      ⚠️ Ordinal encoding performs better (unexpected)")
                else:
                    print(f"      ➡️ Minimal difference between encoding approaches")
    
    def analyze_spatial_effects(self, results_df):
        """Analyze the effect of spatial features"""
        
        print(f"\n🌍 SPATIAL REGRESSION ANALYSIS")
        print("="*80)
        
        # Compare specifications with and without spatial features
        comparisons = [
            ('ruca_ordinal', 'spatial_ordinal'),
            ('ruca_categorical', 'spatial_categorical'),
            ('ruca_grouped', 'spatial_grouped')
        ]
        
        print("Spatial Feature Effects (Best Model per Specification):")
        print("-" * 70)
        
        for base_spec, spatial_spec in comparisons:
            base_results = results_df[results_df['specification'] == base_spec]
            spatial_results = results_df[results_df['specification'] == spatial_spec]
            
            if len(base_results) > 0 and len(spatial_results) > 0:
                best_base = base_results.loc[base_results['cv_r2_mean'].idxmax()]
                best_spatial = spatial_results.loc[spatial_results['cv_r2_mean'].idxmax()]
                
                spatial_improvement = best_spatial['cv_r2_mean'] - best_base['cv_r2_mean']
                
                print(f"{base_spec:20s} → {spatial_spec:20s}")
                print(f"   Base:    {best_base['model']:15s} | R² = {best_base['cv_r2_mean']:+.3f} ± {best_base['cv_r2_std']:.3f}")
                print(f"   Spatial: {best_spatial['model']:15s} | R² = {best_spatial['cv_r2_mean']:+.3f} ± {best_spatial['cv_r2_std']:.3f}")
                print(f"   📈 Improvement: {spatial_improvement:+.3f} R² points")
                print()
        
        # Overall spatial effects
        base_specs = ['ruca_ordinal', 'ruca_categorical', 'ruca_grouped']
        spatial_specs = ['spatial_ordinal', 'spatial_categorical', 'spatial_grouped']
        
        base_performance = results_df[results_df['specification'].isin(base_specs)]['cv_r2_mean']
        spatial_performance = results_df[results_df['specification'].isin(spatial_specs)]['cv_r2_mean']
        
        if len(base_performance) > 0 and len(spatial_performance) > 0:
            base_mean = base_performance.mean()
            spatial_mean = spatial_performance.mean()
            overall_improvement = spatial_mean - base_mean
            
            print(f"Overall Spatial Effects:")
            print(f"   Base models (mean):    {base_mean:+.3f} R²")
            print(f"   Spatial models (mean): {spatial_mean:+.3f} R²") 
            print(f"   📈 Average improvement: {overall_improvement:+.3f} R² points")
            
            if overall_improvement > 0.01:
                print(f"      ✅ Spatial features provide meaningful improvement")
            elif overall_improvement > 0.005:
                print(f"      📊 Spatial features provide modest improvement")
            else:
                print(f"      ➡️ Minimal spatial effects detected")
    
    def print_top_performers(self, results_df, top_n=10):
        """Print top performing models overall"""
        
        print(f"\n🏆 TOP {top_n} PERFORMING MODELS")
        print("="*80)
        
        # Sort by CV R² score
        top_models = results_df.nlargest(top_n, 'cv_r2_mean')
        
        print("Rank | Specification              | Model           | CV R²     | Full R² | Features")
        print("-" * 85)
        
        for i, (_, row) in enumerate(top_models.iterrows(), 1):
            print(f"{i:3d}  | {row['spec_name']:25s} | {row['model']:15s} | "
                  f"{row['cv_r2_mean']:+.3f}±{row['cv_r2_std']:.3f} | "
                  f"{row['full_r2']:+.3f} | {row['n_features']:2d}")
        
        # Best model details
        best_model = top_models.iloc[0]
        print(f"\n🥇 BEST MODEL:")
        print(f"   Specification: {best_model['spec_name']}")
        print(f"   Algorithm: {best_model['model']}")
        print(f"   CV Performance: {best_model['cv_r2_mean']:+.3f} ± {best_model['cv_r2_std']:.3f} R²")
        print(f"   Full Dataset R²: {best_model['full_r2']:+.3f}")
        print(f"   RMSE: {best_model['rmse']:.4f}")
        print(f"   Features ({best_model['n_features']}): {', '.join(best_model['features'][:5])}...")
    
    def generate_summary_report(self, results_df):
        """Generate comprehensive summary report"""
        
        print(f"\n📋 COMPREHENSIVE SUMMARY REPORT")
        print("="*80)
        
        print(f"Analysis Overview:")
        print(f"   Models tested: {len(results_df)}")
        print(f"   Specifications: {results_df['specification'].nunique()}")
        print(f"   Algorithms: {results_df['model'].nunique()}")
        print(f"   ZIP codes: {len(pd.read_csv(self.data_path))}")
        
        # Performance statistics
        print(f"\nPerformance Statistics:")
        print(f"   Best CV R²: {results_df['cv_r2_mean'].max():+.3f}")
        print(f"   Worst CV R²: {results_df['cv_r2_mean'].min():+.3f}")
        print(f"   Mean CV R²: {results_df['cv_r2_mean'].mean():+.3f}")
        print(f"   Median CV R²: {results_df['cv_r2_mean'].median():+.3f}")
        
        # Model algorithm performance
        print(f"\nBest Algorithm per Category:")
        model_performance = results_df.groupby('model')['cv_r2_mean'].agg(['mean', 'max', 'count']).round(3)
        model_performance = model_performance.sort_values('max', ascending=False)
        
        for model, stats in model_performance.head(5).iterrows():
            print(f"   {model:15s}: Best = {stats['max']:+.3f}, Mean = {stats['mean']:+.3f} (n={int(stats['count'])})")
        
        # Key findings
        print(f"\n🔍 KEY FINDINGS:")
        
        # 1. RUCA encoding findings
        ordinal_best = results_df[results_df['specification'] == 'ruca_ordinal']['cv_r2_mean'].max()
        categorical_best = results_df[results_df['specification'] == 'ruca_categorical']['cv_r2_mean'].max()
        
        if not np.isnan(ordinal_best) and not np.isnan(categorical_best):
            if categorical_best > ordinal_best + 0.01:
                print(f"   ✅ Categorical RUCA encoding outperforms ordinal by {categorical_best - ordinal_best:+.3f} R²")
            elif ordinal_best > categorical_best + 0.01:
                print(f"   ⚠️ Ordinal RUCA encoding unexpectedly outperforms categorical by {ordinal_best - categorical_best:+.3f} R²")
            else:
                print(f"   ➡️ Minimal difference between RUCA encoding approaches ({abs(categorical_best - ordinal_best):.3f} R²)")
        
        # 2. Spatial effects
        base_best = results_df[results_df['specification'].isin(['ruca_ordinal', 'ruca_categorical', 'ruca_grouped'])]['cv_r2_mean'].max()
        spatial_best = results_df[results_df['specification'].isin(['spatial_ordinal', 'spatial_categorical', 'spatial_grouped'])]['cv_r2_mean'].max()
        
        if not np.isnan(base_best) and not np.isnan(spatial_best):
            spatial_effect = spatial_best - base_best
            if spatial_effect > 0.01:
                print(f"   🌍 Spatial features provide substantial improvement: {spatial_effect:+.3f} R²")
            elif spatial_effect > 0.005:
                print(f"   🌍 Spatial features provide modest improvement: {spatial_effect:+.3f} R²")
            else:
                print(f"   🌍 Minimal spatial autocorrelation effects: {spatial_effect:+.3f} R²")
        
        # 3. Best overall approach
        best_overall = results_df.loc[results_df['cv_r2_mean'].idxmax()]
        print(f"   🏆 Best overall approach: {best_overall['spec_name']} with {best_overall['model']} (R² = {best_overall['cv_r2_mean']:+.3f})")
        
        print("="*80)

def main():
    """Run comprehensive ML suite with spatial regression and proper RUCA encoding"""
    
    suite = ComprehensiveMLSuite()
    
    # Run comprehensive analysis
    results_df = suite.run_comprehensive_analysis()
    
    # Analyze results
    suite.analyze_ruca_encoding_comparison(results_df)
    suite.analyze_spatial_effects(results_df)
    suite.print_top_performers(results_df)
    suite.generate_summary_report(results_df)
    
    # Save results
    output_path = Path("results/comprehensive_ml_results.csv")
    output_path.parent.mkdir(exist_ok=True)
    results_df.to_csv(output_path, index=False)
    print(f"\n💾 Results saved to: {output_path}")

if __name__ == "__main__":
    main()
