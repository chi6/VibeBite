import os
import json
import asyncio
from typing import List, Dict, Any
from llm_client import ChatGptClient
from prompt_manager import PromptManager
from agent import Agent
from group import Group
from rag_utils import RAGTools
from config import Config

def init_directories():
    """初始化必要的目录"""
    directories = [
        Config.MEMORY_PATH,
        Config.PROMPT_PATH,
        Config.VECTOR_DB_PATH
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"创建目录: {directory}")

def init_prompts(prompt_manager: PromptManager):
    """初始化基础prompt模板"""
    base_prompts = {
        "chat": """你是一个友好的AI助手。
在回答问题时，请注意：
1. 使用简洁清晰的语言
2. 基于上下文信息提供答案
3. 如果不确定，请诚实地表示不知道""",

        "analysis": """你是一个专业的数据分析师。
分析数据时请：
1. 提供数据的关键洞察
2. 使用客观的分析方法
3. 给出可行的建议""",

        "expert": """你是相关领域的专家。
回答问题时请：
1. 提供专业的见解
2. 使用准确的术语
3. 结合实际案例说明"""
    }
    
    for task_name, prompt in base_prompts.items():
        prompt_manager.add_prompt(task_name, prompt)
    print("初始化prompt模板完成")

def init_knowledge_base(rag_tools: RAGTools):
    """初始化知识库"""
    # 示例文档
    documents = [
        "人工智能是计算机科学的一个重要分支，致力于创建能够模拟人类智能的系统。",
        "机器学习是人工智能的一个子领域，通过数据学习来改善系统性能。",
        "深度学习是机器学习的一种方法，使用多层神经网络处理复杂问题。"
    ]
    
    metadata = [
        {"source": "ai_intro", "topic": "ai"},
        {"source": "ai_intro", "topic": "machine_learning"},
        {"source": "ai_intro", "topic": "deep_learning"}
    ]
    
    rag_tools.add_documents(documents, metadata)
    print("初始化知识库完成")

async def init_agents(llm_client: ChatGptClient, prompt_manager: PromptManager, rag_tools: RAGTools) -> List[Agent]:
    """初始化智能体"""
    agents = [
        Agent("1", "通用助手", llm_client, prompt_manager, rag_tools),
        Agent("2", "���析专家", llm_client, prompt_manager, rag_tools),
        Agent("3", "领域专家", llm_client, prompt_manager, rag_tools)
    ]
    print("初始化智能体完成")
    return agents

async def main():
    print("开始初始化服务...")
    
    # 初始化目录
    init_directories()
    
    # 初始化组件
    llm_client = ChatGptClient(
        model_name="gpt-35-turbo-16k",
        timeout=80,
        retry=7,
        thread_num=1
    )
    prompt_manager = PromptManager()
    rag_tools = RAGTools()
    
    # 初始化各个模块
    init_prompts(prompt_manager)
    init_knowledge_base(rag_tools)
    agents = await init_agents(llm_client, prompt_manager, rag_tools)
    
    # 创建群组
    group = Group("main_group", "主群组")
    for agent in agents:
        group.add_agent(agent)
    
    print("\n服务初始化完成！")
    print("\n可用的agents:")
    for agent in agents:
        print(f"- {agent.name} (ID: {agent.agent_id})")
    
    # 测试对话
    print("\n开始测试对话...")
    test_message = "请简单介绍一下人工智能。"
    responses = await group.group_chat(agents[0].agent_id, test_message, "chat")
    
    print(f"\n测试问题: {test_message}")
    print("回复:")
    for response in responses:
        print(f"- Agent {response['agent_id']}: {response['content']}")
    
    print("\n服务启动成功！")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
