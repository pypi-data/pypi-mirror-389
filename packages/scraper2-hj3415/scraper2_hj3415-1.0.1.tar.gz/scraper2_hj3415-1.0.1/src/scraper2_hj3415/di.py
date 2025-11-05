# scraper2_hj3415/di.py
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable, Awaitable

from scraper2_hj3415.core.types import NormalizedBundle
from scraper2_hj3415.core.usecases.c1034_ingest import C1034IngestUseCase
from scraper2_hj3415.core.ports.sink_port import C1034SinkPort
from scraper2_hj3415.core.ports.source_port import C1034BundleSourcePort
from contracts_hj3415.ports.c1034_write_repo import C1034WriteRepoPort

# ── Adapters (실어댑터) ──────────────────────────────────────────────────────
from scraper2_hj3415.adapters.clients.browser import PlaywrightSession
from scraper2_hj3415.adapters.nfs.sources.bundle_source import NfsBundleSource
from scraper2_hj3415.adapters.nfs.sinks.c1034_sink import C1034Sink


# ── 설정값 로딩 도우미 ───────────────────────────────────────────────────────
def _env_bool(key: str, default: bool) -> bool:
    v = os.getenv(key)
    if v is None:
        return default
    return v.lower() in {"1", "true", "yes", "on"}

def _env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, "").strip() or default)
    except Exception:
        return default


# ── DI: Playwright 세션 + Source + Sink + UseCase 조립 ──────────────────────
@asynccontextmanager
async def provide_ingest_usecase(
    *,
    repo: C1034WriteRepoPort,                           # ← db2_hj3415 등 구현체 주입 필수
    headless: bool | None = None,                        # 기본: ENV로 제어
    chunk: int | None = None,                            # 기본: ENV로 제어
    on_bundle: Callable[[str, NormalizedBundle], Awaitable[None]] | None = None,
) -> AsyncIterator[C1034IngestUseCase]:
    """
    실제 어댑터를 사용해 C1034IngestUseCase를 만들어 주는 async context manager.

    Lifecyle:
      - PlaywrightSession 생성 → NfsBundleSource 생성 → C1034Sink(repo) 생성
      - with 블록 종료 시 세션 정리

    Args:
        repo: C1034RepositoryPort 구현체 (예: db2_hj3415의 Mongo/Beanie 리포지토리)
        headless: 브라우저 headless 여부 (None이면 환경변수로 결정)
        chunk: Sink 배치 저장 크기 (None이면 환경변수로 결정)
        on_bundle: 각 번들 저장 전 훅(옵션)

    ENV:
        SCRAPER_HEADLESS=true|false (default: true)
        SCRAPER_SINK_CHUNK=1000      (default: 1000)
    """
    # 환경변수 기반 기본값
    headless = _env_bool("SCRAPER_HEADLESS", True) if headless is None else headless
    chunk = _env_int("SCRAPER_SINK_CHUNK", 1000) if chunk is None else chunk

    # 1) 브라우저 세션
    session = await PlaywrightSession.create(headless=headless)

    try:
        # 2) Source 어댑터 (실제 네트워크/브라우저 사용)
        source: C1034BundleSourcePort = NfsBundleSource(session)

        # 3) Sink 어댑터 (repo 구현체로 저장)
        sink: C1034SinkPort = C1034Sink(repo, chunk=chunk)

        # 4) UseCase 조립 (Core는 어댑터 타입을 몰라도 Port로만 의존)
        uc = C1034IngestUseCase(source=source, sink=sink, on_bundle=on_bundle)
        yield uc
    finally:
        await session.close()


# ── 세션 재사용 버전 (이미 열린 PlaywrightSession 주입) ──────────────────────
@asynccontextmanager
async def provide_ingest_usecase_with_session(
    *,
    session: PlaywrightSession,                          # 이미 띄워둔 세션을 재사용
    repo: C1034WriteRepoPort,
    chunk: int | None = None,
    on_bundle: Callable[[str, NormalizedBundle], Awaitable[None]] | None = None,
) -> AsyncIterator[C1034IngestUseCase]:
    """
    외부에서 PlaywrightSession을 직접 관리하는 경우 사용하세요.
    (이 컨텍스트는 세션을 닫지 않습니다)
    """
    chunk = _env_int("SCRAPER_SINK_CHUNK", 1000) if chunk is None else chunk

    source: C1034BundleSourcePort = NfsBundleSource(session)
    sink: C1034SinkPort = C1034Sink(repo, chunk=chunk)
    uc = C1034IngestUseCase(source=source, sink=sink, on_bundle=on_bundle)
    try:
        yield uc
    finally:
        # 세션은 외부 소유이므로 닫지 않음
        pass