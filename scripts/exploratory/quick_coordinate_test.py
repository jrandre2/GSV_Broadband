#!/usr/bin/env python3
"""
Quick Test of Exact Coordinate Analysis
======================================
"""

import pandas as pd
import numpy as np
import cv2
from pathlib import Path
from sklearn.cluster import DBSCAN

def parse_filename(filename):
    """Parse image filename to extract ZIP, building, and angle"""
    try:
        # Format: {ZIP}_bldg_{BUILDING_ID}_{ANGLE}.jpg
        parts = filename.replace('.jpg', '').split('_')
        zip_code = int(parts[0])
        building_id_num = parts[2]  # e.g., "00852"
        building_id = f"bldg_{building_id_num}"  # Convert to manifest format
        angle = int(parts[3])
        return zip_code, building_id, angle
    except:
        return None, None, None

def extract_simple_features(image_path):
    """Extract simple visual features"""
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            return None
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        return {
            'brightness': float(np.mean(hsv[:,:,2])),
            'saturation': float(np.mean(hsv[:,:,1])),
            'texture': float(np.std(gray))
        }
    except:
        return None

def main():
    print("🔍 QUICK TEST: Exact Coordinate Analysis")
    print("="*50)
    
    # Load datasets
    print("Loading data...")
    df = pd.read_csv('data/processed/broadband_labels_with_ruca.csv')
    manifest = pd.read_csv('data/raw/nebraska_streetview_manifest.csv')
    
    # Get building coordinates
    building_coords = manifest.groupby(['zip', 'building_id']).agg({
        'lat': 'first',
        'lon': 'first'
    }).reset_index()
    
    print(f"Data loaded: {len(df)} ZIP codes, {len(building_coords):,} buildings")
    
    # Create spatial clusters (quick test with fewer buildings)
    print("Creating spatial clusters...")
    
    # Use a subset for quick test
    test_coords = building_coords.head(1000).copy()
    
    lat_mean = test_coords['lat'].mean()
    cos_lat = np.cos(np.radians(lat_mean))
    
    x_km = test_coords['lon'] * 111.0 * cos_lat
    y_km = test_coords['lat'] * 111.0
    coords_km = np.column_stack([x_km, y_km])
    
    clustering = DBSCAN(eps=5.0, min_samples=5)
    cluster_labels = clustering.fit_predict(coords_km)
    
    test_coords['spatial_cluster'] = cluster_labels
    
    print(f"Clusters created: {len(np.unique(cluster_labels))} clusters")
    
    # Test on first few ZIP codes
    image_base = Path("archive/images_legacy/redownload/images_redownload")
    
    building_data = []
    test_zips = [68001, 68002, 68003]  # Test first 3 ZIP codes
    
    for zip_code in test_zips:
        print(f"Processing ZIP {zip_code}...")
        
        # Get broadband data for this ZIP
        zip_broadband = df[df['zip'] == zip_code]
        if len(zip_broadband) == 0:
            continue
        
        broadband_usage = zip_broadband.iloc[0]['broadband_usage']
        ruca_code = zip_broadband.iloc[0]['RUCA1']
        
        zip_dir = image_base / str(zip_code)
        if not zip_dir.exists():
            continue
        
        # Group images by building
        building_groups = {}
        image_files = list(zip_dir.glob("*.jpg"))
        
        for img_path in image_files:
            parsed_zip, building_id, angle = parse_filename(img_path.name)
            if parsed_zip == zip_code and building_id:
                if building_id not in building_groups:
                    building_groups[building_id] = []
                building_groups[building_id].append(img_path)
        
        print(f"  Found {len(building_groups)} buildings with {len(image_files)} images")
        
        # Process buildings
        for building_id, building_images in building_groups.items():
            if len(building_images) >= 2:
                
                # Get coordinates
                coord_match = test_coords[
                    (test_coords['zip'] == zip_code) & 
                    (test_coords['building_id'] == building_id)
                ]
                
                if len(coord_match) == 0:
                    continue
                
                # Extract features
                feature_list = []
                for img_path in building_images:
                    features = extract_simple_features(img_path)
                    if features:
                        feature_list.append(features)
                
                if len(feature_list) >= 1:
                    # Average features
                    avg_features = {}
                    for feature_name in feature_list[0].keys():
                        values = [f[feature_name] for f in feature_list]
                        avg_features[feature_name] = np.mean(values)
                    
                    # Add building record
                    coord_data = coord_match.iloc[0]
                    building_record = {
                        'zip_code': zip_code,
                        'building_id': building_id,
                        'lat': coord_data['lat'],
                        'lon': coord_data['lon'],
                        'spatial_cluster': coord_data['spatial_cluster'],
                        'broadband_usage': broadband_usage,
                        'ruca_code': ruca_code,
                        'n_images': len(feature_list),
                        **avg_features
                    }
                    
                    building_data.append(building_record)
    
    building_df = pd.DataFrame(building_data)
    
    print(f"\n✅ Results:")
    print(f"   Buildings collected: {len(building_df)}")
    if len(building_df) > 0:
        print(f"   ZIP codes: {building_df['zip_code'].nunique()}")
        print(f"   Spatial clusters: {building_df['spatial_cluster'].nunique()}")
        print(f"   Sample records:")
        print(building_df[['zip_code', 'building_id', 'lat', 'lon', 'spatial_cluster', 'broadband_usage']].head())
    else:
        print(f"   ❌ No buildings collected!")

if __name__ == "__main__":
    main()
