import requests
import json

package_name = "requests"
url = f"https://pypi.org/pypi/{package_name}/json"

response = requests.get(url)
data = response.json()

print(json.dumps(data))
print(data['info'])
# 查看基本信息

print("描述：",data['info']['description'])
print("github url",data['info']['project_urls']['Source'])
print("版本：", data['info']['version'])
print("简介：", data['info']['summary'])
print("作者：", data['info']['author'])
print("上传时间：", data['releases'][data['info']['version']][0]['upload_time'])
