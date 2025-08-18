# from itertools import chain
#
# import numpy as np
# import matplotlib.ticker as mtick
# import pandas as pd
# import sqlite3
# import seaborn as sns
# from matplotlib import pyplot as plt
#
# conn = sqlite3.connect(
#     r'C:\Users\szk\Desktop\code\SP-Reviewer\dockerPull\PackageAnalysis\packages_info_code\merge.db')  # 连接到数据库
# data = pd.read_csv('../../Data/Pypi/pypi_osv/merged_result.csv')  # 读取CSV数据
# cursor = conn.cursor()
# cursor.execute("SELECT repo_name,pypi_info_list FROM kv_data ")  # 获取pypi_info_list信息
# space = cursor.fetchall()  # 获取pypi_info_list信息
#
# # 创建一个新的DataFrame，只包含Package Name和Package Version列
# data_filtered = data[['Package Name', 'Package Version', "Aliases", "Cwe_Ids"]]
#
# # 遍历space，对于每个pypi_info_list，筛选出对应的CVE和CWE信息，并添加到space中
# for index, item in enumerate(space):
#     cve_cwe_info = []
#     for pkg in eval(item[1]):  # item[1] is pypi_info_list
#         pkg_name, pkg_version = pkg.split('-')
#         filtered_data = data_filtered[
#             (data_filtered['Package Name'] == pkg_name) & (data_filtered['Package Version'] == pkg_version)]
#         if not filtered_data.empty:
#             aliases = filtered_data['Aliases'].dropna().tolist()
#             cve_list = [a
#                         for a in aliases
#                         if isinstance(a, str) and a.lower().startswith('cve')]
#             cve_list = list(set(cve_list))
#             cve_cwe_info.append({
#                 'CVE': cve_list,
#                 'CWE': filtered_data['Cwe_Ids'].values[0]
#             })
#     space[index] = (item[0], item[1], cve_cwe_info)
#
# # 创建一个新的DataFrame来保存CVE和CWE信息
# cve_cwe_df = pd.DataFrame([(item[0], cve_info['CVE'], cve_info['CWE']) for item in space for cve_info in item[2]],
#                           columns=['Repo Name', 'CVE', 'CWE'])
# grouped = (
#     cve_cwe_df
#     .groupby('Repo Name')
#     .agg({
#         # 把所有小 list 铺平后去重
#         'CVE': lambda series: list(set(chain.from_iterable(series))),
#         # 直接对每个 CWE 去重
#         'CWE': lambda series: list(set(series))
#     })
#     .reset_index()
# )
# # 将新的DataFrame保存到CSV文件中
# grouped.to_csv('cve_cwe_info.csv', index=False)
import csv

import pandas as pd

