import asyncio
import json
import re
from typing import Optional, List, Dict, Any

from agents import Agent, Runner, OpenAIChatCompletionsModel, RunConfig, set_default_openai_client, \
    set_default_openai_api, set_tracing_disabled, ModelSettings

from agents.mcp import MCPServerStreamableHttp

from pydantic import BaseModel
from openai import AsyncOpenAI

BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
API_KEY = "913cfb02ffa84828ad836098e88d68c7.RIq89Zp76UbHaFnF"
MODEL_NAME = "glm-4-air"

set_default_openai_api("chat_completions")
set_default_openai_client(AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY))
set_tracing_disabled(disabled=True)


class RepositoryInfo(BaseModel):
    """存储库信息的数据类"""
    exists: bool
    owner: Optional[str] = None
    name: Optional[str] = None
    full_name: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    stars: Optional[int] = None
    forks: Optional[int] = None
    summary: Optional[str] = None
    error: Optional[str] = None
    similar_repos: Optional[List[Dict[str, Any]]] = None


def parse_repository_info(text: str) -> RepositoryInfo:
    """解析agent返回的文本，提取仓库信息"""
    try:
        # 尝试直接解析JSON
        if text.strip().startswith('{') and text.strip().endswith('}'):
            data = json.loads(text)
            return RepositoryInfo(**data)
        
        # 尝试从markdown代码块中提取JSON
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
            return RepositoryInfo(**data)
        
        # 如果无法解析JSON，尝试从文本中提取信息
        exists = "not found" not in text.lower() and "不存在" not in text
        summary = text.strip()
        
        # 尝试提取仓库名称
        name_match = re.search(r'repository[:\s]+([^\s/]+/[^\s\n]+)', text, re.IGNORECASE)
        full_name = name_match.group(1) if name_match else None
        
        # 尝试提取描述
        desc_match = re.search(r'description[:\s]+([^\n]+)', text, re.IGNORECASE)
        description = desc_match.group(1).strip() if desc_match else None
        
        # 尝试提取语言
        lang_match = re.search(r'language[:\s]+([^\s\n,]+)', text, re.IGNORECASE)
        language = lang_match.group(1).strip() if lang_match else None
        
        return RepositoryInfo(
            exists=exists,
            full_name=full_name,
            description=description,
            language=language,
            summary=summary
        )
        
    except Exception as e:
        return RepositoryInfo(
            exists=False,
            error=f"解析失败: {str(e)}",
            summary=text
        )


async def check_repository_exists(repo_name: str) -> RepositoryInfo:
    """检查仓库是否存在并返回详细信息"""
    github_server = MCPServerStreamableHttp(
        params={"url": "https://api.githubcopilot.com/mcp/x/repos",
                "headers": {"Authorization": "Bearer "
                                             "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"}},
        name="github",
        cache_tools_list=True
    )
    
    async with github_server:
        agent = Agent(
            name="repository_checker",
            model=MODEL_NAME,
            model_settings=ModelSettings(temperature=0.0, truncation="auto"),
            mcp_servers=[github_server]
        )
        
        task = f"""请检查GitHub仓库 "{repo_name}" 是否存在，并提供详细信息。

要求：
1. 首先验证仓库是否存在
2. 如果存在，请收集以下信息：
   - 所有者/组织名称
   - 仓库名称
   - 完整仓库路径 (owner/repo)
   - 描述
   - 主要编程语言
   - 星标数量
   - 分支数量
   - 仓库总结

3. 如果不存在，请：
   - 搜索相似的仓库
   - 提供可能的替代建议
   - 说明为什么可能不存在

4. 请以JSON格式返回结果，包含以下字段：
   {{
     "exists": true/false,
     "owner": "所有者名称",
     "name": "仓库名称", 
     "full_name": "完整路径",
     "description": "描述",
     "language": "主要语言",
     "stars": 星标数,
     "forks": 分支数,
     "summary": "总结",
     "error": "错误信息(如果有)",
     "similar_repos": [相似仓库列表]
   }}

请确保返回的是有效的JSON格式。"""
        
        try:
            result = await Runner.run(agent, task)
            return parse_repository_info(result.final_output)
        except Exception as e:
            return RepositoryInfo(
                exists=False,
                error=f"Agent执行失败: {str(e)}",
                summary=f"检查仓库 {repo_name} 时发生错误"
            )


