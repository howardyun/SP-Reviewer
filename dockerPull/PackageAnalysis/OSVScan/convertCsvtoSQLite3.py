import pandas as pd
import sqlite3

# 1. 读取 CSV 文件
csv_file = '../package_info_data/result.csv'
df = pd.read_csv(csv_file)

# 2. 创建 SQLite 数据库并建立连接
conn = sqlite3.connect('../package_info_data/OSV_record.db')

# 3. 写入数据到数据库中的表（如果存在将替换）
df.to_sql('my_table', conn, if_exists='replace', index=False)



# 4. 关闭连接
conn.close()

print("✅ CSV 已成功写入 SQLite 数据库！")
