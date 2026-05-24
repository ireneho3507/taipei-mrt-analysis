# 🚇 臺北捷運運量分析 Streamlit App

NS5116《電腦硬體與程式語言在行為科學實驗與大數據分析之應用》期末專案
以臺灣政府開放資料製作的公開互動分析網站。

## 數據源

皆來自政府開放資料平台（[data.gov.tw](https://data.gov.tw)）／臺北大眾捷運股份有限公司：

| 檔案 | 粒度 | 內容 |
|------|------|------|
| `data/臺北市捷運客運概況按月別.csv` | 月 × 全系統（1998-01～2026-03） | 客運人次（總/中運量/高運量）、平均每日人次、客運收入 |
| `data/臺北市捷運各站進出站人次_年別.csv` | 年 × 站（1996～2025，134 站） | 各站進站/出站人次與增減率 |

> 「中運量」＝文湖線（膠輪系統），「高運量」＝其餘重運量路線。

## 功能

五個互動分析分頁 + 跨頁 AI 解讀：

| 分頁 | 內容 | 主要互動 |
|------|------|---------|
| 📈 歷史趨勢 | 人次／營收／客單價折線，含路網通車與疫情事件標註 | 指標、平滑（原始/12月移動平均/年增率）、年份範圍 |
| 🧩 運量結構 | 中運量 vs 高運量 100% 堆疊長條 | 人次/營收、百分比切換、年份範圍 |
| 🗓️ 季節與崩跌 | 季節指數（去天數干擾）＋年增率（標註 SARS／COVID） | 季節指標、年份範圍 |
| 🏆 站點排行 | 站點人流排行＋成長最快榜 | 年份、排序基準、**合併同站閘門**、Top-N |
| 🌗 通勤潮汐 | 進出比散點，分住宅型／商業型 | 年份、合併閘門、最少人次門檻 |
| 🤖 AI 解讀 | 每頁按鈕，將當前畫面摘要送 Claude（`claude-sonnet-4-6`）回傳繁中洞見 | — |

## 執行方式（本機）

```bash
pip install -r requirements.txt
streamlit run app.py
# 開啟 http://localhost:8501
```

### 設定 AI 解讀（選用）

AI 解讀需要 Anthropic API 金鑰。本機開發時建立 `.streamlit/secrets.toml`（已被 `.gitignore` 排除）：

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

部署到 Streamlit Cloud 時，改在 Cloud 的 **Settings → Secrets** 填入同一行（**切勿**提交金鑰進版控）。未設定金鑰時，app 其餘功能照常運作，AI 區會顯示提示。

## 測試

純函式單元測試（不需金鑰或網路）：

```bash
pip install -r requirements-dev.txt
pytest -q
```

GitHub Actions（`.github/workflows/ci.yml`）會在每次 push／PR 自動跑這些測試。

## 專案結構

```
app.py                    Streamlit 進入點（5 分頁 + AI）
src/
  data_loader.py          載入/清理（純 pandas）
  analysis.py             五模組分析純函式
  charts.py               Plotly 圖表 + 事件標註
  ai_insights.py          Claude API 解讀（prompt caching）
tests/                    pytest（data_loader / analysis）
data/                     兩份開放資料 CSV
.streamlit/config.toml    主題（secrets.toml 為機密，不提交）
.github/workflows/ci.yml  CI
docs/                     規則、藍圖、討論記錄
```

## 限制

- **資料粒度不一**：站別資料僅到「年」，月趨勢與季節分析僅用全系統資料，無法做「各站逐月」分析。
- **2026 為不完整年**（僅 1～3 月）：年度分析已自動排除以免誤判崩跌。
- **平/假日**：本專案未納入；季節分析以月為單位。
- **轉乘站閘門**：同站不同路線會被拆成多筆（如台北車站 R／BL），排行與潮汐分析提供「合併閘門」選項處理。
- **AI 解讀**：依賴外部 API，需金鑰且會產生少量費用；無金鑰時自動停用該功能。
- 評估過更細的「每日分時各站 OD 流量」資料，因單月約 280MB、全量約 30GB 過大，未採用。

## 資料來源致謝

臺北大眾捷運股份有限公司、政府資料開放平台。
