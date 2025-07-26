#!/usr/bin/env python3
"""
GitHub仓库存在性检查工具使用示例

这个脚本展示了如何使用 pypiclassifierbyagent.py 中的功能来检查GitHub仓库是否存在。

使用方法:
1. 检查单个仓库: python repository_checker_example.py microsoft/vscode
2. 从文件批量检查: python repository_checker_example.py --file repositories.txt
3. 交互式检查: python repository_checker_example.py --interactive
"""

import asyncio
import sys
import os
from pypiclassifierbyagent import (
    check_single_repository, 
    check_repositories_from_file,
    load_repositories_from_file,
    RepositoryInfo
)


async def interactive_mode():
    """交互式模式，用户可以输入仓库名称进行检查"""
    print("=== GitHub仓库检查工具 (交互式模式) ===")
    print("输入仓库名称 (格式: owner/repo) 或 'quit' 退出")
    
    while True:
        try:
            repo_name = input("\n请输入仓库名称: ").strip()
            if repo_name.lower() in ['quit', 'exit', 'q']:
                print("退出程序")
                break
            
            if not repo_name:
                continue
                
            await check_single_repository(repo_name)
            
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
            break
        except Exception as e:
            print(f"发生错误: {e}")


def create_sample_repository_file():
    """创建示例仓库列表文件"""
    sample_repos = [
        "# GitHub仓库列表示例文件",
        "# 每行一个仓库，格式: owner/repo",
        "# 以#开头的行会被忽略",
        "",
        "microsoft/vscode",
        "facebook/react",
        "tensorflow/tensorflow",
        "pytorch/pytorch",
        "vuejs/vue",
        "angular/angular",
        "nonexistent/repo",  # 这个仓库不存在
        "vldemo",  # 这个可能不存在
    ]
    
    filename = "sample_repositories.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sample_repos))
    
    print(f"已创建示例文件: {filename}")
    return filename


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("GitHub仓库检查工具")
        print("\n使用方法:")
        print("1. 检查单个仓库: python repository_checker_example.py <owner/repo>")
        print("2. 从文件批量检查: python repository_checker_example.py --file <filename>")
        print("3. 交互式检查: python repository_checker_example.py --interactive")
        print("4. 创建示例文件: python repository_checker_example.py --create-sample")
        return
    
    command = sys.argv[1]
    
    if command == "--interactive":
        await interactive_mode()
    
    elif command == "--file":
        if len(sys.argv) < 3:
            print("错误: 请指定文件名")
            print("用法: python repository_checker_example.py --file <filename>")
            return
        
        file_path = sys.argv[2]
        if not os.path.exists(file_path):
            print(f"错误: 文件 {file_path} 不存在")
            return
        
        await check_repositories_from_file(file_path)
    
    elif command == "--create-sample":
        filename = create_sample_repository_file()
        print(f"\n现在可以使用以下命令检查示例仓库:")
        print(f"python repository_checker_example.py --file {filename}")
    
    else:
        # 检查单个仓库
        repo_name = command
        await check_single_repository(repo_name)


if __name__ == '__main__':
    asyncio.run(main()) 