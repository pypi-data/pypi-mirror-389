import pytest
import httpx
from types import SimpleNamespace
from scraper2_hj3415.adapters.nfs.sources import c1034_fetch as fetch_mod
from scraper2_hj3415.core import constants as C


# -------------------------------------------------------------------
# 공용 픽스처: 더미 세션 정보
# -------------------------------------------------------------------
@pytest.fixture
def fake_session_info():
    return {
        "encparam": "ENC123",
        "cookies": "a=1; b=2",
        "referer": "https://example.com",
        "user_agent": "pytest-agent",
    }


# -------------------------------------------------------------------
# 1️⃣ fetch_financial_json - 정상 JSON 응답
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_fetch_financial_json_success(monkeypatch):
    payload = {"DATA": [{"ACCODE": "1000", "ACC_NM": "매출액"}]}

    async def fake_get(url, params=None, headers=None):
        # httpx.Response 모방 객체
        return SimpleNamespace(
            json=lambda: payload,
            text="",
            headers={"Content-Type": "application/json"},
            raise_for_status=lambda: None,
            request=SimpleNamespace(),
        )

    class FakeAsyncClient:
        def __init__(self):
            self.get = fake_get
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(fetch_mod, "create_http_client", lambda **_: FakeAsyncClient())

    result = await fetch_mod.fetch_financial_json(
        cmp_cd="005930",
        aspx_inner=C.ASPXInner.c103,
        rpt=C.C103RPT.손익계산서,
        frq=C.FRQ.Y,
        encparam="ENC123",
        cookies="a=1",
        referer="https://example.com",
        user_agent="pytest-agent",
    )

    assert "DATA" in result
    assert result["DATA"][0]["ACCODE"] == "1000"


# -------------------------------------------------------------------
# 2️⃣ fetch_financial_json - JSON 문자열 응답 (text.startswith("{"))
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_fetch_financial_json_text_json(monkeypatch):
    text_json = '{"DATA": [{"ACCODE": "2000"}]}'

    async def fake_get(url, params=None, headers=None):
        return SimpleNamespace(
            json=lambda: (_ for _ in ()).throw(ValueError("not json")),
            text=text_json,
            headers={"Content-Type": "text/plain"},
            raise_for_status=lambda: None,
            request=SimpleNamespace(),
        )

    class FakeAsyncClient:
        def __init__(self):
            self.get = fake_get

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(fetch_mod, "create_http_client", lambda **_: FakeAsyncClient())

    result = await fetch_mod.fetch_financial_json(
        cmp_cd="005930",
        aspx_inner=C.ASPXInner.c104,
        rpt=C.C104RPT.수익성,
        frq=C.FRQ.Y,
        encparam="ENC123",
        cookies="a=1",
        referer="https://example.com",
        user_agent="pytest-agent",
    )

    assert result["DATA"][0]["ACCODE"] == "2000"

# -------------------------------------------------------------------
# 3️⃣ fetch_financial_json - HTML 응답 시 예외 발생
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_fetch_financial_json_html_raises(monkeypatch):
    async def fake_get(url, params=None, headers=None):
        return SimpleNamespace(
            json=lambda: (_ for _ in ()).throw(ValueError("not json")),
            text="<html><body>Error</body></html>",
            headers={"Content-Type": "text/html"},
            raise_for_status=lambda: None,
            request=SimpleNamespace(),
            response=SimpleNamespace(),
        )

    class FakeAsyncClient:
        def __init__(self):
            self.get = fake_get
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(fetch_mod, "create_http_client", lambda **_: FakeAsyncClient())

    with pytest.raises(httpx.HTTPStatusError):
        await fetch_mod.fetch_financial_json(
            cmp_cd="005930",
            aspx_inner=C.ASPXInner.c103,
            rpt=C.C103RPT.손익계산서,
            frq=C.FRQ.Y,
            encparam="ENC123",
            cookies="a=1",
            referer="https://example.com",
            user_agent="pytest-agent",
        )


# -------------------------------------------------------------------
# 4️⃣ fetch_financial_json - encparam 누락
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_fetch_financial_json_missing_encparam_raises():
    with pytest.raises(ValueError):
        await fetch_mod.fetch_financial_json(
            cmp_cd="005930",
            aspx_inner=C.ASPXInner.c103,
            rpt=C.C103RPT.손익계산서,
            frq=C.FRQ.Y,
            encparam="",  # ❌ 누락
            cookies="a=1",
            referer="https://example.com",
            user_agent="pytest-agent",
        )


# -------------------------------------------------------------------
# 5️⃣ get_c103_data / get_c104_data - session_info 전달 검증
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_c103_and_c104_data(monkeypatch, fake_session_info):
    called = {}

    async def fake_fetch_financial_json(**kwargs):
        called.update(kwargs)
        return {"DATA": [{"ACCODE": "3000"}]}

    monkeypatch.setattr(fetch_mod, "fetch_financial_json", fake_fetch_financial_json)

    # c103
    res1 = await fetch_mod.get_c103_data(session_info=fake_session_info, cmp_cd="005930")
    assert res1["DATA"][0]["ACCODE"] == "3000"
    assert called["encparam"] == "ENC123"
    assert called["cookies"] == "a=1; b=2"

    # c104
    res2 = await fetch_mod.get_c104_data(session_info=fake_session_info, cmp_cd="005930")
    assert res2["DATA"][0]["ACCODE"] == "3000"
    assert called["referer"] == "https://example.com"