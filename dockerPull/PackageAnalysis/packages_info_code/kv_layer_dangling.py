import json
import os
import sqlite3

# Read the JSON file
with open('classified_packages.json', 'r', encoding="UTF-8") as file:
    data = json.load(file)


def find_repos_with_pypi_intersection(db_path, input_list):
    """
    读取 SQLite 数据库，查询 kv_data 表中 pypi_info_list 与输入 list 有交集的 repo_name。

    参数:
        db_path (str): .db 文件路径
        input_list (list): 输入的数组，用于比较交集

    返回:
        list: 与 input_list 有交集的 repo_name 列表
    """
    global cursor, conn
    matching_repos = []

    try:
        # 连接到数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 查询 kv_data 表中的所有数据
        cursor.execute("SELECT repo_name, pypi_info_list FROM kv_data")
        rows = cursor.fetchall()
        print(len(rows))

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
                matching_repos.append(repo_name)

        return matching_repos

    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return []
    finally:
        # 关闭游标和连接
        if cursor:
            cursor.close()
        if conn:
            conn.close()


file_path = "dangling.json"

if os.path.exists(file_path):
    print(f"文件 {file_path} 存在")
    # 加载
    with open(file_path, 'r') as f:
        dangling_keys = json.load(f)
else:
    # Initialize counters and list for dangling keys
    dangling_count = 0
    valid_count = 0
    dangling_keys = []

    # Process each entry
    for key, item in data.items():
        if 'info' in item and 'error' in item['info'] and item['info']['error'] == 'HTTP 404':
            dangling_count += 1
            dangling_keys.append(key)
        else:
            valid_count += 1
    # 保存
    with open(file_path, 'w') as f:
        json.dump(dangling_keys, f)

print(len(find_repos_with_pypi_intersection("repo_pypi_first_time.db", dangling_keys)))
