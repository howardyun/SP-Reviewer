import subprocess
import oss2
import stat
import os
import sys
import gzip
import json
import hashlib
import shutil
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import tarfile
import urllib3

os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'


urllib3.disable_warnings()

access_key_id = "LTAI5tLnzCKqzC9TAsjRGQuh"
access_key_secret = "kUpakWCNXpVqWOsRLRejmWrUoPxz5q"
endpoint = "oss-accelerate.aliyuncs.com"

oss_auth = oss2.Auth(access_key_id, access_key_secret)
src_bucket = oss2.Bucket(oss_auth, endpoint, "ysxtestbucket")


# File extensions for text files
TEXT_EXTENSIONS = [
    '.txt', '.md', '.csv', '.json', '.xml', '.yaml', '.yml', '.html', '.htm',
    '.css', '.js', '.ts', '.py', '.c', '.cpp', '.h', '.hpp', '.java', '.sh',
    '.bash', '.conf', '.cfg', '.ini', '.log', '.sql', '.toml',
    '.jsx', '.tsx', '.vue', '.rb', '.pl', '.php', '.go', '.rs', '.scala', '.dart',
    '.proto', '.diff', '.patch', '.rst', '.tex', '.bib', '.markdown', '.gitignore',
    '.properties', '.gradle', '.bat', '.ps1', '.vbs', '.cs', '.csproj', '.sln'
]
def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Check if proxy environment variables are set
    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')

    if http_proxy or https_proxy:
        session.proxies = {
            'http': http_proxy,
            'https': https_proxy
        }
        print('[+] Using proxy settings from environment')

    return session


def count_files_larger_than_size(folder_path, min_size=10, size_unit='B'):
    """递归统计文件夹及所有子文件夹中大小超过指定值的文件个数"""
    units = {'B': 1, 'KB': 1024, 'MB': 1024 * 1024, 'GB': 1024 * 1024 * 1024}
    min_bytes = min_size * units.get(size_unit, 1)

    count = 0
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                if os.path.getsize(file_path) > min_bytes:
                    count += 1
            except (OSError, FileNotFoundError):
                pass  # 处理无法访问的文件

    return count


def calculate_hashes(file_path):
    """Calculate MD5 and SHA1 hashes for a file."""
    md5_hash = hashlib.md5()
    sha1_hash = hashlib.sha1()

    with open(file_path, 'rb') as f:
        # Read the file in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b''):
            md5_hash.update(chunk)
            sha1_hash.update(chunk)

    return md5_hash.hexdigest(), sha1_hash.hexdigest()


def is_special_file(file_path):
    """检查文件是否是特殊文件或指向特殊文件的软链接"""
    try:
        # 获取文件状态
        st = os.lstat(file_path)

        # 检查是否是软链接
        if stat.S_ISLNK(st.st_mode):
            # 获取软链接的目标
            target = os.readlink(file_path)

            # 检查目标是否是特殊文件描述符
            if '/dev/fd/' in target or '/proc/self/fd/' in target:
                print(f"跳过特殊文件描述符链接: {file_path} -> {target}")
                return True

            # 如果是相对路径，转换为绝对路径
            if not os.path.isabs(target):
                target = os.path.normpath(os.path.join(os.path.dirname(file_path), target))

            # 防止循环链接导致无限递归
            if target != file_path:
                return is_special_file(target)

        # 检查是否是设备文件、FIFO等
        return (stat.S_ISCHR(st.st_mode) or
                stat.S_ISBLK(st.st_mode) or
                stat.S_ISFIFO(st.st_mode) or
                stat.S_ISSOCK(st.st_mode) or
                file_path.startswith('/dev/') or
                file_path.startswith('/proc/'))

    except Exception as e:
        # print(f"检查文件 {file_path} 时出错: {e}")
        return True  # 如果无法确定，最好跳过


