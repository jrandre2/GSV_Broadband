import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
import random

random.seed(42)
np.random.seed(42)

ROOT = Path(__file__).resolve().parents[1]

def create_stratified_sample():
    # Load filtered buildings
    buildings = gpd.read_parquet(ROOT / "data/interim/study_area_buildings.parquet")

    # Load MS labels for additional context
    ms_labels = pd.read_csv(ROOT / "data/interim/labels_ms.csv", dtype={'zip': str})

    # Configuration
    SAMPLES_PER_ZIP = 50  # from your config
    HEADINGS = [0, 90, 180, 270]

    rows = []

    for zip_code, zip_buildings in buildings.groupby('zip'):
        # Get MS speed info for this ZIP if available
        ms_info = ms_labels[ms_labels.zip == zip_code]
        has_ms_data = len(ms_info) > 0

        # Stratified sampling by building category
        n_available = len(zip_buildings)
        n_to_sample = min(SAMPLES_PER_ZIP, n_available)

        if n_available <= SAMPLES_PER_ZIP:
            sampled = zip_buildings
        else:
            # Stratify by building category
            sampled = zip_buildings.groupby('building_category', group_keys=False).apply(
                lambda x: x.sample(
                    n=max(1, int(n_to_sample * len(x) / n_available)),
                    replace=False
                )
            ).sample(n=n_to_sample)

        # Create manifest entries
        for idx, (_, building) in enumerate(sampled.iterrows()):
            centroid = building.geometry.centroid
            lon, lat = centroid.x, centroid.y
            for heading in HEADINGS:
                row_data = {
                    "zip": zip_code,
                    "sample_id": f"{zip_code}_{idx:04d}",
                    "building_id": f"{zip_code}_bldg_{idx:04d}",
                    "lat": lat,
                    "lon": lon,
                    "heading": heading,
                    "building_area_sqm": building.area_sqm,
                    "building_category": building.building_category,
                    "download_status": "PENDING",
                    "bsl_status": "UNKNOWN",
                    "bsl_location_id": None,
                }
                if has_ms_data:
                    row_data['ms_pct_25_3'] = ms_info.iloc[0]['pct_25_3']
                    row_data['ms_device_count'] = ms_info.iloc[0]['total_device_count']
                rows.append(row_data)

    manifest = pd.DataFrame(rows)
    output = ROOT / "data/interim/manifest_buildings.parquet"
    manifest.to_parquet(output, index=False)

    print(f"✓ Created manifest with {len(manifest)} image requests")
    print(f"  Covering {manifest.building_id.nunique()} buildings in {manifest.zip.nunique()} ZIPs")
    print("\nBuilding category distribution:")
    print(manifest.groupby('building_category')['building_id'].nunique())

    return output

if __name__ == "__main__":
    create_stratified_sample()
