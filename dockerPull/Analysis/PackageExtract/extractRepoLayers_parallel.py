import json
import os
from pathlib import Path
from collections import defaultdict
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..analysisUtils import extract_Pypi, check_pypi_info


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
    if not layers:
        return None

    target_path = f"{base_path}/layers"
    packages, lack_layers = extract_pypi_by_layers(target_path, layers)
    if packages:
        save_filename = file_path.split('\\')[-1].split('_')[1]
        save_to_json(save_filename, packages, f'{base_path}/Space_Pypi_output')
    if lack_layers:
        return (file_path.split('\\')[-1], lack_layers)
    return None


if __name__ == '__main__':
    base_path = r'Z:/Space_Image_1'
    folder_path = Path(f'{base_path}/images-r8')
    json_files = list(folder_path.glob('*.json'))  # 当前目录下的所有 .json 文件

    lack_record = {}
    lack_layer_count = 0
    batch_size = 3000

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_manifest, file, base_path): file for file in json_files}

        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result:
                manifestname, layers = result
                lack_record[manifestname] = layers

            if (i + 1) % batch_size == 0:
                print('Record:'+str(3000*(lack_layer_count+1)))
                df = pd.DataFrame(list(lack_record.items()), columns=['manifestname', 'layers'])
                df.to_csv(f'lack_layers_{lack_layer_count}.csv', index=False, encoding='utf-8')
                lack_layer_count += 1
                lack_record.clear()

    # 最后一次记录
    if lack_record:
        df = pd.DataFrame(list(lack_record.items()), columns=['manifestname', 'layers'])
        df.to_csv(f'lack_layers_{lack_layer_count}.csv', index=False, encoding='utf-8')
