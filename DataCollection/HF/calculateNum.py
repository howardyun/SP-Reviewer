import os
import json
import re

def is_in_date_range(filename, start_year, start_month, end_year, end_month):
    match = re.match(r"(\d{4})-(\d{2})\.json$", filename)
    if not match:
        return False
    year, month = int(match.group(1)), int(match.group(2))
    return (year, month) >= (start_year, start_month) and (year, month) <= (end_year, end_month)

def count_top_level_elements_within_range(folder_path, start_year, start_month, end_year, end_month):
    count_total = 0
    for filename in os.listdir(folder_path):
        if is_in_date_range(filename, start_year, start_month, end_year, end_month):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, (list, dict)):
                        print(f"{filename}: 顶层元素数量 = {len(data)}")
                        count_total += len(data)
                    else:
                        print(f"{filename}: 顶层不是 list 或 dict，类型是 {type(data).__name__}")
            except Exception as e:
                print(f"{filename}: 解析失败 - {e}")
    return count_total
# 示例：统计 2025 年 5 月 到 2025 年 7 月之间的文件
total =  count_top_level_elements_within_range(
    folder_path="monthly_spaceId_files",
    start_year=2022,
    start_month=3,
    end_year=2025,
    end_month=4
)
print(total)