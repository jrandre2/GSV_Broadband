#!/usr/bin/env python3
"""Setup script to copy ZCTA shapefile data to cache directory"""

import shutil
from pathlib import Path
import geopandas as gpd
import sys

ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_SOURCE = Path("/Users/jesseandrews/Downloads/tl_2022_us_zcta520")
LOCAL_SHP = ROOT / "tl_2022_us_zcta520.shp"
LOCAL_SOURCE_DIR = ROOT / "tl_2022_us_zcta520"
if LOCAL_SHP.exists():
    SOURCE_ZCTA = LOCAL_SHP.parent
elif LOCAL_SOURCE_DIR.exists():
    SOURCE_ZCTA = LOCAL_SOURCE_DIR
else:
    SOURCE_ZCTA = DOWNLOAD_SOURCE
TARGET_DIR = ROOT / ".cache" / "geo" / "zcta22"

def setup_zcta_data():
    """Copy ZCTA shapefile components to cache directory"""
    
    # Check if source exists
    if not SOURCE_ZCTA.exists():
        print(f"ERROR: Source directory not found: {SOURCE_ZCTA}")
        sys.exit(1)
    
    # Create cache directory
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Setting up ZCTA data in {TARGET_DIR}")
    
    # Copy all shapefile components
    copied_files = []
    for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg', '.shp.xml']:
        source_file = SOURCE_ZCTA / f"tl_2022_us_zcta520{ext}"
        if source_file.exists():
            target_file = TARGET_DIR / f"tl_2022_us_zcta520{ext}"
            shutil.copy2(source_file, target_file)
            copied_files.append(source_file.name)
            print(f"  ✓ Copied {source_file.name}")
    
    if not copied_files:
        print(f"ERROR: No shapefile components found in {SOURCE_ZCTA}")
        sys.exit(1)
    
    # Verify the data
    try:
        zcta = gpd.read_file(TARGET_DIR / "tl_2022_us_zcta520.shp")
        print(f"\n✓ Successfully loaded {len(zcta)} ZCTA records")
        print(f"Columns: {list(zcta.columns)}")
        
        # Check for expected column
        if 'ZCTA5CE20' not in zcta.columns:
            print("\nWARNING: Expected column 'ZCTA5CE20' not found!")
            print("You may need to update column references in other scripts.")
            # Check for similar columns
            zcta_cols = [col for col in zcta.columns if col.startswith('ZCTA')]
            if zcta_cols:
                print(f"Found ZCTA columns: {zcta_cols}")
        
        # Create a marker file to indicate successful setup
        marker_file = TARGET_DIR / ".setup_complete"
        marker_file.touch()
        
    except Exception as e:
        print(f"ERROR: Failed to verify shapefile: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_zcta_data()
