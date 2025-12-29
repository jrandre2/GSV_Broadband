#!/usr/bin/env python3
"""
Simplified spatial CV analysis focusing on key performance patterns
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import GroupKFold, train_test_split
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score

# Load data
df = pd.read_csv('data/processed/broadband_labels_with_ruca.csv')
print(f"📍 Loaded {len(df)} ZIP codes")

# Create spatial groups using 4th digit of ZIP code
spatial_groups = df['zip'].astype(str).str[3].astype(int)
print(f"🗺️  Created {len(spatial_groups.unique())} spatial groups: {sorted(spatial_groups.unique())}")
print(f"   Group sizes: {[sum(spatial_groups == g) for g in sorted(spatial_groups.unique())]}")

# Simple baseline analysis
y = df['broadband_usage'].values
X_simple = df[['RUCA1']].values

print(f"\n🎯 Dataset overview:")
print(f"   RUCA1 correlation with broadband: {np.corrcoef(X_simple.flatten(), y)[0,1]:.3f}")
print(f"   RUCA1 values: {sorted(df['RUCA1'].unique())}")
print(f"   Broadband range: {y.min():.3f} to {y.max():.3f}")
print(f"   Mean broadband: {y.mean():.3f} ± {y.std():.3f}")

# Cross-validation analysis with 5 groups (as used in our optimizer)
# Filter to groups that have enough data for 5-fold CV
group_counts = spatial_groups.value_counts()
large_groups = group_counts[group_counts >= 10].index.tolist()
large_groups = sorted(large_groups)[:5]  # Take first 5 groups

print(f"\n🔍 Using 5 largest groups for CV: {large_groups}")

# Filter data to these groups
mask = spatial_groups.isin(large_groups)
X_filtered = X_simple[mask]
y_filtered = y[mask]
groups_filtered = spatial_groups[mask]

print(f"   Filtered dataset: {len(X_filtered)} samples")
print(f"   Filtered group sizes: {[sum(groups_filtered == g) for g in large_groups]}")

# Map groups to 0-4 for GroupKFold
group_mapping = {g: i for i, g in enumerate(large_groups)}
groups_mapped = groups_filtered.map(group_mapping)

cv = GroupKFold(n_splits=5)
train_scores = []
test_scores = []

print(f"\n🔬 Cross-validation fold analysis:")
print("="*60)

for fold, (train_idx, test_idx) in enumerate(cv.split(X_filtered, y_filtered, groups=groups_mapped)):
    X_train, X_test = X_filtered[train_idx], X_filtered[test_idx]
    y_train, y_test = y_filtered[train_idx], y_filtered[test_idx]
    
    # Train simple model
    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)
    
    # Evaluate
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)
    
    train_r2 = r2_score(y_train, train_pred)
    test_r2 = r2_score(y_test, test_pred)
    
    train_scores.append(train_r2)
    test_scores.append(test_r2)
    
    test_group = large_groups[fold]
    print(f"Fold {fold+1}:")
    print(f"  Test group: {test_group}")
    print(f"  Train size: {len(train_idx)}, Test size: {len(test_idx)}")
    print(f"  Train R²: {train_r2:.3f}, Test R²: {test_r2:.3f}")
    print(f"  Train broadband: {y_train.mean():.3f} ± {y_train.std():.3f}")
    print(f"  Test broadband: {y_test.mean():.3f} ± {y_test.std():.3f}")
    print(f"  Model coef: {model.coef_[0]:.3f}, intercept: {model.intercept_:.3f}")
    print()

print(f"📊 Spatial CV Results:")
print(f"   Train R²: {np.mean(train_scores):.3f} ± {np.std(train_scores):.3f}")
print(f"   Test R²: {np.mean(test_scores):.3f} ± {np.std(test_scores):.3f}")
print(f"   Overfitting gap: {np.mean(train_scores) - np.mean(test_scores):.3f}")

# Compare with simple train/test split
X_train_simple, X_test_simple, y_train_simple, y_test_simple = train_test_split(
    X_filtered, y_filtered, test_size=0.2, random_state=42
)

model_simple = Ridge(alpha=1.0)
model_simple.fit(X_train_simple, y_train_simple)
simple_r2 = r2_score(y_test_simple, model_simple.predict(X_test_simple))

print(f"\n🔄 Comparison with random split:")
print(f"   Random split R²: {simple_r2:.3f}")
print(f"   Spatial CV R²: {np.mean(test_scores):.3f}")
print(f"   Difference: {simple_r2 - np.mean(test_scores):.3f}")

# Naive baseline (predict mean)
naive_r2 = 1 - np.var(y_filtered) / np.var(y_filtered)
print(f"   Naive baseline R²: 0.000 (by definition)")

# Analyze group characteristics
print(f"\n📈 Group-wise analysis:")
print("="*50)
for group in large_groups:
    group_data = df[spatial_groups == group]
    group_y = group_data['broadband_usage'].values
    group_ruca = group_data['RUCA1'].values
    
    print(f"Group {group}:")
    print(f"  Size: {len(group_data)}")
    print(f"  Broadband: {group_y.mean():.3f} ± {group_y.std():.3f}")
    print(f"  RUCA modes: {sorted(pd.Series(group_ruca).value_counts().head(3).to_dict().items())}")
    print(f"  Within-group RUCA correlation: {np.corrcoef(group_ruca, group_y)[0,1]:.3f}")

print(f"\n💡 Analysis:")
if simple_r2 > np.mean(test_scores):
    print(f"   ✓ Spatial autocorrelation detected!")
    print(f"   ✓ Random splits overestimate performance by {simple_r2 - np.mean(test_scores):.3f}")
    print(f"   ✓ Spatial CV prevents data leakage")
else:
    print(f"   ⚠️ No strong spatial autocorrelation detected")
    
if np.mean(test_scores) < 0:
    print(f"   ⚠️ Negative R² indicates worse-than-naive performance")
    print(f"   ⚠️ Model predictions worse than predicting the mean")
    print(f"   ⚠️ This suggests overfitting or poor feature quality")
