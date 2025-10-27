import os
import csv
import json
from collections import defaultdict

import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed


def parse_git_log_output(output):
    commits = []
    sections = output.split("===COMMIT===")
    for section in sections:
        lines = section.strip().splitlines()
        if not lines:
            continue

        commit_hash = lines[0].strip()
        author_name = None
        author_email = None
        for i in range(1, len(lines)):
            if not lines[i].startswith("gpg:"):
                if author_name is None:
                    author_name = lines[i].strip()
                elif author_email is None:
                    author_email = lines[i].strip()
                    signature_block = "\n".join(lines[i+1:])
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


def ensure_git_safe_directory(repo_path):

    try:
        subprocess.run(
            ["git", "config", "--global", "--unset-all", "safe.directory"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        subprocess.run(
            ["git", "config", "--global", "--add", "safe.directory",
             repo_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )
    except subprocess.CalledProcessError as e:
        print(f"⚠️ 添加 safe.directory 失败: {e.stderr.strip()}")

def check_repo(repo_path):
    print(f"\n==== 检查仓库：{os.path.basename(repo_path)} ====")
    # repo_path = os.path.abspath(repo_path).replace("\\", "/")
    print(repo_path)
    # subprocess.run(
    #     ["git", "config", "--global", "--add", "safe.directory",
    #      repo_path],
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE,
    #     text=True,
    #     encoding="utf-8"
    # )
    # ensure_git_safe_directory(repo_path)
    try:
        # result = subprocess.run(
        #     [
        #         "git", "log",
        #         "--reverse",
        #         "--pretty=format:===COMMIT===%n%H%n%an%n%ae",
        #         "--show-signature"
        #     ],
        #     cwd=repo_path,
        #     stdout=subprocess.PIPE,
        #     stderr=subprocess.PIPE,
        #     text=True,
        #     timeout=180,
        #     env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        # )
        result = subprocess.run(
            ["git", "-c", "safe.directory=*", "log", "--reverse", "--pretty=format:===COMMIT===%n%H%n%an%n%ae",
             "--show-signature"],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=180,
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())

        output = result.stdout
        commits_info = parse_git_log_output(output)

        total_commits = len(commits_info)
        if total_commits == 0:
            print('Pause')
        else:
            print(total_commits)
        signed_commits = sum(1 for c in commits_info if c['signed'])

        author_stats = defaultdict(lambda: {"total": 0, "signed": 0})
        for commit in commits_info:
            key = f"{commit['author_name']} <{commit['author_email']}>"
            author_stats[key]["total"] += 1
            if commit["signed"]:
                author_stats[key]["signed"] += 1

        author_stats_json = {}
        for author, stats in author_stats.items():
            all_signed = stats["signed"] == stats["total"]
            author_stats_json[author] = {
                "total": stats["total"],
                "signed": stats["signed"],
                "all_signed": all_signed
            }

        return os.path.basename(repo_path), {
            "total_commits": total_commits,
            "signed_commits": signed_commits,
            "all_signed": signed_commits == total_commits,
            "author_stats": author_stats_json
        }

    except Exception as e:
        print(f"❌ 仓库读取失败: {e}")
        return os.path.basename(repo_path), {"error": str(e)}


def save_repo_jsons_simple(repo_names, repo_jsons, filename="repo_signatures.csv"):
    with open(filename, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["repo_name", "repo_json"])
        for name, json_obj in zip(repo_names, repo_jsons):
            writer.writerow([name, json.dumps(json_obj, ensure_ascii=False)])


def main(dir, max_workers=8):
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
    root_dir = "Z:/download_space"
    output_dir = f"{root_dir}/commit_history_info/"
    os.makedirs(output_dir, exist_ok=True) 
    for i in range(1,6):
        new_folder_path = f"{root_dir}/2025-{i:02d}"
        repo_names, repo_jsons = main(new_folder_path)
        output_path = os.path.join(output_dir, f"{new_folder_path.split('/')[-1]}.csv")
        save_repo_jsons_simple(repo_names, repo_jsons, output_path)
