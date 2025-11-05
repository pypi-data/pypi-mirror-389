import pytest
import httpx
from scraper2_hj3415.adapters.clients import http as http_mod


@pytest.mark.asyncio
async def test_create_http_client_default_settings():
    """기본 설정으로 http client 생성 확인"""
    client = http_mod.create_http_client()
    assert isinstance(client, httpx.AsyncClient)
    # 기본 헤더에 User-Agent가 포함되어야 함
    ua = client.headers.get("User-Agent")
    assert "Mozilla" in ua
    assert "Safari" in ua
    # 기본값 검증
    assert client.timeout.connect == 10.0
    assert client.follow_redirects is True
    # base_url이 비어 있을 수 있음
    assert isinstance(client.base_url, httpx.URL)
    await client.aclose()


@pytest.mark.asyncio
async def test_create_http_client_custom_settings():
    """base_url, timeout, headers 지정 시 반영되는지 검증"""
    custom_headers = {"X-API-KEY": "test-key"}
    client = http_mod.create_http_client(
        base_url="https://example.com/api/",
        timeout=5.0,
        headers=custom_headers,
    )
    try:
        assert isinstance(client, httpx.AsyncClient)
        # base_url 반영 확인
        assert str(client.base_url) == "https://example.com/api/"
        # timeout 반영 확인
        assert client.timeout.connect == 5.0
        # 헤더 병합 확인
        assert client.headers["X-API-KEY"] == "test-key"
        assert "User-Agent" in client.headers
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_retry_on_http_error_success():
    """예외 없이 성공하면 재시도 없이 1회만 호출된다."""
    called = {"count": 0}

    @http_mod.retry_on_http_error()
    async def dummy_request():
        called["count"] += 1
        return "ok"

    result = await dummy_request()
    assert result == "ok"
    assert called["count"] == 1


@pytest.mark.asyncio
async def test_retry_on_http_error_retry_then_raise_last_exception():
    """
    RequestError가 계속 발생하면 재시도 3회 후 마지막 예외(RequestError)가 그대로 발생한다.
    (reraise=True 설정이므로 RetryError가 아니다)
    """
    called = {"count": 0}

    @http_mod.retry_on_http_error()
    async def dummy_request():
        called["count"] += 1
        raise httpx.RequestError("network fail")

    with pytest.raises(httpx.RequestError):
        await dummy_request()

    assert called["count"] == 3  # stop_after_attempt(3) → 총 3회 호출