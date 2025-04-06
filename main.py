import DataCollection
import DataCollection.CollectSpaceList
import DataCollection.CollectSpaceVariable 
import Regex_Match
import json
import glob
import os
from Analysis.ApiVerify import (verify_cohere_api_key, verify_github_token, test_openai, 
                      test_huggingface_api, groq_api, aws_api, mongodb_test, 
                      postgresql_test, test_anthropic, test_deepseek, 
                      test_Gemini, test_nvidia, test_replicate)

def extract_values_from_file(filename):
    """
    读取JSON文件并提取所有value值
    """
    try:
        # 读取文件
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # 提取values
        values = []
        for repo in data:
            result = repo.get('result', {})
            for config in result.values():
                if 'value' in config:
                    values.append((repo["repo"],config['value']))
                    
        return values
    
    except FileNotFoundError:
        print(f"文件 {filename} 未找到")
        return None
    except json.JSONDecodeError:
        print("JSON 格式错误")
        return None




DataCollection.CollectSpaceList.run()


 # 设定文件路径
 # 设定文件路径
folder_path = "../../Data/Leak_repo_data"  # 修改为你的实际路径
file_pattern = os.path.join(folder_path, "*.csv")  # 查找所有 CSV 文件
all_time_interval = []
# 获取所有匹配的文件列表
csv_files = sorted(glob.glob(file_pattern))
for file in csv_files:
    filename = os.path.basename(file)  # 获取文件名
    time = filename.split("_")[0]
    print("正在处理"+time+'.'*10)
    repo_file_path = f"../../Data/monthly_spaceId_files/{time}.json"
    scan_file_path = f"../../Data/Leak_repo_data/{time}_scan_results.csv"
    #查找
    filtered_data = DataCollection.CollectSpaceVariable.search_varible(repo_file_path)
    output_file = 'Output/'+ f'{time}_space_variables.json'
    # 保存 filtered_data 到 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=4, default=DataCollection.CollectSpaceVariable.custom_serializer) 



input_file=os.path.join('Output', "*.json")
filename = sorted(glob.glob(file_pattern))
for file in filename:
    values=extract_values_from_file(file)
    if values is None:
        continue
    for i in values:
        secret=Regex_Match.app.regex_check(i[1])
        if secret==None:
            continue
        # 创建存储验证结果的字典
        result_dict = {
            'Repository': i[0],
            'api': i[1],
            'organization': None,
            'valid': 0,
            'available': 0,
            'userinfo': None,
            'permissions': None,
            'balance': None,
            'models': None,
            'datasets': None,
            'spaces': None,
            'context': None
        }
        api_type = secret[0].lower()  # 转换为小写以保持一致性
        if api_type == 'huggingface':
            test_huggingface_api(secret[1], result_dict)
        elif api_type == 'openai':
            test_openai(secret[1], result_dict)
        elif api_type == 'github':
            verify_github_token(secret[1], result_dict)
        elif api_type == 'cohere':
            verify_cohere_api_key(secret[1], result_dict)
        elif api_type == 'groq':
            groq_api(secret[1], result_dict)
        elif api_type == 'deepseek':
            test_deepseek(secret[1], result_dict)
        elif api_type == 'gemini':
            test_Gemini(secret[1], result_dict)
        elif api_type == 'nvidia':
            test_nvidia(secret[1], result_dict)
        elif api_type == 'replicate':
            test_replicate(secret[1], result_dict)
        elif api_type == 'anthropic':
            test_anthropic(secret[1], result_dict)
        elif api_type == 'mongodb':
            mongodb_test(secret[1], result_dict)
        elif api_type == 'postgresql':
            postgresql_test(secret[1], result_dict)
        elif api_type == 'aws':
            # AWS需要额外的参数，这里假设secret[1]包含所需信息
            # 你可能需要根据实际情况调整参数格式
            try:
                access_key, secret_key, region, bucket = secret[1].split(',')
                aws_api(access_key, secret_key, region, bucket)
            except ValueError:
                result_dict['organization'] = 'aws'
                result_dict['valid'] = 0
                result_dict['available'] = 0
                print(f"AWS API密钥格式错误: {secret[1]}")
        else:
            result_dict['organization'] = 'unknown'
            print(f"未知的API类型: {api_type}")
        
        # 打印验证结果（可选）
        print(f"验证结果 for {i[0]}: {result_dict}")



        