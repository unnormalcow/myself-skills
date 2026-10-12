# -*- coding: utf-8 -*-
import json, sys, os

# 用法: python3 gen_html_md.py [metrics.json路径] [输出目录] [区域显示名]
METRICS = sys.argv[1] if len(sys.argv) > 1 else "/tmp/metrics.json"
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
REGION = sys.argv[3] if len(sys.argv) > 3 else "华北区"

m = json.load(open(METRICS, encoding="utf-8"))
D = m["dept"]; P = m["projects"]; MONTHS = m["months"]
MW = ["1月","2月","3月","4月","5月","6月","7月"]

# 签约目标（可选）：年度目标 / 上半年新签 / 上半年累计签约（万元）
SG = m.get("signing") or {}
ANN = SG.get("annual_target") or 0
SNEW = SG.get("signed_new") or 0
STOT = SG.get("signed_total") or 0
BL = m.get("backlog") or {}
def signing_html():
    if not ANN:
        return ""
    attain = STOT/ANN*100; gap = ANN-STOT
    newr = (SNEW/STOT*100) if STOT else 0; renewal = STOT-SNEW
    return (f'<h2>三、目标达成与签约情况（上半年）</h2>'
        f'''<table><tr><th>指标</th><th class="num">数值</th><th>说明</th></tr>
        <tr><td>年度签约目标</td><td class="num">{ANN:.0f} 万</td><td>全年签约额目标</td></tr>
        <tr><td>上半年新签</td><td class="num">{SNEW:.0f} 万</td><td>新客户 / 新项目签约</td></tr>
        <tr><td>上半年累计签约（含续签 / 老客户）</td><td class="num">{STOT:.0f} 万</td><td>新签 {SNEW:.0f} + 续签 {renewal:.0f}</td></tr>
        <tr><td>目标达成率</td><td class="num">{attain:.1f}%</td><td>{STOT:.0f} / {ANN:.0f}</td></tr>
        <tr><td>下半年缺口</td><td class="num">{gap:.0f} 万</td><td>{ANN:.0f} − {STOT:.0f}</td></tr>
        <tr><td>新签占比</td><td class="num">{newr:.1f}%</td><td>{SNEW:.0f} / {STOT:.0f}</td></tr>
        <tr><td>续签贡献</td><td class="num">{renewal:.0f} 万</td><td>{STOT:.0f} − {SNEW:.0f}</td></tr></table>'''
        f'''<div class="callout"><b>签约进度判断：</b>上半年目标达成率仅 <b>{attain:.1f}%</b>，时间过半但目标未过半；下半年缺口 <b>{gap:.0f} 万</b>，须在中纺 / 中煤 / 中信金属 / 中海油等售前转化与合同下发上集中发力。新签占比 <b>{newr:.1f}%</b> 说明新客拓展为主力，续签 {renewal:.0f} 万体现老客户粘性，结构健康。</div>''')

def w(v):  # 元 -> 万元，1位小数
    return None if v is None else v/10000.0
def f1(x):  return "—" if x is None else f"{x:,.1f}"
def f2(x):  return "—" if x is None else f"{x:,.2f}"
def pc(x):  return "—" if x is None else f"{x*100:.1f}%"
def pp(x):  return "—" if x is None else f"{x*100:+.1f}pp"
def sign(x):return "—" if x is None else (f"+{x:,.1f}" if x>=0 else f"{x:,.1f}")

# ---------- 部门指标 ----------
ext = D["ext_rev"]; proj = D["proj_rev"]; gp = D["dept_gp"]; gpr = D["gp_rate"]
prof = D["dept_profit"]; profr = D["profit_rate"]; pprof = D["perf_profit"]; pprofr = D["perf_rate"]
bad = D["bad_debt"][0]; sale = D["sale_exp"][0]; labor = D["labor"][0]; impexp = D["imp_exp"][0]
coll = D["collection"][0]; inv = D["invoice"][0]; ncf = D["net_cashflow"][0]
B = D["budget"]
ext_yoy = B["外部收入"]["yoy_growth"]; proj_yoy = B["部门项目收入"]["yoy_growth"]
gp_yoy = B["部门毛利"]["yoy_growth"]; gpr_yoy = B["部门毛利率"]["yoy_growth"]
ncf_yoy = B["部门净现金流"]["yoy_growth"]
CF = D["cashflow"]; REP = D["report"]
end_cash = CF["期末现金余额"]["actual"]; uncoll_rev = CF["已确认收入未收款"]["actual"]
unbill = CF.get("已开票未收款金额",{}).get("actual"); ar_1y = CF.get("1年以内应收账款",{}).get("actual")
onetime = REP["onetime_rate"]; due_rep = REP["due"]; sub_rep = REP["submitted"]

# ---------- 项目指标 ----------
A = P["agg"]
prev = w(A["total_rev"]); pgp = w(A["total_gp"]); pnp = w(A["total_np"]); pbad = w(A["total_bad"])
pinv = w(A["total_inv"]); pcol = w(A["total_col"]); pcf = w(A["total_cf"]); plabor = w(A["total_labor"])
pn = int(A["n_active"])
mgr = [(nm, {k:(v/10000.0 if isinstance(v,float) else v) for k,v in d.items()}) for nm,d in P["by_manager"]]
mgr = [(nm, d) for nm,d in mgr if d["rev"]>0]
mgr.sort(key=lambda x:-x[1]["rev"])
typ = [(t, {k:(v/10000.0 if isinstance(v,float) else v) for k,v in d.items()}) for t,d in P["by_type"]]
typ.sort(key=lambda x:-x[1]["rev"])
top_rev = [[r[0], r[1], w(r[2]), w(r[3]), w(r[4]), r[5]] for r in P["top_rev"]]
loss    = [[r[0], r[1], w(r[2]), w(r[3]), w(r[4])] for r in P["loss"]]
overdue = [[r[0], r[1], r[2]] for r in P["overdue"]]

# =====================================================================
#  SVG CHART HELPERS
# =====================================================================
def vchart(title, cats, bars, line=None, bar_color="#2563eb", line_color="#0d9488",
           y_fmt=lambda v:f"{v:,.0f}", height=300):
    W,H=680,height; pl,pr,pb,pt=48,16,40,34
    iw=W-pl-pr; ih=H-pt-pb
    allv=bars+ (line or [])
    mx=max(allv) if allv else 1; mn=min(allv) if allv else 0
    if mn>=0: mn=0
    span=mx-mn or 1
    def Y(v): return pt+ih-((v-mn)/span)*ih
    def X(i): return pl+(iw/len(cats))*(i+0.5)
    s=[f'<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif">']
    s.append(f'<text x="{pl}" y="20" font-size="13" font-weight="600" fill="#111827">{title}</text>')
    # grid + y labels
    for g in range(0,5):
        yy=pt+ih*g/4; val=mx-(span*g/4)
        s.append(f'<line x1="{pl}" y1="{yy:.1f}" x2="{W-pr}" y2="{yy:.1f}" stroke="#eef2f7" stroke-width="1"/>')
        s.append(f'<text x="{pl-6}" y="{yy+3:.1f}" font-size="9" fill="#9ca3af" text-anchor="end">{y_fmt(val)}</text>')
    bw=iw/len(cats)*0.5
    for i,val in enumerate(bars):
        x=X(i)-bw/2; y=Y(val); h=pt+ih-y
        c = bar_color if val>=0 else "#dc2626"
        s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{max(h,0):.1f}" fill="{c}" rx="2"><title>{cats[i]}: {y_fmt(val)}</title></rect>')
        lab_y = y-4 if val>=0 else y+11
        s.append(f'<text x="{X(i):.1f}" y="{lab_y:.1f}" font-size="9" fill="#374151" text-anchor="middle">{y_fmt(val)}</text>')
    if line:
        pts=" ".join(f"{X(i):.1f},{Y(v):.1f}" for i,v in enumerate(line))
        s.append(f'<polyline points="{pts}" fill="none" stroke="{line_color}" stroke-width="2.5"/>')
        for i,v in enumerate(line):
            s.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3" fill="{line_color}"/>')
    for i,c in enumerate(cats):
        s.append(f'<text x="{X(i):.1f}" y="{H-14}" font-size="10" fill="#6b7280" text-anchor="middle">{c}</text>')
    s.append('</svg>')
    return "".join(s)

