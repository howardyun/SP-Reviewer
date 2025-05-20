import requests
import json

def get_pypi_info(package_name):

    url = f"https://pypi.org/pypi/{package_name}/json"

    response = requests.get(url)
    data = response.json()

    print("描述：",data['info']['description'])
    print("github url",data['info']['project_urls'])
    print("版本：", data['info']['version'])
    print("简介：", data['info']['summary'])
    print("作者：", data['info']['author'])
    print("上传时间：", data['releases'][data['info']['version']][0]['upload_time'])
    return data['info']
#
# def get_pypi_dependency_graph(package_names):








if __name__ == "__main__":
    json_data_url = "../../../Data/JSON/first_data_pypi_info.json"

    with open(json_data_url, "r", encoding="utf-8") as f:
        data = json.load(f)
    pypi_package_list = list(data.keys())
    for package_name in pypi_package_list:
        package_info = get_pypi_info(package_name)
