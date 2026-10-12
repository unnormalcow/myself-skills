# -*- coding: utf-8 -*-
"""生成《沙田丽海公司生产控制部数据资产目录建设调研问卷》Word 文档。
严格对齐用户提供之《福田公司销售部门数据资产目录建设调研问卷》的公文排版规范：
  · 正文/题目/目录/答行/选项 = 仿宋 12pt；题目加粗
  · 一~五 一级标题 = 黑体 16pt（Heading 1）；3.x = 黑体 14pt（Heading 2）；4.x = 黑体 12pt（Heading 3）
  · 编号 (一)(二) / 1.2.3. = 黑体 12pt 加粗；(1)(2)(3) 枚举 = 仿宋 12pt
  · 副标题/【说明】 = 楷体
  · 大标题 = 黑体 22pt；元信息 = 仿宋 12pt
  · 正文行距 1.5、段后 3pt；目录段后 4pt
  · 每个一级章节与每个 4.x 子章节前插分页符（共 13 个）
  · 目录为手工目录：一~五 + 缩进的 4.1~4.8
  · 4.6.1 表格：表头 仿宋 9pt 加粗 + 浅蓝底；内容 仿宋 9pt
"""
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()

# ---------- 页面（对齐原文件：左右3.17cm 上下2.54cm）----------
sec = doc.sections[0]
sec.left_margin = Cm(3.17); sec.right_margin = Cm(3.17)
sec.top_margin = Cm(2.54); sec.bottom_margin = Cm(2.54)

# ---------- 字体常量 ----------
FANG = '仿宋'   # 正文
HEI  = '黑体'   # 标题/编号
KAI  = '楷体'   # 副标题/说明
BLUE = '1F497D'

def set_cjk(run, font):
    run.font.name = font
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts'); rpr.append(rfonts)
    rfonts.set(qn('w:eastAsia'), font)
    rfonts.set(qn('w:ascii'), font)
    rfonts.set(qn('w:hAnsi'), font)

def set_cell(cell, text, bold, size, fill=None):
    cell.text = text
    p = cell.paragraphs[0]
    r = p.runs[0] if p.runs else p.add_run(text)
    r.bold = bold; r.font.size = Pt(size)
    set_cjk(r, FANG)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    if fill:
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd'); shd.set(qn('w:val'),'clear'); shd.set(qn('w:color'),'auto'); shd.set(qn('w:fill'), fill)
        tcPr.append(shd)

# ---------- Normal 正文样式：仿宋 12pt / 行距1.5 / 段后3 ----------
normal = doc.styles['Normal']
normal.font.name = FANG
normal.font.size = Pt(12)
normal.element.rPr.rFonts.set(qn('w:eastAsia'), FANG)
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_after = Pt(3)

# ---------- Heading 样式：黑体，段前12 段后6 ----------
for name, sz in [('Heading 1', 16), ('Heading 2', 14), ('Heading 3', 12)]:
    st = doc.styles[name]
    st.font.name = HEI; st.font.size = Pt(sz); st.font.bold = True; st.font.color.rgb = RGBColor(0,0,0)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), HEI)
    st.paragraph_format.space_before = Pt(12)
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.line_spacing = 1.15

# ---------- 通用助手 ----------
def para(text='', font=FANG, size=12, bold=False, align='left', space_after=None, indent=0, italic=False, color=None, first_indent=Pt(24)):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if align=='center' else WD_ALIGN_PARAGRAPH.LEFT
    if text:
        r = p.add_run(text); r.bold = bold; r.italic = italic; r.font.size = Pt(size)
        if color: r.font.color.rgb = color
        set_cjk(r, font)
    if space_after is not None: p.paragraph_format.space_after = Pt(space_after)
    if indent: p.paragraph_format.left_indent = Pt(indent)
    if first_indent is not None: p.paragraph_format.first_line_indent = first_indent
    return p

def title(text):
    return para(text, font=HEI, size=22, bold=True, align='center', space_after=2, first_indent=Pt(0))

def subtitle(text):
    return para(text, font=KAI, size=14, align='center', space_after=2, first_indent=Pt(0))

