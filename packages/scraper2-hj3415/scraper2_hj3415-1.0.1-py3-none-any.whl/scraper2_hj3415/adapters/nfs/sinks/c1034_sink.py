# scraper2_hj3415/adapters/nfs/sinks/c1034_sink.py

import pandas as pd

from .df_to_dto_mappers import (
    rows_to_dim_account, rows_to_dim_period,
    rows_to_fact_finance, rows_to_delta_finance,
)
from scraper2_hj3415.adapters._shared.utils import chunked
from scraper2_hj3415.core.ports.sink_port import C1034SinkPort
from contracts_hj3415.ports.c1034_write_repo import C1034WriteRepoPort

DEFAULT_CHUNK = 1_000

class C1034Sink(C1034SinkPort):
    def __init__(self, repo: C1034WriteRepoPort, chunk: int = DEFAULT_CHUNK):
        self.repo = repo
        self.chunk = chunk

    async def save_dim_account(self, df: pd.DataFrame) -> None:
        for batch in chunked(rows_to_dim_account(df), self.chunk):
            await self.repo.upsert_dim_account(batch)

    async def save_dim_period(self, df: pd.DataFrame) -> None:
        for batch in chunked(rows_to_dim_period(df), self.chunk):
            await self.repo.upsert_dim_period(batch)

    async def save_fact_finance(self, df: pd.DataFrame) -> None:
        for batch in chunked(rows_to_fact_finance(df), self.chunk):
            await self.repo.upsert_fact_finance(batch)

    async def save_delta_finance(self, df: pd.DataFrame) -> None:
        for batch in chunked(rows_to_delta_finance(df), self.chunk):
            await self.repo.upsert_delta_finance(batch)

    async def save_all(
        self,
        *,
        dim_account_df: pd.DataFrame,
        dim_period_df: pd.DataFrame,
        fact_df: pd.DataFrame,
        delta_df: pd.DataFrame,
    ) -> None:
        if dim_account_df is not None:
            await self.save_dim_account(dim_account_df)
        if dim_period_df is not None:
            await self.save_dim_period(dim_period_df)
        if fact_df is not None:
            await self.save_fact_finance(fact_df)
        if delta_df is not None:
            await self.save_delta_finance(delta_df)