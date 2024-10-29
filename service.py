from flask import Flask, request, jsonify
from typing import Dict, Optional
from llm_client import ChatGptClient
from prompt_manager import PromptManager
from agent import Agent
from group import Group
from rag_utils import RAGTools
import asyncio
import time

class AgentChatService:
    def __init__(self):
        self.app = Flask(__name__)
        self.llm_client = None
        self.prompt_manager = None
        self.rag_tools = None
        self.agents: Dict[str, Agent] = {}
        self.groups: Dict[str, Group] = {}
        
        # 注册路由
        self.register_routes()
        
    def register_routes(self):
        """注册所有路由"""
        self.app.route('/initAgent', methods=['POST'])(self.init_agent)
        self.app.route('/chat', methods=['POST'])(self.chat)
        
    def init_components(self):
        """初始化所有组件"""
        # 初始化LLM客户端
        self.llm_client = ChatGptClient(
            model_name="qwen-max",
            timeout=80,
            retry=7,
            thread_num=1
        )
        
        # 初始化Prompt管理器
        self.prompt_manager = PromptManager()
        self._init_prompts()
        
        # 初始化RAG工具
        #self.rag_tools = RAGTools()
        self._init_knowledge_base()
        
        # 初始化默认agents和groups
        self._init_default_agents()
        
    def _init_prompts(self):
        """初始化基础prompt"""
        base_prompts = {
            "chat": "你是一个友好的助手，请根据提供的上下文信息回答问题。",
            "analysis": "你是一个数据分析师，请分析用户提供的数据。",
            "expert": "你是相关领域的专家，请提供专业的建议。"
        }
        for task_name, prompt in base_prompts.items():
            self.prompt_manager.add_prompt(task_name, prompt)
            
    def _init_knowledge_base(self):
        """初始化知识库"""
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
        #self.rag_tools.add_documents(documents, metadata)
        
    def _init_default_agents(self):
        """初始化默认agents和groups"""
        # 创建默认agents
        default_agents = [
            Agent("1", "通用助手", self.llm_client, self.prompt_manager),
            Agent("2", "分析专家", self.llm_client, self.prompt_manager),
            Agent("3", "领域专家", self.llm_client, self.prompt_manager)
        ]
        
        for agent in default_agents:
            self.agents[agent.agent_id] = agent
            
        # 创建默认group
        default_group = Group("main_group", "主群组")
        for agent in default_agents:
            default_group.add_agent(agent)
        self.groups[default_group.group_id] = default_group
        
    def init_agent(self):
        """初始化新的agent"""
        start_time = time.time()
        
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "Invalid JSON",
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 400
            
        agent_id = data.get('agent_id')
        name = data.get('name', f"Agent_{agent_id}")
        
        if agent_id in self.agents:
            return jsonify({
                "error": "Agent ID already exists",
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 400
            
        new_agent = Agent(
            agent_id,
            name,
            self.llm_client,
            self.prompt_manager,
            #self.rag_tools
        )
        self.agents[agent_id] = new_agent
        
        return jsonify({
            "agent_id": agent_id,
            "name": name,
            "status": "initialized",
            "response_time": f"{time.time() - start_time:.3f}s"
        })
        
    async def chat(self):
        """处理聊天请求"""
        start_time = time.time()
        
        data = request.get_json()
        print(data)
        if not data:
            return jsonify({
                "error": "Invalid JSON",
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 400
            
        agent_id = data.get('agent_id')
        message = data.get('message')
        task_name = data.get('task_name', 'chat')
        group_id = data.get('group_id', 'main_group')
        
        if group_id not in self.groups:
            return jsonify({
                "error": "Group not found",
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 404
            
        group = self.groups[group_id]
        #responses = await group.group_chat(agent_id, message, task_name)
        responses = await self.agents[agent_id].process_task(task_name, message)
        
        return jsonify({
            "response": responses,
            "response_time": f"{time.time() - start_time:.3f}s"
        })
        
    def run(self, host='0.0.0.0', port=5000, debug=True):
        """运行服务"""
        self.init_components()
        self.app.run(host=host, port=port, debug=debug)

# 创建服务实例
service = AgentChatService()

if __name__ == '__main__':
    service.run() 