def meta(text):
    return para(text, font=FANG, size=12, align='center', space_after=0, first_indent=Pt(0))

def h1(text):
    p = doc.add_paragraph(text, style='Heading 1')
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Pt(0)
    return p

def h2(text):
    p = doc.add_paragraph(text, style='Heading 2')
    p.paragraph_format.first_line_indent = Pt(0)
    return p

def h3(text):
    p = doc.add_paragraph(text, style='Heading 3')
    p.paragraph_format.first_line_indent = Pt(0)
    return p

def body(text, space_after=3, indent=0):
    return para(text, font=FANG, size=12, space_after=space_after, indent=indent)

def hint(text):
    return para('【说明】' + text, font=KAI, size=12, space_after=6, italic=False)

def num_bold(text, prefix=''):
    """黑体加粗编号：(一)(二) 或 1. 2. 3."""
    return para(prefix + text, font=HEI, size=12, bold=True, space_after=2)

def enum(text, prefix=''):
    """仿宋枚举：(1)(2)(3)，首行缩进 2 字符。"""
    return para(prefix + text, font=FANG, size=12, space_after=2)

def bullet(text):
    return para('• ' + text, font=FANG, size=12, space_after=1)

def question(label, blanks=1):
    p = para(label, font=FANG, size=12, bold=True, space_after=1)
    for _ in range(blanks):
        para('答：____________________________________________________________', font=FANG, size=12, space_after=1)
    return p

def select_q(label, items, prefix='（  ）', label_bold=True):
    p = para(label, font=FANG, size=12, bold=label_bold, space_after=1)
    for it in items:
        para(prefix + '  ' + it, font=FANG, size=12, space_after=1)

def checkbox(text):
    para('□  ' + text, font=FANG, size=12, space_after=1)

def pagebreak():
    """在上一段落末尾插入分页符（对齐原文件 13 处分页）。"""
    run = doc.paragraphs[-1].add_run()
    br = OxmlElement('w:br'); br.set(qn('w:type'), 'page'); run._r.append(br)

# =================== 封面 + 目录 ===================
title('沙田丽海公司生产控制部数据资产目录建设调研问卷')
subtitle('——面向生产控制部全体人员的专题调研——')
for line in ['编制单位：数据治理工作组','版    本：V1.0','编制日期：2026年7月','密    级：内部资料']:
    meta(line)
pagebreak()   # 封面独立成页，目录另起一页
para('', space_after=6)
p_toc = doc.add_paragraph('目  录', style='Heading 1')
p_toc.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_toc.paragraph_format.first_line_indent = Pt(0)
toc = [
    '一、项目背景','二、项目目标','三、调研目的与范围','四、调研问题',
    '    4.1 生产控制业务概况','    4.2 物料·BOM·工艺主数据','    4.3 生产工单与执行流程',
    '    4.4 生产计划·排产与委外管理','    4.5 生产数据与报表','    4.6 数据标准化与主数据',
    '    4.7 数据安全管理','    4.8 使用痛点与优化需求','五、附录：受访者信息',
]
for t in toc:
    para(t, font=FANG, size=12, space_after=4, first_indent=Pt(0))
pagebreak()   # 目录 → 一、项目背景 起新页

# =================== 一、项目背景 ===================
h1('一、项目背景')
body('当前，新一轮科技革命和产业变革加速演进，党中央、国务院高度重视数字经济发展，明确提出要加快建设数字中国，推进产业数字化转型升级。国务院国资委印发了《关于加快推进国有企业数字化转型工作的通知》，要求国有企业以数据为关键要素，系统推进数字化转型工作。纺织行业作为国民经济重要支柱产业，正加快从传统制造向智能化、绿色化、数字化方向转型。')
body('沙田丽海公司主要从事色布、纱线及成衣的制造与销售。生产控制部作为连接销售订单与车间执行的枢纽，承担着生产计划、物料控制、工单管理、排产调度、投料报工与在制跟踪等重要职能，日常工作产生了大量关键数据。这些数据是公司精益生产、业财一体化和经营决策的重要基础。')
body('然而，随着业务规模扩大与多品种小批量趋势加剧，生产数据管理方面的一些问题逐渐显现：一是物料、BOM、工艺路线等主数据的完整性、准确性有待提升；二是从计划到完工全链路的数据流转效率不高，存在手工衔接环节；三是生产数据的标准化程度不够，不同产品线之间数据口径存在差异；四是生产报表与在制分析手段有限，尚不能充分支撑精细化排产与成本管控需求。')
body('为此，公司决定开展生产控制部数据资产目录建设专项工作，系统摸清生产各环节的数据资产家底，建立统一的数据标准和规范。本次调研是该工作的基础环节，旨在全面了解生产控制部的业务流程、信息系统使用现状和数据管理痛点。')
pagebreak()

