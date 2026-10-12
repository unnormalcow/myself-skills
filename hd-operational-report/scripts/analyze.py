# -*- coding: utf-8 -*-
"""analyze.py — 解析抽取出的 CSV，计算部门 + 项目指标，输出 metrics.json。

用法:
  python3 analyze.py <csv目录> [组织过滤全路径] [metrics.json输出路径] [签约目标json路径]

默认 csv目录: 当前目录/_data
默认组织过滤: Global事业部群.产业数智化.数智平台事业部.数据治理部.华北区
默认输出: ./metrics.json
签约目标 json (可选): {"annual_target":890,"signed_new":171,"signed_total":299}
  —— 单位万元；annual_target=年度签约目标, signed_new=上半年新签,
     signed_total=上半年累计签约(含续签/老客户)。提供后报告会生成
     「三、目标达成与签约情况」章节，否则跳过该章。

⚠️ 关键: 项目必须按「项目所属部门名称」(表头第14列) 的【精确全路径】过滤，
   不能用模糊子串匹配（否则会混入其他区域，项目收入/坏账被错误放大）。
"""
import csv, json, sys, os
from collections import defaultdict

def num(s):
    if s is None: return None
    s = str(s).strip()
    if s == "" or s.upper().startswith("#") or s in ("-", "—"): return None
    s = s.replace(",", "").replace("%", "")
    try:
        return float(s)
    except:
        return None

def pct(v):
    return None if v is None else v/100.0

DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.getcwd(), "_data")
ORG_FILTER = sys.argv[2] if len(sys.argv) > 2 else "Global事业部群.产业数智化.数智平台事业部.数据治理部.华北区"
OUT_JSON = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.getcwd(), "metrics.json")
SIGNING_JSON = sys.argv[4] if len(sys.argv) > 4 else None

# ---------- DEPARTMENT: key metrics ----------
km = {}
with open(f"{DATA}/dept_keymetrics.csv", encoding="utf-8") as f:
    rows = list(csv.reader(f))
# row0..2 header-ish; data from row3 (file line 4) -> in list index 3
hdr = rows[2]  # ['项目','总计','202601',...]
for r in rows[3:]:
    if not r or not r[0].strip(): continue
    name = r[0].strip()
    vals = [num(x) for x in r[1:]]
    km[name] = vals  # [总计, 202601..202607]

def km_get(name):
    return km.get(name) or km.get("-"+name) or [None]*8

months = ["202601","202602","202603","202604","202605","202606","202607"]

# ---------- DEPARTMENT: budget (YoY) ----------
budget = {}
with open(f"{DATA}/dept_budget.csv", encoding="utf-8") as f:
    brows = list(csv.reader(f))
# header row index 3 (list idx 3): subheader. data from idx4
for r in brows[4:]:
    if not r or not r[0].strip(): continue
    name = r[0].strip()
    # cols: 0 name,1 实际,2 年初计划,3 计划完成率,4 收入同比完成度,5 去年同期,6 去年同比,7 全年最新计划
    budget[name] = {
        "actual": num(r[1]), "plan_ytd": num(r[2]), "plan_rate": pct(num(r[3])),
        "yoy_complete": pct(num(r[4])), "lastyear": num(r[5]), "yoy_growth": pct(num(r[6])),
        "plan_full": num(r[7])
    }

# ---------- DEPARTMENT: cash flow ----------
cf = {}
with open(f"{DATA}/dept_cashflow.csv", encoding="utf-8") as f:
    crows = list(csv.reader(f))
for r in crows[4:]:
    if not r or not r[0].strip(): continue
    name = r[0].strip()
    cf[name] = {"actual": num(r[1]), "forecast": num(r[2]), "monthly": [num(x) for x in r[3:3+7]]}

# ---------- DEPARTMENT: perf ----------
perf = {}
with open(f"{DATA}/dept_perf.csv", encoding="utf-8") as f:
    prows = list(csv.reader(f))
for r in prows[4:]:
    if not r or not r[0].strip(): continue
    perf[r[0].strip()] = [num(x) for x in r[1:]]