def calc_dir_hash(input_dir, output_file):
    # Set up argument parser
    input_dir = os.path.abspath(input_dir)
    output_file = os.path.abspath(output_file)

    # Ensure input directory exists
    if not os.path.isdir(input_dir):
        print(f"Error: '{input_dir}' is not a valid directory")
        return 1

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Process files and write results
    with open(output_file, 'w') as out_file:
        # Traverse the directory
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                file_path = os.path.join(root, file)

                # Skip the output file if it's in the directory being scanned
                if file_path == output_file:
                    print(f"Skipping output file: {file_path}")
                    continue

                try:
                    # Calculate hashes
                    # print(f"calc hash {file_path}")
                    if not is_special_file(file_path):
                        md5_hash, sha1_hash = calculate_hashes(file_path)
                        # Write to output file
                        out_file.write(f"{file_path} {md5_hash} {sha1_hash}\n")
                except Exception as e:
                    # print(f"Error processing {file_path}: {e}")
                    pass

    print(f"Hash calculations complete. Results written to {output_file}")



def extract_tar(tar_path, destination_path):
    """
    解压 tar 文件到指定目录

    参数:
    tar_path (str): tar 文件的路径
    destination_path (str): 解压目标目录

    返回:
    bool: 解压是否成功
    """
    try:
        # 确保目标目录存在
        os.makedirs(destination_path, exist_ok=True)

        # 打开 tar 文件
        with tarfile.open(tar_path, 'r:*') as tar:
            # 解压所有内容到目标目录
            tar.extractall(path=destination_path)

        return True
    except tarfile.ReadError:
        print(f"错误: {tar_path} 不是有效的 tar 文件或无法读取")
        return False
    except PermissionError:
        print(f"错误: 没有权限写入目标目录 {destination_path}")
        return False
    except Exception as e:
        print(f"解压过程中发生错误: {e}")
        return False


def process_my_dir(inputDir, outDir):
    # Create output directories
    outDir1 = os.path.join(outDir, 'outDir1')
    outDir2 = os.path.join(outDir, 'outDir2')
    outDir3 = os.path.join(outDir, 'outDir3')

    for directory in [outDir, outDir1, outDir2, outDir3]:
        os.makedirs(directory, exist_ok=True)

    for root, dirs, files in os.walk(inputDir):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, inputDir)
            # Check if the file is a text file
            if any(file.lower().endswith(ext) for ext in TEXT_EXTENSIONS):
                dest_path = os.path.join(outDir1, rel_path)
                dest_dir = os.path.dirname(dest_path)
                os.makedirs(dest_dir, exist_ok=True)
                try:
                    shutil.copy2(file_path, dest_path)
                except:
                    pass

    # Create tarball of outDir1
    tree_path = os.path.join(outDir, 'tree.txt')
    tarball_path = os.path.join(outDir, 'text.tar.gz')
    with tarfile.open(tarball_path, 'w:gz') as tar:
        file_count = count_files_larger_than_size(outDir1)
        print(f"文本文件有效输出数量： {file_count}")
        tar.add(outDir1, arcname=os.path.basename(outDir1))

    # Clean up - delete everything except the tarballs
    print("Cleaning up...")
    for item in os.listdir(outDir):
        item_path = os.path.join(outDir, item)
        if item_path not in [tarball_path, tree_path]:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)

    print(f"Processing complete. Saved archives to:")
    print(f"  {tarball_path}")


def check_string_in_file_line_by_line(file_path, search_string):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if search_string in line:
                    return True
            return False
    except FileNotFoundError:
        print(f"文件 {file_path} 不存在")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        return False


if len(sys.argv) != 2:
    print('Usage:\n\tdocker_pull.py [registry/][repository/]image[:tag|@digest]\n')
    exit(1)

# Create a session for all requests
session = create_session()

# Look for the Docker image to download
repo = 'library'
tag = 'latest'
imgparts = sys.argv[1].split('/')
try:
    img, tag = imgparts[-1].split('@')
except ValueError:
    try:
        img, tag = imgparts[-1].split(':')
    except ValueError:
        img = imgparts[-1]
# Docker client doesn't seem to consider the first element as a potential registry unless there is a '.' or ':'
if len(imgparts) > 1 and ('.' in imgparts[0] or ':' in imgparts[0]):
    registry = imgparts[0]
    repo = '/'.join(imgparts[1:-1])
else:
    registry = 'registry-1.docker.io'
    if len(imgparts[:-1]) != 0:
        repo = '/'.join(imgparts[:-1])
    else:
        repo = 'library'
