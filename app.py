# -*- coding: utf-8 -*-
"""臺北捷運運量分析 — Streamlit 互動網站。

五個分析分頁（M1 趨勢 / M2 運量結構 / M3 季節與崩跌 / M4 站點排行 / M5 通勤潮汐）。
M5 採每日分時 OD 流量（離線聚合的 2019-11、2025-11 代表月）。
資料來源：data.gov.tw / data.taipei → 臺北大眾捷運公司。
"""
import streamlit as st

from src import analysis as an
from src import charts
from src import data_loader as dl

st.set_page_config(page_title="臺北捷運運量分析", page_icon="🚇", layout="wide")


@st.cache_data
def get_overview():
    return dl.load_overview()


@st.cache_data
def get_stations():
    return dl.load_stations()


@st.cache_data
def get_tidal():
    return dl.load_tidal()


@st.cache_data
def get_raw_csv(filename: str) -> bytes:
    """讀取 data/ 原始 CSV 位元組（保留 UTF-8-BOM 編碼）供下載。"""
    return (dl.DATA_DIR / filename).read_bytes()


overview = get_overview()
stations = get_stations()
tidal = get_tidal()

OV_YEARS = (int(overview["西元年"].min()), int(overview["西元年"].max()))
ST_YEARS = (int(stations["西元年"].min()), int(stations["西元年"].max()))
TIDAL_YEARS = sorted(tidal["西元年"].unique())  # 代表月：疫情前 2019、近期 2025


st.title("🚇 臺北捷運運量分析")
st.caption("資料來源：政府開放資料平台（data.gov.tw）／臺北大眾捷運股份有限公司")

with st.expander("📥 下載原始開放資料（CSV）"):
    st.caption("本站分析所用的兩份原始檔，皆為政府開放資料，歡迎下載核對。")
    d1, d2 = st.columns(2)
    d1.download_button(
        "客運概況（月）CSV",
        get_raw_csv(dl.OVERVIEW_FILE),
        file_name=dl.OVERVIEW_FILE,
        mime="text/csv",
        key="dl_overview",
    )
    d2.download_button(
        "各站進出站（年）CSV",
        get_raw_csv(dl.STATIONS_FILE),
        file_name=dl.STATIONS_FILE,
        mime="text/csv",
        key="dl_stations",
    )

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 歷史趨勢", "🧩 運量結構", "🗓️ 季節與崩跌", "🏆 站點排行", "🌗 通勤潮汐"]
)

# ---------- M1 歷史趨勢 ----------
with tab1:
    st.subheader("人次與營收的歷史趨勢")
    c1, c2, c3 = st.columns(3)
    metric = c1.selectbox("指標", ["人次", "營收", "客單價"], key="m1_metric")
    smoothing = c2.radio("平滑方式", ["raw", "ma12", "yoy"],
                         format_func=lambda x: charts._SMOOTH_LABEL[x], key="m1_smooth")
    show_events = c3.checkbox("顯示路網/政策事件標註", value=True, key="m1_events")
    yr = st.slider("年份範圍", *OV_YEARS, value=OV_YEARS, key="m1_yr")

    trend = an.monthly_trend(overview, metric, smoothing)  # 全序列算平滑
    trend = trend[(trend["西元年"] >= yr[0]) & (trend["西元年"] <= yr[1])]
    st.plotly_chart(charts.trend_chart(trend, metric, smoothing, show_events),
                    width="stretch")
    st.caption("提示：原始月資料含季節波動，建議搭配「12 個月移動平均」看長期趨勢；"
               "「客單價」＝收入÷人次，可看出票價政策影響。2026 為不完整年。")

# ---------- M2 運量結構 ----------
with tab2:
    st.subheader("中運量（文湖線）vs 高運量 貢獻")
    c1, c2 = st.columns(2)
    metric2 = c1.radio("指標", ["人次", "營收"], horizontal=True, key="m2_metric")
    as_pct = c2.checkbox("以百分比（100% 堆疊）顯示", value=True, key="m2_pct")
    yr2 = st.slider("年份範圍", *OV_YEARS, value=OV_YEARS, key="m2_yr")

    ov2 = overview[(overview["西元年"] >= yr2[0]) & (overview["西元年"] <= yr2[1])]
    share = an.line_type_share(ov2, metric2, as_pct)
    st.plotly_chart(charts.line_type_chart(share, metric2, as_pct),
                    width="stretch")
    st.caption("中運量＝文湖線（膠輪），高運量＝其餘重運量路線。"
               "文湖線人次佔比約 9.5%，其**收入佔比高於人次佔比**（每人次票價較高），"
               "但總量仍遠小於高運量。"
               "※ 切換『營收』時 2005–2007 為空白：開放資料該三年未提供分車種收入。")

