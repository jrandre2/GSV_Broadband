import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
shp_path = ROOT / "tl_2022_us_zcta520.shp"

# Load all ZCTA data
zcta = gpd.read_file(shp_path)
zcta = zcta.to_crs("epsg:4326")

# Use internal point coordinates if available, else use centroid
if 'INTPTLAT20' in zcta.columns and 'INTPTLON20' in zcta.columns:
    zcta['lat'] = zcta['INTPTLAT20'].str.replace('+', '').astype(float)
    zcta['lon'] = zcta['INTPTLON20'].str.replace('+', '').astype(float)
else:
    zcta['lat'] = zcta.geometry.centroid.y
    zcta['lon'] = zcta.geometry.centroid.x

# Filter for Nebraska using geographic bounds
ne = zcta[(zcta['lat'] >= 40.0) & (zcta['lat'] <= 43.0) &
          (zcta['lon'] >= -104.05) & (zcta['lon'] <= -95.3)].copy()

# Eastern Nebraska ZIPs (east of 100°W)
east = ne[ne['lon'] > -100].copy()

# Plot
fig, ax = plt.subplots(figsize=(10, 10))
ne.plot(ax=ax, color='lightgray', edgecolor='black', linewidth=0.5)
east.plot(ax=ax, color='red', edgecolor='black', linewidth=0.7)

ax.set_title('Nebraska ZIP Codes\nEastern Nebraska (East of 100°W) in Red', fontsize=16)
ax.set_axis_off()
plt.tight_layout()
plt.savefig(ROOT / 'nebraska_zip_map.png', dpi=300)
plt.show()
print(f"Map saved to {ROOT / 'nebraska_zip_map.png'}")
