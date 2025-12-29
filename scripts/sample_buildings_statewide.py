#!/usr/bin/env python3
"""
Sample buildings from ALL Nebraska ZIP codes for Street View collection

This script:
1. Loads Nebraska building footprints
2. Filters for buildings in ALL Nebraska ZIP codes (not just eastern)
3. Filters by building size (50-10,000 sq meters)
4. Samples up to 75 buildings per ZIP (50 primary + 25 backup)
5. Creates Street View points with 4 headings per building
6. Outputs JSON and CSV files for image downloading
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Input paths
BUILDINGS_PATH = Path("/Users/jesseandrews/Downloads/Nebraska.geojson")
ZCTA_PATH = ROOT / "tl_2022_us_zcta520.shp"

# Configuration
MIN_BUILDING_SIZE = 50      # square meters
MAX_BUILDING_SIZE = 10000   # square meters
BUILDINGS_PER_ZIP = 50      # target number of buildings per ZIP
BACKUP_FACTOR = 1.5         # sample 50% extra as backups
HEADINGS = [0, 90, 180, 270]  # camera headings for Street View

# Output
OUTPUT_JSON = "nebraska_streetview_manifest.json"
OUTPUT_CSV = "nebraska_streetview_manifest.csv"

# Check input files exist
if not BUILDINGS_PATH.exists():
    print(f"ERROR: Buildings file not found at {BUILDINGS_PATH}")
    exit(1)
if not ZCTA_PATH.exists():
    print(f"ERROR: ZCTA file not found at {ZCTA_PATH}")
    exit(1)

print("Loading Nebraska buildings...")
buildings = gpd.read_file(BUILDINGS_PATH)
if buildings.crs is None:
    buildings = buildings.set_crs('EPSG:4326')

print("Calculating building areas...")
buildings_proj = buildings.to_crs('EPSG:3857')
buildings['area_sqm'] = buildings_proj.geometry.area

print("Loading ZCTA boundaries...")
zcta = gpd.read_file(ZCTA_PATH)
print(f"ZCTA shapefile has {len(zcta)} records")

# Check column names
print(f"ZCTA columns: {list(zcta.columns)}")

# Since ZCTAs don't have state columns, we'll filter by Nebraska's geographic bounds
# Nebraska approximate bounds: Lat 40-43°N, Lon -104 to -95.3°W
print("Filtering for ALL Nebraska ZCTAs using geographic bounds...")

# Convert to lat/lon if needed
zcta = zcta.to_crs('EPSG:4326')

# Use the internal point coordinates to filter
if 'INTPTLAT20' in zcta.columns and 'INTPTLON20' in zcta.columns:
    # Convert string coordinates to float
    zcta['lat'] = zcta['INTPTLAT20'].astype(float)
    zcta['lon'] = zcta['INTPTLON20'].astype(float)
    
    # Filter for Nebraska bounds - ALL of Nebraska
    ne_zcta = zcta[
        (zcta['lat'] >= 40.0) & (zcta['lat'] <= 43.0) &
        (zcta['lon'] >= -104.05) & (zcta['lon'] <= -95.3)
    ].copy()
else:
    # Use geometry centroids
    zcta['centroid_lat'] = zcta.geometry.centroid.y
    zcta['centroid_lon'] = zcta.geometry.centroid.x
    ne_zcta = zcta[
        (zcta['centroid_lat'] >= 40.0) & (zcta['centroid_lat'] <= 43.0) &
        (zcta['centroid_lon'] >= -104.05) & (zcta['centroid_lon'] <= -95.3)
    ].copy()

print(f"Found {len(ne_zcta)} ZCTAs in Nebraska")

# Add a region indicator for later filtering if needed
if 'lon' in ne_zcta.columns:
    ne_zcta['region'] = ne_zcta['lon'].apply(lambda x: 'eastern' if x > -100 else 'western')
else:
    ne_zcta['region'] = ne_zcta['centroid_lon'].apply(lambda x: 'eastern' if x > -100 else 'western')

# Count by region
region_counts = ne_zcta['region'].value_counts()
print(f"  Eastern Nebraska: {region_counts.get('eastern', 0)} ZCTAs")
print(f"  Western Nebraska: {region_counts.get('western', 0)} ZCTAs")

# Show some sample ZIP codes from both regions
if len(ne_zcta) > 0:
    eastern_samples = ne_zcta[ne_zcta['region'] == 'eastern']['ZCTA5CE20'].head(5).tolist()
    western_samples = ne_zcta[ne_zcta['region'] == 'western']['ZCTA5CE20'].head(5).tolist()
    print(f"Sample eastern ZIP codes: {', '.join(eastern_samples)}")
    print(f"Sample western ZIP codes: {', '.join(western_samples)}")

# Prepare for spatial join - keep all Nebraska ZCTAs
ne_zcta_for_join = ne_zcta[['ZCTA5CE20', 'geometry', 'region']].copy()

print("\nMatching buildings to ZIP codes...")
buildings_with_zip = gpd.sjoin(buildings, ne_zcta_for_join[['ZCTA5CE20', 'geometry', 'region']], 
                               predicate='within', how='inner')
buildings_with_zip['zip'] = buildings_with_zip['ZCTA5CE20']

if len(buildings_with_zip) == 0:
    print("WARNING: No buildings matched to ZIP codes!")
    print(f"  Buildings CRS: {buildings.crs}")
    print(f"  ZCTA CRS: {ne_zcta_for_join.crs}")
    print(f"  Building bounds: {buildings.total_bounds}")
else:
    print(f"Matched {len(buildings_with_zip)} buildings to ZIP codes")
    # Show distribution by region
    region_building_counts = buildings_with_zip.groupby('region').size()
    print(f"  Eastern Nebraska: {region_building_counts.get('eastern', 0)} buildings")
    print(f"  Western Nebraska: {region_building_counts.get('western', 0)} buildings")

print("\nFiltering buildings by size...")
filtered = buildings_with_zip[
    (buildings_with_zip.area_sqm >= MIN_BUILDING_SIZE) &
    (buildings_with_zip.area_sqm <= MAX_BUILDING_SIZE)
]

print(f"Buildings after size filter: {len(filtered)}")
if len(filtered) > 0:
    print(f"  Size range: {filtered.area_sqm.min():.1f} - {filtered.area_sqm.max():.1f} sq meters")
    print(f"  ZIP codes with buildings: {filtered['zip'].nunique()}")
    # Show by region
    zip_by_region = filtered.groupby('region')['zip'].nunique()
    print(f"  Eastern Nebraska ZIPs: {zip_by_region.get('eastern', 0)}")
    print(f"  Western Nebraska ZIPs: {zip_by_region.get('western', 0)}")

print("\nSampling buildings per ZIP code...")
manifest_records = []
building_id = 0

# Check if we have any buildings to process
if len(filtered) == 0:
    print("WARNING: No buildings found after filtering!")
else:
    # Process all ZIP codes
    for zip_code in sorted(filtered['zip'].unique()):
        zip_buildings = filtered[filtered['zip'] == zip_code]
        region = zip_buildings['region'].iloc[0]  # Get region for this ZIP
        
        # Sample with backups
        n_available = len(zip_buildings)
        n_sample = min(int(BUILDINGS_PER_ZIP * BACKUP_FACTOR), n_available)
        
        if n_available > 0:
            sampled = zip_buildings.sample(n=n_sample, random_state=42)
            
            # Create records for each building and heading
            for rank, (idx, building) in enumerate(sampled.iterrows(), 1):
                centroid = building.geometry.centroid
                
                # Create a record for each heading
                for heading in HEADINGS:
                    manifest_records.append({
                        'zip': zip_code,
                        'region': region,  # Add region for easy filtering later
                        'building_id': f"bldg_{building_id:05d}",
                        'sample_id': f"{zip_code}_{building_id:05d}_{heading}",
                        'lat': round(centroid.y, 6),
                        'lon': round(centroid.x, 6),
                        'heading': heading,
                        'building_area_sqm': round(building.area_sqm, 2),
                        'sample_rank': rank,
                        'is_backup': rank > BUILDINGS_PER_ZIP,
                        'download_status': 'PENDING'
                    })
                
                building_id += 1

# Calculate statistics
total_zips = len(filtered['zip'].unique()) if len(filtered) > 0 else 0
df_manifest = pd.DataFrame(manifest_records) if manifest_records else pd.DataFrame()

# Save as JSON
print(f"\nSaving results...")
metadata = {
    'total_records': len(manifest_records),
    'total_buildings': building_id,
    'total_zip_codes': total_zips,
    'buildings_per_zip': BUILDINGS_PER_ZIP,
    'backup_factor': BACKUP_FACTOR,
    'headings': HEADINGS
}

# Add region breakdown to metadata if we have data
if not df_manifest.empty:
    eastern_stats = df_manifest[df_manifest['region'] == 'eastern']
    western_stats = df_manifest[df_manifest['region'] == 'western']
    
    metadata['breakdown'] = {
        'eastern_nebraska': {
            'records': len(eastern_stats),
            'buildings': len(eastern_stats) // len(HEADINGS) if len(eastern_stats) > 0 else 0,
            'zip_codes': eastern_stats['zip'].nunique() if len(eastern_stats) > 0 else 0
        },
        'western_nebraska': {
            'records': len(western_stats),
            'buildings': len(western_stats) // len(HEADINGS) if len(western_stats) > 0 else 0,
            'zip_codes': western_stats['zip'].nunique() if len(western_stats) > 0 else 0
        }
    }

with open(OUTPUT_JSON, 'w') as f:
    json.dump({
        'metadata': metadata,
        'manifest': manifest_records
    }, f, indent=2)

# Also save as CSV for compatibility
if manifest_records:
    df_manifest.to_csv(OUTPUT_CSV, index=False)
else:
    # Create empty dataframe with expected columns
    df = pd.DataFrame(columns=['zip', 'region', 'building_id', 'sample_id', 'lat', 'lon', 
                               'heading', 'building_area_sqm', 'sample_rank', 
                               'is_backup', 'download_status'])
    df.to_csv(OUTPUT_CSV, index=False)

# Summary statistics
print(f"\nGenerated manifest with:")
print(f"  - {len(manifest_records)} total records")
print(f"  - {building_id} unique buildings")
print(f"  - {total_zips} ZIP codes across Nebraska")
print(f"  - {len(HEADINGS)} headings per building")

if not df_manifest.empty:
    print(f"\nBreakdown by region:")
    print(f"  Eastern Nebraska: {metadata['breakdown']['eastern_nebraska']['zip_codes']} ZIPs, "
          f"{metadata['breakdown']['eastern_nebraska']['buildings']} buildings")
    print(f"  Western Nebraska: {metadata['breakdown']['western_nebraska']['zip_codes']} ZIPs, "
          f"{metadata['breakdown']['western_nebraska']['buildings']} buildings")

print(f"\nOutput files:")
print(f"  - JSON: {OUTPUT_JSON}")
print(f"  - CSV: {OUTPUT_CSV}")

# Show sample of the data
if manifest_records:
    print(f"\nSample records:")
    # Show samples from both regions if available
    if not df_manifest.empty:
        eastern_sample = df_manifest[df_manifest['region'] == 'eastern'].head(2)
        western_sample = df_manifest[df_manifest['region'] == 'western'].head(2)
        
        if len(eastern_sample) > 0:
            print("  Eastern Nebraska samples:")
            for _, row in eastern_sample.iterrows():
                print(f"    {row.to_dict()}")
        
        if len(western_sample) > 0:
            print("  Western Nebraska samples:")
            for _, row in western_sample.iterrows():
                print(f"    {row.to_dict()}")

print("\nYou can now filter the data by region for specific analysis:")
print("  Eastern Nebraska: df[df['region'] == 'eastern']")
print("  Western Nebraska: df[df['region'] == 'western']")
