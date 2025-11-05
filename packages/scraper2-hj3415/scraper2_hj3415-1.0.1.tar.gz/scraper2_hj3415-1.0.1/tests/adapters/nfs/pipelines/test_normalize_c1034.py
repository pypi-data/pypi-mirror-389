# tests/adapters/nfs/pipeline/test_normalize_c1034.py
from __future__ import annotations

import pandas as pd
import pytest

from scraper2_hj3415.core import constants as C
from scraper2_hj3415.adapters.nfs.pipelines.normalize_c1034 import (
    normalize_metric_rows,
    normalize_quarter_payload,
    normalize_year_payload,
    normalize_dispatch,
)
# 모듈 내부에서 호출하는 log_df를 no-op으로 바꿔 테스트 로그를 깔끔하게 유지
import scraper2_hj3415.adapters.nfs.pipelines.normalize_c1034 as mod
mod.log_df = lambda *_a, **_k: None


@pytest.fixture
def sample_yymm_labels() -> list[str]:
    # DATA1 → 2024/03, DATA2 → 2024/06(E)
    # 마지막 항목은 YoY/QoQ 라벨(비-기간 라벨)이므로 무시되어야 함
    return [
        "2024/03 (연결)",
        "2024/06 (E) (개별)",
        "전년대비 YoY",  # should be filtered out
    ]


@pytest.fixture
def sample_rows() -> list[dict]:
    # 최소 필수 컬럼 + DATA1..k
    return [
        {
            "ACCODE": "A001",
            "ACC_NM": "매출액",
            "LVL": 1,
            "P_ACCODE": None,
            "GRP_TYP": 0,
            "UNT_TYP": 1,
            "ACKIND": "N",
            "POINT_CNT": 0,
            "DATA1": 100.0,
            "DATA2": 120.0,
        },
        {
            "ACCODE": "A002",
            "ACC_NM": "영업이익",
            "LVL": 1,
            "P_ACCODE": None,
            "GRP_TYP": 0,
            "UNT_TYP": 1,
            "ACKIND": "N",
            "POINT_CNT": 0,
            "DATA1": 10.0,
            "DATA2": None,  # None은 dropna(subset=["period","value"])로 걸러질 수 있음
        },
    ]


@pytest.fixture
def meta_quarter() -> dict:
    return {
        "cmp_cd": "005930",
        "page": C.PAGE.c103,
        "rpt": C.C103RPT.손익계산서,
        "frq": C.FRQ.Q,
    }


@pytest.fixture
def meta_year() -> dict:
    return {
        "cmp_cd": "000660",
        "page": C.PAGE.c103,
        "rpt": C.C103RPT.손익계산서,
        "frq": C.FRQ.Y,
    }


def test_normalize_metric_rows_quarter_basic(sample_rows, sample_yymm_labels, meta_quarter):
    fact, dim_account, dim_period, delta = normalize_metric_rows(
        rows=sample_rows,
        yymm=sample_yymm_labels,
        frq=C.FRQ.Q,
        rate_fields={"numeric": ["QOQ", "QOQ_E"], "comments": ["QOQ_COMMENT", "QOQ_E_COMMENT"]},
        meta=meta_quarter,
    )

    # fact: 기본 컬럼 존재 여부
    expected_fact_cols = {
        "accode",
        "account_name",
        "level",
        "parent_accode",
        "group_type",
        "unit_type",
        "acc_kind",
        "precision",
        "period",
        "basis",
        "is_estimate",
        "value",
        "cmp_cd",
        "page",
        "rpt",
        "frq",
    }
    assert expected_fact_cols.issubset(set(fact.columns))

    # 팩트 행 개수: DATA1/2 중 유효 period/value만 남음
    # sample_rows: (A001: DATA1=100, DATA2=120) → 2개
    #              (A002: DATA1=10,  DATA2=None) → 1개
    # 총 3개가 되어야 함
    assert len(fact) == 3

    # 라벨 파싱 확인: 첫 컬럼은 2024/03, 둘째는 2024/06(E)
    # period가 Timestamp로 변환되고, (E)는 is_estimate=True가 되어야 함
    periods = sorted(fact["period"].unique())
    assert all(isinstance(p, pd.Timestamp) for p in periods)
    assert pd.Timestamp("2024-03-01") in periods
    assert pd.Timestamp("2024-06-01") in periods
    # 2024/06 라인의 is_estimate가 True여야 함
    est_rows = fact[fact["period"] == pd.Timestamp("2024-06-01")]
    assert est_rows["is_estimate"].iloc[0] == True

    # 메타 라벨 매핑 확인
    assert set(fact["cmp_cd"].unique()) == {"005930"}
    assert set(fact["page"].unique()) == {C.PAGE_TO_LABEL[C.PAGE.c103]}  # "c103"
    assert set(fact["rpt"].unique()) == {C.RPT_TO_LABEL[C.C103RPT.손익계산서]}  # "손익계산서"
    assert set(fact["frq"].unique()) == {C.FRQ_TO_LABEL[C.FRQ.Q]}  # "q"

    # dim_account: 고유 계정 2개
    assert {"accode", "account_name", "level", "parent_accode", "group_type", "unit_type", "acc_kind", "precision"}.issubset(
        dim_account.columns
    )
    assert len(dim_account) == 2

    # dim_period: YoY 라벨(날짜 아님)은 제외되어 2개만
    assert {"period", "basis", "is_estimate", "frq"}.issubset(dim_period.columns)
    assert len(dim_period) == 2
    assert set(dim_period["frq"].unique()) == {C.FRQ_TO_LABEL[C.FRQ.Q]}  # "q"

    # delta: 분기 rate 필드가 컬럼으로 포함
    expected_delta_cols = {"accode", "QOQ", "QOQ_E", "QOQ_COMMENT", "QOQ_E_COMMENT", "cmp_cd", "page", "rpt", "frq"}
    assert expected_delta_cols.issubset(delta.columns)


