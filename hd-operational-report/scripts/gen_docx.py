# -*- coding: utf-8 -*-
import json, sys, os
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

# 用法: python3 gen_docx.py [metrics.json路径] [输出目录] [区域显示名]
METRICS = sys.argv[1] if len(sys.argv) > 1 else "/tmp/metrics.json"
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
REGION = sys.argv[3] if len(sys.argv) > 3 else "华北区"

m = json.load(open(METRICS, encoding="utf-8"))
D=m["dept"]; P=m["projects"]; MW=["1月","2月","3月","4月","5月","6月","7月"]

# 签约目标（可选）：年度目标 / 上半年新签 / 上半年累计签约（万元）
SG = m.get("signing") or {}
BL = m.get("backlog") or {}
ANN = SG.get("annual_target") or 0
SNEW = SG.get("signed_new") or 0
STOT = SG.get("signed_total") or 0
def w(v): return None if v is None else v/10000.0
def f1(x): return "—" if x is None else f"{x:,.1f}"
def pc(x): return "—" if x is None else f"{x*100:.1f}%"

ext=D["ext_rev"]; proj=D["proj_rev"]; gp=D["dept_gp"]; gpr=D["gp_rate"]
prof=D["dept_profit"]; pprof=D["perf_profit"]; bad=D["bad_debt"][0]
B=D["budget"]; CF=D["cashflow"]; REP=D["report"]
A=P["agg"]; prev=w(A["total_rev"]); pgp=w(A["total_gp"]); pnp=w(A["total_np"]); pbad=w(A["total_bad"])
pn=int(A["n_active"])
mgr=[(nm,{k:(v/10000.0 if isinstance(v,float) else v) for k,v in d.items()}) for nm,d in P["by_manager"] if d["rev"]>0]
mgr.sort(key=lambda x:-x[1]["rev"])
typ=[(t,{k:(v/10000.0 if isinstance(v,float) else v) for k,v in d.items()}) for t,d in P["by_type"]]
typ.sort(key=lambda x:-x[1]["rev"])
top_rev=[[r[0],r[1],w(r[2]),w(r[3]),w(r[4]),r[5]] for r in P["top_rev"]]
loss=[[r[0],r[1],w(r[2]),w(r[3]),w(r[4])] for r in P["loss"]]
overdue=[[r[0],r[1],r[2]] for r in P["overdue"]]

doc=Document()
st=doc.styles["Normal"]; st.font.name="Microsoft YaHei"; st.font.size=Pt(10.5)

def H(t,lvl=1):
    h=doc.add_heading(t,level=lvl); return h
def para(t,bold=False,color=None):
    p=doc.add_paragraph(); r=p.add_run(t); r.bold=bold
    if color: r.font.color.rgb=RGBColor(*color)
    return p
def table(headers, rows, aligns=None):
    t=doc.add_table(rows=1, cols=len(headers)); t.style="Light Grid Accent 1"
    for i,h in enumerate(headers):
        c=t.rows[0].cells[i]; c.text=h
        for rr in c.paragraphs[0].runs: rr.bold=True
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row): cells[i].text=str(v)
    return t

# 封面
tp=doc.add_paragraph(); tp.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=tp.add_run(f"{REGION} 2026 年上半年经营分析报告"); r.bold=True; r.font.size=Pt(20)
doc.add_paragraph(f"统计区间：2026年1月 – 2026年7月　|　部门：{REGION}（编码 203124）　|　生成日期：2026-08-09").alignment=WD_ALIGN_PARAGRAPH.CENTER

# 核心汇报观点（前置要点）
H("核心汇报观点",1)
para("一句话：增长稳健、基本盘健康，但坏账与回款是两大「出血点」，定向治理可由亏转盈；团队与 AI 已构建可持续能力。", bold=True)
for s in [
    "1）增长稳健，利润质量是首要风险。外部收入 463 万（同比 +24.5%），部门毛利 87 万（毛利率 27.4%，+8.5pp）；但会计口径部门利润 −13 万，根因是坏账准备 74 万。剔除坏账后考核利润达 183 万，基本盘健康，坏账是主要「出血点」。",
    "2）坏账高度集中，定向治理即可扭亏。74 万坏账几乎全部来自「人力外包」类型，由冉龙梅（38.6 万）+ 刘伟（34.9 万）两人承担（占 99.3%），集中催收/法务专项、目标下半年减提 50%+ 即可由亏转盈。",
    "3）现金与回款是经营链瓶颈。期末现金余额 −161 万，已确认未收款 533 万；报告及时签回率仅 13.8%，收入确认与回款高度依赖报告进度。",
    "4）业务基本盘健康，售前储备充足。项目业绩收入 504 万、项目净利 131 万（净利率 26%）；中纺（中标）、中煤（入围）、中信金属、中海油数据中台（进行中）多点推进。",
    "5）团队与 AI 双轮驱动可持续。3 名高级顾问 + 3 名新人在「实际项目练兵 + 带教」体系培养；Dataclaw / ChatGPT / WorkBuddy 已沉淀可复用项目 Skill。"]:
    para(s)