# =================== 二、项目目标 ===================
h1('二、项目目标')
body('本项目以"摸清家底、打通链路、建立标准、提升效能"为总体思路，具体目标如下：')
for t in ['1. 全面摸清生产数据家底。系统梳理生产控制业务各环节中产生、使用和管理的各类数据，形成完整的数据资产清单。',
          '2. 打通从计划到完工的数据链。厘清生产计划—物料需求—工单—投料—报工—完工入库全流程的数据流转关系，识别断点和盲区。',
          '3. 规范物料、BOM与工艺主数据管理。分析主数据的标准化现状，识别编码不统一、版本不一致、信息更新不及时等问题。',
          '4. 识别信息系统覆盖缺口。评估生产业务信息化系统（ERP/MES/APS等）的覆盖度、功能完整性和使用效果，明确改进方向。',
          '5. 夯实数据治理基础。为后续建立生产领域的数据管理制度、数据质量监控体系提供第一手调研资料。']:
    num_bold(t)
pagebreak()

# =================== 三、调研目的与范围 ===================
h1('三、调研目的与范围')
h2('3.1 调研目的')
for t in ['(1) 深入了解生产控制部的组织架构、业务分工和信息化系统使用现状；',
          '(2) 掌握物料、BOM、工艺路线及生产工单全生命周期的数据流转和存储情况；',
          '(3) 识别从计划到完工（Plan-to-Produce）全链路中的数据断点和薄弱环节；',
          '(4) 收集一线计划员、物控员、调度对数据管理和系统使用的真实反馈和改进建议；',
          '(5) 为生产数据资产目录的架构设计和实施路线图制定提供依据。']:
    enum(t)

h2('3.2 调研范围')
body('本次调研覆盖生产控制部的以下业务领域：', space_after=2)
num_bold('销售业务涵盖生产计划、物料需求、生产工单、投料发料、车间报工、完工入库、委外加工、产能负荷与在制管理等。涉及产品类型包括色布、纱线、成衣三大类。', '（一）')
num_bold('相关信息系统指生产控制部在业务处理过程中使用的各类信息系统，包括但不限于企业资源计划（ERP）、制造执行系统（MES）、高级计划排程（APS）、仓储管理（WMS）等。请根据实际情况作答。', '（二）')

h2('3.3 调研对象')
for t in ['生产控制部经理/主管','生产计划员（色布/纱线/成衣组）','物料控制/物控员','车间调度/工单管理员','投料/报工数据录入员']:
    bullet(t)

h2('3.4 填写说明')
for t in ['(1) 问题均基于日常工作场景提出，请用业务语言如实作答。',
          '(2) 涉及信息系统的部分，请说明使用的是哪个系统（如不便回答系统名称，写明"系统A""系统B"亦可）。',
          '(3) 对于不清楚或不确定的问题，可直接标注"不清楚"或"不适用"。',
          '(4) 您的真实反馈（包括遇到的问题和提出的改进建议）对项目建设至关重要，欢迎畅言。']:
    enum(t)
pagebreak()

# =================== 四、调研问题 ===================
h1('四、调研问题')

