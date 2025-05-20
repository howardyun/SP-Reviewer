import json
import csv
import json
import os
import shutil
import subprocess
from pathlib import Path


def parse_and_write_to_csv(folder_path, scan_data, csv_writer):
    """解析osv-scanner的JSON输出并写入CSV"""
    results = scan_data.get("results", [])
    for result in results:
        source_type = result.get("source", {}).get("type", "")

        packages = result.get("packages", [])
        for pkg in packages:
            package = pkg.get("package", {})
            package_name = package.get("name", "")
            package_version = package.get("version", "")
            ecosystem = package.get("ecosystem", "")

            vulnerabilities = pkg.get("vulnerabilities", [])
            for vuln in vulnerabilities:
                vuln_id = vuln.get("id", "")
                aliases = ",".join(vuln.get("aliases", []))
                severity = ""
                cwe_ids = ""
                if vuln.get("database_specific", ""):
                    severity = vuln.get("database_specific", "").get("severity", "")
                    cwe_ids = ",".join(vuln.get("database_specific", "").get("cwe_ids", []))
                # 获取最新的 CVSS 评分
                severity_score = ""
                severity_list = vuln.get("severity", [])
                for sev in severity_list:
                    if sev.get("type") == "CVSS_V4":
                        severity_score = sev.get("score", "")
                        break
                if not severity_score:  # 如果没有 CVSS_V4，尝试 CVSS_V3
                    for sev in severity_list:
                        if sev.get("type") == "CVSS_V3":
                            severity_score = sev.get("score", "")
                            break
                if not severity_score:  # 如果没有 CVSS_V4，尝试 CVSS_V3
                    for sev in severity_list:
                        if sev.get("type") == "CVSS_V2":
                            severity_score = sev.get("score", "")
                            break
                # 获取分组信息
                group_ids = ""
                experimental_analysis = ""
                for group in pkg.get("groups", []):
                    if vuln_id in group.get("ids", []):
                        group_ids = ",".join(group.get("ids", []))
                        # 解析实验性分析结果
                        exp_analysis = group.get("experimentalAnalysis", {})
                        analysis_items = []
                        for key, value in exp_analysis.items():
                            analysis_items.append(f"{key}: called={value['called']}")
                        experimental_analysis = ",".join(analysis_items)

                # 写入CSV
                csv_writer.writerow({
                    "Space name": "",
                    "Source Type": source_type,
                    "Package Name": package_name,
                    "Package Version": package_version,
                    "Ecosystem": ecosystem,
                    "Vulnerability ID": vuln_id,
                    "Severity": severity,
                    "Severity_score": severity_score,
                    "Aliases": aliases,
                    "Group IDs": group_ids,
                    "Cwe_Ids": cwe_ids,
                    "Experimental Analysis": experimental_analysis
                })


def scan_folder(folder_path, csv_writer):
    """对指定文件夹运行osv-scanner扫描"""
    try:
        print(f"正在扫描文件夹: {folder_path}")
        # 运行osv-scanner命令
        result = subprocess.run(
            [
                "osv-scanner", "scan", "source",
                "--format", "json", "--offline",
                "--lockfile", "requirements.txt:./requirements.txt"
            ],
            cwd=str(folder_path),  # 设置工作目录为当前文件夹
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=False
        )
        # 解析 JSON 输出
        if result.stdout:
            try:
                scan_data = json.loads(result.stdout)
                parse_and_write_to_csv(os.path.basename(os.path.normpath(folder_path)), scan_data, csv_writer)
            except json.JSONDecodeError:
                print(f"警告: {folder_path} 的输出不是有效的 JSON")
    except subprocess.CalledProcessError as e:
        print(f"扫描 {folder_path} 时发生错误: {e}")
    except FileNotFoundError:
        print("错误: 未找到osv-scanner命令，请确保已安装osv-scanner")


def scan_all_folders(root_path, csv_file):
    """遍历指定路径下的所有文件夹并进行扫描"""
    root = Path(root_path)
    if not root.exists():
        print(f"错误: 路径 {root_path} 不存在")
        return

    if not root.is_dir():
        print(f"错误: {root_path} 不是一个文件夹")
        return
    # 初始化CSV文件
    csv_fields = [
        "Space name", "Source Type", "Package Name",
        "Package Version", "Ecosystem", "Vulnerability ID", "Severity", "Aliases", "Cwe_Ids", "Severity_score",
        "Group IDs", "Experimental Analysis"
    ]
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        csv_writer = csv.DictWriter(f, fieldnames=csv_fields)
        csv_writer.writeheader()
        # 遍历所有子文件夹
        for item in root.iterdir():
            if item.is_dir():
                scan_folder(item, csv_writer)


if __name__ == "__main__":

    import json
    import os

    # 读取 JSON 文件
    with open('../package_info_data/first_data_pypi_info.json', 'r') as file:
        data = json.load(file)

    # 准备 requirements.txt 内容
    requirements = []
    for package, versions in data.items():
        for version in versions:
            requirements.append(f"{package}=={version}")

    # 计算每份的数量
    total_lines = len(requirements)
    lines_per_file = total_lines // 10 + (1 if total_lines % 10 else 0)

    # 创建 10 个文件夹并分配内容
    for i in range(10):
        # 创建文件夹
        folder_name = f'../package_info_data/part_{i + 1}'
        os.makedirs(folder_name, exist_ok=True)

        # 计算当前份的起始和结束索引
        start_idx = i * lines_per_file
        end_idx = min((i + 1) * lines_per_file, total_lines)

        # 获取当前份的内容
        current_lines = requirements[start_idx:end_idx]

        # 写入 requirements.txt
        with open(os.path.join(folder_name, 'requirements.txt'), 'w', encoding='utf-8') as file:
            file.write('\n'.join(current_lines))

    print("已将 requirements.txt 分为 10 份并存入相应文件夹")

    # 设置命令行参数
    path = "../package_info_data/"
    csv_file = "../package_info_data/result.csv"

    # 执行扫描
    scan_all_folders(path, csv_file)

    # 删除所有生成的文件夹
    for i in range(10):
        folder_name = f'../package_info_data/part_{i + 1}'
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)

    print("所有生成的文件夹已删除")
