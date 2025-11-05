# scraper2_hj3415/adapters/nfs/pipeline/normalize_c1034.py

import re
import pandas as pd
from scraper2_hj3415.core import constants as C
from scraper2_hj3415.core.types import NormalizedBundle
from scraper2_hj3415.adapters._shared.utils import log_df

def _parse_yymm(lbl: str):
    s = re.sub(r"<br\s*/?>", " ", lbl).strip()
    # 날짜가 아닌 지표 라벨들(전년/전분기 비교 섹션) 필터링
    if any(key in s for key in ["전년대비", "YoY", "QoQ", "전분기대비"]):
        return {"label": s, "period": None, "basis": None, "is_estimate": False, "is_yoy_row": True}
    est = "(E)" in s
    m = re.search(r"(\d{4})/(\d{2})", s)
    period = pd.Timestamp(f"{m.group(1)}-{m.group(2)}-01") if m else None
    b = re.search(r"\(([^)]+)\)$", s.replace("(E)","").strip())
    basis = b.group(1) if b else None
    return {"label": s, "period": period, "basis": basis, "is_estimate": est, "is_yoy_row": False}

def normalize_metric_rows(rows: list[dict], yymm: list[str], *, frq: C.FRQ, rate_fields: dict, meta: dict):
    lab = pd.DataFrame([_parse_yymm(x) for x in yymm]).rename_axis("pos").reset_index()
    lab_valid = lab[~lab["is_yoy_row"]].copy().reset_index(drop=True)
    lab_valid["pos1"] = lab_valid.index + 1  # DATA1..K 매핑용
    df = pd.DataFrame(rows)

    # enum 값을 이해하기 쉬운 라벨로 변환
    meta_lbl = {
        "cmp_cd": meta["cmp_cd"],
        "page": C.PAGE_TO_LABEL[meta["page"]],
        "rpt": C.RPT_TO_LABEL[meta["rpt"]],
        "frq": C.FRQ_TO_LABEL[meta["frq"]],
    }

    # fact 처리
    k = len(lab_valid)
    data_cols = [f"DATA{i}" for i in range(1, k+1) if f"DATA{i}" in df.columns]

    long = df.melt(
        id_vars=["ACCODE","ACC_NM","LVL","P_ACCODE","GRP_TYP","UNT_TYP","ACKIND","POINT_CNT"],
        value_vars=data_cols, var_name="data_col", value_name="value"
    )
    long["pos1"] = long["data_col"].str.replace("DATA","",regex=False).astype(int)
    long = long.merge(lab_valid[["pos1","period","basis","is_estimate"]], on="pos1", how="inner")
    long = long.dropna(subset=["period", "value"])

    for k in ["cmp_cd","page","rpt","frq"]:
        long[k] = meta_lbl[k]
    fact = (long
        .drop(columns=["data_col","pos1"])
        .rename(columns={
            "ACCODE":"accode","ACC_NM":"account_name","LVL":"level",
            "P_ACCODE":"parent_accode","GRP_TYP":"group_type","UNT_TYP":"unit_type",
            "ACKIND":"acc_kind","POINT_CNT":"precision"
        })
        .reset_index(drop=True)
    )

    # dim_account 처리
    dim_account = (fact[["accode","account_name","level","parent_accode","group_type","unit_type","acc_kind","precision"]]
                   .drop_duplicates().reset_index(drop=True))

    # dim_period 처리
    dim_period = (lab_valid[["period","basis","is_estimate"]].dropna(subset=["period"]).drop_duplicates().reset_index(drop=True))
    dim_period["frq"] = meta_lbl["frq"]

    # delta 처리
    rate_numeric = rate_fields.get("numeric", [])
    rate_comments = rate_fields.get("comments", [])
    use_cols = ["ACCODE"] + [c for c in rate_numeric+rate_comments if c in df.columns]
    if len(use_cols) > 1:
        delta = df[use_cols].copy().rename(columns={"ACCODE":"accode"})
        for k in ["cmp_cd","page","rpt","frq"]:
            delta[k] = meta_lbl[k]
    else:
        delta = pd.DataFrame(columns=["accode"] + rate_numeric + rate_comments + ["cmp_cd","page","rpt","frq"])

    # 데이터프레임 로그출력
    log_df(fact, "fact_df", 1000)
    log_df(dim_account, "dim_account_df", 1000)
    log_df(dim_period, "dim_period_df", 1000)
    log_df(delta, "delta_df", 1000)

    return fact, dim_account, dim_period, delta

def normalize_quarter_payload(payload: dict, meta: dict):
    return normalize_metric_rows(
        payload["DATA"], payload["YYMM"], frq=C.FRQ.Q,
        rate_fields={"numeric":["QOQ","QOQ_E"], "comments":["QOQ_COMMENT","QOQ_E_COMMENT"]},
        meta=meta,
    )

def normalize_year_payload(payload: dict, meta: dict):
    return normalize_metric_rows(
        payload["DATA"], payload["YYMM"], frq=C.FRQ.Y,
        rate_fields={"numeric":["YYOY","YEYOY"], "comments":[]},
        meta=meta,
    )

def normalize_dispatch(payload: dict, meta: dict) -> NormalizedBundle:
    """frq에 따라 분기/연간 정규화를 자동 선택."""
    frq: C.FRQ = meta["frq"]
    if frq == C.FRQ.Q:
        fact, dim_account, dim_period, delta = normalize_quarter_payload(payload, meta)
    elif frq == C.FRQ.Y:
        fact, dim_account, dim_period, delta = normalize_year_payload(payload, meta)
    else:
        raise ValueError(f"Unsupported FRQ: {frq!r}")
    return NormalizedBundle(fact, dim_account, dim_period, delta)