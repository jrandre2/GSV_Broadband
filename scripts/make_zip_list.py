import geopandas as gpd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tiger = ROOT / "tl_2022_us_zcta520.shp"
out   = ROOT / "data" / "raw" / "zip_east_264.csv"

# Ensure output directory exists
out.parent.mkdir(parents=True, exist_ok=True)

# Load ZCTA data
print(f"Loading ZCTA data from {tiger}")

# Load all ZCTA data
zcta = gpd.read_file(tiger)
print(f"Available columns: {list(zcta.columns)}")
print(f"Total ZCTAs: {len(zcta)}")

# Convert to WGS84 if not already
zcta = zcta.to_crs("epsg:4326")

# Filter for Nebraska using geographic bounds
# Nebraska approximate bounds: Lat 40-43°N, Lon -104 to -95.3°W
print("Filtering for Nebraska using geographic bounds...")

# Use the internal point coordinates or centroid to filter
if 'INTPTLAT20' in zcta.columns and 'INTPTLON20' in zcta.columns:
    # Convert string coordinates to float
    zcta['lat'] = zcta['INTPTLAT20'].str.replace('+', '').astype(float)
    zcta['lon'] = zcta['INTPTLON20'].str.replace('+', '').astype(float)
    
    # Filter for Nebraska bounds
    ne = zcta[
        (zcta['lat'] >= 40.0) & (zcta['lat'] <= 43.0) &
        (zcta['lon'] >= -104.05) & (zcta['lon'] <= -95.3)
    ].copy()
else:
    # Use geometry centroids
    centroids = zcta.geometry.centroid
    ne = zcta[
        (centroids.y >= 40.0) & (centroids.y <= 43.0) &
        (centroids.x >= -104.05) & (centroids.x <= -95.3)
    ].copy()
    ne['lat'] = ne.geometry.centroid.y
    ne['lon'] = ne.geometry.centroid.x

print(f"Found {len(ne)} ZCTAs in Nebraska")

# Filter for eastern Nebraska (east of 100°W)
east = ne[ne['lon'] > -100].copy()
east["zip"] = east["ZCTA5CE20"]

print(f"Found {len(east)} ZCTAs in eastern Nebraska")

# Save ZIP list
east[["zip"]].to_csv(out, index=False)
print(f"✓ Wrote {out} with {len(east)} ZIP codes in eastern Nebraska")

# Plot all Nebraska ZIP Codes, highlight eastern ones in red
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(10, 10))

# Plot all Nebraska ZIPs in light gray
ne.plot(ax=ax, color='lightgray', edgecolor='black', linewidth=0.5)

# Plot eastern Nebraska ZIPs in red
if not east.empty:
    east.plot(ax=ax, color='red', edgecolor='black', linewidth=1)

ax.set_title('Nebraska ZIP Codes\nEastern Nebraska (East of 100°W) in Red', fontsize=16)
ax.set_axis_off()
plt.tight_layout()
plt.savefig(ROOT / 'nebraska_zip_map.png', dpi=300)
plt.show()
