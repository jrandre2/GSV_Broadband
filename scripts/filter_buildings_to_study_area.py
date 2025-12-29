import geopandas as gpd
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def filter_buildings():
    # Load buildings
    print("Loading Nebraska buildings...")
    buildings = gpd.read_parquet(ROOT / ".cache/buildings/nebraska_buildings.parquet")

    # Load study area ZIPs
    print("Loading study area ZIP codes...")
    zips = pd.read_csv(ROOT / "data/raw/zip_east_264.csv")
    
    # Load ZCTA shapefile
    zcta_path = ROOT / ".cache/geo/zcta22/tl_2022_us_zcta520.shp"
    print(f"Loading ZCTA data from {zcta_path}")
    zcta = gpd.read_file(zcta_path, columns=["ZCTA5CE20", "geometry"])
    
    # Filter for study area ZCTAs
    study_zcta = zcta[zcta.ZCTA5CE20.isin(zips.zip.astype(str))].to_crs(buildings.crs)
    print(f"Found {len(study_zcta)} ZCTAs in study area")

    # Spatial join to get buildings in study area
    print("Performing spatial join to find buildings in study area...")
    buildings_in_study = gpd.sjoin(buildings, study_zcta, predicate='within')
    buildings_in_study['zip'] = buildings_in_study['ZCTA5CE20']

    # Filter by building size (e.g., > 50 sqm to avoid sheds/garages)
    MIN_BUILDING_SIZE = 50  # square meters
    MAX_BUILDING_SIZE = 10000  # exclude huge warehouses/factories

    filtered = buildings_in_study[
        (buildings_in_study.area_sqm >= MIN_BUILDING_SIZE) &
        (buildings_in_study.area_sqm <= MAX_BUILDING_SIZE)
    ].copy()

    # Add building categories based on size
    filtered['building_category'] = pd.cut(
        filtered['area_sqm'],
        bins=[0, 150, 300, 500, 1000, 10000],
        labels=[
            'small_residential',
            'medium_residential',
            'large_residential',
            'small_commercial',
            'large_commercial'
        ]
    )

    # Save
    output = ROOT / "data/interim/study_area_buildings.parquet"
    output.parent.mkdir(parents=True, exist_ok=True)
    filtered.to_parquet(output)

    print(f"\n✓ Filtered to {len(filtered)} buildings in {filtered.zip.nunique()} ZIPs")
    print(f"\nBuilding categories:")
    print(filtered.building_category.value_counts())
    print(f"\nSaved to: {output}")

    return output

if __name__ == "__main__":
    filter_buildings()
