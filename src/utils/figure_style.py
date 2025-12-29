"""
Figure Styling Utilities
========================

Matplotlib styling for publication-quality figures.
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
from typing import Tuple, Optional


# Color palettes
COLORS = {
    'primary': '#2E86AB',      # Blue
    'secondary': '#A23B72',    # Magenta
    'accent': '#F18F01',       # Orange
    'success': '#C73E1D',      # Red
    'neutral': '#3B3B3B',      # Dark gray
    'light': '#E8E8E8',        # Light gray
}

# Sequential palette for heatmaps
SEQUENTIAL_PALETTE = ['#FFF7EC', '#FEE8C8', '#FDD49E', '#FDBB84',
                      '#FC8D59', '#EF6548', '#D7301F', '#B30000', '#7F0000']

# Diverging palette for correlation
DIVERGING_PALETTE = ['#2166AC', '#4393C3', '#92C5DE', '#D1E5F0',
                     '#F7F7F7', '#FDDBC7', '#F4A582', '#D6604D', '#B2182B']


def set_publication_style():
    """
    Set matplotlib defaults for publication-quality figures.
    """
    plt.style.use('seaborn-v0_8-whitegrid')

    mpl.rcParams.update({
        # Figure
        'figure.figsize': (8, 6),
        'figure.dpi': 150,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.1,

        # Font
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
        'font.size': 11,

        # Axes
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'axes.linewidth': 1.2,
        'axes.spines.top': False,
        'axes.spines.right': False,

        # Ticks
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'xtick.major.width': 1.0,
        'ytick.major.width': 1.0,

        # Legend
        'legend.fontsize': 10,
        'legend.frameon': True,
        'legend.framealpha': 0.9,

        # Lines
        'lines.linewidth': 2.0,
        'lines.markersize': 8,

        # Grid
        'grid.alpha': 0.3,
        'grid.linewidth': 0.5,
    })


def get_figure(
    nrows: int = 1,
    ncols: int = 1,
    figsize: Optional[Tuple[float, float]] = None,
    constrained_layout: bool = True,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a figure with consistent styling.

    Parameters
    ----------
    nrows, ncols : int
        Number of subplot rows and columns.
    figsize : tuple, optional
        Figure size (width, height). If None, uses defaults.
    constrained_layout : bool
        Whether to use constrained layout.

    Returns
    -------
    fig, axes : tuple
        Matplotlib figure and axes.
    """
    if figsize is None:
        width = 4 + 4 * ncols
        height = 3 + 3 * nrows
        figsize = (width, height)

    fig, axes = plt.subplots(
        nrows, ncols,
        figsize=figsize,
        constrained_layout=constrained_layout,
    )
    return fig, axes


def add_significance_annotation(
    ax: plt.Axes,
    x1: float,
    x2: float,
    y: float,
    p_value: float,
    height: float = 0.02,
):
    """
    Add significance annotation bracket between two bars.

    Parameters
    ----------
    ax : plt.Axes
        Axes to annotate.
    x1, x2 : float
        X positions of the two bars.
    y : float
        Y position for the bracket.
    p_value : float
        P-value for significance stars.
    height : float
        Height of the bracket.
    """
    # Determine significance stars
    if p_value < 0.001:
        text = '***'
    elif p_value < 0.01:
        text = '**'
    elif p_value < 0.05:
        text = '*'
    else:
        text = 'n.s.'

    # Draw bracket
    ax.plot([x1, x1, x2, x2], [y, y + height, y + height, y],
            color='black', linewidth=1.0)
    ax.text((x1 + x2) / 2, y + height, text,
            ha='center', va='bottom', fontsize=10)


def save_figure(
    fig: plt.Figure,
    path: str,
    formats: Tuple[str, ...] = ('png', 'pdf'),
):
    """
    Save figure in multiple formats.

    Parameters
    ----------
    fig : plt.Figure
        Figure to save.
    path : str
        Base path without extension.
    formats : tuple
        Output formats.
    """
    from pathlib import Path
    path = Path(path)

    for fmt in formats:
        fig.savefig(path.with_suffix(f'.{fmt}'))


# Apply publication style on import
set_publication_style()
