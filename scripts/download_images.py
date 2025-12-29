import pandas as pd, requests, cv2, numpy as np, time, pathlib, os, argparse

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
    outfile = outdir / f"{row.sample_id}_{row.heading}.jpg"
    outfile.write_bytes(r.content)
    return "OK"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zips", nargs="+", help="ZIP codes to download")
    args = ap.parse_args()

    man = pd.read_parquet("data/interim/manifest.parquet")
    subset = (man[man.zip.isin(args.zips)] if args.zips
              else man[man.zip.isin(sorted(man.zip.unique())[:3])])

    out_status = []
    for i, row in subset.iterrows():
        status = download(row, pathlib.Path("images")/row.zip)
        out_status.append(status)
        if i % 5 == 4:          # throttle to 5 req/s
            time.sleep(1)

    man.loc[subset.index, "download_status"] = out_status
    man.to_parquet("data/interim/manifest.parquet", index=False)
    print("Finished", len(subset), "requests")

if __name__ == "__main__":
    main()
