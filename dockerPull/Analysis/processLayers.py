from pathlib import Path

from analysisUtils import extract_Pypi,check_pypi_info

from collections import defaultdict

import json


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

def iterate_layers(dir):
    root_path = Path(dir)
    all_packages = set()

    # 遍历layers
    for subfolder in root_path.iterdir():
        if subfolder.is_dir():
            tree_file = subfolder / 'tree.txt'
            if tree_file.is_file():
                # 以二进制方式读取
                with open(tree_file, 'rb') as f:
                    content_bytes = f.read()
                    if check_pypi_info(content_bytes):
                        package_versions = extract_Pypi(content_bytes)
                        all_packages.update(package_versions)

                    # 这里content_bytes就是tree.txt的全部内容，类型是bytes
    print(all_packages)
    package_dict = to_dict(all_packages)
    return package_dict

if __name__ == '__main__':
    layers_dir = 'layers'   #更换为真实路径
    package_dict = iterate_layers(layers_dir)
    save_to_json(package_dict)









