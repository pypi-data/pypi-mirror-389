# scraper2_hj3415/adapters/nfs/pipelines/c1034_pipeline.py

import asyncio
from typing import List, Callable
from playwright.async_api import Browser
from scraper2_hj3415.core import constants as C
from scraper2_hj3415.core.types import NormalizedBundle
from scraper2_hj3415.adapters.nfs.sources import c1034_fetch as fetch, c1034_session as session
from scraper2_hj3415.adapters.nfs.pipelines.normalize_c1034 import normalize_dispatch
from loguru import logger

async def list_bundles(
    page: C.PAGE,
    cmp_cd: str,
    rpt_enum: type[C.C103RPT | C.C104RPT],
    get_data_func: Callable,
    *,
    browser: Browser | None = None,
    concurrency: int = 2,
) -> list[NormalizedBundle]:
    sem = asyncio.Semaphore(max(1, concurrency))
    session_info = await session.extract_session_info(browser=browser, cmp_cd=cmp_cd, page=page)

    async def _one(rpt, frq):
        async with sem:
            meta = {"cmp_cd": cmp_cd, "page": page, "rpt": rpt, "frq": frq}
            payload = await get_data_func(session_info=session_info, cmp_cd=cmp_cd, rpt=rpt, frq=frq)
            return normalize_dispatch(payload, meta)

    tasks = [_one(rpt, frq) for rpt in rpt_enum for frq in (C.FRQ.Q, C.FRQ.Y)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    bundles: list[NormalizedBundle] = []
    for r in results:
        if isinstance(r, Exception):
            logger.warning(f"{C.PAGE_TO_LABEL[page]} partial failure: {r}")
            continue
        bundles.append(r)
    return bundles

async def list_c103_bundles(
    cmp_cd: str,
    *,
    browser: Browser | None = None,
    concurrency: int = 3,   # 분기/연간 총 6페이지 중 절반
) -> List[NormalizedBundle]:
    return await list_bundles(C.PAGE.c103, cmp_cd, C.C103RPT, fetch.get_c103_data, browser=browser, concurrency=concurrency)

async def list_c104_bundles(
    cmp_cd: str,
    *,
    browser: Browser | None = None,
    concurrency: int = 5,   # 분기/연간 총 10페이지 중 절반
) -> List[NormalizedBundle]:
    return await list_bundles(C.PAGE.c104, cmp_cd, C.C104RPT, fetch.get_c104_data, browser=browser, concurrency=concurrency)

