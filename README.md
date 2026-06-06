# GSV Broadband: Street View Imagery and Broadband Adoption in Rural Nebraska

This project investigates whether the physical appearance of communities—as captured in Google Street View (GSV) imagery—can predict broadband internet adoption rates. Using computer vision applied to over 7,600 street-level photographs across eastern Nebraska, we explore whether visual signals of infrastructure and built-environment development supplement traditional rural-urban classifications in explaining the broadband divide.

## Manuscript

The paper is at the repository root:

- [`manuscript.pdf`](manuscript.pdf) — current submission PDF
- [`manuscript.docx`](manuscript.docx) — editable Word document

Source (Quarto) and publication figures are in [`manuscript_quarto/`](manuscript_quarto/).

## Research Question

Can visual features of the built environment—extracted from street view imagery—predict broadband adoption rates, either alone or as a supplement to standard rural-urban typologies (USDA RUCA codes)?

## Approach

1. **Image collection**: 7,619 GSV images sampled from 261 of 264 study-area ZIP Code Tabulation Areas (ZCTAs) in eastern Nebraska, covering four cardinal directions per location.
2. **Feature extraction**: 24 visual features per image using OpenCV — 15 infrastructure features (edges, line density, texture) and 9 color features (vegetation, sky ratio, HSV statistics) — aggregated to the ZCTA level.
3. **Modeling**: Three ridge-regression specifications — RUCA-only baseline, visual-features-only, and a two-stage combined model — evaluated under spatially-aware cross-validation to prevent geographic data leakage.
4. **Outcome**: Broadband usage rate (0–1) from Microsoft broadband usage data, at the ZIP code level.


## Key Findings

Spatial cross-validation is essential: neighboring ZCTAs share broadband adoption rates, so standard random cross-validation inflates apparent model performance. Results under spatially-aware evaluation are reported in the manuscript and in [`doc/RESULTS_SUMMARY.md`](doc/RESULTS_SUMMARY.md).

## Repository Map

| Path | Contents |
|------|----------|
| `manuscript.pdf` / `manuscript.docx` | Root manuscript (canonical published snapshots) |
| `manuscript_quarto/` | Quarto source, figures, bibliography |
| `src/` | Pipeline source code (stages `s00`–`s06`, utilities, config) |
| `scripts/` | Data preparation and download scripts |
| `data_raw/` | Raw inputs: image manifests, broadband labels, RUCA codes *(gitignored)* |
| `data_work/` | Processed data, extracted features, trained models, diagnostics *(gitignored)* |
| `models/` | Production model artifact (`production_broadband_predictor.pkl`) *(not committed — ~53 MB)* |
| `images/` | GSV image corpus (~129 MB, ~7,600 images) *(not committed — see data notes below)* |
| `results/` | Output tables, figures, CSVs from model runs |
| `doc/` | Methodology, pipeline reference, data dictionary, results summary |
| `tests/` | Unit and integration tests |
| `archive/` | Legacy scripts and image corpora (pre-CENTAUR pipeline) |

## Data and Reproducibility Notes

**Images and model are not committed to this repository** due to file size. The GSV image corpus (~129 MB across 511 ZCTA directories) and the trained model file (`models/production_broadband_predictor.pkl`, ~53 MB) are stored locally. Researchers wishing to reproduce the analysis will need access to a Google Street View Static API key and should follow the collection protocol described in [`doc/METHODOLOGY.md`](doc/METHODOLOGY.md).

Processed feature matrices and intermediate Parquet files are also excluded (`data_work/` is gitignored). The pipeline re-derives them from raw inputs; see [`doc/PIPELINE.md`](doc/PIPELINE.md) for stage-by-stage instructions.


## Documentation

- [`doc/METHODOLOGY.md`](doc/METHODOLOGY.md) — full methods: feature extraction, spatial CV, model specs, regularization strategy
- [`doc/PIPELINE.md`](doc/PIPELINE.md) — stage-by-stage pipeline reference with commands
- [`doc/DATA_DICTIONARY.md`](doc/DATA_DICTIONARY.md) — canonical variable definitions
- [`doc/RESULTS_SUMMARY.md`](doc/RESULTS_SUMMARY.md) — pointers to current diagnostic outputs
- [`doc/MODEL_COMPARISON.md`](doc/MODEL_COMPARISON.md) — model specification comparison
- [`doc/JIP_SUBMISSION.md`](doc/JIP_SUBMISSION.md) — journal submission notes

## Environment Setup

Requires Python 3.11+. See [`requirements.txt`](requirements.txt) or [`env.yml`](env.yml) for dependencies. Full setup and pipeline instructions are in [`doc/PIPELINE.md`](doc/PIPELINE.md).

## License

Apache 2.0