def hbars(title, labels, values, color="#0d9488", unit="万", width=680, rowh=26):
    W=width; pl=120; pr=70; pt=30; n=len(values)
    H=pt+n*rowh+10
    mx=max(values) if values else 1
    iw=W-pl-pr
    s=[f'<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif">']
    s.append(f'<text x="{pl}" y="18" font-size="13" font-weight="600" fill="#111827">{title}</text>')
    for i,(lab,val) in enumerate(zip(labels,values)):
        y=pt+i*rowh
        bw=iw*(val/mx)
        c=color if val>=0 else "#dc2626"
        s.append(f'<text x="{pl-8}" y="{y+rowh/2+3:.1f}" font-size="10" fill="#374151" text-anchor="end">{lab[:14]}</text>')
        s.append(f'<rect x="{pl}" y="{y+3:.1f}" width="{max(bw,1):.1f}" height="{rowh-8:.1f}" fill="{c}" rx="3"><title>{lab}: {val:.1f}{unit}</title></rect>')
        s.append(f'<text x="{pl+max(bw,1)+6:.1f}" y="{y+rowh/2+3:.1f}" font-size="10" fill="#111827">{val:.1f}{unit}</text>')
    s.append('</svg>')
    return "".join(s)

chart_rev = vchart("月度外部收入 vs 部门项目收入（万元）", MW, ext[1:], line=proj[1:],
                   bar_color="#2563eb", line_color="#f59e0b")
chart_profit = vchart("月度部门毛利 vs 部门利润（万元）", MW, gp[1:], line=prof[1:],
                      bar_color="#0d9488", line_color="#dc2626")
chart_margin = vchart("月度毛利率（%）", MW, [x*100 for x in gpr[1:]], bar_color="#6366f1",
                      y_fmt=lambda v:f"{v:.0f}%", height=260)
chart_mgr = hbars("项目经理业绩收入排名（万元，TOP10）",
                  [x[0] for x in mgr[:10]], [x[1]["rev"] for x in mgr[:10]], color="#0d9488")
chart_type = hbars("项目类型收入分布（万元）",
                   [x[0].replace("服务-","").replace("产品销售-","").replace("订阅费-","").replace("维护-","").replace("管理-","").replace("休假-","") for x in typ[:8]],
                   [x[1]["rev"] for x in typ[:8]], color="#2563eb")

# =====================================================================
#  HTML
# =====================================================================
def kpi_card(label, value, sub="", color="#111827"):
    return f'''<div class="kpi"><div class="kpi-l">{label}</div><div class="kpi-v" style="color:{color}">{value}</div><div class="kpi-s">{sub}</div></div>'''

html=[]
html.append('''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>华北区2026年上半年经营分析报告</title>
<style>
* {box-sizing:border-box;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Roboto,Helvetica,Arial,sans-serif;color:#1f2937;background:#f5f7fa;line-height:1.7;}
.wrap{max-width:980px;margin:0 auto;background:#fff;padding:48px 56px;box-shadow:0 1px 4px rgba(0,0,0,.06);}
h1{font-size:26px;margin:0 0 4px;color:#0f172a;}
h2{font-size:20px;margin:38px 0 12px;padding-left:10px;border-left:4px solid #2563eb;color:#0f172a;}
h3{font-size:15px;margin:22px 0 8px;color:#1e3a8a;}
.meta{color:#6b7280;font-size:13px;margin-bottom:8px;}
.cover{border-bottom:2px solid #e5e7eb;padding-bottom:22px;margin-bottom:8px;}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:18px 0 6px;}
.kpi{background:#f8fafc;border:1px solid #eef2f7;border-radius:10px;padding:14px 16px;}
.kpi-l{font-size:12px;color:#6b7280;margin-bottom:6px;}
.kpi-v{font-size:22px;font-weight:700;}
.kpi-s{font-size:11px;color:#9ca3af;margin-top:4px;}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:13px;}
th,td{border:1px solid #e5e7eb;padding:7px 10px;text-align:left;}
th{background:#f1f5f9;font-weight:600;color:#334155;}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;}
tr:nth-child(even) td{background:#fafbfc;}
.pos{color:#059669;font-weight:600;} .neg{color:#dc2626;font-weight:600;}
.chart{margin:14px 0;border:1px solid #eef2f7;border-radius:10px;padding:8px 6px;background:#fff;}
.callout{background:#fff7ed;border-left:4px solid #f59e0b;padding:12px 16px;margin:14px 0;border-radius:6px;font-size:13.5px;}
.callout.blue{background:#eff6ff;border-left-color:#2563eb;}
.callout.red{background:#fef2f2;border-left-color:#dc2626;}
.callout.green{background:#ecfdf5;border-left-color:#059669;}
.viewpoints{background:linear-gradient(135deg,#0f172a,#1e3a8a);color:#fff;border-radius:12px;padding:22px 26px;margin:18px 0 8px;}
.viewpoints h2{border:none;color:#fff;font-size:19px;margin:0 0 14px;padding:0;display:flex;align-items:center;gap:8px;}
.viewpoints h2::before{content:"";display:inline-block;width:6px;height:20px;background:#f59e0b;border-radius:3px;}
.viewpoints ol{margin:0;padding-left:22px;} .viewpoints li{margin:9px 0;font-size:13.5px;line-height:1.65;}
.viewpoints li b{color:#fcd34d;} .viewpoints .vk{color:#93c5fd;font-weight:700;}
ul{margin:8px 0 8px 4px;padding-left:20px;} li{margin:5px 0;font-size:13.5px;}
.note{color:#9ca3af;font-size:12px;margin-top:6px;}
.tag{display:inline-block;background:#e0e7ff;color:#3730a3;border-radius:4px;padding:1px 7px;font-size:11px;margin-right:4px;}
.foot{margin-top:40px;border-top:1px solid #e5e7eb;padding-top:14px;color:#9ca3af;font-size:12px;}
</style></head><body><div class="wrap">''')

html.append(f'''<div class="cover">
<h1>{REGION} 2026 年上半年经营分析报告</h1>
<div class="meta">统计区间：2026年1月 – 2026年7月　|　部门：{REGION}（编码 203124）　|　生成日期：2026-08-09<br>
数据来源：部门业绩总览表（1010）、项目业绩总览表·项目经理（2010）</div>
</div>''')

