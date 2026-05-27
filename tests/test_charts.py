# -*- coding: utf-8 -*-
"""圖表層回歸測試（聚焦容易出錯的資料↔視覺對齊）。"""
import pytest

from src import analysis as an
from src import charts
from src import data_loader as dl


@pytest.fixture(scope="module")
def overview():
    return dl.load_overview()


def test_annual_yoy_chart_colors_align_with_negative_years(overview):
    """年增率長條的顏色必須與長條對齊：負成長紅、其餘綠。

    回歸：曾用含 NaN 首列的完整 df 算顏色、卻用 dropna 後的 df 畫長條，
    造成顏色錯位一格（紅色標到 2004/2021/2022 而非 2003/2020/2021）。
    """
    yoy = an.annual_yoy(overview, "人次")
    fig = charts.annual_yoy_chart(yoy, "人次")
    d = yoy.dropna(subset=["年增率"]).reset_index(drop=True)

    colors = list(fig.data[0].marker.color)
    assert len(colors) == len(d)  # 顏色數＝長條數，無錯位
    for i, row in d.iterrows():
        expected = "#d73027" if row["年增率"] < 0 else "#1a9850"
        assert colors[i] == expected, (row["西元年"], row["年增率"], colors[i])

    # 具體三次崩跌年必須是紅色
    for yr in (2003, 2020, 2021):
        idx = int(d.index[d["西元年"] == yr][0])
        assert colors[idx] == "#d73027"
