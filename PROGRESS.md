# 期末專案進度記錄 — 臺北捷運運量分析 Streamlit App

> 最後更新：2026-05-25
> 下次銜接：先讀本檔，再看 `docs/blueprint.md`（完整架構）；報告當天看 `docs/presentation_plan.md`。

## 專案概要

- 課程：NS5116 電腦硬體與程式語言在行為科學實驗與大數據分析之應用
- 目標：用臺北捷運開放資料做一個**公開 Streamlit 互動網站**，整合 Plotly 互動圖 + Claude API + pytest/GitHub Actions + 部署 Streamlit Cloud。
- 規則與評分：見 `docs/rules.md`（重點：穩定性 25、開放數據洞見 20、互動 15、視覺化 15、AI 15、報告 10；金鑰外洩 −10、requirements 缺 −5）。
- 報告：當日 9:00 前繳交、現場演示 8 分 + 問答 2 分。

## 資料來源（已定案：兩份檔，放 `data/`）

| 檔案 | 粒度 | 用途 |
|------|------|------|
| `臺北市捷運客運概況按月別.csv` | 月 × 全系統（1998-01~2026-03，連續無缺） | 趨勢、運量結構、季節、營收、客單價 |
| `臺北市捷運各站進出站人次_年別.csv` | 年 × 站（1996~2025，134 站） | 站點排行、通勤潮汐 |

> 已評估並**放棄**第三份「每日分時 OD 流量」（單月 ~280MB、全量 ~30GB，過大）。索引檔與聚合腳本已清除。

## 五個分析模組（+ AI）

- M1 歷史趨勢（折線，客運概況）：人次/營收/客單價 × raw/MA12/YoY + 事件標註線。
- M2 運量結構（100% 堆疊，客運概況）：中運量(文湖線) vs 高運量，人次/營收切換。
- M3 季節與崩跌（客運概況）：季節指數（用平均每日去天數干擾）+ 年增率（標 SARS/COVID，排除 2026）。
- M4 站點排行（各站年）：排行 + 成長榜，**合併閘門** toggle。
- M5 通勤潮汐（各站年）：進出比 → 住宅型/商業型散點分群。
- AI：每頁「🤖 AI 解讀目前畫面」按鈕 → claude-sonnet-4-6 + prompt caching（**尚未實作**）。

## 進度狀態

| 階段 | 內容 | 狀態 |
|------|------|------|
| 1 | `src/data_loader.py` + `tests/test_data_loader.py`（9 項） | ✅ 完成 |
| 2 | `src/analysis.py` + `tests/test_analysis.py`（8 項） | ✅ 完成 |
| 3 | `src/charts.py`（10 個 Plotly 圖） | ✅ 完成 |
| 4 | `app.py`（5 分頁 + 11 widget），AppTest 無例外 | ✅ 完成 |
| 5 | `src/ai_insights.py` 接 Claude（claude-sonnet-4-6 + prompt caching），5 分頁傳真實摘要 | ✅ 完成（唯真實金鑰實測待 demo 前） |
| 6 | `requirements.txt`/`-dev`、`.gitignore`、`.streamlit/`、`.github/workflows/ci.yml`、`README.md` | ✅ 完成 |
| 7 | 推 GitHub（✅ public repo + CI 綠燈）+ 部署 Streamlit Cloud（✅ 上線） | ✅ 完成（剩 AI 金鑰 + Firefox 檢查 + 排練） |

> GitHub：`ireneho3507/taipei-mrt-analysis`（**public**），CI 通過（17 測試）。
> 上線網址：**https://irene-taipei-mrt-analysis.streamlit.app/** （Playwright 無痕驗收：0 console errors、圖表/widget/中文正常）。
> 剩：到 Streamlit Cloud Secrets 填 `ANTHROPIC_API_KEY` 啟用 AI（**demo 前唯一硬待辦**，沒填 AI 段會開天窗）、Firefox 開一次。

### 2026-05-25 報告準備 + 小修（已完成，需 push）
- **報告文件三份**（`docs/`）：`presentation_plan.md`（當天完整架構：三問題主線、8 分節奏、逐段講法、轉場句、應變）、`demo_script.md`（逐字稿）、`qa_prep.md`（Q&A 備答小抄）。
- **新增頁面頂端「📥 下載原始開放資料」expander**：並排兩鈕下載 `data/` 原始 CSV 位元組（保留 UTF-8-BOM）。AppTest 確認兩鈕存在、無例外。
- **M2 caption 修正**：原「文湖線收入佔比較高」易誤讀成贏過高運量；改為「收入佔比高於人次佔比、但總量仍遠小於高運量」，並加註 2005–2007 營收缺值。
- **README 限制段**：新增「分車種營收 2005–2007 缺漏」（開放資料來源缺，人次正常，忠實呈現不補值）。
- 17 測試仍全過。**以上改動尚未 commit/push。**

