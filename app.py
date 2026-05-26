# -*- coding: utf-8 -*-
"""臺北捷運運量分析 — Streamlit 互動網站。

五個分析分頁（M1 趨勢 / M2 運量結構 / M3 季節與崩跌 / M4 站點排行 / M5 通勤潮汐）。
資料來源：data.gov.tw → 臺北大眾捷運公司。
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
def get_raw_csv(filename: str) -> bytes:
    """讀取 data/ 原始 CSV 位元組（保留 UTF-8-BOM 編碼）供下載。"""
    return (dl.DATA_DIR / filename).read_bytes()


overview = get_overview()
stations = get_stations()

OV_YEARS = (int(overview["西元年"].min()), int(overview["西元年"].max()))
ST_YEARS = (int(stations["西元年"].min()), int(stations["西元年"].max()))


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

# ---------- M5 通勤潮汐 ----------
with tab5:
    st.subheader("站點通勤潮汐：住宅型 vs 商業型")
    c1, c2, c3 = st.columns(3)
    yr5 = c1.slider("年份", *ST_YEARS, value=ST_YEARS[1], key="m5_yr")
    merge5 = c2.checkbox("合併同站不同閘門", value=True, key="m5_merge")
    minv = c3.select_slider("最少進站人次（過濾小站）",
                            options=[0, 500_000, 1_000_000, 3_000_000, 5_000_000],
                            value=1_000_000, key="m5_minv")
    tidal = an.commuter_tidal(stations, yr5, merge_gates=merge5, min_volume=minv)
    st.plotly_chart(charts.tidal_chart(tidal, f"{yr5}"), width="stretch")

    cc1, cc2 = st.columns(2)
    cc1.markdown("**最偏住宅型（進＞出）**")
    cc1.dataframe(tidal.head(5)[["站名", "進出比", "類型"]], hide_index=True)
    cc2.markdown("**最偏商業/轉乘型（出＞進）**")
    cc2.dataframe(tidal.tail(5)[["站名", "進出比", "類型"]].iloc[::-1], hide_index=True)
    st.caption("進出比＝進站÷出站。>1 偏住宅型（居民進站通勤）、<1 偏商業/轉乘型。"
               "轉乘站建議開啟合併以免比值失真。")
