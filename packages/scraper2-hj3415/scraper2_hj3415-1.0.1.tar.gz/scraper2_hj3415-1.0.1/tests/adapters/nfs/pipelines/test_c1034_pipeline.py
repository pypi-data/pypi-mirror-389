import pytest
import pandas as pd
from scraper2_hj3415.core import constants as C
from scraper2_hj3415.adapters.nfs.pipelines import c1034_pipeline as pipe_mod

# 모듈 내부 utils_mod / fetch 참조
import scraper2_hj3415.adapters.nfs.sources.c1034_fetch as fetch_mod
import scraper2_hj3415.adapters.nfs.sources.c1034_session as session_mod


# -------------------------------------------------
# 공통: 모킹용 Dummy NormalizedBundle 생성기
# -------------------------------------------------
class DummyBundle:
    """normalize_dispatch가 반환하는 더미 NormalizedBundle 흉내"""
    def __init__(self, page: str, rpt: str, frq: str):
        self.fact = pd.DataFrame([
            {"cmp_cd": "005930", "page": page, "rpt": rpt, "frq": frq, "value": 123},
        ])
        self.dim_period = pd.DataFrame([{"period": "2024-12-31", "frq": frq}])
        self.dim_account = pd.DataFrame([{"accode": "1000"}])
        self.delta = pd.DataFrame([{"accode": "1000", "qoq": 0.1}])


# -------------------------------------------------
# 픽스처: 세션 추출 / fetch 함수 모킹
# -------------------------------------------------
@pytest.fixture(autouse=True)
def mock_extract_session_info(monkeypatch):
    """extract_session_info가 항상 동일한 세션 정보를 반환하도록"""
    async def fake_extract_session_info(*, browser=None, cmp_cd=None, page=None):
        return {
            "encparam": "FAKE123",
            "cookies": "a=1; b=2",
            "referer": f"https://example.com/{page}",
            "user_agent": "pytest-agent",
        }
    monkeypatch.setattr(session_mod, "extract_session_info", fake_extract_session_info)


@pytest.fixture
def mock_get_data(monkeypatch):
    """HTTP 호출(fetch_financial_json)을 모킹"""
    async def fake_get_data(*, session_info, cmp_cd, rpt, frq):
        # 데이터 구조만 단순히 흉내
        return {"YYMM": ["2023/12", "2024/12"], "DATA": [{"ACCODE": "1000"}]}
    monkeypatch.setattr(fetch_mod, "get_c103_data", fake_get_data)
    monkeypatch.setattr(fetch_mod, "get_c104_data", fake_get_data)


@pytest.fixture(autouse=True)
def mock_normalize(monkeypatch):
    """normalize_dispatch 결과를 DummyBundle로 대체"""
    def fake_normalize(payload, meta):
        return DummyBundle(meta["page"].value if hasattr(meta["page"], "value") else meta["page"],
                           meta["rpt"].value if hasattr(meta["rpt"], "value") else meta["rpt"],
                           meta["frq"].value if hasattr(meta["frq"], "value") else meta["frq"])
    monkeypatch.setattr(pipe_mod, "normalize_dispatch", fake_normalize)


# -------------------------------------------------
# TEST 1: list_c103_bundles
# -------------------------------------------------
@pytest.mark.asyncio
async def test_list_c103_bundles_basic(mock_get_data):
    bundles = await pipe_mod.list_c103_bundles("005930", concurrency=2)
    # C103RPT * 2(FRQ)
    expected_cnt = len(list(C.C103RPT)) * 2
    assert len(bundles) == expected_cnt

    for b in bundles:
        assert isinstance(b.fact, pd.DataFrame)
        assert not b.fact.empty
        assert set(b.fact.columns) >= {"cmp_cd", "page", "rpt", "frq", "value"}
        assert isinstance(b.dim_period, pd.DataFrame)
        assert not b.dim_period.empty


# -------------------------------------------------
# TEST 2: list_c104_bundles
# -------------------------------------------------
@pytest.mark.asyncio
async def test_list_c104_bundles_basic(mock_get_data):
    bundles = await pipe_mod.list_c104_bundles("005930", concurrency=2)
    expected_cnt = len(list(C.C104RPT)) * 2
    assert len(bundles) == expected_cnt
    for b in bundles:
        assert isinstance(b.fact, pd.DataFrame)
        assert isinstance(b.dim_period, pd.DataFrame)
        assert not b.fact.empty
        assert not b.dim_period.empty


# -------------------------------------------------
# TEST 3: 에러 허용 (fetch에서 일부 예외)
# -------------------------------------------------
@pytest.mark.asyncio
async def test_partial_failure(monkeypatch):
    async def fake_get_data(*, session_info, cmp_cd, rpt, frq):
        if frq == C.FRQ.Q:
            raise ValueError("Network Error")
        return {"YYMM": ["2024/12"], "DATA": [{"ACCODE": "1000"}]}
    monkeypatch.setattr(fetch_mod, "get_c103_data", fake_get_data)

    bundles = await pipe_mod.list_c103_bundles("005930", concurrency=3)
    # 일부 실패는 skip되어야 하므로 전체보다 적음
    assert 0 < len(bundles) < len(list(C.C103RPT)) * 2