async def batch_check_repositories(repo_names: List[str]) -> List[RepositoryInfo]:
    """批量检查多个仓库"""
    results = []
    for repo_name in repo_names:
        print(f"正在检查仓库: {repo_name}")
        result = await check_repository_exists(repo_name)
        results.append(result)
        print(f"结果: {'存在' if result.exists else '不存在'} - {result.summary[:100]}...")
        # 添加延迟避免API限制
        await asyncio.sleep(1)
    return results


async def check_single_repository(repo_name: str) -> RepositoryInfo:
    """检查单个仓库是否存在"""
    print(f"正在检查仓库: {repo_name}")
    result = await check_repository_exists(repo_name)
    
    print(f"检查结果:")
    print(f"  存在: {'是' if result.exists else '否'}")
    if result.exists:
        print(f"  完整路径: {result.full_name}")
        print(f"  描述: {result.description}")
        print(f"  语言: {result.language}")
        print(f"  星标: {result.stars}")
        print(f"  分支: {result.forks}")
    else:
        print(f"  错误: {result.error}")
    print(f"  总结: {result.summary}")
    
    return result


def load_repositories_from_file(file_path: str) -> List[str]:
    """从文件中加载仓库列表"""
    repositories = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # 跳过空行和注释
                    repositories.append(line)
        print(f"从文件 {file_path} 加载了 {len(repositories)} 个仓库")
    except FileNotFoundError:
        print(f"文件 {file_path} 不存在")
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
    
    return repositories


async def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1:
        # 如果提供了命令行参数，检查指定的仓库
        repo_name = sys.argv[1]
        await check_single_repository(repo_name)
    else:
        # 默认检查示例仓库列表
        test_repos = [
            "microsoft/vscode",
            "facebook/react", 
            "vldemo",  # 这个可能不存在
            "tensorflow/tensorflow",
            "nonexistent/repo"  # 这个肯定不存在
        ]
        
        print("开始检查仓库...")
        results = await batch_check_repositories(test_repos)
        
        print("\n=== 检查结果汇总 ===")
        for i, (repo_name, result) in enumerate(zip(test_repos, results)):
            print(f"\n{i+1}. {repo_name}:")
            print(f"   存在: {'是' if result.exists else '否'}")
            if result.exists:
                print(f"   完整路径: {result.full_name}")
                print(f"   描述: {result.description}")
                print(f"   语言: {result.language}")
                print(f"   星标: {result.stars}")
                print(f"   分支: {result.forks}")
            else:
                print(f"   错误: {result.error}")
            print(f"   总结: {result.summary}")
        
        # 保存结果到JSON文件
        with open('repository_check_results.json', 'w', encoding='utf-8') as f:
            json.dump([result.dict() for result in results], f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到 repository_check_results.json")


async def check_repositories_from_file(file_path: str):
    """从文件读取仓库列表并批量检查"""
    repositories = load_repositories_from_file(file_path)
    if not repositories:
        print("没有找到要检查的仓库")
        return
    
    print(f"开始检查 {len(repositories)} 个仓库...")
    results = await batch_check_repositories(repositories)
    
    # 保存结果
    output_file = f"check_results_{file_path.replace('.txt', '').replace('.csv', '')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump([result.dict() for result in results], f, ensure_ascii=False, indent=2)
    print(f"结果已保存到 {output_file}")
    
    # 打印统计信息
    existing_count = sum(1 for r in results if r.exists)
    print(f"\n统计信息:")
    print(f"  总仓库数: {len(repositories)}")
    print(f"  存在的仓库: {existing_count}")
    print(f"  不存在的仓库: {len(repositories) - existing_count}")


if __name__ == '__main__':
    asyncio.run(main())
