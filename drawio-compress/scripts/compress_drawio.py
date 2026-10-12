#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch uniform SCALE of Draw.io (.drawio) files.

User-specified scale rules (verbatim):
  SCALE OBJECTS (×SCALE):
    - mxGeometry x / y / width / height on every cell
    - Edge endpoint mxPoint as="sourcePoint" / as="targetPoint"
    - Waypoints: every <mxPoint> inside <Array as="points"> (none dropped)
    - Canvas: pageWidth / pageHeight / dx / dy / gridSize
  KEEP UNCHANGED:
    - fontSize (=N inside style strings) — style strings are never touched
    - Relative ports: exitX / exitY / exitDx / exitDy / entryX / entryY /
      entryDx / entryDy (these are 0..1 fractions and must NOT scale)
    - Edge style: endArrow / endFill / strokeColor / strokeWidth / dashed /
      edgeStyle etc.
    - Cell ids and edge source/target references

Usage:
    python3 compress_drawio.py [--scale 0.4] [--out-suffix "-压缩60"] FILE [FILE ...]

If --out-suffix is omitted, default is "-压缩{int((1-SCALE)*100)}".
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET


# ---------- core transform ----------

def scale_attr(elem: ET.Element, name: str, scale: float) -> None:
    v = elem.get(name)
    if v is None:
        return
    try:
        f = float(v)
    except (TypeError, ValueError):
        return
    elem.set(name, f"{f * scale:.4f}".rstrip("0").rstrip("."))


def transform_diagram(diagram: ET.Element, scale: float, counters: dict) -> None:
    model = diagram.find("mxGraphModel")
    if model is None:
        return
    root_el = model.find("root")
    if root_el is None:
        return

    # Canvas + grid
    for name in ("pageWidth", "pageHeight", "dx", "dy", "gridSize"):
        v = model.get(name)
        if v is None:
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        model.set(name, f"{f * scale:.4f}".rstrip("0").rstrip("."))

    for cell in root_el.findall("mxCell"):
        g = cell.find("mxGeometry")
        if g is None:
            continue
        # 1) mxGeometry x/y/width/height on every cell
        for n in ("x", "y", "width", "height"):
            scale_attr(g, n, scale)
        # 2) Walk mxGeometry children
        for child in list(g):
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "mxPoint":
                a = child.get("as")
                if a in ("sourcePoint", "targetPoint"):
                    scale_attr(child, "x", scale)
                    scale_attr(child, "y", scale)
                    if a == "sourcePoint":
                        counters["sourcePoint"] += 1
                    else:
                        counters["targetPoint"] += 1
                # else: free mxPoint without "as" — leave alone (rare; safe)
            elif tag == "Array" and child.get("as") == "points":
                for sub in list(child):
                    stag = sub.tag.split("}")[-1] if "}" in sub.tag else sub.tag
                    if stag == "mxPoint":
                        scale_attr(sub, "x", scale)
                        scale_attr(sub, "y", scale)
                        counters["waypoints"] += 1


# ---------- inspection ----------

def collect_meta(root: ET.Element) -> dict:
    fonts: set[int] = set()
    sp = tp = wp = verts = edges = 0
    for d in root.findall("diagram"):
        for c in d.find("mxGraphModel").find("root").findall("mxCell"):
            if c.get("vertex") == "1":
                verts += 1
            if c.get("edge") == "1":
                edges += 1
                g = c.find("mxGeometry")
                if g is None:
                    continue
                for ch in list(g):
                    tag = ch.tag.split("}")[-1] if "}" in ch.tag else ch.tag
                    if tag == "mxPoint":
                        a = ch.get("as")
                        if a == "sourcePoint":
                            sp += 1
                        elif a == "targetPoint":
                            tp += 1
                    elif tag == "Array" and ch.get("as") == "points":
                        for s in ch:
                            if s.tag.split("}")[-1] == "mxPoint":
                                wp += 1
            for m in re.findall(r"fontSize\s*=\s*(\d+)", c.get("style") or ""):
                fonts.add(int(m))
    return {
        "fonts": fonts,
        "sp": sp, "tp": tp, "wp": wp,
        "verts": verts, "edges": edges,
    }


# ---------- CLI ----------

def derive_out_name(src_path: str, scale: float, suffix: str | None) -> str:
    base, ext = os.path.splitext(os.path.basename(src_path))
    if suffix is None:
        suffix = f"-压缩{int((1 - scale) * 100)}"
    return os.path.join(os.path.dirname(src_path), base + suffix + ext)


def main() -> int:
    ap = argparse.ArgumentParser(description="Uniform-scale Draw.io files.")
    ap.add_argument("--scale", type=float, default=0.4,
                    help="scale factor (default: 0.4 = 60%% compression)")
    ap.add_argument("--out-suffix", type=str, default=None,
                    help="suffix appended before .drawio (default: -压缩{int((1-SCALE)*100)})")
    ap.add_argument("files", nargs="+", help="one or more .drawio files")
    args = ap.parse_args()

    scale = args.scale
    if scale <= 0 or scale > 1.0:
        ap.error("--scale must be in (0, 1.0]")

    overall = {"sourcePoint": 0, "targetPoint": 0, "waypoints": 0}
    print(f"Scale: {scale} (compression = {(1-scale)*100:.0f}%)\n")
    print(f"{'file':<60} {'pages':>5} {'verts':>5} {'edges':>5} {'sp':>4} {'tp':>4} {'wp':>4} fonts")
    print("-" * 110)
    for src in args.files:
        if not os.path.isfile(src):
            print(f"SKIP (not found): {src}", file=sys.stderr)
            continue
        dst = derive_out_name(src, scale, args.out_suffix)
        src_root = ET.parse(src).getroot()
        meta = collect_meta(src_root)
        print(f"{os.path.basename(src):<60} {len(src_root.findall('diagram')):>5} "
              f"{meta['verts']:>5} {meta['edges']:>5} "
              f"{meta['sp']:>4} {meta['tp']:>4} {meta['wp']:>4} {sorted(meta['fonts'])}")

        shutil.copy(src, dst)
        tree = ET.parse(dst)
        root = tree.getroot()
        counters = {"sourcePoint": 0, "targetPoint": 0, "waypoints": 0}
        for d in root.findall("diagram"):
            transform_diagram(d, scale, counters)
        # Verify counts match expected (no point dropped)
        assert counters["sourcePoint"] == meta["sp"], \
            f"{src}: sourcePoint count mismatch {counters['sourcePoint']} vs {meta['sp']}"
        assert counters["targetPoint"] == meta["tp"], \
            f"{src}: targetPoint count mismatch"
        assert counters["waypoints"] == meta["wp"], \
            f"{src}: waypoint count mismatch {counters['waypoints']} vs {meta['wp']}"

        out_xml = ET.tostring(root, encoding="utf-8").decode("utf-8")
        with open(dst, "w", encoding="utf-8") as fp:
            fp.write(out_xml)
        for k in overall:
            overall[k] += counters[k]
        print(f"  -> {os.path.basename(dst)}  ({os.path.getsize(dst)} bytes)  "
              f"sp={counters['sourcePoint']} tp={counters['targetPoint']} wp={counters['waypoints']}")

    print("\n=== Totals ===")
    print(f"sourcePoint scaled: {overall['sourcePoint']}")
    print(f"targetPoint scaled: {overall['targetPoint']}")
    print(f"waypoints scaled  : {overall['waypoints']}  (no points dropped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
