import json
import os

from dockerPull.Analysis.PackageExtract.analysisUtils import extract_Pypi,check_pypi_info

from collections import defaultdict
from pathlib import Path
import pandas as pd
def save_to_json(filename, package_dict,path = ''):
    # 假设你的字典是 final_package_dict
    # 保存到 JSON 文件
    with open(f'{path}/{filename}.json', 'w', encoding='utf-8') as f:
        json.dump(package_dict, f, ensure_ascii=False, indent=4)

def to_dict(all_packages):
    package_dict = defaultdict(list)

    for pkg in all_packages:
        pkg_clean = pkg.replace('.wh.', '')
        name, version = pkg_clean.rsplit('-', 1)
        package_dict[name].append(version)
    return package_dict

def get_layers_by_manifest_json(file_path):

    # 读取 JSON 内容
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 提取 "Layers" 内容
    if isinstance(data, list) and 'Layers' in data[0]:
        layers = data[0]['Layers']
        # print("Found Layers:")
        for layer in layers:
            layer = str(layer)
            # print(layer.split('/')[0])
        return [s.split('/')[0] for s in layers]
    else:
        # print("No 'Layers' field found.")
        return []
def extract_pypi_by_layers(target_path, layers):
    all_packages = set()
    lack_layers = []
    for layer in layers:
        try:
            file_path = os.path.join(target_path, layer+'/tree.txt')
            with open(file_path, 'rb') as f:
                content_bytes = f.read()
                if check_pypi_info(content_bytes):
                    package_versions = extract_Pypi(content_bytes)
                    all_packages.update(package_versions)
        except FileNotFoundError:
            lack_layers.append(layer)
            # print(f'{layer} not found.')
    return to_dict(all_packages), lack_layers

# # JSON 文件路径
# file_path = "manifests/_kemalpm-openai-whisper-large-v3__manifest.json"
# layers = get_layers_by_manifest_json(file_path)
#
#
# if len(layers) != 0:
#     target_path = ""
#     packages = extract_pypi_by_layers('testdata/kemalpm-openai-whisper-large-v3/',layers)
#     save_to_json('kemalpm-openai-whisper-large-v3',packages)
#


if __name__ == '__main__':
    base_path = r'Z:/Space_Image_1'
    folder_path = Path(f'{base_path}/images-r8')  # 替换为你的文件夹路径
    json_files = list(folder_path.glob('*.json'))  # 只匹配当前文件夹的 .json 文件
    lack_layer_count = 0
    # 如果要包含子文件夹中的 json 文件
    # json_files = list(folder_path.rglob('*.json'))
    lack_record = {}
    index = 0
    for file in json_files:
        index = index + 1
        if index % 1000 == 0:
            print(index)
            if index % 3000 == 0:
                df = pd.DataFrame(list(lack_record.items()), columns=['manifestname', 'layers'])
                df.to_csv(f'lack_layers{lack_layer_count}.csv', index=False, encoding='utf-8')
                lack_layer_count +=1
                lack_record.clear()
        # if index % 10000 == 0:
        #     break
        # JSON 文件路径
        file_path =str(file)
        layers = get_layers_by_manifest_json(file_path)

        if len(layers) != 0:
            target_path = "" #换成
            packages, lack_layers = extract_pypi_by_layers(f'{base_path}/layers',layers)
            if packages:
                save_filename = file_path.split('\\')[-1].split('_')[1]
                save_to_json(save_filename, packages, f'{base_path}/Space_Pypi_output')
                print(save_filename)


            if len(lack_layers) != 0:
                lack_record[file_path.split('\\')[-1]] = lack_layers
                # save_filename = file_path.split('\\')[-1].split('_')[1]
                # save_to_json(save_filename, packages, f'{base_path}/Space_Pypi_output')
                # print(file_path)
            else:
                print()
                # save_filename = file_path.split('\\')[-1].split('_')[1]
                # save_to_json(save_filename,packages,f'{base_path}/Space_Pypi_output')


    df = pd.DataFrame(list(lack_record.items()), columns=['manifestname', 'layers'])
    df.to_csv(f'lack_layers{lack_layer_count}.csv', index=False, encoding='utf-8')
    lack_layer_count += 1
    lack_record.clear()

        # print(file)




