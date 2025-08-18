import os
import csv
import json
from pathlib import Path
from collections import defaultdict


def extract_file_info(file_path):
    """
    从文件中提取组织信息和其他字段，包括每个组织的详细信息
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        orgs = None
        username = None
        models_count = 0
        datasets_count = 0
        spaces_count = 0
        collections_count = 0
        private_models_count = 0
        private_datasets_count = 0
        private_spaces_count = 0
        private_collections_count = 0
        permission = None

        # 用于存储每个组织的统计信息
        org_stats = {}
        current_org = None

        lines = content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if 'orgs:' in line:
                orgs = line.split('orgs:')[-1].strip()
            elif 'username:' in line:
                username = line.split('username:')[-1].strip()
            elif 'permission:' in line:
                permission = line.split('permission:')[-1].strip()
                permission = permission.replace(').', '')

            elif '>>> ' in line:  # 新组织的开始
                current_org = line.replace('>>> ', '').replace(':', '').strip()

                if current_org:
                    org_stats[current_org] = {
                        'models_count': 0,
                        'datasets_count': 0,
                        'spaces_count': 0,
                        'collections_count': 0,
                        "private_models_count": 0,
                        "private_datasets_count": 0,
                        "private_spaces_count": 0,
                        "private_collections_count": 0
                    }
            elif current_org and line:
                if 'Models:' in line:
                    # 计算当前组织的Models数量
                    j = i + 1
                    while j < len(lines) and not lines[j].strip().startswith('>>>') and 'Datasets:' not in lines[j]:
                        if lines[j].strip() and '\t' in lines[j]:
                            org_stats[current_org]['models_count'] += 1
                            models_count += 1
                            if "Private=True" in lines[j]:
                                private_models_count += 1
                                org_stats[current_org]["private_models_count"] += 1
                        j += 1
                elif 'Datasets:' in line:
                    # 计算当前组织的Datasets数量
                    j = i + 1
                    while j < len(lines) and not lines[j].strip().startswith('>>>') and 'Spaces:' not in lines[j]:
                        if lines[j].strip() and '\t' in lines[j]:
                            org_stats[current_org]['datasets_count'] += 1
                            datasets_count += 1
                            if "Private=True" in lines[j]:
                                private_datasets_count += 1
                                org_stats[current_org]["private_datasets_count"] += 1
                        j += 1
                elif 'Spaces:' in line:
                    # 计算当前组织的Spaces数量
                    j = i + 1
                    while j < len(lines) and not lines[j].strip().startswith('>>>') and 'Collections:' not in lines[j]:
                        if lines[j].strip() and '\t' in lines[j]:
                            org_stats[current_org]['spaces_count'] += 1
                            spaces_count += 1
                            if "Private=True" in lines[j]:
                                private_spaces_count += 1
                                org_stats[current_org]["private_spaces_count"] += 1
                        j += 1
                elif 'Collections:' in line:
                    # 计算当前组织的Collections数量
                    j = i + 1
                    while j < len(lines) and not lines[j].strip().startswith('>>>'):
                        if lines[j].strip() and '\t' in lines[j]:
                            org_stats[current_org]['collections_count'] += 1
                            collections_count += 1
                            if "Private=True" in lines[j]:
                                private_collections_count += 1
                                org_stats[current_org]["private_collections_count"] += 1
                        j += 1
        org_stats.pop(username, None)
        return {
            'filename': os.path.basename(file_path).split('.')[0],
            'username': username,
            'orgs': orgs,
            "Permission": permission,
            'models_count': models_count,
            'datasets_count': datasets_count,
            'spaces_count': spaces_count,
            'collections_count': collections_count,
            "private_models_count": private_models_count,
            "private_datasets_count": private_datasets_count,
            "private_spaces_count": private_spaces_count,
            "private_collections_count": private_collections_count,
            'org_stats': org_stats
        }
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return None


def process_directories(base_path):
    """
    处理目录结构并收集信息
    """
    results = []
    org_total_stats = defaultdict(lambda: {
        'models_count': 0,
        'datasets_count': 0,
        'spaces_count': 0,
        'collections_count': 0,
        "private_models_count": 0,
        "private_datasets_count": 0,
        "private_spaces_count": 0,
        "private_collections_count": 0,
        'num': 0,
    })

    base_path = Path(base_path)

    # 遍历 testresult/testresult 下的 EV 和 file 目录
    for category in ['EV', 'file']:
        category_path = base_path / category
        if not category_path.exists():
            continue

        # 遍历日期文件夹
        for date_dir in category_path.iterdir():
            if not date_dir.is_dir():
                continue

            # 检查并处理 success 文件夹
            success_path = date_dir / 'success'
            if not success_path.exists():
                continue

            # 处理 success 文件夹中的所有文件
            for file_path in success_path.glob('*'):
                if not file_path.is_file():
                    continue

                info = extract_file_info(str(file_path))
                if info:
                    info['date'] = date_dir.name
                    info['category'] = category
                    results.append(info)

                    # 更新组织总统计
                    if info['org_stats']:
                        for org_name, stats in info['org_stats'].items():
                            for key in ['models_count', 'datasets_count', 'spaces_count', 'collections_count',
                                        "private_models_count", "private_datasets_count", "private_spaces_count",
                                        "private_collections_count"]:
                                org_total_stats[org_name][key] = stats[key]
                            org_total_stats[org_name]['num'] += 1
    return results, org_total_stats


def save_to_csv(results, output_file, org_stats_file, org_total_stats):
    """
    将结果保存为CSV文件
    """
    if not results:
        print("No results to save")
        return

    # 保存用户数据
    fieldnames = ['date', 'category', 'filename', 'username', 'orgs',
                  'models_count', 'datasets_count', 'spaces_count', 'collections_count', "private_models_count",
                  "private_datasets_count", "private_spaces_count", "private_collections_count", "Permission"]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            row = {field: result[field] for field in fieldnames}
            if row['username'] is None or row['username'].startswith("Invalid user token"):
                continue
            writer.writerow(row)

    print(f"User results saved to {output_file}")

    # 保存组织统计数据
    org_fieldnames = ['organization', 'models_count',
                      'datasets_count', 'spaces_count', 'collections_count', "private_models_count",
                      "private_datasets_count", "private_spaces_count", "private_collections_count", 'num']

    with open(org_stats_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=org_fieldnames)
        writer.writeheader()
        for org_name, stats in org_total_stats.items():
            row = {'organization': org_name}
            row.update(stats)
            writer.writerow(row)

    print(f"Organization statistics saved to {org_stats_file}")


def main():
    base_path = r"../Data/testresult/testresult"
    output_file = r"../Data/organization_analysis_results.csv"
    org_stats_file = r"../Data/organization_statistics.csv"

    results, org_total_stats = process_directories(base_path)
    save_to_csv(results, output_file, org_stats_file, org_total_stats)


if __name__ == "__main__":
    main()