# ---------- PROJECTS ----------
with open(f"{DATA}/projects.csv", encoding="utf-8") as f:
    prows2 = list(csv.reader(f))
# header rows: idx0 = 会计年度 line, idx1 = grouped (identity names), idx2 = detailed subheaders (measure names, YTD=first)
hdr_id = prows2[1]
hdr_meas = prows2[2]
def cidx(name):
    # identity columns live in row1; measure columns in row2 (first occurrence = YTD)
    if name in hdr_id:
        return hdr_id.index(name)
    return hdr_meas.index(name)
m_name = cidx("子项目经理姓名")
m_code = cidx("子项目经理工号")
p_name = cidx("子项目名称")
p_type = cidx("项目类型")
p_cat = cidx("产品管理大类")
org = cidx("项目所属部门名称")
status = cidx("项目状态")
ytd_rev = cidx("业绩收入")
ytd_labor = cidx("人工成本")
ytd_exp = cidx("项目费用")
ytd_gp = cidx("项目毛利")
ytd_gpr = cidx("毛利率")
ytd_np = cidx("项目净利")
ytd_npr = cidx("项目净利率")
ytd_bad = cidx("坏账计提")
ytd_inv = cidx("累计开票金额")
ytd_col = cidx("累计收款金额")
ytd_cf = cidx("业绩现金流")
overdue = cidx("报告逾期天数")
pending = cidx("待提交报告数量")
contract = cidx("本币税后合同金额")

# distinct org
orgs = {}
projects = []
for r in prows2[3:]:
    if len(r) <= org or not r[0].strip(): continue
    o = r[org].strip()
    orgs[o] = orgs.get(o,0)+1
    projects.append(r)

print("=== DISTINCT 项目经营部门名称 (top) ===")
for k,v in sorted(orgs.items(), key=lambda x:-x[1])[:15]:
    print(f"  {v:3d}  {k}")

# Decide scope: 必须按「项目所属部门名称」精确全路径过滤（不要模糊子串！）
scope = [r for r in projects if r[org].strip() == ORG_FILTER]
print(f"\nTotal project rows: {len(projects)}, scoped to [{ORG_FILTER}]: {len(scope)}")

# Active = 上半年产生业绩收入（YTD 业绩收入 != 0）。
# 注意：与已审批报告口径一致——以「业绩收入>0」判定活跃，避免把仅有毛利/净利的零收入行计入，
# 否则活跃项目数会从 28 变成 36，与已交付报告数字不一致。
def active(r):
    return abs(num(r[ytd_rev]) or 0) > 0.0001

def s(col, rows):
    return sum((num(r[col]) or 0) for r in rows)

active_rows = [r for r in scope if active(r)]
print(f"华北区 active projects (有业绩收入/毛利/净利>0): {len(active_rows)}")
# compare to dept 部门项目收入
print(f"  -> sum YTD 业绩收入 = {s(ytd_rev, active_rows):,.1f}  (dept 部门项目收入=316)")
print(f"  -> sum 项目毛利 = {s(ytd_gp, active_rows):,.1f}  (dept 部门毛利=87)")
print(f"  -> sum 项目净利 = {s(ytd_np, active_rows):,.1f}  (dept 部门利润=-13)")
print(f"  -> sum 业绩现金流 = {s(ytd_cf, active_rows):,.1f}  (dept 净现金流=-18)")

def s(col, rows):
    return sum((num(r[col]) or 0) for r in rows)

agg = {
    "total_rev": s(ytd_rev, active_rows),
    "total_gp": s(ytd_gp, active_rows),
    "total_np": s(ytd_np, active_rows),
    "total_labor": s(ytd_labor, active_rows),
    "total_exp": s(ytd_exp, active_rows),
    "total_bad": s(ytd_bad, active_rows),
    "total_inv": s(ytd_inv, active_rows),
    "total_col": s(ytd_col, active_rows),
    "total_cf": s(ytd_cf, active_rows),
    "n_active": len(active_rows),
    "n_total": len(scope),
}
print("\n=== 华北区 ACTIVE project aggregates (YTD) ===")
for k,v in agg.items():
    print(f"  {k}: {v:,.2f}" if isinstance(v,float) else f"  {k}: {v}")

