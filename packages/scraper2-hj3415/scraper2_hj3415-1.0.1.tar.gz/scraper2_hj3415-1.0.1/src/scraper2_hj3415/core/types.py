# scraper2_hj3415/core/types.py

from dataclasses import dataclass
import pandas as pd

@dataclass(frozen=True)
class NormalizedBundle:
    fact: pd.DataFrame
    dim_account: pd.DataFrame
    dim_period: pd.DataFrame
    delta: pd.DataFrame