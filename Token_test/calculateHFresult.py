import os

def processSingleFile(file_path):
    private_true_counts = {"Models": 0, "Datasets": 0, "Spaces": 0}
    current_section = None

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.endswith("Models:"):
                current_section = "Models"
            elif line.endswith("Datasets:"):
                current_section = "Datasets"
            elif line.endswith("Spaces:"):
                current_section = "Spaces"
            elif line == "" or line.startswith(">>>") or line.endswith("Collections:"):
                current_section = None
            elif current_section and "Private=True" in line:
                private_true_counts[current_section] += 1

    print(f"\n处理文件: {file_path}")
    print("Private=True 统计结果：")
    for key, count in private_true_counts.items():
        print(f"{key}: {count}")
    print(f"总计: {sum(private_true_counts.values())}")
    return   private_true_counts["Models"],private_true_counts["Datasets"],private_true_counts["Spaces"]


# 初始化总计数变量
total_error = 0
total_invalid = 0
total_success = 0
total_leak = 0
total_leak_model = 0
total_leak_datasets = 0
total_leak_spaces = 0
# 获取主目录下的所有子文件夹
base_folder = 'testresult'
folders = [f for f in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, f))]

for fold in folders:
    print(f"\n处理文件夹：{fold}")

    category = ["error", "invalid", "success"]
    file_counts = {}

    for cat in category:
        folder_path = os.path.join(base_folder, fold, cat)
        if os.path.exists(folder_path):
            files = [
                name for name in os.listdir(folder_path)
                if os.path.isfile(os.path.join(folder_path, name))
            ]
            count = len(files)
            file_counts[cat] = count

            # 如果是 success 文件夹，遍历并处理文件
            if cat == "success":
                for filename in files:
                    file_path = os.path.join(folder_path, filename)
                    models_count,datasets_count,spaces_count = processSingleFile(file_path)
                    if models_count == 0 and datasets_count == 0 and spaces_count == 0:
                        continue
                    else:
                        total_leak += 1
                        total_leak_model += models_count
                        total_leak_datasets += datasets_count
                        total_leak_spaces += spaces_count

        else:
            file_counts[cat] = 0

    # 累加总计数
    total_error += file_counts["error"]
    total_invalid += file_counts["invalid"]
    total_success += file_counts["success"]

    print("当前分类文件数：", file_counts)

# 输出最终统计
print("\n=== 总计 ===")
print(f"total error: {total_error}")
print(f"total invalid: {total_invalid}")
print(f"total success: {total_success}")
print(f"total leak: {total_leak}/{total_success}")
print(f"total leak model: {total_leak_model}")
print(f"total leak datasets: {total_leak_datasets}")
print(f"total leak spaces: {total_leak_spaces}")
print(f"total leak model+ datasets + spaces: {total_leak_model+total_leak_datasets+total_leak_spaces}")
print(f"总文件数: {total_error + total_invalid + total_success}")