# """
# 从 merge.db 与 merged_result.csv 生成 repo→CVE/CWE 的汇总表 cve_cwe_info.csv
# """
# from __future__ import annotations
#
# import sqlite3
# from pathlib import Path
# from typing import Iterable
#
# import pandas as pd
#
# # ---------------------- 路径配置 ---------------------- #
# BASE_DIR = Path(__file__).resolve().parent
# DB_PATH = r"C:\Users\szk\Desktop\code\SP-Reviewer\dockerPull\PackageAnalysis\packages_info_code\merge.db"
# CSV_PATH = '../../Data/Pypi/pypi_osv/merged_result.csv'
# OUT_PATH = "cve_cwe_info.csv"
#
# # ---------------------- 工具函数 ---------------------- #
# def load_kv_data(db: Path | str) -> pd.DataFrame:
#     """从 kv_data 表一次性取出 repo_name、pypi_info_list"""
#     with sqlite3.connect(db) as conn:
#         return pd.read_sql(
#             "SELECT repo_name, pypi_info_list FROM kv_data  ",
#             conn,
#         )
#
# def parse_pkg_version(pypi_info_list: str) -> pd.DataFrame:
#     """
#     把形如 ["pkg1-1.0", "pkg2-2.3"] 的字符串解析成 DataFrame
#     columns: repo_name, Package Name, Package Version
#     """
#     try:
#         records = []
#         for repo_name, pairs in pypi_info_list:
#             for pair in eval(pairs, {"__builtins__": {}}, {}):
#                 pkg, ver = pair.rsplit("-", 1)
#                 records.append((repo_name, pkg, ver))
#         return pd.DataFrame.from_records(
#             records, columns=["repo_name", "Package Name", "Package Version"]
#         )
#     except Exception as e:
#         raise ValueError(f"解析 pypi_info_list 失败: {e}") from e
#
# def extract_cves(aliases) -> list[str]:
#     """从 aliases 里抽 CVE-ID 并去重"""
#     aliases = aliases.split(',')
#     return sorted(
#         {a for a in aliases if isinstance(a, str) and a.upper().startswith("CVE-")}
#     )
#
# # ---------------------- 主流程 ---------------------- #
# def build_cve_cwe_table() -> pd.DataFrame:
#     # 1. 读入三方数据
#     kv_df = load_kv_data(DB_PATH)
#     vul_df = pd.read_csv(CSV_PATH, usecols=["Package Name", "Package Version", "Aliases", "Cwe_Ids"])
#
#     # 2. 把 kv_data 的 pypi_info_list 拆成行
#     repo_pkg_df = parse_pkg_version(kv_df.values)
#
#     # 3. 关联漏洞信息
#     merged = repo_pkg_df.merge(
#         vul_df,
#         on=["Package Name", "Package Version"],
#         how="inner",
#     )
#
#     # 4. CVE/CWE 展开 & 去重
#     cve_df = (
#         merged
#         .assign(CVE=lambda df: df["Aliases"].dropna().apply(extract_cves))
#         .explode("CVE")
#         .groupby(["repo_name", "Cwe_Ids"])["CVE"]
#         .apply(lambda s: sorted(set(s.dropna())))
#         .reset_index()
#         .rename(columns={"repo_name": "Repo Name", "Cwe_Ids": "CWE"})
#     )
#
#     # 5. 同一 repo 进一步汇总
#     summary_df = (
#         cve_df
#         .groupby("Repo Name")
#         .agg(
#             CVE=("CVE", lambda s: sorted({c for lst in s for c in lst})),
#             CWE=("CWE", lambda s: sorted(set(s.dropna()))),
#         )
#         .reset_index()
#     )
#     return summary_df
#
# if __name__ == "__main__":
#     result = build_cve_cwe_table()
#     result.to_csv(OUT_PATH, index=False)
#     print(f"输出已保存至 {OUT_PATH}")
# import sqlite3
# import polars as pl
# from pathlib import Path
#
# DB_PATH = r"../../dockerPull/PackageAnalysis/packages_info_code/merge.db"
# CSV_PATH = '../../Data/Pypi/pypi_osv/merged_result.csv'
# OUT_PATH = "cve_cwe_info2.csv"
#
#
# def load_kv_data(db: str | Path) -> pl.LazyFrame:
#     conn = sqlite3.connect(db)
#     return pl.read_database(
#         query="SELECT repo_name, pypi_info_list FROM kv_data ",
#         connection=conn
#     ).lazy()
#
#
# def build_cve_cwe_table() -> pl.DataFrame:
#     kv_df = load_kv_data(DB_PATH)
#
#     # ---------- 把 pypi_info_list 拆成行 ----------
#     repo_pkg_df = (
#         kv_df
#         # 去掉前后中括号、引号，拆成 list[str]
#         .with_columns(
#             pl.col("pypi_info_list")
#             .str.strip_chars("[]")
#             .str.split(", ")
#             .list.eval(pl.element().str.strip_chars('"'))
#             .alias("items")
#         )
#         .explode("items")  # 一行一个 "pkg-ver"
#         # 用正则把 pkg 和 ver 拆开；^([^-]+)-(.+)$ -> (pkg, ver)
#         .with_columns(
#             pl.col("items")
#             .str.extract_groups(r"^(?P<PackageName>[^-]+)-(?P<PackageVersion>.+)$")
#         )
#         .unnest("items")
#         .rename({
#             "PackageName": "Package Name",
#             "PackageVersion": "Package Version"
#         })
#         .select("repo_name", "Package Name", "Package Version")
#
#     )
#
#     # ---------- 读漏洞 CSV ----------
#     vul_df = (
#         pl.scan_csv(CSV_PATH)
#         .select("Package Name", "Package Version", "Aliases", "Cwe_Ids")
#     )
#
#     # ---------- 关联 & CVE 展开 ----------
#     exploded = (
#         repo_pkg_df.join(
#             vul_df,
#             on=["Package Name", "Package Version"],
#             how="inner"
#         )
#         .with_columns(
#             pl.col("Aliases")
#             .str.split(",")
#             .list.eval(pl.element().str.strip_chars())
#             .list.eval(
#                 pl.when(pl.element().str.to_uppercase().str.starts_with("CVE-"))
#                 .then(pl.element())
#             )
#             .list.drop_nulls()
#             .alias("CVE")
#         )
#         .explode("CVE")
#         .filter(pl.col("CVE").is_not_null())
#     )
#
#     # ---------- 两次 group_by ----------
#     cve_df = (
#         exploded
#         .group_by(["repo_name", "Cwe_Ids"])
#         .agg(CVE=pl.col("CVE").unique().sort())
#         .rename({"repo_name": "Repo Name", "Cwe_Ids": "CWE"})
#     )
#
#     summary_df = (
#         exploded
#         .group_by("repo_name")
#         .agg(
#             CVE=pl.col("CVE").flatten().unique().sort(),
#             CWE=pl.col("Cwe_Ids").drop_nulls().unique().sort(),
#         )
#         # -------------- 关键：把 list 转字符串 --------------
#         .with_columns(
#             pl.col("CVE").list.join(","),
#             pl.col("CWE").list.join(","),
#         )
#     )
#
#     return summary_df.collect()
#
#
# if __name__ == "__main__":
#     build_cve_cwe_table().write_csv(OUT_PATH)
#     print(f"输出已保存至 {OUT_PATH}")
# df = pd.read_csv("cve_cwe_info2.csv")
# # 2. 只保留“cve”这一列
# cve_col = df['CWE'].dropna().astype(str)
# # 3. 按逗号拆成单个 CVE，再去重/计数
# all_cves = cve_col.str.split(',', expand=True).stack()   # 变成长 Series
# all_cves = all_cves.str.strip()                          # 去掉空格
#
# # 4. 统计
# unique_cnt = all_cves.nunique()   # 不重复的 CVE 数量
# total_cnt  = all_cves.shape[0]    # 所有出现的次数
# print(f"唯一 CVE 数：{unique_cnt}")
# print(f"总 CVE 数：{total_cnt}")
# import polars as pl
#
# cwe_list = (
#     pl.read_csv("cve_cwe_info2.csv")["CWE"]
#     .str.split(",")
#     .explode()
#     .str.strip_chars()
#     .drop_nulls()
# )
# counts_df = (
#     cwe_list
#     .value_counts()
#     .sort("count", descending=True)   # or .sort("CWE") if you want alphabetical order
# )
# print(counts_df.head(10))
# top10_ratio = (
#     counts_df
#     .head(10)["count"].sum()          # 前 10 行的 count 之和
#     /
#     counts_df["count"].sum()          # 全表 count 之和
# )
# print(f"Top10 CWE 占比: {top10_ratio:.2%}")

