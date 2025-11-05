# scraper2_hj3415/core/ports/sink_port.py

from typing import Protocol
import pandas as pd

class C1034SinkPort(Protocol):
    async def save_all(
        self,
        *,
        dim_account_df: pd.DataFrame,
        dim_period_df: pd.DataFrame,
        fact_df: pd.DataFrame,
        delta_df: pd.DataFrame,
    ) -> None: ...


