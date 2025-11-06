"""Core methods"""

import pandas as pd

from .config import consdata_root


def list_cons() -> list:
    """list constituent files"""
    root = consdata_root()
    return [p.stem for p in root.glob("*.parquet")]


def load_cons(name: str) -> pd.DataFrame:
    """load constituents dataframe"""
    root = consdata_root()
    file = root.joinpath(f"{name}.parquet")
    return pd.read_parquet(file.as_uri())


def save_cons(name: str, data: pd.DataFrame) -> pd.DataFrame:
    """save constituents dataframe"""
    root = consdata_root()
    file = root.joinpath(f"{name}.parquet")
    data.to_parquet(file.as_uri())


def get_symbols(name: str) -> list:
    """get list of symbols"""
    cons = load_cons(name)
    return cons.index.tolist()

