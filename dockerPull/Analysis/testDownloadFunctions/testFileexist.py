from pathlib import Path

import json
import os


from collections import defaultdict
from pathlib import Path
import pandas as pd



# 将set变成dict用于统计
def to_dict(all_packages):
    package_dict = defaultdict(list)

    for pkg in all_packages:
        pkg_clean = pkg.replace('.wh.', '')
        name, version = pkg_clean.rsplit('-', 1)
        package_dict[name].append(version)
    return package_dict


def save_to_json(package_dict):
    # 假设你的字典是 final_package_dict
    # 保存到 JSON 文件
    with open('packages.json', 'w', encoding='utf-8') as f:
        json.dump(package_dict, f, ensure_ascii=False, indent=4)




def has_file_with_name(folder_path, filename):
    return (Path(folder_path) / filename).is_file()


def iterate_layers(dir):
    root_path = Path(dir)
    layer_file_lack = list()
    count  = 0
    # 遍历layers
    for subfolder in root_path.iterdir():
        count += 1
        if count %10000 == 0:
            print(count)
        if subfolder.is_dir():
            # 定义两个文件名称
            tree_file = subfolder / 'tree.txt'
            tar_file = subfolder / 'text.tar.gz'

            # 如果两个文件都存在
            if tree_file.is_file() and tar_file.is_file():
                continue
            else:
                layer_file_lack.append(subfolder)

if __name__ == '__main__':
    layers_dir = 'Z:/hf-images1/layers'   #更换为真实路径
    layer_file_lack = iterate_layers(layers_dir)
    print(layer_file_lack)

    with open('output.txt', 'w', encoding='utf-8') as f:
        for item in layer_file_lack:
            f.write(f"{item}\n")