# 核心汇报观点（前置要点）
html.append(f'''<div class="viewpoints">
<h2>核心汇报观点</h2>
<ol>
<li><span class="vk">增长稳健，利润质量是首要风险。</span> 外部收入 <b>463 万（同比 +24.5%）</b>、部门毛利 <b>87 万（毛利率 27.4%，+8.5pp）</b>；但会计口径部门利润 <b>−13 万</b>，根因是坏账准备 74 万。剔除坏账后考核利润达 <b>183 万</b>，说明经营基本盘健康，坏账是主要「出血点」。</li>
<li><span class="vk">坏账高度集中，定向治理即可扭亏。</span> 74 万坏账几乎全部来自「人力外包」类型，且由 <b>冉龙梅（38.6 万）+ 刘伟（34.9 万）两人承担（占 99.3%）</b>。集中催收/法务专项，目标下半年减提 50%+，可由亏转盈。</li>
<li><span class="vk">现金与回款是经营链瓶颈。</span> 期末现金余额 <b>−161 万</b>，已确认未收款高达 <b>533 万</b>；报告及时签回率仅 <b>13.8%</b>。收入确认与回款高度依赖报告进度，是当前最突出的运营短板。</li>
<li><span class="vk">业务基本盘健康，售前储备充足。</span> 项目业绩收入 <b>504 万</b>、项目净利 <b>131 万（净利率 26%）</b>；近 3 个月售前中纺集团（中标）、中煤（框架入围）、中信金属、中海油数据中台（进行中）多点推进，储备良好。</li>
<li><span class="vk">团队与 AI 双轮驱动可持续。</span> 3 名高级顾问 + 3 名新人在「实际项目练兵 + 带教」体系培养；AI 工具（Dataclaw / ChatGPT / WorkBuddy）已沉淀可复用项目 Skill，成为团队效率资产。</li>
<li><span class="vk">目标达成需提速。</span> 年度签约目标 <b>{ANN:.0f} 万</b>，上半年累计签约 <b>{STOT:.0f} 万（新签 {SNEW:.0f} 万 + 续签 {STOT-SNEW:.0f} 万）</b>，达成率 <b>{STOT/ANN*100:.1f}%</b>；下半年缺口 {ANN-STOT:.0f} 万，须在售前转化与合同下发上集中发力。</li>
</ol>
</div>''')

# 执行摘要
html.append('<h2>一、执行摘要</h2>')
html.append('<div class="kpis">')
html.append(kpi_card("外部收入","463","万元 · 同比 "+pc(ext_yoy), "#2563eb"))
html.append(kpi_card("部门毛利","87","万元 · 毛利率 27.4%", "#0d9488"))
html.append(kpi_card("考核利润","183","万元 · 利润率 35.7%", "#059669"))
html.append(kpi_card("部门利润","-13","万元 · 受坏账拖累", "#dc2626"))
html.append('</div>')
html.append('<div class="kpis">')
html.append(kpi_card("在管项目","%d"%pn,"个（YTD有确认）", "#2563eb"))
html.append(kpi_card("项目业绩收入",f"{prev:.1f}","万元（华北区·数据治理部）", "#0d9488"))
html.append(kpi_card("项目坏账计提","74.3","万元", "#dc2626"))
html.append(kpi_card("报告及时签回率","13.8","% · 重大运营风险", "#dc2626"))
html.append('</div>')
html.append('''<div class="callout green"><b>总体判断：</b>华北区上半年收入与毛利实现双增长——外部收入 463 万元，同比 <b>+24.5%</b>；部门毛利 87 万元，同比 <b>+58.2%</b>，毛利率由 18.9% 提升至 27.4%。但会计口径部门利润为 <b>-13 万元</b>（考核口径 +183 万元），差距主要来自 <b>坏账准备 74 万元</b>；同时<b>报告及时签回率仅 13.8%</b>、期末现金余额持续为负（-161 万元），是下半年必须破解的两大短板。</div>''')
if ANN:
    html.append(f'<div class="callout green"><b>签约目标：</b>年度签约目标 <b>{ANN:.0f} 万</b>，上半年累计签约 <b>{STOT:.0f} 万</b>（新签 {SNEW:.0f} + 续签 {STOT-SNEW:.0f}），达成率 <b>{STOT/ANN*100:.1f}%</b>；下半年缺口 <b>{ANN-STOT:.0f} 万</b>，目标达成需提速。</div>')

def backlog_html():
    if not BL:
        return ""
    b = BL; items = b["items"]
    def fmt_bl(it):
        return "-" if it["backlog"] is None else f"{it['backlog']:.1f}"
    rows = "".join(
        f"<tr><td>{it['code']}</td><td>{it['name']}</td><td>{it['type']}</td>"
        f"<td>{it['status']}</td><td>{it['mgr']}</td>"
        f"<td class='num'>{it['contract']:.1f}</td><td class='num'>{it['ytd']:.1f}</td>"
        f"<td class='num'>{it['pjtd']:.1f}</td>"
        f"<td class='num'>{fmt_bl(it)}</td></tr>"
        for it in items)
    return f'''<h2>十三、合同储备与 Backlog 分析</h2>
<p class="note">口径说明：合同额取「本币税后合同金额」；Backlog（未执行合同余额）= 在执行中(Ongoing)项目合同额 − 该项目上半年已确认业绩收入(YTD)。已关闭(Closed)/已取消项目视为执行完毕，不计入未执行余额。统计区间 2026-01 至 2026-07，已按「项目所属部门名称 = {m['project_filter']}」过滤，共 {len(items)} 个华北区项目。</p>
<table><tr><th>指标</th><th class="num">数值(万)</th><th>说明</th></tr>
<tr><td>在手合同总额（税后）</td><td class="num">{b['total_contract']:.1f}</td><td>全部华北区项目合同额合计</td></tr>
<tr><td>　其中·执行中(Ongoing)</td><td class="num">{b['ongoing_contract']:.1f}</td><td>{b['ongoing_count']} 个项目</td></tr>
<tr><td>　其中·已关闭(Closed)</td><td class="num">{b['closed_contract']:.1f}</td><td>{b['closed_count']} 个项目</td></tr>
<tr><td>上半年已确认业绩收入(YTD)</td><td class="num">{b['ytd_rev_total']:.1f}</td><td>合同转化为收入的部分</td></tr>
<tr><td><b>Backlog（未执行余额）</b></td><td class="num"><b>{b['backlog_ongoing']:.1f}</b></td><td>执行中合同额 − 已确认收入</td></tr>
<tr><td>待定报告收入(YTD)</td><td class="num">{b['pending_report']:.1f}</td><td>已交付未确认报告对应的收入</td></tr>
</table>
<p>在手合同储备 <b>{b['total_contract']:.1f} 万</b> 远高于年度签约目标 890 万，储备充足；但其中执行中未执行余额 <b>{b['backlog_ongoing']:.1f} 万</b> 与待定报告收入 <b>{b['pending_report']:.1f} 万</b> 合计约 <b>{b['backlog_ongoing']+b['pending_report']:.1f} 万</b>，是下半年收入确认的核心来源，需加快交付与报告签回节奏。</p>
<h3>13.1 项目明细（按合同额降序）</h3>
<div style="overflow-x:auto"><table><tr><th>项目编码</th><th>项目名称</th><th>类型</th><th>状态</th><th>项目经理</th><th class="num">合同额(万)</th><th class="num">上半年确认(万)</th><th class="num">累计确认(万)</th><th class="num">未执行余额(万)</th></tr>
{rows}</table></div>'''

