import os
import ast
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress  # 用于IP地址验证


def is_private_ip(ip_str):
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private
    except ValueError:
        return False


def is_ip_address(s):
    # IPv4 正则
    ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    # IPv6 正则（简化版）
    ipv6_pattern = r'^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))$'
    return bool(re.match(ipv4_pattern, s) or re.match(ipv6_pattern, s))


def is_domain(s):
    # 简单域名正则：至少一个点，顶级域如.com, .net等
    domain_pattern = r'^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$'
    return bool(re.match(domain_pattern, s))


def extract_calls_from_file(file_path):
    items = set()  # 收集IP或域名
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                s = node.value.strip()
                # 检查是否是IP（非私有）或域名
                if is_ip_address(s) and not is_private_ip(s):
                    items.add(s)
                elif is_domain(s):
                    items.add(s)
            elif isinstance(node, ast.Str):  # 兼容旧Python
                s = node.s.strip()
                if is_ip_address(s) and not is_private_ip(s):
                    items.add(s)
                elif is_domain(s):
                    items.add(s)
    except Exception as e:
        print(f"[WARN] Failed to parse {file_path}: {e}")
    return items


def analyze_one_repo(repo_path):
    repo_name = os.path.basename(repo_path)
    all_items = set()  # all_items
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                items = extract_calls_from_file(file_path)
                all_items.update(items)
    return repo_name, sorted(all_items) if all_items else None


def analyze_month_folder(month_folder, output_dir, max_workers=8):
    all_repos = [
        os.path.join(month_folder, repo)
        for repo in os.listdir(month_folder)
        if os.path.isdir(os.path.join(month_folder, repo))
    ]
    result = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(analyze_one_repo, repo_path): repo_path for repo_path in all_repos}
        for future in as_completed(futures):
            repo_path = futures[future]
            try:
                repo_name, items = future.result()  # items
                if items:
                    result[repo_name] = items
            except Exception as exc:
                print(f"[X] Error in repo {repo_path}: {exc}")
    if result:
        month = os.path.basename(month_folder)
        output_path = os.path.join(output_dir, f"{month}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"[✓] Saved: {month} ({len(result)} repos with items)")  # 调整打印信息


if __name__ == "__main__":
    base_dir = r"F:\download_space"
    output_dir = os.path.join(base_dir, "ip_domain")  # 可以改为其他输出目录名，如 "ip_domain"
    os.makedirs(output_dir, exist_ok=True)
    for i in range(11, 13):
        month_folder = f"{base_dir}/2023-{'0' + str(i) if i < 10 else str(i)}"
        if os.path.exists(month_folder):
            analyze_month_folder(month_folder, output_dir, max_workers=6)
