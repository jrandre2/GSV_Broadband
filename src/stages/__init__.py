# Pipeline Stages
"""
CENTAUR pipeline stages for ML Vision Broadband.

Stages:
- s00_ingest: Load manifest, labels, RUCA codes
- s01_link: Link images to ZIP codes and labels
- s02_panel: Extract CV features, build analysis panel
- s03_estimation: Train ML models
- s04_robustness: Robustness checks (spatial CV, ablation)
- s05_figures: Generate publication figures
- s06_manuscript: Validate manuscript
"""