# 4.1
h3('4.1 生产控制业务概况')
hint('本部分旨在了解生产控制部的组织架构、业务范围和信息系统使用情况。')
question('4.1.1、生产控制部目前的组织架构如何？按产品线（色布/纱线/成衣）分组还是按职能（计划/物控/调度）分组？各组的人员规模如何？', 2)
question('4.1.2、生产控制部目前使用哪些信息系统来支撑日常工作？请列出系统名称（如ERP/MES/APS/WMS）及其主要功能。', 3)
question('4.1.3、从接单/计划、排产、工单下达、投料、报工到完工入库的全流程中，哪些环节在系统内完成，哪些环节还依赖手工或纸质方式？', 2)
question('4.1.4、色布、纱线、成衣三类产品的生产特点和业务流程是否有明显差异？（如按订单生产 vs 按库存生产、连续生产 vs 离散装配、内销 vs 外销流程差异等）', 3)
question('4.1.5、生产控制部现有多少位同事日常使用系统？系统反应速度能否满足排产与跟单的业务需要？', 2)

# 4.2
h3('4.2 物料·BOM·工艺主数据管理')
hint('本部分旨在了解物料、BOM、工艺路线等工作中心主数据的管理现状。')
question('4.2.1、目前公司有多少个活跃物料（原料、半成品、成品）？色布、纱线、成衣三类产品的物料体系是否有显著差异？各自大致数量为多少？', 2)
question('4.2.2、物料主数据包含哪些信息？（如物料编码、名称、规格、计量单位、库存参数、工艺属性等）这些信息目前在哪个系统里维护？', 3)
question('4.2.3、物料主数据、BOM的创建、变更和冻结是否有规范的审批流程？由哪个部门负责执行？是否出现过同一物料有多个编码或BOM版本不一致的情况？', 2)
question('4.2.4、工艺路线与工作中心管理：工艺路线如何在系统中维护？工作中心/产线/设备如何定义？产能、节拍等基础数据是否准确、是否及时更新？', 2)
question('4.2.5、生产配方/工艺参数（如染色配方、工艺条件）是如何管理的？（1）在系统中管理还是线下管理？（2）能否被工单/报工环节引用？（3）与质量检验标准是否关联？', 3)
question('4.2.6、委外加工管理：委外工序与委外供应商如何管理？委外加工单是否与生产工单关联？委外进度与质量数据如何回流？', 2)

# 4.3
h3('4.3 生产工单与执行流程')
hint('本部分旨在了解从生产工单创建到完工入库的全流程数据管理情况。')
question('4.3.1、请描述目前生产工单的创建流程：（1）工单是手工录入、系统自动生成还是通过其他方式创建？（2）创建一张工单大约需要多长时间？操作步骤多吗？（3）工单下达前是否有内部审核或确认流程？', 4)
question('4.3.2、色布、纱线、成衣三类产品的生产工单在处理流程上是否有差异？请分别描述。', 3)
question('4.3.3、工单执行跟踪方面：（1）工单下达后，如何传递到车间或产线？信息传递是否存在延迟或遗漏？（2）能否实时了解工单的生产进度和预计完工时间？（3）工单变更（数量调整、交期提前或推迟、取消等）在系统中有无记录和版本追溯？', 4)
question('4.3.4、投料与发料管理方面：（1）投料/发料通知单是如何生成的？由谁负责操作？（2）发料后，库存数据是否实时扣减？（3）是否存在"先领料后补单"的情况？频率如何？', 3)
question('4.3.5、报工与完工方面：（1）报工方式是什么（按工序/按个人/按设备）？（2）能否通过工单追溯到每个布卷/批次的生产过程参数、设备与质检记录？（3）完工入库数据是否及时、准确？', 3)
select_q('4.3.6、请勾选生产执行中遇到过的常见问题：',
    ['工单变更频繁，系统难以追溯变更历史','交期延误——经常不能按承诺时间完工','物料不足——排产后才发现缺料或产能不足',
     '委外协调困难，进度难以跟踪','发料后库存扣减不及时影响后续排产','生产系统与质检/库存系统数据不一致','其他（请说明）：__________'])

