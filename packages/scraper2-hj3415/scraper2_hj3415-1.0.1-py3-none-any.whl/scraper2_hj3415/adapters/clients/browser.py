# src/scraper2_hj3415/adapters/clients/browser.py

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import subprocess
import sys
import os

from playwright.async_api import async_playwright, Browser, Error as PWError

def _install_playwright_browsers(*names: str) -> None:
    """
    playwright install [names...] 를 코드에서 실행.
    macOS/Windows에선 install만, Linux면 필요시 install-deps도 함께.
    """
    args = [sys.executable, "-m", "playwright", "install", *names]
    subprocess.run(args, check=True)

    if sys.platform.startswith("linux"):
        try:
            subprocess.run(
                [sys.executable, "-m", "playwright", "install-deps"], check=True
            )
        except Exception:
            pass

class PlaywrightSession:
    def __init__(self, browser, pw):
        self.browser = browser
        self.pw = pw

    @classmethod
    async def create(cls, headless=True):
        browser, pw = await PlaywrightSession.create_browser(headless=headless)
        return cls(browser, pw)

    @staticmethod
    async def create_browser(headless: bool = True) -> tuple[Browser, any]:
        """
        Playwright Browser 인스턴스를 생성하고 반환합니다.
        (asynccontextmanager를 사용하지 않는 일반 버전)

        사용 예시:
            browser, pw = await create_browser()
            page = await browser.new_page()
            await page.goto("https://example.com")
            html = await page.content()
            await browser.close()
            await pw.stop()

        Args:
            headless: 브라우저를 headless 모드로 실행할지 여부 (기본 True)
        Returns:
            (browser, pw): (Browser 객체, async_playwright 인스턴스)
        """
        pw = await async_playwright().start()
        try:
            try:
                browser = await pw.chromium.launch(headless=headless)
            except PWError as e:
                msg = str(e)
                need_install = (
                    "Executable doesn't exist" in msg
                    or "Please run the following command to download new browsers"
                    in msg
                )
                if need_install and os.getenv("PW_SKIP_AUTO_INSTALL") != "1":
                    await pw.stop()
                    _install_playwright_browsers("chromium")
                    pw = await async_playwright().start()
                    browser = await pw.chromium.launch(headless=headless)
                else:
                    raise
            return browser, pw
        except Exception:
            await pw.stop()
            raise

    async def close(self):
        await self.browser.close()
        await self.pw.stop()



@asynccontextmanager
async def browser_context(headless: bool = True) -> AsyncGenerator[Browser, None]:
    """
    Playwright Browser 인스턴스를 생성하고 반환합니다.
    블록을 벗어나면 자동으로 종료됩니다.

    Usage:
        async with create_browser() as browser:
            page = await browser.new_page()
            await page.goto("https://example.com")
            html = await page.content()

    Args:
        headless: 브라우저를 headless 모드로 실행할지 여부 (기본 True)
    """
    pw = await async_playwright().start()
    try:
        try:
            browser = await pw.chromium.launch(headless=headless)
        except PWError as e:
            # 바이너리 미설치 상황 감지
            msg = str(e)
            need_install = "Executable doesn't exist" in msg or "Please run the following command to download new browsers" in msg
            if need_install and os.getenv("PW_SKIP_AUTO_INSTALL") != "1":
                # 일단 정리
                await pw.stop()
                # 브라우저 설치
                _install_playwright_browsers("chromium")
                # 재시작 후 재시도
                pw = await async_playwright().start()
                browser = await pw.chromium.launch(headless=headless)
            else:
                raise

        try:
            yield browser
        finally:
            await browser.close()
    finally:
        await pw.stop()