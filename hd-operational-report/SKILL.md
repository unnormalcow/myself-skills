---
name: hd-operational-report
description: |
  基于汉得(HAND) ERP 导出的两份 Excel（部门业绩总览表 + 项目业绩总览表·项目经理），
  生成「区域经营分析报告」的可复用工作流。当用户提供这两个 xlsx 并要求产出
  "区域经营分析报告 / 经营分析报告 / 上半年经营分析 / 部门+项目维度分析"时使用。
  覆盖数据抽取（本地 editor_sdk）、按组织路径精确过滤项目、部门+项目指标计算、
  自绘 SVG 图表，并产出 HTML / Markdown / 可编辑 DOCX 三版一致格式的报告。
  支持用户在成稿后追加自定义章节（售前/人员/AI创新等），由 Agent 判断插入位置。
agent_created: true
---

# HD-Operational-Report（区域经营分析报告生成）

## Overview

把汉得 ERP 导出的两份标准工作簿，转化为一份数据驱动、含图表与结论建议的
「区域经营分析报告」。输出三版一致格式：HTML（含自绘 SVG 图表，可浏览器预览）、
Markdown（源）、DOCX（可编辑）。整条流水线确定性、可复跑，避免每次重新摸索抽取/过滤/口径。

## 何时使用

- 用户提供 `1010_部门业绩总览表.xlsx` 与 `2010_项目业绩总览表_-项目经理.xlsx`（或等价命名），
  并希望生成经营/半年度分析报告。
- 需要"部门维度 + 项目维度（项目经理）"双视角，且项目必须归属到**指定区域/部门路径**。
- 用户想在报告里追加章节（如售前、人员培养、AI 创新），由 Agent 决定插在哪。

## 输入文件（必须，缺一不可）

| 文件 | 含义 |
|---|---|
| `1010_部门业绩总览表.xlsx` | 部门经营总表（6 个 sheet：预算/关键指标/总表/现金流量表/展开/业绩绩效表） |
| `2010_项目业绩总览表_-项目经理.xlsx` | 项目经理维度的项目组合总表（1 个 sheet，含 YTD 列） |

注：数据字典、列索引、过滤路径、口径关系见 `references/schema.md`，**生成前先读它**。

## 工作流（按顺序执行）

全部脚本位于 `scripts/`，用托管 Python 运行
（`/Users/Mac/.workbuddy/binaries/python/versions/3.13.12/bin/python3`；
DOCX 生成用 venv `/Users/Mac/.workbuddy/binaries/python/envs/default/bin/python`，已装 python-docx）。

### Step 1 — 抽取 CSV
```bash
python3 scripts/extract.py 部门表.xlsx 项目表.xlsx 输出目录/_data
```
通过本地 `editor_sdk` 的 `sheet_get_cell_data(return_csv=true)` 把 7 张表导出为 CSV。
（注意：`sheet_get_cell_data` 返回 `{"csv_data": "..."}`，脚本已处理 JSON 解析；
`editor_sdk` 的 `open_file` 是异步的，脚本内部已先 open 再读。）

### Step 2 — 计算指标 → metrics.json
```bash
python3 scripts/analyze.py 输出目录/_data "组织过滤全路径" 输出目录/metrics.json [签约目标.json]
```
默认过滤路径：`Global事业部群.产业数智化.数智平台事业部.数据治理部.华北区`。
**关键**：项目按「项目所属部门名称」(列14) 的**精确全路径**过滤，非模糊子串；
活跃口径 = 业绩收入大于 0。输出 `metrics.json`（部门+项目全量指标，供 Step 3 消费）。
可选第 4 参数传签约目标 json（`{"annual_target":890,"signed_new":171,"signed_total":327}`，单位万元），
并入 `metrics.json["signing"]`，使报告生成「三、目标达成与签约情况」章节。
示例文件见 `signing_example.json`（华北区 890/171/327），可直接复用：`python3 scripts/analyze.py _data "组织路径" metrics.json signing_example.json`。

### Step 2.5 — 提取 Backlog（可选）→ metrics.json["backlog"]
```bash
pip install openpyxl   # 仅首次需要
python3 scripts/extract_backlog.py "2010_项目业绩总览表_-项目经理 (1).xlsx" "组织过滤全路径" 输出目录/metrics.json
```
直接读项目业绩总览表 xlsx，按列14 精确过滤，计算合同储备与 Backlog 统计 + 全量项目明细，
并入 `metrics.json["backlog"]`，使报告生成「十三、合同储备与 Backlog 分析」章节（含明细表）。
⚠️ 金额列为「带千分位逗号的文本」，脚本已内置去逗号处理；如需自行取数务必先 `str.replace(",","")` 再转 float。

### Step 3 — 生成 HTML + MD
```bash
python3 scripts/gen_html_md.py metrics.json 输出目录 区域显示名
```

### Step 4 — 生成 DOCX
```bash
python3 scripts/gen_docx.py metrics.json 输出目录 区域显示名
```

输出：`{区域}2026年上半年经营分析报告.{html,md,docx}`。

