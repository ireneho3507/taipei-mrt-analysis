# -*- coding: utf-8 -*-
"""分析計算層（純函式，輸入為 data_loader 產生的 DataFrame）。

對應藍圖的五個分析模組：
  M1 月趨勢 / 年趨勢      monthly_trend, annual_total, annual_yoy
  M2 運量結構（中/高）    line_type_share
  M3 季節型態             seasonal_pattern
  M4 站點排行 / 成長       station_ranking, station_growth
  M5 通勤潮汐             commuter_tidal, tidal_compare
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


# ---------- M5 通勤潮汐（OD 分時方向流） ----------
def _tidency(tidal_index: float) -> str:
    """依潮汐指數正負給傾向標籤。0 是有意義的樞紐（早晚出發佔比相等），非人為門檻。"""
    return "住宅傾向" if tidal_index > 0 else "商業/轉乘傾向"


def commuter_tidal(tidal: pd.DataFrame, year: int, min_volume: int = 0,
                   top_n: int | None = None) -> pd.DataFrame:
    """單一年度各站的通勤潮汐（來自每日分時 OD）。

    潮汐指數 = 早晨出發佔比 − 傍晚出發佔比。早高峰(07-09)以「出發」為主、
    晚高峰(17-19)以「抵達」為主者為住宅傾向(指數>0)；反之為商業/轉乘傾向。
    此為分時方向的實測差，不會被「同站早晚來回」抵消（早晚為各自的時間窗）。

    min_volume 以工作日均運量過濾小站雜訊；top_n 取絕對排序前 N。
    回傳依潮汐指數遞減排序，附「傾向」欄。
    """
    df = tidal[tidal["西元年"] == year].copy()
    df = df[df["工作日均運量"] >= min_volume]
    if df.empty:
        raise ValueError(f"{year} 年無符合條件（min_volume={min_volume}）的站點")
    df["傾向"] = df["潮汐指數"].map(_tidency)
    df = df.sort_values("潮汐指數", ascending=False).reset_index(drop=True)
    return df.head(top_n) if top_n else df


def tidal_compare(tidal: pd.DataFrame, year_a: int, year_b: int,
                  min_volume: int = 0) -> pd.DataFrame:
    """兩年度潮汐指數對照（疫情前 vs 後），僅取兩年皆有的站。

    回傳欄位：站名、潮汐指數_{a}、潮汐指數_{b}、變化(=b−a)、
              工作日均運量_{b}、傾向_{b}。依年 b 的潮汐指數遞減排序。
    """
    a = commuter_tidal(tidal, year_a, min_volume)[["站名", "潮汐指數"]]
    b = commuter_tidal(tidal, year_b, min_volume)[
        ["站名", "潮汐指數", "工作日均運量", "傾向"]]
    m = a.merge(b, on="站名", suffixes=(f"_{year_a}", f"_{year_b}"))
    m = m.rename(columns={"工作日均運量": f"工作日均運量_{year_b}",
                          "傾向": f"傾向_{year_b}"})
    m["變化"] = m[f"潮汐指數_{year_b}"] - m[f"潮汐指數_{year_a}"]
    return m.sort_values(f"潮汐指數_{year_b}", ascending=False).reset_index(drop=True)
