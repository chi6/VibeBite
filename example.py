import asyncio
from typing import List, Dict, Any
from llm_client import ChatGptClient
from prompt_manager import PromptManager
from agent import Agent
from group import Group
from rag_utils import RAGTools

async def main():
    # 初始化组件
    llm_client = ChatGptClient(model_name="gpt-35-turbo-16k", timeout=80, retry=7, thread_num=1)
    prompt_manager = PromptManager()
    rag_tools = RAGTools()
    
    # 添加知识库文档
    documents = [
        "北京是中国的首都，有着悠久的历史文化。",
        "上海是中国最大的经济中心城市。",
        "广州是中国南方重要的经济中心。"
    ]
    metadata = [
        {"source": "city_info", "city": "beijing"},
        {"source": "city_info", "city": "shanghai"},
        {"source": "city_info", "city": "guangzhou"}
    ]
    rag_tools.add_documents(documents, metadata)
    
    # 添加prompt
    prompt_manager.add_prompt("chat", "你是一个友好的助手，请根据提供的上下文信息回答问题。")
    prompt_manager.add_prompt("analysis", "你是一个数据分析师，请分析用户提供的数据。")
    
    # 创建agents（添加RAG支持）
    agent1 = Agent("1", "助手A", llm_client, prompt_manager, rag_tools)
    agent2 = Agent("2", "助手B", llm_client, prompt_manager, rag_tools)
    
    # 创建群组
    group = Group("group1", "测试群组")
    group.add_agent(agent1)
    group.add_agent(agent2)
    
    # 发起群组对话（现在会使用RAG检索相关信息）
    responses = await group.group_chat("1", "请介绍一下北京的特点。", "chat")
    print(responses)
    
    # 获取对话总结
    summary = group.summarize_chat()
    print(summary)

if __name__ == "__main__":
    asyncio.run(main())
