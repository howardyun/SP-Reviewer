from pathlib import Path

from collections import defaultdict

import json

import sqlite3

def get_layers_by_manifest_json(file_path):

    # 读取 JSON 内容
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 提取 "Layers" 内容
    if isinstance(data, list) and 'Layers' in data[0]:
        layers = data[0]['Layers']
        config = data[0]['Config']
        repoTags = data[0]['RepoTags']
        # print("Found Layers:")
        for layer in layers:
            layer = str(layer)
            # print(layer.split('/')[0])
        return [s.split('/')[0] for s in layers] ,config,repoTags
    else:
        # print("No 'Layers' field found.")
        return [],[],[]

def check_lack_layer(layers,layer_folder_names):
    lack_layer = []
    for layer in layers:
        if layer not in layer_folder_names:
            lack_layer.append(layer)

    return lack_layer


def iterate_layers(dir, cache_file='layers_cache_first_data.json'):
    cache_path = Path(cache_file)

    # 如果缓存文件存在，直接加载返回
    if cache_path.exists():
        with open(cache_path, 'r', encoding='utf-8') as f:
            print(f"从缓存中读取层信息：{cache_file}")
            return set(json.load(f))

    # 否则重新遍历文件夹并记录
    root_path = Path(dir)
    folder_names = set()

    for subfolder in root_path.iterdir():
        if subfolder.is_dir():
            folder_names.add(subfolder.name)

    # 写入缓存文件
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(list(folder_names), f, ensure_ascii=False, indent=4)
        print(f"已保存层信息到缓存：{cache_file}")

    return folder_names

def iterate_manifest(dir,folder_names):
    folder_path = Path(dir)  # 替换为你的文件夹路径
    json_files = list(folder_path.glob('*.json'))  # 只匹配当前文件夹的 .json 文件
    # 如果要包含子文件夹中的 json 文件
    # json_files = list(folder_path.rglob('*.json'))
    count = 0
    index_lack = 0
    index_complete = 0
    for file in json_files:
        count += 1
        if count % 1000 == 0:
            print(count)
        file_path = str(file)
        layers,config,repotag = get_layers_by_manifest_json(file_path)
        lack_layer = check_lack_layer(layers, folder_names)
        if len(lack_layer) != 0 :
            index_lack += 1
            # print(file.name)
            data = [{
                "Config": config,
                "RepoTags": repotag,
                "Layers": lack_layer
            }]
            with open(f'lackLayersRepo/{file.name}', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        else:
            index_complete += 1
    print(f'Complete:{index_complete}')
    print(f'lack:{index_lack}')


if __name__ == '__main__':
    # layer folder 的路径
    base_path= 'Z:/hf-images1'
    # 获取所有的layer folder 的名称
    folder_names = iterate_layers(f'{base_path}/layers')
    iterate_manifest(f'{base_path}/images-r8',folder_names)





