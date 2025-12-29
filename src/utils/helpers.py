"""
Helper Utilities
================

Common I/O and data processing utilities for the CENTAUR pipeline.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Parameters
    ----------
    path : str or Path
        Directory path.

    Returns
    -------
    Path
        The directory path.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_parquet(path: Union[str, Path]) -> pd.DataFrame:
    """
    Load a parquet file.

    Parameters
    ----------
    path : str or Path
        Path to parquet file.

    Returns
    -------
    pd.DataFrame
        Loaded DataFrame.
    """
    return pd.read_parquet(path, engine='fastparquet')


def save_parquet(
    df: pd.DataFrame,
    path: Union[str, Path],
    compression: str = 'snappy',
) -> Path:
    """
    Save a DataFrame to parquet format.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to save.
    path : str or Path
        Output path.
    compression : str
        Compression algorithm.

    Returns
    -------
    Path
        The saved file path.
    """
    path = Path(path)
    ensure_dir(path.parent)
    # Use fastparquet engine for better compatibility with object columns
    df.to_parquet(path, compression=compression, index=False, engine='fastparquet')
    return path


def load_csv(
    path: Union[str, Path],
    **kwargs,
) -> pd.DataFrame:
    """
    Load a CSV file with common defaults.

    Parameters
    ----------
    path : str or Path
        Path to CSV file.
    **kwargs
        Additional arguments for pd.read_csv.

    Returns
    -------
    pd.DataFrame
        Loaded DataFrame.
    """
    return pd.read_csv(path, **kwargs)


def save_csv(
    df: pd.DataFrame,
    path: Union[str, Path],
    index: bool = False,
    **kwargs,
) -> Path:
    """
    Save a DataFrame to CSV format.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to save.
    path : str or Path
        Output path.
    index : bool
        Whether to include index.
    **kwargs
        Additional arguments for df.to_csv.

    Returns
    -------
    Path
        The saved file path.
    """
    path = Path(path)
    ensure_dir(path.parent)
    df.to_csv(path, index=index, **kwargs)
    return path


def get_timestamp() -> str:
    """
    Get current timestamp string for file naming.

    Returns
    -------
    str
        Timestamp in format YYYYMMDD_HHMMSS.
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def format_r2(r2: float, std: Optional[float] = None) -> str:
    """
    Format R² value for display.

    Parameters
    ----------
    r2 : float
        R² score.
    std : float, optional
        Standard deviation.

    Returns
    -------
    str
        Formatted string.
    """
    if std is not None:
        return f"{r2:.3f} ± {std:.3f}"
    return f"{r2:.3f}"


def format_pvalue(p: float) -> str:
    """
    Format p-value with significance stars.

    Parameters
    ----------
    p : float
        P-value.

    Returns
    -------
    str
        Formatted p-value with stars.
    """
    if p < 0.001:
        return f"{p:.4f}***"
    elif p < 0.01:
        return f"{p:.4f}**"
    elif p < 0.05:
        return f"{p:.4f}*"
    else:
        return f"{p:.4f}"


def validate_required_columns(
    df: pd.DataFrame,
    required: List[str],
    source: str = "DataFrame",
) -> bool:
    """
    Validate that required columns exist in a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to validate.
    required : list
        Required column names.
    source : str
        Source name for error messages.

    Returns
    -------
    bool
        True if all columns present.

    Raises
    ------
    ValueError
        If any required columns are missing.
    """
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {source}: {missing}")
    return True


def calculate_summary_stats(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Calculate summary statistics for numeric columns.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    columns : list, optional
        Columns to summarize. If None, uses all numeric columns.

    Returns
    -------
    pd.DataFrame
        Summary statistics.
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()

    stats = []
    for col in columns:
        col_stats = {
            'column': col,
            'count': df[col].count(),
            'mean': df[col].mean(),
            'std': df[col].std(),
            'min': df[col].min(),
            'p25': df[col].quantile(0.25),
            'median': df[col].median(),
            'p75': df[col].quantile(0.75),
            'max': df[col].max(),
            'missing': df[col].isna().sum(),
            'missing_pct': df[col].isna().mean() * 100,
        }
        stats.append(col_stats)

    return pd.DataFrame(stats)
