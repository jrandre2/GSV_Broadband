import geopandas as gpd, pandas as pd, numpy as np
from shapely.ops import linemerge
from shapely.geometry import LineString, Point
from pathlib import Path
import random

random.seed(42)
np.random.seed(42)

ROOT = Path(__file__).resolve().parents[1]
roads_shp = ROOT / ".cache" / "geo" / "roads24" / "tl_2024_31_roads.shp"
zcta_shp  = ROOT / ".cache" / "geo" / "zcta22" / "tl_2022_us_zcta520.shp"
zips_csv  = ROOT / "data" / "raw" / "zip_east_264.csv"
out_path  = ROOT / "data" / "interim" / "manifest.parquet"

# Ensure output directory exists
out_path.parent.mkdir(parents=True, exist_ok=True)

# 1. Load data
print("Loading roads data...")
roads = gpd.read_file(roads_shp, columns=["LINEARID","MTFCC","geometry"])
roads = roads.to_crs(epsg=3857)   # metres
roads = roads[roads.MTFCC.isin(["S1200","S1400"])]  # residential & rural local

print("Loading ZCTA data...")
zcta = gpd.read_file(zcta_shp, columns=["ZCTA5CE20","geometry"])
east_zcta = zcta[zcta["ZCTA5CE20"].isin(pd.read_csv(zips_csv)["zip"].astype(str))]
east_zcta = east_zcta.to_crs(epsg=3857)

# 2. Spatial join roads → ZIP polygon
print("Performing spatial join...")
roads_zip = gpd.sjoin(roads, east_zcta, predicate="intersects", how="inner")
roads_zip = roads_zip.rename(columns={"ZCTA5CE20":"zip"}).drop(columns="index_right")

def sample_points(line: LineString, n: int):
    """Return n roughly equidistant points along a linestring."""
    length = line.length
    if length == 0:  # degenerate segment
        return []
    distances = np.linspace(0, length, n+2)[1:-1]   # drop endpoints
    return [line.interpolate(d) for d in distances]

rows = []
print("Generating sample points...")
for zip_code, group in roads_zip.groupby("zip"):
    # Merge lines → one multiline per ZIP → then dissolve
    merged = linemerge(group.geometry.values)
    if merged.geom_type == "MultiLineString":
        merged = LineString([pt for line in merged.geoms for pt in line.coords])

    pts = sample_points(merged, n=50)
    for i, geom in enumerate(pts):
        # Jitter ±5 m perpendicular
        geom_jit = Point(geom.x + np.random.uniform(-5,5),
                         geom.y + np.random.uniform(-5,5))
        geom_ll = gpd.GeoSeries([geom_jit], crs=3857).to_crs(epsg=4326).geometry.iloc[0]
        lat, lon = geom_ll.y, geom_ll.x
        for head in [0,90,180,270]:
            rows.append({
                "zip": zip_code,
                "sample_id": f"{zip_code}_{i:03d}",
                "lat": lat,
                "lon": lon,
                "heading": head,
                "download_status": "PENDING"
            })

manifest = pd.DataFrame(rows)
manifest.to_parquet(out_path, index=False)
print(f"✓ Manifest saved: {out_path}")
print(f"  Total rows: {len(manifest)}")
print(f"  ZIP codes: {manifest.zip.nunique()}")
print(f"  Sample points per ZIP: {len(manifest[manifest.zip == manifest.zip.iloc[0]]) // 4}")
