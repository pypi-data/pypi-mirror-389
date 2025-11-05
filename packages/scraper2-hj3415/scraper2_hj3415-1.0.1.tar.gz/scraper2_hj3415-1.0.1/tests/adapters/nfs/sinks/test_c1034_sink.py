# tests/adapters/nfs/sinks/test_c1034_sink.py
from __future__ import annotations

import pandas as pd
import pytest
from typing import Iterable, Any

import scraper2_hj3415.adapters.nfs.sinks.c1034_sink as mod
from scraper2_hj3415.adapters.nfs.sinks.c1034_sink import C1034Sink


class RecordingRepo:
    """C1034RepositoryPort 대역: upsert 호출을 기록."""
    def __init__(self) -> None:
        self.calls = {
            "dim_account": [],
            "dim_period": [],
            "fact": [],
            "delta": [],
        }

    async def upsert_dim_account(self, rows: Iterable[Any]) -> None:
        self.calls["dim_account"].append(list(rows))

    async def upsert_dim_period(self, rows: Iterable[Any]) -> None:
        self.calls["dim_period"].append(list(rows))

    async def upsert_fact_finance(self, rows: Iterable[Any]) -> None:
        self.calls["fact"].append(list(rows))

    async def upsert_delta_finance(self, rows: Iterable[Any]) -> None:
        self.calls["delta"].append(list(rows))


@pytest.fixture
def dfs():
    # 각 DF는 동일한 형태로 7행을 만들어 청크 분할(예: 3,3,1)을 확인
    base = pd.DataFrame({"i": list(range(7))})
    return {
        "dim_account_df": base.copy(),
        "dim_period_df": base.copy(),
        "fact_df": base.copy(),
        "delta_df": base.copy(),
    }


def _mk_mapper(return_key: str):
    """DataFrame → DTO 리스트로 변환하는 간단한 더블 매퍼."""
    def _map(df: pd.DataFrame):
        return [{return_key: int(v)} for v in df["i"].tolist()]
    return _map


@pytest.mark.asyncio
async def test_save_all_batches_per_mapper(monkeypatch, dfs):
    """
    - 매퍼가 반환한 리스트가 chunk 크기대로 잘려 Repo에 전달되는지
    - 7개 입력, chunk=3 → [3,3,1] 형태로 각 upsert가 호출되어야 함
    """
    # 매퍼 함수들을 모듈 네임스페이스에 패치
    monkeypatch.setattr(mod, "rows_to_dim_account", _mk_mapper("acc"))
    monkeypatch.setattr(mod, "rows_to_dim_period", _mk_mapper("per"))
    monkeypatch.setattr(mod, "rows_to_fact_finance", _mk_mapper("fact"))
    monkeypatch.setattr(mod, "rows_to_delta_finance", _mk_mapper("del"))

    repo = RecordingRepo()
    sink = C1034Sink(repo, chunk=3)

    await sink.save_all(
        dim_account_df=dfs["dim_account_df"],
        dim_period_df=dfs["dim_period_df"],
        fact_df=dfs["fact_df"],
        delta_df=dfs["delta_df"],
    )

    # 각 종류별로 3회 호출(3,3,1)
    for kind in ["dim_account", "dim_period", "fact", "delta"]:
        assert len(repo.calls[kind]) == 3
        sizes = [len(batch) for batch in repo.calls[kind]]
        assert sizes == [3, 3, 1]

        # 내용도 일관적인지 간단 점검 (첫 배치 첫 원소 키 존재)
        first_elem = repo.calls[kind][0][0]
        assert isinstance(first_elem, dict)
        assert len(first_elem) == 1  # {"acc":0} 같은 구조
        assert list(first_elem.keys())[0] in {"acc", "per", "fact", "del"}


@pytest.mark.asyncio
async def test_save_individual_methods(monkeypatch):
    """
    개별 save_* 메서드도 동일하게 청크 호출됨을 확인.
    """
    monkeypatch.setattr(mod, "rows_to_dim_account", _mk_mapper("acc"))
    monkeypatch.setattr(mod, "rows_to_dim_period", _mk_mapper("per"))
    monkeypatch.setattr(mod, "rows_to_fact_finance", _mk_mapper("fact"))
    monkeypatch.setattr(mod, "rows_to_delta_finance", _mk_mapper("del"))

    df = pd.DataFrame({"i": list(range(5))})  # 5개 → chunk=2 → [2,2,1]
    repo = RecordingRepo()
    sink = C1034Sink(repo, chunk=2)

    await sink.save_dim_account(df)
    await sink.save_dim_period(df)
    await sink.save_fact_finance(df)
    await sink.save_delta_finance(df)

    for kind in ["dim_account", "dim_period", "fact", "delta"]:
        sizes = [len(batch) for batch in repo.calls[kind]]
        assert sizes == [2, 2, 1]


@pytest.mark.asyncio
async def test_save_all_skips_none(monkeypatch):
    """
    None으로 들어온 DF는 해당 저장 로직을 건너뛴다.
    """
    monkeypatch.setattr(mod, "rows_to_dim_account", _mk_mapper("acc"))
    monkeypatch.setattr(mod, "rows_to_dim_period", _mk_mapper("per"))
    monkeypatch.setattr(mod, "rows_to_fact_finance", _mk_mapper("fact"))
    monkeypatch.setattr(mod, "rows_to_delta_finance", _mk_mapper("del"))

    repo = RecordingRepo()
    sink = C1034Sink(repo, chunk=10)

    df = pd.DataFrame({"i": list(range(4))})
    await sink.save_all(
        dim_account_df=None,     # ← skip
        dim_period_df=df,
        fact_df=None,            # ← skip
        delta_df=df,
    )

    # 호출된 것만 존재해야 함
    assert repo.calls["dim_account"] == []  # skip
    assert repo.calls["fact"] == []         # skip

    assert len(repo.calls["dim_period"]) == 1
    assert len(repo.calls["delta"]) == 1
    assert [len(repo.calls["dim_period"][0]), len(repo.calls["delta"][0])] == [4, 4]