注：区域名、组织过滤路径均作为参数，换区域时只改参数，无需改脚本逻辑。
报告中的编辑性叙述（核心汇报观点、结论建议、坏账归因等）是针对华北区数据写定的，
换区域后 Agent 应依据 `metrics.json` 重新生成这些叙述，或保留结构仅替换数据。

## 已知坑（务必规避，详见 `references/schema.md` 第五节）

1. **不要用** `tencent-docs-sheetagent` skill（本环境不可用）→ 用本地 `editor_sdk`。
2. `sheet_get_cell_data` 返回 JSON 包裹 CSV，须 `json.loads(...)["csv_data"]`。
3. **项目必须按列14 精确全路径过滤**，否则收入/坏账会被其他区域污染（曾误得 623 万/45项目，正确为 504 万/65项目/28活跃）。
4. 成本指标（坏账准备等）带负号前缀，`analyze.py` 已兼容，勿手工取负。
5. Python 字符串内中文引号用「」或全角 " "，ASCII 双引号会截断字符串。
6. 坏账归因要交叉「类型×经理×累计收款×应收」，定位到单一客户外包项目回款归零。

## 输出格式与章节

三版格式一致。默认章节（13 章）：封面 → **核心汇报观点**（最前，深色面板/导语）→
一、执行摘要 → 二、经营概况与核心指标 → **三、目标达成与签约情况（上半年）** →
四、月度经营趋势 → 五、成本/费用/利润质量 → 六、项目业绩分析（经理维度）→
七、现金流与回款 → 八、报告提交与签收 → 九、售前与业务拓展 → 十、团队与人员培养 →
十一、AI 创新应用 → 十二、问题诊断与改进建议 → **十三、合同储备与 Backlog 分析**。

**三、目标达成与签约情况** 由 `metrics.json["signing"]` 驱动（可选）：提供
`annual_target / signed_new / signed_total`（万元）后自动生成，含达成率、下半年缺口、
新签占比、续签贡献等指标；不提供则跳过该章。喂入方式：运行 `analyze.py` 时传第 4 参数为
签约目标 json（`{"annual_target":890,"signed_new":171,"signed_total":327}`），见 Step 2。

**十三、合同储备与 Backlog 分析** 由 `metrics.json["backlog"]` 驱动（可选）：提供后自动生成
「在手合同总额 / 执行中·已关闭拆分 / 上半年已确认 / Backlog 未执行余额 / 待定报告收入」统计表，
以及**全量项目明细表（按合同额降序，含合同额、上半年确认、累计确认、未执行余额）**。
Backlog 口径 = 在执行中(Ongoing)项目合同额 − 该项目上半年已确认业绩收入(YTD)；已关闭/已取消不计。
喂入方式：运行 `scripts/extract_backlog.py <项目xlsx> <组织路径> metrics.json`，见 Step 2.5。

HTML 含 5 张自绘 SVG 图表（月度收入/毛利/毛利率、经理收入排名、类型分布）与 KPI 卡片；
DOCX 用 python-docx 的 Light Grid 表格样式，便于二次编辑。

## 自定义章节协议（用户追加内容时）

当用户提供额外章节文本（如"最近3个月售前情况""人员培养""AI创新"），按以下规则处理：

1. **接收内容**：用户以自然语言/要点给出章节正文，无需自带编号与位置。
2. **判断位置**：默认插入在 **「八、报告提交与签收」之后、「十二、问题诊断」之前**，
   作为"经营管理补充"类章节。若内容明显属于"结论/建议"，则置于「问题诊断」之内或之后，
   由 Agent 据语义裁定。
3. **重新编号**：新章节顺延为九、十、十一…；原"九、售前"等依次后移，"十二、问题诊断"保持末章。
   （若已存在九/十/十一，则继续往后排，例如售前=九、人员=十、AI=十一、问题诊断=十二。）
4. **落地方式**：直接编辑 `scripts/gen_html_md.py` 与 `scripts/gen_docx.py`
   中对应插入点（HTML 用 `html.append(...)`、MD 用 `md.append(...)`、DOCX 用 `H(...)`/`para(...)`），
   然后重跑 Step 3 与 Step 4 重新生成三版。
5. **一致性**：三版（HTML/MD/DOCX）必须同步加入同一章节，且编号连贯；
   数字不得写死矛盾值，引用数据一律取自 `metrics.json`。
6. **口径说明**：若追加章节含敏感人事评价（如"某员工试用期风险"），如实写入但提醒用户注意保密范围。

## Resources

- `scripts/extract.py` — xlsx → CSV 抽取（依赖本地 editor_sdk）
- `scripts/analyze.py` — CSV → metrics.json（含精确组织过滤、活跃口径）
- `scripts/gen_html_md.py` — metrics.json → HTML + Markdown
- `scripts/gen_docx.py` — metrics.json → DOCX（需 venv python-docx）
- `signing_example.json` — 签约目标示例（华北区 890/171/327，单位万元），Step 2 第 4 参数可直接引用
- `references/schema.md` — 数据字典、列索引、过滤路径、口径关系、踩坑清单、输出规范
