# coding: utf-8
"""
Utilities to load the embedded sample dataset.
Works on Python 3.6 using pkgutil.get_data (no importlib.resources).
"""

import io
import pkgutil
import numpy as np
import pandas as pd


def load_sample_dataframe() -> pd.DataFrame:
    """
    Return the embedded sample.csv as a DataFrame.
    """
    raw = pkgutil.get_data("missalpha", "data/sample.csv")
    if raw is None:
        raise FileNotFoundError("Embedded sample.csv not found inside the package.")
    return pd.read_csv(io.BytesIO(raw))


def load_sample_matrix(dtype=float) -> np.ndarray:
    """
    Return the embedded sample.csv as a numpy array (NaN preserved).
    """
    df = load_sample_dataframe()
    return df.to_numpy(dtype=dtype)
