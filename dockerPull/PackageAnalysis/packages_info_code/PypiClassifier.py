import requests
import json
import os
from openai import OpenAI
from tqdm import tqdm  # 用于显示进度条

# 初始化大模型客户端
client = OpenAI(api_key="sk-de52569cccea4977bfa54db7d6690569", base_url="https://api.deepseek.com")

# 文件路径配置
RAW_DATA_FILE = "pypi_packages_raw.json"
CLASSIFIED_DATA_FILE = "classified_packages.json"


def fetch_all_packages_info(package_list, output_file):
    """获取所有包的原始信息并保存到本地"""
    if os.path.exists(output_file):
        print(f"检测到已存在的原始数据文件 {output_file}")
        return

    all_packages_data = {}

    print(f"开始从PyPI获取{len(package_list)}个包的原始数据...")

    for package_name in tqdm(package_list):
        url = f"https://pypi.org/pypi/{package_name}/json"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                info = data['info']
                package_data = {
                    "name": package_name,
                    "description": info.get('description', ''),
                    "project_urls": info.get('project_urls', {}),
                    "version": info.get('version', ''),
                    "summary": info.get('summary', ''),
                    "author": info.get('author', ''),
                    "upload_time": data['releases'][info['version']][0]['upload_time'] if info.get('version') and data[
                        'releases'].get(info['version']) else ''
                }
                all_packages_data[package_name] = package_data
            else:
                all_packages_data[package_name] = {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            all_packages_data[package_name] = {"error": str(e)}

    # 保存原始数据
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_packages_data, f, ensure_ascii=False, indent=2)

    print(f"所有包原始数据已保存到 {output_file}")


def extract_package_info(raw_data):
    """从原始数据中提取我们需要的信息"""
    if not raw_data or isinstance(raw_data, str) or "info" not in raw_data:
        return None

    info = raw_data['info']
    package_data = {
        "name": info.get('name', ''),
        "description": info.get('description', ''),
        "project_urls": info.get('project_urls', {}),
        "version": info.get('version', ''),
        "summary": info.get('summary', ''),
        "author": info.get('author', ''),
        "upload_time": raw_data['releases'][info['version']][0]['upload_time']
        if info.get('version') and raw_data['releases'].get(info['version'])
        else ''
    }
    return package_data


def classify_package(package_info):
    """使用大模型对包进行分类"""
    if not package_info or not package_info.get('description'):
        return "Unknown"

    prompt = f"""
        Analyze the following Python package information and classify it into the most appropriate category. 
        Choose ONLY ONE from these precise categories:
        - Web Development
        - Data Science/Machine Learning
        - Web Scraping
        - System Tools
        - Game Development
        - Graphics Processing
        - Natural Language Processing
        - Computer Vision
        - Automated Testing
        - Databases
        - Security
        - DevOps
        - Scientific Computing
        - Networking
        - GUI Development
        - Other (only if none above fit)

        Package Name: {package_info['name']}
        Description: {package_info.get('description', '')}
        Summary: {package_info.get('summary', '')}

        Important Rules:
        1. Respond ONLY with the exact category name from the list above
        2. No explanations, no punctuation, just the category
        3. Be specific - choose subcategories when applicable
        4. If unsure between two categories, pick the more specific one

        Your classification:
        """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的Python包分类助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=30
        )

        category = response.choices[0].message.content.strip()
        return category

    except Exception as e:
        print(f"Error classifying package {package_info['name']}: {e}")
        return "Unknown"


def process_classification(package_list, raw_data_file, output_file):
    """从本地文件读取数据并进行分类处理"""
    # 加载原始数据
    with open(raw_data_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    classified_results = {}

    print(f"开始处理{len(package_list)}个包的分类...")

    for package_name in tqdm(package_list):
        package_raw_data = raw_data.get(package_name, {})
        package_info = extract_package_info(package_raw_data)

        if package_info:
            category = classify_package(package_info)
            classified_results[package_name] = {
                "info": package_info,
                "category": category
            }
        else:
            classified_results[package_name] = {
                "info": None,
                "category": "Unknown"
            }

    # 保存分类结果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(classified_results, f, ensure_ascii=False, indent=2)

    print(f"分类完成! 结果已保存到 {output_file}")


if __name__ == "__main__":
    # 加载已有的包列表
    with open("../../Data/Pypi/PypiMetaData/first_data_pypi_info.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    with open("../../Data/Pypi/PypiMetaData/second_data_pypi_info.json", "r", encoding="utf-8") as f:
        data2 = json.load(f)

    pypi_package_list = list(data.keys())

    pypi_package_list2 = list(data2.keys())

    pypi_package_list.extend(pypi_package_list2)

    pypi_package_list = list(set(pypi_package_list))

    # 第一步：获取所有包原始数据（如果不存在）
    fetch_all_packages_info(pypi_package_list, RAW_DATA_FILE)

    # 第二步：处理分类
    process_classification(pypi_package_list, RAW_DATA_FILE, CLASSIFIED_DATA_FILE)
