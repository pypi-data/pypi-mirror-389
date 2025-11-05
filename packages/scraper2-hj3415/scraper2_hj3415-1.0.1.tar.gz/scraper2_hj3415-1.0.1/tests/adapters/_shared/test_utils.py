# tests/adapters/_shared/test_utils.py
from __future__ import annotations

import pandas as pd
import pytest

import scraper2_hj3415.adapters._shared.utils as utils


# ────────────────────────────────
# chunked() 테스트
# ────────────────────────────────
def test_chunked_exact_division():
    data = list(range(10))
    result = list(utils.chunked(data, 2))
    # 2개씩 5묶음
    assert result == [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]]


def test_chunked_not_exact_division():
    data = list(range(7))
    result = list(utils.chunked(data, 3))
    # 마지막 묶음은 1개
    assert result == [[0, 1, 2], [3, 4, 5], [6]]


def test_chunked_with_empty_iterable():
    result = list(utils.chunked([], 3))
    assert result == []


def test_chunked_with_generator_input():
    gen = (x for x in range(5))
    result = list(utils.chunked(gen, 2))
    assert result == [[0, 1], [2, 3], [4]]


# ────────────────────────────────
# log_df() 테스트
# ────────────────────────────────
@pytest.fixture
def sample_df():
    return pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})


def test_log_df_empty(monkeypatch):
    """빈 DataFrame이면 info 로그 한 번"""
    called = {"info": 0, "debug": 0}

    def fake_info(msg):
        called["info"] += 1
        assert "empty" in msg

    def fake_debug(msg):
        called["debug"] += 1

    monkeypatch.setattr(utils.logger, "info", fake_info)
    monkeypatch.setattr(utils.logger, "debug", fake_debug)

    df = pd.DataFrame(columns=["a", "b"])
    utils.log_df(df, name="test_empty")

    assert called["info"] == 1
    assert called["debug"] == 0


def test_log_df_non_empty(monkeypatch, sample_df):
    """비어 있지 않으면 debug 로그로 head 내용 출력"""
    called = {"info": 0, "debug": 0}
    msgs: list[str] = []

    def fake_info(msg):
        called["info"] += 1

    def fake_debug(msg):
        called["debug"] += 1
        msgs.append(msg)

    monkeypatch.setattr(utils.logger, "info", fake_info)
    monkeypatch.setattr(utils.logger, "debug", fake_debug)

    utils.log_df(sample_df, name="sample", max_rows=2)

    # info는 안 찍힘, debug 1회
    assert called["info"] == 0
    assert called["debug"] == 1
    msg = msgs[0]
    assert "[sample]" in msg
    assert "shape=(3, 2)" in msg
    assert "a" in msg and "b" in msg  # markdown 테이블 헤더가 포함됨


def test_log_df_truncation_message(monkeypatch):
    """max_rows보다 많으면 총 행 수 표기"""
    called = {"debug": 0}
    msgs = []

    def fake_debug(msg):
        called["debug"] += 1
        msgs.append(msg)

    monkeypatch.setattr(utils.logger, "debug", fake_debug)

    df = pd.DataFrame({"x": list(range(20))})
    utils.log_df(df, name="big_df", max_rows=5)

    msg = msgs[0]
    assert "(20, 1)" in msg
    assert "... (20 rows total)" in msg