# import polars as pl
#
# df = pl.read_csv("../../Data/Pypi/pypi_osv/merged_result.csv")
#
# df = df.with_columns(
#     pl.col("Aliases")
#     .str.split(",")  # 拆成 list[str]
#     .list.eval(  # 行内逐元素过滤
#         pl.when(pl.element().str.strip_chars('"')  # 去掉引号
#                 .str.starts_with("CVE-"))
#         .then(pl.element())  # 保留 CVE- 开头的
#         .otherwise(None)  # 其余置 None
#     )
#     .list.drop_nulls()  # 去掉 None
#     .list.join(",")  # 拼回字符串
#     .alias("Aliases")
# )
# cve_list = (
#     df
#     .select(
#         pl.col("Aliases")
#         .str.split(",")
#         .list.explode()
#         .str.strip_chars()
#     )
#     .drop_nulls()
#     .unique()  # 保留唯一 CVE
#     .to_series()  # 把单列 DataFrame → Series
#     .to_list()  # Series → Python list[str]
# )
#
# print(len(set(cve_list)))
#
# import argparse
# import json
# import sys
# import time
# from typing import List, Dict
# import requests
# from tqdm import tqdm  # pip install requests tqdm
#
# NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
#
#
# def fetch_cve(cve_id: str, api_key: str | None = None) -> Dict | None:
#     """返回单个 CVE 的完整 JSON"""
#     headers = {"User-Agent": "py-nvd-demo/1.0"}
#     params = {"cveId": cve_id}
#     if api_key:
#         headers["apiKey"] = api_key
#     try:
#         r = requests.get(NVD_URL, params=params, headers=headers, timeout=20)
#         r.raise_for_status()
#         return r.json()
#     except requests.HTTPError as e:
#         print(f"[E] {cve_id}: HTTP {e.response.status_code}", file=sys.stderr)
#     except Exception as e:
#         print(f"[E] {cve_id}: {e}", file=sys.stderr)
#     return None
#
#
# def extract_fields(raw: Dict) -> Dict:
#     """从原始 JSON 抽我们需要的字段"""
#     cve = raw["vulnerabilities"][0]["cve"]
#     # 1) 严重级别
#     severity = "N/A"
#     if "cvssMetricV31" in cve.get("metrics", {}):
#         severity = cve["metrics"]["cvssMetricV31"][0]["cvssData"]["baseSeverity"]
#     # 2) CWE 列表
#     cwes = []
#     for w in cve.get("weaknesses", []):
#         for desc in w.get("description", []):
#             if desc["lang"] == "en":
#                 cwes.append(desc["value"])
#     return {
#         "id": cve["id"],
#         "severity": severity,
#         "cwes": sorted(set(cwes)),
#     }
#
#
# def main() -> None:
#     cve_ids = ["CVE-2024-39329", "CVE-2022-29210", "CVE-2024-6827", "CVE-2023-2356", "CVE-2022-29213", "CVE-2020-5312"]
#     api_key = "53b2d447-cf3e-4596-9422-3e1d0552d4a7"
#
#     results = []
#     delay = 1 if api_key else 6.0  # NVD rate-limit guidance
#     for cid in tqdm(cve_ids, desc="Fetching"):
#         raw = fetch_cve(cid, api_key)
#         if raw:
#             results.append(extract_fields(raw))
#         time.sleep(delay)
#     with open("cve_report2.csv", "w", newline="", encoding="utf-8") as f:
#         writer = csv.DictWriter(f, fieldnames=["id", "severity", "cwes"])
#         writer.writeheader()
#         writer.writerows(results)
#     print(f"\n已导出 {len(results)} 条记录 → {"cve_report.csv"}")
#
#
# main()

