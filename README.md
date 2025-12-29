# ML Vision Broadband

Computer vision analysis of Google Street View images to predict broadband usage across Nebraska ZIP codes.

## Research Question

Can visual features of the built environment—extracted from street view imagery—predict broadband adoption rates, either alone or as a supplement to traditional rural-urban classifications?

## Key Findings

- **Spatial cross-validation is required** to avoid geographic leakage.
- **Canonical model specs** are RUCA baseline, visual-only, and two-stage combined (see `src/stages/s03_estimation.py`).
- **Current metrics** live in `data_work/diagnostics/estimation_results.csv` and `data_work/diagnostics/robustness_results.csv`.

## Dataset

- **Study Area**: 264 ZCTAs in eastern Nebraska
- **Images**: 7,619 Google Street View images (261 ZCTAs with coverage)
- **Image source**: `archive/images_legacy/enhanced_processed/images_enhanced_processed` (configured in `src/config.py`)
- **Features**: 24 visual features (15 infrastructure + 9 color)
- **Outcome**: Broadband usage rate (0-1 scale)

## Installation

```bash
# Clone or navigate to project
cd "/Volumes/T9/Projects/ML Vision Broadband"

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run Full Pipeline

```bash
python src/pipeline.py run_all
```

### Run Individual Stages

```bash
python src/pipeline.py ingest_data       # Load and validate data
python src/pipeline.py link_records      # Link images to ZIP codes
python src/pipeline.py build_panel       # Extract features, build panel
python src/pipeline.py run_estimation    # Train ML models
python src/pipeline.py estimate_robustness  # Robustness checks
python src/pipeline.py make_figures      # Generate publication figures
python src/pipeline.py validate_manuscript  # Validate manuscript
```

### Model Training Options

```bash
# Train specific models
python src/pipeline.py run_estimation --models ruca_baseline visual_only

# Train all model specifications
python src/pipeline.py run_estimation --all
```

## Project Structure

```
.
├── src/
│   ├── config.py           # Centralized configuration
│   ├── pipeline.py         # CLI entry point
│   ├── stages/             # Pipeline stages (s00-s06)
│   └── utils/              # Shared utilities
├── data_raw/               # Input data (gitignored, canonical)
│   ├── manifest/           # Image manifests
│   ├── labels/             # Broadband labels + RUCA
│   └── images/             # Unused; see IMAGES_DIR in src/config.py
├── data_work/              # Processed data (gitignored)
│   ├── features/           # Extracted visual features
│   ├── models/             # Trained models
│   └── diagnostics/        # Analysis outputs
├── manuscript_quarto/      # Quarto manuscript system
├── doc/                    # Documentation
├── tests/                  # Test suite
└── archive/                # Legacy scripts and image corpora
```

## Methodology

For full methodological details, see `doc/METHODOLOGY.md`. The pipeline uses spatial cross-validation and ridge-based baselines, with optional robustness checks.

## Docs index

- `doc/PIPELINE.md` is the canonical CENTAUR stage reference.
- `doc/METHODOLOGY.md` summarizes methods aligned to the pipeline outputs.
- `doc/DATA_DICTIONARY.md` defines the canonical analysis dataset fields.
- `doc/RESULTS_SUMMARY.md` points to current diagnostics outputs.
- `doc/logs/` stores legacy text dumps from pre-CENTAUR work.
- `manuscript_quarto/` holds the working draft; treat the conference submission as the current draft of this paper and revise directly (no metacommentary).

## Citation

Manuscript drafts live in `manuscript_quarto/`. Use the finalized paper for citation.

## License

Apache 2.0
