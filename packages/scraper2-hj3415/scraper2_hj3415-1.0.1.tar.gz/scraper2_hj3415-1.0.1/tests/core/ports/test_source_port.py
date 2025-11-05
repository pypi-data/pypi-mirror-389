# tests/core/ports/test_source_port.py
from __future__ import annotations

import pytest
import pandas as pd

import scraper2_hj3415.core.ports.source_port as mod
from scraper2_hj3415.core.ports.source_port import C1034BundleSourcePort
from scraper2_hj3415.core.types import NormalizedBundle


@pytest.mark.asyncio
async def test_fake_bundle_source_matches_protocol():
    """
    Protocol은 @runtime_checkable이 없기 때문에 isinstance 검증 대신
    실제로 list_bundles() 호출이 비동기로 동작하고,
    NormalizedBundle 리스트를 반환하는지만 확인합니다.
    """
    class FakeBundleSource(C1034BundleSourcePort):
        async def list_bundles(self, cmp_cd: str, page: str, *, concurrency: int = 2):
            # 단순히 더미 NormalizedBundle 객체를 반환
            bundle = NormalizedBundle(
                fact=pd.DataFrame({"v": [1]}),
                dim_account=pd.DataFrame({"a": ["A1"]}),
                dim_period=pd.DataFrame({"p": ["2024-01-01"]}),
                delta=pd.DataFrame({"d": [0.1]}),
            )
            return [bundle]

    src = FakeBundleSource()
    bundles = await src.list_bundles("005930", page="c103", concurrency=3)

    # 반환값 검증
    assert isinstance(bundles, list)
    assert len(bundles) == 1
    b = bundles[0]
    assert isinstance(b, NormalizedBundle)
    assert set(b.__dict__.keys()) == {"fact", "dim_account", "dim_period", "delta"}
    assert isinstance(b.fact, pd.DataFrame)
    assert isinstance(b.dim_account, pd.DataFrame)
    assert isinstance(b.dim_period, pd.DataFrame)
    assert isinstance(b.delta, pd.DataFrame)


def test_protocol_has_correct_signature():
    """
    Protocol의 list_bundles 시그니처가 예상대로 존재하는지 점검.
    (cmp_cd, page, *, concurrency)
    """
    sig = mod.C1034BundleSourcePort.list_bundles
    params = list(sig.__annotations__.keys())

    # 시그니처와 리턴타입 확인
    assert "cmp_cd" in params
    assert "page" in params
    assert "concurrency" in params
    assert "return" in params

    assert sig.__annotations__["return"].__origin__ is list  # -> List[NormalizedBundle]