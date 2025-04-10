import os
import pandas as pd

# 设置你要遍历的文件夹路径
folder_path = 'monthly_spaceId_files'


total_space = 0
# 初始化总数
total_count = 0


# 遍历文件夹中的所有文件
for filename in os.listdir(folder_path):
    if filename.endswith('.csv'):
        file_path = os.path.join(folder_path, filename)
        try:
            df = pd.read_csv(file_path)
            total_space += df.shape[0]
            if 'Likes' in df.columns:
                count = (df['Likes'] > 1).sum()
                print(f"{filename} 中 'Likes' > 1 的数量为: {count}")
                total_count += count
            else:
                print(f"{filename} 中没有 'likes' 列")
        except Exception as e:
            print(f"读取 {filename} 时出错: {e}")

print(f"\n所有 仓库的总数量为: {total_space}")
print(f"\n所有 CSV 文件中 'likes' > 1 的总数量为: {total_count}")