para(f"6）目标达成需提速。年度签约目标 {ANN:.0f} 万，上半年累计签约 {STOT:.0f} 万（新签 {SNEW:.0f} 万 + 续签 {STOT-SNEW:.0f} 万），达成率 {STOT/ANN*100:.1f}%；下半年缺口 {ANN-STOT:.0f} 万，须在售前转化与合同下发上集中发力。")

H("一、执行摘要",1)
para(f"外部收入 463 万元（同比 +24.5%）；部门毛利 87 万元（同比 +58.2%，毛利率 27.4%）；考核利润 183 万元（利润率 35.7%），但会计口径部门利润 −13 万元，主因坏账准备 74 万元。在管项目 {pn} 个，组合业绩收入 {prev:.1f} 万元、项目净利 {pnp:.1f} 万元；报告及时签回率仅 {REP['onetime_rate']:.1f}%，期末现金余额 −161 万元，为两大短板。",)
if ANN:
    para(f"签约目标：年度签约目标 {ANN:.0f} 万元，上半年累计签约 {STOT:.0f} 万元（新签 {SNEW:.0f} + 续签 {STOT-SNEW:.0f}），达成率 {STOT/ANN*100:.1f}%；下半年缺口 {ANN-STOT:.0f} 万元，目标达成需提速。",)

H("二、经营概况与核心指标",1)
table(["指标","2026H1实际","去年同期","同比","全年最新计划","计划完成率"],
      [["外部收入","463","372","+24.5%","461","100.4%"],
       ["部门项目收入","316","291","+8.6%","315","100.3%"],
       ["部门毛利","87","55","+58.2%","85","102.4%"],
       ["毛利率","27.4%","18.9%","+8.5pp","27.0%","—"],
       ["考核利润","183","-64","扭亏为盈","182","100.5%"],
       ["部门利润","-13","0","—","-13","—"],
       ["收款金额","383","217","+76.5%","383","100%"],
       ["部门净现金流","-18","-121","改善85.1%","-19","—"]])

if ANN:
    H("三、目标达成与签约情况（上半年）",1)
    renewal = STOT - SNEW
    table(["指标","数值","说明"],
          [[f"年度签约目标","{ANN:.0f} 万","全年签约额目标"],
           [f"上半年新签","{SNEW:.0f} 万","新客户 / 新项目签约"],
           [f"上半年累计签约（含续签 / 老客户）","{STOT:.0f} 万",f"新签 {SNEW:.0f} + 续签 {renewal:.0f}"],
           ["目标达成率",f"{STOT/ANN*100:.1f}%",f"{STOT:.0f} / {ANN:.0f}"],
           ["下半年缺口",f"{ANN-STOT:.0f} 万",f"{ANN:.0f} − {STOT:.0f}"],
           ["新签占比",f"{(SNEW/STOT*100 if STOT else 0):.1f}%",f"{SNEW:.0f} / {STOT:.0f}"],
           ["续签贡献",f"{renewal:.0f} 万",f"{STOT:.0f} − {SNEW:.0f}"]])
    para(f"签约进度判断：上半年目标达成率仅 {STOT/ANN*100:.1f}%，时间过半但目标未过半；下半年缺口 {ANN-STOT:.0f} 万，须在中纺 / 中煤 / 中信金属 / 中海油等售前转化与合同下发上集中发力。新签占比 {(SNEW/STOT*100 if STOT else 0):.1f}% 说明新客拓展为主力，续签 {renewal:.0f} 万体现老客户粘性，结构健康。",)

H("四、月度经营趋势",1)
table(["月份","外部收入","部门项目收入","部门毛利","毛利率","部门利润"],
      [[MW[i],f1(ext[1:][i]),f1(proj[1:][i]),f1(gp[1:][i]),pc(gpr[1:][i]),f1(prof[1:][i])] for i in range(7)])
para("6月毛利率骤降至 −78.6%（毛利 −20万），7月回升至 20.7%；部门利润 1–5月累计 +60万，6–7月转亏（−31万、−41万），与坏账集中确认相关。")

H("五、成本、费用与利润质量",1)
para("人工成本 130 万、实施费用 101 万为主要成本；坏账准备 74 万占收入 23.4%，是利润转负首因。坏账高度集中：冉龙梅 38.6 万 + 刘伟 34.9 万，占 98.7%。")

