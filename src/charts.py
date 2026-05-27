# -*- coding: utf-8 -*-
"""圖表建構層（Plotly）。每個函式回傳 plotly Figure，含座標標題、單位與事件標註。"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 路網與政策事件（用於 M1 趨勢標註線）
EVENTS = [
    ("2009-07-01", "文湖線通車"),
    ("2013-11-01", "信義線通車"),
    ("2014-11-01", "松山線通車"),
    ("2020-01-01", "環狀線通車"),
    ("2021-05-01", "COVID 三級警戒"),
    ("2023-07-01", "TPASS 1200 月票"),
]

# 指標 → 座標標題(含單位)
_METRIC_AXIS = {
    "人次": "客運人次（人次）",
    "營收": "客運收入（千元）",
    "客單價": "每人次平均票價（元）",
}
_SMOOTH_LABEL = {"raw": "原始", "ma12": "12 個月移動平均", "yoy": "年增率（%）"}

COLOR_MID = "#f1a340"   # 中運量(文湖線)
COLOR_HIGH = "#4575b4"  # 高運量


def trend_chart(df: pd.DataFrame, metric: str, smoothing: str,
                show_events: bool = True) -> go.Figure:
    """M1 月趨勢折線圖。"""
    ytitle = "年增率（%）" if smoothing == "yoy" else _METRIC_AXIS[metric]
    fig = px.line(df, x="日期", y="數值",
                  title=f"{metric}月趨勢（{_SMOOTH_LABEL[smoothing]}）")
    fig.update_traces(line=dict(width=2), hovertemplate="%{x|%Y-%m}<br>%{y:,.1f}")
    fig.update_layout(xaxis_title="年月", yaxis_title=ytitle, hovermode="x unified")

    if smoothing == "yoy":
        fig.add_hline(y=0, line_dash="dot", line_color="gray")
    if show_events:
        valid = df["日期"].dropna()
        lo, hi = (valid.min(), valid.max()) if len(valid) else (None, None)
        for d, label in EVENTS:
            dt = pd.Timestamp(d)
            if lo is not None and lo <= dt <= hi:
                fig.add_vline(x=dt, line_width=1, line_dash="dash",
                              line_color="rgba(150,150,150,0.7)")
                fig.add_annotation(x=dt, yref="paper", y=1.0, text=label,
                                   showarrow=False, textangle=-90,
                                   font=dict(size=9, color="gray"), xshift=-6)
    return fig


def line_type_chart(df: pd.DataFrame, metric: str, as_pct: bool) -> go.Figure:
    """M2 中運量 vs 高運量 堆疊長條。"""
    long = df.melt(id_vars="西元年", value_vars=["高運量", "中運量"],
                   var_name="運量別", value_name="值")
    ytitle = "貢獻比例（%）" if as_pct else (_METRIC_AXIS[metric])
    fig = px.bar(long, x="西元年", y="值", color="運量別", barmode="stack",
                 color_discrete_map={"中運量": COLOR_MID, "高運量": COLOR_HIGH},
                 title=f"中運量 vs 高運量{metric}{'貢獻比例' if as_pct else '結構'}")
    fig.update_layout(xaxis_title="西元年", yaxis_title=ytitle,
                      legend_title="運量別（中運量＝文湖線）")
    if as_pct:
        fig.update_yaxes(range=[0, 100])
    return fig


def seasonal_chart(df: pd.DataFrame, metric: str) -> go.Figure:
    """M3 各月季節型態（季節指數）。"""
    fig = px.bar(df, x="月", y="季節指數",
                 title=f"淡旺季月型態（季節指數，基於{metric}）")
    fig.add_hline(y=100, line_dash="dot", line_color="gray",
                  annotation_text="全年平均", annotation_position="top left")
    fig.update_layout(xaxis_title="月份", yaxis_title="季節指數（全年平均＝100）")
    fig.update_xaxes(dtick=1)
    return fig


def annual_yoy_chart(df: pd.DataFrame, metric: str) -> go.Figure:
    """M3 年增率長條，標註 SARS / COVID。"""
    fig = px.bar(df.dropna(subset=["年增率"]), x="西元年", y="年增率",
                 title=f"年度{metric}增減率（已排除不完整年）")
    fig.update_traces(marker_color=df["年增率"].apply(
        lambda v: "#d73027" if v < 0 else "#1a9850"))
    fig.add_hline(y=0, line_color="gray")
    notes = {2003: "SARS", 2020: "COVID", 2021: "三級警戒"}
    for yr, label in notes.items():
        row = df[df["西元年"] == yr]
        if not row.empty and pd.notna(row["年增率"].iloc[0]):
            fig.add_annotation(x=yr, y=row["年增率"].iloc[0], text=label,
                               showarrow=True, arrowhead=2, ax=0, ay=-30,
                               font=dict(size=10))
    fig.update_layout(xaxis_title="西元年", yaxis_title="年增率（%）",
                      showlegend=False)
    return fig


def ranking_chart(df: pd.DataFrame, basis: str, year_label: str) -> go.Figure:
    """M4 站點排行 橫向長條。"""
    d = df.sort_values(basis)
    fig = px.bar(d, x=basis, y="站名", orientation="h", text=basis,
                 title=f"{year_label} 捷運站{basis}人流排行（前 {len(df)} 名）")
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(xaxis_title=f"{basis}人次（人次）", yaxis_title="站名")
    return fig


def growth_chart(df: pd.DataFrame, year_label: str) -> go.Figure:
    """M4 成長最快站。"""
    d = df.sort_values("增減率")
    fig = px.bar(d, x="增減率", y="站名", orientation="h", text="增減率",
                 title=f"{year_label} 成長最快的站（進站人次年增率）")
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside",
                      marker_color="#1a9850")
    fig.update_layout(xaxis_title="年增率（%）", yaxis_title="站名")
    return fig


def tidal_chart(df: pd.DataFrame, year_label: str) -> go.Figure:
    """M5 通勤潮汐散點：早晨出發佔比 × 傍晚出發佔比。

    住宅站落在右下（早上多出發、傍晚多抵達）、商業/轉乘站落在左上；
    對角線 y=x 為「早晚方向對稱」，點偏離對角線即代表潮汐反轉。
    顏色為潮汐指數（綠=住宅、紅=商業）、圓點大小為工作日均運量。
    """
    fig = px.scatter(
        df, x="早晨出發佔比", y="傍晚出發佔比", color="潮汐指數",
        hover_name="站名", size="工作日均運量", size_max=30,
        color_continuous_scale="RdYlGn", range_color=[-0.75, 0.75],
        custom_data=["傾向", "工作日均運量"],
        title=f"{year_label} 站點通勤潮汐（早高峰 vs 晚高峰 出發佔比）")
    fig.update_traces(hovertemplate=(
        "<b>%{hovertext}</b><br>早晨出發佔比 %{x:.0%}<br>傍晚出發佔比 %{y:.0%}"
        "<br>傾向：%{customdata[0]}<br>工作日均運量 %{customdata[1]:,.0f}<extra></extra>"))
    fig.add_shape(type="line", x0=0, y0=0, x1=1, y1=1,
                  line=dict(color="gray", dash="dot"))
    fig.add_annotation(x=0.83, y=0.2, text="↘ 住宅傾向<br>(早出發·晚抵達)",
                       showarrow=False, font=dict(size=10, color="#1a9850"))
    fig.add_annotation(x=0.2, y=0.83, text="商業/轉乘傾向 ↖<br>(早抵達·晚出發)",
                       showarrow=False, font=dict(size=10, color="#d73027"))
    fig.update_layout(xaxis_title="早高峰(07–09)出發佔比 = 出發 ÷ (出發+抵達)",
                      yaxis_title="晚高峰(17–19)出發佔比",
                      coloraxis_colorbar_title="潮汐指數")
    fig.update_xaxes(tickformat=".0%", range=[0, 1])
    fig.update_yaxes(tickformat=".0%", range=[0, 1])
    return fig


def tidal_compare_chart(df: pd.DataFrame, year_a: int, year_b: int) -> go.Figure:
    """M5 疫情前後對照散點：x=year_a 潮汐指數、y=year_b 潮汐指數。

    點落在對角線 y=x 代表該站通勤型態在兩年間維持不變（網絡形狀已回復）。
    """
    xa, yb = f"潮汐指數_{year_a}", f"潮汐指數_{year_b}"
    lim = 0.85
    fig = px.scatter(df, x=xa, y=yb, color="變化", hover_name="站名",
                     custom_data=["變化"],
                     color_continuous_scale="RdBu", range_color=[-0.2, 0.2],
                     title=f"通勤潮汐：{year_a}（疫情前）vs {year_b} 對照")
    fig.update_traces(hovertemplate=(
        f"<b>%{{hovertext}}</b><br>{year_a} 潮汐指數 %{{x:.3f}}"
        f"<br>{year_b} 潮汐指數 %{{y:.3f}}"
        "<br>變化 %{customdata[0]:+.3f}<extra></extra>"))
    fig.add_shape(type="line", x0=-lim, y0=-lim, x1=lim, y1=lim,
                  line=dict(color="gray", dash="dot"))
    fig.add_hline(y=0, line_color="rgba(150,150,150,0.5)")
    fig.add_vline(x=0, line_color="rgba(150,150,150,0.5)")
    fig.update_layout(xaxis_title=f"{year_a} 潮汐指數（>0 住宅、<0 商業）",
                      yaxis_title=f"{year_b} 潮汐指數",
                      coloraxis_colorbar_title=f"變化<br>({year_b}−{year_a})")
    fig.update_xaxes(range=[-lim, lim])
    fig.update_yaxes(range=[-lim, lim])
    return fig
