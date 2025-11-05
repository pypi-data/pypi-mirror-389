# 예) entrypoints/main.py
import asyncio
from scraper2_hj3415.di import provide_ingest_usecase

from db2_hj3415.adapters.mongo.db import init_beanie_async, close_client
from db2_hj3415.adapters.nfs.repo_impls.c1034_write_repo_impl import MongoC1034WriteRepo  # ← 예시

async def main():
    client = await init_beanie_async(
        uri="mongodb://192.168.100.172:27017",
        db_name="nfs_db",
    )
    repo = MongoC1034WriteRepo()
    async with provide_ingest_usecase(repo=repo) as uc:
        stats = await uc.ingest_all("005930", pages=("c103", "c104"), save=True)
        print(stats)
    await close_client(client)

if __name__ == "__main__":
    asyncio.run(main())