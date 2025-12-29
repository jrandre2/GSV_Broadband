#!/usr/bin/env python3
"""
Debug Coordinate Matching
=========================
"""

import pandas as pd
from pathlib import Path

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

def main():
    print("🔍 DEBUGGING COORDINATE MATCHING")
    print("="*50)
    
    # Load manifest
    print("Loading manifest...")
    manifest = pd.read_csv('data/raw/nebraska_streetview_manifest.csv')
    
    # Get building coordinates
    building_coords = manifest.groupby(['zip', 'building_id']).agg({
        'lat': 'first',
        'lon': 'first'
    }).reset_index()
    
    print(f"Manifest: {len(manifest):,} records, {len(building_coords):,} buildings")
    print(f"Sample manifest buildings:")
    print(building_coords.head())
    
    # Check images in one ZIP
    image_base = Path("archive/images_legacy/redownload/images_redownload")
    test_zip = 68001
    zip_dir = image_base / str(test_zip)
    
    if zip_dir.exists():
        image_files = list(zip_dir.glob("*.jpg"))[:10]
        print(f"\nImages in ZIP {test_zip}: {len(image_files)} total")
        
        matched = 0
        for img_path in image_files:
            parsed_zip, building_id, angle = parse_filename(img_path.name)
            
            if parsed_zip == test_zip and building_id:
                # Check if building exists in manifest coordinates
                coord_match = building_coords[
                    (building_coords['zip'] == test_zip) & 
                    (building_coords['building_id'] == building_id)
                ]
                
                if len(coord_match) > 0:
                    matched += 1
                    print(f"✅ {img_path.name} -> {building_id} MATCHED")
                else:
                    print(f"❌ {img_path.name} -> {building_id} NOT FOUND")
            else:
                print(f"⚠️ {img_path.name} -> Parse failed")
        
        print(f"\nMatching rate: {matched}/{len(image_files)} = {100*matched/len(image_files):.1f}%")
        
        # Show manifest buildings for this ZIP
        zip_buildings = building_coords[building_coords['zip'] == test_zip]
        print(f"\nManifest buildings in ZIP {test_zip}: {len(zip_buildings)}")
        print(zip_buildings['building_id'].head(10).tolist())

if __name__ == "__main__":
    main()
