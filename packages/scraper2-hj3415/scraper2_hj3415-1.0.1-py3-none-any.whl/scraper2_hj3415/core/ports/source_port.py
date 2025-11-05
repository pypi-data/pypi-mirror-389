# scraper2_hj3415/core/ports/source_port.py

from typing import Literal, Protocol, List
from scraper2_hj3415.core.types import NormalizedBundle

class C1034BundleSourcePort(Protocol):
    async def list_bundles(
        self,
        cmp_cd: str,
        page: Literal["c103", "c104"],
        *,
        concurrency: int = 2,
    ) -> List[NormalizedBundle]: ...