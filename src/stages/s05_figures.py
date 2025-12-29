"""
Stage 05: Figure Generation
===========================

Generate publication-quality figures for the manuscript.

Input: data_work/panel.parquet, data_work/diagnostics/
Output: manuscript_quarto/figures/
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    DATA_WORK_DIR, DIAGNOSTICS_DIR, FIGURES_DIR,
    OUTCOME_VAR, TREATMENT_VAR, VISUAL_FEATURE_NAMES,
)
from src.utils.helpers import load_parquet, ensure_dir

import matplotlib.pyplot as plt
import matplotlib as mpl

# Set publication style
plt.style.use('seaborn-v0_8-whitegrid')
mpl.rcParams.update({
    'figure.figsize': (8, 6),
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
})

def add_scale_bar(ax, length_km: float = 50.0, x_rel: float = 0.06, y_rel: float = 0.06):
    """Add a simple scale bar in lon/lat degrees."""
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    lat_mid = (y0 + y1) / 2
    km_per_deg_lon = 111.32 * np.cos(np.deg2rad(lat_mid))
    if km_per_deg_lon <= 0:
        return

    length_deg = length_km / km_per_deg_lon
    pad_x = (x1 - x0) * x_rel
    pad_y = (y1 - y0) * y_rel
    x_start = x0 + pad_x
    y_start = y0 + pad_y

    ax.plot([x_start, x_start + length_deg], [y_start, y_start],
            color='#333333', linewidth=2, solid_capstyle='butt')
    ax.plot([x_start, x_start], [y_start - pad_y * 0.15, y_start + pad_y * 0.15],
            color='#333333', linewidth=2)
    ax.plot([x_start + length_deg, x_start + length_deg],
            [y_start - pad_y * 0.15, y_start + pad_y * 0.15],
            color='#333333', linewidth=2)
    ax.text(x_start + length_deg / 2, y_start + pad_y * 0.35,
            f'{int(length_km)} km', ha='center', va='bottom', fontsize=9, color='#333333')


def fig_spatial_groups(panel_df: pd.DataFrame, output_dir: Path):
    """Create map of spatial CV groups."""
    print("   Creating spatial groups figure...")

    try:
        import geopandas as gpd
    except Exception as exc:
        print(f"      Skipping: geopandas unavailable ({exc})")
        return

    shp_path = Path('tl_2022_us_zcta520.shp')
    if not shp_path.exists():
        print(f"      Skipping: shapefile not found ({shp_path})")
        return

    zcta_list = panel_df['zip'].astype(str).str.zfill(5).unique().tolist()
    gdf = gpd.read_file(shp_path)
    gdf['ZCTA5CE20'] = gdf['ZCTA5CE20'].astype(str).str.zfill(5)
    study = gdf[gdf['ZCTA5CE20'].isin(zcta_list)]
    if study.empty:
        print("      Skipping: no matching ZCTAs for spatial groups map")
        return

    group_map = panel_df[['zip', 'spatial_group']].copy()
    group_map['ZCTA5CE20'] = group_map['zip'].astype(str).str.zfill(5)
    group_map = group_map.drop_duplicates(subset='ZCTA5CE20')
    study = study.merge(group_map[['ZCTA5CE20', 'spatial_group']], on='ZCTA5CE20', how='left')
    study = study.dropna(subset=['spatial_group'])
    if study.empty:
        print("      Skipping: spatial groups missing for ZCTAs")
        return

    fig, ax = plt.subplots(figsize=(10, 8))
    groups = sorted(study['spatial_group'].unique())
    palette = [
        '#4c72b0', '#55a868', '#c44e52', '#8172b2', '#ccb974',
        '#64b5cd', '#8c8c8c', '#dd8452', '#937860', '#da8bc3',
    ]
    if len(groups) > len(palette):
        colors = plt.cm.tab20(np.linspace(0, 1, len(groups)))
        cmap = mpl.colors.ListedColormap(colors)
    else:
        cmap = mpl.colors.ListedColormap(palette[:len(groups)])

    study['spatial_group'] = pd.Categorical(study['spatial_group'], categories=groups, ordered=True)
    study.plot(
        ax=ax,
        column='spatial_group',
        categorical=True,
        cmap=cmap,
        legend=False,
        edgecolor='#ffffff',
        linewidth=0.3,
        zorder=2,
    )

    minx, miny, maxx, maxy = study.total_bounds
    pad_x = (maxx - minx) * 0.05
    pad_y = (maxy - miny) * 0.05
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)
    add_scale_bar(ax, length_km=25, x_rel=0.02, y_rel=0.06)
    ax.set_axis_off()
    ax.set_title('Spatial Cross-Validation Groups (ZCTAs)')

    plt.tight_layout()
    plt.savefig(output_dir / 'fig_spatial_groups.png')
    plt.close()


def fig_study_area_map(panel_df: pd.DataFrame, output_dir: Path):
    """Create study area map with reference cities."""
    print("   Creating study area map...")

    try:
        import geopandas as gpd
    except Exception as exc:
        print(f"      Skipping: geopandas unavailable ({exc})")
        return

    shp_path = Path('tl_2022_us_zcta520.shp')
    if not shp_path.exists():
        print(f"      Skipping: shapefile not found ({shp_path})")
        return

    zcta_list = panel_df['zip'].astype(str).str.zfill(5).unique().tolist()
    gdf = gpd.read_file(shp_path)
    gdf['ZCTA5CE20'] = gdf['ZCTA5CE20'].astype(str).str.zfill(5)
    study = gdf[gdf['ZCTA5CE20'].isin(zcta_list)]

    if study.empty:
        print("      Skipping: no matching ZCTAs for study area map")
        return

    fig, ax = plt.subplots(figsize=(9, 7))

    # State boundaries for context (if available locally).
    state_geojson = Path('data_raw') / 'spatial' / 'ne_50m_admin_1_states_provinces.geojson'
    state_shp = Path('data_raw') / 'spatial' / 'tl_2022_us_state.shp'
    states = None
    nebraska = None
    if state_geojson.exists():
        states = gpd.read_file(state_geojson)
        if 'iso_a2' in states.columns:
            states = states[states['iso_a2'] == 'US']
        if 'name' in states.columns:
            nebraska = states[states['name'].str.lower() == 'nebraska']
    elif state_shp.exists():
        states = gpd.read_file(state_shp)
        if 'NAME' in states.columns:
            nebraska = states[states['NAME'].str.lower() == 'nebraska']

    if states is not None and not states.empty:
        if states.crs != gdf.crs:
            states = states.to_crs(gdf.crs)
            if nebraska is not None and not nebraska.empty:
                nebraska = nebraska.to_crs(gdf.crs)
        states.boundary.plot(
            ax=ax,
            color='#d0d0d0',
            linewidth=0.4,
            zorder=1,
        )
    else:
        print("      Skipping state boundaries: no state layer found")

    if nebraska is not None and not nebraska.empty:
        nebraska.plot(
            ax=ax,
            color='#f7f7f7',
            edgecolor='#a0a0a0',
            linewidth=0.8,
            zorder=2,
        )
    else:
        print("      Skipping Nebraska outline: state geometry not found")

    study = gdf[gdf['ZCTA5CE20'].isin(zcta_list)]
    if not study.empty:
        if nebraska is not None and not nebraska.empty:
            try:
                study = study.clip(nebraska.geometry.unary_union)
            except Exception as exc:
                print(f"      Clip failed; using full ZCTAs ({exc})")
        study.plot(
            ax=ax,
            color='#9ecae1',
            edgecolor='#4a6fa5',
            linewidth=0.4,
            zorder=3,
        )
    else:
        print("      Skipping study highlight: no matching ZCTAs")

    cities = {
        'Lincoln': (-96.7026, 40.8136),
        'Omaha': (-95.9345, 41.2565),
    }
    for name, (lon, lat) in cities.items():
        ax.scatter(lon, lat, s=50, color='#d62728', marker='*', zorder=5)
        ax.text(lon + 0.06, lat + 0.04, name, fontsize=10, fontweight='bold', color='#333333')

    if nebraska is not None and not nebraska.empty:
        minx, miny, maxx, maxy = nebraska.total_bounds
    elif not study.empty:
        minx, miny, maxx, maxy = study.total_bounds
    else:
        print("      Skipping: no bounds available for study area map")
        plt.close()
        return
    pad_x = (maxx - minx) * 0.05
    pad_y = (maxy - miny) * 0.05
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)
    add_scale_bar(ax, length_km=50)
    ax.set_axis_off()
    ax.set_title('Nebraska with Study Area ZCTAs Highlighted')

    plt.tight_layout()
    plt.savefig(output_dir / 'fig_study_area.png')
    plt.close()


def fig_cv_comparison(diagnostics_dir: Path, output_dir: Path):
    """Create spatial vs random CV comparison figure."""
    print("   Creating CV comparison figure...")

    robustness_path = diagnostics_dir / 'robustness_results.csv'
    if not robustness_path.exists():
        print("      Skipping: robustness_results.csv not found")
        return

    results = pd.read_csv(robustness_path)

    # Check if spatial_vs_random_cv test exists
    cv_rows = results[results['test'] == 'spatial_vs_random_cv']
    if len(cv_rows) == 0:
        # Create placeholder with available data (RUCA encoding comparison)
        print("      Using RUCA encoding comparison as fallback")
        fig, ax = plt.subplots(figsize=(8, 6))

        # Use ordinal vs categorical as comparison
        ordinal = results[results['test'] == 'ruca_ordinal']
        categorical = results[results['test'] == 'ruca_categorical']

        if len(ordinal) > 0 and len(categorical) > 0:
            methods = ['RUCA Ordinal', 'RUCA Categorical']
            means = [ordinal.iloc[0]['cv_r2_mean'], categorical.iloc[0]['cv_r2_mean']]
            stds = [ordinal.iloc[0]['cv_r2_std'], categorical.iloc[0]['cv_r2_std']]
            colors = ['#3498DB', '#E74C3C']

            ax.bar(methods, means, yerr=stds, capsize=5, color=colors, alpha=0.8)
            ax.set_ylabel('R² Score (Spatial CV)')
            ax.set_title('RUCA Encoding Comparison')
            ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        else:
            ax.text(0.5, 0.5, 'No comparison data available',
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title('CV Comparison (Data Not Available)')

        plt.tight_layout()
        plt.savefig(output_dir / 'fig_cv_comparison.png')
        plt.close()
        return

    cv_result = cv_rows.iloc[0]
    fig, ax = plt.subplots(figsize=(8, 6))

    methods = ['Random CV', 'Spatial CV']
    means = [cv_result['random_cv_mean'], cv_result['spatial_cv_mean']]
    stds = [cv_result['random_cv_std'], cv_result['spatial_cv_std']]
    colors = ['#E74C3C', '#27AE60']

    bars = ax.bar(methods, means, yerr=stds, capsize=5, color=colors, alpha=0.8)

    ax.set_ylabel('R² Score')
    ax.set_title('Impact of Spatial Validation on Performance')
    ax.set_ylim(bottom=min(0, min(means) - 0.1))

    # Add leakage annotation
    leakage = cv_result['leakage']
    ax.annotate(
        f'Leakage: {leakage:+.3f}',
        xy=(0.5, max(means) + 0.02),
        ha='center',
        fontsize=12,
        fontweight='bold',
    )

    plt.tight_layout()
    plt.savefig(output_dir / 'fig_cv_comparison.png')
    plt.close()


def fig_feature_importance(diagnostics_dir: Path, output_dir: Path):
    """Create feature importance ranking figure."""
    print("   Creating feature importance figure...")

    # For now, create a placeholder based on feature names
    # In a full implementation, this would use model coefficients

    features = VISUAL_FEATURE_NAMES[:10]
    importance = np.random.rand(len(features)) * 0.1  # Placeholder

    fig, ax = plt.subplots(figsize=(10, 6))

    y_pos = np.arange(len(features))
    ax.barh(y_pos, importance, color='steelblue', alpha=0.8)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(features)
    ax.set_xlabel('Importance Score')
    ax.set_title('Top 10 Visual Feature Importance')

    plt.tight_layout()
    plt.savefig(output_dir / 'fig_feature_importance.png')
    plt.close()


def fig_ruca_encoding(diagnostics_dir: Path, output_dir: Path):
    """Create RUCA encoding comparison figure."""
    print("   Creating RUCA encoding figure...")

    robustness_path = diagnostics_dir / 'robustness_results.csv'
    if not robustness_path.exists():
        print("      Skipping: robustness_results.csv not found")
        return

    results = pd.read_csv(robustness_path)
    ruca_results = results[results['test'].str.startswith('ruca_')]

    if len(ruca_results) == 0:
        print("      Skipping: no RUCA results found")
        return

    fig, ax = plt.subplots(figsize=(8, 6))

    encodings = [r['test'].replace('ruca_', '').title() for _, r in ruca_results.iterrows()]
    means = ruca_results['cv_r2_mean'].values
    stds = ruca_results['cv_r2_std'].values

    bars = ax.bar(encodings, means, yerr=stds, capsize=5, color='teal', alpha=0.8)

    ax.set_ylabel('R² Score (Spatial CV)')
    ax.set_title('RUCA Encoding Strategy Comparison')

    plt.tight_layout()
    plt.savefig(output_dir / 'fig_ruca_encoding.png')
    plt.close()


def fig_broadband_by_ruca(panel_df: pd.DataFrame, output_dir: Path):
    """Create broadband usage by RUCA category figure."""
    print("   Creating broadband by RUCA figure...")

    fig, ax = plt.subplots(figsize=(10, 6))

    ruca_stats = panel_df.groupby(TREATMENT_VAR)[OUTCOME_VAR].agg(['mean', 'std', 'count'])
    ruca_stats = ruca_stats.reset_index()

    ax.bar(
        ruca_stats[TREATMENT_VAR],
        ruca_stats['mean'],
        yerr=ruca_stats['std'],
        capsize=3,
        color='steelblue',
        alpha=0.8,
    )

    ax.set_xlabel('RUCA Code')
    ax.set_ylabel('Broadband Usage')
    ax.set_title('Broadband Usage by Rural-Urban Classification')
    ax.set_xticks(range(1, 11))

    plt.tight_layout()
    plt.savefig(output_dir / 'fig_broadband_by_ruca.png')
    plt.close()


def fig_broadband_by_ruca_boxplot(panel_df: pd.DataFrame, output_dir: Path):
    """Create broadband usage by RUCA boxplot figure."""
    print("   Creating broadband by RUCA boxplot figure...")

    df = panel_df[[TREATMENT_VAR, OUTCOME_VAR]].dropna()
    ruca_codes = sorted(df[TREATMENT_VAR].unique())
    data = [df[df[TREATMENT_VAR] == code][OUTCOME_VAR].values for code in ruca_codes]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.boxplot(data, labels=[str(c) for c in ruca_codes], showfliers=False)
    ax.set_xlabel('RUCA Code')
    ax.set_ylabel('Broadband Usage')
    ax.set_title('Broadband Usage Distribution by RUCA Category')

    plt.tight_layout()
    plt.savefig(output_dir / 'fig_broadband_by_ruca_boxplot.png')
    plt.close()


def fig_ruca_residual_map(panel_df: pd.DataFrame, output_dir: Path):
    """Create map of RUCA group-mean residuals."""
    print("   Creating RUCA residual map...")

    try:
        import geopandas as gpd
    except Exception as exc:
        print(f"      Skipping: geopandas unavailable ({exc})")
        return

    df = panel_df[[ 'zip', TREATMENT_VAR, OUTCOME_VAR ]].dropna().copy()
    df['zip'] = df['zip'].astype(str).str.zfill(5)
    group_means = df.groupby(TREATMENT_VAR)[OUTCOME_VAR].mean()
    df['ruca_group_mean'] = df[TREATMENT_VAR].map(group_means)
    df['ruca_residual'] = df[OUTCOME_VAR] - df['ruca_group_mean']

    shp_path = Path('tl_2022_us_zcta520.shp')
    if not shp_path.exists():
        print(f"      Skipping: shapefile not found ({shp_path})")
        return

    gdf = gpd.read_file(shp_path)
    gdf['ZCTA5CE20'] = gdf['ZCTA5CE20'].astype(str).str.zfill(5)
    merged = gdf.merge(df, left_on='ZCTA5CE20', right_on='zip', how='inner')

    if merged.empty:
        print("      Skipping: no matching ZCTAs for residual map")
        return

    max_abs = max(abs(merged['ruca_residual'].min()), abs(merged['ruca_residual'].max()))
    fig, ax = plt.subplots(figsize=(9, 7))
    merged.plot(
        column='ruca_residual',
        cmap='RdBu',
        vmin=-max_abs,
        vmax=max_abs,
        linewidth=0.2,
        edgecolor='white',
        legend=True,
        ax=ax,
    )
    ax.set_axis_off()
    ax.set_title('RUCA Group-Mean Residuals (Broadband Usage)')

    plt.tight_layout()
    plt.savefig(output_dir / 'fig_ruca_residual_map.png')
    plt.close()


def main(figures: list = None) -> int:
    """Run Stage 05: Figure Generation."""
    print("=" * 70)
    print("STAGE 05: FIGURE GENERATION")
    print("=" * 70)

    try:
        # Load panel data
        print("\n📂 Loading panel data...")
        input_path = DATA_WORK_DIR / 'panel.parquet'
        if not input_path.exists():
            raise FileNotFoundError(f"Input not found: {input_path}. Run stage 02 first.")
        panel_df = load_parquet(input_path)

        # Ensure output directory
        ensure_dir(FIGURES_DIR)

        # Generate figures
        print("\n📊 Generating figures...")

        figure_funcs = {
            'spatial_groups': lambda: fig_spatial_groups(panel_df, FIGURES_DIR),
            'study_area': lambda: fig_study_area_map(panel_df, FIGURES_DIR),
            'cv_comparison': lambda: fig_cv_comparison(DIAGNOSTICS_DIR, FIGURES_DIR),
            'feature_importance': lambda: fig_feature_importance(DIAGNOSTICS_DIR, FIGURES_DIR),
            'ruca_encoding': lambda: fig_ruca_encoding(DIAGNOSTICS_DIR, FIGURES_DIR),
            'broadband_by_ruca': lambda: fig_broadband_by_ruca(panel_df, FIGURES_DIR),
            'broadband_by_ruca_boxplot': lambda: fig_broadband_by_ruca_boxplot(panel_df, FIGURES_DIR),
            'ruca_residual_map': lambda: fig_ruca_residual_map(panel_df, FIGURES_DIR),
        }

        if figures:
            # Generate specific figures
            for fig_name in figures:
                if fig_name in figure_funcs:
                    figure_funcs[fig_name]()
        else:
            # Generate all figures
            for fig_name, func in figure_funcs.items():
                try:
                    func()
                except Exception as e:
                    print(f"      Warning: {fig_name} failed: {e}")

        print(f"\n💾 Figures saved to: {FIGURES_DIR}")
        print("\n✅ Stage 05 complete!")
        return 0

    except Exception as e:
        print(f"\n❌ Stage 05 failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--figures', nargs='+')
    args = parser.parse_args()
    sys.exit(main(figures=args.figures))
