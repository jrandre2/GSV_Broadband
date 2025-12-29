#!/usr/bin/env python3
"""
Degrees of Freedom Analysis for Nonlinear Regression Models
===========================================================
Analyzing why p-values are high despite large apparent sample sizes
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

def analyze_degrees_of_freedom():
    """
    Analyze the degrees of freedom problem in our nonlinear regression analysis
    """
    
    print("🔢 DEGREES OF FREEDOM ANALYSIS")
    print("="*60)
    
    # From the analysis output, extract key statistics
    print("📊 SAMPLE SIZE vs DEGREES OF FREEDOM BREAKDOWN:")
    print("="*60)
    
    # Key numbers from the analysis output
    total_buildings = 1903  # From manifest
    
    # For k=10 (optimal), from the output:
    k10_analysis = {
        'spatial_clusters': 97,
        'viable_clusters_20+': 12,
        'selected_clusters': 6,
        'buildings_in_cv': 970,
        'cv_folds': 6,
        'effective_sample_per_fold': 970 // 6  # ~161 per fold
    }
    
    print(f"1. TOTAL DATA AVAILABLE:")
    print(f"   • Total buildings: {total_buildings:,}")
    print(f"   • With exact coordinates: {total_buildings:,}")
    
    print(f"\n2. SPATIAL CLUSTERING CONSTRAINTS:")
    print(f"   • Spatial clusters created: {k10_analysis['spatial_clusters']}")
    print(f"   • Clusters viable for CV (≥20 buildings): {k10_analysis['viable_clusters_20+']}")
    print(f"   • Actually selected for analysis: {k10_analysis['selected_clusters']}")
    print(f"   • Reason: Need spatially separated folds to avoid autocorrelation")
    
    print(f"\n3. CROSS-VALIDATION SAMPLE REDUCTION:")
    print(f"   • Buildings used in CV: {k10_analysis['buildings_in_cv']:,}")
    print(f"   • Reduction factor: {k10_analysis['buildings_in_cv']/total_buildings:.1%}")
    print(f"   • CV folds: {k10_analysis['cv_folds']}")
    print(f"   • Test set size per fold: ~{k10_analysis['effective_sample_per_fold']}")
    
    print(f"\n4. DEGREES OF FREEDOM FOR STATISTICAL TESTS:")
    print("="*60)
    
    # The key issue: We're testing improvements across CV folds, not individual buildings
    df_for_ttest = k10_analysis['cv_folds'] - 1  # 6-1 = 5 degrees of freedom
    n_comparisons = k10_analysis['cv_folds']     # 6 fold-level improvements
    
    print(f"   • Statistical test: One-sample t-test on CV fold improvements")
    print(f"   • Sample size for t-test: {n_comparisons} (fold-level improvements)")
    print(f"   • Degrees of freedom: {df_for_ttest}")
    print(f"   • NOT {k10_analysis['buildings_in_cv']:,} buildings (that would be pseudoreplication)")
    
    print(f"\n🚨 THE DEGREES OF FREEDOM PROBLEM:")
    print("="*60)
    print(f"   • We have {df_for_ttest} degrees of freedom, NOT {k10_analysis['buildings_in_cv']:,}")
    print(f"   • Each 'observation' is a spatially-independent fold improvement")
    print(f"   • High p-values make sense with only {n_comparisons} independent samples")
    print(f"   • This is the correct approach to avoid spatial pseudoreplication")
    
    # Calculate power analysis
    print(f"\n📈 STATISTICAL POWER ANALYSIS:")
    print("="*60)
    
    # From the analysis, typical improvements and standard deviations
    example_results = {
        'Polynomial_3': {'improvement': 1.307, 'std': 3.019, 'n_folds': 6},
        'SVR_RBF': {'improvement': 0.846, 'std': 2.322, 'n_folds': 6},
        'Decision_Tree': {'improvement': 1.137, 'std': 2.740, 'n_folds': 6}
    }
    
    for model, stats_dict in example_results.items():
        n = stats_dict['n_folds']
        mean_imp = stats_dict['improvement']
        std_imp = stats_dict['std']
        
        # Calculate observed t-statistic
        t_obs = mean_imp / (std_imp / np.sqrt(n))
        
        # Critical t-value for df=n-1, alpha=0.05 (two-tailed)
        t_crit = stats.t.ppf(0.975, df=n-1)
        
        # Calculate effect size (Cohen's d)
        cohens_d = mean_imp / std_imp
        
        # Power calculation (approximate)
        # For power analysis, we need the non-central t-distribution
        from scipy.stats import nct
        power = 1 - nct.cdf(t_crit, df=n-1, nc=np.sqrt(n)*cohens_d)
        
        print(f"\n   {model.replace('_', ' ')}:")
        print(f"     • Observed t = {t_obs:.3f}, Critical t = {t_crit:.3f}")
        print(f"     • Effect size (Cohen's d) = {cohens_d:.3f}")
        print(f"     • Statistical power ≈ {power:.1%}")
        print(f"     • Need |t| > {t_crit:.2f} for significance")
    
    print(f"\n💡 POWER TO DETECT MEANINGFUL EFFECTS:")
    print("="*60)
    
    # Calculate required effect sizes for 80% power
    n = 6  # Number of CV folds
    df = n - 1
    alpha = 0.05
    target_power = 0.8
    
    # For 80% power, what effect size do we need?
    from scipy.optimize import minimize_scalar
    
    def power_function(effect_size):
        nc = np.sqrt(n) * effect_size  # Non-centrality parameter
        t_crit = stats.t.ppf(1 - alpha/2, df)
        power = 1 - nct.cdf(t_crit, df, nc) + nct.cdf(-t_crit, df, nc)
        return abs(power - target_power)
    
    result = minimize_scalar(power_function, bounds=(0, 5), method='bounded')
    required_effect_size = result.x
    
    print(f"   • For 80% power with n={n} folds:")
    print(f"     • Required Cohen's d ≥ {required_effect_size:.2f}")
    print(f"     • Our observed d values: 0.43, 0.36, 0.41 (all below threshold)")
    print(f"     • This explains the high p-values!")
    
    print(f"\n🎯 SOLUTIONS TO INCREASE STATISTICAL POWER:")
    print("="*60)
    print(f"   1. MORE CV FOLDS:")
    print(f"      • Current: {n} folds → df={df}")
    print(f"      • Need more viable spatial clusters")
    print(f"      • Requires more geographic diversity in data")
    
    print(f"\n   2. LARGER EFFECT SIZES:")
    print(f"      • Current improvements: 0.8-1.3 R² points")
    print(f"      • High variance: ±2.3-3.0 R² points")
    print(f"      • Need stronger or more consistent nonlinear relationships")
    
    print(f"\n   3. REDUCE FOLD-TO-FOLD VARIANCE:")
    print(f"      • Current high variance suggests geographic heterogeneity")
    print(f"      • Could stratify by urban/rural before clustering")
    print(f"      • More homogeneous regions = more consistent effects")
    
    print(f"\n   4. ALTERNATIVE STATISTICAL APPROACHES:")
    print(f"      • Hierarchical/mixed-effects models")
    print(f"      • Permutation tests")
    print(f"      • Bayesian approaches with proper spatial priors")
    
    return {
        'df': df_for_ttest,
        'n_folds': n_comparisons,
        'buildings_per_fold': k10_analysis['effective_sample_per_fold'],
        'total_buildings_in_cv': k10_analysis['buildings_in_cv'],
        'required_effect_size': required_effect_size
    }

def demonstrate_pseudoreplication_problem():
    """
    Demonstrate why we can't use all building-level observations
    """
    
    print(f"\n🚫 WHY WE CAN'T USE ALL {970} BUILDINGS AS DF:")
    print("="*60)
    
    print(f"   SPATIAL AUTOCORRELATION PROBLEM:")
    print(f"   • Buildings in same geographic area are NOT independent")
    print(f"   • They share neighborhood effects, local infrastructure, etc.")
    print(f"   • Using all buildings would be 'spatial pseudoreplication'")
    print(f"   • Would severely inflate Type I error (false positives)")
    
    print(f"\n   CORRECT APPROACH:")
    print(f"   • Use spatially-separated clusters as independent units")
    print(f"   • Each CV fold represents one independent geographic region")
    print(f"   • Fold-level improvements are the true independent observations")
    print(f"   • This gives conservative but valid statistical inference")
    
    print(f"\n   TRADE-OFF:")
    print(f"   • Spatial independence: ✅ Correct")
    print(f"   • Statistical power: ❌ Limited by small n")
    print(f"   • This is fundamental tension in spatial analysis")

if __name__ == "__main__":
    results = analyze_degrees_of_freedom()
    demonstrate_pseudoreplication_problem()
    
    print(f"\n🏁 SUMMARY:")
    print("="*60)
    print(f"   • True degrees of freedom: {results['df']} (not 970)")
    print(f"   • High p-values are statistically correct")
    print(f"   • Need effect size ≥ {results['required_effect_size']:.2f} for 80% power")
    print(f"   • Current approach avoids spatial pseudoreplication")
    print(f"   • Trade power for statistical validity")
