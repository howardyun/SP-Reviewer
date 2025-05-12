import json

# 加载 JSON 文件
with open('../package_info_data/packages_info_1.json', 'r', encoding='utf-8') as f:
    data = json.load(f)



print(len(data))
# 遍历并打印所有的 key 和对应的 values
# for key, versions in data.items():
#     print(f"Package: {key}")
#     print(f"Versions: {', '.join(versions)}")
#     print("="*40)
