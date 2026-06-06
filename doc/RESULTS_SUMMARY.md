# Results Summary

The pipeline is canonical. Use the diagnostics outputs for any reported metrics.

## Canonical Outputs

- data_work/diagnostics/estimation_results.csv (model metrics for ruca_baseline, visual_only, combined)
- data_work/diagnostics/robustness_results.csv (spatial vs random CV, RUCA encodings, feature ablations)
- data_work/diagnostics/spatial_sensitivity/robustness_results.csv (spatial grouping sensitivity runs)
- data_work/diagnostics/spatial_sensitivity/spatial_sensitivity_summary.csv (summary for key tests)
- data_work/diagnostics/linkage_summary.csv and panel_summary.csv (data coverage and panel checks)
- data_work/diagnostics/conference/estimation_results.csv (conference reproduction profile, holdout metrics)

## Notes

- Use cv_r2_mean/std for reporting. Train R2 is in-sample only.
- Conference profile uses test_r2 from the holdout split.
- Legacy results dumps live in doc/logs/results_summary_legacy.md.
- Canonical panel uses the 24 OpenCV feature set (edge/texture/color/infrastructure proxies).
- Image corpus: `archive/images_legacy/enhanced_processed/images_enhanced_processed` (7,619 images; 261/264 ZCTAs; mean 29.2 per covered ZCTA).

## Robustness (Nested Spatial CV, Tuned Models)

- Output: data_work/diagnostics/robustness_results.csv
- Tuned spatial CV (cv_r2_mean +/- cv_r2_std):
  - RUCA (best tuned): RandomForest -0.209 +/- 0.136; Categorical Ridge -0.276 +/- 0.186
  - Visual (best tuned): GBRT -0.457 +/- 0.737
  - Combined one-stage (best tuned): ExtraTrees -0.389 +/- 0.270
  - Combined two-stage (tuned): -0.275 +/- 0.189
- Additional diagnostics (spatial CV):
  - RUCA group-mean baseline: -0.309 +/- 0.208
  - RUCA1+RUCA2 categorical: -0.236 +/- 0.184
  - Late-fusion (stacked): -0.276 +/- 0.190

## Spatial Grouping Sensitivity

- Output: data_work/diagnostics/spatial_sensitivity/spatial_sensitivity_summary.csv
- Ranges across grouping methods:
  - RUCA categorical: -0.276 (contiguity) to 0.219 (longitude bands)
  - Combined two-stage: -0.386 (contiguity) to 0.040 (longitude bands)

## Cap Sensitivity (Image Cap)

- Output: data_work/diagnostics/cap_sensitivity/max_images_*/estimation_results.csv
- Combined spatial CV (cv_r2_mean): -0.050 to -0.019 across caps (5/10/20/all)
- Visual-only spatial CV (cv_r2_mean): -0.196 to -0.173 across caps
- RUCA baseline is unchanged (cv_r2_mean -0.010)

## Analysis Add-ons (SR-004)

- Output: data_work/diagnostics/analysis_addons/holdout_acs_baselines.csv, coordinate_baselines.csv, fold_diagnostics.csv, cap_sensitivity_summary.csv.
- Holdout ACS subset (N=258): RUCA categorical R² 0.250; ACS-only 0.062; RUCA+ACS 0.127.
- Coordinate baselines: holdout lat/long R² -0.068; spatial CV lat/long -1.306 ± 1.414; longitude-only spatial CV -0.815 ± 1.161.
- Visual ridge cap sensitivity: holdout test R² 0.045-0.077; spatial CV mean -0.196 to -0.173 across caps.

## Conference Reproduction (enhanced_optimal_features_20251228_122633.csv)

- Data source: data/processed/enhanced_optimal_features_20251228_122633.csv (261 ZIPs)
- Output: data_work/diagnostics/conference/estimation_results.csv
- Holdout test_r2:
  - RUCA baseline: linear 0.1439; ExtraTrees 0.3918; RandomForest 0.3906; GradientBoosting 0.3920
  - Visual-only: ElasticNet 0.2298 (best); RandomForest 0.1449; ExtraTrees 0.1314; GradientBoosting 0.1149
  - Combined: ElasticNet 0.2276 (best); ExtraTrees 0.1574; RandomForest 0.1394; GradientBoosting 0.1126

## Conference Reproduction (enhanced_all_features_20251228_124331.csv)

- Data source: data/processed/enhanced_all_features_20251228_124331.csv (264 ZIPs)
- Output: data_work/diagnostics/conference/estimation_results.csv
- Holdout test_r2:
  - RUCA baseline: linear 0.1439; one-hot ridge 0.4003; tuned RandomForest 0.4102
  - Visual-only: ElasticNet 0.2990 (baseline best); tuned ExtraTrees 0.3726 (overall best)
  - Combined: ElasticNet 0.2990 (baseline best); tuned ExtraTrees 0.3760 (overall best)
- Tuned tree ensembles (holdout, best per feature set):
  - RUCA-only: RandomForest 0.4102
  - Visual-only: ExtraTrees 0.3726
  - Combined: ExtraTrees 0.3760

## Conference Comparison (Best test_r2)

- Visual-only (baseline): 0.2298 (optimal features, 261 ZIPs) vs 0.2990 (full features, 264 ZIPs)
- Combined (baseline): 0.2276 (optimal features, 261 ZIPs) vs 0.2990 (full features, 264 ZIPs)
