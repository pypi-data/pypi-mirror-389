# scraper2_hj3415/adapters/nfs/sources/bundle_source.py

from typing import List, Literal
from scraper2_hj3415.core.types import NormalizedBundle
from scraper2_hj3415.core.ports.source_port import C1034BundleSourcePort
from scraper2_hj3415.adapters.nfs.pipelines.c1034_pipeline import list_c103_bundles, list_c104_bundles
from scraper2_hj3415.adapters.clients.browser import PlaywrightSession  # 세션은 Adapter에서 관리

class NfsBundleSource(C1034BundleSourcePort):
    def __init__(self, session: PlaywrightSession):
        self.session = session
        self.browser = session.browser

    async def list_bundles(
        self,
        cmp_cd: str,
        page: Literal["c103", "c104"],
        *,
        concurrency: int = 2,
    ) -> List[NormalizedBundle]:
        if page == "c103":
            return await list_c103_bundles(cmp_cd, browser=self.browser, concurrency=concurrency)
        else:
            return await list_c104_bundles(cmp_cd, browser=self.browser, concurrency=concurrency)