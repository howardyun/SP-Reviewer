import pandas as pd
import json
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

def analyze_signature_stats(start_month: str, end_month: str, folder_path: str, output_csv: str = "signature_summary_all.csv"):
    """
    统计给定时间段内多个 CSV 文件中签名提交的分布情况。

    参数：
    - start_month: 开始时间，格式 "YYYY-MM"
    - end_month: 结束时间，格式 "YYYY-MM"
    - folder_path: 存放 CSV 文件的文件夹路径
    - output_csv: 输出结果保存的文件名（默认 "signature_summary_all.csv"）

    返回：
    - Pandas DataFrame，包含每类签名情况的统计数量
    """
    # 时间解析
    start_date = datetime.strptime(start_month, "%Y-%m")
    end_date = datetime.strptime(end_month, "%Y-%m")

    # 收集所有数据
    all_results = []

    def classify_repo(total, signed):
        if signed == 0:
            return "无签名提交"
        elif abs(total - signed) <= 1:
            return "全部签名提交"
        else:
            return "部分签名提交"

    # 遍历月份
    current = start_date
    while current <= end_date:
        filename = current.strftime("%Y-%m") + ".csv"
        filepath = os.path.join(folder_path, filename)
        if os.path.exists(filepath):
            try:
                df = pd.read_csv(filepath)
                df_parsed = df["repo_json"].apply(json.loads).apply(pd.Series)
                df_combined = pd.concat([df["repo_name"], df_parsed[["total_commits", "signed_commits"]]], axis=1)
                df_combined["签名情况"] = df_combined.apply(
                    lambda row: classify_repo(row["total_commits"], row["signed_commits"]), axis=1
                )
                all_results.append(df_combined[["repo_name", "签名情况"]])
            except Exception as e:
                print(f"⚠️ 处理文件 {filename} 时出错：{e}")
        else:
            print(f"⏭️ 文件不存在，跳过：{filename}")
        current += relativedelta(months=1)

    # 合并并统计
    if not all_results:
        print("❌ 没有找到任何有效数据文件。")
        return None

    final_df = pd.concat(all_results, ignore_index=True)
    signature_stats = final_df["签名情况"].value_counts().reset_index()
    signature_stats.columns = ["签名情况", "仓库数量"]

    # 保存结果
    output_path = os.path.join(folder_path, output_csv)
    signature_stats.to_csv(output_path, index=False)
    print(f"✅ 统计结果已保存至: {output_path}")
    return signature_stats

if __name__ == "__main__":
    # 调用函数，统计 2022-03 到 2025-05 的仓库签名情况
    df_result = analyze_signature_stats(
        start_month="2022-03",
        end_month="2025-05",
        folder_path="Z:/download_space/commit_history_info",  # 替换成你的目录
        output_csv="Z:/download_space/commit_history_info/all_signature_stats_1.csv"
    )
    print(df_result)