rule all:
    input: "data/interim/labels_ms.csv"

rule setup_zcta:
    output: ".cache/geo/zcta22/tl_2022_us_zcta520.shp"
    script: "scripts/setup_zcta_data.py"

rule zip_list:
    input: 
        zcta=".cache/geo/zcta22/tl_2022_us_zcta520.shp"
    output: "data/raw/zip_east_264.csv"
    script: "scripts/make_zip_list.py"

rule ms_labels:
    input: 
        zip_list="data/raw/zip_east_264.csv"
    output: "data/interim/labels_ms.csv"
    script: "scripts/build_labels_ms.py"

rule manifest:
    input:
        zip_list="data/raw/zip_east_264.csv",
        zcta=".cache/geo/zcta22/tl_2022_us_zcta520.shp"
    output: "data/interim/manifest.parquet"
    script: "scripts/make_manifest.py"
