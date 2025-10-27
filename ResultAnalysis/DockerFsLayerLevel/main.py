import json
import os
from pathlib import Path
from collections import defaultdict, Counter
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


def process_manifest(file):
    return get_layers_by_manifest_json(str(file))


def process_folder(folder_path: Path):
    json_files = list(folder_path.glob('*.json'))
    layers_record = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_manifest, file): file for file in json_files}
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            layers_record.append(result)
            if i % 10000 == 0:
                print(f'[{folder_path.name}] 已处理 {i} 个文件')

    # 展平所有层
    flattened = [item for sublist in layers_record for item in sublist]
    return flattened


if __name__ == '__main__':
    base_path = Path('Z:/hf-images1')

    # 需要处理的多个文件夹路径
    folder_names = ['Z:/hf-images1/images-r8', 'G:/hf-image2/images-r8']
    total_layers = []

    for folder_name in folder_names:
        folder_path = Path(folder_name)
        print(f'开始处理文件夹: {folder_path}')
        layers = process_folder(folder_path)
        total_layers.extend(layers)

    # 统计所有 layer 出现频率
    counter = Counter(total_layers)

    print('\n=== 合并统计结果 ===')
    for val, count in counter.most_common():
        print(f'Layer {val} 出现了 {count} 次')

    # 保存为 CSV 文件
    df = pd.DataFrame(counter.items(), columns=['layer', 'count'])
    df.sort_values(by='count', ascending=False, inplace=True)

    output_path = base_path / 'layer_statistics.csv'
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f'\n已保存统计结果到: {output_path}')