repository = '{}/{}'.format(repo, img)

# Get Docker authentication endpoint when it is required
auth_url = 'https://auth.docker.io/token'
reg_service = 'registry.docker.io'
resp = requests.get('https://{}/v2/'.format(registry), verify=False)
if resp.status_code == 401:
    auth_url = resp.headers['WWW-Authenticate'].split('"')[1]
    try:
        reg_service = resp.headers['WWW-Authenticate'].split('"')[3]
    except IndexError:
        reg_service = ""


# Get Docker token (this function is useless for unauthenticated registries like Microsoft)
def get_auth_head(type):
    resp = requests.get('{}?service={}&scope=repository:{}:pull'.format(auth_url, reg_service, repository),
                        verify=False)
    access_token = resp.json()['token']
    auth_head = {'Authorization': 'Bearer ' + access_token, 'Accept': type}
    return auth_head


# Docker style progress bar
def progress_bar(ublob, nb_traits):
    sys.stdout.write('\r' + ublob[7:19] + ': Downloading [')
    for i in range(0, nb_traits):
        if i == nb_traits - 1:
            sys.stdout.write('>')
        else:
            sys.stdout.write('=')
    for i in range(0, 49 - nb_traits):
        sys.stdout.write(' ')
    sys.stdout.write(']')
    sys.stdout.flush()


# Fetch manifest v2 and get image layer digests
print('[+] Trying to fetch manifest for {}'.format(repository))
auth_head = get_auth_head('application/vnd.oci.image.manifest.v1+json')
try:
    resp = session.get('https://{}/v2/{}/manifests/{}'.format(registry, repository, tag), headers=auth_head,
                       verify=False, timeout=30)
except requests.exceptions.RequestException as e:
    print('[-] Manifest fetch error:', str(e))
    exit(1)
print('[+] Response status code:', resp.status_code)
print('[+] Response headers:', resp.headers)

if resp.status_code != 200:
    print('[-] Cannot fetch manifest for {} [HTTP {}]'.format(repository, resp.status_code))
    print(resp.content)
    exit(1)

content_type = resp.headers.get('content-type', '')
print('[+] Content type:', content_type)

try:
    resp_json = resp.json()
    print('[+] Response JSON structure:')
    print(json.dumps(resp_json, indent=2))

    # Handle manifest list (multi-arch images)
    if 'manifests' in resp_json:
        print('[+] This is a multi-arch image. Available platforms:')
        for m in resp_json['manifests']:
            if 'platform' in m:
                print('    - {}/{} ({})'.format(
                    m['platform'].get('os', 'unknown'),
                    m['platform'].get('architecture', 'unknown'),
                    m['digest']
                ))

        # Try to find linux/amd64 platform first, then fall back to windows/amd64
        selected_manifest = None
        for m in resp_json['manifests']:
            platform = m.get('platform', {})
            if platform.get('os') == 'linux' and platform.get('architecture') == 'amd64':
                selected_manifest = m
                break

        if not selected_manifest:
            for m in resp_json['manifests']:
                platform = m.get('platform', {})
                if platform.get('os') == 'windows' and platform.get('architecture') == 'amd64':
                    selected_manifest = m
                    break

        if not selected_manifest:
            # If no preferred platform found, use the first one
            selected_manifest = resp_json['manifests'][0]

        print('[+] Selected platform: {}/{}'.format(
            selected_manifest['platform'].get('os', 'unknown'),
            selected_manifest['platform'].get('architecture', 'unknown')
        ))

        # Fetch the specific manifest
        try:
            # Get fresh auth token for manifest
            manifest_auth_head = get_auth_head('application/vnd.docker.distribution.manifest.v2+json')
            manifest_resp = session.get(
                'https://{}/v2/{}/manifests/{}'.format(registry, repository, selected_manifest['digest']),
                headers=manifest_auth_head,  # 使用新的认证头
                verify=False,
                timeout=30
            )
            if manifest_resp.status_code != 200:
                print('[-] Failed to fetch specific manifest:', manifest_resp.status_code)
                print('[-] Response content:', manifest_resp.content)
                exit(1)
            resp_json = manifest_resp.json()
            print('[+] Successfully fetched specific manifest')
        except Exception as e:
            print('[-] Error fetching specific manifest:', e)
            exit(1)

    # Now we should have the actual manifest with layers
    if 'layers' not in resp_json:
        print('[-] Error: No layers found in manifest')
        print('[-] Available keys:', list(resp_json.keys()))
        exit(1)

    layers = resp_json['layers']

