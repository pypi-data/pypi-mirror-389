# tests/core/ports/test_sink_port.py
from __future__ import annotations

import pandas as pd
import pytest

from scraper2_hj3415.core.ports.sink_port import C1034SinkPort

@pytest.mark.asyncio
async def test_sink_protocol_save_all_duck_typing():
    """
    Protocol은 런타임 강제가 없으므로 duck-typing으로 동작 검증.
    save_all이 async로 호출되고 인자가 그대로 전달되는지만 확인.
    """
    recorded: dict[str, pd.DataFrame | None] = {}

    class FakeSink(C1034SinkPort):  # 타입 힌트만: 런타임엔 Protocol 체크 없음
        async def save_all(
            self,
            *,
            dim_account_df: pd.DataFrame,
            dim_period_df: pd.DataFrame,
            fact_df: pd.DataFrame,
            delta_df: pd.DataFrame,
        ) -> None:
            recorded["dim_account_df"] = dim_account_df
            recorded["dim_period_df"] = dim_period_df
            recorded["fact_df"] = fact_df
            recorded["delta_df"] = delta_df

    sink = FakeSink()

    da = pd.DataFrame({"i": [1, 2]})
    dp = pd.DataFrame({"p": ["2024-01-01"]})
    fact = pd.DataFrame({"v": [10.0, 20.0, 30.0]})
    delta = pd.DataFrame({"qoq": [0.1]})

    await sink.save_all(
        dim_account_df=da,
        dim_period_df=dp,
        fact_df=fact,
        delta_df=delta,
    )

    assert recorded["dim_account_df"] is da
    assert recorded["dim_period_df"] is dp
    assert recorded["fact_df"] is fact
    assert recorded["delta_df"] is delta