# by manager
from collections import defaultdict
mgr = defaultdict(lambda: {"n":0,"rev":0.0,"gp":0.0,"np":0.0,"bad":0.0,"inv":0.0,"col":0.0,"cf":0.0,"contract":0.0})
for r in active_rows:
    m = r[m_name].strip() or "(未命名)"
    d = mgr[m]
    d["n"]+=1; d["rev"]+=num(r[ytd_rev]) or 0; d["gp"]+=num(r[ytd_gp]) or 0
    d["np"]+=num(r[ytd_np]) or 0; d["bad"]+=num(r[ytd_bad]) or 0
    d["inv"]+=num(r[ytd_inv]) or 0; d["col"]+=num(r[ytd_col]) or 0
    d["cf"]+=num(r[ytd_cf]) or 0; d["contract"]+=num(r[contract]) or 0
mgr_list = sorted(mgr.items(), key=lambda x:-x[1]["rev"])
print("\n=== By 项目经理 (active, sorted by revenue) ===")
for m,d in mgr_list:
    gpr = (d["gp"]/d["rev"]*100) if d["rev"] else 0
    print(f"  {m:8s} n={d['n']:2d} 收入={d['rev']:10.1f} 毛利={d['gp']:9.1f}({gpr:5.1f}%) 净利={d['np']:9.1f} 坏账={d['bad']:7.1f} 收款={d['col']:9.1f}")

# by type
typ = defaultdict(lambda: {"n":0,"rev":0.0,"gp":0.0,"np":0.0})
for r in active_rows:
    t = r[p_type].strip() or "(未分类)"
    d = typ[t]; d["n"]+=1; d["rev"]+=num(r[ytd_rev]) or 0; d["gp"]+=num(r[ytd_gp]) or 0; d["np"]+=num(r[ytd_np]) or 0
typ_list = sorted(typ.items(), key=lambda x:-x[1]["rev"])
print("\n=== By 项目类型 (active) ===")
for t,d in typ_list:
    print(f"  {t:20s} n={d['n']:2d} 收入={d['rev']:10.1f} 毛利={d['gp']:9.1f} 净利={d['np']:9.1f}")

# Top 10 by revenue
top_rev = sorted(active_rows, key=lambda r:-(num(r[ytd_rev]) or 0))[:10]
print("\n=== TOP 10 项目 by 业绩收入 (YTD) ===")
for r in top_rev:
    print(f"  {r[p_name][:34]:34s} | {r[m_name]:6s} | 收入={num(r[ytd_rev]) or 0:9.1f} 毛利={num(r[ytd_gp]) or 0:8.1f} 净利={num(r[ytd_np]) or 0:8.1f} 状态={r[status]}")

# Top 10 by gross profit
top_gp = sorted(active_rows, key=lambda r:-(num(r[ytd_gp]) or 0))[:10]
print("\n=== TOP 10 项目 by 项目毛利 (YTD) ===")
for r in top_gp:
    print(f"  {r[p_name][:34]:34s} | 毛利={num(r[ytd_gp]) or 0:8.1f} 毛利率={r[ytd_gpr]} 收入={num(r[ytd_rev]) or 0:9.1f}")

# Risk: negative net profit (loss-making) among active
loss = [r for r in active_rows if (num(r[ytd_np]) or 0) < 0]
print(f"\n=== 亏损项目 (净利<0): {len(loss)} ===")
for r in sorted(loss, key=lambda r:(num(r[ytd_np]) or 0))[:15]:
    print(f"  {r[p_name][:34]:34s} | {r[m_name]:6s} | 净利={num(r[ytd_np]) or 0:8.1f} 毛利={num(r[ytd_gp]) or 0:8.1f} 坏账={num(r[ytd_bad]) or 0:7.1f}")

