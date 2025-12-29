#!/usr/bin/env python3
"""
RUCA Correlation vs Predictive Performance Analysis
=================================================
Investigating why high correlation doesn't translate to good R² performance
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.model_selection import cross_val_score, GroupKFold
import warnings
warnings.filterwarnings('ignore')

class CorrelationVsPredictionAnalysis:
    """Analyze why high correlation doesn't translate to good predictive performance"""
    
    def __init__(self):
        self.data_path = "data/processed/broadband_labels_with_ruca.csv"
        
    def load_and_examine_data(self):
        """Load data and examine basic relationships"""
        print("="*80)
        print("🔍 CORRELATION vs PREDICTIVE PERFORMANCE ANALYSIS")
        print("="*80)
        print("Investigating: High correlation but poor R² performance")
        
        df = pd.read_csv(self.data_path)
        print(f"\nDataset: {len(df)} ZIP codes")
        
        # Basic statistics
        print(f"\n📊 BASIC STATISTICS:")
        print(f"Broadband usage: {df['broadband_usage'].mean():.3f} ± {df['broadband_usage'].std():.3f}")
        print(f"RUCA codes: {df['RUCA1'].min()}-{df['RUCA1'].max()} (median: {df['RUCA1'].median()})")
        print(f"RUCA distribution: {df['RUCA1'].value_counts().sort_index().to_dict()}")
        
        return df
    
    def calculate_correlations(self, df):
        """Calculate different types of correlations"""
        print(f"\n🔗 CORRELATION ANALYSIS:")
        print("-" * 50)
        
        # Pearson correlation (linear relationship)
        pearson_r, pearson_p = pearsonr(df['RUCA1'], df['broadband_usage'])
        
        # Spearman correlation (rank-order relationship)
        spearman_r, spearman_p = spearmanr(df['RUCA1'], df['broadband_usage'])
        
        print(f"Pearson correlation:  r = {pearson_r:.4f}, p = {pearson_p:.6f}")
        print(f"Spearman correlation: ρ = {spearman_r:.4f}, p = {spearman_p:.6f}")
        
        # R² from simple linear regression
        X = df[['RUCA1']].values
        y = df['broadband_usage'].values
        
        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        r2_simple = r2_score(y, y_pred)
        
        print(f"Simple regression R²: {r2_simple:.4f}")
        print(f"R² vs r² relationship: {r2_simple:.4f} vs {pearson_r**2:.4f}")
        
        # Explained: R² should equal r² for simple linear regression
        print(f"✓ R² = r² check: {abs(r2_simple - pearson_r**2) < 0.001}")
        
        return pearson_r, spearman_r, r2_simple
    
    def analyze_data_structure(self, df):
        """Analyze the structure of the data that might affect predictions"""
        print(f"\n🏗️ DATA STRUCTURE ANALYSIS:")
        print("-" * 50)
        
        # Sample size per RUCA code
        ruca_counts = df['RUCA1'].value_counts().sort_index()
        print(f"Sample sizes by RUCA:")
        for ruca, count in ruca_counts.items():
            pct = count / len(df) * 100
            mean_bb = df[df['RUCA1'] == ruca]['broadband_usage'].mean()
            std_bb = df[df['RUCA1'] == ruca]['broadband_usage'].std()
            print(f"  RUCA {ruca}: n={count:3d} ({pct:4.1f}%) | BB: {mean_bb:.3f} ± {std_bb:.3f}")
        
        # Variance within vs between groups
        total_var = df['broadband_usage'].var()
        
        # Between-group variance (how much RUCA explains)
        group_means = df.groupby('RUCA1')['broadband_usage'].mean()
        overall_mean = df['broadband_usage'].mean()
        between_var = sum(ruca_counts * (group_means - overall_mean)**2) / len(df)
        
        # Within-group variance (residual variance)
        within_var = total_var - between_var
        
        print(f"\nVariance decomposition:")
        print(f"  Total variance:        {total_var:.6f}")
        print(f"  Between-group (RUCA):  {between_var:.6f} ({between_var/total_var*100:.1f}%)")
        print(f"  Within-group (residual): {within_var:.6f} ({within_var/total_var*100:.1f}%)")
        print(f"  Eta-squared (η²):      {between_var/total_var:.4f}")
        
        return ruca_counts, between_var, within_var, total_var
    
    def cross_validation_analysis(self, df):
        """Analyze why cross-validation R² differs from simple R²"""
        print(f"\n🔄 CROSS-VALIDATION vs SIMPLE R² ANALYSIS:")
        print("-" * 50)
        
        X = df[['RUCA1']].values
        y = df['broadband_usage'].values
        
        # Simple R² (training = testing)
        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        simple_r2 = r2_score(y, y_pred)
        
        # Standard K-fold CV
        cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
        cv_mean = cv_scores.mean()
        cv_std = cv_scores.std()
        
        print(f"Simple R² (no CV):     {simple_r2:.4f}")
        print(f"5-fold CV R²:         {cv_mean:.4f} ± {cv_std:.4f}")
        print(f"CV degradation:       {simple_r2 - cv_mean:+.4f} R² points")
        
        # Spatial clustering analysis (if applicable)
        if 'zip' in df.columns:
            # Create crude spatial groups by ZIP code first digits
            df['zip_region'] = df['zip'].astype(str).str[:3]
            spatial_groups = df['zip_region']
            
            # Spatial CV using GroupKFold
            group_cv = GroupKFold(n_splits=min(5, spatial_groups.nunique()))
            
            try:
                spatial_cv_scores = cross_val_score(model, X, y, cv=group_cv, groups=spatial_groups, scoring='r2')
                spatial_cv_mean = spatial_cv_scores.mean()
                spatial_cv_std = spatial_cv_scores.std()
                
                print(f"Spatial Group CV R²:  {spatial_cv_mean:.4f} ± {spatial_cv_std:.4f}")
                print(f"Spatial degradation:  {simple_r2 - spatial_cv_mean:+.4f} R² points")
                
            except Exception as e:
                print(f"Spatial CV failed: {e}")
                spatial_cv_mean = np.nan
        
        else:
            spatial_cv_mean = np.nan
        
        return simple_r2, cv_mean, spatial_cv_mean
    
    def investigate_outliers_and_leverage(self, df):
        """Investigate outliers and high-leverage points"""
        print(f"\n🎯 OUTLIERS AND LEVERAGE ANALYSIS:")
        print("-" * 50)
        
        X = df[['RUCA1']].values
        y = df['broadband_usage'].values
        
        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        residuals = y - y_pred
        
        # Standardized residuals
        residual_std = np.std(residuals)
        standardized_residuals = residuals / residual_std
        
        # Leverage (for simple regression: how far RUCA is from mean)
        ruca_mean = np.mean(X)
        ruca_var = np.var(X)
        leverage = 1/len(X) + (X - ruca_mean)**2 / (len(X) * ruca_var)
        
        # Cook's distance
        p = 1  # number of parameters (just RUCA)
        cooks_d = (standardized_residuals**2 / p) * (leverage.flatten() / (1 - leverage.flatten()))
        
        # Identify problematic points
        high_residual = np.abs(standardized_residuals) > 2
        high_leverage = leverage.flatten() > 2 * (p + 1) / len(X)
        high_cooks = cooks_d > 4 / len(X)
        
        print(f"Residual analysis:")
        print(f"  High residuals (|z| > 2):     {np.sum(high_residual)} ZIPs ({np.sum(high_residual)/len(df)*100:.1f}%)")
        print(f"  High leverage points:         {np.sum(high_leverage)} ZIPs ({np.sum(high_leverage)/len(df)*100:.1f}%)")
        print(f"  High Cook's distance:         {np.sum(high_cooks)} ZIPs ({np.sum(high_cooks)/len(df)*100:.1f}%)")
        
        # Show most problematic cases
        df_analysis = df.copy()
        df_analysis['residual'] = residuals
        df_analysis['standardized_residual'] = standardized_residuals
        df_analysis['leverage'] = leverage.flatten()
        df_analysis['cooks_d'] = cooks_d
        
        # Most extreme cases
        extreme_cases = df_analysis[high_residual | high_leverage | high_cooks].copy()
        
        if len(extreme_cases) > 0:
            print(f"\nMost problematic cases:")
            extreme_cases = extreme_cases.sort_values('cooks_d', ascending=False)
            for _, row in extreme_cases.head(5).iterrows():
                print(f"  ZIP {row['zip']}: RUCA={row['RUCA1']}, BB={row['broadband_usage']:.3f}, "
                      f"Residual={row['standardized_residual']:+.2f}σ, Cook's D={row['cooks_d']:.4f}")
        
        return df_analysis
    
    def sample_size_simulation(self, df):
        """Simulate how sample size affects R² stability"""
        print(f"\n📈 SAMPLE SIZE vs R² STABILITY:")
        print("-" * 50)
        
        X = df[['RUCA1']].values
        y = df['broadband_usage'].values
        
        # Test different sample sizes
        sample_sizes = [50, 100, 150, 200, len(df)]
        n_simulations = 100
        
        results = {}
        
        for n in sample_sizes:
            if n >= len(df):
                # Use full dataset
                r2_values = []
                for _ in range(n_simulations):
                    # Bootstrap sampling
                    indices = np.random.choice(len(df), size=len(df), replace=True)
                    X_sample, y_sample = X[indices], y[indices]
                    
                    model = LinearRegression()
                    model.fit(X_sample, y_sample)
                    y_pred = model.predict(X_sample)
                    r2 = r2_score(y_sample, y_pred)
                    r2_values.append(r2)
            else:
                # Random subsampling
                r2_values = []
                for _ in range(n_simulations):
                    indices = np.random.choice(len(df), size=n, replace=False)
                    X_sample, y_sample = X[indices], y[indices]
                    
                    model = LinearRegression()
                    model.fit(X_sample, y_sample)
                    y_pred = model.predict(X_sample)
                    r2 = r2_score(y_sample, y_pred)
                    r2_values.append(r2)
            
            results[n] = {
                'mean_r2': np.mean(r2_values),
                'std_r2': np.std(r2_values),
                'r2_values': r2_values
            }
            
            print(f"  n={n:3d}: R² = {np.mean(r2_values):.4f} ± {np.std(r2_values):.4f}")
        
        return results
    
    def visualize_relationships(self, df):
        """Create visualizations to understand the relationships"""
        print(f"\n📊 Creating visualizations...")
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('RUCA vs Broadband Usage: Correlation vs Prediction Analysis', fontsize=14)
        
        # 1. Scatter plot with regression line
        ax1 = axes[0, 0]
        ax1.scatter(df['RUCA1'], df['broadband_usage'], alpha=0.6, s=30)
        
        # Add regression line
        X = df[['RUCA1']].values
        y = df['broadband_usage'].values
        model = LinearRegression()
        model.fit(X, y)
        x_line = np.linspace(df['RUCA1'].min(), df['RUCA1'].max(), 100)
        y_line = model.predict(x_line.reshape(-1, 1))
        ax1.plot(x_line, y_line, 'r-', linewidth=2)
        
        # Calculate correlation
        r, p = pearsonr(df['RUCA1'], df['broadband_usage'])
        r2 = r2_score(y, model.predict(X))
        
        ax1.set_xlabel('RUCA Code')
        ax1.set_ylabel('Broadband Usage')
        ax1.set_title(f'Linear Relationship\nr = {r:.4f}, R² = {r2:.4f}')
        ax1.grid(True, alpha=0.3)
        
        # 2. Box plot by RUCA code
        ax2 = axes[0, 1]
        ruca_codes = sorted(df['RUCA1'].unique())
        box_data = [df[df['RUCA1'] == ruca]['broadband_usage'] for ruca in ruca_codes]
        bp = ax2.boxplot(box_data, labels=ruca_codes, patch_artist=True)
        
        # Color boxes by sample size
        ruca_counts = df['RUCA1'].value_counts()
        for patch, ruca in zip(bp['boxes'], ruca_codes):
            count = ruca_counts[ruca]
            # Color intensity based on sample size
            intensity = min(count / 50, 1.0)  # Normalize to max of 50
            patch.set_facecolor(plt.cm.Blues(0.3 + 0.7 * intensity))
        
        ax2.set_xlabel('RUCA Code')
        ax2.set_ylabel('Broadband Usage')
        ax2.set_title('Distribution by RUCA\n(Color intensity = sample size)')
        ax2.grid(True, alpha=0.3)
        
        # 3. Residuals plot
        ax3 = axes[1, 0]
        residuals = y - model.predict(X)
        ax3.scatter(model.predict(X), residuals, alpha=0.6, s=30)
        ax3.axhline(y=0, color='r', linestyle='--')
        ax3.set_xlabel('Predicted Broadband Usage')
        ax3.set_ylabel('Residuals')
        ax3.set_title(f'Residuals vs Fitted\nStd Dev = {np.std(residuals):.4f}')
        ax3.grid(True, alpha=0.3)
        
        # 4. Sample size effect
        ax4 = axes[1, 1]
        ruca_counts = df['RUCA1'].value_counts().sort_index()
        ruca_means = df.groupby('RUCA1')['broadband_usage'].mean()
        ruca_stds = df.groupby('RUCA1')['broadband_usage'].std()
        
        ax4.errorbar(ruca_counts.index, ruca_means, yerr=ruca_stds, 
                    fmt='o', capsize=5, capthick=2, markersize=8)
        
        # Size of points proportional to sample size
        for ruca in ruca_counts.index:
            size = ruca_counts[ruca] * 2  # Scale factor
            ax4.scatter(ruca, ruca_means[ruca], s=size, alpha=0.3, color='red')
        
        ax4.set_xlabel('RUCA Code')
        ax4.set_ylabel('Mean Broadband Usage ± Std Dev')
        ax4.set_title('Means by RUCA\n(Point size = sample size)')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('ruca_correlation_analysis.png', dpi=300, bbox_inches='tight')
        print("   Saved: ruca_correlation_analysis.png")
        
        return fig
    
    def run_comprehensive_analysis(self):
        """Run the complete analysis"""
        
        # Load data
        df = self.load_and_examine_data()
        
        # Calculate correlations
        pearson_r, spearman_r, simple_r2 = self.calculate_correlations(df)
        
        # Analyze data structure
        ruca_counts, between_var, within_var, total_var = self.analyze_data_structure(df)
        
        # Cross-validation analysis
        simple_r2_cv, cv_mean, spatial_cv_mean = self.cross_validation_analysis(df)
        
        # Outlier analysis
        df_analysis = self.investigate_outliers_and_leverage(df)
        
        # Sample size effects
        sample_results = self.sample_size_simulation(df)
        
        # Visualizations
        fig = self.visualize_relationships(df)
        
        # Summary and conclusions
        self.print_conclusions(pearson_r, simple_r2, cv_mean, spatial_cv_mean, 
                             between_var, total_var, ruca_counts)
        
        return df_analysis
    
    def print_conclusions(self, pearson_r, simple_r2, cv_mean, spatial_cv_mean, 
                         between_var, total_var, ruca_counts):
        """Print final conclusions about correlation vs prediction discrepancy"""
        
        print(f"\n" + "="*80)
        print("🎯 CONCLUSIONS: Why High Correlation ≠ Good Prediction")
        print("="*80)
        
        print(f"📊 CORRELATION vs PREDICTION SUMMARY:")
        print(f"   Pearson correlation:    r = {pearson_r:.4f} ({'Strong' if abs(pearson_r) > 0.7 else 'Moderate' if abs(pearson_r) > 0.3 else 'Weak'})")
        print(f"   Simple regression R²:   {simple_r2:.4f}")
        print(f"   Cross-validation R²:    {cv_mean:.4f}")
        if not np.isnan(spatial_cv_mean):
            print(f"   Spatial CV R²:          {spatial_cv_mean:.4f}")
        
        print(f"\n🔍 KEY EXPLANATIONS:")
        
        # 1. Sample size and imbalance
        max_group = ruca_counts.max()
        min_group = ruca_counts.min()
        imbalance_ratio = max_group / min_group
        
        explanations = []
        
        if imbalance_ratio > 10:
            explanations.append(f"📉 SEVERE CLASS IMBALANCE: Largest group ({max_group}) vs smallest ({min_group}) = {imbalance_ratio:.1f}x")
            explanations.append(f"   → Correlation dominated by large groups, but prediction fails on small groups")
        
        # 2. Cross-validation penalty
        cv_penalty = simple_r2 - cv_mean
        if cv_penalty > 0.1:
            explanations.append(f"🔄 OVERFITTING DETECTED: CV penalty = {cv_penalty:.4f} R² points")
            explanations.append(f"   → Model memorizes training data but fails to generalize")
        
        # 3. Variance explained
        eta_squared = between_var / total_var
        if eta_squared < 0.15:
            explanations.append(f"📊 LOW VARIANCE EXPLAINED: η² = {eta_squared:.4f} ({eta_squared*100:.1f}%)")
            explanations.append(f"   → RUCA explains little of the total broadband variation")
        
        # 4. Spatial correlation issues
        if not np.isnan(spatial_cv_mean):
            spatial_penalty = cv_mean - spatial_cv_mean
            if spatial_penalty > 0.05:
                explanations.append(f"🗺️ SPATIAL CORRELATION: Additional penalty = {spatial_penalty:.4f} R² points")
                explanations.append(f"   → Geographic clustering violates independence assumption")
        
        # 5. Small sample size effects
        if len(ruca_counts) < 100:
            explanations.append(f"📊 SMALL SAMPLE SIZE: n = {sum(ruca_counts)} may lead to unstable estimates")
            explanations.append(f"   → High correlation might be sample-specific, not generalizable")
        
        for i, explanation in enumerate(explanations, 1):
            print(f"   {i}. {explanation}")
        
        print(f"\n💡 PRACTICAL IMPLICATIONS:")
        implications = [
            f"📈 Correlation measures linear association in your specific sample",
            f"🎯 R² measures how well the model predicts NEW, unseen data",
            f"⚠️ High correlation can be misleading with imbalanced or small samples",
            f"🔄 Cross-validation reveals the model's true predictive capability",
            f"🌍 Spatial/geographic clustering further reduces effective sample size"
        ]
        
        for implication in implications:
            print(f"   • {implication}")
        
        print(f"\n🎪 THE BOTTOM LINE:")
        if abs(pearson_r) > 0.5 and cv_mean < 0.1:
            print(f"   Your data shows a classic 'correlation trap':")
            print(f"   Strong correlation ({pearson_r:.3f}) but poor prediction (R² = {cv_mean:.3f})")
            print(f"   This suggests the relationship is not robust enough for reliable prediction.")
        elif cv_mean < 0:
            print(f"   Negative CV R² means your model performs WORSE than just predicting the mean!")
            print(f"   This indicates severe overfitting or fundamental model inadequacy.")
        else:
            print(f"   The relationship shows modest predictive value but requires careful interpretation.")
        
        print("="*80)

def main():
    """Run the correlation vs prediction analysis"""
    analyzer = CorrelationVsPredictionAnalysis()
    results = analyzer.run_comprehensive_analysis()
    return results

if __name__ == "__main__":
    main()
