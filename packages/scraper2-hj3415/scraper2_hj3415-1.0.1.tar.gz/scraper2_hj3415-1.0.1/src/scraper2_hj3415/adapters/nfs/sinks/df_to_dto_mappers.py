# scraper2_hj3415/adapters/nfs/sinks/mappers.py
# DF → DTO 변환 유틸

from typing import Iterator
import math
import pandas as pd
from pydantic import ValidationError
from contracts_hj3415.nfs.dto import FactC1034DTO, DimAccountDTO, DimPeriodDTO, DeltaC1034DTO

def _none_if_nan(v):
    # pandas NaN/NaT → None
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if pd.isna(v):
        return None
    return v

def rows_to_dim_account(df: pd.DataFrame) -> Iterator[DimAccountDTO]:
    # 기대 컬럼: ['accode','account_name','level','parent_accode','group_type','unit_type','acc_kind','precision']
    for row in df.itertuples(index=False):
        try:
            yield DimAccountDTO(
                accode=row.accode,
                account_name=row.account_name,
                level=_none_if_nan(getattr(row, "level", None)),
                parent_accode=_none_if_nan(getattr(row, "parent_accode", None)),
                group_type=_none_if_nan(getattr(row, "group_type", None)),
                unit_type=_none_if_nan(getattr(row, "unit_type", None)),
                acc_kind=_none_if_nan(getattr(row, "acc_kind", None)),
                precision=_none_if_nan(getattr(row, "precision", None)),
            )
        except ValidationError:
            # 필요시 로깅/수집
            continue

def _sanitize_basis(v):
    return "" if v is None or (isinstance(v, float) and pd.isna(v)) else v

def rows_to_dim_period(df: pd.DataFrame) -> Iterator[DimPeriodDTO]:
    # 기대 컬럼: ['period','basis','is_estimate','frq']
    # period는 반드시 date로 변환되어 있어야 안전
    if df["period"].dtype != "datetime64[ns]":
        df = df.copy()
        df["period"] = pd.to_datetime(df["period"], errors="coerce").dt.date

    for row in df.itertuples(index=False):
        try:
            yield DimPeriodDTO(
                period=row.period,
                basis=_sanitize_basis(getattr(row, "basis", None)),
                is_estimate=bool(getattr(row, "is_estimate", False)),
                frq=row.frq,
            )
        except ValidationError:
            continue

def rows_to_fact_finance(df: pd.DataFrame) -> Iterator[FactC1034DTO]:
    # 기대 컬럼: ['cmp_cd','page','rpt','frq','accode','account_name','period','value', ...옵션들]
    if df["period"].dtype != "datetime64[ns]":
        df = df.copy()
        df["period"] = pd.to_datetime(df["period"], errors="coerce").dt.date

    for row in df.itertuples(index=False):
        try:
            yield FactC1034DTO(
                cmp_cd=row.cmp_cd,
                page=row.page,
                rpt=row.rpt,
                frq=row.frq,
                accode=row.accode,
                account_name=row.account_name,
                period=row.period,
                value=float(row.value),
                basis=_none_if_nan(getattr(row, "basis", None)),
                is_estimate=bool(getattr(row, "is_estimate", False)),
                unit_type=_none_if_nan(getattr(row, "unit_type", None)),
                level=_none_if_nan(getattr(row, "level", None)),
                parent_accode=_none_if_nan(getattr(row, "parent_accode", None)),
                group_type=_none_if_nan(getattr(row, "group_type", None)),
                acc_kind=_none_if_nan(getattr(row, "acc_kind", None)),
                precision=_none_if_nan(getattr(row, "precision", None)),
            )
        except (ValidationError, TypeError, ValueError):
            continue

def rows_to_delta_finance(df: pd.DataFrame) -> Iterator[DeltaC1034DTO]:
    # 기대 컬럼: ['cmp_cd','page','rpt','frq','accode','qoq','yoy','qoq_e','yoy_e','qoq_comment','yoy_comment']
    for row in df.itertuples(index=False):
        try:
            yield DeltaC1034DTO(
                cmp_cd=row.cmp_cd,
                page=row.page,
                rpt=row.rpt,
                frq=row.frq,
                accode=row.accode,
                qoq=_none_if_nan(getattr(row, "qoq", None)),
                yoy=_none_if_nan(getattr(row, "yoy", None)),
                qoq_e=_none_if_nan(getattr(row, "qoq_e", None)),
                yoy_e=_none_if_nan(getattr(row, "yoy_e", None)),
                qoq_comment=_none_if_nan(getattr(row, "qoq_comment", None)),
                yoy_comment=_none_if_nan(getattr(row, "yoy_comment", None)),
            )
        except ValidationError:
            continue