import json
import os

# 目录路径（包含所有的 JSON 文件）
directory_path = r'Z:/HF_Space_Variable'  # 修改为您自己的路径
# 设置筛选的开始和结束日期
start_date = '2022-03'  # 设置开始日期（格式为 'YYYY-MM'）
end_date = '2025-05'  # 设置结束日期（格式为 'YYYY-MM'）

# 获取目录中的所有 JSON 文件
json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]

# 初始化计数器
total_repos = 0
total_env_vars = 0

# 遍历所有 JSON 文件进行统计
for json_file in json_files:
    # 提取文件名中的日期部分
    file_date = json_file[:7]  # 文件名中的日期（如 '2022-03'）

    # 只处理在指定日期范围内的文件
    if start_date <= file_date <= end_date:
        file_path = os.path.join(directory_path, json_file)

        # 读取 JSON 文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 统计仓库数量和环境变量数量
        total_repos += len(data)
        total_env_vars += sum(len(repo["result"]) for repo in data)

# 输出结果
print(f"筛选日期范围内的仓库数量: {total_repos}")
print(f"筛选日期范围内的环境变量数量: {total_env_vars}")