# import csv
# import ast
# from collections import Counter
#
# file_path = 'cve_report.csv'
# cwe_counts = Counter()
#
# with open(file_path, newline='', encoding='utf-8') as f:
#     reader = csv.DictReader(f)
#     for row in reader:
#         cwes_str = row['cwes'].strip()
#         if not cwes_str:
#             continue  # 空字段跳过
#
#         # 将字符串安全地转换成列表
#         try:
#             cwes = ast.literal_eval(cwes_str)
#         except Exception:
#             continue
#
#         # 只要第一个 CWE
#         if cwes:
#             first_cwe = cwes[0]
#             cwe_counts[first_cwe] += 1
#
# # 打印结果
# for cwe, cnt in sorted(cwe_counts.items(), key=lambda x: x[1], reverse=True):
#     print(f"{cwe}: {cnt}")

import csv, ast
from collections import defaultdict

file_path = 'cve_report.csv'
stats = defaultdict(lambda: {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0})

with open(file_path, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cwes_str = row['cwes'].strip()
        sev = row['severity'].strip().upper()

        # 只统计这 4 个等级
        if sev not in {'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'}:
            continue

        try:
            cwes = ast.literal_eval(cwes_str)
        except Exception:
            continue

        if cwes:
            first_cwe = cwes[0]
            stats[first_cwe][sev] += 1

# 按 CRITICAL→HIGH→MEDIUM→LOW 顺序打印
for cwe, cnt in sorted(stats.items()):
    print(f"{cwe}: CRITICAL={cnt['CRITICAL']}  HIGH={cnt['HIGH']}  "
          f"MEDIUM={cnt['MEDIUM']}  LOW={cnt['LOW']}")