# Overdue reports
od = [r for r in scope if (num(r[overdue]) or 0) > 0]
pd_ = [r for r in scope if (num(r[pending]) or 0) > 0]
print(f"\n=== 报告逾期项目: {len(od)} | 待提交报告项目: {len(pd_)} ===")
for r in sorted(od, key=lambda r:-(num(r[overdue]) or 0))[:10]:
    print(f"  {r[p_name][:34]:34s} | 逾期={num(r[overdue]) or 0:6.0f}天 待提交={num(r[pending]) or 0:.0f}")

# Save metrics for report building
metrics = {
    "dept": {
        "ext_rev": km_get("外部收入"),
        "proj_rev": km_get("部门项目收入"),
        "dept_gp": km_get("部门毛利"),
        "gp_rate": [ (v/100.0 if v is not None else 0.0) for v in km_get("毛利率") ],
        "dept_profit": km_get("部门利润"),
        "profit_rate": km_get("部门利润率"),
        "labor": km_get("人工成本"),
        "imp_exp": km_get("项目实施费用"),
        "sale_exp": km_get("销售费用"),
        "bad_debt": km_get("坏账准备"),
        "perf_profit": km_get("考核利润"),
        "perf_rate": km_get("考核利润率"),
        "invoice": km_get("开票金额"),
        "collection": km_get("收款金额"),
        "net_cashflow": km_get("部门净现金流"),
        "budget": budget,
        "cashflow": {k: cf.get(k,{}) for k in ["本期净现金流","期末现金余额","收款金额","已开票未收款金额","已确认收入未收款","1年以内应收账款","期初现金余额"]},
        "perf": {k: perf.get(k,[]) for k in ["部门收入","项目成本及费用"]},
        "report": {
            "due": km_get("本期应提交报告阶段数")[0],
            "submitted": km_get("本期已提交报告阶段数")[0],
            "onetime_rate": km_get("及时签回率")[0],
        }
    },
    "projects": {
        "agg": agg,
        "by_manager": [(m,d) for m,d in mgr_list],
        "by_type": [(t,d) for t,d in typ_list],
        "top_rev": [[r[p_name],r[m_name],num(r[ytd_rev]) or 0,num(r[ytd_gp]) or 0,num(r[ytd_np]) or 0, r[status]] for r in top_rev],
        "top_gp": [[r[p_name],num(r[ytd_gp]) or 0, r[ytd_gpr], num(r[ytd_rev]) or 0] for r in top_gp],
        "loss": [[r[p_name],r[m_name],num(r[ytd_np]) or 0,num(r[ytd_gp]) or 0,num(r[ytd_bad]) or 0] for r in sorted(loss,key=lambda r:(num(r[ytd_np]) or 0))[:15]],
        "overdue": [[r[p_name],num(r[overdue]) or 0,num(r[pending]) or 0] for r in sorted(od,key=lambda r:-(num(r[overdue]) or 0))[:10]],
    },
    "months": months,
    "project_filter": ORG_FILTER,
}
# 签约目标（可选）：年度签约目标 / 上半年新签 / 上半年累计签约（万元）
if SIGNING_JSON and os.path.exists(SIGNING_JSON):
    try:
        sg = json.load(open(SIGNING_JSON, encoding="utf-8"))
        metrics["signing"] = {
            "annual_target": float(sg.get("annual_target") or 0),
            "signed_new": float(sg.get("signed_new") or 0),
            "signed_total": float(sg.get("signed_total") or 0),
        }
        print(f"\n[signing] 年度目标 {metrics['signing']['annual_target']:.0f} 万 / "
              f"新签 {metrics['signing']['signed_new']:.0f} 万 / "
              f"累计 {metrics['signing']['signed_total']:.0f} 万 -> 已并入 metrics.json")
    except Exception as e:
        print("WARN: 解析签约目标 json 失败:", e)
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(metrics, f, ensure_ascii=False, indent=1)
print("\nSaved /tmp/metrics.json")
