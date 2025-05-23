from pathlib import Path

from collections import defaultdict

import json

import sqlite3


def init_create_db(db_name):
    # # 连接数据库（自动创建）
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    # 创建一个表
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS kv_data (
                       repo_name TEXT PRIMARY KEY,
                       pypi_info_list TEXT,
                       lack BOOLEAN
                   )
               ''')
    return conn, cursor
    # 用于新数据库创建

def db_insert(conn,cursor,data,db_name = 'kv_data',key_name='repo_name',value_name= 'pypi_info_list',lack = 'lack'):
    # 插入数据
    for k, v in data.items():
        cursor.execute(
            f"INSERT OR REPLACE INTO {db_name} ({key_name}, {value_name},{lack}) VALUES (?, ?, ?)",
            (k,  json.dumps(v[0][0], ensure_ascii=False),v[0][1])
        )
    conn.commit()

def db_search(cursor,key_to_query,db_name = 'kv_data',key_name='layer',value_name= 'pypi_info_list'):
    pypi_info = []
    for key in key_to_query:
        cursor.execute(f"SELECT {value_name} FROM {db_name} WHERE {key_name}=?", (key,))
        result = cursor.fetchone()

        if result:
            value = json.loads(result[0])
            pypi_info.append(value)
            # print("查询结果：", value)
        # else:
            # print("未找到对应 Key")
    pypi_info = sum(pypi_info,[])
    return pypi_info



def get_layers_by_manifest_json(file_path):

    # 读取 JSON 内容
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 提取 "Layers" 内容
    if isinstance(data, list) and 'Layers' in data[0]:
        layers = data[0]['Layers']
        config = data[0]['Config']
        repoTags = data[0]['RepoTags']
        # print("Found Layers:")
        for layer in layers:
            layer = str(layer)
            # print(layer.split('/')[0])
        return [s.split('/')[0] for s in layers] ,config,repoTags
    else:
        # print("No 'Layers' field found.")
        return [],[],[]

def check_lack_layer_and_extract_pypi_info(layers,layer_folder_names,conn_pypi,cursor_pypi):
    lack_layer = []
    for layer in layers:
        if layer not in layer_folder_names:
            lack_layer.append(layer)

    pypi_info = db_search(cursor_pypi,layers)

    return lack_layer,pypi_info




def iterate_layers(dir, cache_file='layers_cache_first_data.json'):
    cache_path = Path(cache_file)

    # 如果缓存文件存在，直接加载返回
    if cache_path.exists():
        with open(cache_path, 'r', encoding='utf-8') as f:
            print(f"从缓存中读取层信息：{cache_file}")
            return set(json.load(f))

    # 否则重新遍历文件夹并记录
    root_path = Path(dir)
    folder_names = set()

    for subfolder in root_path.iterdir():
        if subfolder.is_dir():
            folder_names.add(subfolder.name)

    # 写入缓存文件
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(list(folder_names), f, ensure_ascii=False, indent=4)
        print(f"已保存层信息到缓存：{cache_file}")

    return folder_names

def iterate_manifest(dir,folder_names):
    folder_path = Path(dir)  # 替换为你的文件夹路径
    json_files = list(folder_path.glob('*.json'))  # 只匹配当前文件夹的 .json 文件
    # 如果要包含子文件夹中的 json 文件
    # json_files = list(folder_path.rglob('*.json'))
    count = 0
    index_lack = 0
    index_complete = 0
    for file in json_files:
        count += 1
        if count % 1000 == 0:
            print(count)
        file_path = str(file)
        layers,config,repotag = get_layers_by_manifest_json(file_path)
        lack_layer,pypi_info = check_lack_layer_and_extract_pypi_info(layers, folder_names)
        if len(lack_layer) != 0 :
            index_lack += 1
            # print(file.name)
            data = [{
                "Config": config,
                "RepoTags": repotag,
                "Layers": lack_layer
            }]
            with open(f'lackLayersRepo/{file.name}', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        else:
            index_complete += 1
    print(f'Complete:{index_complete}')
    print(f'lack:{index_lack}')

def iterate_layers_db(db_file,db_name = 'kv_data',key_name='layer',value_name= 'pypi_info_list'):
    conn = sqlite3.connect(db_file)
    cursor= conn.cursor()
    # 选出所有的
    cursor.execute(f"SELECT {key_name} FROM {db_name}")
    result =  cursor.fetchall()
    result = [row[0] for row in result]
    print(len(result))

    return result,conn,cursor

def iterate_manifest_db(dir,folder_names,db_file,conn_pypi,cursor_pypi):
    # 初始化
    conn_repo,cursor_repo = init_create_db(db_file)
    package_dict_tmp = defaultdict(list)

    folder_path = Path(dir)  # 替换为你的文件夹路径
    json_files = list(folder_path.glob('*.json'))  # 只匹配当前文件夹的 .json 文件
    # 如果要包含子文件夹中的 json 文件
    # json_files = list(folder_path.rglob('*.json'))
    count = 0
    index_lack = 0
    index_complete = 0
    for file in json_files:
        count += 1
        if count % 1000 == 0:
            print(f"{count}: Complte:{index_complete}-----Incomplte:{index_lack}")
            # 插入并提交
            db_insert(conn_repo,cursor_repo, package_dict_tmp)
            # 将tmp清除
            package_dict_tmp.clear()


        file_path = str(file)
        layers, config, repotag = get_layers_by_manifest_json(file_path)
        lack_layer,pypi_info = check_lack_layer_and_extract_pypi_info(layers, folder_names,conn_pypi, cursor_pypi)
        # 如果缺失
        if len(lack_layer) != 0 :
            ### 记录到manifest中 ###
            index_lack += 1
            # print(file.name)
            data = [{
                "Config": config,
                "RepoTags": repotag,
                "Layers": lack_layer
            }]
            with open(f'Z:/hf-images1/lackLayersRepo/{file.name}', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            ### 记录到db ###
            package_dict_tmp[file.name.split('.')[0]].append([pypi_info,True])
        else:
            package_dict_tmp[file.name.split('.')[0]].append([pypi_info,False])
            # 如果全，
            index_complete += 1

    db_insert(conn_repo, cursor_repo, package_dict_tmp)
    # 将tmp清除
    package_dict_tmp.clear()

    print(f'Complete:{index_complete}')
    print(f'lack:{index_lack}')



if __name__ == '__main__':
    # layer folder 的路径
    base_path= 'Z:/hf-images1'
    # 获取所有的layer folder 的名称
    # folder_names = iterate_layers(f'{base_path}/layers')
    folder_names,conn_pypi,cursor_pypi = iterate_layers_db('kv_all_layer_pypi.db')
    iterate_manifest_db(f'{base_path}/images-r8',folder_names,'repo_pypi.db',conn_pypi,cursor_pypi)





