import os
import oss2

endpoint = "oss-accelerate.aliyuncs.com"

oss_auth = oss2.AnonymousAuth()
src_bucket = oss2.Bucket(oss_auth, endpoint, "gycoss")

local_directory = "../TestUploadData"  # 要上传的本地目录路径
base_oss_path = 'exp/hf/space/code-zips'

if not local_directory.endswith(os.sep):
    local_directory += os.sep

with open("output.txt", "w") as output_file:
    for root, dirs, files in os.walk(local_directory):
        for file in files:
            local_file_path = os.path.join(root, file)

            relative_path = os.path.relpath(local_file_path, local_directory)

            oss_object_key = f"{base_oss_path}/{relative_path.replace(os.sep, '/')}"

            try:
                # 上传文件到OSS
                src_bucket.put_object_from_file(oss_object_key, local_file_path)

                # 记录成功上传的文件路径
                output_file.write(f"{oss_object_key}\n")
                output_file.flush()  # 确保写入即时生效

                print(f"已上传: {local_file_path} -> {oss_object_key}")

            except Exception as e:
                print(f"上传失败 {local_file_path}: {str(e)}")
