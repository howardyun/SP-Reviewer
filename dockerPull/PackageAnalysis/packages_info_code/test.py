import csv
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from dockerPull.PackageAnalysis.packages_info_code.kv_layer_dangling import process_dangling_keys


def find_repos_with_pypi_intersection(db_path, input_list):
    """
    读取 SQLite 数据库，查询 kv_data 表中 pypi_info_list 与输入 list 有交集的 repo_name。

    参数:
        db_path (str): .db 文件路径
        input_list (list): 输入的数组，用于比较交集

    返回:
        list: 与 input_list 有交集的 repo_name 列表
    """
    matching_repos = []

    try:
        # 使用 context manager 管理数据库连接
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 查询 kv_data 表中的所有数据
            cursor.execute("SELECT repo_name, pypi_info_list FROM kv_data")
            rows = cursor.fetchall()
            print(f"Processing {len(rows)} rows from {db_path}")

            # 遍历每一行，检查 pypi_info_list 与 input_list 的交集
            for row in rows:
                repo_name, pypi_info_json = row
                # 将 pypi_info_list 从 JSON 字符串解析为 Python 列表
                try:
                    pypi_info_list = json.loads(pypi_info_json)
                    pypi_info_list = list(map(lambda x: x.split('-')[0], pypi_info_list))
                except json.JSONDecodeError:
                    print(f"警告: {repo_name} 的 pypi_info_list 格式错误，跳过")
                    continue

                # 检查交集
                if set(pypi_info_list) & set(input_list):
                    matching_repos.append((repo_name.lstrip('_').replace('-', '/', 1).replace('__manifest', ''),
                                           set(pypi_info_list) & set(input_list)))

    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return matching_repos  # 返回空列表或部分结果，视需求而定
    finally:
        # 确保 cursor 和 conn 已由 context manager 关闭，无需手动关闭
        pass

    return matching_repos


def main():
    dangling_keys = process_dangling_keys("dangling_check.json")

    # Create a thread pool with 2 workers (one for each DB)
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both database processing tasks and store futures
        future1 = executor.submit(find_repos_with_pypi_intersection, "repo_pypi_second_time.db", dangling_keys)
        future2 = executor.submit(find_repos_with_pypi_intersection, "repo_pypi_first_time.db", dangling_keys)

        # Get results from both futures
        result1 = future1.result()
        result2 = future2.result()

    # Merge results
    merge = result1 + result2
    print(f"First DB matches: {len(result1)}")
    print(f"Second DB matches: {len(result2)}")
    print(f"Total matching repos found: {len(merge)}")

    return merge


def save_to_csv(data, output_file='repos_with_pypi_intersection.csv'):
    """
    Save the list of (repo_name, intersecting_packages) to a CSV file.

    Parameters:
        data (list): List of tuples, each containing (repo_name, set of intersecting packages)
        output_file (str): Name of the output CSV file
    """
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            writer.writerow(['repo_name', 'daling_packages'])
            # Write data rows
            for repo_name, packages in data:
                # Convert set of packages to comma-separated string
                packages_str = ','.join(packages)
                writer.writerow([repo_name, packages_str])
        print(f"Successfully saved data to {output_file}")
    except Exception as e:
        print(f"Error writing to CSV: {e}")


def merge_csvs(input_csv1, input_csv2, output_csv):
    # Read the two CSV files
    df1 = pd.read_csv(input_csv1)
    df2 = pd.read_csv(input_csv2)

    # Merge df1 with df2, keeping all columns from df1 and adding daling_packages
    # Use left join to keep all rows from df1
    merged_df = df1.merge(df2[['repo_name', 'daling_packages']],
                          left_on='name',
                          right_on='repo_name',
                          how='left')

    # Drop the redundant repo_name column from the merge
    merged_df = merged_df.drop(columns=['repo_name'], errors='ignore')

    # Remove rows where 'daling_packages' is NaN
    merged_df = merged_df.dropna(subset=['daling_packages'])

    # Save the result to a new CSV file
    merged_df.to_csv(output_csv, index=False)
    print(f"Output CSV saved as {output_csv}")


# if __name__ == '__main__':
#     a = main()
#     save_to_csv(a)


if __name__ == "__main__":
    # a = main()
    # save_to_csv(a)
    #
    # input_csv1 = "sorted_space.csv"
    # input_csv2 = "repos_with_pypi_intersection.csv"
    # output_csv = "bb.csv"
    #
    # merge_csvs(input_csv1, input_csv2, output_csv)

    with open("./dangling_check.json", "r") as f:
        a = json.load(f)

    with open("./dangling_github_check.json", "r") as f:
        b = json.load(f)

    with open("./dangling.json", "r") as f:
        c = json.load(f)

    print(len(set(c) - set(b)))

    # with open("cc.json", 'w', encoding='utf-8') as f:
    #     json.dump(list(set(b) - set(a)), f, ensure_ascii=False)

    d = list(set(b) - set(a))

    e = [s for s in d if "_core_news" not in s]

    e = [s for s in e if "_dep_news" not in s]

    e = [s for s in e if "_core_sci" not in s]

    e = [s for s in e if "_core_web_" not in s]

    e = [s for s in e if "_ner_bc5cdr_" not in s]

    e = [s for s in e if "en_engagement_LSTM" not in s]

    e = [s for s in e if "spacy" not in s]

    e = [s for s in e if "conda" not in s]

    with open("cc.json", 'w', encoding='utf-8') as f:
        json.dump(e, f, ensure_ascii=False)

    print(len(d) - len(e))
    print(len(e))
