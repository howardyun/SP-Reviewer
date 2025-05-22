import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt

# 读取CSV文件
file_path = "../package_info_data/result_new.csv"
df = pd.read_csv(file_path)

# 去除空值
cwe_series = df['Cwe_Ids'].dropna()

# 拆分每行中的多个CWE项（按逗号分隔）
cwe_list = []
for item in cwe_series:
    if isinstance(item, str):
        cwe_list.extend([cwe.strip() for cwe in item.split(",") if cwe.strip()])

# 统计CWE频次
cwe_counts = Counter(cwe_list)

# 转为DataFrame并按频次排序
cwe_df = pd.DataFrame(cwe_counts.items(), columns=['CWE_ID', 'Count'])
cwe_df = cwe_df.sort_values(by='Count', ascending=False)

# 打印或保存结果
print(cwe_df)



# 如果CWE种类太多，这里只画前20个
top_n = 20
top_cwe_df = cwe_df.head(top_n)

# 设置中文支持（可选）
plt.rcParams['font.sans-serif'] = ['Arial']  # 替换为你系统中支持的中文字体
plt.rcParams['axes.unicode_minus'] = False

# 绘制条形图
plt.figure(figsize=(12, 6))
plt.bar(top_cwe_df['CWE_ID'], top_cwe_df['Count'])
plt.xlabel('CWE ID')
plt.ylabel('Count')
plt.title(f'Top {top_n} Most Frequent CWE Occurrences')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()

# 显示图表
plt.show()



# 可选：保存为新CSV
# cwe_df.to_csv("cwe_counts.csv", index=False)