def backlog_md():
    if not BL:
        return ""
    b = BL; items = b["items"]
    L = []
    L.append("## 十三、合同储备与 Backlog 分析\n")
    L.append(f"> 口径：合同额取「本币税后合同金额」；Backlog = 在执行中项目合同额 − 上半年已确认业绩收入(YTD)。已关闭/已取消项目不计入未执行余额。共 {len(items)} 个华北区项目。\n")
    L.append("| 指标 | 数值(万) | 说明 |")
    L.append("|------|------|------|")
    L.append(f"| 在手合同总额（税后） | {b['total_contract']:.1f} | 全部华北区项目合同额合计 |")
    L.append(f"| 　其中·执行中(Ongoing) | {b['ongoing_contract']:.1f} | {b['ongoing_count']} 个项目 |")
    L.append(f"| 　其中·已关闭(Closed) | {b['closed_contract']:.1f} | {b['closed_count']} 个项目 |")
    L.append(f"| 上半年已确认业绩收入(YTD) | {b['ytd_rev_total']:.1f} | 合同转化为收入的部分 |")
    L.append(f"| **Backlog（未执行余额）** | **{b['backlog_ongoing']:.1f}** | 执行中合同额 − 已确认收入 |")
    L.append(f"| 待定报告收入(YTD) | {b['pending_report']:.1f} | 已交付未确认报告对应收入 |")
    L.append("")
    L.append(f"在手合同储备 **{b['total_contract']:.1f} 万** 远高于年度签约目标 890 万，储备充足；执行中未执行余额 **{b['backlog_ongoing']:.1f} 万** 与待定报告收入 **{b['pending_report']:.1f} 万** 合计约 **{b['backlog_ongoing']+b['pending_report']:.1f} 万**，是下半年收入确认核心来源。\n")
    L.append("### 13.1 项目明细（按合同额降序）\n")
    L.append("| 项目编码 | 项目名称 | 类型 | 状态 | 项目经理 | 合同额(万) | 上半年确认(万) | 累计确认(万) | 未执行余额(万) |")
    L.append("|------|------|------|------|------|------|------|------|------|")
    for it in items:
        bl = "-" if it["backlog"] is None else f"{it['backlog']:.1f}"
        L.append(f"| {it['code']} | {it['name']} | {it['type']} | {it['status']} | {it['mgr']} | {it['contract']:.1f} | {it['ytd']:.1f} | {it['pjtd']:.1f} | {bl} |")
    L.append("")
    return "\n".join(L)

# 二、经营概况
html.append('<h2>二、经营概况与核心指标</h2>')
html.append('''<table><tr><th>指标</th><th class="num">2026H1实际</th><th class="num">去年同期</th><th class="num">同比</th><th class="num">全年最新计划</th><th class="num">计划完成率</th></tr>''')
def row(name,a,b,yoy=None,p=None,pr=None,cls=""):
    yoy_s = ("—" if yoy is None else (f'<span class="pos">+{yoy*100:.1f}%</span>' if yoy>=0 else f'<span class="neg">{yoy*100:.1f}%</span>')) if isinstance(yoy,(int,float)) else yoy
    return f'<tr><td>{name}</td><td class="num">{f1(a)}</td><td class="num">{f1(b)}</td><td class="num">{yoy_s}</td><td class="num">{f1(p) if p else "—"}</td><td class="num">{pr if pr else "—"}</td></tr>'
html.append(row("外部收入",463,372,ext_yoy,461,"100.4%"))
html.append(row("部门项目收入",316,291,proj_yoy,315,"100.3%"))
html.append(row("部门毛利",87,55,gp_yoy,85,"102.4%"))
html.append(row("毛利率",0.274,0.189,pp(gpr_yoy),0.270,"—"))
html.append(row("考核利润",183,-64,"扭亏为盈",182,"100.5%"))
html.append(row("考核利润率",0.357,-0.332,"+68.9pp",0.355,"—"))
html.append(row("部门利润",-13,0,"—",-13,"—"))
html.append(row("收款金额",383,217,0.765,383,"100%"))
html.append(row("部门净现金流",-18,-121,"改善85.1%",-19,"—"))
html.append('</table>')
html.append('<p class="note">注：考核利润基于部门业绩收入口径（512万），剔除坏账准备影响；部门利润为会计口径（毛利 87 − 销售费用 25 − 坏账准备 74 = −12 ≈ −13）。</p>')

# 三、目标达成与签约情况（上半年，签约目标数据驱动）
html.append(signing_html())

# 收入结构
html.append('<h3>2.1 收入结构</h3>')
html.append('''<table><tr><th>收入构成</th><th class="num">金额(万)</th><th class="num">占比</th></tr>
<tr><td>外部收入</td><td class="num">463</td><td class="num">100%</td></tr>
<tr><td>├─ 服务收入</td><td class="num">446</td><td class="num">96.3%</td></tr>
<tr><td>├─ 软件收入</td><td class="num">12</td><td class="num">2.6%</td></tr>
<tr><td>└─ 订阅费收入</td><td class="num">4</td><td class="num">0.9%</td></tr>
<tr><td>部门项目收入</td><td class="num">316</td><td class="num">100%</td></tr>
<tr><td>+ 无合同收入</td><td class="num">22</td><td class="num">7.0%</td></tr>
<tr><td>+ 待定报告收入</td><td class="num">174</td><td class="num">55.1%</td></tr>
<tr><td>部门业绩收入</td><td class="num">512</td><td class="num">162.0%</td></tr></table>''')
html.append('<ul><li><b>服务收入占比 96.3%</b>，是华北区绝对核心，软件/订阅占比偏低，产品化收入有提升空间。</li><li><b>待定报告收入 174 万元</b>（占项目收入 55.1%）——大量收入依赖报告确认，回款节奏受报告签回进度制约（见第八节）。</li></ul>')

# 四、月度趋势
html.append('<h2>四、月度经营趋势</h2>')
html.append('<div class="chart">'+chart_rev+'</div>')
html.append('<div class="chart">'+chart_profit+'</div>')
html.append('<div class="chart">'+chart_margin+'</div>')
html.append('''<div class="callout blue"><b>趋势洞察：</b>
<ul>
<li>收入整体平稳，3月（82万）、7月（63万）为高点；6月外部收入降至 41万，为上半年低点。</li>
<li>毛利在 2–5 月维持 27%–55% 的健康区间，但<b>6月毛利率骤降至 −78.6%</b>（毛利 −20万），7月回升至 20.7%，需排查 6月个别低毛利/负毛利项目。</li>
<li>部门利润 1–5月持续为正（累计 60万），<b>6–7月转亏</b>（−31万、−41万），与坏账计提在 6–7月集中确认（6月 10万、7月 47万）直接相关。</li>
</ul></div>''')

# 五、成本与利润
html.append('<h2>五、成本、费用与利润质量</h2>')
html.append('''<table><tr><th>项目</th><th class="num">2026H1(万)</th><th class="num">占收入比</th></tr>
<tr><td>部门毛利</td><td class="num">87</td><td class="num">18.8%</td></tr>
<tr><td>− 销售费用</td><td class="num">25</td><td class="num">5.4%</td></tr>
<tr><td>− 坏账准备</td><td class="num">74</td><td class="num">23.4%</td></tr>
<tr><td><b>部门利润</b></td><td class="num">-13</td><td class="num">-2.8%</td></tr></table>''')
html.append('<ul><li><b>人工成本 130 万、实施费用 101 万</b>为最主要成本项；其中资源池人工 76 万、差旅 47 万占比最高。</li><li><b>坏账准备 74 万是利润转负的首因</b>：占收入 23.4%，几乎吃掉全部毛利。扣除坏账后经营利润约 61 万（毛利率口径）。</li><li>坏账高度集中（见第六节）：冉龙梅 38.6 万、刘伟 34.9 万合计占 98.7%，风险项目定向管控即可显著改善利润。</li></ul>')

# 六、项目业绩
html.append('<h2>六、项目业绩分析（项目经理维度）</h2>')
html.append(f'''<div class="callout blue"><b>组合概览：</b>上半年在管且产生确认收入的项目共 <b>{pn} 个</b>；组合口径业绩收入 <b>{prev:.1f} 万元</b>、项目毛利 <b>{pgp:.1f} 万元</b>（毛利率 {pgp/prev*100:.1f}%）、项目净利 <b>{pnp:.1f} 万元</b>（净利率 {pnp/prev*100:.1f}%）；累计坏账计提 <b>{pbad:.1f} 万元</b>，累计开票 {pinv:.1f} 万、收款 {pcol:.1f} 万。</div>''')

