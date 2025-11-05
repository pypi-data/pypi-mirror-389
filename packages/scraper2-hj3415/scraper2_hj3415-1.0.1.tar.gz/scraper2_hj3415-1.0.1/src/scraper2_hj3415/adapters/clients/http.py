# src/scraper2_hj3415/adapters/clients/http.py

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# HTTPX 에러용 커스텀 예외
class HttpClientError(Exception):
    """기본 HTTP 클라이언트 예외."""

# 재시도 데코레이터 (옵션)
def retry_on_http_error():
    return retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    )

# AsyncClient를 생성하는 팩토리 함수
def create_http_client(
    base_url: str | None = None,
    timeout: float = 10.0,
    headers: dict | None = None,
) -> httpx.AsyncClient:
    """
    공통 설정을 가진 httpx.AsyncClient 인스턴스를 생성합니다.

    Args:
        base_url: 기본 URL (있으면 모든 요청이 상대경로로 가능)
        timeout: 요청 타임아웃 (초)
        headers: 기본 헤더 (없으면 User-Agent 자동 설정)
    """
    default_headers = {
        "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
        ),
    }
    if headers:
        default_headers.update(headers)

    client = httpx.AsyncClient(
        base_url=base_url or "",
        timeout=httpx.Timeout(timeout),
        headers=default_headers,
        follow_redirects=True,
        verify=True,  # SSL 검증
    )
    return client

