import tqdm
from openai import OpenAI
import json

client = OpenAI(api_key="913cfb02ffa84828ad836098e88d68c7.RIq89Zp76UbHaFnF",
                base_url="https://open.bigmodel.cn/api/paas/v4/")


def classify_package(package_info):
    """使用大模型对包进行分类"""

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

        Important Rules:
        1. Respond ONLY with the exact category name from the list above
        2. No explanations, no punctuation, just the category
        3. Be specific - choose subcategories when applicable
        4. If unsure between two categories, pick the more specific one
        
        {package_info}

        Your classification:
        """

    try:
        response = client.chat.completions.create(
            model="glm-4-air",
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

        print(f"{e}")
        return "Unknown"


if __name__ == '__main__':
    # 打开JSON文件并读取内容
    with open('classified_packages.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    classified_results = {}

    for package in tqdm.tqdm(data):
        package_raw_data = data.get(package, {})
        if package_raw_data["category"] == "Unknown" and "info" in package_raw_data and "error" not in package_raw_data[
            "info"]:
            a = classify_package(package_raw_data)
            package_raw_data["category"] = a
        classified_results[package] = package_raw_data

    with open("classified_new_packages.json", 'w', encoding='utf-8') as f:
        json.dump(classified_results, f, ensure_ascii=False, indent=2)
