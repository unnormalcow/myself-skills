---
name: "drawio-compress"
description: "等比缩放 Draw.io 流程图（.drawio），保留字体、端口、边样式与连线引用不变，可批量处理。"
---

# drawio_compress

等比缩放 Draw.io 流程图（.drawio）到指定比例（典型 0.4 = 60% 压缩），严格按用户指定的"缩放对象 / 保持不变"语义执行，绝不修改 fontSize、相对端口、边样式、节点 id 或连线引用。

## 触发场景
- 需要把多个流程图统一压缩到更紧凑的画布，便于合并展示或排版
- 需要把流程图缩到适配 PPT/Word 页面大小
- 客户/同事交付了一组流程图，需要统一压缩比例

## 缩放对象（×SCALE）
- `mxGeometry` 上的 `x` / `y` / `width` / `height`（节点位置与尺寸）
- 边端点 `<mxPoint as="sourcePoint" />` 和 `<mxPoint as="targetPoint" />`
- 折线 waypoint：`<Array as="points">` 里的所有 `<mxPoint>`（不丢点）
- 画布：`pageWidth` / `pageHeight` / `dx` / `dy` / `gridSize`

## 保持不变
- `fontSize`（在 `style` 字符串内）—— 任何字体大小都不动
- 相对端口：`exitX` / `exitY` / `exitDx` / `exitDy` / `entryX` / `entryY` / `entryDx` / `entryDy`（0~1 相对量，缩了反而错）
- 边样式：`endArrow` / `endFill` / `strokeColor` / `strokeWidth` / `dashed` / `edgeStyle` 等
- 节点 `id`、连线 `source` / `target` 引用

## 使用

脚本入口：`scripts/compress_drawio.py`，支持批量处理。

```bash
# 默认：×0.4（压缩 60%），输出名加 "-压缩60"
python3 scripts/compress_drawio.py FILE.drawio [FILE2.drawio ...]

# 自定义比例与后缀
python3 scripts/compress_drawio.py --scale 0.5 --out-suffix "-半幅" FILE.drawio
```

输出命名规则：
- 默认：`{原名}-压缩{int((1-SCALE)*100)}.drawio`（例：`原名-压缩60.drawio`）
- 自定义后缀：`{原名}{suffix}.drawio`

## 工作流程

1. 读取每个 `.drawio`，先 `collect_meta()` 统计：page 数、顶点/边数、sourcePoint/targetPoint/waypoint 数、字体种类 —— 用于一致性校验。
2. 把源文件复制到目标路径（避免污染原文件，符合"回收站 > 删除"的不可逆操作保护原则）。
3. 用 `transform_diagram()` 对每个 `<diagram>`：
   - 缩放 `mxGraphModel` 的画布与网格属性
   - 对每个 `mxCell`：缩放 `mxGeometry` 的 x/y/width/height
   - 遍历 `mxGeometry` 子节点：缩放 `mxPoint as="sourcePoint"/"targetPoint"` 与 `<Array as="points">` 内的所有 `<mxPoint>`
4. 用 `assert` 强制要求缩放后的 sourcePoint / targetPoint / waypoint 计数与源文件一致 —— 这一步是"无丢失"的不变式保证。
5. 输出每个文件的统计与处理摘要。

## 校验（自动）

脚本自带断言：处理后 `sourcePoint` / `targetPoint` / `waypoint` 三个计数必须与源文件一致。否则抛 AssertionError，绝不写出不完整的结果。

## 边界与已知行为

- **浮点四舍五入**：用 `f"{v:.4f}"` 写回，max 偏差 < 0.001（对于极小值如 `0.07 → 0.028` 时相对偏差较大但不影响视觉）。
- **无 `as` 属性的 `mxPoint`**：保留不动（不破坏任何隐藏语义）。
- **多页（multi-page）**：每个 `<diagram>` 独立处理，输出文件保留所有页。
- **命名空间**：使用默认 ET 序列化，输出文件 XML 头不带 prolog，但能被 Draw.io 正常加载。

## 已知验证案例

- 福田-全业务-数据治理流程图-20260914-优化版.drawio：8 页 / 402 顶点 / 363 边 / 238 waypoints
- 国际服装-内贸、外销业务流程-整合.drawio：2 页 / 313 顶点 / 310 边 / 86 waypoints
- 金维金旭-全部门-数据治理流程图20260914-优化版.drawio：6 页 / 242 顶点 / 211 边 / 123 waypoints
- 沙田丽海-全业务-数据治理流程图-20260914-优化版.drawio：20 页 / 679 顶点 / 619 边 / 395 waypoints
- 盐城福汇-全业务-数据治理流程图-20260914-优化版.drawio：11 页 / 346 顶点 / 311 边 / 196 waypoints

5 个文件累计：483 sourcePoint + 516 targetPoint + 1038 waypoint 全部按 0.4 缩放、0 丢失；fontSize/端口/边样式/id 完全保留。

## dataclaw.json

```json
{
  "schema_version": 1,
  "display_name": "Draw.io 流程图缩放",
  "description": "等比缩放 Draw.io 流程图（.drawio）到指定比例，保持字体、端口、边样式、节点引用不变，可批量处理多个文件。"
}
```
