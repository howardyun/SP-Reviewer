import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. 读入 CSV
df = pd.read_csv('bb.csv')

font_size = {
    'font.size': 16,  # 全局默认
    'axes.titlesize': 20,  # 标题
    'axes.labelsize': 18,  # 轴标题
    'xtick.labelsize': 14,  # x 刻度
    'ytick.labelsize': 16,  # y 刻度
    'legend.fontsize': 14  # 图例（虽然这里没用上）
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
plt.figure(figsize=(8, 5))
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

# 设置 x 轴标签加粗
# plt.gca().tick_params(axis='x', labelweight='bold')

plt.tight_layout()
plt.savefig('Top10_dangling_Package.pdf', dpi=300)
plt.show()
