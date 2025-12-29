#!/usr/bin/env python3
"""Fix ZCTA column names if they differ between versions"""

import geopandas as gpd
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ZCTA_PATH = ROOT / ".cache/geo/zcta22/tl_2022_us_zcta520.shp"

def fix_columns():
    """Rename columns to match expected names if needed"""
    
    if not ZCTA_PATH.exists():
        print("ERROR: ZCTA file not found. Run setup_zcta_data.py first.")
        sys.exit(1)
    
    # Load the shapefile
    print("Loading ZCTA shapefile...")
    zcta = gpd.read_file(ZCTA_PATH)
    
    # Check current columns
    print(f"Current columns: {list(zcta.columns)}")
    
    # Define expected mappings
    column_mappings = {
        # Expected name: [possible alternatives]
        'ZCTA5CE20': ['ZCTA5CE10', 'ZCTA5CE', 'ZCTA5CE00'],
        'STATEFP20': ['STATEFP10', 'STATEFP', 'STATEFP00']
    }
    
    # Check and rename columns
    renamed = False
    for expected, alternatives in column_mappings.items():
        if expected not in zcta.columns:
            for alt in alternatives:
                if alt in zcta.columns:
                    print(f"  Renaming '{alt}' → '{expected}'")
                    zcta = zcta.rename(columns={alt: expected})
                    renamed = True
                    break
    
    if renamed:
        # Save the modified shapefile
        print("\nSaving updated shapefile...")
        zcta.to_file(ZCTA_PATH)
        print("✓ Column names updated successfully")
    else:
        print("✓ All columns already have expected names")
    
    # Verify final columns
    final_zcta = gpd.read_file(ZCTA_PATH)
    print(f"\nFinal columns: {list(final_zcta.columns)}")
    
    # Check if required columns exist
    required = ['ZCTA5CE20', 'STATEFP20', 'geometry']
    missing = [col for col in required if col not in final_zcta.columns]
    
    if missing:
        print(f"\n⚠️  WARNING: Still missing required columns: {missing}")
        print("You may need to manually update the column references in the scripts.")
        return False
    else:
        print("\n✓ All required columns present!")
        return True

if __name__ == "__main__":
    fix_columns()
