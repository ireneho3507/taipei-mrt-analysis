# -*- coding: utf-8 -*-
"""分析計算層（純函式，輸入為 data_loader 產生的 DataFrame）。

對應藍圖的五個分析模組：
  M1 月趨勢 / 年趨勢      monthly_trend, annual_total, annual_yoy
  M2 運量結構（中/高）    line_type_share
  M3 季節型態             seasonal_pattern
  M4 站點排行 / 成長       station_ranking, station_growth
  M5 通勤潮汐             commuter_tidal
"""
from __future__ import annotations

import pandas as pd

from . import data_loader as dl

# 指標 → 客運概況欄位對照
METRIC_COLUMNS = {
    "人次": dl.COL_RIDERS_TOTAL,
    "營收": dl.COL_REV_TOTAL,
    "客單價": "客單價_總",
}


# ---------- M1 趨勢 ----------
def monthly_trend(overview: pd.DataFrame, metric: str = "人次",
                  smoothing: str = "raw") -> pd.DataFrame:
    """月趨勢。smoothing: 'raw' 原始 / 'ma12' 12 月移動平均 / 'yoy' 年增率(%)。"""
    if metric not in METRIC_COLUMNS:
        raise ValueError(f"未知指標：{metric}")
    col = METRIC_COLUMNS[metric]
    out = overview[["日期", "西元年", "月", "完整年", col]].copy()
    out = out.rename(columns={col: "數值"}).sort_values("日期")

    if smoothing == "ma12":
        out["數值"] = out["數值"].rolling(12, min_periods=12).mean()
    elif smoothing == "yoy":
        out["數值"] = out["數值"].pct_change(12) * 100
    elif smoothing != "raw":
        raise ValueError(f"未知平滑方式：{smoothing}")
    return out.reset_index(drop=True)


def annual_total(overview: pd.DataFrame, metric: str = "人次",
                 exclude_partial: bool = True) -> pd.DataFrame:
    """年度彙總。人次/營收採加總；客單價採當年加權平均(總收入/總人次)。"""
    df = overview[overview["完整年"]] if exclude_partial else overview
    if metric == "客單價":
        g = df.groupby("西元年").apply(
            lambda x: x[dl.COL_REV_TOTAL].sum() * 1000 / x[dl.COL_RIDERS_TOTAL].sum(),
            include_groups=False,
        )
        out = g.rename("數值").reset_index()
    else:
        col = METRIC_COLUMNS[metric]
        out = df.groupby("西元年")[col].sum().rename("數值").reset_index()
    return out.sort_values("西元年").reset_index(drop=True)


def annual_yoy(overview: pd.DataFrame, metric: str = "人次",
               exclude_partial: bool = True) -> pd.DataFrame:
    """年增率(%)。預設排除不完整年(如僅 3 個月的 2026)以免假性崩跌。"""
    out = annual_total(overview, metric, exclude_partial)
    out["年增率"] = out["數值"].pct_change() * 100
    return out


# ---------- M2 運量結構 ----------
def line_type_share(overview: pd.DataFrame, metric: str = "人次",
                    as_pct: bool = True) -> pd.DataFrame:
    """各年中運量 vs 高運量的貢獻。metric: '人次' 或 '營收'。"""
    if metric == "人次":
        mid_c, high_c = dl.COL_RIDERS_MID, dl.COL_RIDERS_HIGH
    elif metric == "營收":
        mid_c, high_c = dl.COL_REV_MID, dl.COL_REV_HIGH
    else:
        raise ValueError("運量結構僅支援 '人次' 或 '營收'")
    g = overview.groupby("西元年").agg(中運量=(mid_c, "sum"),
                                       高運量=(high_c, "sum")).reset_index()
    if as_pct:
        total = g["中運量"] + g["高運量"]
        g["中運量"] = g["中運量"] / total * 100
        g["高運量"] = g["高運量"] / total * 100
    return g


# ---------- M3 季節型態 ----------
def seasonal_pattern(overview: pd.DataFrame, metric: str = "平均每日",
                     years: tuple[int, int] | None = None) -> pd.DataFrame:
    """各月型態（跨年平均）。metric '平均每日' 去除月天數干擾；亦提供季節指數。

    回傳欄位：月、平均值、季節指數(該月平均 ÷ 全月總平均 × 100)。
    """
    col = dl.COL_DAILY_AVG if metric == "平均每日" else dl.COL_RIDERS_TOTAL
    df = overview
    if years:
        df = df[(df["西元年"] >= years[0]) & (df["西元年"] <= years[1])]
    g = df.groupby("月")[col].mean().rename("平均值").reset_index()
    g["季節指數"] = g["平均值"] / g["平均值"].mean() * 100
    return g


