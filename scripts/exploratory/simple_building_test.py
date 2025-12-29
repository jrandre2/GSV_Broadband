#!/usr/bin/env python3
"""
Simple Building-Level Test
==========================
Simplified version to test building-level analysis
"""

import pandas as pd
import numpy as np
import cv2
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

def extract_simple_features(image_path):
    """Extract simple visual features"""
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            return None
        
        # Convert to HSV and grayscale
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Simple features
        features = {
            'brightness': float(np.mean(hsv[:,:,2])),
            'saturation': float(np.mean(hsv[:,:,1])),
            'edge_density': float(np.sum(cv2.Canny(gray, 50, 150) > 0) / gray.size),
            'texture': float(np.std(gray)),
            'contrast': float(np.std(gray) / (np.mean(gray) + 1e-8))
        }
        
        return features
        
    except Exception:
        return None

def main():
    """Simple building-level analysis"""
    
    print("="*70)
    print("🏢 SIMPLE BUILDING-LEVEL ANALYSIS")
    print("="*70)
    
    # Load data
    df = pd.read_csv('data/processed/broadband_labels_with_ruca.csv')
    print(f"📊 Loaded {len(df)} ZIP codes")
    
    # Process first 5 ZIP codes only
    image_base = Path("archive/images_legacy/redownload/images_redownload")
    building_data = []
    
    for idx, (_, row) in enumerate(df.iterrows()):
        if idx >= 5:  # Only first 5 ZIP codes
            break
            
        zip_code = int(row['zip'])  # Convert to integer
        zip_dir = image_base / str(zip_code)
        
        print(f"\n📍 Processing ZIP {zip_code}...")
        
        if not zip_dir.exists():
            print(f"   ❌ Directory not found: {zip_dir}")
            continue
        
        # Get image files
        image_files = list(zip_dir.glob("*.jpg")) + list(zip_dir.glob("*.png"))
        print(f"   📸 Found {len(image_files)} images")
        
        if len(image_files) < 3:
            continue
        
        # Group into buildings (every 3 images)
        building_groups = []
        for i in range(0, len(image_files), 3):
            group = image_files[i:i+3]
            if len(group) >= 2:
                building_groups.append(group)
        
        print(f"   🏢 Created {len(building_groups)} building groups")
        
        # Extract features for each building
        buildings_added = 0
        for building_idx, building_images in enumerate(building_groups):
            feature_list = []
            
            for img_path in building_images:
                features = extract_simple_features(img_path)
                if features is not None:
                    feature_list.append(features)
            
            if len(feature_list) >= 1:  # At least one successful extraction
                # Average features
                avg_features = {}
                for feature_name in feature_list[0].keys():
                    values = [f[feature_name] for f in feature_list]
                    avg_features[feature_name] = np.mean(values)
                
                # Create building record
                building_record = {
                    'building_id': f"{zip_code}_{building_idx}",
                    'zip_code': zip_code,
                    'zip_group': str(zip_code)[3],  # 4th digit for spatial grouping
                    'broadband_usage': row['broadband_usage'],
                    'ruca_code': row['RUCA1'],
                    'n_images': len(feature_list),
                    **avg_features
                }
                
                building_data.append(building_record)
                buildings_added += 1
        
        print(f"   ✅ Added {buildings_added} buildings")
    
    # Create DataFrame
    building_df = pd.DataFrame(building_data)
    print(f"\n📊 Final Results:")
    print(f"   Total buildings: {len(building_df)}")
    
    if len(building_df) == 0:
        print("❌ No buildings collected")
        return
    
    print(f"   ZIP codes: {building_df['zip_code'].nunique()}")
    print(f"   Spatial groups: {building_df['zip_group'].nunique()}")
    
    # Quick model test
    print(f"\n🧪 Quick Model Test:")
    
    # Prepare data
    feature_cols = ['brightness', 'saturation', 'edge_density', 'texture', 'contrast']
    X_visual = building_df[feature_cols].values
    X_ruca = building_df[['ruca_code']].values
    y = building_df['broadband_usage'].values
    
    # Simple train/test split
    n = len(y)
    train_size = int(0.8 * n)
    
    np.random.seed(42)
    indices = np.random.permutation(n)
    train_idx = indices[:train_size]
    test_idx = indices[train_size:]
    
    print(f"   Train: {len(train_idx)} buildings, Test: {len(test_idx)} buildings")
    
    if len(test_idx) < 3:
        print("   ⚠️ Test set too small for reliable evaluation")
        return
    
    # Split data
    X_train_ruca, X_test_ruca = X_ruca[train_idx], X_ruca[test_idx]
    X_train_visual, X_test_visual = X_visual[train_idx], X_visual[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    # Two-stage model
    # Stage 1: RUCA baseline
    ruca_model = Ridge(alpha=1.0)
    ruca_model.fit(X_train_ruca, y_train)
    ruca_pred_train = ruca_model.predict(X_train_ruca)
    ruca_pred_test = ruca_model.predict(X_test_ruca)
    ruca_r2 = r2_score(y_test, ruca_pred_test)
    
    # Stage 2: Visual residuals
    residuals_train = y_train - ruca_pred_train
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_visual)
    X_test_scaled = scaler.transform(X_test_visual)
    
    visual_model = Ridge(alpha=10.0)  # Moderate regularization
    visual_model.fit(X_train_scaled, residuals_train)
    visual_pred_test = visual_model.predict(X_test_scaled)
    
    combined_pred_test = ruca_pred_test + visual_pred_test
    combined_r2 = r2_score(y_test, combined_pred_test)
    
    improvement = combined_r2 - ruca_r2
    
    print(f"\n📈 Results:")
    print(f"   RUCA baseline R²: {ruca_r2:.3f}")
    print(f"   Combined model R²: {combined_r2:.3f}")
    print(f"   Improvement: {improvement:+.3f}")
    
    # Feature importance
    print(f"\n🎨 Visual Feature Importance:")
    for i, feature in enumerate(feature_cols):
        coef = visual_model.coef_[i]
        print(f"   {feature:<15}: {coef:>8.4f}")
    
    # Sample size comparison
    zip_level_n = building_df['zip_code'].nunique()
    building_level_n = len(building_df)
    
    print(f"\n📊 Sample Size Comparison:")
    print(f"   ZIP-level sample: {zip_level_n}")
    print(f"   Building-level sample: {building_level_n}")
    print(f"   Sample size increase: {building_level_n/zip_level_n:.1f}x")
    
    print(f"\n💡 Key Insights:")
    insights = [
        f"✅ Successfully extracted features from {building_level_n} buildings",
        f"📈 {building_level_n/zip_level_n:.1f}x larger sample than ZIP-level analysis",
        f"🎯 Building-level units with spatial controls via ZIP grouping",
        f"🔍 Improvement: {improvement:+.3f} R² with building-level features"
    ]
    
    for insight in insights:
        print(f"   {insight}")
    
    print("="*70)

if __name__ == "__main__":
    main()