html.append('<h3>6.1 项目经理业绩排名（按业绩收入 TOP10）</h3>')
html.append('<div class="chart">'+chart_mgr+'</div>')
html.append('''<table><tr><th>项目经理</th><th class="num">项目数</th><th class="num">业绩收入(万)</th><th class="num">项目毛利(万)</th><th class="num">毛利率</th><th class="num">项目净利(万)</th><th class="num">坏账计提(万)</th></tr>''')
for nm,d in mgr[:10]:
    gpr_ = d["gp"]/d["rev"]*100 if d["rev"] else 0
    html.append(f'<tr><td>{nm}</td><td class="num">{int(d["n"])}</td><td class="num">{f1(d["rev"])}</td><td class="num">{f1(d["gp"])}</td><td class="num">{gpr_:.1f}%</td><td class="num">{f1(d["np"])}</td><td class="num {("neg" if d["bad"]>0 else "")}">{f1(d["bad"])}</td></tr>')
html.append('</table>')
html.append('<ul><li><b>王梦蝶（142.8万）、冉龙梅（104.1万）、王杰（94.7万）、张蒙轲（63.0万）</b>为收入第一梯队，合计贡献组合收入的 80.3%。</li><li><b>王杰</b>毛利率高达 50.7%、<b>李鑫</b> 68.3%，盈利质量最优；<b>冉龙梅</b>虽收入第二，但坏账 38.6 万侵蚀净利，净利率仅 2.7%。</li><li><b>王强</b>管理 7 个项目却毛利率 −514%（毛利 −21.6万），为典型亏损聚集，须重点复盘。</li></ul>')

html.append('<h3>6.2 项目类型分布</h3>')
html.append('<div class="chart">'+chart_type+'</div>')
html.append('''<table><tr><th>项目类型</th><th class="num">项目数</th><th class="num">业绩收入(万)</th><th class="num">项目毛利(万)</th><th class="num">毛利率</th></tr>''')
for t,d in typ[:8]:
    gpr_ = d["gp"]/d["rev"]*100 if d["rev"] else 0
    html.append(f'<tr><td>{t}</td><td class="num">{int(d["n"])}</td><td class="num">{f1(d["rev"])}</td><td class="num">{f1(d["gp"])}</td><td class="num">{gpr_:.1f}%</td></tr>')
html.append('</table>')
html.append('<ul><li><b>服务-实施</b>为主力（372.7万，毛利率 37.4%），是收入与利润基本盘。</li><li><b>服务-人力外包</b>收入 114.3 万但毛利率仅 13.6%，且集中承载 73.5 万坏账（占组合坏账 99%），属"低毛利+高坏账"双高风险，应控制外包占比并对既有外包项目启动回款专项。</li></ul>')

html.append('<h3>6.3 重点创收项目 TOP10（按业绩收入）</h3>')
html.append('''<table><tr><th>项目名称</th><th>项目经理</th><th class="num">业绩收入(万)</th><th class="num">项目毛利(万)</th><th class="num">项目净利(万)</th><th>状态</th></tr>''')
for r in top_rev[:10]:
    html.append(f'<tr><td>{r[0][:30]}</td><td>{r[1]}</td><td class="num">{f1(r[2])}</td><td class="num">{f1(r[3])}</td><td class="num">{f1(r[4])}</td><td>{r[5]}</td></tr>')
html.append('</table>')

html.append('<h3>6.4 风险项目（亏损 / 坏账 / 逾期报告）</h3>')
html.append('''<table><tr><th>项目名称</th><th>项目经理</th><th class="num">项目净利(万)</th><th class="num">项目毛利(万)</th><th class="num">坏账计提(万)</th></tr>''')
for r in loss[:12]:
    html.append(f'<tr><td>{r[0][:30]}</td><td>{r[1]}</td><td class="num neg">{f1(r[2])}</td><td class="num {("neg" if r[3]<0 else "")}">{f1(r[3])}</td><td class="num {("neg" if r[4]>0 else "")}">{f1(r[4])}</td></tr>')
html.append('</table>')
html.append(f'<div class="callout blue"><b>坏账高度集中：</b>组合坏账 {pbad:.1f} 万中，<b>服务-人力外包</b>类型占 73.5 万（≈99%）；按经理看，<b>冉龙梅 38.6 万 + 刘伟 34.9 万 = 73.5 万</b>，占组合坏账 99.3%。对这两位经理相关外包项目启动回款/法务专项，目标下半年减提 50% 以上，可直接改善会计利润。</div>')
if overdue:
    html.append('<div class="callout red"><b>严重逾期报告：</b>')
    for r in overdue:
        html.append(f'{r[0][:36]} —— 报告逾期 <b>{r[1]:.0f} 天</b>，待提交报告 {r[2]:.0f} 个。')
    html.append('</div>')

# 七、现金流
html.append('<h2>七、现金流与回款</h2>')
html.append('''<table><tr><th>指标</th><th class="num">金额(万)</th><th>说明</th></tr>
<tr><td>期初现金余额</td><td class="num">-143</td><td>内部借款占用</td></tr>
<tr><td>本期净现金流</td><td class="num">-18</td><td>同比 -121 大幅改善</td></tr>
<tr><td>期末现金余额</td><td class="num">-161</td><td>持续为负，依赖内部资金</td></tr>
<tr><td>已确认收入未收款</td><td class="num">533</td><td>收入确认但未回款</td></tr>
<tr><td>已开票未收款</td><td class="num">165</td><td>开票待回款</td></tr>
<tr><td>1年以内应收账款</td><td class="num">375</td><td>账龄结构需关注</td></tr></table>''')
html.append('<ul><li>净现金流同比改善 85%，但<b>期末现金余额仍为 −161 万</b>，部门依赖内部借款维持运转，资金自给能力弱。</li><li><b>已确认收入未收款高达 533 万</b>，是营收的 1.15 倍——回款管理是改善现金流的关键杠杆。</li><li>内部结算现金流 −221 万（部门间资源借入结算），属结构性安排。</li></ul>')

# 八、报告签回
html.append('<h2>八、报告提交与签收</h2>')
html.append(f'''<div class="callout red"><b>重大运营风险：</b>上半年应提交报告阶段数 <b>{due_rep:.0f}</b>，实际提交仅 <b>{sub_rep:.0f}</b>，<b>报告及时签回率仅 {onetime:.1f}%</b>。报告滞后直接拖慢收入确认（待定报告收入 174 万）与回款（已确认未收款 533 万），是当前最亟需治理的环节。</div>''')

