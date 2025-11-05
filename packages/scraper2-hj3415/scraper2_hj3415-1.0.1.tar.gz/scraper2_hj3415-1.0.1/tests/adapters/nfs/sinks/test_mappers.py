import math
import pandas as pd
import numpy as np

from scraper2_hj3415.adapters.nfs.sinks.df_to_dto_mappers import (
    rows_to_dim_account,
    rows_to_dim_period,
    rows_to_fact_finance,
    rows_to_delta_finance,
)

from contracts_hj3415.nfs.dto import (
    DimAccountDTO,
    DimPeriodDTO,
    FactC1034DTO,
    DeltaC1034DTO,
)


def test_rows_to_dim_account_basic_and_nan():
    df = pd.DataFrame(
        [
            {
                "accode": "211300",
                "account_name": "매출총이익률",
                "level": 1,
                "parent_accode": None,     # None 유지
                "group_type": 2,
                "unit_type": 7,
                "acc_kind": "M",
                "precision": 2,
            },
            {
                "accode": "121000",
                "account_name": "매출액",
                "level": np.nan,            # NaN → None
                "parent_accode": "211300",
                "group_type": 0,
                "unit_type": 2,
                "acc_kind": "M",
                "precision": np.nan,        # NaN → None
            },
        ]
    )

    out = list(rows_to_dim_account(df))
    assert len(out) == 2
    assert all(isinstance(x, DimAccountDTO) for x in out)

    a0, a1 = out
    assert a0.accode == "211300"
    assert a0.level == 1
    assert a0.parent_accode is None
    assert a0.precision == 2

    assert a1.accode == "121000"
    assert a1.level is None                     # NaN → None 확인
    assert a1.parent_accode == "211300"
    assert a1.precision is None                 # NaN → None 확인


def test_rows_to_dim_period_auto_parse_period_to_date():
    # period 가 문자열이어도 내부에서 date 로 바뀌어야 함
    df = pd.DataFrame(
        [
            {"period": "2024-12-01", "basis": "IFRS연결", "is_estimate": False, "frq": "y"},
            {"period": "2024-06-01", "basis": "IFRS연결", "is_estimate": True, "frq": "q"},
        ]
    )

    out = list(rows_to_dim_period(df))
    assert len(out) == 2
    assert all(isinstance(x, DimPeriodDTO) for x in out)

    p0, p1 = out
    # pydantic 이 date 로 파싱되어야 함
    assert str(p0.period) == "2024-12-01"
    assert p0.basis == "IFRS연결"
    assert p0.is_estimate is False
    assert p0.frq == "y"

    assert str(p1.period) == "2024-06-01"
    assert p1.is_estimate is True
    assert p1.frq == "q"


def test_rows_to_fact_finance_happy_path_and_nan_optional_fields():
    df = pd.DataFrame(
        [
            {
                "cmp_cd": "005930",
                "page": "c104",
                "rpt": "수익성",
                "frq": "y",
                "accode": "211300",
                "account_name": "매출총이익률",
                "period": "2024-12-01",
                "value": 30.3,
                "basis": "IFRS연결",
                "is_estimate": False,
                "unit_type": 7,
                "level": 1,
                "parent_accode": None,
                "group_type": 2,
                "acc_kind": "M",
                "precision": 2,
            },
            {
                # NaN/결측 → None 으로 들어가야 하는 케이스
                "cmp_cd": "005930",
                "page": "c104",
                "rpt": "수익성",
                "frq": "y",
                "accode": "121000",
                "account_name": "매출액",
                "period": pd.Timestamp("2024-12-01"),
                "value": 50000,
                "basis": np.nan,
                "is_estimate": False,
                "unit_type": np.nan,
                "level": np.nan,
                "parent_accode": np.nan,
                "group_type": 0,
                "acc_kind": "M",
                "precision": np.nan,
            },
        ]
    )

    out = list(rows_to_fact_finance(df))
    assert len(out) == 2
    assert all(isinstance(x, FactC1034DTO) for x in out)

    f0, f1 = out
    assert f0.cmp_cd == "005930"
    assert f0.page == "c104"
    assert f0.rpt == "수익성"
    assert f0.frq == "y"
    assert f0.accode == "211300"
    assert str(f0.period) == "2024-12-01"
    assert math.isclose(f0.value, 30.3, rel_tol=1e-9)
    assert f0.unit_type == 7
    assert f0.precision == 2

    # NaN → None 확인
    assert f1.accode == "121000"
    assert f1.basis is None
    assert f1.unit_type is None
    assert f1.level is None
    assert f1.parent_accode is None
    assert f1.precision is None


def test_rows_to_delta_finance_basic_and_missing_fields():
    df = pd.DataFrame(
        [
            {
                "cmp_cd": "005930",
                "page": "c104",
                "rpt": "수익성",
                "frq": "q",
                "accode": "211300",
                "qoq": -1.35,
                "yoy": -5.98,
                "qoq_e": 1.82,
                "yoy_e": None,
                "qoq_comment": "이전분기: 35.55 → 최근: 34.19",
                "yoy_comment": None,
            },
            {
                # 일부 컬럼이 아예 없어도 _none_if_nan + getattr 로 None 으로 채워져야 함
                "cmp_cd": "005930",
                "page": "c104",
                "rpt": "수익성",
                "frq": "q",
                "accode": "121000",
            },
        ]
    )

    out = list(rows_to_delta_finance(df))
    assert len(out) == 2
    assert all(isinstance(x, DeltaC1034DTO) for x in out)

    d0, d1 = out
    assert d0.accode == "211300"
    assert d0.qoq == -1.35
    assert d0.yoy == -5.98
    assert d0.qoq_e == 1.82
    assert d0.yoy_e is None
    assert d0.qoq_comment.startswith("이전분기")
    assert d0.yoy_comment is None

    # 결측 필드 → None
    assert d1.accode == "121000"
    assert d1.qoq is None
    assert d1.yoy is None
    assert d1.qoq_e is None
    assert d1.yoy_e is None
    assert d1.qoq_comment is None
    assert d1.yoy_comment is None