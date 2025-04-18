import io
import zipfile
from pathlib import Path
from collections import defaultdict
import zipfile
import shutil
import os

from dockerPull.Analysis.analysisUtils import recursive_extract

TMP_DIR = Path("tmp")
TMP_DIR.mkdir(exist_ok=True)

# 上一个版本,忽略
# def my_uzip(zip_file_path):
#     """
#     打开一个ZIP压缩包，定位其中与压缩包同名的一级目录（常见于自动压缩生成），
#     并提取该目录下的直接子文件和子文件夹（不递归），将其分类保存。
#
#     参数：
#         zip_file_path (str): ZIP文件的路径。
#
#     返回：
#         tuple:
#             - zip_ref (zipfile.ZipFile): 已打开的ZIP文件对象，可用于后续读取内容。
#             - folders (list): 该一级目录下的文件夹列表（以 `/` 结尾）。
#             - files (list): 该一级目录下的文件列表。
#     """
#
#     # 打开ZIP文件
#     zip_ref = zipfile.ZipFile(zip_file_path, 'r')
#     file_list = zip_ref.namelist()  # 获取压缩包内的所有文件路径
#
#     # 筛选出manifest.json
#     json_files = [s for s in file_list if s.endswith('.json')]
#
#
#     # 筛选出包含两个 '/' 字符且第二个 '/' 后面还有字符的字符串，且排除__MACOSX
#     img_file = [s for s in file_list if s.count('/') == 2 and len(s.split('/', 2)[-1]) > 0 and not s.startswith('__MACOSX')]
#
#
#     # 创建一个默认字典来保存归类结果,这个东西的key就是fs_layer的名字，value就是文件夹下对应的文件
#     fs_groups = defaultdict(list)
#
#     # 遍历文件路径，按第二个 '/' 后的子字符串进行归类
#     for path in img_file:
#         # 获取第二个 '/' 后的子字符串
#         key = path.split('/')[1]  # 第二个 '/' 后的部分
#         fs_groups[key].append(path)
#
#     # 输出归类结果
#     for key, files in fs_groups.items():
#         print(f"Group: {key}")
#         for file in files:
#             print(f"  {file}")
#
#     # 返回ZIP对象和分类后的文件夹、文件列表
#     return zip_ref, fs_groups,json_files

# 上一版本,先忽略

# def process_tree_txt(zip_ref, fs_groups):
#     for key in fs_groups:
#         # 取对应的file
#         files = fs_groups[key]
#         for file in files:
#             if file.endswith('.txt'):
#                 content = zip_ref.read(file)
#                 # print(f"\n🎯 {specific_file} 的内容：")
#                 print(content.decode('utf-8'))
#     return 0
#
#     # specific_file = 'sundas-tamimi-updated-image-text-audio/e38042d6b4eec9c7b84ef9072047ac1494a16fa52ca731375c7fcb8a5ced25ce/tree.txt'
#     # content = zip_ref.read(specific_file)
#     # print(f"\n🎯 {specific_file} 的内容：")
#     # print(content.decode('utf-8'))

# 该函数用于将目标gz文件中的内容解压到output_dir


def extract_gz_file_to_tmp(zip_ref,file_name,output_dir):
    print(f"[*] Found .gz file: {file_name}")
    gz_bytes = io.BytesIO(zip_ref.read(file_name))
    recursive_extract(gz_bytes, file_name, output_dir)

# 该函数解压第一层zip包
def extract_gz_from_zip(zip_path):
    """
    解析一个 ZIP 压缩包中的内容，查找其中的 .json 文件和嵌套结构中 .gz 文件对应的路径，进行分类处理。

    具体功能如下：
    1. 打开指定路径的 ZIP 文件，读取其中所有文件路径。
    2. 从文件列表中筛选出所有以 .json 结尾的文件（通常用于 manifest 文件记录）。
    3. 筛选出路径中包含两个 '/' 且第二个 '/' 后仍有子路径的文件（即位于某层子目录下的实际文件），同时排除路径以 '__MACOSX' 开头的系统生成文件。
    4. 将上述筛选得到的文件路径，根据其属于的 FS layer 文件夹进行归类（以路径中的第二段作为分组键）。
    5. 打印归类后的结果，方便调试或进一步处理。
    6. 返回打开的 ZIP 文件对象、分组后的文件字典（键为 layer 名称，值为该层下的文件列表）、以及所有 .json 文件路径列表。

    参数：
        zip_path (str): ZIP 压缩文件的路径。

    返回：
        tuple:
            - zip_ref (zipfile.ZipFile): 打开的 ZIP 文件对象，可用于后续读取实际文件内容。
            - fs_groups (defaultdict[list]): 按 layer 名称归类的嵌套文件路径字典，便于后续解压与分析。
            - json_files (list[str]): 所有以 .json 结尾的文件路径列表（通常为 manifest 文件）。
    """
    # with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref = zipfile.ZipFile(zip_path, 'r')
    file_list = zip_ref.namelist()  # 获取压缩包内的所有文件路径

    # 筛选出manifest.json
    json_files = [s for s in file_list if s.endswith('.json')]

    # 筛选出包含两个 '/' 字符且第二个 '/' 后面还有字符的字符串，且排除__MACOSX
    img_file = [s for s in file_list if
                s.count('/') == 2 and len(s.split('/', 2)[-1]) > 0 and not s.startswith('__MACOSX')]

    print(json_files)
    print(img_file)
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
    return zip_ref, fs_groups, json_files


if __name__ == "__main__":
    # 一些代码使用示例
    # ###############

    #获取zip_ref对象
    zip_ref, fs_groups, json_files = extract_gz_from_zip("testdata/kemalpm-openai-whisper-large-v3.zip")

    # 可以从fs_groups中遍历看有什么tree.txt以及text.tar.gz
    for key in fs_groups:
        # 取对应的file
        files = fs_groups[key]
        for file in files:
            # 这个一般是用于查看tree.txt的内容
            if file.endswith('.txt'):
                content = zip_ref.read(file)
                # print(f"\n🎯 {specific_file} 的内容：")
                # print(content.decode('utf-8'))

    # 在上面的代码中,如果你根据tree找到了对应的文件的话,可以用下面的代码去解压包,以下为示例:
    target_unzip_file_name = 'kemalpm-openai-whisper-large-v3/4b72ad191495c4439dee3c85898d50b1ae12291e1f313189b02dc3ae4aa29878/text.tar.gz'

    extract_gz_file_to_tmp(zip_ref, target_unzip_file_name, TMP_DIR)

    print(1)




    # zip_ref, fs_groups, json_files = my_uzip('testdata/sundas-tamimi-updated-image-text-audio.zip')
    #
    #
    # process_tree_txt(zip_ref, fs_groups)
    #
    # zip_ref.close()








