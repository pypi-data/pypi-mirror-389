# scraper2_hj3415/entrypoints/cli.py
from __future__ import annotations

import os
import asyncio
import json
from pathlib import Path
from typing import List, Optional, Sequence

import typer
from loguru import logger

from scraper2_hj3415.di import provide_ingest_usecase
from scraper2_hj3415.core.usecases.c1034_ingest import IngestStats

# Beanie v2 (PyMongo AsyncMongoClient)
from db2_hj3415.adapters.mongo.db import init_beanie_async, close_client
# 저장 어댑터 (구현체)
from db2_hj3415.adapters.nfs.repo_impls.c1034_write_repo_impl import MongoC1034WriteRepo

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="scraper2_hj3415 - C103/C104 수집/정규화/저장 CLI",
)

# ────────────────────────────────────────────────
# 환경변수 로딩 도우미
# ────────────────────────────────────────────────
def get_env_or_fail(key: str) -> str:
    value = os.getenv(key)
    if not value:
        typer.echo(f"❌ 환경변수 {key} 가 설정되어 있지 않습니다.")
        raise typer.Exit(code=1)
    return value

# -----------------------
# 공통 로깅 설정
# -----------------------
def _setup_logging(verbose: int, quiet: bool) -> None:
    level = "INFO"
    if quiet:
        level = "WARNING"
    if verbose >= 2:
        level = "DEBUG"
    elif verbose == 1 and not quiet:
        level = "INFO"

    logger.remove()
    logger.add(typer.echo, colorize=True, level=level,
               format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                      "<level>{level: <8}</level> | "
                      "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                      "<level>{message}</level>")


# -----------------------
# 공통 실행 유틸
# -----------------------
async def _with_beanie(mongo_uri: str, db_name: str, coro):
    client = await init_beanie_async(uri=mongo_uri, db_name=db_name)
    try:
        return await coro()
    finally:
        await close_client(client)


def _parse_pages(pages: Sequence[str]) -> Sequence[str]:
    pages = [p.lower() for p in pages]
    for p in pages:
        if p not in {"c103", "c104"}:
            raise typer.BadParameter("pages는 c103, c104 중에서 선택하세요.")
    return tuple(pages)


def _print_stats_or_bundles(result):
    if isinstance(result, IngestStats):
        typer.echo(json.dumps({
            "dim_account_rows": result.dim_account_rows,
            "dim_period_rows": result.dim_period_rows,
            "fact_rows": result.fact_rows,
            "delta_rows": result.delta_rows,
        }, ensure_ascii=False, indent=2))
    else:
        # collect_only=True 인 경우
        typer.echo(f"Collected bundles: {len(result)}")


# -----------------------
# Commands
# -----------------------
@app.command(help="단일 종목 수집/저장 (c103/c104)")
def ingest_one(
    cmp_cd: str = typer.Argument(..., help="종목코드(6자리)"),
    pages: List[str] = typer.Option(["c103", "c104"], "--pages", "-p", help="수집할 페이지 선택(반복 옵션)"),
    save: bool = typer.Option(True, help="DB 저장 여부"),
    collect_only: bool = typer.Option(False, help="수집만 수행(저장은 안 함)"),
    concurrency: int = typer.Option(2, help="페이지 내부 동시성(번들 수집)"),
    verbose: int = typer.Option(0, "--verbose", "-v", count=True),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
):
    """
    지정한 종목의 C103/C104 페이지를 수집하고 MongoDB에 저장합니다.
    Mongo 연결정보는 반드시 환경변수로 설정해야 합니다:

        export MONGO_URI="mongodb://localhost:27017"
        export MONGO_DB="nfs_db"
    """

    headless = get_env_or_fail("SCRAPER_HEADLESS")
    chunk = get_env_or_fail("SCRAPER_SINK_CHUNK")
    mongo_uri = get_env_or_fail("MONGO_URI")
    mongo_db = get_env_or_fail("MONGO_DB")

    _setup_logging(verbose, quiet)
    pages_ = _parse_pages(pages)

    if collect_only and save:
        typer.secho(
            "[warn] --collect-only 가 지정되어 저장은 수행하지 않습니다 (--no-save 적용).",
            fg=typer.colors.YELLOW,
        )
        save = False

    async def run():
        repo = MongoC1034WriteRepo()
        async with provide_ingest_usecase(repo=repo, headless=headless, chunk=chunk) as uc:
            # 주의: 내부 source는 concurrency=2로 고정되어 있으면, 필요 시 di에서 파라미터로 넘겨 조정하세요.
            result = await uc.ingest_all(cmp_cd, pages=pages_, save=save, collect_only=collect_only)
            _print_stats_or_bundles(result)

    asyncio.run(_with_beanie(mongo_uri, mongo_db, run))


@app.command(help="여러 종목을 파일/인자에서 받아 일괄 수집/저장")
def ingest_many(
    cmp_cds: Optional[List[str]] = typer.Argument(None, help="종목코드들(공백 구분)"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="한 줄당 1개 종목코드"),
    pages: List[str] = typer.Option(["c103", "c104"], "--pages", "-p"),
    save: bool = typer.Option(True, help="DB 저장 여부"),
    collect_only: bool = typer.Option(False, help="수집만 수행(저장은 안 함)"),
    concurrency: int = typer.Option(3, help="종목 병렬 처리 동시성"),
    verbose: int = typer.Option(0, "--verbose", "-v", count=True),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
):

    headless = get_env_or_fail("SCRAPER_HEADLESS")
    chunk = get_env_or_fail("SCRAPER_SINK_CHUNK")
    mongo_uri = get_env_or_fail("MONGO_URI")
    mongo_db = get_env_or_fail("MONGO_DB")

    _setup_logging(verbose, quiet)
    pages_ = _parse_pages(pages)

    if collect_only and save:
        typer.secho(
            "[warn] --collect-only 가 지정되어 저장은 수행하지 않습니다 (--no-save 적용).",
            fg=typer.colors.YELLOW,
        )
        save = False

    codes: List[str] = []
    if file:
        codes.extend([line.strip() for line in file.read_text().splitlines() if line.strip()])
    if cmp_cds:
        codes.extend(cmp_cds)
    if not codes:
        raise typer.BadParameter("종목코드를 인자 또는 --file 로 제공하세요.")

    async def run():
        repo = MongoC1034WriteRepo()
        async with provide_ingest_usecase(repo=repo, headless=headless, chunk=chunk) as uc:
            result = await uc.ingest_many(
                codes,
                pages=pages_,
                concurrency=concurrency,
                save=save,
                collect_only=collect_only,
            )
            if isinstance(result, IngestStats):
                _print_stats_or_bundles(result)
            else:
                # collect_only=True 인 경우: dict[str, list[NormalizedBundle]]
                typer.echo(f"Collected codes: {list(result.keys())}")

    asyncio.run(_with_beanie(mongo_uri, mongo_db, run))


@app.command(help="DB 연결 확인(ping) 및 모델 인덱스 보장 체크")
def healthcheck(
    verbose: int = typer.Option(0, "--verbose", "-v", count=True),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
):
    mongo_uri = get_env_or_fail("MONGO_URI")
    mongo_db = get_env_or_fail("MONGO_DB")

    _setup_logging(verbose, quiet)

    async def run():
        client = await init_beanie_async(uri=mongo_uri, db_name=mongo_db)
        try:
            await client.admin.command("ping")
            typer.echo("OK: Mongo ping success & Beanie init done.")
        finally:
            await close_client(client)

    asyncio.run(run())


@app.command(help="버전/환경 출력")
def info():
    import platform
    import scraper2_hj3415
    typer.echo(json.dumps({
        "python": platform.python_version(),
        "package": "scraper2_hj3415",
        "version": getattr(scraper2_hj3415, "__version__", "0.0.0"),
    }, ensure_ascii=False, indent=2))


def main():
    app()


if __name__ == "__main__":
    main()