#!/usr/bin/env python3
"""
Quick Individual Image Test
==========================
Test the individual image analysis approach on a small sample
"""

import pandas as pd
import numpy as np
import cv2
import re
from pathlib import Path
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
from collections import defaultdict

def main():
    print("🖼️ QUICK INDIVIDUAL IMAGE TEST")
    print("="*50)
    
    # Load data
    df = pd.read_csv('data/processed/broadband_labels_with_ruca.csv')
    print(f"📊 Loaded {len(df)} ZIP codes")
    
    # Test on first 5 ZIP codes
    test_df = df.head(5)
    
    image_base = Path("archive/images_legacy/redownload/images_redownload")
    filename_pattern = re.compile(r'(\d+)_bldg_(\d+)_(\d+)\.jpg')
    
    image_data = []
    
    print(f"\n📂 Processing {len(test_df)} ZIP codes...")
    
    for idx, (_, row) in enumerate(test_df.iterrows()):
        zip_code = int(row['zip'])
        zip_dir = image_base / str(zip_code)
        
        if not zip_dir.exists():
            print(f"   {zip_code}: Directory not found")
            continue
        
        # Get image files
        image_files = list(zip_dir.glob("*.jpg"))
        print(f"   {zip_code}: {len(image_files)} images found")
        
        for img_path in image_files[:20]:  # Limit to first 20 images per ZIP
            # Parse filename
            match = filename_pattern.match(img_path.name)
            if not match:
                continue
                
            parsed_zip, building_id, angle = int(match.group(1)), int(match.group(2)), int(match.group(3))
            
            if parsed_zip != zip_code:
                continue
            
            # Simple feature extraction
            try:
                img = cv2.imread(str(img_path))
                if img is None:
                    continue
                
                # Basic features
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
                features = {
                    'brightness': float(np.mean(hsv[:,:,2])),
                    'saturation': float(np.mean(hsv[:,:,1])),
                    'texture': float(np.std(gray)),
                    'edges': float(np.sum(cv2.Canny(gray, 50, 150) > 0) / gray.size)
                }
                
                # Create record
                record = {
                    'image_id': f"{zip_code}_{building_id}_{angle}",
                    'zip_code': zip_code,
                    'building_id': building_id,
                    'angle': angle,
                    'zip_4th_digit': int(str(zip_code)[3]) if len(str(zip_code)) >= 4 else 0,
                    'broadband_usage': row['broadband_usage'],
                    'ruca_code': row['RUCA1'],
                    **features
                }
                
                image_data.append(record)
                
            except Exception as e:
                print(f"   Error processing {img_path.name}: {e}")
                continue
    
    if len(image_data) == 0:
        print("❌ No images processed")
        return
    
    image_df = pd.DataFrame(image_data)
    
    print(f"\n✅ Processing complete:")
    print(f"   Images: {len(image_df)}")
    print(f"   Buildings: {image_df['building_id'].nunique()}")
    print(f"   ZIP codes: {image_df['zip_code'].nunique()}")
    print(f"   Angles: {sorted(image_df['angle'].unique())}")
    
    # Building analysis
    building_stats = defaultdict(list)
    for _, row in image_df.iterrows():
        building_key = f"{row['zip_code']}_{row['building_id']}"
        building_stats[building_key].append(row['angle'])
    
    complete_buildings = sum(1 for angles in building_stats.values() if len(set(angles)) == 4)
    
    print(f"   Buildings with 4 angles: {complete_buildings}/{len(building_stats)}")
    
    # Sample model test
    if len(image_df) >= 10:
        print(f"\n🔬 Simple model test:")
        
        feature_cols = ['brightness', 'saturation', 'texture', 'edges']
        X = image_df[feature_cols].values
        y = image_df['broadband_usage'].values
        X_ruca = image_df[['ruca_code']].values
        
        # Simple train/test split
        n_train = int(0.7 * len(X))
        
        X_train, X_test = X[:n_train], X[n_train:]
        X_ruca_train, X_ruca_test = X_ruca[:n_train], X_ruca[n_train:]
        y_train, y_test = y[:n_train], y[n_train:]
        
        # RUCA baseline
        ruca_model = Ridge(alpha=1.0)
        ruca_model.fit(X_ruca_train, y_train)
        ruca_pred = ruca_model.predict(X_ruca_test)
        ruca_r2 = r2_score(y_test, ruca_pred)
        
        # Visual model
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        visual_model = Ridge(alpha=10.0)
        visual_model.fit(X_train_scaled, y_train)
        visual_pred = visual_model.predict(X_test_scaled)
        visual_r2 = r2_score(y_test, visual_pred)
        
        print(f"   Train: {n_train}, Test: {len(X_test)}")
        print(f"   RUCA R²: {ruca_r2:.3f}")
        print(f"   Visual R²: {visual_r2:.3f}")
        print(f"   Improvement: {visual_r2 - ruca_r2:+.3f}")
    
    print(f"\n📋 Sample data preview:")
    print(image_df[['image_id', 'zip_code', 'building_id', 'angle', 'broadband_usage']].head(10))

if __name__ == "__main__":
    main()
