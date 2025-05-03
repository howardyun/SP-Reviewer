import json
import time
from collections import Counter

import requests


def get_pypi_classifiers(pkg, topic_only=True, sleep_time=0.5):
    """
    查询 PyPI 包的分类标签（Trove Classifiers）

    参数:
        package_list (list): 要查询的 PyPI 包名列表
        topic_only (bool): 是否仅保留 Topic:: 开头的功能性标签
        sleep_time (float): 每次请求后的间隔时间（避免频繁访问被封IP）

    返回:
        results (list of dict): 每个包的包名、版本、分类标签列表
    """
    results = []

    url = f"https://pypi.org/pypi/{pkg}/json"
    try:
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"❌ Failed to fetch {pkg}")
            return None

        data = resp.json()
        version = data["info"]["version"]
        classifiers = data["info"].get("classifiers", [])

        if topic_only:
            classifiers = [c for c in classifiers if c.startswith("Topic")]

        results.append({
            "package": pkg,
            "version": version,
            "classifiers": classifiers
        })

        time.sleep(sleep_time)

    except Exception as e:
        print(f"⚠️ Error processing {pkg}: {e}")
        return None
    return results



def get_latest_upload_date(pkg_name):
    url = f"https://pypi.org/pypi/{pkg_name}/json"
    resp = requests.get(url)
    data = resp.json()
    latest_version = data["info"]["version"]
    return data["releases"][latest_version][0]["upload_time"]


with open("package_info_data/packages_info_1.json") as f:
    data = json.load(f)

package_version_counts = {pkg: len(versions) for pkg, versions in data.items()}

print(package_version_counts)
for package_name, versions in package_version_counts.items():
        upload_date = get_latest_upload_date(package_name)
        classifiers = get_pypi_classifiers(package_name)
        print(f"{classifiers}")
        print(upload_date)