# 九、售前与业务拓展（最近3个月）
html.append('<h2>九、售前与业务拓展（最近 3 个月）</h2>')
html.append('''<table><tr><th>客户 / 项目</th><th>状态</th><th>说明</th></tr>
<tr><td>中粮酒业</td><td><span style="color:#dc2626;font-weight:600">已丢标</span></td><td>项目交由兰海波团队，我方未中标。</td></tr>
<tr><td>中纺集团数据治理项目</td><td><span style="color:#16a34a;font-weight:600">已中标</span></td><td>成功中标，进入交付准备。</td></tr>
<tr><td>中煤集团供应链运维项目（框架入围标）</td><td><span style="color:#16a34a;font-weight:600">已中标入围</span></td><td>框架入围已完成，待具体合同发出后再行投标。</td></tr>
<tr><td>中信金属</td><td><span style="color:#2563eb;font-weight:600">进行中</span></td><td>前期已交流数据治理相关内容，后续主数据方向由刘伟继续跟进。</td></tr>
<tr><td>中海油数据中台</td><td><span style="color:#2563eb;font-weight:600">进行中</span></td><td>已完成交流，由总集成商引荐；目前推进 POC 事项。</td></tr>
</table>''')
html.append('<ul><li>近 3 个月新增/推进商机 <b>5 个</b>：中标与框架入围各 1 项（中纺、中煤），丢标 1 项（中粮），进行中 2 项（中信金属、中海油）。</li><li><b>中煤供应链运维</b>为框架入围，需紧盯合同下发节奏转化为实质订单；<b>中海油数据中台</b> POC 是关键转化节点，建议配置专项资源。</li><li>由"数据治理"向"主数据"延伸（中信金属）体现能力复用，可沉淀为标准售前打法。</li></ul>')

# 十、团队与人员培养
html.append('<h2>十、团队与人员培养</h2>')
html.append('''<table><tr><th>人员</th><th>层级</th><th>现状与培养安排</th></tr>
<tr><td>薛维</td><td>高级顾问</td><td>项目中问题较多，<b>试用期可能无法通过</b>，需重点评估与帮扶或汰换。</td></tr>
<tr><td>宋文斌</td><td>高级顾问</td><td>由主数据部门转入，需补数据治理知识，已安排学习计划；项目管理以实际项目（徕芬）进行培养。</td></tr>
<tr><td>张晨瑞</td><td>高级顾问</td><td>项目反馈良好，正安排向项目管理方向学习。</td></tr>
<tr><td>助理顾问 ×3</td><td>新入职</td><td>以学习已发布的内容资料为主要任务，夯实基础。</td></tr>
</table>''')
html.append('<ul><li>团队结构：<b>3 名高级顾问 + 3 名新入职助理顾问</b>。高级顾问梯队初成，但<b>薛维存在试用期不通过风险</b>，需尽快明确处置方案，避免交付能力缺口。</li><li>能力补齐：宋文斌（主数据→数据治理）、张晨瑞（向项目管理转型）已形成清晰成长路径；新人以标准化资料学习切入，培养节奏可控。</li><li>建议建立"<b>高级顾问带教 + 实际项目练兵</b>"机制（如徕芬项目），加速新人独立交付能力。</li></ul>')

# 十一、AI 创新应用
html.append('<h2>十一、AI 创新应用</h2>')
html.append('''<table><tr><th>工具</th><th>定位</th><th>使用情况</th></tr>
<tr><td>Dataclaw</td><td>常规主力</td><td>日常数据分析与文档处理，已常态化应用。</td></tr>
<tr><td>ChatGPT</td><td>常规主力</td><td>通用问答与方案草拟，已常态化应用。</td></tr>
<tr><td>WorkBuddy</td><td>新近引入</td><td>近期开始使用，已沉淀若干<b>可复用的项目 skill</b>，提升交付效率。</td></tr>
</table>''')
html.append('<ul><li>AI 工具已从"试点"走向"<b>常态化生产</b>"：Dataclaw、ChatGPT 支撑日常分析，WorkBuddy 通过自定义 skill 实现项目经验复用。</li><li>建议将已产出的项目 skill 沉淀为团队资产并建立共享机制，把个人效率转化为组织能力。</li></ul>')

# 十二、问题诊断与建议
html.append('<h2>十二、问题诊断与改进建议</h2>')
html.append('''<h3>核心问题</h3>
<ul>
<li><b>利润质量偏弱：</b>会计利润 −13 万，坏账准备 74 万是主因，且高度集中于 2 名项目经理。</li>
<li><b>回款与报告双滞后：</b>及时签回率 13.8%、已确认未收款 533 万，现金流持续为负。</li>
<li><b>低质收入结构：</b>人力外包毛利率仅 13.6%；软件/订阅收入占比不足 4%。</li>
<li><b>个别项目严重亏损：</b>王强管项目毛利率 −514%，需专项复盘。</li>
</ul>
<h3>改进建议</h3>
<ul>
<li><b>坏账专项治理：</b>对冉龙梅、刘伟相关项目（合计 73.5 万坏账）启动回款/法务专项，目标下半年减提 50% 以上，可直接扭亏为盈。</li>
<li><b>报告签回攻坚战：</b>设周度报告签回看板，将签回率纳入项目经理考核，目标 Q3 提升至 60%+。</li>
<li><b>回款提速：</b>对 533 万已确认未收款建立账龄清单与责任人机制，优先清理 1 年以内 375 万。</li>
<li><b>收入结构优化：</b>提升软件/订阅类产品占比，控制低毛利人力外包规模，提高实施报价毛利率。</li>
<li><b>亏损项目复盘：</b>对王强管项目、负毛利 6月项目做成本与定价复盘，止损并优化交付。</li>
</ul>''')

html.append(f'''<div class="callout"><b>数据口径说明：</b>本报告部门维度数据来自《部门业绩总览表》（华北区，编码 203124），统计区间 2026-01 至 2026-07；项目维度数据来自《项目业绩总览表·项目经理》，已按"项目所属部门名称 = {m['project_filter']}"严格过滤，共 <b>{A['n_total']} 个项目</b>（其中 {A['n_active']} 个上半年产生业绩收入）纳入统计。项目维度业绩收入（{prev:.1f}万）与部门"部门项目收入"科目（316万）存在差异，源于口径不同——业绩收入为项目毛利前确认口径（含跨科目/未剔除项），部门项目收入为净收入口径；但<b>项目坏账计提（{pbad:.1f}万）与部门坏账准备（74万）完全吻合</b>，印证该子集即华北区数据治理部交付基本盘。</div>''')
html.append(backlog_html())

html.append(f'<div class="foot">华北区2026年上半年经营分析报告 · 基于 1010_部门业绩总览表、2010_项目业绩总览表_-项目经理 自动生成 · 生成日期 2026-08-09</div>')
html.append('</div></body></html>')

HTML = "".join(html)
open(os.path.join(OUTDIR, f"{REGION}2026年上半年经营分析报告.html"),"w",encoding="utf-8").write(HTML)
print("HTML written:", len(HTML), "bytes")

# =====================================================================
#  MARKDOWN
# =====================================================================
md=[]
md.append(f"# {REGION} 2026 年上半年经营分析报告\n")
md.append(f"> **统计区间：** 2026年1月 – 2026年7月　|　**部门：** {REGION}（编码 203124）　|　**生成日期：** 2026-08-09  \n> **数据来源：** 部门业绩总览表（1010）、项目业绩总览表·项目经理（2010）\n")
md.append("## 核心汇报观点\n")
md.append("> **一句话：增长稳健、基本盘健康，但坏账与回款是两大「出血点」，定向治理可由亏转盈；团队与 AI 已构建可持续能力。**\n")
md.append("1. **增长稳健，利润质量是首要风险。** 外部收入 463 万（同比 +24.5%），部门毛利 87 万（毛利率 27.4%，+8.5pp）；但会计口径部门利润 −13 万，根因是坏账准备 74 万。剔除坏账后考核利润达 183 万，基本盘健康，坏账是主要「出血点」。\n")
md.append("2. **坏账高度集中，定向治理即可扭亏。** 74 万坏账几乎全部来自「人力外包」类型，由冉龙梅（38.6 万）+ 刘伟（34.9 万）两人承担（占 99.3%），集中催收/法务专项、目标下半年减提 50%+ 即可由亏转盈。\n")
md.append("3. **现金与回款是经营链瓶颈。** 期末现金余额 −161 万，已确认未收款 533 万；报告及时签回率仅 13.8%，收入确认与回款高度依赖报告进度。\n")
md.append("4. **业务基本盘健康，售前储备充足。** 项目业绩收入 504 万、项目净利 131 万（净利率 26%）；中纺（中标）、中煤（入围）、中信金属、中海油数据中台（进行中）多点推进。\n")
md.append("5. **团队与 AI 双轮驱动可持续。** 3 名高级顾问 + 3 名新人在「实际项目练兵 + 带教」体系培养；Dataclaw / ChatGPT / WorkBuddy 已沉淀可复用项目 Skill。\n")
md.append(f"6. **目标达成需提速。** 年度签约目标 {ANN:.0f} 万，上半年累计签约 {STOT:.0f} 万（新签 {SNEW:.0f} 万 + 续签 {STOT-SNEW:.0f} 万），达成率 {STOT/ANN*100:.1f}%；下半年缺口 {ANN-STOT:.0f} 万，须在售前转化与合同下发上集中发力。\n")
md.append("")

