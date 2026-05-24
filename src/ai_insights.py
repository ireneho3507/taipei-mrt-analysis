# -*- coding: utf-8 -*-
"""Claude API 解讀模組。

每個分頁的「🤖 AI 解讀目前畫面」按鈕呼叫此處：把當前篩選後的摘要統計送進
claude-sonnet-4-6，回傳 2-3 句繁體中文洞見。

設計：
- system prompt 含完整資料背景與解讀準則，設 prompt caching（cache_control ephemeral）。
  注意 Sonnet 4.6 最小可快取前綴約 2048 tokens；本 system 較短時可能不實際命中快取，
  但維持設定以便日後擴充背景時自動受益、且不影響正確性。
- 金鑰自 st.secrets["ANTHROPIC_API_KEY"] 讀取（部署於 Streamlit Cloud 時設於 secrets），
  本機則退而求其次讀環境變數，皆不寫入版本控制。
"""
from __future__ import annotations

import os

MODEL = "claude-sonnet-4-6"

# 穩定、可快取的資料背景與解讀準則（放 system，volatile 的當前數據放 user 訊息）
SYSTEM_PROMPT = """你是臺北捷運運量資料的分析助理，協助使用者解讀一個 Streamlit 互動分析網站的畫面。

資料背景：
- 資料來源：政府開放資料平台（data.gov.tw）／臺北大眾捷運公司。
- 兩份資料：A「客運概況（月）」涵蓋 1998-01～2026-03 的全系統客運人次、收入、平均每日人次；
  B「各站進出站（年）」涵蓋 1996～2025、共 134 站的各站進站/出站人次與增減率。
- 「中運量」＝文湖線（膠輪系統，約佔總人次 9.5%），「高運量」＝其餘重運量路線（板南、淡水信義、松山新店、中和新蘆、環狀線）。
- 文湖線單程平均票價較高，故其收入佔比高於人次佔比。
- 已知運量崩跌：SARS（2003，約 −2.5%）、COVID（2020 約 −11.9%、2021 約 −23.7%，2021 因五月三級警戒最重）。
- 2 月常因春節假期與天數較少而為淡季低谷；運量在後疫情逐年回升。
- 2026 年僅有 1～3 月資料（不完整年），年度分析時應排除以免誤判。
- 站點排行若合併同站不同路線閘門（如台北車站 R＋BL），台北車站為全系統最繁忙站。

解讀準則：
- 根據使用者提供的「目前畫面摘要數據」進行解讀，務必貼合實際數字，不要編造未提供的數值。
- 用繁體中文，2 到 3 句，精簡且有洞見：點出重點趨勢或對比，並在合理時補一句可能成因。
- 語氣自然專業，不用條列、不用 markdown 標題、不要重複貼出原始數字清單。"""


def _get_api_key() -> str | None:
    """依序自 st.secrets、環境變數取得金鑰。"""
    try:
        import streamlit as st
        key = st.secrets.get("ANTHROPIC_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY")


def is_configured() -> bool:
    """是否已設定 API 金鑰。"""
    return bool(_get_api_key())


def interpret(context: str) -> str:
    """對 context（目前畫面摘要數據）產生 2-3 句繁中洞見。"""
    import anthropic

    key = _get_api_key()
    if not key:
        raise RuntimeError("未設定 ANTHROPIC_API_KEY")

    client = anthropic.Anthropic(api_key=key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {"role": "user", "content": f"目前畫面摘要數據：\n{context}\n\n請解讀。"}
        ],
    )
    return "".join(b.text for b in response.content if b.type == "text").strip()
