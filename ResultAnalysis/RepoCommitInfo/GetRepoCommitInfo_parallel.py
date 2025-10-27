import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
def parse_git_log_output(output):
    commits = []
    sections = output.split("===COMMIT===")
    for section in sections:
        lines = section.strip().splitlines()
        if not lines:
            continue

        # 提取 commit hash
        commit_hash = lines[0].strip()

        # 提取 author name 和 email（跳过 gpg 行）
        author_name = None
        author_email = None
        for i in range(1, len(lines)):
            if not lines[i].startswith("gpg:"):
                if author_name is None:
                    author_name = lines[i].strip()
                elif author_email is None:
                    author_email = lines[i].strip()
                    signature_block = "\n".join(lines[i+1:])  # 剩余的为 signature block
                    break

        if author_name and author_email:
            has_signature = "gpg: Signature made" in signature_block
            commits.append({
                "commit": commit_hash,
                "author_name": author_name,
                "author_email": author_email,
                "signed": has_signature
            })
        else:
            print(f"⚠️ 无法解析作者信息，跳过 commit: {commit_hash}")

    return commits

def check_repo(repo_path):
    print(f"\n==== 检查仓库：{os.path.basename(repo_path)} ====")
    try:
        result = subprocess.run(
            [
                "git", "log",
                "--reverse",
                "--pretty=format:===COMMIT===%n%H%n%an%n%ae",
                "--show-signature"
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60
        )

        output = result.stdout
        commits_info = parse_git_log_output(output)

        total_commits = len(commits_info)
        signed_commits = sum(1 for c in commits_info if c['signed'])

        # 作者级别签名统计
        author_stats = defaultdict(lambda: {"total": 0, "signed": 0})
        for commit in commits_info:
            key = f"{commit['author_name']} <{commit['author_email']}>"
            author_stats[key]["total"] += 1
            if commit["signed"]:
                author_stats[key]["signed"] += 1

        # 打印基础信息
        # for commit in commits_info:
        #     print(f"{commit['commit'][:7]} by {commit['author_name']} <{commit['author_email']}> "
        #           f"{'✅ 有签名' if commit['signed'] else '❌ 无签名'}")
        #
        # print(f"\n📊 仓库提交统计（{total_commits} 提交）:")
        # print(f"  🔐 有签名提交数: {signed_commits}")
        # print(f"  ✅ 是否全签: {'是' if signed_commits == total_commits else '否'}")
        #
        # print("\n📊 作者级别签名统计：")
        author_stats_json = {}
        for author, stats in author_stats.items():
            all_signed = stats["signed"] == stats["total"]
            author_stats_json[author] = {
                "total": stats["total"],
                "signed": stats["signed"],
                "all_signed": all_signed
            }
            # print(f"  👤 {author}: {stats['signed']}/{stats['total']} 已签名 "
            #       f"{'✅ 全签' if all_signed else '❌ 部分未签'}")

        # 返回 JSON 结构
        return os.path.basename(repo_path),{
            "total_commits": total_commits,
            "signed_commits": signed_commits,
            "all_signed": signed_commits == total_commits,
            "author_stats": author_stats_json
        }

    except Exception as e:
        print(f"❌ 仓库读取失败: {e}")
        return os.path.basename(repo_path),{
            "error": str(e)
        }
import csv
import json

def save_repo_jsons_simple(repo_names, repo_jsons, filename="repo_signatures.csv"):
    with open(filename, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["repo_name", "repo_json"])  # 表头

        for name, json_obj in zip(repo_names, repo_jsons):
            writer.writerow([
                name,
                json.dumps(json_obj, ensure_ascii=False)  # 转成字符串
            ])



def main(dir, max_workers=1):
    repo_names = []
    repo_jsons = []

    repo_paths = [
        os.path.join(dir, repo_name)
        for repo_name in os.listdir(dir)
        if os.path.isdir(os.path.join(dir, repo_name)) and os.path.exists(os.path.join(dir, repo_name, ".git"))
    ]

    def task(repo_path):
        return check_repo(repo_path)  # 你已改为返回 (repo_name, repo_json)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(task, path): path for path in repo_paths}

        for future in as_completed(futures):
            try:
                repo_name, repo_json = future.result()
                repo_names.append(repo_name)
                repo_jsons.append(repo_json)
            except Exception as e:
                print(f"❌ 处理失败: {futures[future]} 错误: {e}")

    return repo_names, repo_jsons

def test():
    new_folder_path = r'D:\workspace\test'
    repo_names, repo_jsons = main(new_folder_path)
    print(repo_names)
    print(repo_jsons)



if __name__ == "__main__":
    # test()
    root_dir = "F:/download_space"  # 你的仓库目录

    # 定义根目录和输出结果根目录
    output_dir = f"{root_dir}/commit_history_info/"
    os.makedirs(output_dir, exist_ok=True)  # 如果目录不存在，则创建
    for i in range(3,4):
        new_folder_path = ''
        if i <10:
            new_folder_path = f"{root_dir}/2022-0"+str(i)
        else:
            new_folder_path = f"{root_dir}/2022-" + str(i)

        repo_names ,repo_jsons= main(new_folder_path)
        save_repo_jsons_simple(repo_names, repo_jsons,output_dir+new_folder_path.split("/")[-1]+".csv")
