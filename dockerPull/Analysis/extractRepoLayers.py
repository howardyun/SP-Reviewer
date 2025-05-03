import json
import os

from analysisUtils import extract_Pypi,check_pypi_info

from collections import defaultdict

def save_to_json(filename, package_dict):
    # 假设你的字典是 final_package_dict
    # 保存到 JSON 文件
    with open(f'{filename}.json', 'w', encoding='utf-8') as f:
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
        print("Found Layers:")
        for layer in layers:
            layer = str(layer)
            print(layer.split('/')[0])
        return [s.split('/')[0] for s in layers]
    else:
        print("No 'Layers' field found.")
        return []
def extract_pypi_by_layers(target_path, layers):
    all_packages = set()

    for layer in layers:
        try:
            file_path = os.path.join(target_path, layer+'/tree.txt')
            with open(file_path, 'rb') as f:
                content_bytes = f.read()
                if check_pypi_info(content_bytes):
                    package_versions = extract_Pypi(content_bytes)
                    all_packages.update(package_versions)
        except FileNotFoundError:
            print(f'{layer} not found.')
    return to_dict(all_packages)

# JSON 文件路径
file_path = "manifests/_kemalpm-openai-whisper-large-v3__manifest.json"
layers = get_layers_by_manifest_json(file_path)


if len(layers) != 0:
    target_path = ""
    packages = extract_pypi_by_layers('testdata/kemalpm-openai-whisper-large-v3/',layers)
    save_to_json('kemalpm-openai-whisper-large-v3',packages)






