import json
import requests
import csv
import os
from typing import List, Dict, Any
from urllib.parse import urljoin

# 配置
API_BASE_URL = "https://api.osv.dev/v1/"
JSON_INPUT_FILE = "../package_info_data/packages_info_1.json"
CSV_OUTPUT_FILE = "vulnerabilities.csv"
ECOSYSTEM = "PyPI"  # 假设为PyPI生态系统
INITIAL_MAX_QUERIES_PER_BATCH = 100  # 初始每批最大查询数
MIN_QUERIES_PER_BATCH = 10  # 最小批次大小

# CSV字段
CSV_FIELDS = [
    "Space name",
    "Package Name",
    "Package Version",
    "Ecosystem",
    "Vulnerability ID",
    "Severity",
    "Aliases",
    "Cwe_Ids",
    "Severity_score",
    "Group IDs",
    "Experimental Analysis"
]


def read_packages(file_path: str) -> Dict[str, List[str]]:
    """读取JSON文件中的软件包名称和版本。"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误：文件 {file_path} 未找到。")
        return {}
    except json.JSONDecodeError:
        print(f"错误：文件 {file_path} 包含无效JSON。")
        return {}


def build_queries(packages: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """为/v1/querybatch端点构建查询列表。"""
    queries = []
    for package_name, versions in packages.items():
        for version in versions:
            query = {
                "package": {
                    "name": package_name,
                    "ecosystem": ECOSYSTEM
                },
                "version": version
            }
            queries.append(query)
    return queries


def query_vulnerabilities(queries: List[Dict[str, Any]], page_token: str = None) -> Dict[str, Any]:
    """查询OSV.dev /v1/querybatch端点。"""
    payload = {"queries": queries}
    if page_token:
        for query in payload["queries"]:
            query["page_token"] = page_token

    try:
        response = requests.post(urljoin(API_BASE_URL, "querybatch"), json=payload)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        if response.status_code == 400 and b'"code":3' in response.content:
            print(f"错误：查询过多 - {response.json().get('message', 'Too many queries.')}")
            return {"results": [], "too_many_queries": True}
        raise


def get_vulnerability_details(vuln_id: str) -> Dict[str, Any]:
    """通过ID获取详细的漏洞信息。"""
    try:
        response = requests.get(urljoin(API_BASE_URL, f"vulns/{vuln_id}"))
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        print(f"错误：获取漏洞 {vuln_id} 详细信息失败 - {e}")
        return {}


def process_vulnerabilities(results: Dict[str, Any], package_queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """处理漏洞结果并获取详细信息。"""
    vulnerability_data = []

    for query_idx, result in enumerate(results.get("results", [])):
        package_query = package_queries[query_idx]
        package_name = package_query["package"]["name"]
        package_version = package_query.get("version", "")

        for vuln in result.get("vulns", []):
            vuln_id = vuln["id"]
            vuln_details = get_vulnerability_details(vuln_id)
            if not vuln_details:
                continue

            # 提取最新严重性信息（优先CVSS_V4，其次CVSS_V3，回退到ecosystem_specific.severity）
            severity_score = next(
                (s for s in vuln_details.get("severity", []) if s["type"] == "CVSS_V4"),
                next(
                    (s for s in vuln_details.get("severity", []) if s["type"] == "CVSS_V3"),
                    {}
                )
            )
            severity_score = severity_score.get("score", "")

            # 确定Severity字段：CVSS评分或ecosystem_specific.severity
            # 从affected列表的第一个ecosystem_specific.severity获取
            database_specifc = vuln_details.get('database_specific', {})
            severity = database_specifc.get("severity", "")

            # 提取别名和CWE ID
            aliases = ",".join(vuln_details.get("aliases", []))
            cwe_ids = database_specifc.get("cwe_ids", [])

            # 提取组ID和实验性分析
            group_ids = ",".join(vuln_details.get("database_specific", {}).get("groups", []))
            experimental_analysis = vuln_details.get("database_specific", {}).get("experimental_analysis", "")

            # 编译行数据
            row = {
                "Space name": " ",
                "Package Name": package_name,
                "Package Version": package_version,
                "Ecosystem": ECOSYSTEM,
                "Vulnerability ID": vuln_id,
                "Severity": severity,
                "Aliases": aliases,
                "Cwe_Ids": cwe_ids,
                "Severity_score": severity_score,
                "Group IDs": group_ids,
                "Experimental Analysis": str(experimental_analysis)
            }
            vulnerability_data.append(row)

    return vulnerability_data


def write_to_csv(data: List[Dict[str, Any]], output_file: str, append: bool = True):
    """将漏洞数据写入CSV文件，支持追加模式。"""
    try:
        mode = 'a' if append and os.path.exists(output_file) else 'w'
        with open(output_file, mode, newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            if mode == 'w':
                writer.writeheader()
            for row in data:
                writer.writerow(row)
    except IOError as e:
        print(f"错误：写入CSV文件 {output_file} 失败 - {e}")


def process_batch(batch_queries: List[Dict[str, Any]], max_queries_per_batch: int, batch_number: int) -> List[
    Dict[str, Any]]:
    """处理单个批次的查询，支持分页和错误重试，并在完成后写入CSV。"""
    vulnerability_data = []
    next_page_tokens = [None] * len(batch_queries)

    while True:
        # 更新当前批次查询的下一页令牌
        current_queries = []
        query_indices = []
        for idx, (query, token) in enumerate(zip(batch_queries, next_page_tokens)):
            if token != "":  # 如果令牌为None或有效令牌，则继续处理
                q = query.copy()
                if token:
                    q["page_token"] = token
                current_queries.append(q)
                query_indices.append(idx)

        if not current_queries:
            break

        # 查询漏洞
        results = query_vulnerabilities(current_queries)
        if results.get("too_many_queries", False):
            if max_queries_per_batch <= MIN_QUERIES_PER_BATCH:
                print(f"错误：批次大小已达最小值 {MIN_QUERIES_PER_BATCH}，无法继续处理批次 {batch_number}")
                return vulnerability_data
            return None  # 触发重试

        batch_data = process_vulnerabilities(results, current_queries)
        vulnerability_data.extend(batch_data)

        # 更新下一页令牌
        for result_idx, result in enumerate(results.get("results", [])):
            original_query_idx = query_indices[result_idx]
            next_page_tokens[original_query_idx] = result.get("next_page_token", "")

    # 批次处理完成后写入CSV
    if vulnerability_data:
        write_to_csv(vulnerability_data, CSV_OUTPUT_FILE, append=(batch_number > 1))
        print(f"批次 {batch_number} 写入 {len(vulnerability_data)} 行到 {CSV_OUTPUT_FILE}")

    return vulnerability_data


def main():
    # 从JSON文件读取软件包
    packages = read_packages(JSON_INPUT_FILE)
    if not packages:
        print("没有要处理的软件包。")
        return

    # 构建查询
    queries = build_queries(packages)
    if not queries:
        print("未生成任何查询。")
        return

    # 处理查询，分批并支持分页
    all_vulnerability_data = []
    max_queries_per_batch = INITIAL_MAX_QUERIES_PER_BATCH
    batch_number = 0

    while queries and max_queries_per_batch >= MIN_QUERIES_PER_BATCH:
        for batch_start in range(0, len(queries), max_queries_per_batch):
            batch_number += 1
            batch_queries = queries[batch_start:batch_start + max_queries_per_batch]
            print(f"处理批次 {batch_number}，包含 {len(batch_queries)} 个查询，批次大小 {max_queries_per_batch}")

            # 处理当前批次
            batch_data = process_batch(batch_queries, max_queries_per_batch, batch_number)
            if batch_data is None:
                # 触发"Too many queries"，减小批次大小并重试
                max_queries_per_batch = max(max_queries_per_batch // 2, MIN_QUERIES_PER_BATCH)
                print(f"减小批次大小至 {max_queries_per_batch} 并重试")
                batch_number -= 1  # 重复当前批次编号
                break
            all_vulnerability_data.extend(batch_data)
        else:
            break  # 所有批次处理完成，退出循环
        queries = queries[:batch_start + max_queries_per_batch]  # 保留未处理的查询

    # 最终检查是否有数据写入
    if all_vulnerability_data:
        print(f"总计写入 {len(all_vulnerability_data)} 行到 {CSV_OUTPUT_FILE}")
    else:
        print("未找到任何漏洞。")


if __name__ == "__main__":
    main()
