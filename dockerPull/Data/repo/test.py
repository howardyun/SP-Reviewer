import sqlite3

# 连接数据库
conn = sqlite3.connect("repo_pypi_first_time.db")
cursor = conn.cursor()


table_name = "kv_data"
cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
count = cursor.fetchone()[0]
print(f"Table '{table_name}' has {count} rows.")

conn.close()
