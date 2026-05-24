# -*- coding: utf-8 -*-
"""資料載入層測試。"""
import pandas as pd
import pytest

from src import data_loader as dl


@pytest.fixture(scope="module")
def overview():
    return dl.load_overview()


@pytest.fixture(scope="module")
def stations():
    return dl.load_stations()


# ---------- 客運概況 ----------
def test_overview_parsed_columns(overview):
    for c in ["民國年", "西元年", "月", "日期", "完整年",
              "客單價_總", "客單價_中運量", "客單價_高運量"]:
        assert c in overview.columns


def test_overview_year_month_parse(overview):
    # 第一筆應為 87年 1月 → 西元 1998
    first = overview.iloc[0]
    assert first["西元年"] == 1998
    assert first["月"] == 1
    assert overview["月"].between(1, 12).all()


def test_overview_partial_year_flag(overview):
    # 2019 為完整年(12 個月)、2026 僅 3 個月應標為不完整
    assert overview.loc[overview["西元年"] == 2019, "完整年"].all()
    assert not overview.loc[overview["西元年"] == 2026, "完整年"].any()
    assert (overview[overview["西元年"] == 2026]["月"].max()) == 3


def test_overview_fare_positive(overview):
    fares = overview["客單價_總"].dropna()
    assert (fares > 0).all()
    # 合理區間：單程票價約 20~35 元
    assert fares.between(15, 40).mean() > 0.8


# ---------- 各站進出站 ----------
def test_stations_parsed_columns(stations):
    for c in ["民國年", "西元年", "路線後綴", "基底站名"]:
        assert c in stations.columns


def test_stations_year_range(stations):
    assert stations["西元年"].min() == 1996  # 85年
    assert stations["西元年"].max() == 2025  # 114年


def test_gate_base_name_merge(stations):
    # 台北車站R / 台北車站BL → 基底站名皆為 台北車站
    names = stations["捷運站別"]
    tp = stations[names.str.contains("台北車站")]
    assert set(tp["基底站名"].unique()) == {"台北車站"}
    # 無後綴站基底名不變
    row = stations[stations["捷運站別"] == "西門"].iloc[0]
    assert row["基底站名"] == "西門"
    assert row["路線後綴"] == ""


def test_suffix_extracted(stations):
    row = stations[stations["捷運站別"] == "台北車站R"].iloc[0]
    assert row["路線後綴"] == "R"
