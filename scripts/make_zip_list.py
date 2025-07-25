import geopandas as gpd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tiger = ROOT / ".cache" / "geo" / "zcta24" / "tl_2024_us_zcta520.shp"
out   = ROOT / "data" / "raw" / "zip_east_264.csv"

zcta = gpd.read_file(tiger, columns=["ZCTA5CE20","STATEFP","geometry"])
ne   = zcta[zcta["STATEFP"] == "31"].to_crs("epsg:4326")
east = ne[ne.geometry.centroid.x > -100].copy()    # east of 100°W
east["zip"] = east["ZCTA5CE20"]
east[["zip"]].to_csv(out, index=False)
print("Wrote", out, "with", len(east), "rows")
