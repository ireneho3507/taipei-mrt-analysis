# -*- coding: utf-8 -*-
"""離線聚合：把巨量的「每日分時各站 OD 流量」原始檔（每月約 270MB）
壓成可進版控的小檔，供 app 的 M5「通勤潮汐」使用。

原始檔放在 _od_raw/（不進 git），來源：data.taipei「臺北捷運每日分時各站
OD流量統計資料」。欄位：日期, 時段(00-23), 進站(起站), 出站(訖站), 人次。

方法（直接回應「年進出比會被同站來回均衡掉」的質疑）：
  對每一站，分早高峰(07-09)與晚高峰(17-19)，分別累計它作為
    起站(出發, 進站欄==該站) 與 訖站(抵達, 出站欄==該站) 的人次。
  住宅站：早上大量「出發」、傍晚大量「抵達」；商業/上班站相反。
  潮汐指數 = 早晨出發佔比 − 傍晚出發佔比
           = AM_origin/(AM_origin+AM_dest) − PM_origin/(PM_origin+PM_dest)
  住宅傾向 → 正；商業/轉乘傾向 → 負。這是分時方向的實測反轉，
  不會被「同站來回」抵消（早晚為各自獨立的時間窗）。

只計工作日（排除週末；所選月份 11 月在台灣無國定假日）。

輸出：data/od_tidal.csv（多年合併，UTF-8 with BOM）。
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "_od_raw"
OUT_FILE = ROOT / "data" / "od_tidal.csv"

AM_HOURS = {7, 8}    # 早高峰 07:00–08:59
PM_HOURS = {17, 18}  # 晚高峰 17:00–18:59
CHUNK = 2_000_000

# 要聚合的 (西元年, 原始檔名)
SOURCES = [
    (2019, "od_201911.csv"),
    (2025, "od_202511.csv"),
]


def _accumulate(path: Path) -> tuple[pd.DataFrame, int]:
    """串流讀取單月 OD，回傳各站早晚出發/抵達彙總 + 工作日天數。"""
    acc = {  # 站名 -> 四個方向量
        "早晨出發": pd.Series(dtype="int64"),
        "早晨抵達": pd.Series(dtype="int64"),
        "傍晚出發": pd.Series(dtype="int64"),
        "傍晚抵達": pd.Series(dtype="int64"),
        "工作日全日量": pd.Series(dtype="int64"),  # 該站(起+訖)全日合計，作規模
    }
    weekdays: set[str] = set()

    def add(key, s):
        acc[key] = acc[key].add(s, fill_value=0)

    for chunk in pd.read_csv(
        path, encoding="utf-8-sig",
        usecols=["日期", "時段", "進站", "出站", "人次"],
        dtype={"時段": "int16", "進站": "string", "出站": "string", "人次": "int32"},
        chunksize=CHUNK,
    ):
        dates = pd.to_datetime(chunk["日期"])
        is_weekday = dates.dt.weekday < 5
        chunk = chunk[is_weekday]
        weekdays.update(dates[is_weekday].dt.date.astype(str).unique())
        if chunk.empty:
            continue

        am = chunk[chunk["時段"].isin(AM_HOURS)]
        pm = chunk[chunk["時段"].isin(PM_HOURS)]
        add("早晨出發", am.groupby("進站")["人次"].sum())
        add("早晨抵達", am.groupby("出站")["人次"].sum())
        add("傍晚出發", pm.groupby("進站")["人次"].sum())
        add("傍晚抵達", pm.groupby("出站")["人次"].sum())
        # 規模用：該站當起站的全日量（每筆只算一次起站，避免重複）
        add("工作日全日量", chunk.groupby("進站")["人次"].sum())

    df = pd.DataFrame(acc).fillna(0).astype("int64")
    df.index.name = "站名"
    return df.reset_index(), len(weekdays)


def build() -> pd.DataFrame:
    frames = []
    for year, fname in SOURCES:
        path = RAW_DIR / fname
        if not path.exists():
            raise FileNotFoundError(f"找不到原始檔：{path}（請先下載到 _od_raw/）")
        print(f"處理 {year} … {path.name}")
        g, n_wd = _accumulate(path)
        g.insert(0, "西元年", year)
        g["工作日數"] = n_wd
        frames.append(g)
        print(f"  {year}: {len(g)} 站、{n_wd} 個工作日")

    out = pd.concat(frames, ignore_index=True)

    am_total = out["早晨出發"] + out["早晨抵達"]
    pm_total = out["傍晚出發"] + out["傍晚抵達"]
    out["早晨出發佔比"] = (out["早晨出發"] / am_total).where(am_total > 0)
    out["傍晚出發佔比"] = (out["傍晚出發"] / pm_total).where(pm_total > 0)
    out["潮汐指數"] = out["早晨出發佔比"] - out["傍晚出發佔比"]
    out["工作日均運量"] = (out["工作日全日量"] / out["工作日數"]).round().astype("int64")

    cols = ["西元年", "站名", "早晨出發", "早晨抵達", "傍晚出發", "傍晚抵達",
            "早晨出發佔比", "傍晚出發佔比", "潮汐指數", "工作日均運量", "工作日數"]
    return out[cols].sort_values(["西元年", "潮汐指數"], ascending=[True, False])


if __name__ == "__main__":
    result = build()
    OUT_FILE.parent.mkdir(exist_ok=True)
    result.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n已寫出 {OUT_FILE}（{len(result)} 列）")
    print("\n=== 2025 最住宅傾向（潮汐指數高）===")
    print(result[result["西元年"] == 2025].head(8)[
        ["站名", "早晨出發佔比", "傍晚出發佔比", "潮汐指數", "工作日均運量"]
    ].to_string(index=False))
    print("\n=== 2025 最商業/轉乘傾向（潮汐指數低）===")
    print(result[result["西元年"] == 2025].tail(8)[
        ["站名", "早晨出發佔比", "傍晚出發佔比", "潮汐指數", "工作日均運量"]
    ].to_string(index=False))
