# -*- coding: utf-8 -*-
"""提取指定组织（默认华北区）的合同储备与 Backlog 统计 + 项目明细，并入 metrics.json["backlog"]。

依赖: openpyxl  (pip install openpyxl)

用法:
  python3 extract_backlog.py <项目业绩总览表.xlsx> <组织过滤全路径> [metrics.json路径]

默认:
  xlsx = 2010_项目业绩总览表_-项目经理 (1).xlsx
  组织过滤 = Global事业部群.产业数智化.数智平台事业部.数据治理部.华北区
  metrics = ./metrics.json

⚠️ 关键:
  1) 项目必须按「项目所属部门名称」(col14) 的【精确全路径】过滤。
  2) 金额列为「带千分位逗号的文本」(如 "11,792.45")，读取时必须 strip(",") 再转 float，
     否则会被当成 0（见 schema.md 踩坑第 14 条）。
  3) 表头占 2 行（Excel 行2=主列名，行3=子列名），数据从 Excel 行4 (min_row=4) 开始。
  4) 列索引: 合同额=col25(本币税后合同金额), YTD业绩收入=col37, PJTD业绩收入=col59,
     待定报告收入(YTD)=col50, 项目状态=col17, 项目类型=col2, 子项目经理=col9, 项目编码=col0。
  5) Backlog 口径 = 在执行中(Ongoing)项目合同额 − 该项目上半年已确认业绩收入(YTD)；
     已关闭/已取消项目视为执行完毕，不计入未执行余额。
"""
import json, sys, warnings
import openpyxl

warnings.filterwarnings("ignore")

XLSX = sys.argv[1] if len(sys.argv) > 1 else "2010_项目业绩总览表_-项目经理 (1).xlsx"
ORG = sys.argv[2] if len(sys.argv) > 2 else "Global事业部群.产业数智化.数智平台事业部.数据治理部.华北区"
METRICS = sys.argv[3] if len(sys.argv) > 3 else "metrics.json"


def f(x):
    if x is None:
        return 0.0
    s = str(x).replace(",", "").replace("%", "").strip()
    try:
        return float(s)
    except Exception:
        return 0.0


def main():
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=4, values_only=True))
    proj = [r for r in rows if r[14] is not None and str(r[14]).strip() == ORG]

    tc = sum(f(r[25]) for r in proj)
    ty = sum(f(r[37]) for r in proj)
    og = [r for r in proj if r[17] == "Ongoing"]
    cl = [r for r in proj if r[17] == "Closed"]
    ca = [r for r in proj if r[17] == "Canceled"]
    ogc = sum(f(r[25]) for r in og)
    ogy = sum(f(r[37]) for r in og)
    clc = sum(f(r[25]) for r in cl)
    pending = sum(f(r[50]) for r in proj)

    items = []
    for r in proj:
        c = f(r[25]); y = f(r[37]); p = f(r[59]); st = r[17]
        bl = round((c - y) / 10000, 1) if st == "Ongoing" else None
        items.append({
            "code": r[0], "name": (r[1] or "")[:40], "type": r[2], "status": st,
            "mgr": r[9], "contract": round(c / 10000, 1), "ytd": round(y / 10000, 1),
            "pjtd": round(p / 10000, 1), "backlog": bl,
        })
    items.sort(key=lambda x: -x["contract"])

    stat = {
        "total_contract": round(tc / 10000, 1),
        "ongoing_contract": round(ogc / 10000, 1),
        "ongoing_count": len(og),
        "closed_contract": round(clc / 10000, 1),
        "closed_count": len(cl),
        "canceled_count": len(ca),
        "ytd_rev_total": round(ty / 10000, 1),
        "backlog_ongoing": round((ogc - ogy) / 10000, 1),
        "pending_report": round(pending / 10000, 1),
        "items": items,
    }

    m = json.load(open(METRICS, encoding="utf-8"))
    m["backlog"] = stat
    json.dump(m, open(METRICS, "w"), ensure_ascii=False, indent=1)
    print(f"backlog 已并入 {METRICS}: 在手合同 {stat['total_contract']} 万 / Backlog {stat['backlog_ongoing']} 万 / 明细 {len(items)} 条")


if __name__ == "__main__":
    main()
