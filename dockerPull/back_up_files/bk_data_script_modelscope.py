from modelscope.hub.api import HubApi

# YOUR_ACCESS_TOKEN = '请从https://modelscope.cn/my/myaccesstoken 获取SDK令牌'
# api = HubApi()
# api.login('77ff52f9-98fe-41be-88a7-718d48834550')
#
#
# owner_name = 'shaoxuanyun'
# dataset_name = 'Space-Image-Dataset-Second-Time'
#
# print('开始上传')
# api.upload_folder(
#     repo_id=f"{owner_name}/{dataset_name}",
#     folder_path='E:/hf-image2-bk',
#     commit_message='upload dataset folder to repo',
#     repo_type = 'dataset'
# )
# print('上传结束')
#
#
#
# from modelscope.hub.snapshot_download import snapshot_download
# import os
#
# model_dir = snapshot_download('username/modelname')
#
# file_count = 0
# for root, dirs, files in os.walk(model_dir):
#     file_count += len(files)
#
# print(f'仓库总文件数：{file_count}')


import requests

def list_dataset_files(owner, dataset_name, branch='master', path=''):
    api_url = f'https://modelscope.cn/api/v1/datasets/{owner}/{dataset_name}/files'
    params = {'Revision': branch, 'Path': path}
    headers = {'Accept': 'application/json'}

    try:
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        items = response.json()
    except Exception as e:
        print(f'Error fetching {path or "root"}: {e}')
        return []

    all_files = []
    for item in items:
        if item['type'] == 'file':
            all_files.append(item['path'])
        elif item['type'] == 'tree':
            all_files.extend(list_dataset_files(owner, dataset_name, branch, item['path']))
    return all_files


# shaoxuanyun/Space-Image-Dataset-Second-Time





# 示例：列出某个数据集中的所有文件（替换为你想看的数据集）
owner = 'open-r1'
dataset_name = 'Mixture-of-Thoughts'

file_list = list_dataset_files(owner, dataset_name)
print(f'共找到 {len(file_list)} 个文件：')
for f in file_list:
    print(f)



