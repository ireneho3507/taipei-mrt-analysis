# -*- coding: utf-8 -*-
"""將作業 md 轉成帶中文字型樣式的 HTML，供瀏覽器列印成 PDF。"""
import sys
import markdown

src, out = sys.argv[1], sys.argv[2]
with open(src, encoding="utf-8") as f:
    body = markdown.markdown(f.read(), extensions=["tables", "fenced_code", "sane_lists"])

html = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<style>
@page {{ size: A4; margin: 18mm 16mm; }}
body {{ font-family: "Microsoft JhengHei","微軟正黑體",sans-serif; font-size: 11pt;
        line-height: 1.7; color: #1a1a1a; }}
h1 {{ font-size: 19pt; border-bottom: 3px solid #0a5; padding-bottom: 6px; }}
h2 {{ font-size: 15pt; margin-top: 22px; border-left: 5px solid #0a5; padding-left: 8px; }}
h3 {{ font-size: 12.5pt; color: #06743a; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 10pt; }}
th,td {{ border: 1px solid #bbb; padding: 5px 8px; text-align: left; vertical-align: top; }}
th {{ background: #e8f6ee; }}
tr:nth-child(even) td {{ background: #f7f7f7; }}
code {{ background: #f0f0f0; padding: 1px 4px; border-radius: 3px; font-size: 9.5pt; }}
blockquote {{ border-left: 4px solid #ccc; margin: 8px 0; padding: 2px 12px; color: #555; background:#fafafa; }}
hr {{ border: none; border-top: 1px solid #ddd; margin: 18px 0; }}
strong {{ color: #06743a; }}
</style></head><body>
{body}
</body></html>"""

with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("HTML written:", out)
