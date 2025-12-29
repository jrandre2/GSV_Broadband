#!/usr/bin/env python3
"""
Debug spatial cross-validation methodology
Compare train/test performance and understand why R² scores are so low
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
import geopandas as gpd

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using haversine formula"""
    R = 6371  # Earth's radius in kilometers
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

# Load data
df = pd.read_csv('data/processed/broadband_labels_with_ruca.csv')
print(f"📍 Loaded {len(df)} ZIP codes")

# Create spatial groups using 4th digit of ZIP code
spatial_groups = df['zip'].astype(str).str[3].astype(int)
print(f"🗺️  Created {len(spatial_groups.unique())} spatial groups: {sorted(spatial_groups.unique())}")
print(f"   Group sizes: {[sum(spatial_groups == g) for g in sorted(spatial_groups.unique())]}")

# Check group geographic distribution
zip_shp = gpd.read_file('data/raw/nebraska_zips.shp')
df_geo = df.merge(zip_shp, left_on='zip', right_on='ZCTA5CE10', how='inner')
print(f"🌍 Geographic merge: {len(df_geo)} ZIPs matched")

# Calculate centroids and distances
gdf = gpd.GeoDataFrame(df_geo)
gdf['centroid'] = gdf.geometry.centroid
gdf['lat'] = gdf.centroid.y
gdf['lon'] = gdf.centroid.x

print("\n📊 Spatial Group Analysis:")
print("="*50)
for group in sorted(spatial_groups.unique()):
    group_data = gdf[spatial_groups == group]
    if len(group_data) > 1:
        coords = [(row.lat, row.lon) for _, row in group_data.iterrows()]
        distances = [haversine_distance(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
                    for i in range(len(coords)) 
                    for j in range(i+1, len(coords))]
        print(f"Group {group}: {len(group_data)} ZIPs")
        print(f"  Min distance: {min(distances):.1f} km")
        print(f"  Max distance: {max(distances):.1f} km") 
        print(f"  Mean distance: {np.mean(distances):.1f} km")
    else:
        print(f"Group {group}: {len(group_data)} ZIPs (single ZIP)")

# Simple baseline analysis
y = df['broadband_usage'].values
X_simple = df[['RUCA1']].values

print(f"\n🎯 Simple baseline analysis:")
print(f"   RUCA1 correlation with broadband: {np.corrcoef(X_simple.flatten(), y)[0,1]:.3f}")
print(f"   RUCA1 range: {X_simple.min()} to {X_simple.max()}")
print(f"   Broadband range: {y.min():.3f} to {y.max():.3f}")

# Cross-validation analysis
cv = GroupKFold(n_splits=5)
train_scores = []
test_scores = []

print(f"\n🔬 Cross-validation fold analysis:")
print("="*60)

for fold, (train_idx, test_idx) in enumerate(cv.split(X_simple, y, groups=spatial_groups)):
    X_train, X_test = X_simple[train_idx], X_simple[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
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
    
    test_groups = spatial_groups.iloc[test_idx].unique()
    print(f"Fold {fold+1}:")
    print(f"  Test groups: {sorted(test_groups)}")
    print(f"  Train size: {len(train_idx)}, Test size: {len(test_idx)}")
    print(f"  Train R²: {train_r2:.3f}, Test R²: {test_r2:.3f}")
    print(f"  Train broadband range: {y_train.min():.3f}-{y_train.max():.3f}")
    print(f"  Test broadband range: {y_test.min():.3f}-{y_test.max():.3f}")
    print()

print(f"📊 Overall CV Results:")
print(f"   Train R²: {np.mean(train_scores):.3f} ± {np.std(train_scores):.3f}")
print(f"   Test R²: {np.mean(test_scores):.3f} ± {np.std(test_scores):.3f}")
print(f"   Overfitting gap: {np.mean(train_scores) - np.mean(test_scores):.3f}")

# Compare with simple train/test split
from sklearn.model_selection import train_test_split
X_train_simple, X_test_simple, y_train_simple, y_test_simple = train_test_split(
    X_simple, y, test_size=0.2, random_state=42
)

model_simple = Ridge(alpha=1.0)
model_simple.fit(X_train_simple, y_train_simple)
simple_r2 = r2_score(y_test_simple, model_simple.predict(X_test_simple))

print(f"\n🔄 Comparison with random split:")
print(f"   Random split R²: {simple_r2:.3f}")
print(f"   Spatial CV R²: {np.mean(test_scores):.3f}")
print(f"   Difference: {simple_r2 - np.mean(test_scores):.3f}")

# Analyze why spatial CV is worse
print(f"\n💡 Analysis:")
if simple_r2 > np.mean(test_scores):
    print(f"   ✓ Spatial autocorrelation detected!")
    print(f"   ✓ Random splits overestimate performance by {simple_r2 - np.mean(test_scores):.3f}")
    print(f"   ✓ Spatial CV prevents data leakage")
else:
    print(f"   ⚠️ No spatial autocorrelation detected")
    print(f"   ⚠️ Spatial CV and random splits similar")