# 4.4
h3('4.4 生产计划·排产与委外管理')
hint('本部分旨在了解生产计划模式、排产规则与委外管理的数据管理情况（对应原调研"定价与开票"维度，按生产控制域特征替换）。')
question('4.4.1、生产计划模式是如何管理的？（1）主生产计划/物料需求计划（MPS/MRP）在哪个系统中制定或运行？（2）计划是系统运算还是手工排定？（3）计划变更（如插单、急单、缺料）能否及时更新到系统中？', 3)
question('4.4.2、排产规则方面：（1）排产依据是什么（交期优先/产能均衡/成本最优）？（2）不同产品、不同产线的排产规则是否有差异？（3）插单、急单如何处理，是否在系统中记录？', 3)
question('4.4.3、产能与负荷方面：（1）各工作中心/产线的产能数据是否准确？（2）能否方便地查询产线负荷、瓶颈与在制情况？（3）是否存在因产能不足导致的交期延误？主要原因是什么？', 3)
question('4.4.4、委外与结算方面：（1）委外加工如何管理与结算（按工时/按件/按工序）？（2）委外进度与完工数据如何跟踪和回写系统？', 2)

# 4.5
h3('4.5 生产数据与报表')
hint('本部分旨在了解生产数据的统计分析现状和报表使用情况。')
question('4.5.1、您日常需要查看哪些生产报表或数据统计？（如生产日报、产量达成率、一次合格率/良率、工时效率、在制品库存、委外进度等）这些报表是从系统直接获取还是需要手工整理？', 3)
question('4.5.2、系统中的生产数据能满足您的统计分析需求吗？是否存在"数据有但出不来"或"数据不全、不准"的情况？', 2)
question('4.5.3、在制品与库存管理方面：（1）在制与库存的对账是如何进行的？（2）能否方便地查询各车间/产线的在制数量、库存与账龄？（3）是否存在长期呆滞物料或账实不符的情况？主要原因是什么？', 3)
select_q('4.5.4、请对以下生产数据进行重要程度排序（填 1-6，1 为最关键）：',
    ['物料/BOM主数据（影响计划与工单全流程）','生产工单数据（影响排产与产能）','产能/负荷数据（影响交期达成）',
     '在制/库存数据（影响资金与齐套）','质量/良率数据（影响成本与客户满意）','成本/工费数据（影响利润核算）'])

# 4.6
h3('4.6 数据标准化与主数据')
hint('本部分旨在了解生产相关基础数据的标准化现状。')
para('4.6.1 核心数据清单', font=FANG, size=12, bold=True, space_after=2)
para('请对以下各类数据，逐一说明：（1）该数据目前在哪个系统或文件中管理；（2）数据的准确性和完整性如何；（3）是否有正式的数据管理规范。', font=FANG, size=10, space_after=4, indent=6)

cols = ['数据类别','具体内容','管理位置（系统/文件）','规范情况']
rows = [
    ['物料主数据','物料编码、名称、规格、单位、库存参数、工艺属性','',''],
    ['BOM数据','父项、子项、用量、损耗率、版本、生效日期','',''],
    ['工艺路线数据','工序、工作中心、标准工时、顺序','',''],
    ['工作中心/设备数据','设备编码、产能、节拍、状态','',''],
    ['生产工单数据','工单号、物料、数量、计划/实际起止、状态','',''],
    ['投料/发料数据','工单、物料、数量、批次、发料日期','',''],
    ['报工/完工数据','工序、数量、工时、设备、完工日期','',''],
    ['质量/检验数据','检验单、不良原因、良率、批次追溯','',''],
    ['委外数据','委外单、工序、供应商、进度、结算','',''],
    ['成本/工费数据','料/工/费归集、分摊规则、实际成本','',''],
]
try:
    table = doc.add_table(rows=1, cols=4); table.style = 'Light Grid Accent 1'
except Exception:
    table = doc.add_table(rows=1, cols=4); table.style = 'Table Grid'
table.alignment = WD_TABLE_ALIGNMENT.CENTER
hdr = table.rows[0].cells
for i,c in enumerate(cols):
    set_cell(hdr[i], c, True, 9, fill='D9E2F3')
