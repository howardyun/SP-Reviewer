import csv
import json
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from huggingface_hub import login
from huggingface_hub import HfApi
from huggingface_hub.errors import RepositoryNotFoundError
from tqdm import tqdm

# Read the JSON file
with open('classified_packages.json', 'r', encoding="UTF-8") as file:
    data = json.load(file)


class SpaceInfo:
    def __init__(self, name, created_at, last_modified, like, runtime, trending_score, sdk, author, org, status):
        self.name = name
        self.like = like
        self.status = status
        self.runtime = runtime
        self.created_at = created_at
        self.last_modified = last_modified
        self.trending_score = trending_score
        self.author = author
        self.org = org
        self.sdk = sdk


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
    conn = None
    cursor = None

    try:
        # 连接到数据库
        conn = sqlite3.connect(db_path)
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


def process_dangling_keys(file_path="dangling.json"):
    """Process dangling keys and save to file"""

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

    return dangling_keys


def main():
    dangling_keys = process_dangling_keys()

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


if __name__ == "__main__":
    # Initialize the HfApi client
    login(token="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")
    api = HfApi()

    if os.path.exists("merge_dangling_space.json"):
        print(f"文件 merge_dangling_space.json 存在")
        # 加载
        with open("merge_dangling_space.json", 'r') as f:
            merge = json.load(f)
    else:
        merge = main()
        with open("merge_dangling_space.json", "w") as f:
            json.dump(merge, f)

    merge = [s.lstrip('_').replace('-', '/', 1).replace('__manifest', '') for s in merge]

    Space = []
    for i in tqdm(merge[:10]):
        try:
            tmp = api.space_info(repo_id=i,
                                 expand=["author", "createdAt", "lastModified", "likes", "runtime", "sdk", "sha",
                                         "trendingScore", ])
            Space.append(
                SpaceInfo(i, tmp.created_at, tmp.last_modified, tmp.likes, tmp.runtime.stage, tmp.trending_score,
                          tmp.sdk,
                          tmp.author, api.get_user_overview(tmp.author).orgs, 0))
        except RepositoryNotFoundError as e:
            Space.append(SpaceInfo(i, None, None, None, None, None, None, None, None, status=404))
            print(f"Error: Repository {i} not found. Skipping... Details: {e}")
        except Exception as e:
            print(f"An unexpected error occurred for {i}: {e}")
            Space.append(SpaceInfo(i, None, None, None, None, None, None, None, None, status=1))

    sorted_space = sorted(Space, key=lambda x: x.like if x.like is not None else -float('inf'), reverse=True)

    # 保存到 CSV 文件
    csv_file = "sorted_space.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        # 定义 CSV 表头，包含所有 SpaceInfo 字段
        fieldnames = ['name', 'created_at', 'last_modified', 'like', 'runtime', 'trending_score', "sdk", "author",
                      "org", 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        # 写入表头
        writer.writeheader()

        # 写入每条记录
        for space in sorted_space:
            writer.writerow({
                'name': space.name,
                'created_at': space.created_at if space.created_at else 'N/A',
                'last_modified': space.last_modified if space.last_modified else 'N/A',
                'like': space.like if space.like is not None else 'N/A',
                'runtime': space.runtime if space.runtime else 'N/A',
                'trending_score': space.trending_score if space.trending_score is not None else 'N/A',
                "sdk": space.sdk if space.sdk is not None else 'N/A',
                'author': space.author if space.author is not None else 'N/A',
                'org': space.org if space.org is not None else 'N/A',
                'status': space.status
            })

    print(f"排序后的数据已保存到 {csv_file}")
