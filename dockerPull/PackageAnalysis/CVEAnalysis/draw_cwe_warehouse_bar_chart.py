import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# # 1. 读取数据
# df = pd.read_csv("cve_cwe_info2.csv", usecols=['repo_name', 'CWE'])
#
# # 2. 将 CWE 列拆分成列表，并统计每个 repo 的 CWE 数量
# df['CWE'] = df['CWE'].astype(str).str.strip()  # 去掉可能的前后空格
# df['CWE'] = df['CWE'].str.split(',')  # str -> list
# CWE_per_repo = df.groupby('repo_name')['CWE'].sum()  # 合并同一 repo 的多行
# CWE_per_repo = CWE_per_repo.apply(lambda x: len(set(x)))  # 去重后计数
# CWE_per_repo = CWE_per_repo.reset_index(name='CWE_count')
#
# # 3. 画区间分布直方图
# plt.figure(figsize=(10, 5))
# sns.histplot(CWE_per_repo['CWE_count'],
#              bins=range(0, 100, 5),  # 自动决定区间个数，也可给定具体整数
#              kde=False,
#              color='steelblue')
#
# plt.title('Distribution of CWE counts per repository')
# plt.xlabel('Number of CWEs')
# plt.ylabel('Number of repositories')
# plt.tight_layout()
# plt.show()


def draw_cwe_warehouse_bar_chart(csv_path: str,
                                 top_n: int = 10,
                                 figsize=(12, 6)):
    """
    读取 CVE-CWE 数据，绘制仓库中 Top-N 的 CWE 类型分布柱状图。

    参数
    ----
    csv_path : str
        数据文件路径（必须包含 'repo_name' 与 'CWE' 两列）。
    top_n : int, 默认 10
        要展示的 CWE 类型数量。
    figsize : tuple, 默认 (12, 6)
        图像大小。
    """
    # 1. 读取数据
    df = pd.read_csv(csv_path, usecols=['repo_name', 'CWE'])

    # 2. 拆分并扁平化所有 CWE
    df['CWE'] = df['CWE'].astype(str).str.strip().str.split(',')
    all_cwe = [c.strip() for sublist in df['CWE'].dropna() for c in sublist if c.strip() != '']

    # 3. 统计每个 CWE 出现的仓库数
    #   先把每个 repo 的 CWE 去重
    repo_cwe = (
        df.groupby('repo_name')['CWE']
          .sum()                  # 合并同一 repo 的多行
          .apply(lambda x: set(c.strip() for c in x if c.strip() != ''))
    )

    # 扁平化后统计每个 CWE 在多少仓库出现过
    from collections import Counter
    cwe_repos_cnt = Counter()
    for cwe_set in repo_cwe:
        cwe_repos_cnt.update(cwe_set)

    # 4. 取 Top-N
    top_cwe = cwe_repos_cnt.most_common(top_n)
    cwe_df = pd.DataFrame(top_cwe, columns=['CWE', 'repo_count'])

    # 5. 画图
    plt.figure(figsize=figsize)
    sns.barplot(data=cwe_df, x='CWE', y='repo_count', palette='viridis')

    plt.title(f'Top-{top_n} CWE Types in Repositories', fontsize=14)
    plt.xlabel('CWE Type')
    plt.ylabel('Number of Space')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()


draw_cwe_warehouse_bar_chart("cve_cwe_info2.csv", top_n=10)
