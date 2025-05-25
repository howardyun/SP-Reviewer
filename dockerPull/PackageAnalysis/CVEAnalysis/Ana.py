import pandas as pd

# 读取CSV文件
df = pd.read_csv("../package_info_data/merged_result.csv")  # 替换为实际路径

# 统计 CVE（Aliases 列）
aliases_stats = {
    'Non-Null Count': df['Aliases'].count(),
    'Unique Values': df['Aliases'].nunique(),
    'Sample Values': df['Aliases'].dropna().unique()[:5]
}

# 统计 CWE（Cwe_Ids 列）
cwe_stats = {
    'Non-Null Count': df['Cwe_Ids'].count(),
    'Unique Values': df['Cwe_Ids'].nunique(),
    'Sample Values': df['Cwe_Ids'].dropna().unique()[:5]
}

# 合并为DataFrame输出
summary_df = pd.DataFrame([aliases_stats, cwe_stats], index=['Aliases (CVE)', 'Cwe_Ids (CWE)'])

print(summary_df)
