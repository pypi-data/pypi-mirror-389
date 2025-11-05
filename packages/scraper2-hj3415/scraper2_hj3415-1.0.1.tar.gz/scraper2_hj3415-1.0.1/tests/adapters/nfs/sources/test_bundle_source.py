# tests/adapters/nfs/sources/test_bundle_source.py
from __future__ import annotations

import asyncio
import pandas as pd
import pytest

import scraper2_hj3415.adapters.nfs.sources.bundle_source as mod
from scraper2_hj3415.adapters.nfs.sources.bundle_source import NfsBundleSource
from scraper2_hj3415.core.types import NormalizedBundle


class FakeSession:
    def __init__(self):
        self.browser = object()


def make_bundle(n_fact=2, n_dim_acc=1, n_dim_period=1, n_delta=0) -> NormalizedBundle:
    fact = pd.DataFrame({"x": list(range(n_fact))})
    dim_account = pd.DataFrame({"accode": [f"A{i}" for i in range(n_dim_acc)]})
    dim_period = pd.DataFrame({"period": pd.date_range("2024-01-01", periods=n_dim_period, freq="MS")})
    delta = pd.DataFrame({"d": list(range(n_delta))})
    return NormalizedBundle(fact=fact, dim_account=dim_account, dim_period=dim_period, delta=delta)


@pytest.mark.asyncio
async def test_init_stores_session_and_browser():
    sess = FakeSession()
    src = NfsBundleSource(sess)
    assert src.session is sess
    assert src.browser is sess.browser


@pytest.mark.asyncio
async def test_list_bundles_c103_calls_list_c103_bundles(monkeypatch):
    # 준비: 반환할 번들과 호출 기록 저장소
    bundles = [make_bundle(2), make_bundle(3)]
    called = {"args": None, "kwargs": None, "times": 0}

    async def fake_list_c103_bundles(cmp_cd: str, *, browser, concurrency: int):
        called["args"] = (cmp_cd,)
        called["kwargs"] = {"browser": browser, "concurrency": concurrency}
        called["times"] += 1
        # asyncio.sleep(0)로 비동기 문맥 보장
        return await asyncio.sleep(0, result=bundles)

    # monkeypatch
    monkeypatch.setattr(mod, "list_c103_bundles", fake_list_c103_bundles)

    sess = FakeSession()
    src = NfsBundleSource(sess)

    res = await src.list_bundles("005930", page="c103", concurrency=5)

    # 호출 검증
    assert called["times"] == 1
    assert called["args"] == ("005930",)
    assert called["kwargs"]["browser"] is sess.browser
    assert called["kwargs"]["concurrency"] == 5

    # 반환 검증
    assert res is bundles
    assert all(isinstance(b.fact, pd.DataFrame) for b in res)


@pytest.mark.asyncio
async def test_list_bundles_c104_calls_list_c104_bundles(monkeypatch):
    bundles = [make_bundle(1), make_bundle(1, n_delta=1)]
    called = {"args": None, "kwargs": None, "times": 0}

    async def fake_list_c104_bundles(cmp_cd: str, *, browser, concurrency: int):
        called["args"] = (cmp_cd,)
        called["kwargs"] = {"browser": browser, "concurrency": concurrency}
        called["times"] += 1
        return await asyncio.sleep(0, result=bundles)

    monkeypatch.setattr(mod, "list_c104_bundles", fake_list_c104_bundles)

    sess = FakeSession()
    src = NfsBundleSource(sess)

    res = await src.list_bundles("000660", page="c104", concurrency=7)

    assert called["times"] == 1
    assert called["args"] == ("000660",)
    assert called["kwargs"]["browser"] is sess.browser
    assert called["kwargs"]["concurrency"] == 7

    assert res is bundles
    assert all(isinstance(b.dim_period, pd.DataFrame) for b in res)