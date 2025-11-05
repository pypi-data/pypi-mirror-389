# tests/core/usecases/test_c1034_ingest.py
from __future__ import annotations

import asyncio
import pandas as pd
import pytest

from scraper2_hj3415.core.usecases.c1034_ingest import C1034IngestUseCase, IngestStats
from scraper2_hj3415.core.types import NormalizedBundle


def make_bundle(n_fact=2, n_dim_acc=1, n_dim_period=1, n_delta=0) -> NormalizedBundle:
    fact = pd.DataFrame({"x": list(range(n_fact))})
    dim_account = pd.DataFrame({"accode": [f"A{i}" for i in range(n_dim_acc)]})
    dim_period = pd.DataFrame({"period": pd.date_range("2024-01-01", periods=n_dim_period, freq="MS")})
    delta = pd.DataFrame({"d": list(range(n_delta))})
    return NormalizedBundle(fact=fact, dim_account=dim_account, dim_period=dim_period, delta=delta)


class FakeSource:
    """C1034BundleSourcePort 대역: list_bundles만 제공."""
    def __init__(self, bundles_by_page: dict[str, list[NormalizedBundle]]):
        self.bundles_by_page = bundles_by_page
        self.calls: list[tuple[str, str, int]] = []  # (cmp_cd, page, concurrency)

    async def list_bundles(self, cmp_cd: str, page: str, *, concurrency: int = 2):
        self.calls.append((cmp_cd, page, concurrency))
        # asyncio 문맥 보장
        return await asyncio.sleep(0, result=list(self.bundles_by_page.get(page, [])))


class RecordingSink:
    """C1034SinkPort 대역: save_all 호출 기록 및 간단 검증."""
    def __init__(self):
        self.calls: list[dict[str, pd.DataFrame]] = []

    async def save_all(
        self,
        *,
        dim_account_df: pd.DataFrame,
        dim_period_df: pd.DataFrame,
        fact_df: pd.DataFrame,
        delta_df: pd.DataFrame,
    ) -> None:
        self.calls.append(
            {
                "dim_account_df": dim_account_df,
                "dim_period_df": dim_period_df,
                "fact_df": fact_df,
                "delta_df": delta_df,
            }
        )


@pytest.mark.asyncio
async def test_ingest_c103_save_mode_returns_stats_and_calls_sink():
    # 준비: c103에서 번들 2개 반환 → 각 번들의 row 수 기반으로 합산 검증
    bundles_c103 = [make_bundle(3, 2, 2, 1), make_bundle(1, 1, 1, 0)]
    source = FakeSource({"c103": bundles_c103})
    sink = RecordingSink()

    uc = C1034IngestUseCase(source=source, sink=sink)

    stats = await uc.ingest_c103("005930", save=True, collect_only=False)
    assert isinstance(stats, IngestStats)

    # 저장 호출 횟수 = 번들 수(2)
    assert len(sink.calls) == 2

    # 기대 통계: 번들별 row 수 합산
    exp_dim_acc = sum(len(b.dim_account) for b in bundles_c103)
    exp_dim_period = sum(len(b.dim_period) for b in bundles_c103)
    exp_fact = sum(len(b.fact) for b in bundles_c103)
    exp_delta = sum(len(b.delta) for b in bundles_c103)
    assert stats.dim_account_rows == exp_dim_acc
    assert stats.dim_period_rows == exp_dim_period
    assert stats.fact_rows == exp_fact
    assert stats.delta_rows == exp_delta

    # source 호출 검증
    assert source.calls == [("005930", "c103", 2)]


@pytest.mark.asyncio
async def test_ingest_c104_collect_only_returns_bundles_and_calls_on_bundle():
    bundles_c104 = [make_bundle(2), make_bundle(4)]
    source = FakeSource({"c104": bundles_c104})
    sink = RecordingSink()
    called = []

    async def on_bundle(page_label: str, bundle: NormalizedBundle):
        called.append((page_label, len(bundle.fact)))

    uc = C1034IngestUseCase(source=source, sink=sink, on_bundle=on_bundle)

    res = await uc.ingest_c104("000660", save=False, collect_only=True)
    # 번들 그대로 반환
    assert isinstance(res, list)
    assert res is not bundles_c104  # 복사일 수도 있지만 내용은 동일해야 함
    assert len(res) == len(bundles_c104)
    assert all(isinstance(b.fact, pd.DataFrame) for b in res)

    # 저장 안 했으므로 sink 호출 없음
    assert len(sink.calls) == 0

    # 훅 호출 검증
    assert called == [("c104", 2), ("c104", 4)]

    # source 호출 검증
    assert source.calls == [("000660", "c104", 2)]


