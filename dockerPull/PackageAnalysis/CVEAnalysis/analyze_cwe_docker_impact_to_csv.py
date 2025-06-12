import json
import pandas as pd
from typing import List, Dict
import os
from tqdm import tqdm
from openai import OpenAI

client = OpenAI(
    api_key="9278228e128744ec94bf3e068f4cbdc6.Mr6uEiXteDt1ScbN",
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)


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


def query_api(cwe_id: str) -> Dict:
    """
    调用 API 判断 CWE 是否对 Docker 有影响。
    返回格式: {"cwe_id": str, "is_relevant": bool, "explanation": str}
    """
    messages = [
        {"role": "user", "content": f"Analyzing whether {cwe_id} would cause real harm to Docker's usage. Return a "
                                    f"JSON object"
                                    f"with 'cwe_id', 'is_relevant' (in English, e.g., true or false), "
                                    f"and 'explanation' (a brief explanation in Chinese)."}
    ]

    try:
        response = client.chat.completions.create(
            model="glm-4-air-250414",
            messages=messages,
            max_tokens=400,
            temperature=0.4,
            response_format={"type": "json_object"},
            stream=False
        )

        # 解析 API 返回的 content
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"cwe_id": cwe_id, "is_relevant": False, "explanation": "API returned invalid JSON"}
        else:
            return {"cwe_id": cwe_id, "is_relevant": False, "explanation": "No valid response from API"}

    except Exception as e:
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
        result = query_api(cwe_id)
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
