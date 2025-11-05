import pytest
import scraper2_hj3415.adapters.clients.browser as browser_mod


@pytest.mark.asyncio
#@pytest.mark.skipif(os.getenv("PLAYWRIGHT_E2E") != "1", reason="Set PLAYWRIGHT_E2E=1 to run real browser test")
async def test_create_browser_e2e_real_playwright():
    """
    실제 Playwright를 사용한 간단 E2E 테스트 (기본 skip).
    환경변수 PLAYWRIGHT_E2E=1 로 활성화.
    """
    async with browser_mod.browser_context(headless=True) as browser:
        page = await browser.new_page()
        await page.goto("https://example.com", wait_until="load")
        html = await page.content()
        assert "<title>Example Domain</title>" in html
        await page.close()