H("六、项目业绩分析（项目经理维度）",1)
para(f"在管且产生确认收入项目 {pn} 个；组合业绩收入 {prev:.1f} 万、项目毛利 {pgp:.1f} 万（毛利率 {pgp/prev*100:.1f}%）、项目净利 {pnp:.1f} 万（净利率 {pnp/prev*100:.1f}%）；坏账 {pbad:.1f} 万。")
H("6.1 项目经理业绩排名 TOP10",2)
table(["项目经理","项目数","业绩收入(万)","项目毛利(万)","毛利率","项目净利(万)","坏账(万)"],
      [[nm,int(d["n"]),f1(d["rev"]),f1(d["gp"]),f"{(d['gp']/d['rev']*100 if d['rev'] else 0):.1f}%",f1(d["np"]),f1(d["bad"])] for nm,d in mgr[:10]])
H("6.2 项目类型分布",2)
table(["项目类型","项目数","业绩收入(万)","项目毛利(万)","毛利率"],
      [[t,int(d["n"]),f1(d["rev"]),f1(d["gp"]),f"{(d['gp']/d['rev']*100 if d['rev'] else 0):.1f}%"] for t,d in typ[:8]])
H("6.3 重点创收项目 TOP10",2)
table(["项目名称","项目经理","业绩收入(万)","项目毛利(万)","项目净利(万)","状态"],
      [[r[0][:28],r[1],f1(r[2]),f1(r[3]),f1(r[4]),r[5]] for r in top_rev[:10]])
H("6.4 风险项目（亏损/坏账）",2)
table(["项目名称","项目经理","项目净利(万)","项目毛利(万)","坏账(万)"],
      [[r[0][:28],r[1],f1(r[2]),f1(r[3]),f1(r[4])] for r in loss[:12]])
if overdue:
    para("严重逾期报告："+ "；".join(f"{r[0][:34]}（逾期{r[1]:.0f}天，待提交{r[2]:.0f}个）" for r in overdue), bold=True, color=(0xC0,0x00,0x00))

H("七、现金流与回款",1)
table(["指标","金额(万)","说明"],
      [["期初现金余额","-143","内部借款占用"],
       ["本期净现金流","-18","同比-121大幅改善"],
       ["期末现金余额","-161","持续为负"],
       ["已确认收入未收款","533","收入确认未回款"],
       ["已开票未收款","165","开票待回款"],
       ["1年以内应收账款","375","账龄结构需关注"]])
para("净现金流同比改善 85%，但期末现金余额仍为 −161 万；已确认收入未收款高达 533 万（为营收 1.15 倍），回款管理是关键杠杆。")

H("八、报告提交与签收",1)
para(f"应提交报告阶段数 {REP['due']:.0f}，实际提交 {REP['submitted']:.0f}，及时签回率仅 {REP['onetime_rate']:.1f}%。报告滞后拖慢收入确认（待定报告收入 174 万）与回款。", bold=True, color=(0xC0,0x00,0x00))

H("九、售前与业务拓展（最近 3 个月）",1)
table(["客户 / 项目","状态","说明"],
      [["中粮酒业","已丢标","项目交由兰海波团队，我方未中标。"],
       ["中纺集团数据治理项目","已中标","成功中标，进入交付准备。"],
       ["中煤集团供应链运维项目（框架入围标）","已中标入围","框架入围已完成，待具体合同发出后再行投标。"],
       ["中信金属","进行中","前期已交流数据治理相关内容，后续主数据方向由刘伟继续跟进。"],
       ["中海油数据中台","进行中","已完成交流，由总集成商引荐；目前推进 POC 事项。"]])
para("近 3 个月新增/推进商机 5 个：中标与框架入围各 1（中纺、中煤），丢标 1（中粮），进行中 2（中信金属、中海油）。中煤供应链运维为框架入围，需紧盯合同下发节奏转化为实质订单；中海油数据中台 POC 是关键转化节点，建议配置专项资源。由「数据治理」向「主数据」延伸（中信金属）体现能力复用，可沉淀为标准售前打法。")

H("十、团队与人员培养",1)
table(["人员","层级","现状与培养安排"],
      [["薛维","高级顾问","项目中问题较多，试用期可能无法通过，需重点评估与帮扶或汰换。"],
       ["宋文斌","高级顾问","由主数据部门转入，需补数据治理知识，已安排学习计划；项目管理以实际项目（徕芬）进行培养。"],
       ["张晨瑞","高级顾问","项目反馈良好，正安排向项目管理方向学习。"],
       ["助理顾问 ×3","新入职","以学习已发布的内容资料为主要任务，夯实基础。"]])