except KeyError as e:
    print('[-] Error: Could not find required key in response:', e)
    print('[-] Available keys:', list(resp_json.keys()))
    exit(1)
except Exception as e:
    print('[-] Unexpected error:', e)
    exit(1)

# Create tmp directory if it doesn't exist
imgdir = 'tmp'
if not os.path.exists(imgdir):
    print('[+] Creating temporary directory:', imgdir)
    os.makedirs(imgdir)

config = resp_json['config']['digest']
try:
    confresp = session.get('https://{}/v2/{}/blobs/{}'.format(registry, repository, config), headers=auth_head,
                           verify=False, timeout=30)
except requests.exceptions.RequestException as e:
    print('[-] Config fetch error:', str(e))
    exit(1)
file = open('{}/{}.json'.format(imgdir, config[7:]), 'wb')
file.write(confresp.content)
file.close()

content = [{
    'Config': config[7:] + '.json',
    'RepoTags': [],
    'Layers': []
}]
if len(imgparts[:-1]) != 0:
    content[0]['RepoTags'].append('/'.join(imgparts[:-1]) + '/' + img + ':' + tag)
else:
    content[0]['RepoTags'].append(img + ':' + tag)

empty_json = '{"created":"1970-01-01T00:00:00Z","container_config":{"Hostname":"","Domainname":"","User":"","AttachStdin":false, \
	"AttachStdout":false,"AttachStderr":false,"Tty":false,"OpenStdin":false, "StdinOnce":false,"Env":null,"Cmd":null,"Image":"", \
	"Volumes":null,"WorkingDir":"","Entrypoint":null,"OnBuild":null,"Labels":null}}'

