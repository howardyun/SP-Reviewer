import pandas as pd

# 读取两个CSV文件
df1 = pd.read_csv("../../Data/Pypi/pypi_osv/result_first.csv")   # 第一个CSV文件路径
df2 = pd.read_csv("../../Data/Pypi/pypi_osv/result_second.csv")  # 第二个CSV文件路径

# 合并两个DataFrame
merged_df = pd.concat([df1, df2], ignore_index=True)

# 去除完全重复的行（如果有）
merged_df = merged_df.drop_duplicates()

# 保存合并后的结果为新的CSV文件
merged_df.to_csv("merged_result.csv", index=False)

print("合并完成，结果已保存为 merged_result.csv")