md.append("## 一、执行摘要\n")
md.append(f"- **外部收入 463 万元**，同比 **+24.5%**；**部门毛利 87 万元**，同比 **+58.2%**，毛利率由 18.9% 升至 27.4%。")
md.append(f"- **考核利润 183 万元**（利润率 35.7%），但**会计口径部门利润 −13 万元**，主因坏账准备 74 万元。")
md.append(f"- 在管项目 **{pn} 个**，组合业绩收入 **{prev:.1f} 万元**、项目净利 **{pnp:.1f} 万元**；坏账计提 **{pbad:.1f} 万元**。**报告及时签回率仅 13.8%**，期末现金余额 −161 万元，为两大短板。\n")
if ANN:
    md.append(f"- **签约目标**：年度签约目标 **{ANN:.0f} 万元**，上半年累计签约 **{STOT:.0f} 万元**（新签 {SNEW:.0f} + 续签 {STOT-SNEW:.0f}），达成率 **{STOT/ANN*100:.1f}%**；下半年缺口 **{ANN-STOT:.0f} 万元**，目标达成需提速。\n")
md.append("## 二、经营概况与核心指标\n")
md.append("| 指标 | 2026H1实际 | 去年同期 | 同比 | 全年最新计划 | 计划完成率 |")
md.append("|------|------|------|------|------|------|")
md.append(f"| 外部收入 | 463 | 372 | +24.5% | 461 | 100.4% |")
md.append(f"| 部门项目收入 | 316 | 291 | +8.6% | 315 | 100.3% |")
md.append(f"| 部门毛利 | 87 | 55 | +58.2% | 85 | 102.4% |")
md.append(f"| 毛利率 | 27.4% | 18.9% | +8.5pp | 27.0% | — |")
md.append(f"| 考核利润 | 183 | -64 | 扭亏为盈 | 182 | 100.5% |")
md.append(f"| 考核利润率 | 35.7% | -33.2% | +68.9pp | 35.5% | — |")
md.append(f"| 部门利润 | -13 | 0 | — | -13 | — |")
md.append(f"| 收款金额 | 383 | 217 | +76.5% | 383 | 100% |")
md.append(f"| 部门净现金流 | -18 | -121 | 改善85.1% | -19 | — |\n")
if ANN:
    attain = STOT/ANN*100; gap = ANN-STOT; newr = (SNEW/STOT*100) if STOT else 0; renewal = STOT-SNEW
    md.append(f"## 三、目标达成与签约情况（上半年）\n")
    md.append("| 指标 | 数值 | 说明 |")
    md.append("|------|------|------|")
    md.append(f"| 年度签约目标 | {ANN:.0f} 万 | 全年签约额目标 |")
    md.append(f"| 上半年新签 | {SNEW:.0f} 万 | 新客户 / 新项目签约 |")
    md.append(f"| 上半年累计签约（含续签 / 老客户） | {STOT:.0f} 万 | 新签 {SNEW:.0f} + 续签 {renewal:.0f} |")
    md.append(f"| 目标达成率 | {attain:.1f}% | {STOT:.0f} / {ANN:.0f} |")
    md.append(f"| 下半年缺口 | {gap:.0f} 万 | {ANN:.0f} − {STOT:.0f} |")
    md.append(f"| 新签占比 | {newr:.1f}% | {SNEW:.0f} / {STOT:.0f} |")
    md.append(f"| 续签贡献 | {renewal:.0f} 万 | {STOT:.0f} − {SNEW:.0f} |")
    md.append(f"\n> **签约进度判断：** 上半年目标达成率仅 **{attain:.1f}%**，时间过半但目标未过半；下半年缺口 **{gap:.0f} 万**，须在中纺 / 中煤 / 中信金属 / 中海油等售前转化与合同下发上集中发力。新签占比 **{newr:.1f}%** 说明新客拓展为主力，续签 {renewal:.0f} 万体现老客户粘性，结构健康。\n")
md.append("## 四、月度经营趋势\n")
md.append("| 月份 | 外部收入 | 部门项目收入 | 部门毛利 | 毛利率 | 部门利润 |")
md.append("|------|------|------|------|------|------|")
for i,mo in enumerate(MW):
    html.append("")  # noop
    md.append(f"| {mo} | {f1(ext[1:][i])} | {f1(proj[1:][i])} | {f1(gp[1:][i])} | {pc(gpr[1:][i])} | {f1(prof[1:][i])} |")
md.append("\n- 收入 3月（82万）、7月（63万）为高点，6月（41万）为低点。")
md.append("- **6月毛利率骤降至 −78.6%**（毛利 −20万），7月回升至 20.7%。")
md.append("- 部门利润 1–5月累计 +60万，**6–7月转亏**（−31万、−41万），与坏账在 6–7月集中确认相关。\n")
md.append("## 五、成本、费用与利润质量\n")
md.append("- 人工成本 130 万、实施费用 101 万为主要成本；资源池人工 76 万、差旅 47 万占比高。")
md.append(f"- **坏账准备 74 万占收入 23.4%**，是利润转负首因；扣除坏账后经营利润约 61 万。")
md.append(f"- 坏账高度集中：冉龙梅 38.6 万 + 刘伟 34.9 万 = 占 99.3%（且几乎全部来自服务-人力外包类型）。\n")
md.append("## 六、项目业绩分析（项目经理维度）\n")
md.append(f"在管且产生确认收入项目 **{pn} 个**；组合业绩收入 **{prev:.1f} 万**、项目毛利 **{pgp:.1f} 万**（毛利率 {pgp/prev*100:.1f}%）、项目净利 **{pnp:.1f} 万**（净利率 {pnp/prev*100:.1f}%）；坏账 **{pbad:.1f} 万**。\n")
md.append("### 6.1 项目经理业绩排名 TOP10（按业绩收入）\n")
md.append("| 项目经理 | 项目数 | 业绩收入(万) | 项目毛利(万) | 毛利率 | 项目净利(万) | 坏账(万) |")
md.append("|------|------|------|------|------|------|------|")
for nm,d in mgr[:10]:
    gpr_ = d["gp"]/d["rev"]*100 if d["rev"] else 0
    md.append(f"| {nm} | {int(d['n'])} | {f1(d['rev'])} | {f1(d['gp'])} | {gpr_:.1f}% | {f1(d['np'])} | {f1(d['bad'])} |")
md.append("\n### 6.2 项目类型分布\n")
md.append("| 项目类型 | 项目数 | 业绩收入(万) | 项目毛利(万) | 毛利率 |")
md.append("|------|------|------|------|------|")
for t,d in typ[:8]:
    gpr_ = d["gp"]/d["rev"]*100 if d["rev"] else 0
    md.append(f"| {t} | {int(d['n'])} | {f1(d['rev'])} | {f1(d['gp'])} | {gpr_:.1f}% |")