# Build layer folders
parentid = ''
for layer in layers:
    ublob = layer['digest']
    fake_layerid = hashlib.sha256(ublob.encode('utf-8')).hexdigest()
    oss_dir_key = "exp/sls/layers/" + fake_layerid + "/tree.txt"
    print(oss_dir_key)
    exist_in_oss = src_bucket.object_exists(oss_dir_key)
    print(f"checking {exist_in_oss}  {oss_dir_key}")
    if not exist_in_oss:
        # FIXME: Creating fake layer ID. Don't know how Docker generates it
        layerdir = imgdir + '/' + fake_layerid
        os.mkdir(layerdir)

        # Creating VERSION file
        file = open(layerdir + '/VERSION', 'w')
        file.write('1.0')
        file.close()

        # Creating layer.tar file
        sys.stdout.write(ublob[7:19] + ': Downloading...')
        sys.stdout.flush()
        auth_head = get_auth_head(
            'application/vnd.docker.distribution.manifest.v2+json')  # refreshing token to avoid its expiration
        bresp = requests.get('https://{}/v2/{}/blobs/{}'.format(registry, repository, ublob), headers=auth_head,
                             stream=True, verify=False)
        if (bresp.status_code != 200):  # When the layer is located at a custom URL
            bresp = requests.get(layer['urls'][0], headers=auth_head, stream=True, verify=False)
            if (bresp.status_code != 200):
                print('\rERROR: Cannot download layer {} [HTTP {}]'.format(ublob[7:19], bresp.status_code,
                                                                           bresp.headers['Content-Length']))
                print(bresp.content)
                exit(0)
        # Stream download and follow the progress
        bresp.raise_for_status()
        unit = int(bresp.headers['Content-Length']) / 50
        acc = 0
        nb_traits = 0
        progress_bar(ublob, nb_traits)
        with open(layerdir + '/layer_gzip.tar', "wb") as file:
            for chunk in bresp.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    acc = acc + 8192
                    if acc > unit:
                        nb_traits = nb_traits + 1
                        progress_bar(ublob, nb_traits)
                        acc = 0
        sys.stdout.write("\r{}: Extracting...{}".format(ublob[7:19], " " * 50))  # Ugly but works everywhere
        sys.stdout.flush()
        with open(layerdir + '/layer.tar', "wb") as file:  # Decompress gzip response
            unzLayer = gzip.open(layerdir + '/layer_gzip.tar', 'rb')
            shutil.copyfileobj(unzLayer, file)
            unzLayer.close()
        os.remove(layerdir + '/layer_gzip.tar')
        print("\r{}: Pull complete [{}]".format(ublob[7:19], bresp.headers['Content-Length']))
        # 分析layer
        analysis_files_dir = layerdir + '/layer.out'
        print("begin extract_tar... {}".format(layerdir + '/layer.tar'))
        extract_tar(layerdir + '/layer.tar', analysis_files_dir)
        analysis_layer_result_dir = layerdir + '/layer.out_result'
        os.makedirs(analysis_layer_result_dir, exist_ok=True)
        # step 1. 计算文件hash
        analysis_file_hash_path = analysis_layer_result_dir + "/tree.txt"
        print("begin calc_dir_hash... {}".format(analysis_files_dir))
        calc_dir_hash(analysis_files_dir, analysis_file_hash_path)
        # step 2. 分析文件
        print("begin process_my_dir... {}".format(analysis_files_dir))
        process_my_dir(analysis_files_dir, analysis_layer_result_dir)
        # step 3. 上传
        print("Uploading to oss...")
        try:
            src_bucket.put_object_from_file("exp/sls/layers/" + fake_layerid + "/check_model.sh",
                                            analysis_layer_result_dir + "/check_model.sh")
            src_bucket.put_object_from_file("exp/sls/layers/" + fake_layerid + "/model_check.tar.gz",
                                            analysis_layer_result_dir + "/model_check.tar.gz")
            src_bucket.put_object_from_file("exp/sls/layers/" + fake_layerid + "/text.tar.gz",
                                            analysis_layer_result_dir + "/text.tar.gz")
            src_bucket.put_object_from_file("exp/sls/layers/" + fake_layerid + "/tree.txt",
                                            analysis_layer_result_dir + "/tree.txt")
            # subprocess.run("ossutil cp -r " + analysis_layer_result_dir + " oss://hct-ae-test/exp/serverless/" + fake_layerid + "/", shell=True, check=True)
            print("Uploading to oss completed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Uploading to oss encountered an error (exit code {e.returncode}), but continuing with the process")
        shutil.rmtree(analysis_files_dir)
        shutil.rmtree(analysis_layer_result_dir)
        # 分析layer END

        # Creating json file
        file = open(layerdir + '/json', 'w')
        # last layer = config manifest - history - rootfs
        if layers[-1]['digest'] == layer['digest']:
            # FIXME: json.loads() automatically converts to unicode, thus decoding values whereas Docker doesn't
            json_obj = json.loads(confresp.content)
            del json_obj['history']
            try:
                del json_obj['rootfs']
            except:  # Because Microsoft loves case insensitiveness
                del json_obj['rootfS']
        else:  # other layers json are empty
            json_obj = json.loads(empty_json)
        json_obj['id'] = fake_layerid
        if parentid:
            json_obj['parent'] = parentid
        parentid = json_obj['id']
        file.write(json.dumps(json_obj))
        file.close()
    else:
        print("\r{}: Skip Layer".format(ublob[7:19]))
    content[0]['Layers'].append(fake_layerid + '/layer.tar')

manifest_file_path = imgdir + "/" + repo.replace('/', '_') + '_' + img + '__manifest.json'
file = open(manifest_file_path, 'w')
file.write(json.dumps(content))
file.close()

print("Uploading to oss...")
try:
    src_bucket.put_object_from_file("exp/sls/images-r8/" + repo.replace('/', '_') + '_' + img + '__manifest.json',
                                    manifest_file_path)
    print("Uploading to oss completed successfully")
except subprocess.CalledProcessError as e:
    print(f"Uploading to oss encountered an error (exit code {e.returncode}), but continuing with the process")

shutil.rmtree(imgdir)
print('\rDocker image pulled: ' + repo.replace('/', '_') + '_' + img)
