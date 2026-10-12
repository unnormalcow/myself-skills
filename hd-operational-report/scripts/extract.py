# -*- coding: utf-8 -*-
"""extract.py — 从两份 HAND/汉得 ERP 导出的 xlsx 抽取各 sheet 为 CSV。

用法:
  python3 extract.py <部门业绩总览表.xlsx> <项目业绩总览表.xlsx> [输出目录]

默认输出目录: 当前目录/_data
依赖: 本地 editor_sdk 服务（tencent-local-office-edit skill 的 edsdk.py）。
说明: sheet_get_cell_data 返回 JSON（{"csv_data": "..."}），本脚本解析后落盘为纯 CSV。

重要踩坑: editor_sdk 的 open_file 是异步调用，open 之后必须等待(约2秒)再读取，
否则会出现 "workbook is not open" 导致导出的 CSV 为空。每个文件只需 open 一次。
"""
import subprocess, json, os, sys, time

SKILL = "/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/resources/builtin-skills/tencent-local-office-edit"

F1 = sys.argv[1] if len(sys.argv) > 1 else "/Users/Mac/Downloads/区域经营分析/1010_部门业绩总览表.xlsx"
F2 = sys.argv[2] if len(sys.argv) > 2 else "/Users/Mac/Downloads/区域经营分析/2010_项目业绩总览表_-项目经理 (1).xlsx"
OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.getcwd(), "_data")
os.makedirs(OUT, exist_ok=True)

# 部门表 6 个 sheet 的 sheet_id 与导出列范围（稳定，与 ERP 导出顺序一致）
jobs = [
    (F1, "000001", 200, 46, "dept_budget.csv"),
    (F1, "000002", 200, 26, "dept_keymetrics.csv"),
    (F1, "000003", 200, 41, "dept_total.csv"),
    (F1, "000004", 200, 26, "dept_cashflow.csv"),
    (F1, "000005", 200, 46, "dept_breakdown.csv"),
    (F1, "000006", 200, 26, "dept_perf.csv"),
    (F2, "000001", 200, 97, "projects.csv"),
]

def open_wb(path):
    # editor_sdk 的 open_file 用 file_path= 参数（绝不是 file_id=），且为异步，
    # open 之后必须等待(约4秒)再读取，否则会报 "workbook is not open"。
    subprocess.run(["python3", "edsdk.py", "call", "open_file", f"file_path={path}"],
                   cwd=SKILL, capture_output=True, text=True)
    time.sleep(4)

opened = set()
for fid, sid, er, ec, name in jobs:
    if fid not in opened:
        open_wb(fid)
        opened.add(fid)
    cmd = ["python3", "edsdk.py", "call", "sheet_get_cell_data",
           f"file_id={fid}", f"sheet_id={sid}",
           "start_row=0", "start_col=0", f"end_row={er}", f"end_col={ec}", "return_csv=true"]
    r = subprocess.run(cmd, cwd=SKILL, capture_output=True, text=True)
    csv = ""
    try:
        d = json.loads(r.stdout)
        csv = d.get("csv_data", "")
    except Exception as e:
        print("PARSE ERR", name, str(e), r.stdout[:150], r.stderr[:150])
    open(os.path.join(OUT, name), "w").write(csv)
    print(f"wrote {name}: {csv.count(chr(10))} lines")
