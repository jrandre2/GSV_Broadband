import geopandas as gpd
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def match_buildings_to_bsl():
    """
    After sampling, check which buildings are broadband serviceable locations.
    This assumes you've downloaded FCC BDC data separately.
    """
    # Load manifest with sampled buildings
    manifest = pd.read_parquet(ROOT / "data/interim/manifest_buildings.parquet")

    # Create unique building locations
    unique_buildings = manifest[['building_id', 'lat', 'lon', 'zip']].drop_duplicates()
    geometry = gpd.points_from_xy(unique_buildings.lon, unique_buildings.lat)
    buildings_gdf = gpd.GeoDataFrame(unique_buildings, geometry=geometry, crs='EPSG:4326')

    # Path to BSL data (assumed to be downloaded separately)
    bsl_file = ROOT / ".cache/bdc_data/nebraska_bsl.parquet"

    if bsl_file.exists():
        print("Loading BSL data...")
        bsl = gpd.read_parquet(bsl_file)

        # Join each building to the nearest BSL within 20 meters
        joined = gpd.sjoin_nearest(
            buildings_gdf.to_crs('EPSG:3857'),
            bsl.to_crs('EPSG:3857'),
            max_distance=20,
            how='left'
        )

        # Determine match status
        bsl_matches = joined[['building_id', 'location_id', 'service_tier', 'technology']].copy()
        bsl_matches['bsl_status'] = joined['location_id'].notna().map({True: 'MATCHED', False: 'NO_MATCH'})

        # Merge match info back into manifest
        manifest_updated = manifest.merge(
            bsl_matches[['building_id', 'bsl_status', 'location_id', 'service_tier', 'technology']],
            on='building_id',
            how='left',
            suffixes=('', '_new')
        )

        # Fill missing statuses and rename columns
        manifest_updated['bsl_status'] = manifest_updated['bsl_status'].fillna('NO_BSL_DATA')
        manifest_updated['bsl_location_id'] = manifest_updated['location_id']
        cols_to_keep = [col for col in manifest_updated.columns if not col.endswith('_new')]
        manifest_updated = manifest_updated[cols_to_keep]

        print("\nBSL Matching Results:")
        print(manifest_updated.groupby('bsl_status')['building_id'].nunique())
    else:
        print("No BSL data found. Run download_bsl_data.py first to enable matching.")
        manifest_updated = manifest.copy()
        manifest_updated['bsl_status'] = 'NO_BSL_DATA'

    # Save updated manifest
    output = ROOT / "data/interim/manifest_buildings_with_bsl.parquet"
    manifest_updated.to_parquet(output, index=False)
    return output

if __name__ == "__main__":
    match_buildings_to_bsl()
