import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt

# 读取CSV文件
file_path = "../../Data/Pypi/pypi_osv/result_first.csv"
file_path2 = "../../Data/Pypi/pypi_osv/result_second.csv"
df1 = pd.read_csv(file_path)
df2 = pd.read_csv(file_path2)

# 合并DataFrame
df = pd.concat([df1, df2])

# 去除空值
cve_series = df['Aliases'].dropna()

# 拆分每行中的多个CVE项
cve_list = []
for item in cve_series:
    if isinstance(item, str):
        cve_list.extend([cve.strip() for cve in item.split(",") if cve.strip().startswith('CVE-')])

# 统计CVE频次
cve_counts = Counter(cve_list)

# 转为DataFrame并按频次排序
cve_df = pd.DataFrame(cve_counts.items(), columns=['CVE_ID', 'Count'])
cve_df = cve_df.sort_values(by='Count', ascending=False)

# 打印结果
print(cve_df)

# 绘制前20个CVE的条形图
top_n = 50
top_cve_df = cve_df.head(top_n)

plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.unicode_minus'] = False

plt.figure(figsize=(12, 6))
plt.bar(top_cve_df['CVE_ID'], top_cve_df['Count'])
plt.xlabel('CVE ID')
plt.ylabel('Count')
plt.title(f'Top {top_n} Most Frequent CVE Occurrences')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()

plt.show()

# 可选：保存为新CSV
# cve_df.to_csv("cve_counts.csv", index=False)