import requests
import geopandas as gpd
import pandas as pd
from pathlib import Path
import json
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / ".cache" / "buildings"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def download_nebraska_buildings():
    """Download Microsoft Building Footprints for Nebraska"""
    
    # Direct link to Nebraska buildings from Microsoft's USBuildingFootprints repo
    url = "https://usbuildingdata.blob.core.windows.net/usbuildings-v2/Nebraska.geojson.gz"
    
    output_file = CACHE_DIR / "nebraska_buildings.geojson.gz"
    
    if not output_file.exists():
        print("Downloading Nebraska building footprints...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded to {output_file}")
    
    # Convert to GeoParquet for faster processing
    parquet_file = CACHE_DIR / "nebraska_buildings.parquet"
    if not parquet_file.exists():
        print("Converting to GeoParquet...")
        gdf = gpd.read_file(output_file)
        
        # Add building area (square meters)
        gdf['area_sqm'] = gdf.geometry.to_crs('EPSG:3857').area
        
        # Save as parquet
        gdf.to_parquet(parquet_file)
        print(f"Saved {len(gdf)} buildings to {parquet_file}")
    
    return parquet_file

if __name__ == "__main__":
    download_nebraska_buildings()
