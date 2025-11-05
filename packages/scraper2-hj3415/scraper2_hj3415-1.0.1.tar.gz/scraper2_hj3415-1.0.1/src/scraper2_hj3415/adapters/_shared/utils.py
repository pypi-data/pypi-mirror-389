# scraper2_hj3415/adapters/_shared/utils.py

from loguru import logger
import pandas as pd
from typing import Iterable, Iterator, TypeVar, List

T = TypeVar("T")

def chunked(iterable: Iterable[T], size: int) -> Iterator[List[T]]:
    # 큰 데이터 시퀀스를 size개씩 끊어서(List로 묶어서) 하나씩 yield 하는 제너레이터 함수.
    buf: List[T] = []
    for item in iterable:
        buf.append(item)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf

def log_df(df: pd.DataFrame, name: str = "DataFrame", max_rows: int = 10):
    """짧고 깔끔하게 DataFrame 로그 찍기"""
    if df.empty:
        logger.info(f"[{name}] DataFrame is empty.")
        return

    head = df.head(max_rows)
    msg = head.to_markdown(index=False)
    more = "" if len(df) <= max_rows else f"\n... ({len(df)} rows total)"
    logger.debug(f"\n[{name}] shape={df.shape}\n{msg}{more}")