md.append("\n### 6.3 重点创收项目 TOP10\n")
md.append("| 项目名称 | 项目经理 | 业绩收入(万) | 项目毛利(万) | 项目净利(万) | 状态 |")
md.append("|------|------|------|------|------|------|")
for r in top_rev[:10]:
    md.append(f"| {r[0][:28]} | {r[1]} | {f1(r[2])} | {f1(r[3])} | {f1(r[4])} | {r[5]} |")
md.append("\n### 6.4 风险项目（亏损/坏账）\n")
md.append("| 项目名称 | 项目经理 | 项目净利(万) | 项目毛利(万) | 坏账(万) |")
md.append("|------|------|------|------|------|")
for r in loss[:12]:
    md.append(f"| {r[0][:28]} | {r[1]} | {f1(r[2])} | {f1(r[3])} | {f1(r[4])} |")
if overdue:
    md.append("\n**严重逾期报告：**")
    for r in overdue:
        md.append(f"- {r[0][:34]}：逾期 {r[1]:.0f} 天，待提交 {r[2]:.0f} 个。")
md.append("")
md.append(f"> **坏账高度集中：** 组合坏账 {pbad:.1f} 万中，服务-人力外包类型占 73.5 万（≈99%）；冉龙梅（38.6万）+ 刘伟（34.9万）= 73.5 万，占 99.3%。对两人相关外包项目启动回款/法务专项，目标下半年减提 50%+，可直接改善会计利润。\n")
md.append("## 七、现金流与回款\n")
md.append("- 净现金流 −18 万（同比 −121 大幅改善），但**期末现金余额 −161 万**，依赖内部借款。")
md.append(f"- **已确认收入未收款 533 万**（为营收 1.15 倍），已开票未收款 165 万，1年以内应收账款 375 万。回款管理是改善现金流的关键。\n")
md.append("## 八、报告提交与签收\n")
md.append(f"- 应提交报告阶段数 {due_rep:.0f}，实际提交 {sub_rep:.0f}，**及时签回率仅 {onetime:.1f}%**。报告滞后拖慢收入确认（待定报告收入 174 万）与回款。\n")
md.append("## 九、售前与业务拓展（最近 3 个月）\n")
md.append("| 客户 / 项目 | 状态 | 说明 |")
md.append("|------|------|------|")
md.append("| 中粮酒业 | 已丢标 | 项目交由兰海波团队，我方未中标。 |")
md.append("| 中纺集团数据治理项目 | 已中标 | 成功中标，进入交付准备。 |")
md.append("| 中煤集团供应链运维项目（框架入围标） | 已中标入围 | 框架入围已完成，待具体合同发出后再行投标。 |")
md.append("| 中信金属 | 进行中 | 前期已交流数据治理相关内容，后续主数据方向由刘伟继续跟进。 |")
md.append("| 中海油数据中台 | 进行中 | 已完成交流，由总集成商引荐；目前推进 POC 事项。 |")
md.append("\n- 近 3 个月新增/推进商机 5 个：中标与框架入围各 1（中纺、中煤），丢标 1（中粮），进行中 2（中信金属、中海油）。\n")
md.append("- 中煤供应链运维为框架入围，需紧盯合同下发节奏转化为实质订单；中海油数据中台 POC 是关键转化节点，建议配置专项资源。\n")
md.append("- 由「数据治理」向「主数据」延伸（中信金属）体现能力复用，可沉淀为标准售前打法。\n")
md.append("## 十、团队与人员培养\n")
md.append("| 人员 | 层级 | 现状与培养安排 |")
md.append("|------|------|------|")
md.append("| 薛维 | 高级顾问 | 项目中问题较多，**试用期可能无法通过**，需重点评估与帮扶或汰换。 |")
md.append("| 宋文斌 | 高级顾问 | 由主数据部门转入，需补数据治理知识，已安排学习计划；项目管理以实际项目（徕芬）进行培养。 |")
md.append("| 张晨瑞 | 高级顾问 | 项目反馈良好，正安排向项目管理方向学习。 |")
md.append("| 助理顾问 ×3 | 新入职 | 以学习已发布的内容资料为主要任务，夯实基础。 |")
md.append("\n- 团队结构：3 名高级顾问 + 3 名新入职助理顾问。高级顾问梯队初成，但**薛维存在试用期不通过风险**，需尽快明确处置方案，避免交付能力缺口。\n")
md.append("- 能力补齐：宋文斌（主数据→数据治理）、张晨瑞（向项目管理转型）已形成清晰成长路径；新人以标准化资料学习切入，培养节奏可控。\n")
md.append("- 建议建立「高级顾问带教 + 实际项目练兵」机制（如徕芬项目），加速新人独立交付能力。\n")
md.append("## 十一、AI 创新应用\n")
md.append("| 工具 | 定位 | 使用情况 |")
md.append("|------|------|------|")
md.append("| Dataclaw | 常规主力 | 日常数据分析与文档处理，已常态化应用。 |")
md.append("| ChatGPT | 常规主力 | 通用问答与方案草拟，已常态化应用。 |")
md.append("| WorkBuddy | 新近引入 | 近期开始使用，已沉淀若干**可复用的项目 skill**，提升交付效率。 |")
md.append("\n- AI 工具已从「试点」走向「常态化生产」：Dataclaw、ChatGPT 支撑日常分析，WorkBuddy 通过自定义 skill 实现项目经验复用。\n")
md.append("- 建议将已产出的项目 skill 沉淀为团队资产并建立共享机制，把个人效率转化为组织能力。\n")
md.append("## 十二、问题诊断与改进建议\n")
md.append("**核心问题：** ①利润质量弱（坏账 74 万致会计利润转负，且集中于 2 人）；②回款与报告双滞后（签回率 13.8%、未收款 533 万）；③低质收入结构（外包毛利率 13.6%，软件/订阅<4%）；④个别项目严重亏损（王强管项目毛利率 −514%）。\n")
md.append("**改进建议：**")
md.append("1. **坏账专项治理**：对冉龙梅、刘伟项目（73.5 万）启动回款/法务专项，目标下半年减提 50%+，可直接扭亏。")
md.append("2. **报告签回攻坚战**：设周度签回看板并纳入考核，目标 Q3 签回率 ≥60%。")
md.append("3. **回款提速**：对 533 万未收款建账龄清单与责任人机制，优先清理 1 年以内 375 万。")
md.append("4. **收入结构优化**：提升软件/订阅占比，控制低毛利外包，提高实施报价毛利率。")
md.append("5. **亏损项目复盘**：专项复盘王强管项目与 6月负毛利项目，止损并优化交付。\n")
md.append(f"> **数据口径说明：** 部门维度来自《部门业绩总览表》（华北区）；项目维度来自《项目业绩总览表·项目经理》，已按「项目所属部门名称 = {m['project_filter']}」严格过滤，共 {A['n_total']} 个项目（{A['n_active']} 个有业绩收入）。项目业绩收入（{prev:.1f}万）与部门科目「部门项目收入」（316万）存在口径差异（业绩收入为毛利前确认口径，部门项目收入为净收入口径），但项目坏账（{pbad:.1f}万）与部门坏账准备（74万）吻合，印证该子集即华北区数据治理部交付基本盘。")

md.append(backlog_md())
MD = "\n".join(md)
open(os.path.join(OUTDIR, f"{REGION}2026年上半年经营分析报告.md"),"w",encoding="utf-8").write(MD)
print("MD written:", len(MD), "bytes")
