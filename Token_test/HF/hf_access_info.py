import requests
import json
import os
import argparse
import time
import random


def load_processed_tokens(filename="hf_access_info_done.txt"):
    """
    加载已经处理过的tokens

    Args:
        filename (str): 存储已处理tokens的文件名

    Returns:
        set: 已处理过的tokens集合
    """
    processed_tokens = set()
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    token = line.strip()
                    if token:
                        processed_tokens.add(token)
            print(f"已从 {filename} 中加载 {len(processed_tokens)} 个已处理的tokens")
        except Exception as e:
            print(f"读取已处理tokens文件时出错: {e}")
    return processed_tokens


def mark_token_as_processed(token, filename="hf_access_info_done.txt"):
    """
    将token标记为已处理

    Args:
        token (str): 已处理的Hugging Face API令牌
        filename (str): 存储已处理tokens的文件名
    """
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(f"{token}\n")
    except Exception as e:
        print(f"更新已处理tokens文件时出错: {e}")


def get_current_user_info(token):
    """
    调用Hugging Face API获取当前用户信息

    Args:
        token (str): Hugging Face API令牌

    Returns:
        tuple: (user_info, error_message, is_rate_limit)
            - user_info: 用户信息字典，如果请求失败则为None
            - error_message: 错误信息，如果请求成功则为None
            - is_rate_limit: 布尔值，表示是否为速率限制错误
    """
    url = "https://huggingface.co/api/whoami-v2"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json(), None, False
    except requests.exceptions.HTTPError as e:
        # 检查状态码或响应体中是否包含速率限制错误
        is_rate_limit = False

        # 检查状态码
        if e.response.status_code == 429:
            is_rate_limit = True

        # 检查响应体
        error_text = e.response.text
        rate_limit_keywords = ["429 Client Error", "rate limit", "too many requests", "ratelimit"]
        for keyword in rate_limit_keywords:
            if keyword.lower() in error_text.lower():
                print("\tRate Limit")
                is_rate_limit = True
                break

        error_message = f"HTTP错误: {e}\n详细信息: {error_text}"
        return None, error_message, is_rate_limit
    except Exception as e:
        return None, f"发生错误: {e}", False


def get_current_user_info_with_retry(token, max_retries=10, initial_delay=5):
    """
    带重试机制的获取用户信息函数，遇到rate limit错误会自动重试

    Args:
        token (str): Hugging Face API令牌
        max_retries (int): 最大重试次数
        initial_delay (int): 初始等待秒数

    Returns:
        tuple: (user_info, error_message)
            - user_info: 用户信息字典，如果请求失败则为None
            - error_message: 错误信息，如果请求成功则为None
    """
    delay = initial_delay
    retries = 0

    while retries <= max_retries:
        user_info, error_message, is_rate_limit = get_current_user_info(token)

        # 如果成功或者不是rate limit错误，直接返回结果
        if user_info is not None or not is_rate_limit:
            return user_info, error_message

        # 遇到rate limit错误，进行重试
        retries += 1
        if retries <= max_retries:
            # 增加一些随机性，避免所有请求同时重试
            jitter = random.uniform(0, 0.5)
            sleep_time = delay + jitter

            print(f"遇到rate limit错误，等待 {sleep_time:.2f} 秒后重试 (重试 {retries}/{max_retries})...")
            time.sleep(sleep_time)

            # 指数退避 - 每次失败后将等待时间翻倍
            delay *= 2
        else:
            print(f"达到最大重试次数 ({max_retries})，放弃请求。")

    return None, error_message


def save_to_file(token, user_info, txtoutputdir,error_message=None):
    """
    保存用户信息到文件

    Args:
        token (str): Hugging Face API令牌
        user_info (dict or None): 用户信息或None（如果请求失败）
        error_message (str or None): 错误信息（如果有）
    """
    if user_info is not None:
        # 令牌有效
        filename = f"{txtoutputdir}/valid/{token}.txt"
        content = json.dumps(user_info, indent=2, ensure_ascii=False)
    else:
        # 令牌无效
        filename = f"{txtoutputdir}/invalid/invalid_{token}.txt"
        content = error_message or "Invalid token"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="获取Hugging Face用户信息")
    parser.add_argument("--input", "-i", required=True,
                        help="包含HuggingFace tokens的输入txt文件路径，每行一个token")
    parser.add_argument("--txtoutputdir", "-txto", required=True,
                        help="给出每一个token的输出目录")
    parser.add_argument("--max-retries", type=int, default=10,
                        help="遇到rate limit时的最大重试次数")
    parser.add_argument("--initial-delay", type=int, default=5,
                        help="第一次重试前的等待秒数")
    parser.add_argument("--done-file", type=str, default="hf_access_info_done.txt",
                        help="记录已处理tokens的文件名")

    args = parser.parse_args()

    # 确保输入文件存在
    if not os.path.exists(args.input):
        print(f"错误: 输入文件 {args.input} 不存在")
        return

    # 加载已处理的tokens
    processed_tokens = load_processed_tokens(args.done_file)

    # 读取所有tokens
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            tokens = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"读取输入文件时出错: {e}")
        return

    if not tokens:
        print("输入文件中没有找到有效的tokens")
        return

    # 遍历每个token并获取用户信息
    total_tokens = len(tokens)
    skipped_tokens = 0

    for i, token in enumerate(tokens, 1):
        # 跳过已处理的tokens
        if token in processed_tokens:
            skipped_tokens += 1
            print(f"[{i}/{total_tokens}] 跳过已处理的token: {token}")
            continue

        print(f"[{i}/{total_tokens}] 正在处理token: {token}")
        time.sleep(2)
        user_info, error_message = get_current_user_info_with_retry(
            token,
            max_retries=args.max_retries,
            initial_delay=args.initial_delay
        )

        save_to_file(token, user_info, args.txtoutputdir,error_message,)

        if user_info is not None:
            print(f"  有效token，结果已保存到 {token}.txt")
            # 将有效token标记为已处理
            mark_token_as_processed(token, args.done_file)
        else:
            print(f"  无效token，结果已保存到 invalid_{token}.txt")

    print(f"\n处理完成！共处理 {total_tokens} 个tokens，其中跳过了 {skipped_tokens} 个已处理的tokens")


if __name__ == "__main__":
    main()
