# tests/e2e/test_ingest_c1034_mongo_e2e.py
from __future__ import annotations

import os
import pytest
from loguru import logger

pytestmark = pytest.mark.asyncio(scope="session")

from scraper2_hj3415.di import provide_ingest_usecase
from db2_hj3415.adapters.mongo.db import init_beanie_async, close_client
from db2_hj3415.adapters.nfs.repo_impls.c1034_write_repo_impl import MongoC1034WriteRepo
from db2_hj3415.adapters.mongo.models import (
    FactFinanceDoc, DimAccountDoc, DimPeriodDoc, DeltaFinanceDoc
)

# ─────────────────────────────────────────────────────────────────────
# 환경 변수
#   NFS_E2E=1               실제 네트워크 E2E 진행 (없으면 skip)
#   MONGO_URI, MONGO_DB     MongoDB 연결 정보
#   SCRAPER_HEADLESS=true   브라우저 headless 설정(기본 true)
# ─────────────────────────────────────────────────────────────────────
E2E = os.getenv("NFS_E2E") == "1"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "c1034_e2e")
HEADLESS = (os.getenv("SCRAPER_HEADLESS", "true").lower() in {"1", "true", "yes", "on"})

E2E = True
MONGO_URI = "mongodb://192.168.100.172:27017"
MONGO_DB = "c1034_e2e"
HEADLESS = True

@pytest.fixture(scope="session")
async def beanie_client():
    """
    Beanie v2 초기화/종료 (AsyncMongoClient).
    모듈 스코프로 한 번만 연결하고, 테스트 종료 시 닫아줍니다.
    """
    client = await init_beanie_async(uri=MONGO_URI, db_name=MONGO_DB)
    logger.info(f"Beanie initialized: uri={MONGO_URI} db={MONGO_DB}")
    try:
        yield client
    finally:
        await close_client(client)
        logger.info("Beanie client closed.")


@pytest.mark.skipif(not E2E, reason="Set NFS_E2E=1 to run real network E2E test.")
async def test_ingest_real_to_mongo(beanie_client):
    """
    실제 네트워크 + MongoDB 저장까지 E2E 검증.
    - Playwright로 WiseReport 페이지 접속
    - 파이프라인 정규화
    - MongoDB 컬렉션 저장
    """
    repo = MongoC1034WriteRepo()

    async with provide_ingest_usecase(repo=repo, headless=HEADLESS, chunk=1000) as uc:
        cmp_cd = "005930"  # 삼성전자
        stats = await uc.ingest_all(cmp_cd, pages=("c103", "c104"), save=True)

        # 기본 통계 검증
        assert stats.fact_rows > 0
        assert stats.dim_account_rows > 0
        assert stats.dim_period_rows > 0
        assert stats.delta_rows >= 0

    # 실제 DB 쿼리 확인
    facts = await FactFinanceDoc.find(FactFinanceDoc.cmp_cd == "005930").to_list()
    assert len(facts) > 0
    accs = await DimAccountDoc.find_all().to_list()
    pers = await DimPeriodDoc.find_all().to_list()
    dels = await DeltaFinanceDoc.find_all().to_list()

    logger.info(f"facts={len(facts)}, accounts={len(accs)}, periods={len(pers)}, deltas={len(dels)}")
    assert len(accs) > 0
    assert len(pers) > 0
    # 델타는 0일 수도 있으니 존재만 확인
    assert dels is not None


@pytest.mark.skipif(not E2E, reason="Set NFS_E2E=1 to run real network E2E test.")
async def test_ingest_many_collect_only(beanie_client):
    """
    두 개 종목을 동시에 수집 (collect_only=True) — 저장 없이 번들만 수집 검증
    """
    repo = MongoC1034WriteRepo()

    async with provide_ingest_usecase(repo=repo, headless=HEADLESS, chunk=1000) as uc:
        codes = ["005930", "000660"]  # 삼성전자, SK하이닉스
        res = await uc.ingest_many(
            codes,
            pages=("c103", "c104"),
            concurrency=2,
            save=False,
            collect_only=True,
        )

    # 수집 결과 구조 검증
    assert isinstance(res, dict)
    assert set(res.keys()) == set(codes)
    for code, bundles in res.items():
        assert len(bundles) > 0
        for b in bundles:
            # 최소 팩트는 비어있지 않아야 함
            assert hasattr(b, "fact")
            assert not b.fact.empty