def test_normalize_metric_rows_year_basic(sample_rows, sample_yymm_labels, meta_year):
    fact, dim_account, dim_period, delta = normalize_metric_rows(
        rows=sample_rows,
        yymm=sample_yymm_labels,
        frq=C.FRQ.Y,
        rate_fields={"numeric": ["YYOY", "YEYOY"], "comments": []},
        meta=meta_year,
    )

    # 연간 라벨 매핑 확인
    assert set(fact["cmp_cd"].unique()) == {"000660"}
    assert set(fact["frq"].unique()) == {C.FRQ_TO_LABEL[C.FRQ.Y]}  # "y"

    # delta: 연간 rate 필드가 컬럼으로 포함
    expected_delta_cols = {"accode", "YYOY", "YEYOY", "cmp_cd", "page", "rpt", "frq"}
    assert expected_delta_cols.issubset(delta.columns)


def test_normalize_quarter_payload_wrapper(sample_rows, sample_yymm_labels, meta_quarter):
    payload = {"DATA": sample_rows, "YYMM": sample_yymm_labels}
    fact, dim_account, dim_period, delta = normalize_quarter_payload(payload, meta_quarter)

    # wrapper가 내부 normalize_metric_rows와 동일한 결과 형태를 제공하는지만 간단 검증
    assert isinstance(fact, pd.DataFrame)
    assert isinstance(dim_account, pd.DataFrame)
    assert isinstance(dim_period, pd.DataFrame)
    assert isinstance(delta, pd.DataFrame)
    assert set(fact["frq"].unique()) == {C.FRQ_TO_LABEL[C.FRQ.Q]}


def test_normalize_year_payload_wrapper(sample_rows, sample_yymm_labels, meta_year):
    payload = {"DATA": sample_rows, "YYMM": sample_yymm_labels}
    fact, dim_account, dim_period, delta = normalize_year_payload(payload, meta_year)

    assert isinstance(fact, pd.DataFrame)
    assert set(fact["frq"].unique()) == {C.FRQ_TO_LABEL[C.FRQ.Y]}


def test_normalize_dispatch_by_frq(sample_rows, sample_yymm_labels, meta_quarter, meta_year):
    payload = {"DATA": sample_rows, "YYMM": sample_yymm_labels}

    # 분기
    bundle_q = normalize_dispatch(payload, meta_quarter)
    assert hasattr(bundle_q, "fact") and hasattr(bundle_q, "dim_account") and hasattr(bundle_q, "dim_period") and hasattr(bundle_q, "delta")
    assert isinstance(bundle_q.fact, pd.DataFrame)
    assert set(bundle_q.fact["frq"].unique()) == {C.FRQ_TO_LABEL[C.FRQ.Q]}

    # 연간
    bundle_y = normalize_dispatch(payload, meta_year)
    assert set(bundle_y.fact["frq"].unique()) == {C.FRQ_TO_LABEL[C.FRQ.Y]}


def test_normalize_metric_rows_when_no_rate_fields(sample_rows, sample_yymm_labels, meta_quarter):
    # rate_fields에 유효 컬럼이 하나도 없을 때 delta가 빈 프레임이어야 함
    fact, dim_account, dim_period, delta = normalize_metric_rows(
        rows=sample_rows,
        yymm=sample_yymm_labels,
        frq=C.FRQ.Q,
        rate_fields={"numeric": ["NOT_EXIST"], "comments": ["ALSO_NOT_EXIST"]},
        meta=meta_quarter,
    )
    # 정의상 최소 컬럼 세트는 존재하되, 실제 행은 0이어야 함
    assert list(delta.columns) == ["accode", "cmp_cd", "page", "rpt", "frq"] or len(delta) == 0


def test_normalize_dispatch_raises_on_unsupported_frq(sample_rows, sample_yymm_labels):
    payload = {"DATA": sample_rows, "YYMM": sample_yymm_labels}
    bad_meta = {
        "cmp_cd": "005930",
        "page": C.PAGE.c103,
        "rpt": C.C103RPT.손익계산서,
        "frq": "UNKNOWN",  # 잘못된 값
    }
    with pytest.raises(ValueError):
        normalize_dispatch(payload, bad_meta)