**測試現況：17 項 pytest 全過；app 已用 `streamlit.testing` AppTest 驗證互動無例外。**

## 目前檔案結構

```
final_project_mrt/
├── app.py                    ✅ 5 分頁 + widgets（AI 區為佔位）
├── src/
│   ├── data_loader.py        ✅ 載入/清理（純 pandas，無 streamlit 依賴）
│   ├── analysis.py           ✅ 五模組分析純函式
│   ├── charts.py             ✅ Plotly 圖表 + 事件標註
│   └── ai_insights.py        ⬜ 佔位（is_configured()=False）
├── tests/
│   ├── test_data_loader.py   ✅ 9 項
│   └── test_analysis.py      ✅ 8 項
├── data/                     ✅ 兩份 csv
├── docs/
│   ├── rules.md              期末規則
│   ├── blueprint.md          完整架構藍圖（含 AI 定案）
│   ├── presentation_plan.md  ✅ 報告當天完整架構（三問題主線/節奏/講法/應變）
│   ├── demo_script.md        ✅ 演示逐字稿
│   ├── qa_prep.md            ✅ Q&A 備答小抄
│   └── 作業_與Claude討論期末計畫.md/.pdf   小作業（已完成）
├── scripts/md_to_html.py     md→PDF 用
└── PROGRESS.md               本檔
```

## 如何執行 / 測試

```powershell
# 測試
cd C:\irene_python\final_project_mrt
$env:PYTHONIOENCODING="utf-8"; python -m pytest -q

# 本機啟動 app
python -m streamlit run app.py
# → http://localhost:8501
```

依賴（尚未寫進 requirements.txt）：`streamlit pandas plotly anthropic pytest`（皆已 pip 安裝於本機）。

## 已定案的決策

- AI 形式：**解讀按鈕**（不做自由問答框）；模型 **claude-sonnet-4-6**；採 prompt caching。
- 視覺：中運量配色 #f1a340、高運量 #4575b4。

## 關鍵資料事實／陷阱（實作時務必記得）

- 「客運」=捷運載客（非公路客運）；兩檔年總量對得起來 ≈97%。
- 中運量=文湖線（~9.5%）、高運量=其餘；是車種之分，非人多寡。
- 站名後綴 R/BL/BR/G/O/Y=路線；去尾端英文字母即基底站名（合併閘門）。
- **台北車站** R+BL 合併 5,545 萬 > 西門 2,489 萬；不合併會被低估。
- **2026 僅 1–3 月**（不完整年），年分析須排除（`完整年` 欄）。
- **分車種營收 2005–2007 在原始資料為 0（缺）**，人次正常；M2 切「營收」這三年空白屬資料源缺漏，非 bug。
- **M5 進出比僅 0.91~1.13（±13%）**：年資料下對稱來回會抵消，量到的是不對稱行程的「淨傾向」；114 站中 86 站為均衡型。住宅/商業是傾向非硬分類。
- 崩跌年：SARS 2003（−2.5%）、COVID 2020（−11.9%）、2021（−23.7%）。
- CSV 編碼皆 UTF-8 with BOM（`encoding="utf-8-sig"`）。

## 下一步（階段 7：部署）

1. **AI 實測（待 demo 前）**：到 console.anthropic.com 取得金鑰、Billing 儲值（≥US$5），填入 `.streamlit/secrets.toml`，啟動 app 點「產生解讀」驗證。每次解讀約 US$0.003–0.01。
2. **推上 GitHub**：`git init` → commit（確認 secrets.toml 未被加入）→ push；CI 應綠燈（17 測試）。
3. **部署 Streamlit Cloud**：連 repo、設定 main file=`app.py`、在 Cloud Secrets 填 `ANTHROPIC_API_KEY`。
4. **驗收**：無痕模式可開、首次載入 <20 秒、Chrome＋Firefox 皆測。

## 安裝狀態（本機）
已 pip 安裝：streamlit 1.57.0、pandas 3.0.2、plotly 6.7.0、anthropic 0.104.1、pytest 9.0.3。
`.streamlit/secrets.toml` 目前為佔位字串（尚未填真實金鑰）。
