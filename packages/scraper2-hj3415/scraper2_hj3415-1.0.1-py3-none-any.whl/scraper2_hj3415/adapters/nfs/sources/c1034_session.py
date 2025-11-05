# scraper2_hj3415/adapters/nfs/sources/c1034_session.py

import re
from loguru import logger

from scraper2_hj3415.adapters.clients.browser import browser_context
from scraper2_hj3415.core.constants import PAGE
from playwright.async_api import Browser

async def extract_session_info(
    *,
    browser: Browser | None = None,
    cmp_cd: str = "005930",
    page: PAGE = PAGE.c103,
) -> dict:
    """
    Playwright로 referer/UA/쿠키/encparam만 추출.
    - 외부 browser가 있으면 재사용, 없으면 내부에서 열고 닫음.
    - 데이터 호출은 httpx로 하는 하이브리드 구성 전제를 만족하도록 세션 구성만 담당.
    """
    is_external = browser is not None

    if not is_external:
        # 내부 생성
        browser_cm = browser_context(headless=True)  # 기존에 갖고있는 @asynccontextmanager
        browser = await browser_cm.__aenter__()

    context = None
    page_ = None
    try:
        # 1) 격리된 Context 생성 (쿠키/스토리지 분리)
        context = await browser.new_context()

        # 2) 리소스 차단: 불필요한 렌더링 비용 제거
        await context.route("**/*", lambda route: (
            route.abort()
            if route.request.resource_type in {"image", "font", "stylesheet", "media"}
            else route.continue_()
        ))

        # 3) 페이지 오픈
        page_ = await context.new_page()
        # StrEnum이라도 안전하게 .value 로 명시
        url = f"https://navercomp.wisereport.co.kr/v2/company/{page.value}?cmp_cd={cmp_cd}"

        # UA는 context 생성 이후 읽어도 같지만, page 쪽이 더 직관적
        await page_.goto(url, wait_until="domcontentloaded")

        # 4) 'encparam'이 들어있는 스크립트가 로드될 시간을 짧게 확보
        #    가능하면 안정적인 셀렉터를 쓰세요(예: 표/탭 등). 없으면 폴백 타임아웃.
        try:
            # 스크립트 내 텍스트 매칭 (Playwright의 has-text 선택자를 활용)
            await page_.wait_for_selector("script:has-text('encparam')", timeout=3000)
        except Exception:
            # 폴백: 짧은 대기
            await page_.wait_for_timeout(300)

        html = await page_.content()
        m = re.search(
            r"""encparam\s*(?:[:=])\s*['"]([^'"]+)['"]""", html, re.IGNORECASE
        )
        encparam = m.group(1) if m else None
        if not encparam:
            logger.warning("encparam not found in page HTML")

        # 5) UA / 쿠키 수집(컨텍스트 기준)
        ua = await page_.evaluate("navigator.userAgent")
        cookies = await context.cookies()
        cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

        logger.debug(f"encparam={encparam!r}")
        logger.debug(f"cookies={cookie_header!r}")

        return {
            "encparam": encparam,
            "cookies": cookie_header,
            "referer": url,
            "user_agent": ua,
        }

    finally:
        # 열린 순서의 반대로 정리
        try:
            if page_:
                await page_.close()
        finally:
            if context:
                await context.close()
            if not is_external:
                await browser_cm.__aexit__(None, None, None)