para("团队结构：3 名高级顾问 + 3 名新入职助理顾问。高级顾问梯队初成，但薛维存在试用期不通过风险，需尽快明确处置方案，避免交付能力缺口。能力补齐：宋文斌（主数据→数据治理）、张晨瑞（向项目管理转型）已形成清晰成长路径；新人以标准化资料学习切入，培养节奏可控。建议建立「高级顾问带教 + 实际项目练兵」机制（如徕芬项目），加速新人独立交付能力。")

H("十一、AI 创新应用",1)
table(["工具","定位","使用情况"],
      [["Dataclaw","常规主力","日常数据分析与文档处理，已常态化应用。"],
       ["ChatGPT","常规主力","通用问答与方案草拟，已常态化应用。"],
       ["WorkBuddy","新近引入","近期开始使用，已沉淀若干可复用的项目 skill，提升交付效率。"]])
para("AI 工具已从「试点」走向「常态化生产」：Dataclaw、ChatGPT 支撑日常分析，WorkBuddy 通过自定义 skill 实现项目经验复用。建议将已产出的项目 skill 沉淀为团队资产并建立共享机制，把个人效率转化为组织能力。")

H("十二、问题诊断与改进建议",1)
para("核心问题：①利润质量弱（坏账 74 万致会计利润转负，且集中于 2 人）；②回款与报告双滞后；③低质收入结构（外包毛利率 13.6%，软件/订阅<4%）；④个别项目严重亏损（王强管项目毛利率 −514%）。")
for s in ["坏账专项治理：对冉龙梅、刘伟项目（73.5 万）启动回款/法务专项，目标下半年减提 50%+。",
          "报告签回攻坚战：设周度签回看板并纳入考核，目标 Q3 签回率 ≥60%。",
          "回款提速：对 533 万未收款建账龄清单与责任人机制，优先清理 1 年以内 375 万。",
          "收入结构优化：提升软件/订阅占比，控制低毛利外包，提高实施报价毛利率。",
          "亏损项目复盘：专项复盘王强管项目与 6月负毛利项目，止损并优化交付。"]:
    doc.add_paragraph(s, style="List Number")

para(f"数据口径说明：部门维度来自《部门业绩总览表》（华北区）；项目维度来自《项目业绩总览表·项目经理》，已按「项目所属部门名称 = {m['project_filter']}」严格过滤，共 {A['n_total']} 个项目（{A['n_active']} 个有业绩收入）。项目业绩收入（{prev:.1f}万）与部门科目「部门项目收入」（316万）存在口径差异（业绩收入为毛利前确认口径，部门项目收入为净收入口径），但项目坏账（{pbad:.1f}万）与部门坏账准备（74万）吻合，印证该子集即华北区数据治理部交付基本盘。")

if BL:
    b = BL; items = b["items"]
    H("十三、合同储备与 Backlog 分析", 1)
    table(["指标", "数值(万)", "说明"],
          [["在手合同总额（税后）", f"{b['total_contract']:.1f}", "全部华北区项目合同额合计"],
           ["　其中·执行中(Ongoing)", f"{b['ongoing_contract']:.1f}", f"{b['ongoing_count']} 个项目"],
           ["　其中·已关闭(Closed)", f"{b['closed_contract']:.1f}", f"{b['closed_count']} 个项目"],
           ["上半年已确认业绩收入(YTD)", f"{b['ytd_rev_total']:.1f}", "合同转化为收入的部分"],
           ["Backlog（未执行余额）", f"{b['backlog_ongoing']:.1f}", "执行中合同额 − 已确认收入"],
           ["待定报告收入(YTD)", f"{b['pending_report']:.1f}", "已交付未确认报告对应收入"]])
    para(f"在手合同储备 {b['total_contract']:.1f} 万远高于年度签约目标 890 万，储备充足；执行中未执行余额 {b['backlog_ongoing']:.1f} 万与待定报告收入 {b['pending_report']:.1f} 万合计约 {b['backlog_ongoing']+b['pending_report']:.1f} 万，是下半年收入确认核心来源。")
    H("13.1 项目明细（按合同额降序）", 2)
    rows = [["项目编码", "名称", "类型", "状态", "经理", "合同额(万)", "上半年确认(万)", "累计确认(万)", "未执行余额(万)"]]
    for it in items:
        bl = "-" if it["backlog"] is None else f"{it['backlog']:.1f}"
        rows.append([it["code"], it["name"], it["type"], it["status"], it["mgr"],
                     f"{it['contract']:.1f}", f"{it['ytd']:.1f}", f"{it['pjtd']:.1f}", bl])
    table(rows[0], rows[1:])

doc.save(os.path.join(OUTDIR, f"{REGION}2026年上半年经营分析报告.docx"))
print("DOCX written")