# ---------- M4 站點排行 / 成長 ----------
def _year_label(year) -> str:
    """接受西元年(int)或統計期字串，回傳檔內統計期字串(如 '114年')。"""
    if isinstance(year, str):
        return year
    return f"{year - 1911}年"


def _select_year(stations: pd.DataFrame, year) -> pd.DataFrame:
    if isinstance(year, str):
        return stations[stations["統計期"] == year].copy()
    return stations[stations["西元年"] == year].copy()


def station_ranking(stations: pd.DataFrame, year, basis: str = "進站",
                    merge_gates: bool = True, top_n: int = 10) -> pd.DataFrame:
    """站點人流排行。

    basis: '進站' / '出站' / '進出合計'
    merge_gates: True 時把同站不同路線閘門(如 台北車站R+BL)合併。
    """
    df = _select_year(stations, year)
    df = df[(df[dl.COL_ENTRY] > 0) | (df[dl.COL_EXIT] > 0)]

    name_col = "基底站名" if merge_gates else dl.COL_STATION
    g = df.groupby(name_col).agg(進站=(dl.COL_ENTRY, "sum"),
                                 出站=(dl.COL_EXIT, "sum")).reset_index()
    g = g.rename(columns={name_col: "站名"})
    g["進出合計"] = g["進站"] + g["出站"]

    if basis not in ("進站", "出站", "進出合計"):
        raise ValueError(f"未知排序基準：{basis}")
    g = g.sort_values(basis, ascending=False).reset_index(drop=True)
    g.insert(0, "名次", g.index + 1)
    return g.head(top_n) if top_n else g


def station_growth(stations: pd.DataFrame, year, basis: str = "進站",
                   merge_gates: bool = True, min_volume: int = 0,
                   top_n: int = 10) -> pd.DataFrame:
    """成長最快的站（依當年人次相對前一年的增減率）。

    合併閘門時，以基底站名重算 YoY（前一年同站合併量為基準），避免閘門級雜訊。
    """
    cur = _select_year(stations, year)
    if isinstance(year, str):
        prev_year = int(year.replace("年", "")) - 1
        prev = stations[stations["民國年"] == prev_year].copy()
    else:
        prev = stations[stations["西元年"] == year - 1].copy()

    name_col = "基底站名" if merge_gates else dl.COL_STATION
    metric_col = dl.COL_ENTRY if basis == "進站" else dl.COL_EXIT

    cur_g = cur.groupby(name_col)[metric_col].sum().rename("本期")
    prev_g = prev.groupby(name_col)[metric_col].sum().rename("前期")
    m = pd.concat([cur_g, prev_g], axis=1).reset_index()
    m = m.rename(columns={name_col: "站名"})
    m = m[(m["前期"] >= min_volume) & (m["前期"] > 0)]
    m["增減率"] = (m["本期"] - m["前期"]) / m["前期"] * 100
    m = m.sort_values("增減率", ascending=False).reset_index(drop=True)
    return m.head(top_n) if top_n else m


# ---------- M5 通勤潮汐 ----------
def commuter_tidal(stations: pd.DataFrame, year, merge_gates: bool = True,
                   min_volume: int = 0) -> pd.DataFrame:
    """進出站不平衡 → 住宅型 vs 商業型分類。

    進出比 = 進站 ÷ 出站。>1.05 住宅型(淨流出)、<0.95 商業/轉乘型(淨流入)、其餘均衡。
    min_volume：以進站量過濾小站雜訊。
    """
    df = _select_year(stations, year)
    name_col = "基底站名" if merge_gates else dl.COL_STATION
    g = df.groupby(name_col).agg(進站=(dl.COL_ENTRY, "sum"),
                                 出站=(dl.COL_EXIT, "sum")).reset_index()
    g = g.rename(columns={name_col: "站名"})
    g = g[(g["進站"] >= min_volume) & (g["出站"] > 0)]
    g["進出比"] = g["進站"] / g["出站"]
    g["類型"] = pd.cut(g["進出比"], bins=[0, 0.95, 1.05, float("inf")],
                       labels=["商業/轉乘型", "均衡型", "住宅型"])
    return g.sort_values("進出比", ascending=False).reset_index(drop=True)