@pytest.mark.asyncio
async def test_ingest_all_mixes_pages_returns_stats_when_save_true():
    bundles_c103 = [make_bundle(2, 1, 1, 0)]
    bundles_c104 = [make_bundle(1, 2, 1, 1), make_bundle(3, 1, 2, 0)]
    source = FakeSource({"c103": bundles_c103, "c104": bundles_c104})
    sink = RecordingSink()

    uc = C1034IngestUseCase(source=source, sink=sink)

    stats = await uc.ingest_all("373220", pages=("c103", "c104"), save=True, collect_only=False)
    assert isinstance(stats, IngestStats)

    # sink는 총 3번(= 모든 번들 개수) 호출
    assert len(sink.calls) == 1 + 2

    exp_dim_acc = sum(len(b.dim_account) for b in (bundles_c103 + bundles_c104))
    exp_dim_period = sum(len(b.dim_period) for b in (bundles_c103 + bundles_c104))
    exp_fact = sum(len(b.fact) for b in (bundles_c103 + bundles_c104))
    exp_delta = sum(len(b.delta) for b in (bundles_c103 + bundles_c104))
    assert stats.dim_account_rows == exp_dim_acc
    assert stats.dim_period_rows == exp_dim_period
    assert stats.fact_rows == exp_fact
    assert stats.delta_rows == exp_delta

    # c103, c104 순서로 source 호출
    assert source.calls == [("373220", "c103", 2), ("373220", "c104", 2)]


@pytest.mark.asyncio
async def test_ingest_all_collect_only_returns_merged_bundles():
    bundles_c103 = [make_bundle(1)]
    bundles_c104 = [make_bundle(2)]
    source = FakeSource({"c103": bundles_c103, "c104": bundles_c104})
    sink = RecordingSink()

    uc = C1034IngestUseCase(source=source, sink=sink)

    res = await uc.ingest_all("005380", pages=("c103", "c104"), save=False, collect_only=True)
    # 수집 전용: 리스트로 합쳐 반환
    assert isinstance(res, list)
    assert len(res) == len(bundles_c103) + len(bundles_c104)
    assert len(sink.calls) == 0  # 저장 없음


@pytest.mark.asyncio
async def test_ingest_many_aggregates_stats_for_multiple_codes():
    # 코드별로 번들 크기를 달리하여 합산 검증
    src_map = {
        # code1
        "c103": [make_bundle(2, 1, 1, 0)],
        "c104": [make_bundle(1, 1, 1, 1)],
    }
    # FakeSource는 page별로만 데이터를 가지므로 인스턴스 1개로 공유
    source = FakeSource(src_map)
    sink = RecordingSink()

    uc = C1034IngestUseCase(source=source, sink=sink)

    codes = ["005930", "000660", "373220"]
    stats = await uc.ingest_many(codes, pages=("c103", "c104"), concurrency=2, save=True, collect_only=False)
    assert isinstance(stats, IngestStats)

    # 코드가 3개이므로 동일한 번들 패턴이 3회 저장된다.
    per_code_dim_acc = sum(len(b.dim_account) for b in (src_map["c103"] + src_map["c104"]))
    per_code_dim_period = sum(len(b.dim_period) for b in (src_map["c103"] + src_map["c104"]))
    per_code_fact = sum(len(b.fact) for b in (src_map["c103"] + src_map["c104"]))
    per_code_delta = sum(len(b.delta) for b in (src_map["c103"] + src_map["c104"]))

    assert stats.dim_account_rows == per_code_dim_acc * len(codes)
    assert stats.dim_period_rows == per_code_dim_period * len(codes)
    assert stats.fact_rows == per_code_fact * len(codes)
    assert stats.delta_rows == per_code_delta * len(codes)

    # sink 호출 수 = (코드 개수) × (번들 수 per code)
    per_code_bundles = len(src_map["c103"]) + len(src_map["c104"])
    assert len(sink.calls) == per_code_bundles * len(codes)