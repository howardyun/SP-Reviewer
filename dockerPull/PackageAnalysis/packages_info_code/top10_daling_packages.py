# import json
# import matplotlib.pyplot as plt
# from collections import Counter
#
# # Read the JSON file
# with open('classified_packages.json', 'r',encoding="UTF-8") as file:
#     data = json.load(file)
#
# # Extract categories
# categories = []
# for item in data.values():
#     if 'info' in item and 'error' in item['info'] and item['info']['error'] == 'HTTP 404':
#         categories.append('Dangling')
#     else:
#         categories.append(item.get('category', 'Unknown'))
#
# # Count occurrences of each category
# category_counts = Counter(categories)
#
# # Prepare data for plotting
# labels = list(category_counts.keys())
# values = list(category_counts.values())
#
# # Create bar plot
# plt.figure(figsize=(10, 6))
# plt.bar(labels, values, color='skyblue')
# plt.xlabel('Category')
# plt.ylabel('Count')
# plt.title('Distribution of Categories (Including Dangling)')
# plt.xticks(rotation=45, ha='right')
# plt.tight_layout()
#
# # Save the plot
# plt.savefig('category_distribution.png')
# plt.close()
#
# # Print category counts
# print("Category Counts:")
# for category, count in category_counts.items():
#     print(f"{category}: {count}")
# pip install pandas matplotlib seaborn
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. 读入 CSV
df = pd.read_csv('bb.csv')

font_size = {
    'font.size': 12,  # 全局默认
    'axes.titlesize': 16,  # 标题
    'axes.labelsize': 14,  # 轴标题
    'xtick.labelsize': 12,  # x 刻度
    'ytick.labelsize': 12,  # y 刻度
    'legend.fontsize': 10  # 图例（虽然这里没用上）
}
# 4-2 统一风格
sns.set_theme(
    style="whitegrid",
    palette="viridis",
    rc=font_size  # 直接塞字典
)

# 2. 把 daling_packages 拆成行
#    .dropna() 去掉空值
#    .str.split(',') 按逗号拆成列表
#    .explode() 把列表拆成行
packages = (
    df['daling_packages']
    .dropna()
    .astype(str)
    .str.strip()  # 去掉首尾空格
    .str.split(',')
    .explode()
    .str.strip()  # 再次去掉空格
)

# 3. 统计频次并仅取 Top10（按出现次数降序）
count = packages.value_counts().head(10)

# 4. 画图（保持降序）
plt.figure(figsize=(10, 4))
sns.barplot(
    x=count.index,
    y=count.values,
    hue=count.index,
    palette='viridis',
    legend=False,
    order=count.index  # 固定顺序，防止 seaborn 自动排序
)
plt.xticks(rotation=45, ha='right')
plt.ylabel('Number of repositories')
plt.xlabel('daling_packages')
plt.title('Top 10 daling_packages by repository count')
plt.tight_layout()
plt.savefig('top10_daling_packages.png', dpi=300)
plt.show()
