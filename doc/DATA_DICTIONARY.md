# Data Dictionary

## Overview

This document defines all variables used in the ML Vision Broadband analysis pipeline.
The canonical analysis dataset is `data_work/panel.parquet` (Stage 02 output).

## Naming Conventions

- **Case**: Lowercase with underscores (snake_case)
- **Prefixes**:
  - `n_`: Count variables
  - `is_` / `has_`: Boolean indicators
  - `pct_`: Percentages (0-100)
- **Suffixes**:
  - `_ratio`: Proportion (0-1)
  - `_density`: Per-unit area measure

---

## Identifier Variables

| Variable | Type | Description |
|----------|------|-------------|
| `zip` | str | 5-digit ZIP code (zero-padded) |
| `spatial_group` | int | Spatial CV group assignment (0-4) |

## Outcome Variable

| Variable | Type | Range | Description |
|----------|------|-------|-------------|
| `broadband_usage` | float | 0-1 | Broadband adoption rate for ZIP code |

## Treatment/Classification Variables

| Variable | Type | Values | Description |
|----------|------|--------|-------------|
| `RUCA1` | int | 1-10 | Primary RUCA code |
| `RUCA2` | float | 1.0-10.3 | Secondary RUCA code |

### RUCA Code Definitions

| Code | Category | Description |
|------|----------|-------------|
| 1 | Metropolitan | Metropolitan area core |
| 2 | Metropolitan | High commuting to metro (30-50%) |
| 3 | Metropolitan | Low commuting to metro (10-30%) |
| 4 | Micropolitan | Micropolitan area core |
| 5 | Micropolitan | High commuting to micro |
| 6 | Micropolitan | Low commuting to micro |
| 7 | Small Town | Small town core |
| 8 | Small Town | High commuting to small town |
| 9 | Small Town | Low commuting to small town |
| 10 | Rural | Rural areas |

---

## Geographic Variables

| Variable | Type | Description |
|----------|------|-------------|
| `latitude` | float | ZIP centroid latitude |
| `longitude` | float | ZIP centroid longitude |

## Image Metadata Variables

| Variable | Type | Description |
|----------|------|-------------|
| `n_images` | int | Number of images in panel |
| `n_images_available` | int | Total images available for ZIP |
| `has_images` | bool | Whether ZIP has image coverage |
| `link_status` | str | Image linkage status ('linked', 'no_images') |
| `has_features` | bool | Whether features were extracted |

---

## Visual Features (24 Total)

### Infrastructure Features (15)

| Variable | Type | Range | Description |
|----------|------|-------|-------------|
| `edge_density` | float | 0-1 | Proportion of edge pixels (Canny) |
| `vertical_density` | float | 0-1 | Vertical edge strength (poles/buildings) |
| `horizontal_density` | float | 0-1 | Horizontal edge strength (roads/horizons) |
| `infrastructure_ratio` | float | 0-1 | Gray/black low-saturation area ratio |
| `road_density` | float | 0-1 | Dark gray horizontal region ratio |
| `building_density` | float | 0-1 | Edge density excluding sky |
| `pole_density` | float | 0-1 | Thin vertical line detection |
| `wire_density` | float | 0-1 | Thin horizontal lines in upper image |
| `pavement_ratio` | float | 0-1 | Lower image gray regions |
| `structure_complexity` | float | 0-1 | Laplacian variance (normalized) |
| `urban_texture` | float | 0-1 | Grayscale standard deviation |
| `development_index` | float | 0-1 | Combined development metric |
| `infrastructure_continuity` | float | 0-1 | Connected edge region count (log) |
| `built_ratio` | float | 0-1 | Non-sky, non-vegetation ratio |
| `openness` | float | 0-1 | Inverse of edge + structure complexity |

### Color Features (9)

| Variable | Type | Range | Description |
|----------|------|-------|-------------|
| `brightness` | float | 0-1 | Mean V channel (HSV) |
| `saturation` | float | 0-1 | Mean S channel (HSV) |
| `color_variance` | float | 0-1 | RGB channel variance |
| `vegetation_ratio` | float | 0-1 | Green area ratio (HSV H=40-80) |
| `sky_ratio` | float | 0-1 | Blue high-brightness area ratio |
| `gray_ratio` | float | 0-1 | Low-saturation area ratio |
| `hue_diversity` | float | 0-1 | Entropy of hue histogram |
| `contrast` | float | 0-1 | 95th-5th percentile intensity range |
| `colorfulness` | float | 0-1 | RG/YB channel variability |

---

## Model Output Variables

| Variable | Type | Description |
|----------|------|-------------|
| `train_r2` | float | Training R² score |
| `cv_r2_mean` | float | Cross-validation R² mean |
| `cv_r2_std` | float | Cross-validation R² std dev |
| `rmse` | float | Root mean squared error |
| `mae` | float | Mean absolute error |

---

## Data Quality Flags

| Variable | Type | Description |
|----------|------|-------------|
| `missing_pct` | float | Percentage of missing values |
| `is_valid` | bool | Passes quality thresholds |
