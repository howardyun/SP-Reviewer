import csv

from huggingface_hub import HfApi
from datetime import datetime, timezone
import os
import json



def initialize_output_dir(output_dir):
    """创建存储目录。"""
    os.makedirs(output_dir, exist_ok=True)

def preload_existing_models(output_dir):
    """预加载已有的模型数据到缓存中。"""
    monthly_models = {}
    for file_name in os.listdir(output_dir):
        if file_name.endswith(".json"):
            month_key = file_name.replace(".json", "")
            file_path = os.path.join(output_dir, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                monthly_models[month_key] = json.load(f)
    return monthly_models

def save_models_to_files(monthly_models, output_dir):
    """保存每个类别的数据到文件。"""
    for month_key, model_ids in monthly_models.items():
        file_path = os.path.join(output_dir, f"{month_key}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(model_ids, f, ensure_ascii=False, indent=4)
        print(f"已保存 {month_key} 的模型到文件: {file_path}")


def save_models_to_monthly_csv(monthly_models, output_dir):
    """将每个月份的模型数据保存为单独的 CSV 文件。"""
    os.makedirs(output_dir, exist_ok=True)

    for month_key, models in monthly_models.items():
        file_path = os.path.join(output_dir, f"{month_key}.csv")
        with open(file_path, "w", newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["ModelID", "Likes"])  # 写入表头

            for model in models:
                writer.writerow([model["id"], model["likes"]])

        print(f"已保存 {month_key} 的模型到 CSV 文件: {file_path}")



def process_models(spaces, monthly_models, start_date, end_date):
    """处理模型列表，将其分类到每个月份或未知分类。"""
    count = 0
    for space in spaces:
        created_at = space.createdAt
        created_at = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%S.%fZ') if created_at else None

        if created_at:
            month_key = created_at.strftime("%Y-%m")
        else:
            month_key = "unknown"

        if month_key not in monthly_models:
            monthly_models[month_key] = []

        # 检查是否已存在该模型
        if not any(item["id"] == space.id for item in monthly_models[month_key]):
            monthly_models[month_key].append({
                "id": space.id,
                "likes": space.likes
            })

        count += 1
        if count % 1000 == 0:
            print(f"已处理 {count} 个space")

def main(api_token, output_dir, start_date, end_date):
    """主函数，负责调用 API 并保存模型数据。"""
    # 初始化 API
    api = HfApi(token=api_token)

    # 初始化存储目录
    initialize_output_dir(output_dir)

    # 预加载已有数据
    monthly_models = preload_existing_models(output_dir)

    # 调用 API 获取模型数据
    print("正在调用 Hugging Face API 获取模型列表...")
    models = api.list_spaces(full=False)

    # 处理模型数据
    process_models(models, monthly_models, start_date, end_date)

    # 保存到文件
    save_models_to_monthly_csv(monthly_models, output_dir)

    print(f"所有spaceid文件已更新到目录: {output_dir}")

# 调用主函数
def run():
    API_TOKEN = "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"
    OUTPUT_DIR = "monthly_spaceId_files"
    START_DATE = datetime(2024, 1, 1, tzinfo=timezone.utc)
    END_DATE = datetime(2025, 12, 31, tzinfo=timezone.utc)

    main(API_TOKEN, OUTPUT_DIR, START_DATE, END_DATE)

if __name__ == "__main__":
    run()
