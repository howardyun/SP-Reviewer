import zipfile
import os
from collections import defaultdict


def my_uzip(zip_file_path):
    """
    打开一个ZIP压缩包，定位其中与压缩包同名的一级目录（常见于自动压缩生成），
    并提取该目录下的直接子文件和子文件夹（不递归），将其分类保存。

    参数：
        zip_file_path (str): ZIP文件的路径。

    返回：
        tuple:
            - zip_ref (zipfile.ZipFile): 已打开的ZIP文件对象，可用于后续读取内容。
            - folders (list): 该一级目录下的文件夹列表（以 `/` 结尾）。
            - files (list): 该一级目录下的文件列表。
    """

    # 打开ZIP文件
    zip_ref = zipfile.ZipFile(zip_file_path, 'r')
    file_list = zip_ref.namelist()  # 获取压缩包内的所有文件路径

    # 筛选出manifest.json
    json_files = [s for s in file_list if s.endswith('.json')]


    # 筛选出包含两个 '/' 字符且第二个 '/' 后面还有字符的字符串，且排除__MACOSX
    img_file = [s for s in file_list if s.count('/') == 2 and len(s.split('/', 2)[-1]) > 0 and not s.startswith('__MACOSX')]


    # 创建一个默认字典来保存归类结果,这个东西的key就是fs_layer的名字，value就是文件夹下对应的文件
    fs_groups = defaultdict(list)

    # 遍历文件路径，按第二个 '/' 后的子字符串进行归类
    for path in img_file:
        # 获取第二个 '/' 后的子字符串
        key = path.split('/')[1]  # 第二个 '/' 后的部分
        fs_groups[key].append(path)

    # 输出归类结果
    for key, files in fs_groups.items():
        print(f"Group: {key}")
        for file in files:
            print(f"  {file}")

    # 返回ZIP对象和分类后的文件夹、文件列表
    return zip_ref, fs_groups,json_files

def process_tree_txt(zip_ref, fs_groups):
    for key in fs_groups:
        # 取对应的file
        files = fs_groups[key]
        for file in files:
            if file.endswith('.txt'):
                content = zip_ref.read(file)
                # print(f"\n🎯 {specific_file} 的内容：")
                print(content.decode('utf-8'))
    return 0

    # specific_file = 'sundas-tamimi-updated-image-text-audio/e38042d6b4eec9c7b84ef9072047ac1494a16fa52ca731375c7fcb8a5ced25ce/tree.txt'
    # content = zip_ref.read(specific_file)
    # print(f"\n🎯 {specific_file} 的内容：")
    # print(content.decode('utf-8'))

zip_ref, fs_groups, json_files = my_uzip('testdata/sundas-tamimi-updated-image-text-audio.zip')


process_tree_txt(zip_ref, fs_groups)

zip_ref.close()







