# -*- coding: utf-8 -*-
"""資料載入與清理層。

兩份臺北捷運開放資料（皆 UTF-8 with BOM）：
  - 客運概況（月 × 全系統）：載入後解析年/月、標記完整年、計算客單價。
  - 各站進出站（年 × 站）：載入後解析年、擷取路線後綴、產生可合併閘門的基底站名。

本模組僅依賴 pandas（不 import streamlit），以便單元測試與重用；
app 端再以 st.cache_data 包裝快取。
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OVERVIEW_FILE = "臺北市捷運客運概況按月別.csv"
STATIONS_FILE = "臺北市捷運各站進出站人次_年別.csv"

# 客運概況欄位常數
COL_RIDERS_TOTAL = "客運人次/總計[人次]"
COL_RIDERS_MID = "客運人次/中運量[人次]"
COL_RIDERS_HIGH = "客運人次/高運量[人次]"
COL_DAILY_AVG = "平均每日客運人次[人次]"
COL_REV_TOTAL = "客運收入/總計[千元]"
COL_REV_MID = "客運收入/中運量[千元]"
COL_REV_HIGH = "客運收入/高運量[千元]"

# 各站進出站欄位常數
COL_STATION = "捷運站別"
COL_ENTRY = "進站人次"
COL_EXIT = "出站人次"
COL_ENTRY_YOY = "進站人次增減率[%]"
COL_EXIT_YOY = "出站人次增減率[%]"

_ROC_MONTH_RE = re.compile(r"\s*(\d+)\s*年\s*(\d+)\s*月")
_ROC_YEAR_RE = re.compile(r"\s*(\d+)\s*年")
_SUFFIX_RE = re.compile(r"[A-Za-z]+$")


def _roc_to_ad(roc_year: int) -> int:
    """民國年 → 西元年。"""
    return roc_year + 1911


def load_overview(path: str | Path | None = None) -> pd.DataFrame:
    """載入客運概況（月）並加上解析欄位與客單價。

    新增欄位：民國年、西元年、月、日期(當月 1 日)、完整年(該年是否有 12 個月)、
              客單價_總/中/高(元/人次)。
    """
    path = Path(path) if path else DATA_DIR / OVERVIEW_FILE
    df = pd.read_csv(path, encoding="utf-8-sig")

    parsed = df["統計期"].str.extract(_ROC_MONTH_RE)
    df["民國年"] = parsed[0].astype(int)
    df["月"] = parsed[1].astype(int)
    df["西元年"] = df["民國年"].map(_roc_to_ad)
    df["日期"] = pd.to_datetime(
        dict(year=df["西元年"], month=df["月"], day=1)
    )

    months_per_year = df.groupby("西元年")["月"].transform("count")
    df["完整年"] = months_per_year.eq(12)

    # 客單價（元/人次）= 收入(千元) × 1000 ÷ 人次；人次為 0 時設為 NaN
    df["客單價_總"] = _fare(df[COL_REV_TOTAL], df[COL_RIDERS_TOTAL])
    df["客單價_中運量"] = _fare(df[COL_REV_MID], df[COL_RIDERS_MID])
    df["客單價_高運量"] = _fare(df[COL_REV_HIGH], df[COL_RIDERS_HIGH])

    return df.sort_values("日期").reset_index(drop=True)


def _fare(revenue_kntd: pd.Series, riders: pd.Series) -> pd.Series:
    """收入(千元)、人次 → 每人次平均票價(元)。"""
    return (revenue_kntd * 1000 / riders).where(riders > 0)


def load_stations(path: str | Path | None = None) -> pd.DataFrame:
    """載入各站進出站（年）並加上解析欄位。

    新增欄位：民國年、西元年、路線後綴(無則為空字串)、基底站名(去除後綴，供合併閘門)。
    """
    path = Path(path) if path else DATA_DIR / STATIONS_FILE
    df = pd.read_csv(path, encoding="utf-8-sig")

    df["民國年"] = df["統計期"].str.extract(_ROC_YEAR_RE)[0].astype(int)
    df["西元年"] = df["民國年"].map(_roc_to_ad)
    df["路線後綴"] = df[COL_STATION].str.extract(r"([A-Za-z]+)$")[0].fillna("")
    df["基底站名"] = df[COL_STATION].str.replace(_SUFFIX_RE, "", regex=True)

    return df.reset_index(drop=True)
