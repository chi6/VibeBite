from flask import Flask, request, jsonify
from llm_client import ChatGptClient
from prompt_manager import PromptManager
from agent import Agent
from group import Group
from rag_utils import RAGTools
import asyncio

app = Flask(__name__)

@app.route('/initAgent', methods=['POST'])
def initAgent():
    data = request.get_json()
    print(data)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    agent_id = data.get('agent_id')
    message = data.get('message')
    task_name = data.get('task_name')
    agent1 = Agent("1", "助手A", llm_client, prompt_manager, rag_tools)
    # 处理请求逻辑
    response = {
        "agent_id": agent_id,
        "message": message,
        "task_name": task_name
    }
    return jsonify(response)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    print(data)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    agent_id = data.get('agent_id')
    message = data.get('message')
    task_name = data.get('task_name')

    # 处理请求逻辑
    response = {
        "agent_id": agent_id,
        "message": message,
        "task_name": task_name
    }
    return jsonify(response)

if __name__ == '__main__':
    
    # 初始化组件
    llm_client = ChatGptClient(model_name="gpt-35-turbo-16k", timeout=80, retry=7, thread_num=1)
    
    prompt_manager = PromptManager()
    rag_tools = RAGTools()

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
    app.run(host='0.0.0.0', port=5000,debug=True) 