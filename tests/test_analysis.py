# -*- coding: utf-8 -*-
"""分析計算層測試。"""
import pytest

from src import analysis as an
from src import data_loader as dl


@pytest.fixture(scope="module")
def overview():
    return dl.load_overview()


@pytest.fixture(scope="module")
def stations():
    return dl.load_stations()


# ---------- M1 趨勢 ----------
def test_monthly_trend_smoothing(overview):
    raw = an.monthly_trend(overview, "人次", "raw")
    ma = an.monthly_trend(overview, "人次", "ma12")
    yoy = an.monthly_trend(overview, "人次", "yoy")
    assert len(raw) == len(overview)
    # 前 11 筆 MA12 應為 NaN（不足 12 期）
    assert ma["數值"].iloc[:11].isna().all()
    assert ma["數值"].iloc[11:].notna().any()
    # YoY 為百分比，前 12 筆為 NaN
    assert yoy["數值"].iloc[:12].isna().all()


def test_annual_yoy_excludes_partial(overview):
    yoy = an.annual_yoy(overview, "人次", exclude_partial=True)
    # 2026 不完整年應被排除，故最大年為 2025
    assert yoy["西元年"].max() == 2025
    # COVID：2021 應為明顯負成長
    v2021 = yoy.loc[yoy["西元年"] == 2021, "年增率"].iloc[0]
    assert v2021 < -15


def test_invalid_metric_raises(overview):
    with pytest.raises(ValueError):
        an.monthly_trend(overview, "不存在的指標")


# ---------- M2 運量結構 ----------
def test_line_type_share_pct_sums_100(overview):
    share = an.line_type_share(overview, "人次", as_pct=True)
    s = share["中運量"] + share["高運量"]
    assert (s.round(6) == 100).all()
    # 高運量應遠大於中運量
    assert (share["高運量"] > share["中運量"]).all()


# ---------- M3 季節型態 ----------
def test_seasonal_pattern(overview):
    s = an.seasonal_pattern(overview, "平均每日")
    assert len(s) == 12
    # 季節指數平均應約等於 100
    assert abs(s["季節指數"].mean() - 100) < 1e-6
    # 2 月(春節/天數少)通常為淡季低谷
    assert s.loc[s["月"] == 2, "季節指數"].iloc[0] < 100


# ---------- M4 排行 ----------
def test_ranking_merge_gates_taipei_main_tops(stations):
    """合併閘門後台北車站應勝過西門；不合併則台北車站被拆而落後。"""
    merged = an.station_ranking(stations, 2025, "進站", merge_gates=True, top_n=5)
    assert merged.iloc[0]["站名"] == "台北車站"
    ximen = merged.loc[merged["站名"] == "西門", "進站"].iloc[0]
    assert merged.iloc[0]["進站"] > ximen

    unmerged = an.station_ranking(stations, 2025, "進站", merge_gates=False, top_n=5)
    # 不合併時榜上不會出現合併名「台北車站」，而是分開的閘門名
    assert "台北車站" not in set(unmerged["站名"])


def test_ranking_accepts_roc_string(stations):
    by_int = an.station_ranking(stations, 2025, "進站", top_n=3)
    by_str = an.station_ranking(stations, "114年", "進站", top_n=3)
    assert list(by_int["站名"]) == list(by_str["站名"])


def test_station_growth(stations):
    g = an.station_growth(stations, 2025, "進站", top_n=10)
    assert "增減率" in g.columns
    assert g["增減率"].is_monotonic_decreasing


# ---------- M5 通勤潮汐 ----------
def test_commuter_tidal(stations):
    t = an.commuter_tidal(stations, 2025, merge_gates=True, min_volume=1_000_000)
    assert (t["進出比"] > 0).all()
    assert set(t["類型"].dropna().unique()) <= {"商業/轉乘型", "均衡型", "住宅型"}
    # 進出比排序遞減
    assert t["進出比"].is_monotonic_decreasing
