# Pipeline Reference

## Overview

The ML Vision Broadband pipeline follows the CENTAUR platform structure with 7 sequential stages.
Pipeline outputs in `data_work/diagnostics/` are canonical for reported metrics.

## Quick Reference

```bash
# Run complete pipeline
python src/pipeline.py run_all

# Run individual stages
python src/pipeline.py ingest_data
python src/pipeline.py link_records
python src/pipeline.py build_panel
python src/pipeline.py run_estimation
python src/pipeline.py estimate_robustness
python src/pipeline.py make_figures
python src/pipeline.py validate_manuscript
```

---

## Stage Details

### Stage 00: Data Ingestion (`s00_ingest.py`)

**Purpose**: Load and validate raw data sources.

**Inputs**:
- `data_raw/manifest/nebraska_streetview_manifest.csv`
- `data_raw/labels/broadband_labels_with_ruca.csv`
- `data_raw/manifest/zip_east_264.csv`

**Outputs**:
- `data_work/data_raw.parquet`
- `data_work/diagnostics/s00_ingest_quality_*.csv`

**Options**:
```bash
python src/pipeline.py ingest_data --use-demo
```

---

### Stage 01: Record Linkage (`s01_link.py`)

**Purpose**: Link images to ZIP codes and validate coverage.

**Inputs**:
- `data_work/data_raw.parquet`
- `IMAGES_DIR` (configured in `src/config.py`, currently `archive/images_legacy/enhanced_processed/images_enhanced_processed`)

**Outputs**:
- `data_work/data_linked.parquet`
- `data_work/diagnostics/linkage_summary.csv`

**Key Metrics**:
- Image coverage: 261/264 ZIPs (98.9%)
- Total images: 7,619
- Average per ZIP: 29.2

---

### Stage 02: Panel Construction (`s02_panel.py`)

**Purpose**: Extract visual features and build analysis panel.

**Inputs**:
- `data_work/data_linked.parquet`
- `IMAGES_DIR` (for feature extraction)
- `data_work/features/` (optional: precomputed features)

**Outputs**:
- `data_work/panel.parquet`
- `data_work/features/extracted_features_*.csv`
- `data_work/diagnostics/panel_summary.csv`

**Options**:
```bash
python src/pipeline.py build_panel --recompute  # Force recomputation
python src/pipeline.py build_panel --max-images 10  # Images per ZIP
```

**Note**: Feature extraction can be slow. Use precomputed features when available.

---

### Stage 03: ML Model Estimation (`s03_estimation.py`)

**Purpose**: Train and evaluate ML models.

**Inputs**:
- `data_work/panel.parquet`

**Outputs**:
- `data_work/diagnostics/estimation_results.csv`
- `data_work/models/*.pkl`

**Model Specifications**:

| Name | Features | Description |
|------|----------|-------------|
| `ruca_baseline` | RUCA1 | Rural-urban baseline |
| `visual_only` | 24 visual | Visual features only |
| `combined` | RUCA + visual | Two-stage model |
| `random_forest` | 24 visual | Random Forest on visual features |

**Options**:
```bash
python src/pipeline.py run_estimation --models ruca_baseline visual_only
python src/pipeline.py run_estimation --all
python src/pipeline.py run_estimation --profile conference
```

**Conference Profile**:
- Uses precomputed feature file `data_work/diagnostics/pretrained_features/pretrained_features_20250728_233330.csv`
- Evaluates with a fixed 80/20 holdout split (seed 42)
- Writes results to `data_work/diagnostics/conference/estimation_results.csv`

---

### Stage 04: Robustness Checks (`s04_robustness.py`)

**Purpose**: Validate results with additional tests.

**Inputs**:
- `data_work/panel.parquet`

**Outputs**:
- `data_work/diagnostics/robustness_results.csv`
- `data_work/diagnostics/spatial_sensitivity/robustness_results.csv`
- `data_work/diagnostics/spatial_sensitivity/spatial_sensitivity_summary.csv`

**Tests Performed**:
1. Spatial vs Random CV comparison
2. RUCA encoding comparisons (ordinal/categorical/grouped)
3. Repeated random CV (baseline stability)
4. Tuned models with nested spatial CV (ridge/elastic net)
5. Tuned tree ensembles with nested spatial CV (RF/ExtraTrees/GBRT)
6. One-stage combined baselines (one-hot RUCA + visuals)
7. Feature ablation (all, infrastructure, color, top_5, top_10)

**Options**:
```bash
python src/pipeline.py estimate_robustness --compare-cv
python src/pipeline.py estimate_robustness --compare-cv --spatial-sensitivity
```

---

### Stage 05: Figure Generation (`s05_figures.py`)

**Purpose**: Create publication-quality figures.

**Inputs**:
- `data_work/panel.parquet`
- `data_work/diagnostics/`

**Outputs**:
- `manuscript_quarto/figures/fig_study_area.png`
- `manuscript_quarto/figures/fig_spatial_groups.png`
- `manuscript_quarto/figures/fig_cv_comparison.png`
- `manuscript_quarto/figures/fig_feature_importance.png`
- `manuscript_quarto/figures/fig_ruca_encoding.png`
- `manuscript_quarto/figures/fig_broadband_by_ruca.png`

**Options**:
```bash
python src/pipeline.py make_figures --figures spatial_groups cv_comparison
```

---

### Stage 06: Manuscript Validation (`s06_manuscript.py`)

**Purpose**: Validate manuscript against requirements.

**Inputs**:
- `manuscript_quarto/`

**Outputs**:
- `data_work/diagnostics/submission_validation.md`

**Options**:
```bash
python src/pipeline.py validate_manuscript --journal default
```

---

## Data Flow Diagram

```
data_raw/
├── manifest/*.csv ──┐
├── labels/*.csv ────┼──► s00_ingest ──► data_work/data_raw.parquet
└── images/ ─────────┘         │
                               ▼
                          s01_link ──► data_work/data_linked.parquet
                               │
                               ▼
                          s02_panel ──► data_work/panel.parquet
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
         s03_estimation   s04_robustness   s05_figures
              │                │                │
              ▼                ▼                ▼
    diagnostics/         diagnostics/     manuscript_quarto/
    estimation_*.csv     robustness_*.csv figures/*.png
    models/*.pkl
```

---

## Configuration

All pipeline configuration is centralized in `src/config.py`:

```python
# Key settings
SPATIAL_CV_N_GROUPS = 5
SPATIAL_GROUPING_METHOD = 'contiguity_queen'
VISUAL_REGULARIZATION = 100.0
RUCA_REGULARIZATION = 1.0
IMAGES_PER_ZIP_MAX = 10
```

---

## Caching

The pipeline supports caching for expensive operations:
- Feature extraction results cached in `data_work/features/`
- Set `--recompute` to force recalculation

---

## Troubleshooting

### "Input file not found"
Run stages in order: s00 → s01 → s02 → s03...

### Feature extraction slow
Use precomputed features or reduce `--max-images`

### Low R² scores
Use `data_work/diagnostics/estimation_results.csv` and `robustness_results.csv` to report current metrics. Do not rely on stale summaries.
