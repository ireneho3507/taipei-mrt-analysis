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


# 分群類型 → 顏色（紅=偏商業/轉乘、綠=偏住宅、灰/藍橘=中間）
_CLUSTER_COLORS = {
    "住宅傾向": "#1a9850",
    "均衡偏住": "#74add1",
    "均衡型": "#999999",
    "均衡偏商": "#fdae61",
    "商業/轉乘傾向": "#d73027",
}


def cluster_chart(df: pd.DataFrame, year_label: str) -> go.Figure:
    """M5 通勤潮汐散點：進站量 × 進出比，依 k-means 資料驅動分群上色。"""
    fig = px.scatter(df, x="進站", y="進出比", color="類型",
                     hover_name="站名", size="進出合計", size_max=28,
                     color_discrete_map=_CLUSTER_COLORS,
                     title=f"{year_label} 站點通勤潮汐 k-means 分群（進出比＝進站÷出站）")
    fig.add_hline(y=1.0, line_dash="dot", line_color="gray",
                  annotation_text="進出平衡", annotation_position="bottom right")
    fig.update_layout(xaxis_title="進站人次（人次，圓點大小＝進出合計）",
                      yaxis_title="進出比（>1 偏住宅，<1 偏商業）",
                      legend_title="資料驅動分群")
    return fig
