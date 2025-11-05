# scraper2_hj3415/core/constants.py

from enum import StrEnum

class PAGE(StrEnum):
    c101 = "c1010001.aspx"
    c103 = "c1030001.aspx"
    c104 = "c1040001.aspx"

PAGE_TO_LABEL = {
    PAGE.c101: "c101",
    PAGE.c103: "c103",
    PAGE.c104: "c104"
}

class ASPXInner(StrEnum):
    c103 = "cF3002.aspx"
    c104 = "cF4002.aspx"

class FRQ(StrEnum):
    Y = "0"   # 연간
    Q = "1"   # 분기

FRQ_TO_LABEL = {FRQ.Y: "y", FRQ.Q: "q"}   # 저장·로그용 라벨

class C103RPT(StrEnum):
    손익계산서 = "0"
    재무상태표 = "1"
    현금흐름표 = "2"

class C104RPT(StrEnum):
    수익성 = "1"
    성장성 = "2"
    안정성 = "3"
    활동성 = "4"
    가치분석 = "5"

RPT_TO_LABEL = {
    C103RPT.손익계산서: "손익계산서",
    C103RPT.재무상태표: "재무상태표",
    C103RPT.현금흐름표: "현금흐름표",
    C104RPT.수익성: "수익성",
    C104RPT.성장성: "성장성",
    C104RPT.안정성: "안정성",
    C104RPT.활동성: "활동성",
    C104RPT.가치분석: "가치분석",
}
