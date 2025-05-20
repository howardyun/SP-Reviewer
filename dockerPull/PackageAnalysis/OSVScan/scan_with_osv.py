import csv
import json
import os
import subprocess
from pathlib import Path
from dockerPull.Analysis.bk.ParseDir import extract_gz_from_zip, extract_gz_file_to_tmp


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
                    "Space name": str(folder_path),
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
                "--format", "json",
                "--lockfile", "requirements.txt:./freeze.txt"
            ],
            cwd=str(folder_path),  # 设置工作目录为当前文件夹
            capture_output=True,
            text=True,
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


def main():

    root = Path("../../Analysis/testdata")
    for item in root.iterdir():
        #解压缩文件
        zip_ref, fs_groups, json_files = extract_gz_from_zip(item)

        for key in fs_groups:
            # 取对应的file
            files = fs_groups[key]
            for file in files:
                # 这个一般是用于查看tree.txt的内容
                if file.endswith('.txt'):
                    content = zip_ref.read(file).decode('utf-8')
                    if "freeze.txt " in content:
                        target_unzip_file_name = file.replace("tree.txt", "text.tar.gz")
                        TMP_DIR = Path("tmp/"+item.name.replace(".zip", "")+"/")
                        TMP_DIR.mkdir(exist_ok=True)
                        extract_gz_file_to_tmp(zip_ref, target_unzip_file_name, TMP_DIR)

        # 设置命令行参数
        path = "../../Analysis/tmp"
        csv_file = "../../Analysis/bk/result.csv"

        # 执行扫描
        scan_all_folders(path, csv_file)


if __name__ == "__main__":
    main()