for row in rows:
    cells = table.add_row().cells
    for i,v in enumerate(row):
        set_cell(cells[i], v, False, 9)

# 4.7
h3('4.7 数据安全管理')
hint('本部分旨在了解生产相关数据的访问控制和安全管控情况。')
question('4.7.1、生产系统的用户权限是如何管理的？各岗位（计划/物控/调度/录单）的权限划分是否合理？是否存在离职人员账号未及时清理的情况？', 2)
question('4.7.2、配方、工艺参数、成本等敏感信息是否做了访问控制？是否所有人员都能查看全部工艺与成本数据？这种机制是否合理？', 2)
question('4.7.3、工艺配方、客户专属工艺等敏感数据是否做了必要保护？您是否担心这些信息存在泄露风险？', 2)
question('4.7.4、生产单据（工单、工艺卡、配方单）电子文档是否有集中存储和权限管理？是否存在文档散落在个人电脑或共享文件夹中难以管理的情况？', 2)
question('4.7.5、关键业务操作（如BOM变更、计划调整、投料、报工）是否有操作记录？能否追溯到具体的操作人、时间和变更内容？', 2)
select_q('4.7.6、请勾选目前已实施的安全管控措施：',
    ['用户密码策略（复杂度/有效期等）','按岗位划分的系统功能权限','敏感操作（BOM变更/计划调整等）的审批流程',
     '操作日志记录','定期用户权限复审','数据备份与恢复测试'])

# 4.8
h3('4.8 使用痛点与优化需求')
hint('本部分旨在收集一线业务人员对生产数据管理的真实感受和改进期望。')
select_q('4.8.1、在您日常的生产控制工作中，数据管理方面遇到的最大困难是什么？请从以下选项中选择最突出的 3 项（填 1、2、3，1 为最痛）：',
    ['物料信息不准确、不完整','物料/BOM编码混乱，查找困难','工单处理效率低，操作步骤繁琐','数据分散在不同系统，需要来回切换',
     '报表需要手工统计，耗费大量时间','工单/工艺单据管理混乱，查找历史记录困难','工艺/配方信息不透明或更新不及时',
     '数据与实际业务对不上（如在制数、库存数）','跨部门数据不互通，需要反复沟通确认'])
body('除上述问题外，您在工作中还遇到哪些与数据相关的困扰？', space_after=2)
question('', 2)
question('4.8.2、如果让您提一项最希望在数据管理或系统功能方面实现的改进，您会提什么？', 2)
question('4.8.3、请用一句话评价当前生产控制业务中数据管理的整体水平（满分 10 分）：______分。', 1)
pagebreak()

# =================== 五、附录 ===================
h1('五、附录：受访者信息')
hint('本部分信息仅用于调研结果的分岗位分类分析，不会单独披露个人作答内容。')
question('1. 受访者姓名：________________  岗位/职务：________________', 0)
question('2. 所属部门/科室：________________  从事本岗位年限：______年', 0)
question('3. 主要负责产品线：□ 色布  □ 纱线  □ 成衣  □ 综合', 0)
question('4. 主要负责业务：□ 生产计划  □ 物料控制  □ 车间调度  □ 投料报工  □ 委外', 0)
question('5. 联系方式（用于调研确认）：________________________', 0)
para('一句话总结', font=FANG, size=12, bold=True, space_after=2)
para('请您用一句话概括数据对您生产控制工作的价值：', font=FANG, size=10, space_after=2, indent=6)
question('', 2)
para('补充说明', font=FANG, size=12, bold=True, space_after=2)
para('如果您对生产领域的数据管理还有其他建议或意见，请在此说明：', font=FANG, size=10, space_after=2, indent=6)
question('', 4)
para('', space_after=4)
end = para('—— 本问卷至此结束，感谢您的宝贵时间与真实反馈 ——', font=FANG, size=10, italic=True, align='center', first_indent=Pt(0))

out = '/workspace/沙田丽海公司-生产控制部-数据资产目录建设调研问卷20260723.docx'
doc.save(out)
print('saved:', out)
