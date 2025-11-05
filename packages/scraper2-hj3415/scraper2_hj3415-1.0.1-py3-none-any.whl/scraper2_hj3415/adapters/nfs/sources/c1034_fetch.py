# scraper2-hj3415/adapters/nfs/sources/c1034_fetch.py

import httpx
from loguru import logger
from scraper2_hj3415.core.constants import ASPXInner, FRQ, C103RPT, C104RPT
from scraper2_hj3415.adapters.clients.http import create_http_client

async def fetch_financial_json(
    *,
    cmp_cd: str = "005930",
    aspx_inner: ASPXInner = ASPXInner.c103,
    rpt: C103RPT | C104RPT = C103RPT.손익계산서,
    frq: FRQ = FRQ.Y,
    encparam: str,
    cookies: str,
    referer: str,
    user_agent: str,
) -> dict | list:
    if not encparam:
        raise ValueError("encparam is missing")

    request_url = f"https://navercomp.wisereport.co.kr/v2/company/{aspx_inner}?cmp_cd={cmp_cd}"

    params = {
        "cmp_cd": cmp_cd,
        "frq": frq,
        "rpt": rpt,
        "finGubun": "MAIN",
        "frqTyp": frq,  # 연간
        "encparam": encparam,
    }
    
    headers = {
        "Cookie": cookies,
        "Referer": referer,
        "User-Agent": user_agent,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",  # 일부 서버가 AJAX 헤더 선호
    }

    async with create_http_client(timeout=10.0) as client:
        r = await client.get(request_url, params=params, headers=headers)
        r.raise_for_status()
        try:
            import json
            payload = r.json()
            for i, row in enumerate(payload["DATA"]):
                logger.debug(
                    "row {}/{} ACC_NM={}, ACCODE={}",
                    i + 1,
                    len(payload["DATA"]),
                    row.get("ACC_NM"),
                    row.get("ACCODE"),
                )
                logger.debug(
                    "row raw:\n{}", json.dumps(row, indent=2, ensure_ascii=False)
                )
            return payload
        except Exception:
            # text/html이더라도 JSON 형태면 그대로 파싱 시도
            text = r.text.strip()
            if text.startswith("{") or text.startswith("["):
                import json
                return json.loads(text)
            # 진짜 HTML일 경우만 예외 발생
            ctype = r.headers.get("Content-Type", "")
            snippet = text[:2000]
            raise httpx.HTTPStatusError(
                f"Unexpected content-type: {ctype}. Snippet:\n{snippet}",
                request=r.request,
                response=r,
            )

async def get_c103_data(
    *,
    session_info : dict,
    cmp_cd: str = "005930",
    rpt: C103RPT = C103RPT.손익계산서,
    frq: FRQ = FRQ.Y,
) -> dict | list:

    aspx_inner = ASPXInner.c103

    resp = await fetch_financial_json(
        cmp_cd=cmp_cd,
        aspx_inner=aspx_inner,
        rpt=rpt,
        frq=frq,
        encparam=session_info["encparam"],
        cookies=session_info["cookies"],
        referer=session_info["referer"],
        user_agent=session_info["user_agent"],
    )

    return resp

async def get_c104_data(
        *,
        session_info : dict,
        cmp_cd: str = "005930",
        rpt: C104RPT = C104RPT.수익성,
        frq: FRQ = FRQ.Y,
) -> dict | list:

    aspx_inner = ASPXInner.c104

    resp = await fetch_financial_json(
        cmp_cd=cmp_cd,
        aspx_inner=aspx_inner,
        rpt=rpt,
        frq=frq,
        encparam=session_info["encparam"],
        cookies=session_info["cookies"],
        referer=session_info["referer"],
        user_agent=session_info["user_agent"],
    )
    return resp