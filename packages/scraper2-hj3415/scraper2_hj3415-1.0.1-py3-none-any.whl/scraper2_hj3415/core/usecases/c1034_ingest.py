# scraper2_hj3415/core/usecases/c1034_ingest.py

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable, Literal, Sequence, Callable, Awaitable

from loguru import logger
from scraper2_hj3415.core.types import NormalizedBundle
from scraper2_hj3415.core.ports.source_port import C1034BundleSourcePort
from scraper2_hj3415.core.ports.sink_port import C1034SinkPort


@dataclass(frozen=True)
class IngestStats:
    dim_account_rows: int = 0
    dim_period_rows: int = 0
    fact_rows: int = 0
    delta_rows: int = 0

    def __add__(self, other: "IngestStats") -> "IngestStats":
        return IngestStats(
            dim_account_rows=self.dim_account_rows + other.dim_account_rows,
            dim_period_rows=self.dim_period_rows + other.dim_period_rows,
            fact_rows=self.fact_rows + other.fact_rows,
            delta_rows=self.delta_rows + other.delta_rows,
        )

class C1034IngestUseCase:
    """
    수집(Source) → 정규화(Pipeline) → 저장(Sink) 전체를 담당하는 유스케이스.

    생성 방법:
        일반 생성자 대신 반드시 아래 팩토리 메서드를 사용해야 합니다.

            uc = await C1034IngestUseCase.create(repo)

        내부적으로 Playwright 브라우저 세션을 자동 생성하며,
        종료 시에는 `await uc.close()` 로 정리해야 합니다.
    """

    def __init__(
        self,
        *,
        source: C1034BundleSourcePort,
        sink: C1034SinkPort,
        on_bundle: Callable[[str, NormalizedBundle], Awaitable[None]] | None = None,
    ) -> None:
        self.source = source
        self.sink = sink
        self.on_bundle = on_bundle

    async def _save_bundle(
        self, page_label: str, bundle: NormalizedBundle
    ) -> IngestStats:
        await self.sink.save_all(
            dim_account_df=bundle.dim_account,
            dim_period_df=bundle.dim_period,
            fact_df=bundle.fact,
            delta_df=bundle.delta,
        )
        stats = IngestStats(
            dim_account_rows=len(bundle.dim_account),
            dim_period_rows=len(bundle.dim_period),
            fact_rows=len(bundle.fact),
            delta_rows=len(bundle.delta),
        )
        logger.debug(f"[{page_label}] saved bundle stats={asdict(stats)}")
        return stats

    async def ingest_c103(
        self, cmp_cd: str, *, save: bool = True, collect_only: bool = False
    ):
        logger.info(f"[c103] ingest start cmp_cd={cmp_cd} save={save}")
        bundles = await self.source.list_bundles(cmp_cd, page="c103", concurrency=2)
        if self.on_bundle:
            for b in bundles:
                await self.on_bundle("c103", b)
        if save and not collect_only:
            stats = IngestStats()
            for b in bundles:
                stats += await self._save_bundle("c103", b)
            logger.info(f"[c103] ingest done cmp_cd={cmp_cd} result={asdict(stats)}")
            return stats
        else:
            logger.info(
                f"[c103] ingest done cmp_cd={cmp_cd} result={len(bundles)} bundles"
            )
            return bundles

    async def ingest_c104(self, cmp_cd: str, *, save: bool = True, collect_only: bool = False):
        logger.info(f"[c104] ingest start cmp_cd={cmp_cd} save={save}")
        bundles = await self.source.list_bundles(cmp_cd, page="c104", concurrency=2)
        if self.on_bundle:
            for b in bundles:
                await self.on_bundle("c104", b)
        if save and not collect_only:
            stats = IngestStats()
            for b in bundles:
                stats += await self._save_bundle("c104", b)
            logger.info(f"[c104] ingest done cmp_cd={cmp_cd} result={asdict(stats)}")
            return stats
        else:
            logger.info(f"[c104] ingest done cmp_cd={cmp_cd} result={len(bundles)} bundles")
            return bundles

    async def ingest_all(self, cmp_cd: str, pages: Sequence[Literal["c103","c104"]] = ("c103","c104"), *, save=True, collect_only=False):
        total = IngestStats()
        collected: list[NormalizedBundle] = []
        if "c103" in pages:
            r = await self.ingest_c103(cmp_cd, save=save, collect_only=collect_only)
            total = total + r if isinstance(r, IngestStats) else total; collected += ([] if isinstance(r, IngestStats) else r)
        if "c104" in pages:
            r = await self.ingest_c104(cmp_cd, save=save, collect_only=collect_only)
            total = total + r if isinstance(r, IngestStats) else total; collected += ([] if isinstance(r, IngestStats) else r)
        return total if save and not collect_only else collected

    async def ingest_many(self, cmp_cds: Iterable[str], pages: Sequence[Literal["c103","c104"]] = ("c103","c104"), *, concurrency=3, save=True, collect_only=False):
        import asyncio
        sem = asyncio.Semaphore(max(1, concurrency))
        agg = IngestStats()
        collected: dict[str, list[NormalizedBundle]] = {}

        async def _worker(code: str):
            async with sem:
                try:
                    res = await self.ingest_all(code, pages=pages, save=save, collect_only=collect_only)
                    return ("stats", res, code) if isinstance(res, IngestStats) else ("bundles", res, code)
                except Exception as e:
                    logger.exception(f"ingest error cmp_cd={code}: {e}")
                    return ("error", e, code)

        tasks = [_worker(c) for c in cmp_cds]
        for coro in asyncio.as_completed(tasks):
            kind, payload, code = await coro
            if kind == "stats":
                agg = agg + payload  # type: ignore[operator]
            elif kind == "bundles":
                collected[code] = payload  # type: ignore[assignment]
        return agg if save and not collect_only else collected