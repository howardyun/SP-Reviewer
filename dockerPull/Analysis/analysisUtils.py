import zipfile
import tarfile
import gzip
import shutil
import io
import os
import re
from pathlib import Path



# 该函数用于解压单个.gz文件，通常用于对fs layer里面对于text.gz.tar文件进行提取，提取路径:tmp_output
def recursive_extract(file_like, filename_hint,tmp_output):
    """
       递归解压任意嵌套层级的压缩文件内容，并将最终的非压缩文件保存至指定目录（tmp_output）。

       支持的压缩格式包括：
           - tar (.tar, .tar.gz, .tgz 等)
           - zip (.zip)
           - gzip (.gz)，包括单文件 GZIP 压缩（.gz 包裹非压缩文件）

       该函数能够识别嵌套的压缩包（即压缩包内还有压缩包），并层层解包直到提取出最终的文件。

       参数：
           file_like (io.BytesIO 或类似文件对象): 当前处理的压缩包文件内容。
           filename_hint (str): 文件名提示，用于辅助判断文件类型（如是否以 .gz 结尾）。
           tmp_output (Path): 用于存储最终解压出文件的目标文件夹（通常是 tmp 路径）。

       函数逻辑：
           1. 首先尝试将 file_like 作为 tar 文件打开，若成功则遍历每个成员文件，递归处理其中内容。
           2. 若不是 tar，再尝试将 file_like 当作 zip 文件处理，并递归处理其中条目。
           3. 若文件名后缀为 .gz，则尝试解压为单个文件后递归处理。
           4. 若上述格式都不匹配，说明是普通文件，直接保存到 tmp_output 目录中。

       输出：
           将所有解压后的文件统一保存到 tmp_output 目录下，并输出每个保存的文件路径。

       注意事项：
           - 每次递归处理时会重置 file_like 的文件指针（seek(0)）。
           - 不支持 7z、rar 等非标准格式，需使用其他工具先转换。
           - 保存的文件名为最内层文件的 basename，可能在不同目录中存在重复，需根据实际情况改进命名。
       """
    # 1. 判断是否为 tar
    try:
        file_like.seek(0)
        with tarfile.open(fileobj=file_like, mode="r:*") as tar:
            for member in tar.getmembers():
                if member.isfile():
                    extracted = tar.extractfile(member)
                    if extracted:
                        inner_bytes = io.BytesIO(extracted.read())
                        recursive_extract(inner_bytes, member.name,tmp_output)
            return
    except tarfile.ReadError:
        pass

    # 2. 判断是否为 zip
    try:
        file_like.seek(0)
        with zipfile.ZipFile(file_like) as zf:
            for name in zf.namelist():
                with zf.open(name) as inner_file:
                    inner_bytes = io.BytesIO(inner_file.read())
                    recursive_extract(inner_bytes, name,tmp_output)
            return
    except zipfile.BadZipFile:
        pass

    # 3. 判断是否为 gzip
    if filename_hint.endswith(".gz"):
        file_like.seek(0)
        with gzip.open(file_like, 'rb') as gz_file:
            decompressed_bytes = gz_file.read()
            filename_no_gz = filename_hint[:-3]
            recursive_extract(io.BytesIO(decompressed_bytes), filename_no_gz,tmp_output)
        return

    # 4. 不是压缩包，保存到 tmp 文件夹
    save_path = tmp_output / os.path.basename(filename_hint)
    file_like.seek(0)
    with open(save_path, 'wb') as f_out:
        shutil.copyfileobj(file_like, f_out)
    print(f"[+] Extracted: {save_path}")

# 该函数用于删除一个文件夹以及所有其中所有的内容
def delete_folder_recursive(folder_path):
    """
    删除指定文件夹及其内部所有文件和子文件夹。

    参数：
        folder_path (str): 要删除的文件夹的完整路径。

    功能说明：
        - 如果路径存在且是一个文件夹，则递归删除其所有内容；
        - 若文件夹不存在，则打印提示信息；
        - 使用 shutil.rmtree 进行彻底删除。

    示例：
        delete_folder_recursive("/tmp/extracted_files")

    注意事项：
        - 请确保传入的是正确的目标路径，删除操作不可恢复。
    """
    if os.path.exists(folder_path):
        if os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
            print(f"[✓] 成功删除文件夹：{folder_path}")
        else:
            print(f"[!] 路径存在但不是文件夹：{folder_path}")
    else:
        print(f"[!] 文件夹不存在：{folder_path}")


def check_pypi_info(content_bytes):
    """检查一个 txt 文件内容中是否包含 PyPI 包信息"""
    try:
        text = content_bytes.decode('utf-8')
    except UnicodeDecodeError:
        # 如果解码失败，可以忽略这个文件
        return False

    # 用正则找 site-packages/xxx-xxx.dist-info 这样的东西
    matches = re.findall(r'site-packages/[^/]+-\d+(?:\.\d+)*?\.dist-info', text)

    return len(matches) > 0  # 至少有一个匹配，就返回 True

def extract_Pypi(content):
    text = content.decode('utf-8')  # 这里通常是 utf-8，如果是别的编码（如gbk）需要调整

    # 第二步：用正则提取 包名-版本号
    package_versions = re.findall(r'site-packages/([A-Za-z0-9_\-\.]+-\d+(?:\.\d+)*?)\.dist-info', text)

    # 第三步：去重 + 排序
    package_versions = sorted(set(package_versions))

    # 第四步：输出或保存
    # for pv in package_versions:
    #     print(pv)
    return package_versions




#
#
# # 示例调用
# extract_gz_from_zip("testdata/sundas-tamimi-updated-image-text-audio.zip")
