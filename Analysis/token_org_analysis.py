import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt


df = pd.read_csv('../Data/organization_analysis_results.csv')

# 2. 拆分 orgs 并标准化（去除空格）
df = (
    df.assign(org=lambda d: d['orgs'].str.split(','))
    .explode('org')
    .assign(org=lambda s: s['org'].str.strip())
)[['org', 'filename']]

# 3. 按 org 分组，并去重 filename
grouped = (
    df.groupby('org')['filename']
    .apply(lambda x: list(set(x)))  # 使用 set 去重
    .rename('filenames')
)

# 4. 仅保留 filename 数量 ≥ 2 的 org
result = grouped[grouped.str.len() >= 2]

# 5. 输出结果（org -> 去重后的 filenames）
for org, filenames in result.items():
    print(f"{org} -> {','.join(filenames)}")

# # 把所有 orgs 拼接成一个长字符
# all_orgs = []
# for orgs in df["orgs"].dropna():
#     # 按逗号分割，去除空格，统一小写
#     parts = [part.strip().lower() for part in str(orgs).split(",") if part.strip()]
#     all_orgs.extend(parts)
#
# text = " ".join(all_orgs)
#
# # ----------------- 3. 生成词云 -----------------
# # 可选：自定义停用词
# stopwords = {"and", "the"}
#
# wc = WordCloud(
#     width=800,
#     height=600,
#     background_color="white",
#     colormap="tab10",
#     stopwords=stopwords,
#     collocations=False,
#     max_words=200
# ).generate(text)
#
# # ----------------- 4. 可视化 -----------------
# plt.figure(figsize=(10, 6))
# plt.imshow(wc, interpolation="bilinear")
# plt.axis("off")
# plt.title("Organizations WordCloud", fontsize=16)
# plt.tight_layout()
# plt.show()
# ---------------- 2. 计算资源数 ----------------
# plt.rcParams['font.family'] = ['SimHei']        # 黑体
# plt.rcParams['axes.unicode_minus'] = False      # 让负号正常显示
# df["resource_total"] = (
#     df[["models_count", "datasets_count", "spaces_count", "collections_count"]]
#     .sum(axis=1)
# )
#
# # ---------------- 3. 分箱 ----------------
# # 区间宽度可自行调：下面 0-5000 每 500 一段，可根据数据范围改
# bins = range(0, 4000, 200)  # [0,500,1000,...,5000]
# labels = [f"{a}-{b}" for a, b in zip(bins[:-1], bins[1:])]
#
# df["bin"] = pd.cut(df["resource_total"], bins=bins, labels=labels, right=False)
#
# # ---------------- 4. 统计人数 ----------------
# count_df = df["bin"].value_counts().sort_index()
#
# # ---------------- 5. 画图 ----------------
# plt.figure(figsize=(8, 4))
# plt.barh(count_df.index.astype(str), count_df.values, color="steelblue")
# plt.xlabel("用户数（落入该区间的个数）")
# plt.ylabel("资源数区间")
# plt.title("资源数区间-用户分布")
# plt.gca().invert_yaxis()  # 让区间从小到大从上到下排
# plt.tight_layout()
# plt.show()