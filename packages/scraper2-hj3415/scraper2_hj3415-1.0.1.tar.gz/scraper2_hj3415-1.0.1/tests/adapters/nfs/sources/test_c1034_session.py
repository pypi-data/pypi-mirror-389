# tests/adapters/nfs/sources/test_c1034_session.py
from __future__ import annotations

import asyncio
import pytest

from scraper2_hj3415.core.constants import PAGE
# 모듈을 불러와서 내부 심볼(monkeypatch 대상)을 이 네임스페이스에서 교체합니다.
import scraper2_hj3415.adapters.nfs.sources.c1034_session as mod


# ─────────────────────────────────────────────
# Fakes (아주 작은 인터페이스만 흉내)
# ─────────────────────────────────────────────
class FakeRouteRequest:
    def __init__(self, resource_type: str = "script") -> None:
        self.resource_type = resource_type

class FakeRoute:
    def __init__(self, resource_type: str = "script") -> None:
        self.request = FakeRouteRequest(resource_type)

    async def abort(self):  # pragma: no cover (로직상 호출되지 않아도 OK)
        return None

    async def continue_(self):  # pragma: no cover
        return None

class FakePage:
    def __init__(self, html_with_encparam: bool = True) -> None:
        self._url = None
        self._ua = "FakeUA/1.0"
        self._html_with_encparam = html_with_encparam
        self.closed = False
        self.goto_calls = []

    async def goto(self, url: str, wait_until: str = "domcontentloaded"):
        self._url = url
        self.goto_calls.append((url, wait_until))

    async def wait_for_selector(self, selector: str, timeout: int = 3000):
        # encparam이 없도록 강제하고 싶으면 일부 테스트에서 예외를 던져
        # 폴백(wait_for_timeout) 분기를 태우도록 할 수도 있습니다.
        return None

    async def wait_for_timeout(self, ms: int):
        await asyncio.sleep(0)

    async def content(self) -> str:
        if self._html_with_encparam:
            return "<html><script>var encparam='ENC-12345';</script></html>"
        else:
            return "<html><body>No encparam here</body></html>"

    async def evaluate(self, js: str):
        if js == "navigator.userAgent":
            return self._ua
        return None

    async def close(self):
        self.closed = True

class FakeContext:
    def __init__(self, page: FakePage) -> None:
        self._page = page
        self.closed = False
        self.routes = []

    async def route(self, pattern: str, handler):
        # 호출만 기록. 필요하면 handler(FakeRoute())를 호출해도 됨.
        self.routes.append((pattern, handler))
        # 여기서는 handler를 바로 호출하지 않음 (리소스별 abort/continue 로직은 유닛테스트 관심사 아님)

    async def new_page(self) -> FakePage:
        return self._page

    async def cookies(self):
        return [{"name": "sid", "value": "abc"}, {"name": "lang", "value": "ko"}]

    async def close(self):
        self.closed = True

class FakeBrowser:
    def __init__(self, page: FakePage) -> None:
        self._page = page

    async def new_context(self) -> FakeContext:
        return FakeContext(self._page)


# ─────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_extract_session_info_with_external_browser(monkeypatch):
    """
    외부 browser를 주입했을 때:
    - browser_context(내부 컨텍스트 매니저)는 호출되지 않아야 함
    - encparam/UA/cookies/referer가 잘 추출되어야 함
    """
    # 내부 browser_context가 호출되면 테스트 실패하도록 가드
    def _should_not_call(*_a, **_k):
        raise AssertionError("browser_context must not be called when external browser is provided")

    monkeypatch.setattr(mod, "browser_context", _should_not_call)

    page = FakePage(html_with_encparam=True)
    browser = FakeBrowser(page)

    result = await mod.extract_session_info(
        browser=browser,
        cmp_cd="005930",
        page=PAGE.c103,
    )

    assert result["encparam"] == "ENC-12345"
    assert result["user_agent"] == "FakeUA/1.0"
    assert result["referer"].startswith("https://navercomp.wisereport.co.kr/v2/company/")
    assert "cmp_cd=005930" in result["referer"]
    # 쿠키 헤더 형식 확인
    assert result["cookies"] in {"sid=abc; lang=ko", "lang=ko; sid=abc"}  # 순서 달라도 허용


@pytest.mark.asyncio
async def test_extract_session_info_creates_and_closes_internal_browser(monkeypatch):
    """
    외부 browser가 없을 때:
    - 내부 browser_context를 통해 생성/정리되는지 확인
    - encparam/UA/cookies/referer 추출 확인
    """
    page = FakePage(html_with_encparam=True)
    fake_browser = FakeBrowser(page)

    class DummyACM:
        def __init__(self):
            self.entered = False
            self.exited = False

        async def __aenter__(self):
            self.entered = True
            return fake_browser

        async def __aexit__(self, exc_type, exc, tb):
            self.exited = True

    dummy_acm = DummyACM()
    monkeypatch.setattr(mod, "browser_context", lambda **_k: dummy_acm)

    result = await mod.extract_session_info(
        browser=None,
        cmp_cd="000660",
        page=PAGE.c103,
    )

    assert dummy_acm.entered is True
    assert dummy_acm.exited is True

    assert result["encparam"] == "ENC-12345"
    assert result["user_agent"] == "FakeUA/1.0"
    assert "cmp_cd=000660" in result["referer"]


@pytest.mark.asyncio
async def test_extract_session_info_when_encparam_missing(monkeypatch):
    """
    encparam이 HTML에 없을 때:
    - encparam=None 으로 반환
    - 나머지 UA/쿠키/레퍼러는 정상
    """
    page = FakePage(html_with_encparam=False)
    browser = FakeBrowser(page)

    # logger.warning 호출 여부를 가볍게 확인(선택)
    called = {"warn": False}

    def fake_warning(msg):
        called["warn"] = True

    monkeypatch.setattr(mod.logger, "warning", fake_warning)

    result = await mod.extract_session_info(
        browser=browser,
        cmp_cd="373220",
        page=PAGE.c103,
    )

    assert result["encparam"] is None
    assert result["user_agent"] == "FakeUA/1.0"
    assert "cmp_cd=373220" in result["referer"]
    assert called["warn"] is True


@pytest.mark.asyncio
async def test_extract_session_info_selector_fallback(monkeypatch):
    """
    wait_for_selector가 타임아웃/예외일 때 폴백(wait_for_timeout) 경로가 실행돼도 문제 없이 동작해야 한다.
    """
    class PageRaising(FakePage):
        async def wait_for_selector(self, selector: str, timeout: int = 3000):
            raise TimeoutError("simulated timeout")

    page = PageRaising(html_with_encparam=True)
    browser = FakeBrowser(page)

    # 폴백 경로를 타도 encparam은 정상 추출되어야 함
    result = await mod.extract_session_info(browser=browser, cmp_cd="005930", page=PAGE.c103)
    assert result["encparam"] == "ENC-12345"