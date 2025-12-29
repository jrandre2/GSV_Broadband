import pandas as pd, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
raw  = ROOT / ".cache" / "labels" / "Zip" / "zip.csv"
zips = pd.read_csv(ROOT / "data" / "raw" / "zip_east_264.csv")["zip"].astype(str)

df = pd.read_csv(raw, dtype={"zip":"string"})
df = (df.loc[df.zip.isin(zips) & (df.total_device_count >= 20),    # coverage rule
             ["zip","percentage_fast_devices","total_device_count"]]
        .rename(columns={"percentage_fast_devices": "pct_25_3"}))

out = ROOT / "data" / "interim" / "labels_ms.csv"
out.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(out, index=False)
print("Saved", out, len(df), "rows on", datetime.date.today())
