import json

import pandas as pd
import requests
from typing import List, Dict
import os

from tqdm import tqdm


def read_and_process_cwe(file_path: str) -> List[str]:
    """
    读取 CSV 文件，提取并清洗 Cwe_Ids 列，生成 CWE 列表。
    """
    try:
        # 读取 CSV 文件
        df = pd.read_csv(file_path)
        # 去除空值
        cwe_series = df['Cwe_Ids'].dropna()
        # 拆分每行中的 CWE 项
        cwe_list = []
        for item in cwe_series:
            if isinstance(item, str):
                cwe_list.extend([cwe.strip() for cwe in item.split(",") if cwe.strip()])
        # 去重
        return list(set(cwe_list))
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return []
    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        return []


def query_api(cwe_id: str, api_key: str, api_url: str = "https://api.deepseek.com/chat/completions") -> Dict:
    """
    调用 DeepSeek API 判断 CWE 是否对 Docker 有影响。
    返回格式: {"cwe_id": str, "is_relevant": bool, "explanation": str}
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 注意：DeepSeek Chat API 使用 "messages" 而非 "prompt"
    messages = [
        {"role": "user", "content": f"Is {cwe_id} relevant to Docker security? "
                                    "Provide a brief explanation and return a JSON object with 'cwe_id', "
                                    "'is_relevant', and 'explanation' fields.'is_relevant'为英文，'explanation'内容为中文"}
    ]

    payload = {
        "model": "deepseek-chat",
        "messages": messages,  # 关键修改：使用 messages
        "max_tokens": 300,
        "temperature": 0.7,  # 建议降低 temperature 以提高确定性
        "response_format": {"type": "json_object"}  # 要求返回 JSON 格式（如果 API 支持）
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        # 解析 API 返回的 content（假设返回在 choices[0].message.content）
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0].get("message", {}).get("content", "{}")
            try:
                return json.loads(content)  # 尝试解析返回的 JSON 字符串
            except json.JSONDecodeError:
                return {"cwe_id": cwe_id, "is_relevant": False, "explanation": "API returned invalid JSON"}
        else:
            return {"cwe_id": cwe_id, "is_relevant": False, "explanation": "No valid response from API"}

    except requests.RequestException as e:
        print(f"Error querying API for {cwe_id}: {str(e)}")
        return {"cwe_id": cwe_id, "is_relevant": False, "explanation": f"API error: {str(e)}"}


def save_to_csv(results: List[Dict], output_file: str):
    """
    将结果保存为 CSV 文件。
    """
    try:
        # 转换为 DataFrame
        df = pd.DataFrame(results, columns=["cwe_id", "is_relevant", "explanation"])
        # 保存为 CSV
        df.to_csv(output_file, index=False, encoding="utf-8")
        print(f"Results saved to {output_file}")
    except Exception as e:
        print(f"Error saving CSV: {str(e)}")


def main():
    # 输入文件路径
    file_path = "../../Data/Pypi/pypi_osv/merged_result.csv"
    # API 密钥（需替换为真实密钥）
    api_key = os.getenv("deepseek_API_KEY", "sk-de52569cccea4977bfa54db7d6690569")
    # 输出文件
    output_file = "cwe_docker_impact.csv"

    # 读取并处理 CWE 列表
    cwe_list = read_and_process_cwe(file_path)
    if not cwe_list:
        print("No valid CWE IDs found.")
        return

    # 存储结果
    results = []

    # 对每个 CWE 调用 API
    for cwe_id in tqdm(cwe_list, desc="Processing CWE IDs"):
        print(f"Processing {cwe_id}...")
        result = query_api(cwe_id, api_key)
        print(result)
        results.append({
            "cwe_id": result.get("cwe_id", cwe_id),
            "is_relevant": result.get("is_relevant", False),
            "explanation": result.get("explanation", "No explanation provided")
        })

    # 保存结果到 CSV
    save_to_csv(results, output_file)


if __name__ == "__main__":
    main()
