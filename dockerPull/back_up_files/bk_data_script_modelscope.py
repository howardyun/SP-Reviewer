from modelscope.hub.api import HubApi

# YOUR_ACCESS_TOKEN = '请从https://modelscope.cn/my/myaccesstoken 获取SDK令牌'
api = HubApi()
api.login('77ff52f9-98fe-41be-88a7-718d48834550')


owner_name = 'shaoxuanyun'
dataset_name = 'Space-Image-Dataset-First-Time'

print('开始上传')
api.upload_folder(
    repo_id=f"{owner_name}/{dataset_name}",
    folder_path='Z:/hf-image-first-time-bk',
    commit_message='upload dataset folder to repo',
    repo_type = 'dataset'
)
print('上传结束')