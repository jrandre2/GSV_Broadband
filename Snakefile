rule all:
    input: "data/interim/labels_ms.csv"

rule zip_list:
    output: "data/raw/zip_east_264.csv"
    script: "scripts/make_zip_list.py"

rule ms_labels:
    input: zip_list="data/raw/zip_east_264.csv"
    output: "data/interim/labels_ms.csv"
    script: "scripts/build_labels_ms.py"
