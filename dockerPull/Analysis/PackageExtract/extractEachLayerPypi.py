from pathlib import Path

from analysisUtils import extract_Pypi,check_pypi_info,sqlite3_init,sqlite3_insert,sqlite3_connect

from collections import defaultdict


import json

import sqlite3

from dockerPull.Analysis.PackageExtract.analysisUtils import sqlit3_fetch_all


# 将set变成dict用于统计,同时包含了去重的作用
def to_dict(all_packages):
    package_dict = defaultdict(list)

    for pkg in all_packages:
        pkg_clean = pkg.replace('.wh.', '')
        name, version = pkg_clean.rsplit('-', 1)
        package_dict[name].append(version)
    return package_dict


def save_to_json(package_dict,output_file_name):
    # 假设你的字典是 final_package_dict
    # 保存到 JSON 文件
    with open(f'{output_file_name}.json', 'w', encoding='utf-8') as f:
        json.dump(package_dict, f, ensure_ascii=False, indent=4)

def iterate_layers(dir,sqlit_conn,sqlit_cursor):
    root_path = Path(dir)
    all_packages = set()
    package_dict_tmp = defaultdict(list)

    count = 0
    # 遍历layers
    for subfolder in root_path.iterdir():
        if subfolder.is_dir():
            count += 1
            tree_file = subfolder / 'tree.txt'
            if tree_file.is_file():
                # 以二进制方式读取
                with open(tree_file, 'rb') as f:
                    # 这里content_bytes就是tree.txt的全部内容，类型是bytes
                    content_bytes = f.read()
                    # 如果这个包中包含的话，
                    if check_pypi_info(content_bytes):
                        package_versions = extract_Pypi(content_bytes)
                        all_packages.update(package_versions)
                        # 找到对应层的名字，将名字存入到临时的dict当中
                        layer_name = subfolder.name
                        package_dict_tmp[layer_name] = package_versions

                    if count % 1000 == 0:
                        print(count)
                        # 插入并提交
                        sqlite3_insert(sqlit_conn, sqlit_cursor, package_dict_tmp)
                        # 将tmp清除
                        package_dict_tmp.clear()
    # print(all_packages)

    # ######最后的处理阶段############
    # 最后一次的将剩余的Pypi信息插入到数据库中并提交
    sqlite3_insert(sqlit_conn, sqlit_cursor, package_dict_tmp)
    # 将tmp清除
    package_dict_tmp.clear()


    # 传出去用于记录查重的Package信息
    package_dict = to_dict(all_packages)
    return package_dict




if __name__ == '__main__':
    # # 初始化数据库
    # conn,cursor = sqlite3_init('kv_layer_pypi.db')
    # layers_dir = 'Z:/hf-images1/layers'   #更换为真实路径
    # # 获取所有Pypi包信息，同时将每一个layer的信息存到SQlite当中
    # package_dict = iterate_layers(layers_dir,conn,cursor)
    # # 记录至Json
    # save_to_json(package_dict,'first_data_pypi_info')
    #
    # conn.close()

    conn , cursor= sqlite3_connect('kv_layer_pypi.db')
    result = sqlit3_fetch_all(cursor)
    print(result)


















