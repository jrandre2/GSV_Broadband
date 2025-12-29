# Methodology

## Research Design

This study examines whether computer vision features extracted from Google Street View imagery can predict broadband adoption rates across ZCTAs, either independently or as a supplement to traditional rural-urban classifications.

## Data Sources

### Street View Imagery
- **Source**: Google Street View API (archived corpus)
- **Coverage**: 261 of 264 study area ZCTAs (98.9%)
- **Total Images**: 7,619 images
- **Headings**: 4 cardinal directions (0°, 90°, 180°, 270°)
- **Average per covered ZCTA**: 29.2 images (min 4, max 52)

### Broadband Labels
- **Source**: Microsoft broadband usage data
- **Measure**: Proportion of population with broadband access
- **Unit**: ZIP code level

### Rural-Urban Classification
- **Source**: USDA Rural-Urban Commuting Area (RUCA) codes
- **Version**: 2010 Census-based codes
- **Categories**: 10-point scale (1 = urban core, 10 = rural)

## Feature Extraction

### Visual Feature Pipeline

Features are extracted using OpenCV from each image:

1. **Color Space Conversion**
   - BGR → HSV for color analysis
   - BGR → Grayscale for edge detection

2. **Infrastructure Detection** (15 features)
   - Edge detection (Canny, Sobel)
   - Line detection (horizontal/vertical)
   - Texture analysis (Laplacian variance)

3. **Color Analysis** (9 features)
   - HSV channel statistics
   - Vegetation detection (green ratio)
   - Sky detection (blue ratio)

### Aggregation

Features are aggregated to ZCTA level:
- Mean across up to 10 images per ZCTA
- Failed extractions excluded from mean

## Spatial Cross-Validation

### Problem: Geographic Data Leakage

Standard k-fold cross-validation can inflate performance metrics when data exhibits spatial autocorrelation. Neighboring ZIP codes have similar characteristics, so random train/test splits allow the model to "memorize" geographic patterns.

### Solution: Spatial Grouping

1. **Group Creation**
   - Contiguity-constrained clustering of ZCTA polygons (queen contiguity)
   - 5 groups to balance fold sizes while keeping adjacent ZCTAs together
   - Sensitivity runs: rook contiguity, k-means on centroids, latitude/longitude bands, spatial blocks

2. **GroupKFold CV**
   - Each fold: 4 groups train, 1 group test
   - Ensures adjacent ZCTAs remain in the same fold

3. **Leakage Quantification**
   - Compare spatial CV to random CV
   - Record leakage in `data_work/diagnostics/robustness_results.csv`

## Model Specifications

### Baseline: RUCA Only
```
broadband_usage ~ β₀ + β₁·RUCA1
```
- **Model**: Ridge regression (α = 1.0)
- **Metrics**: See `data_work/diagnostics/estimation_results.csv`

### Visual Features Only
```
broadband_usage ~ β₀ + Σᵢ βᵢ·visual_featureᵢ
```
- **Model**: Ridge regression (α = 100)
- **Metrics**: See `data_work/diagnostics/estimation_results.csv`

### Two-Stage Combined Model

**Stage 1: RUCA Baseline**
```
ŷ_ruca = β₀ + β₁·RUCA1
residuals = y - ŷ_ruca
```

**Stage 2: Visual Residuals**
```
ŷ_visual = γ₀ + Σᵢ γᵢ·visual_featureᵢ
```
(fitted on residuals)

**Final Prediction**
```
ŷ_final = ŷ_ruca + ŷ_visual
```
- **Metrics**: See `data_work/diagnostics/estimation_results.csv`

## Regularization Strategy

Strong regularization is required to prevent overfitting on the limited sample size (N = 264):

| Model | Ridge α | Rationale |
|-------|---------|-----------|
| RUCA baseline | 1.0 | Single feature, low complexity |
| Visual features | 100.0 | Many features, small sample |

## Robustness Checks

### RUCA Encoding Comparisons
- Ordinal (1-10)
- Categorical (one-hot encoding)
- Grouped (metro/micro/small/rural)

### Feature Ablation
- Infrastructure features only
- Color features only
- Top-N features

### Validation Method Comparison
- Random 5-fold CV (biased)
- Spatial GroupKFold (unbiased)

## Interpretation Guidelines

1. **Use spatial CV metrics**: report `cv_r2_mean`/`cv_r2_std` from diagnostics
2. **Avoid hardcoded values**: results can change with data and configuration
3. **Compare against RUCA baseline** for all interpretations

## Limitations

1. **Sample Size**: 264 ZIP codes limits model complexity
2. **Spatial Autocorrelation**: Difficult to fully eliminate
3. **Image Quality**: Varies by location and collection date
4. **Feature Engineering**: Manual features may miss patterns
5. **Single State**: Results may not generalize nationally
