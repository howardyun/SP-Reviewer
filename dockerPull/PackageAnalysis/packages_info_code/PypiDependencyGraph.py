import requests
import json
import networkx as nx
from pyvis.network import Network

# 获取包的依赖列表
def get_dependencies(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        response = requests.get(url)
        data = response.json()
        requires_dist = data["info"].get("requires_dist", [])
        dependencies = []

        for item in requires_dist:
            dep = item.split(";")[0].strip()  # 去掉环境标记
            if dep:
                dep_name = dep.split()[0]  # 去掉版本约束
                dependencies.append(dep_name)
        return dependencies
    except Exception as e:
        print(f"Failed to fetch {package_name}: {e}")
        return []

# 构建图
def build_dependency_graph(package_list):
    G = nx.DiGraph()
    for package in package_list:
        G.add_node(package)
        dependencies = get_dependencies(package)
        for dep in dependencies:
            G.add_node(dep)
            G.add_edge(package, dep)  # 有向边：package -> dep
    return G

# 可视化图谱
def visualize_graph(G, output_file="dependency_graph.html"):
    net = Network(height="750px", width="100%", directed=True, notebook=False)
    net.from_nx(G)
    net.show_buttons(filter_=['physics'])
    net.write_html(output_file)
    print(f"✅ 可视化图已生成：{output_file}")


if __name__ == "__main__":
    json_data_url = "../../../Data/JSON/first_data_pypi_info.json"

    with open(json_data_url, "r", encoding="utf-8") as f:
        data = json.load(f)
    pypi_package_list = list(data.keys())
    # 输入你要分析的包名

    graph = build_dependency_graph(pypi_package_list)
    visualize_graph(graph)
