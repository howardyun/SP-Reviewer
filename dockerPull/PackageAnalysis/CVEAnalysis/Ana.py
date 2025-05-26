import pandas as pd


# # 统计 CVE（Aliases 列）
# aliases_stats = {
#     'Non-Null Count': df['Aliases'].count(),
#     'Unique Values': df['Aliases'].nunique(),
#     'Sample Values': df['Aliases'].dropna().unique()[:5]
# }
#
# # 统计 CWE（Cwe_Ids 列）
# cwe_stats = {
#     'Non-Null Count': df['Cwe_Ids'].count(),
#     'Unique Values': df['Cwe_Ids'].nunique(),
#     'Sample Values': df['Cwe_Ids'].dropna().unique()[:5]
# }
#
# # 合并为DataFrame输出
# summary_df = pd.DataFrame([aliases_stats, cwe_stats], index=['Aliases (CVE)', 'Cwe_Ids (CWE)'])
#
# print(summary_df)


def count_unique_packages_and_versions(df):
    """
    统计给定CSV文件中不同的 PyPI 包数量及每个包对应的唯一版本数量。

    参数:
     df (DataFrame): CSV 文件对象，文件应包含 'Package Name' 和 'Package Version' 两列。

    返回:
        tuple:
            - unique_package_count (int): 不同 PyPI 包的数量。
            - version_count_df (DataFrame): 每个包对应的唯一版本数量统计表。
    """


    # 统计不同的 PyPI 包数量
    unique_package_count = df['Package Name'].nunique()

    # 统计每个包对应的不同版本数量
    version_count_df = df.groupby('Package Name')['Package Version'].nunique().reset_index()
    version_count_df.columns = ['Package Name', 'Unique Version Count']
    print(unique_package_count)
    print(version_count_df)

    # 所有包的版本数量总和
    total_version_count = version_count_df['Unique Version Count'].sum()
    print(f"涉及的Pypi包数量：{unique_package_count}")
    print(f"涉及的版本号：{total_version_count}")

    return unique_package_count, version_count_df




if __name__ == '__main__':
    # 读取CSV文件
    df = pd.read_csv("../../Data/Pypi/pypi_osv/merged_result.csv")  # 替换为实际路径
    unique_package_count, version_count_df = count_unique_packages_and_versions(df)








