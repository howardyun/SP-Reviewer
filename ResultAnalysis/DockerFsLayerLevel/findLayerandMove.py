import pandas as pd
import shutil
from pathlib import Path
base_path = Path('Z:/hf-images1')
# 路径配置
source_folders = [Path('Z:/hf-images1/layers'), Path('G:/hf-image2/images-r8')]
output_folder = base_path / 'layer_top100'
output_folder.mkdir(parents=True, exist_ok=True)

# 读取 CSV 并提取 Top100
csv_file = base_path / 'layer_statistics.csv'
df = pd.read_csv(csv_file)
top_layers = df.sort_values(by='count', ascending=False).head(100)['layer'].tolist()

# 遍历每个 layer，检查是否存在，复制并打印状态
for layer_id in top_layers:
    found_in = None
    for src_folder in source_folders:
        layer_path = src_folder / layer_id
        if (layer_path / 'tree.txt').exists():
            found_in = src_folder.name
            # 复制整个 layer 文件夹到输出路径
            target_path = output_folder / layer_id
            if not target_path.exists():  # 避免重复复制
                shutil.copytree(layer_path, target_path)
            print(f'Layer {layer_id} 已从 "{src_folder.name}" 复制')
            break  # 一旦找到就不再搜索下一个目录
    if not found_in:
        print(f'Layer {layer_id} 未在任何目录中找到，跳过')
