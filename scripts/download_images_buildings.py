import pandas as pd, requests, cv2, numpy as np, time, pathlib, os, argparse, json

API_KEY = os.environ["GOOGLE_API_KEY"]
BASE = "https://maps.googleapis.com/maps/api/streetview"

def is_blurry(img_bytes, thresh=100):
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return True
    return cv2.Laplacian(img, cv2.CV_64F).var() < thresh

def download(row, outdir):
    params = dict(
        size="640x640",
        location=f"{row.lat},{row.lon}",
        heading=row.heading,
        pitch=0,
        key=API_KEY
    )
    r = requests.get(BASE, params=params, timeout=10)
    if r.status_code != 200:
        return "MISS"
    if b"no imagery" in r.content.lower():
        return "MISS"
    if is_blurry(r.content):
        return "BLUR"
    outdir.mkdir(parents=True, exist_ok=True)
    # Compose filename with building metadata if available
    building_category = row.get('building_category', 'NA')
    bsl_status = row.get('bsl_status', 'NA')
    filename = f"{row.sample_id}_{row.heading}_{building_category}_{bsl_status}.jpg"
    outfile = outdir / filename
    outfile.write_bytes(r.content)
    # Write metadata JSON
    metadata = {
        'building_id': row.get('building_id'),
        'building_area_sqm': row.get('building_area_sqm'),
        'building_category': row.get('building_category'),
        'bsl_status': row.get('bsl_status'),
        'bsl_location_id': row.get('bsl_location_id'),
        'service_tier': row.get('service_tier'),
        'technology': row.get('technology'),
        'ms_pct_25_3': row.get('ms_pct_25_3'),
        'ms_device_count': row.get('ms_device_count')
    }
    meta_file = outfile.with_suffix('.json')
    meta_file.write_text(json.dumps(metadata, indent=2))
    return "OK"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zips", nargs="+", help="ZIP codes to download")
    args = ap.parse_args()

    # Use manifest with building metadata if available
    man_path = pathlib.Path("data/interim/manifest_buildings_with_bsl.parquet")
    if not man_path.exists():
        man_path = pathlib.Path("data/interim/manifest_buildings.parquet")
    man = pd.read_parquet(man_path)
    subset = (man[man.zip.isin(args.zips)] if args.zips
              else man[man.zip.isin(sorted(man.zip.unique())[:3])])

    out_status = []
    for i, row in subset.iterrows():
        status = download(row, pathlib.Path("images")/str(row.zip))
        out_status.append(status)
        if i % 5 == 4:
            time.sleep(1)
    man.loc[subset.index, "download_status"] = out_status
    man.to_parquet(man_path, index=False)
    print("Finished", len(subset), "requests")

if __name__ == "__main__":
    main()
