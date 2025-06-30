import json
import time

import requests
import tqdm

a = []


def check_github_repos(json_file_path, github_token=None):
    # Read repository names from JSON file
    try:
        with open(json_file_path, 'r') as file:
            repo_list = json.load(file)
    except FileNotFoundError:
        print(f"Error: File {json_file_path} not found")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_file_path}")
        return

    # Set up headers for GitHub API
    headers = {}
    if github_token:
        headers['Authorization'] = f'Bearer {github_token}'
    i = 1
    # Check each repository
    for repo_name in tqdm.tqdm(repo_list):
        # Assuming repositories are under a specific owner, e.g., 'owner/repo_name'
        # Modify the owner as needed or make it configurable
        repo_url = f"https://api.github.com/search/repositories?q={repo_name}&per_page=2"

        try:
            response = requests.get(repo_url, headers=headers)

            if response.status_code == 200:
                if response.json()['total_count'] == 0:
                    a.append(repo_name)
                    print(f"Repository '{repo_name}' does not exist")
                if response.json()['total_count'] > 0 and response.json()['items'][0]["name"] != repo_name:
                    a.append(repo_name)
                    print(f"Repository '{repo_name}' does not exists")
                if response.json()['total_count'] > 0 and response.json()['items'][0]["name"] == repo_name:
                    print(f"Repository '{repo_name}' exists")
                i = 1 + i
            print(f"{i}: {repo_name}")
            if i % 30 == 0:
                i = 1
                time.sleep(30)

        except requests.RequestException as e:
            print(e)
            a.append(repo_name)
            time.sleep(60)



# Example usage
if __name__ == "__main__":
    # Path to your JSON file
    json_file = "dangling.json"

    # Optional: Add your GitHub token for authenticated requests (higher rate limit)
    github_token = "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"  # Replace with your token if needed

    check_github_repos(json_file, github_token)

    print(a)

    with open("dangling_github_check.json", 'w', encoding='utf-8') as f:
        json.dump(a, f)