# ---------- M3 季節與崩跌 ----------
with tab3:
    st.subheader("淡旺季（月）與運量崩跌（年）")
    c1, c2 = st.columns(2)
    smetric = c1.radio("季節分析指標", ["平均每日", "總人次"], horizontal=True, key="m3_metric")
    yr3 = c2.slider("季節分析年份範圍", *OV_YEARS, value=(2015, 2019), key="m3_yr")
    seas = an.seasonal_pattern(overview, smetric, years=yr3)
    st.plotly_chart(charts.seasonal_chart(seas, smetric), width="stretch")
    st.caption("採『平均每日客運人次』可去除各月天數差異；2 月常因春節與天數少而為淡季低谷。")

    st.markdown("---")
    yoy = an.annual_yoy(overview, "人次", exclude_partial=True)
    st.plotly_chart(charts.annual_yoy_chart(yoy, "人次"), width="stretch")
    st.caption("年增率已排除不完整年（2026）。可見 SARS（2003）與 COVID（2020–2021）兩波崩跌。")

# ---------- M4 站點排行 ----------
with tab4:
    st.subheader("捷運站點人流排行")
    c1, c2, c3, c4 = st.columns(4)
    yr4 = c1.slider("年份", ST_YEARS[0] + 1, ST_YEARS[1], value=ST_YEARS[1], key="m4_yr")
    basis = c2.radio("排序基準", ["進站", "出站", "進出合計"], key="m4_basis")
    merge = c3.checkbox("合併同站不同閘門", value=True, key="m4_merge")
    topn = c4.slider("顯示前 N 名", 5, 20, 10, key="m4_topn")

    rank = an.station_ranking(stations, yr4, basis, merge_gates=merge, top_n=topn)
    st.plotly_chart(charts.ranking_chart(rank, basis, f"{yr4}"), width="stretch")
    if merge:
        st.caption("已合併同站不同路線閘門（如 台北車站R＋BL）。關閉合併會把轉乘站拆開、低估其排名。")
    else:
        st.caption("⚠️ 未合併閘門：台北車站被拆成 R／BL 兩筆，排名會被低估。")

    st.markdown("---")
    growth = an.station_growth(stations, yr4, "進站", merge_gates=merge,
                               min_volume=1_000_000, top_n=10)
    st.plotly_chart(charts.growth_chart(growth, f"{yr4}"), width="stretch")
    st.caption("成長最快的站（前一年進站量 ≥ 100 萬，排除新開站的暴增雜訊）。")

# ---------- M5 通勤潮汐（OD 分時方向流） ----------
with tab5:
    st.subheader("站點通勤潮汐：早晚高峰的方向流（每日分時 OD）")
    c1, c2 = st.columns(2)
    yr5 = c1.radio("代表月份", TIDAL_YEARS, horizontal=True,
                   format_func=lambda y: f"{y} 年 11 月"
                   + ("（疫情前）" if y == 2019 else "（近期）"), key="m5_yr")
    minv = c2.select_slider(
        "最少工作日均運量（過濾小站雜訊）",
        options=[0, 2_000, 5_000, 10_000, 20_000], value=5_000, key="m5_minv")

    td = an.commuter_tidal(tidal, yr5, min_volume=minv)
    st.plotly_chart(charts.tidal_chart(td, f"{yr5} 年 11 月"), width="stretch")

    cc1, cc2 = st.columns(2)
    cc1.markdown("**最住宅傾向（早出發·晚回家）**")
    cc1.dataframe(td.head(6)[["站名", "早晨出發佔比", "傍晚出發佔比", "潮汐指數"]]
                  .style.format({"早晨出發佔比": "{:.0%}", "傍晚出發佔比": "{:.0%}",
                                 "潮汐指數": "{:+.3f}"}), hide_index=True)
    cc2.markdown("**最商業/轉乘傾向（早抵達·晚離開）**")
    cc2.dataframe(td.tail(6).iloc[::-1][["站名", "早晨出發佔比", "傍晚出發佔比", "潮汐指數"]]
                  .style.format({"早晨出發佔比": "{:.0%}", "傍晚出發佔比": "{:.0%}",
                                 "潮汐指數": "{:+.3f}"}), hide_index=True)
    st.caption(
        "**潮汐指數 = 早高峰(07–09)出發佔比 − 晚高峰(17–19)出發佔比。** "
        "住宅站早上大量「出發」、傍晚大量「抵達」回家（指數>0）；商業/轉乘站相反（<0）。"
        "因為分早、晚兩個獨立時間窗看『方向』，**不會被同站早晚來回抵消**——"
        "這是用站對站 OD 流量、而非年進出總量，才量得到的真實通勤潮汐。"
        "僅計工作日（排除週末）。")

    # 疫情前後對照（兩年皆有的站）
    if len(TIDAL_YEARS) >= 2:
        st.markdown("---")
        st.markdown("##### 疫情前後對照：通勤型態回復了嗎？")
        ya, yb = TIDAL_YEARS[0], TIDAL_YEARS[-1]
        cmp = an.tidal_compare(tidal, ya, yb, min_volume=minv)
        st.plotly_chart(charts.tidal_compare_chart(cmp, ya, yb), width="stretch")
        st.caption(
            f"點落在對角線 = 該站 {ya}↔{yb} 通勤型態不變（網絡形狀已回復）。"
            f"住宅站(右上)與商業站(左下)兩群在 {yb} 依然分明，"
            "顯示通勤潮汐的空間結構在疫情後大致回到原樣。")
