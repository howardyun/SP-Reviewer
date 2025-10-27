# layer_analyzer.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import os, re, glob
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Iterable, Optional, Any

try:
    import pandas as pd
except ImportError:
    pd = None  # 允许无 pandas 环境

@dataclass
class Rule:
    pattern: re.Pattern
    weight: int

@dataclass
class Category:
    name: str
    rules: List[Rule] = field(default_factory=list)

class LayerAnalyzer:
    """基于 tree.txt 的 Layer 用途识别（规则打分 + 证据路径）"""
    def __init__(self, custom_rules: Optional[Dict[str, List[Tuple[str,int]]]] = None):
        base_rules: Dict[str, List[Tuple[str,int]]] = {
            "base-os/apt": [
                (r"/var/lib/apt/",3),(r"/etc/apt/",3),(r"/var/cache/apt/",2),
                (r"/var/lib/dpkg/",3),(r"/usr/bin/apt",2)],
            "python-runtime": [
                (r"/usr/(local/)?bin/python(\d+(\.\d+)*)?$",4),
                (r"/usr/(local/)?lib/python\d+(\.\d+)?/",3),
                (r"site-packages(/|$)",3)],
            "pip/conda-cache": [
                (r"\.cache/pip/",3),(r"/pip/cache/",2),
                (r"/conda-meta/",3),(r"/pkgs/",2)],
            "node/npm/yarn": [
                (r"/node_modules(/|$)",4),(r"/package\.json$",3),
                (r"/\.pnpm-store(/|$)",2),(r"/\.yarn/(cache|releases)/",2)],
            "cuda/cudnn/tensorrt": [
                (r"/usr/local/cuda(/|$)",4),(r"libcudnn",3),
                (r"libcublas",3),(r"libnvinfer",3)],
            "dl-frameworks": [
                (r"/site-packages/torch(/|$)",4),(r"/site-packages/tensorflow(/|$)",4),
                (r"/site-packages/jaxlib(/|$)",3)],
            "hf-cache/models": [
                (r"/root/\.cache/huggingface/",4),(r"/home/.cache/huggingface/",4),
                (r"/models--[^/]+/[^/]+/",4),(r"\.(safetensors|bin)$",3),
                (r"/tokenizer\.json$",2)],
            "hf-datasets": [
                (r"/datasets/[^/]+/",3),(r"/downloads/[^/]+\.lock$",2)],
            "app-code": [
                (r"/(app|workspace|workdir|srv|home/[^/]+/app|src)(/|$)",3),
                (r"/main\.py$",3),(r"/app\.py$",3)],
            "web/runtime": [
                (r"/usr/bin/(uvicorn|gunicorn|nginx|supervisord)",3),
                (r"/etc/nginx/",3),(r"/supervisord\.conf$",3)],
            "shell/toolchain": [
                (r"/usr/bin/(curl|wget|git|bash|zsh)$",2)],
            "config/secret-risk": [
                (r"/\.env$",4),(r"/id_rsa$",5),(r"/known_hosts$",3),
                (r"/config\.(json|yml|yaml)$",2)],
        }
        if custom_rules:
            for k,v in custom_rules.items():
                base_rules.setdefault(k, []).extend(v)

        self.categories: Dict[str, Category] = {
            name: Category(name, [Rule(re.compile(p), w) for p, w in pats])
            for name, pats in base_rules.items()
        }

    def analyze(self, layers_dir: str) -> Tuple[Any, Any]:
        layer_dirs = sorted([d for d in glob.glob(os.path.join(layers_dir, "*")) if os.path.isdir(d)])
        summary_rows: List[Dict[str, Any]] = []
        signal_rows: List[Dict[str, Any]] = []

        for layer_dir in layer_dirs:
            layer_id = os.path.basename(layer_dir.rstrip("/"))
            tree_file = os.path.join(layer_dir, "tree.txt")
            if not os.path.isfile(tree_file):
                continue

            try:
                paths = self._read_paths_from_tree(tree_file)
            except Exception as e:
                summary_rows.append({
                    "layer_id": layer_id, "primary_label": "parse_error",
                    "primary_score": 0, "secondary_label": "", "secondary_score": 0,
                    "primary_examples": str(e), "secondary_examples": "", "path_count": 0
                })
                continue

            scores, hits, primary, secondary = self._score_layer(paths)
            primary_label, primary_score = (primary[0], primary[1]) if primary else ("unknown", 0)
            secondary_label, secondary_score = (secondary[0], secondary[1]) if secondary else ("", 0)

            summary_rows.append({
                "layer_id": layer_id,
                "path_count": len(paths),
                "primary_label": primary_label,
                "primary_score": primary_score,
                "secondary_label": secondary_label,
                "secondary_score": secondary_score,
                "primary_examples": "|".join(hits.get(primary_label, [])[:5]) if primary_label else "",
                "secondary_examples": "|".join(hits.get(secondary_label, [])[:5]) if secondary_label else "",
            })

            for cat, val in scores.items():
                signal_rows.append({
                    "layer_id": layer_id,
                    "category": cat,
                    "score": val,
                    "examples": "|".join(hits.get(cat, [])[:6])
                })

        if pd is not None:
            return pd.DataFrame(summary_rows), pd.DataFrame(signal_rows)
        return summary_rows, signal_rows

    def add_rules(self, category: str, patterns: List[Tuple[str,int]]):
        if category not in self.categories:
            self.categories[category] = Category(category, [])
        for p, w in patterns:
            self.categories[category].rules.append(Rule(re.compile(p), w))

    def _read_paths_from_tree(self, tree_path: str) -> List[str]:
        paths: List[str] = []
        with open(tree_path, "r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.rstrip("\n")
                if not line:
                    continue
                if any(line.lstrip().startswith(s) for s in ["│", "├", "└", "─"]):
                    s = line
                    s = s.replace("│"," ").replace("├"," ").replace("└"," ").replace("─"," ")
                    s = re.sub(r"\s+", " ", s).strip()
                    token = s.split(" ")[-1] if s else ""
                    if token and not token.startswith("("):
                        paths.append(token)
                else:
                    paths.append(line.strip())
        norm = []
        for p in paths:
            if not p:
                continue
            p = p.replace("\\", "/")
            if not p.startswith("/"):
                p = "/" + p
            norm.append(p)
        return list(dict.fromkeys(norm))

    def _score_layer(self, paths: Iterable[str]):
        scores: Counter = Counter()
        hits: Dict[str, List[str]] = defaultdict(list)

        for p in paths:
            for cat in self.categories.values():
                for rule in cat.rules:
                    if rule.pattern.search(p):
                        scores[cat.name] += rule.weight
                        if len(hits[cat.name]) < 6:
                            hits[cat.name].append(p)

        primary = scores.most_common(1)[0] if scores else None
        secondary = None
        if scores:
            for name, val in scores.most_common():
                if not primary or name != primary[0]:
                    secondary = (name, val)
                    break
        return scores, hits, primary, secondary


# =========== main() 示例 ===========
# def main():
#     layers_dir = "Z:/hf-images1/layer_top100"  # 改成你的 Top100 路径
#     analyzer = LayerAnalyzer()
#     summary, signals = analyzer.analyze(layers_dir)
#
#     print("\n[Summary 前5行]:")
#     if pd is not None:
#         print(summary.head())
#     else:
#         print(summary[:5])
#
#     print("\n[Signals 前5行]:")
#     if pd is not None:
#         print(signals.head())
#     else:
#         print(signals[:5])
def main():
    layers_dir = r"Z:\hf-images1\layer_top100"  # 改成你的路径
    analyzer = LayerAnalyzer()
    summary, signals = analyzer.analyze(layers_dir)

    # summary 可能是 DataFrame 或 list[dict]，统一转成 list[dict]
    if not isinstance(summary, list):
        summary = summary.to_dict(orient="records")

    # 按 primary_label 分组
    grouped = {}
    for row in summary:
        grouped.setdefault(row["primary_label"], []).append(row)

    # 打印每一类
    for label, items in grouped.items():
        print(f"\n=== 分类: {label} (共 {len(items)} 个layer) ===")
        for row in sorted(items, key=lambda x: x["primary_score"], reverse=True):
            print(f"- {row['layer_id']} | score={row['primary_score']} | examples={row['primary_examples']}")



if __name__ == "__main__":
    main()
