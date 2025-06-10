import requests
import json
from openai import OpenAI  # 或其他大模型API

# 初始化大模型客户端（这里以OpenAI为例）
client = OpenAI(api_key="sk-de52569cccea4977bfa54db7d6690569", base_url="https://api.deepseek.com")  # 请替换为您的实际API密钥


def get_pypi_info(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        response = requests.get(url)
        data = response.json()
        if data.get("message") == 'Not Found':
            return None

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

        return package_data

    except Exception as e:
        print(f"Error fetching info for {package_name}: {e}")
        return None


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
            model="deepseek-chat",  # 或使用其他适合的模型
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


def save_results(results, filename):
    """保存分类结果到JSON文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    json_data_url = "../../Data/Pypi/PypiMetaData/first_data_pypi_info.json"
    output_file = "classified_packages.json"

    # 加载已有的包列表
    with open(json_data_url, "r", encoding="utf-8") as f:
        data = json.load(f)

    pypi_package_list = list(data.keys())
    classified_results = {}

    # 限制处理的包数量，用于测试
    max_packages = 5  # 设为None处理所有包
    packages_to_process = pypi_package_list[:max_packages] if max_packages else pypi_package_list

    for i, package_name in enumerate(packages_to_process, 1):
        print(f"\nProcessing package {i}/{len(packages_to_process)}: {package_name}")

        package_info = get_pypi_info(package_name)
        if package_info:
            category = classify_package(package_info)
            classified_results[package_name] = {
                "info": package_info,
                "category": category
            }
            print(f"分类结果: {category}")
        else:
            classified_results[package_name] = {
                "info": None,
                "category": "Unknown"
            }
            print("无法获取包信息")

    # 保存分类结果
    save_results(classified_results, output_file)
    print(f"\n分类完成! 结果已保存到 {output_file}")