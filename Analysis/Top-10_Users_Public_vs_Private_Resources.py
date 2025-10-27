import pandas as pd
import matplotlib.pyplot as plt

# 设置字体和大小
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 14

# 1. 读取
df = pd.read_csv('../Data/organization_analysis_results.csv')

prv_cols = ['private_models_count', 'private_datasets_count',
            'private_spaces_count', 'private_collections_count']
pub_cols = ['models_count', 'datasets_count', 'spaces_count', 'collections_count']

df = df[df['category'] == 'EV']

df['private_total'] = df[prv_cols].sum(axis=1)
df['public_total'] = df[pub_cols].sum(axis=1) - df['private_total']
df = df.drop_duplicates(subset=['username'])

df['total'] = df[pub_cols].sum(axis=1)
top10 = df.nlargest(10, 'total').reset_index(drop=True)

# 4. 绘图（垂直条形图）
fig, ax = plt.subplots(figsize=(10, 5))

x = range(10)  # 0..9

# 更改柱子的颜色，并添加边框
bars1 = ax.bar(x, top10['public_total'], label='Public', color='#66c2a5', edgecolor='black', linewidth=1.5)
bars2 = ax.bar(x, top10['private_total'], bottom=top10['public_total'],
               label='Private', color='#fc8d62', edgecolor='black', linewidth=1.5)

# 添加数值标签，并避免重叠
for bar in bars1:
    yval = bar.get_height()
    # 对于较小的条形图，增加数值标签的偏移
    y_offset = -200 if yval > 50 else 25  # 如果条形小，增加偏移量
    ax.text(bar.get_x() + bar.get_width() / 2, yval + y_offset,
            f'{int(yval)}', ha='center', va='bottom', fontsize=14, color='black')

for bar in bars2:
    yval = bar.get_height()
    y_offset = 24 if yval > 50 else 24  # 如果条形小，增加偏移量
    ax.text(bar.get_x() + bar.get_width() / 2, top10['public_total'][bars2.index(bar)] + yval + y_offset,
            f'{int(yval)}', ha='center', va='bottom', fontsize=14, color='black')

# 5. 横坐标改为 user1~user10
ax.set_xticks(x)
ax.set_xticklabels([f'user{i + 1}' for i in x], fontsize=18)

ax.set_ylabel('Total Count', fontsize=16)
# ax.set_title('Top-10 Users: Public vs Private Resources', fontsize=18)

ax.legend(fontsize=18)
plt.tight_layout()
plt.show()
fig.savefig('Top10_Org_Leak.pdf', dpi=300, bbox_inches='tight')  # 保存为 PNG 格式
