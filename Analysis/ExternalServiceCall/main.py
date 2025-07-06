import os
import ast
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

http_libraries = {"requests", "httpx", "urllib", "aiohttp", "http"}
http_methods = {"get", "post", "put", "delete", "head", "options", "patch", "request"}

def is_local_url(url):
    if not isinstance(url, str):
        return False
    local_patterns = [
        r"^http://localhost",
        r"^http://127\.",
        r"^http://0\.0\.0\.0",
        r"^http://\[::1\]",
    ]
    return any(re.match(pat, url) for pat in local_patterns)

def extract_http_calls_from_file(file_path):
    calls = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
                if func_name in http_methods:
                    if isinstance(node.func.value, ast.Name) and node.func.value.id in http_libraries:
                        for arg in node.args:
                            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                url = arg.value.strip()
                                if not is_local_url(url):
                                    calls.add(url)
                            elif isinstance(arg, ast.Str):
                                url = arg.s.strip()
                                if not is_local_url(url):
                                    calls.add(url)
    except Exception as e:
        print(f"[WARN] Failed to parse {file_path}: {e}")
    return calls

def analyze_one_repo(repo_path):
    repo_name = os.path.basename(repo_path)
    all_calls = set()
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                calls = extract_http_calls_from_file(file_path)
                all_calls.update(calls)
    return repo_name, sorted(all_calls) if all_calls else None

def analyze_month_folder(month_folder, output_dir, max_workers=8):
    all_repos = [
        os.path.join(month_folder, repo)
        for repo in os.listdir(month_folder)
        if os.path.isdir(os.path.join(month_folder, repo))
    ]

    result = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(analyze_one_repo, repo_path): repo_path for repo_path in all_repos}

        for future in as_completed(futures):
            repo_path = futures[future]
            try:
                repo_name, urls = future.result()
                if urls:
                    result[repo_name] = urls
            except Exception as exc:
                print(f"[X] Error in repo {repo_path}: {exc}")

    if result:
        month = os.path.basename(month_folder)
        output_path = os.path.join(output_dir, f"{month}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"[✓] Saved: {month} ({len(result)} repos with HTTP calls)")


if __name__ == "__main__":
    base_dir = "F:/download_space"
    output_dir = os.path.join(base_dir, "http_call")
    os.makedirs(output_dir, exist_ok=True)

    for i in range(1, 13):
        month_folder = f"{base_dir}/2023-{'0'+str(i) if i < 10 else str(i)}"
        if os.path.exists(month_folder):
            analyze_month_folder(month_folder, output_dir, max_workers=12)
