import pandas as pd
from huggingface_hub import HfApi
from datetime import datetime, timezone
import os



def initialize_output_dir(output_dir):
    """创建存储目录。"""
    os.makedirs(output_dir, exist_ok=True)


def preload_existing_models(output_dir):
    """预加载已有的模型数据到缓存中。"""
    monthly_models = {}
    for file_name in os.listdir(output_dir):
        if file_name.endswith(".csv"):
            month_key = file_name.replace(".csv", "")
            file_path = os.path.join(output_dir, file_name)
            try:
                df = pd.read_csv(file_path)
                monthly_models[month_key] = set(df['id'].tolist())
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                monthly_models[month_key] = set()
    return monthly_models


def save_models_to_files(monthly_models, output_dir):
    """保存每个类别的数据到CSV文件。"""
    for month_key, spaces in monthly_models.items():
        file_path = os.path.join(output_dir, f"{month_key}.csv")
        # Convert space objects to a list of dictionaries
        space_data = []
        for space in spaces:
            if isinstance(space, dict):
                space_data.append(space)
            else:
                # Convert space object to dict with relevant fields
                space_data.append({
                    'id': space.id,
                    'author': space.author or '',
                    'created_at': space.created_at.isoformat() if space.created_at else '',
                    'likes': space.likes or 0,
                    'private': space.private,
                    "models": space.models or (space.card_data.models if space.card_data is not None else []) or [],
                    "datasets": space.datasets or (space.card_data.datasets if space.card_data is not None else []) or [],
                    "trending_score": space.trending_score or 0,
                    'last_modified': space.last_modified.isoformat() if space.last_modified else ''
                })

        # Create DataFrame and save to CSV
        if space_data:
            df = pd.DataFrame(space_data)
            df.to_csv(file_path, index=False, encoding='utf-8')
            print(f"已保存 {month_key} 的space信息到文件: {file_path}")


def process_models(spaces, monthly_models, start_date, end_date):
    """处理space列表，将其分类到每个月份或未知分类。"""
    count = 0
    for space in spaces:
        created_at = space.created_at
        if created_at and start_date <= created_at <= end_date:
            month_key = created_at.strftime("%Y-%m")
        else:
            continue

        if month_key not in monthly_models:
            monthly_models[month_key] = []

        # Only add if space ID isn't already in the month's data
        space_id = space.id
        existing_ids = {s.id if not isinstance(s, dict) else s['id'] for s in monthly_models[month_key]}
        if space_id not in existing_ids:
            monthly_models[month_key].append(space)

        count += 1
        if count % 1000 == 0:
            print(f"已处理 {count} 个space")


def main(api_token, output_dir, start_date, end_date):
    """主函数，负责调用 API 并保存space数据。"""
    # 初始化 API
    api = HfApi(token=api_token)

    # 初始化存储目录
    initialize_output_dir(output_dir)

    # 预加载已有数据
    monthly_models = preload_existing_models(output_dir)

    # 调用 API 获取space数据
    print("正在调用 Hugging Face API 获取space列表...")
    spaces = api.list_spaces(full=True, sort="created_at")

    # 处理space数据
    process_models(spaces, monthly_models, start_date, end_date)

    # 保存到文件
    save_models_to_files(monthly_models, output_dir)

    print(f"所有space信息文件已更新到目录: {output_dir}")


# 调用主函数
def run():
    API_TOKEN = "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"
    OUTPUT_DIR = "../../Data/monthly_spaceId_files"
    START_DATE = datetime(2022, 3, 1, tzinfo=timezone.utc)
    END_DATE = datetime(2025, 5, 31, tzinfo=timezone.utc)

    main(API_TOKEN, OUTPUT_DIR, START_DATE, END_DATE)


if __name__ == "__main__":
    run()
