import json
import os
from pathlib import Path
from collections import defaultdict
from time import process_time_ns

import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from dockerPull.Analysis.PackageExtract.analysisUtils import extract_Pypi, check_pypi_info


def save_to_json(filename, package_dict, path=''):
    os.makedirs(path, exist_ok=True)
    with open(f'{path}/{filename}.json', 'w', encoding='utf-8') as f:
        json.dump(package_dict, f, ensure_ascii=False, indent=4)


def to_dict(all_packages):
    package_dict = defaultdict(list)
    for pkg in all_packages:
        pkg_clean = pkg.replace('.wh.', '')
        try:
            name, version = pkg_clean.rsplit('-', 1)
            package_dict[name].append(version)
        except ValueError:
            # 防止解析失败
            continue
    return package_dict


def get_layers_by_manifest_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list) and 'Layers' in data[0]:
            return [s.split('/')[0] for s in data[0]['Layers']]
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return []


def extract_pypi_by_layers(target_path, layers):
    all_packages = set()
    lack_layers = []
    for layer in layers:
        try:
            file_path = os.path.join(target_path, layer, 'tree.txt')
            with open(file_path, 'rb') as f:
                content_bytes = f.read()
                if check_pypi_info(content_bytes):
                    package_versions = extract_Pypi(content_bytes)
                    all_packages.update(package_versions)
        except FileNotFoundError:
            lack_layers.append(layer)
    return to_dict(all_packages), lack_layers


def process_manifest(file, base_path):
    file_path = str(file)
    layers = get_layers_by_manifest_json(file_path)
    return layers


if __name__ == '__main__':
    base_path = r'Z:/hf-images1'
    folder_path = Path(f'{base_path}/images-r8')
    json_files = list(folder_path.glob('*.json'))  # 当前目录下的所有 .json 文件

    layers_record = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_manifest, file, base_path): file for file in json_files}

        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            layers_record.append(result)
            if i % 10000 == 0:
                print(f'已处理 {i} 个文件')

    # 多维数组的展平
    flattened = [item for sublist in layers_record for item in sublist]

    np_list = np.array(flattened)
    # 统计每个唯一值出现次数
    unique, counts = np.unique(flattened, return_counts=True)

    # 打印统计结果
    for val, count in zip(unique, counts):
        print(f'值 {val} 出现了 {count} 次')




