"""Download and process ACS 5-year estimates for Nebraska ZCTAs.

This module fetches socioeconomic data from the Census Bureau's American
Community Survey (ACS) 5-year estimates at the ZCTA level.

Variables included:
- Median household income
- % with bachelor's degree or higher
- % age 65+
- % owner-occupied housing
- Total population
"""

import pandas as pd
import numpy as np
from pathlib import Path
import requests
from typing import Optional

# ACS 5-year estimates API endpoint (no key required for basic access)
ACS_BASE_URL = "https://api.census.gov/data/2021/acs/acs5"

# Nebraska FIPS code
NEBRASKA_FIPS = "31"

# Variables to fetch
ACS_VARIABLES = {
    # Median household income
    'B19013_001E': 'median_household_income',
    # Total population
    'B01003_001E': 'total_population',
    # Population 65 years and over (need to sum multiple age groups)
    'B01001_020E': 'male_65_66',
    'B01001_021E': 'male_67_69',
    'B01001_022E': 'male_70_74',
    'B01001_023E': 'male_75_79',
    'B01001_024E': 'male_80_84',
    'B01001_025E': 'male_85_plus',
    'B01001_044E': 'female_65_66',
    'B01001_045E': 'female_67_69',
    'B01001_046E': 'female_70_74',
    'B01001_047E': 'female_75_79',
    'B01001_048E': 'female_80_84',
    'B01001_049E': 'female_85_plus',
    # Education - population 25+ by educational attainment
    'B15003_001E': 'edu_total_25_plus',
    'B15003_022E': 'edu_bachelors',
    'B15003_023E': 'edu_masters',
    'B15003_024E': 'edu_professional',
    'B15003_025E': 'edu_doctorate',
    # Housing tenure
    'B25003_001E': 'housing_total',
    'B25003_002E': 'housing_owner_occupied',
}


def fetch_acs_data(
    year: int = 2021,
    cache_path: Optional[Path] = None,
    manual_data_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Fetch ACS 5-year estimates for Nebraska ZCTAs.

    Parameters
    ----------
    year : int
        ACS 5-year estimates ending year (default 2021).
    cache_path : Path, optional
        Path to cache the raw API response.
    manual_data_path : Path, optional
        Path to manually downloaded ACS data CSV.

    Returns
    -------
    pd.DataFrame
        DataFrame with ZCTA-level ACS variables.

    Notes
    -----
    To manually download ACS data:
    1. Go to https://data.census.gov/
    2. Search for "ACS 5-Year Estimates" for Nebraska
    3. Select ZCTA geography
    4. Download tables: B19013 (income), B01001 (age), B15003 (education), B25003 (housing)
    5. Save as CSV to data_raw/acs/acs_nebraska_zcta.csv
    """
    # Check for manually downloaded data first
    if manual_data_path and manual_data_path.exists():
        print(f"   Loading manually downloaded ACS data from {manual_data_path}")
        return pd.read_csv(manual_data_path)

    # Check cache
    if cache_path and cache_path.exists():
        print(f"   Loading cached ACS data from {cache_path}")
        return pd.read_csv(cache_path)

    # Try API (requires key for ZCTA queries)
    variables = ','.join(ACS_VARIABLES.keys())
    url = f"{ACS_BASE_URL}?get=NAME,{variables}&for=zip%20code%20tabulation%20area:*&in=state:{NEBRASKA_FIPS}"

    print(f"   Attempting to fetch ACS {year} 5-year estimates for Nebraska ZCTAs...")

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"   Note: Census API requires key for ZCTA queries: {e}")
        print("   To add ACS baseline:")
        print("   1. Download ACS data from https://data.census.gov/")
        print("   2. Save to data_raw/acs/acs_nebraska_zcta.csv")
        print("   3. Re-run pipeline")
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])

    # Rename columns
    df = df.rename(columns=ACS_VARIABLES)
    df = df.rename(columns={
        'zip code tabulation area': 'zip',
        'state': 'state_fips',
    })

    # Convert numeric columns
    numeric_cols = list(ACS_VARIABLES.values())
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Cache if path provided
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache_path, index=False)
        print(f"   Cached ACS data to {cache_path}")

    return df


def compute_acs_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute derived ACS features from raw variables.

    Parameters
    ----------
    df : pd.DataFrame
        Raw ACS data from fetch_acs_data().

    Returns
    -------
    pd.DataFrame
        DataFrame with computed ACS features.
    """
    result = pd.DataFrame()
    result['zip'] = df['zip']

    # Median household income (already in raw form)
    result['acs_median_income'] = df['median_household_income']

    # Total population
    result['acs_population'] = df['total_population']

    # % age 65+
    age_65_plus_cols = [
        'male_65_66', 'male_67_69', 'male_70_74', 'male_75_79',
        'male_80_84', 'male_85_plus', 'female_65_66', 'female_67_69',
        'female_70_74', 'female_75_79', 'female_80_84', 'female_85_plus',
    ]
    pop_65_plus = df[age_65_plus_cols].sum(axis=1)
    result['acs_pct_65_plus'] = (pop_65_plus / df['total_population'] * 100).replace([np.inf, -np.inf], np.nan)

    # % with bachelor's degree or higher
    edu_bachelors_plus = (
        df['edu_bachelors'] + df['edu_masters'] +
        df['edu_professional'] + df['edu_doctorate']
    )
    result['acs_pct_bachelors_plus'] = (edu_bachelors_plus / df['edu_total_25_plus'] * 100).replace([np.inf, -np.inf], np.nan)

    # % owner-occupied housing
    result['acs_pct_owner_occupied'] = (df['housing_owner_occupied'] / df['housing_total'] * 100).replace([np.inf, -np.inf], np.nan)

    # Log population density (requires area, which we'll compute from coordinates later)
    # For now, just use log population as a proxy
    result['acs_log_population'] = np.log1p(df['total_population'])

    return result


def get_acs_features(
    year: int = 2021,
    cache_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Get ACS features ready for modeling.

    Parameters
    ----------
    year : int
        ACS 5-year estimates ending year.
    cache_dir : Path, optional
        Directory to cache data.

    Returns
    -------
    pd.DataFrame
        DataFrame with computed ACS features, indexed by ZIP.
    """
    cache_path = cache_dir / f"acs_{year}_nebraska_zcta_raw.csv" if cache_dir else None

    raw_df = fetch_acs_data(year=year, cache_path=cache_path)

    if raw_df.empty:
        return pd.DataFrame()

    features_df = compute_acs_features(raw_df)

    print(f"   Computed ACS features for {len(features_df)} ZCTAs")
    print(f"   Features: {[c for c in features_df.columns if c.startswith('acs_')]}")

    return features_df


# ACS feature names for use in model specifications
ACS_FEATURE_NAMES = [
    'acs_median_income',
    'acs_pct_65_plus',
    'acs_pct_bachelors_plus',
    'acs_pct_owner_occupied',
    'acs_log_population',
]


if __name__ == "__main__":
    # Test fetching ACS data
    from pathlib import Path
    cache_dir = Path("data_raw/acs")
    df = get_acs_features(cache_dir=cache_dir)
    print(df.head())
    print(df.describe())
