import pandas as pd
import matplotlib.pyplot as plt

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

# 4. 绘图（水平条形图）
fig, ax = plt.subplots(figsize=(6, 8))

y = range(10)  # 0..9
ax.barh(y, top10['public_total'],
        label='Public', color='#1f77b4')
ax.barh(y, top10['private_total'],
        left=top10['public_total'],  # 关键：把 bottom 换成 left
        label='Private', color='#ff7f0e')

# 5. 纵坐标改为 user1~user10（因为现在是 y 轴）
ax.set_yticks(y)
ax.set_yticklabels([f'user{i + 1}' for i in y])

ax.set_xlabel('Total Count')  # 原本是 ylabel
ax.set_title('Top-10 Users: Public vs Private Resources')

ax.legend()
plt.tight_layout()
plt.show()
