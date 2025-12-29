#!/usr/bin/env python3
"""Check data compatibility and download missing data"""

import geopandas as gpd
from pathlib import Path
import requests
import zipfile
import shutil

ROOT = Path(__file__).resolve().parents[1]

def check_zcta_columns():
    """Check ZCTA column names for compatibility"""
    zcta_path = ROOT / ".cache/geo/zcta22/tl_2022_us_zcta520.shp"
    
    if not zcta_path.exists():
        print("❌ ZCTA shapefile not found. Run setup_zcta_data.py first.")
        return False
    
    print("Checking ZCTA data compatibility...")
    zcta = gpd.read_file(zcta_path)
    
    # Check for expected columns
    expected_cols = {
        'ZCTA5CE20': 'ZIP Code Tabulation Area',
        'STATEFP20': 'State FIPS code'
    }
    
    missing_cols = []
    for col, desc in expected_cols.items():
        if col not in zcta.columns:
            missing_cols.append((col, desc))
            # Look for alternative column names
            alt_cols = [c for c in zcta.columns if c.startswith(col[:7])]
            if alt_cols:
                print(f"  ⚠️  Expected '{col}' ({desc}) not found")
                print(f"     Found alternatives: {alt_cols}")
    
    if missing_cols:
        print("\n⚠️  Column mapping may be needed!")
        print("Current columns:", list(zcta.columns))
        return False
    else:
        print("✓ All expected columns found")
        return True

def download_roads_data():
    """Download Nebraska roads data from Census TIGER"""
    roads_dir = ROOT / ".cache/geo/roads24"
    roads_shp = roads_dir / "tl_2024_31_roads.shp"
    
    if roads_shp.exists():
        print("✓ Roads data already exists")
        return True
    
    print("Downloading Nebraska roads data...")
    roads_dir.mkdir(parents=True, exist_ok=True)
    
    # Try 2024 data first, fall back to 2023 if not available
    urls = [
        "https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_31_roads.zip",
        "https://www2.census.gov/geo/tiger/TIGER2023/ROADS/tl_2023_31_roads.zip"
    ]
    
    for url in urls:
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                zip_path = roads_dir / "roads.zip"
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Extract the zip file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(roads_dir)
                
                # Rename if we got 2023 data
                if "2023" in url:
                    for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                        old_file = roads_dir / f"tl_2023_31_roads{ext}"
                        new_file = roads_dir / f"tl_2024_31_roads{ext}"
                        if old_file.exists():
                            shutil.move(old_file, new_file)
                
                zip_path.unlink()
                print(f"✓ Downloaded roads data from {url}")
                return True
        except Exception as e:
            print(f"  Failed to download from {url}: {e}")
    
    print("❌ Failed to download roads data")
    return False

def check_ms_labels_data():
    """Check if Microsoft broadband labels data exists"""
    labels_path = ROOT / ".cache/labels/Zip/zip.csv"
    
    if labels_path.exists():
        print("✓ Microsoft labels data exists")
        return True
    else:
        print("❌ Microsoft labels data not found at:", labels_path)
        print("  You need to download this data separately from Microsoft/Ookla")
        return False

def main():
    print("=== Nebraska Broadband Project - Data Compatibility Check ===\n")
    
    # Run all checks
    checks = [
        ("ZCTA columns", check_zcta_columns),
        ("Roads data", download_roads_data),
        ("MS labels data", check_ms_labels_data)
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        if not check_func():
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("✓ All checks passed! You're ready to run the pipeline.")
    else:
        print("⚠️  Some issues need attention before running the pipeline.")
        print("  Fix the issues above and run this script again.")

if __name__ == "__main__":
    main()
