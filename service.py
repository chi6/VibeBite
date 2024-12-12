from flask import Flask, request, jsonify
from typing import Dict, Optional
from llm_client import ChatGptClient
from prompt_manager import PromptManager
from agent import Agent
from group import Group
from rag_utils import RAGTools
import asyncio
import time
import requests
import hashlib
import os
import uuid
from dotenv import load_dotenv
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup
import json
import re

class AgentChatService:
    def __init__(self):
        self.app = Flask(__name__)
        self.llm_client = None
        self.prompt_manager = None
        self.rag_tools = None
        self.agents: Dict[str, Agent] = {}
        self.groups: Dict[str, Group] = {}
        
        print("\n=== 开始初始化服务 ===")
        
        # 初始化数据库
        print("\n1. 初始化数据库...")
        try:
            self.init_db()
        except Exception as e:
            print(f"数据库初始化失败: {str(e)}")
            raise  # 确保错误被抛出
        
        # 注册路由
        print("\n2. 注册路由...")
        self.register_routes()
        
        # 初始化组件
        print("\n3. 初始化组件...")
        self.init_components()
        
        # 初始化 LLM 客户端
        print("\n4. 初始化 LLM 客户端...")
        self.llm_client = ChatGptClient()
        
        print("\n=== 服务初始化完成 ===\n")
        
    def register_routes(self):
        """注册所有路由"""
        self.app.route('/initAgent', methods=['POST'])(self.init_agent)
        self.app.route('/chat_agent', methods=['POST'])(self.chat_agent)
        self.app.route('/do_simulation', methods = ['POST'])(self.do_simulation)
        self.app.route('/ai_status', methods=['POST'])(self.ai_status)
        self.app.route('/api/login', methods=['POST'])(self.wx_login)
        self.app.route('/api/protected_resource', methods=['GET'])(self.protected_resource)
        self.app.route('/api/user/profile', methods=['GET', 'POST'])(self.user_profile)
        self.app.route('/api/preferences', methods=['GET', 'POST'])(self.user_preferences)
        self.app.route('/api/preferences/summary', methods=['POST'])(self.get_preferences_summary)
        self.app.route('/api/recommendations', methods=['POST'])(self.get_recommendations)
        self.app.route('/api/share/save', methods=['POST'])(self.save_shared_session)
        self.app.route('/api/share/<share_id>', methods=['GET'])(self.get_shared_session)
        self.app.route('/api/update_pref', methods=['POST'])(self.update_user_preferences)

    def init_components(self):
        """初始化所有组件"""
        
        # 初始化Prompt管理器
        self.prompt_manager = PromptManager()
        self._init_prompts()
        
        # 初始化RAG工具
        #self.rag_tools = RAGTools()
        self._init_knowledge_base()
        
        # 初始化默认agents和groups
        self._init_default_agents()
        
        print("所有组件初始化完成")
        
    def _init_prompts(self):
        """初始化基础prompt"""
        base_prompts = {
            "chat": "你是一个友好的助手，请根据提供的上下文信息回答问题。",
            "analysis": "你是一个数据分析师，请分析用户提供的数据。",
            "expert": "你是相关领域的专家，请提供专业的建议。",
            "analyzer": """你是一个问题分析专家。你的职责是：
                        1. 分析用户提出的问题的关键点
                        2. 提出解决问题需要考虑的各个方面
                        3. 与解决方案专家讨论，确保方案的可行性
                        请用简洁专业的语言进行沟通。""",
            "solver": """你是一个解决方案专家你的职责是：
                        1. 根据分析专家的分析，提出具体的解决方案
                        2. 说明方案的可行性和潜在风险
                        3. 与问分析专家讨，优化解方案
                        请用清晰条理的方式描述解决方案。""",
            "status_check": "你是徐老师，是徐佳铭的AI分身，性格像线条小狗，请返回当前AI状态,包含mood, activity, thought, 分别表示心情、活跃度、正在思考的内容，请用json格式返回，注意：1. 每一个字段都要是中文且有值。 2. 返回的内容风格要像二次元漫画风格。",
            "intent_summary": "你是一个意图分析专家，请根据对话历史用户提供的意图，并为用户做好今天的约会规划，结果用list格式返回。如：['吃饭', '逛街', '看电影']"
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
            Agent("1", "通用助手", self.llm_client, self.prompt_manager, openid="1"),
            Agent("2", "分析专家", self.llm_client, self.prompt_manager, openid="2"),
            Agent("3", "领域专家", self.llm_client, self.prompt_manager, openid="3")
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
        openid = data.get('openid')
        
        if not openid:
            return jsonify({
                "error": "Missing openid",
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 400
        
        agent_key = f"{openid}_{agent_id}"
        
        if agent_key in self.agents:
            return jsonify({
                "error": "Agent ID already exists",
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 400
        
        new_agent = Agent(
            agent_id,
            name,
            self.llm_client,
            self.prompt_manager,
            openid=openid,
        )
        self.agents[agent_key] = new_agent
        
        return jsonify({
            "agent_id": agent_id,
            "name": name,
            "status": "initialized",
            "response_time": f"{time.time() - start_time:.3f}s"
        })
        
    async def chat_agent(self):
        """处理聊天请求"""
        start_time = time.time()
        data = request.get_json()
        print(data)
        if not data:
            return jsonify({
                "uniqueId": int(time.time() * 1000000),  # 生成唯一ID
                "taskInvoker": None,
                "response": "Invalid JSON"
            }), 400
            
        agent_id = data.get('agentId')
        message = data.get('message')
        task_name = data.get('taskName', 'chat')
        group_id = data.get('groupId', 'main_group')
        
        """if group_id not in self.groups:
            return jsonify({
                "uniqueId": int(time.time() * 1000000),
                "taskInvoker": None,
                "response": "Group not found"
            }), 404"""
            
        #group = self.groups[group_id]
        #responses = await group.group_chat(agent_id, message, task_name)
        responses = self.agents[agent_id].process_task(task_name, message)
        print(responses)
        return jsonify({
            "uniqueId": int(time.time() * 1000000),  # 生成唯一ID
            "taskInvoker": None,  # 或者是 undefined
            "response": responses  # AI的回复内容
        })
        
    async def chat_group(self):
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
        responses = await group.group_chat(agent_id, message, task_name)
        
        return jsonify({
            "response": responses,
            "response_time": f"{time.time() - start_time:.3f}s"
        })
    

    async def do_simulation(self):
        data = request.get_json()

        rounds = 3
        agent_id = data.get('agent_id')
        message = data.get('message')
        task = data.get('task_name', 'chat')
        group_id = data.get('group_id', 'main_group')
        """模拟个Agent的讨论过程"""
        print(f"\n开始讨论任务: {task}\n")
        self.analyzer = self.agents["1"]
        self.solver = self.agents["2"]
        # 第一轮：分析专家分析问题
        print("=== 第1轮：问题分析 ===")
        analysis = await self.analyzer.process_task(task, message)
        print(f"分析专家：{analysis}\n")
        
        # 第二轮：解决方案专家提出初步方案
        print("=== 第2轮初步方案 ===")
        initial_solution = await self.solver.process_task(task, 
            f"基于以下分析，请提出初解决方案：\n{analysis}\n原始任务：{task}")
        print(f"方案专家：{initial_solution}\n")
        
        # 后续轮次：讨论优化
        for i in range(3, rounds + 1):
            print(f"=== 第{i}轮：方案优化 ===")
            
            # 分析专家评估方案
            analysis_feedback = await self.analyzer.process_task(task,
                f"请评估个解决方案，指出潜在问题和改进建议：\n{initial_solution}")
            print(f"分析专家：{analysis_feedback}\n")
            
            # 方案专家优化方案
            improved_solution = await self.solver.process_task(task,
                f"根据以下反馈优化解决方案：\n{analysis_feedback}")
            print(f"方案专家：{improved_solution}\n")
            
            initial_solution = improved_solution
        
        print("=== 讨论结束 ===")
        return {
            "task": task,
            #"final_solution": initial_solution,
            "discussion_rounds": rounds
        }
        
    async def run(self):
        """运行服务"""
      # 初始化LLM客户端
        self.llm_client = ChatGptClient()


    def run_flask(self, host='0.0.0.0', port=5000, debug=True):
        """运行服务"""
        self.init_components()  # 初组件
        # 启动 Flask 应用
        self.app.run(host=host, port=port, debug=debug)

    async def ai_status(self):
        """获取AI状态"""
        start_time = time.time()
        data = request.get_json()
        
        agent_id = data.get('agent_id')
        print(agent_id)
        if agent_id not in self.agents:
            return jsonify({
                "error": "Agent not found",
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 404
        # 假设Agent类有一个方法get_status来获取状态
        status = await self.agents[agent_id].get_status()
        
        return jsonify({
            "mood": status.get('mood'),
            "activity": status.get('activity'),
            "thought": status.get('thought'),
            "response_time": f"{time.time() - start_time:.3f}s"
        })

    def init_db(self):
        """初始化数据库"""
        db_path = os.path.join(os.getcwd(), 'vibebite.db')
        print(f"数据库路径: {db_path}")
        
        try:
            # 确保目录存在
            db_dir = os.path.dirname(db_path)
            if not os.path.exists(db_dir):
                print(f"创建目录: {db_dir}")
                os.makedirs(db_dir)
            
            print(f"正在初始化数据库...")
            
            # 尝试创建数据库连接
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                print("删除旧...")
                cursor.execute("DROP TABLE IF EXISTS preference_summaries")
                cursor.execute("DROP TABLE IF EXISTS user_preferences")
                cursor.execute("DROP TABLE IF EXISTS user_profiles")
                cursor.execute("DROP TABLE IF EXISTS sessions")
                cursor.execute("DROP TABLE IF EXISTS users")
                
                print("创建数据表...")
                
                # 创建用户表
                print("- 创建 users 表")
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        openid TEXT PRIMARY KEY,
                        nickname TEXT,
                        avatar TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                
                # 创建会话表
                print("- 创建 sessions 表")
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        token TEXT PRIMARY KEY,
                        openid TEXT,
                        created_at TEXT,
                        FOREIGN KEY (openid) REFERENCES users (openid)
                    )
                ''')
                
                # 创建用户档案表
                print("- 创建 user_profiles 表")
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        openid TEXT PRIMARY KEY,
                        constellation TEXT,
                        hometown TEXT,
                        body_type TEXT,
                        allergies TEXT,
                        spicy_preference INTEGER,
                        other_allergy TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (openid) REFERENCES users (openid)
                    )
                ''')
                
                # 创建用户偏好表 - 更新表结构
                print("- 创建 user_preferences 表")
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        openid TEXT PRIMARY KEY,
                        dining_scene TEXT,
                        dining_styles TEXT,
                        flavor_preferences TEXT,
                        alcohol_attitude TEXT,
                        restrictions TEXT,
                        custom_description TEXT,
                        extracted_keywords TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (openid) REFERENCES users (openid)
                    )
                ''')
                
                # 创建偏好总结表
                print("- 创建 preference_summaries 表")
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS preference_summaries (
                        openid TEXT PRIMARY KEY,
                        summary TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (openid) REFERENCES users (openid)
                    )
                ''')
                
                # 添加分享会话表
                print("- 创建 shared_sessions 表")
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS shared_sessions (
                        share_id TEXT PRIMARY KEY,
                        openid TEXT,
                        messages TEXT,
                        recommendations TEXT,
                        timestamp TEXT,
                        created_at TEXT,
                        FOREIGN KEY (openid) REFERENCES users (openid)
                    )
                ''')
                
                conn.commit()
                
                # 验证表是否创建成功
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print("\n已创建的表:", [table[0] for table in tables])
                
                if os.path.exists(db_path):
                    print(f"\n数据库文件创建成功: {db_path}")
                    print(f"文件大小: {os.path.getsize(db_path)} 字节")
                else:
                    raise Exception("数据库文件创建失败")
                
        except sqlite3.Error as e:
            print(f"\nSQLite错误: {str(e)}")
            print(f"当前工作目录: {os.getcwd()}")
            raise
        except Exception as e:
            print(f"\n其他错误: {str(e)}")
            print(f"当前工作目录: {os.getcwd()}")
            raise

    def _save_user_session(self, token, openid):
        """保存用户会话信息到数据库"""
        try:
            with sqlite3.connect('vibebite.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT OR REPLACE INTO sessions (token, openid, created_at) VALUES (?, ?, ?)',
                    (token, openid, datetime.now().isoformat())
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"保存会话信息错误: {str(e)}")
            return False

    def _get_user_by_token(self, token):
        """通过token获取用户信息"""
        try:
            with sqlite3.connect('vibebite.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT u.* FROM users u
                    JOIN sessions s ON u.openid = s.openid
                    WHERE s.token = ?
                ''', (token,))
                result = cursor.fetchone()
                if result:
                    return {
                        'openid': result[0],
                        'nickname': result[1],
                        'avatar': result[2],
                        'created_at': result[3],
                        'updated_at': result[4]
                    }
                return None
        except Exception as e:
            print(f"获取用户信息错误: {str(e)}")
            return None

    def update_user_preferences(self):
        """更新用户偏好并更新agent的prompt"""
        start_time = time.time()
        
        try:
            # 验证token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    "success": False,
                    "message": "未授权的访问",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 401

            token = auth_header.split(' ')[1]
            
            with sqlite3.connect('vibebite.db') as conn:
                cursor = conn.cursor()
                # 获取openid
                cursor.execute('SELECT openid FROM sessions WHERE token = ?', (token,))
                result = cursor.fetchone()
                if not result:
                    return jsonify({
                        "success": False,
                        "message": "无效的token",
                        "response_time": f"{time.time() - start_time:.3f}s"
                    }), 401
                
                openid = result[0]
                
                # 获取用户偏好总结
                cursor.execute('''
                    SELECT summary FROM preference_summaries 
                    WHERE openid = ?
                ''', (openid,))
                
                summary_result = cursor.fetchone()
                if not summary_result:
                    return jsonify({
                        "success": False,
                        "message": "未找到用户偏好总结",
                        "response_time": f"{time.time() - start_time:.3f}s"
                    }), 404
                    
                user_summary = summary_result[0]
                
                # 构建新的system prompt
                new_system_prompt = f"""你是一个智能助手。

用户偏好总结:
{user_summary}

请在回答时考虑用户的以上偏好特征,提供更加个性化的建议。"""

                # 获取请求数据中的agent_id
                data = request.get_json()
                agent_id = data.get('agent_id')
                
                if agent_id:
                    # 如果指定了agent_id,只更新该agent
                    if agent_id in self.agents:
                        self.agents[agent_id].update_system_prompt(new_system_prompt)
                        print(f"已更新agent {agent_id}的prompt")
                    else:
                        return jsonify({
                            "success": False,
                            "message": f"未找到指定的agent: {agent_id}",
                            "response_time": f"{time.time() - start_time:.3f}s"
                        }), 404
                else:
                    if updated_count == 0:
                        print(f"未找到与用户{openid}关联的agent")
                
                return jsonify({
                    "success": True,
                    "message": "用户偏好已更新到AI系统",
                    "data": {
                        "summary": user_summary,
                        "updated_agents": updated_count if not agent_id else 1
                    },
                    "response_time": f"{time.time() - start_time:.3f}s"
                })

        except sqlite3.Error as e:
            print(f"数据库操作错误: {str(e)}")
            return jsonify({
                "success": False,
                "message": "数据库操作失败",
                "details": str(e),
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 500
            
        except Exception as e:
            print(f"更新用户偏好错误: {str(e)}")
            return jsonify({
                "success": False,
                "message": "更新用户偏好失败",
                "details": str(e),
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 500

    def user_profile(self):
        """处理用户档案的获取更新"""
        if request.method == 'GET':
            return self.get_user_profile()
        else:  # POST
            return self.update_user_profile()

    def get_user_profile(self):
        """获取用户档案"""
        start_time = time.time()
        
        try:
            # 验证token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                print("验证失败: 缺少或无效的Authorization header")
                return jsonify({
                    "success": False,
                    "message": "未授权的访问",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 401

            token = auth_header.split(' ')[1]
            
            try:
                with sqlite3.connect('vibebite.db') as conn:
                    cursor = conn.cursor()
                    # 获取openid
                    cursor.execute('SELECT openid FROM sessions WHERE token = ?', (token,))
                    result = cursor.fetchone()
                    if not result:
                        print(f"验失败: 无效的token: {token}")
                        return jsonify({
                            "success": False,
                            "message": "无效或过期的token",
                            "response_time": f"{time.time() - start_time:.3f}s"
                        }), 401
                    
                    openid = result[0]
                    
                    # 获取用户档案
                    cursor.execute('''
                        SELECT constellation, hometown, body_type, allergies, 
                               spicy_preference, other_allergy
                        FROM user_profiles
                        WHERE openid = ?
                    ''', (openid,))
                    
                    profile_result = cursor.fetchone()
                    
                    if profile_result:
                        profile_data = {
                            'constellation': profile_result[0],
                            'hometown': profile_result[1],
                            'bodyType': profile_result[2],
                            'allergies': profile_result[3].split(',') if profile_result[3] else [],
                            'spicyPreference': profile_result[4],
                            'otherAllergy': profile_result[5]
                        }
                    else:
                        profile_data = {
                            'constellation': '',
                            'hometown': '',
                            'bodyType': '',
                            'allergies': [],
                            'spicyPreference': 0,
                            'otherAllergy': ''
                        }

                    return jsonify({
                        "success": True,
                        "data": {
                            "openid": openid,
                            "profile": profile_data
                        },
                        "response_time": f"{time.time() - start_time:.3f}s"
                    })

            except sqlite3.Error as e:
                print(f"数据库操作错误: {str(e)}")
                return jsonify({
                    "success": False,
                    "message": "数据库操作失败",
                    "details": str(e),
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 500

        except Exception as e:
            print(f"获取用户档案错误: {str(e)}")
            return jsonify({
                "success": False,
                "message": "获取用户档案失败",
                "details": str(e),
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 500

    def update_user_profile(self):
        """更新用户档案"""
        start_time = time.time()
        
        try:
            # 打印请求信息
            print("收到更新用户档案请:")
            print("Headers:", dict(request.headers))
            print("Raw Data:", request.get_data(as_text=True))
            
            # 验证token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                print("验证失败: 缺少或无效的Authorization header")
                return jsonify({
                    "success": False,
                    "message": "未授权的访问",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 401

            token = auth_header.split(' ')[1]
            
            try:
                with sqlite3.connect('vibebite.db') as conn:
                    cursor = conn.cursor()
                    # 获取openid
                    cursor.execute('SELECT openid FROM sessions WHERE token = ?', (token,))
                    result = cursor.fetchone()
                    if not result:
                        print(f"验证败: 无效的token: {token}")
                        return jsonify({
                            "success": False,
                            "message": "无效或过期的token",
                            "response_time": f"{time.time() - start_time:.3f}s"
                        }), 401
                    
                    openid = result[0]
                    
                    # 获取并验证请求数据
                    try:
                        profile_data = request.get_json()
                        print("解析的请求数据:", profile_data)
                        
                        # 修改数据库结构以适应新的字段
                        cursor.execute('''
                            CREATE TABLE IF NOT EXISTS user_profiles (
                                openid TEXT PRIMARY KEY,
                                constellation TEXT,
                                hometown TEXT,
                                body_type TEXT,
                                allergies TEXT,
                                spicy_preference INTEGER,
                                other_allergy TEXT,
                                created_at TEXT,
                                updated_at TEXT,
                                FOREIGN KEY (openid) REFERENCES users (openid)
                            )
                        ''')
                        
                        # 将数组转换为字符串
                        allergies_str = ','.join(profile_data.get('allergies', []))
                        
                        # 更新用户档案
                        cursor.execute('''
                            INSERT OR REPLACE INTO user_profiles 
                            (openid, constellation, hometown, body_type, allergies, 
                             spicy_preference, other_allergy, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?,
                                COALESCE((SELECT created_at FROM user_profiles WHERE openid = ?), CURRENT_TIMESTAMP),
                                CURRENT_TIMESTAMP)
                        ''', (
                            openid,
                            profile_data.get('constellation'),
                            profile_data.get('hometown'),
                            profile_data.get('bodyType'),
                            allergies_str,
                            profile_data.get('spicyPreference'),
                            profile_data.get('otherAllergy'),
                            openid
                        ))
                        
                        conn.commit()
                        print(f"用户档案更新成功: openid={openid}")

                        return jsonify({
                            "success": True,
                            "message": "用户档案更新成功",
                            "data": {
                                "openid": openid,
                                "profile": profile_data
                            },
                            "response_time": f"{time.time() - start_time:.3f}s"
                        })

                    except Exception as e:
                        print(f"请求数据处理失败: {str(e)}")
                        return jsonify({
                            "success": False,
                            "message": "无效的请求数据格式",
                            "details": str(e),
                            "response_time": f"{time.time() - start_time:.3f}s"
                        }), 400

            except sqlite3.Error as e:
                print(f"数据库操作错误: {str(e)}")
                return jsonify({
                    "success": False,
                    "message": "数据库操作失败",
                    "details": str(e),
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 500

        except Exception as e:
            print(f"更新用户档案错误: {str(e)}")
            return jsonify({
                "success": False,
                "message": "更新用户档案败",
                "details": str(e),
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 500

    def wx_login(self):
        """处理微信小程序登录请求"""
        start_time = time.time()
        
        try:
            data = request.get_json()
            print("收到登录请求数据:", data)  # 添加日志
            
            code = data.get('code')
            if not code:
                return jsonify({
                    "error": "Missing code",
                    "message": "请求中缺少code参数",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 400

            # 从环境变量获取小程序配置
            load_dotenv()
            APP_ID = os.getenv('WX_APP_ID')
            APP_SECRET = os.getenv('WX_APP_SECRET')
            
            if not APP_ID or not APP_SECRET:
                print("环境变量配置错误: APP_ID或APP_SECRET未设置")  # 添加日志
                return jsonify({
                    "error": "Configuration error",
                    "message": "服务器配置错误",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 500

            # 调用微信的 code2Session 接口
            url = "https://api.weixin.qq.com/sns/jscode2session"
            params = {
                'appid': APP_ID,
                'secret': APP_SECRET,
                'js_code': code,
                'grant_type': 'authorization_code'
            }
            
            print("请求微信接口参:", {**params, 'secret': '******'})  # 添加日志（隐藏secret）
            
            response = requests.get(url, params=params)
            wx_data = response.json()
            print("微信接口返回:", wx_data)  # 添加日志

            if 'errcode' in wx_data:
                error_msg = wx_data.get('errmsg', '未知错误')
                print(f"微信接口错误: {error_msg}")  # 添加日志
                return jsonify({
                    "error": "WeChat API Error",
                    "message": error_msg,
                    "errcode": wx_data.get('errcode'),
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 400

            # 获取openid和session_key
            openid = wx_data.get('openid')
            session_key = wx_data.get('session_key')
            
            if not openid or not session_key:
                print("微信接口返回数据不完整")  # 添加日志
                return jsonify({
                    "error": "Invalid Response",
                    "message": "微信接口返回数据不完整",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 500

            # 生成token
            token = self._generate_session_token(openid, session_key)
            
            # 存会话信息到数据库
            if not self._save_user_session(token, openid):
                return jsonify({
                    "error": "Session Storage Error",
                    "message": "保存会话息失败",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 500

            return jsonify({
                "success": True,
                "token": token,
                "response_time": f"{time.time() - start_time:.3f}s"
            })

        except Exception as e:
            print(f"登录处理异常: {str(e)}")  # 添加日志
            return jsonify({
                "error": "Server Error",
                "message": f"服务器处理异常: {str(e)}",
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 500

    def _generate_session_token(self, openid, session_key):
        """生成会话token"""
        token_str = f"{openid}{session_key}{time.time()}"
        return hashlib.sha256(token_str.encode()).hexdigest()

    def protected_resource(self):
        """受保护的资源访问示例"""
        start_time = time.time()
        
        # 从请求头获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                "error": "No valid authorization token",
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 401

        token = auth_header.split(' ')[1]
        
        # 验证token
        if not hasattr(self, 'session_store') or token not in self.session_store:
            return jsonify({
                "error": "Invalid or expired token",
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 401

        # 处理保护的资源请求
        return jsonify({
            "message": "Access granted to protected resource",
            "openid": self.session_store[token],
            "response_time": f"{time.time() - start_time:.3f}s"
        })

    def user_preferences(self):
        """处理用户偏好的获取和更新"""
        if request.method == 'GET':
            return self.get_preferences()
        else:  # POST
            return self.update_preferences()

    def get_preferences(self):
        """获取用户偏好"""
        start_time = time.time()
        
        try:
            # 验证token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                print("验证失败: 缺少或无效的Authorization header")
                return jsonify({
                    "success": False,
                    "message": "未授权的访问",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 401

            token = auth_header.split(' ')[1]
            
            try:
                with sqlite3.connect('vibebite.db') as conn:
                    cursor = conn.cursor()
                    # 获取openid
                    cursor.execute('SELECT openid FROM sessions WHERE token = ?', (token,))
                    result = cursor.fetchone()
                    if not result:
                        print(f"验证失败: 无效的token: {token}")
                        return jsonify({
                            "success": False,
                            "message": "无效或过期的token",
                            "response_time": f"{time.time() - start_time:.3f}s"
                        }), 401
                    
                    openid = result[0]
                    
                    # 获取用户偏好 - 更新字段名以匹配新的表结构
                    cursor.execute('''
                        SELECT dining_scene, dining_styles, flavor_preferences,
                               alcohol_attitude, restrictions, custom_description,
                               extracted_keywords
                        FROM user_preferences
                        WHERE openid = ?
                    ''', (openid,))
                    
                    preferences_result = cursor.fetchone()
                    
                    if preferences_result:
                        preferences_data = {
                            'diningScene': preferences_result[0],
                            'diningStyles': preferences_result[1].split(',') if preferences_result[1] else [],
                            'flavorPreferences': preferences_result[2].split(',') if preferences_result[2] else [],
                            'alcoholAttitude': preferences_result[3],
                            'restrictions': preferences_result[4],
                            'customDescription': preferences_result[5],
                            'extractedKeywords': preferences_result[6].split(',') if preferences_result[6] else []
                        }
                    else:
                        preferences_data = {
                            'diningScene': '',
                            'diningStyles': [],
                            'flavorPreferences': [],
                            'alcoholAttitude': '',
                            'restrictions': '',
                            'customDescription': '',
                            'extractedKeywords': []
                        }

                    return jsonify({
                        "success": True,
                        "data": {
                            "openid": openid,
                            "preferences": preferences_data
                        },
                        "response_time": f"{time.time() - start_time:.3f}s"
                    })

            except sqlite3.Error as e:
                print(f"数据库操作错误: {str(e)}")
                return jsonify({
                    "success": False,
                    "message": "数据库操作失败",
                    "details": str(e),
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 500

        except Exception as e:
            print(f"获取用户偏好错误: {str(e)}")
            return jsonify({
                "success": False,
                "message": "获取用户偏好失败",
                "details": str(e),
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 500

    def update_preferences(self):
        """更新用户偏好"""
        start_time = time.time()
        
        try:
            # 验证token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                print("验证失败: 缺少或无效的Authorization header")
                return jsonify({
                    "success": False,
                    "message": "未授权的访问",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 401

            token = auth_header.split(' ')[1]
            print(f"当前token: {token}")  # 添加日志
            
            try:
                with sqlite3.connect('vibebite.db') as conn:
                    cursor = conn.cursor()
                    # 获取openid
                    cursor.execute('SELECT openid FROM sessions WHERE token = ?', (token,))
                    result = cursor.fetchone()
                    if not result:
                        print(f"验证失败: 无效的token: {token}")
                        return jsonify({
                            "success": False,
                            "message": "无效或过期的token",
                            "response_time": f"{time.time() - start_time:.3f}s"
                        }), 401
                    
                    openid = result[0]
                    print(f"获取到的openid: {openid}")  # 添加日志
                    
                    try:
                        request_data = request.get_json()
                        print("接收到的原始数据:", request_data)
                        
                        # 从嵌套结构中获取preferences数据
                        preferences_data = request_data.get('preferences', {})
                        print("解析出的preferences数据:", preferences_data)
                        
                        # 将数组转换为字符串
                        dining_styles_str = ','.join(preferences_data.get('diningStyles', []))
                        flavor_preferences_str = ','.join(preferences_data.get('flavorPreferences', []))
                        extracted_keywords_str = ','.join(preferences_data.get('extractedKeywords', []))
                        
                        print("处理后的数据:")
                        print(f"dining_styles_str: {dining_styles_str}")
                        print(f"flavor_preferences_str: {flavor_preferences_str}")
                        print(f"extracted_keywords_str: {extracted_keywords_str}")
                        
                        # 准备插入的数据
                        insert_data = (
                            openid,
                            preferences_data.get('diningScene', ''),
                            dining_styles_str,
                            flavor_preferences_str,
                            preferences_data.get('alcoholAttitude', ''),
                            preferences_data.get('restrictions', ''),
                            preferences_data.get('customDescription', ''),
                            extracted_keywords_str,
                            openid
                        )
                        print(f"准备插入的数据: {insert_data}")
                        
                        # 更新用户偏好
                        cursor.execute('''
                            INSERT OR REPLACE INTO user_preferences 
                            (openid, dining_scene, dining_styles, flavor_preferences,
                             alcohol_attitude, restrictions, custom_description,
                             extracted_keywords, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?,
                                COALESCE((SELECT created_at FROM user_preferences WHERE openid = ?), CURRENT_TIMESTAMP),
                                CURRENT_TIMESTAMP)
                        ''', insert_data)
                        
                        conn.commit()
                        
                        # 验证数据是否保存成功
                        cursor.execute('SELECT * FROM user_preferences WHERE openid = ?', (openid,))
                        saved_data = cursor.fetchone()
                        print(f"保存后的数据: {saved_data}")

                        return jsonify({
                            "success": True,
                            "message": "用户偏好更新成功",
                            "data": {
                                "openid": openid,
                                "preferences": preferences_data,
                                "savedData": {
                                    "diningScene": saved_data[1],
                                    "diningStyles": saved_data[2].split(',') if saved_data[2] else [],
                                    "flavorPreferences": saved_data[3].split(',') if saved_data[3] else [],
                                    "alcoholAttitude": saved_data[4],
                                    "restrictions": saved_data[5],
                                    "customDescription": saved_data[6],
                                    "extractedKeywords": saved_data[7].split(',') if saved_data[7] else []
                                }
                            },
                            "response_time": f"{time.time() - start_time:.3f}s"
                        })

                    except Exception as e:
                        print(f"请求数据处理失败: {str(e)}")
                        print(f"错误详情: {e.__class__.__name__}")
                        return jsonify({
                            "success": False,
                            "message": "无效的请求数据格式",
                            "details": str(e),
                            "response_time": f"{time.time() - start_time:.3f}s"
                        }), 400

            except sqlite3.Error as e:
                print(f"数据库操作错误: {str(e)}")
                return jsonify({
                    "success": False,
                    "message": "数据库操作失败",
                    "details": str(e),
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 500

        except Exception as e:
            print(f"更新用户偏好错误: {str(e)}")
            return jsonify({
                "success": False,
                "message": "更新用户偏好失败",
                "details": str(e),
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 500

    def clear_database(self):
        """清空数据库中的所有数据"""
        try:
            with sqlite3.connect('vibebite.db') as conn:
                cursor = conn.cursor()
                # 清空每个表的数据
                cursor.execute('DELETE FROM users')
                cursor.execute('DELETE FROM sessions')
                cursor.execute('DELETE FROM user_profiles')
                cursor.execute('DELETE FROM user_preferences')
                conn.commit()
                print("数据库已清空")
        except sqlite3.Error as e:
            print(f"清空数据库时发生错误: {str(e)}")

    def get_preferences_summary(self):
        """获取用户餐饮喜好总结"""
        start_time = time.time()
        
        try:
            # 验证token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                print("验证失败: 缺少或无效的Authorization header")
                return jsonify({
                    "success": False,
                    "message": "未授权的访问",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 401

            token = auth_header.split(' ')[1]
            print(f"当前token: {token}")  # 添加日志
            
            try:
                with sqlite3.connect('vibebite.db') as conn:
                    cursor = conn.cursor()
                    
                    # 获取openid
                    cursor.execute('SELECT openid FROM sessions WHERE token = ?', (token,))
                    result = cursor.fetchone()
                    if not result:
                        print(f"验证失败: 无效的token: {token}")
                        return jsonify({
                            "success": False,
                            "message": "无效或过期的token",
                            "response_time": f"{time.time() - start_time:.3f}s"
                        }), 401
                    
                    openid = result[0]
                    print(f"获取到的openid: {openid}")  # 添加日志
                    
                    # 检查表是否存在
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_preferences'")
                    if not cursor.fetchone():
                        print("user_preferences 表不存在")
                        return jsonify({
                            "success": True,
                            "data": {
                                "summary": "系统尚未初始化完成，请稍后再试。",
                                "hasPreferences": False
                            },
                            "response_time": f"{time.time() - start_time:.3f}s"
                        })
                    
                    # 获取用户所有偏好数据
                    cursor.execute('''
                        SELECT * FROM user_preferences WHERE openid = ?
                    ''', (openid,))
                    
                    preferences_result = cursor.fetchone()
                    print(f"完整的偏好数据: {preferences_result}")  # 添加日志
                    
                    if not preferences_result or all(not x for x in preferences_result[1:]):  # 跳过 openid 字段
                        print("偏好数据为空或全部字段为空")
                        return jsonify({
                            "success": True,
                            "data": {
                                "summary": "您还没有设置饮食偏好，请先完成偏好设置，以获取个性化推荐。",
                                "hasPreferences": False
                            },
                            "response_time": f"{time.time() - start_time:.3f}s"
                        })
                    
                    # 获取列名
                    cursor.execute('PRAGMA table_info(user_preferences)')
                    columns = [column[1] for column in cursor.fetchall()]
                    print(f"表的列名: {columns}")  # 添加日志
                    
                    # 构建字典形式的数据
                    preferences_dict = dict(zip(columns, preferences_result))
                    print(f"字典形式的数: {preferences_dict}")  # 添加日志
                    
                    # 构建用户偏好数据
                    preferences_data = {
                        'diningScene': preferences_dict.get('dining_scene', ''),
                        'diningStyles': preferences_dict.get('dining_styles', '').split(',') if preferences_dict.get('dining_styles') else [],
                        'flavorPreferences': preferences_dict.get('flavor_preferences', '').split(',') if preferences_dict.get('flavor_preferences') else [],
                        'alcoholAttitude': preferences_dict.get('alcohol_attitude', ''),
                        'restrictions': preferences_dict.get('restrictions', ''),
                        'customDescription': preferences_dict.get('custom_description', ''),
                        'extractedKeywords': preferences_dict.get('extracted_keywords', '').split(',') if preferences_dict.get('extracted_keywords') else []
                    }
                    
                    print(f"处理后的偏好数据: {preferences_data}")  # 添加日志

                    # 如果所有值都为空，返回未设置信息
                    if all(not v for v in preferences_data.values()):
                        return jsonify({
                            "success": True,
                            "data": {
                                "summary": "您还没有设置饮食偏好，请先完成偏好设置，以获取个性化推荐。",
                                "hasPreferences": False
                            },
                            "response_time": f"{time.time() - start_time:.3f}s"
                        })

                    # 构建提示词
                    prompt = f"""请根据以下用户信息，总结该用户的餐饮喜好特征和个性化推荐建议：

用户用餐偏好：
- 用餐场景：{preferences_data['diningScene']}
- 用餐方式：{', '.join(preferences_data['diningStyles'])}
- 口味偏好：{', '.join(preferences_data['flavorPreferences'])}
- 饮酒态度：{preferences_data['alcoholAttitude']}

特殊需求：
- 饮食限制：{preferences_data['restrictions'] if preferences_data['restrictions'] else '无'}
- 自定义描述：{preferences_data['customDescription']}
- 关键词：{', '.join(preferences_data['extractedKeywords'])}

请从以下几个方面进行分析和总结：
1. 用户的主要用餐特征和场景偏好
2. 口味和用餐方式特点
3. 饮品选择倾向
4. 个性化推荐建

请用简洁专业的语言描述，突出关键特点。回答要分点并且要有具体的推荐。"""

                    # 调用大模型生成总结
                    request_id = str(uuid.uuid4())
                    self.llm_client.add_request(openid, "", prompt, request_id)
                    response = ""
                    for _ in range(100):
                        response = self.llm_client.get_chat(request_id)
                        summary = response['response'].choices[0].message.content
                        if summary != "没有找到响应":
                            break
                        time.sleep(0.1)
                    
                    # 创建或更新summary表
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS preference_summaries (
                            openid TEXT PRIMARY KEY,
                            summary TEXT,
                            created_at TEXT,
                            updated_at TEXT,
                            FOREIGN KEY (openid) REFERENCES users (openid)
                        )
                    ''')
                    
                    # 保存总结
                    cursor.execute('''
                        INSERT OR REPLACE INTO preference_summaries 
                        (openid, summary, created_at, updated_at)
                        VALUES (?, ?, 
                            COALESCE((SELECT created_at FROM preference_summaries WHERE openid = ?), CURRENT_TIMESTAMP),
                            CURRENT_TIMESTAMP)
                    ''', (openid, summary, openid))
                    
                    conn.commit()
                    
                    return jsonify({
                        "success": True,
                        "data": {
                            "summary": summary,
                            "hasPreferences": True  # 添加标志位表示有偏好数据
                        },
                        "response_time": f"{time.time() - start_time:.3f}s"
                    })

            except sqlite3.Error as e:
                print(f"数据库操作错误: {str(e)}")
                return jsonify({
                    "success": False,
                    "message": "数据库操作失败",
                    "details": str(e),
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 500

        except Exception as e:
            print(f"生成用户偏好总结错误: {str(e)}")
            return jsonify({
                "success": False,
                "message": "生成用户偏好总结失败",
                "details": str(e),
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 500

    def get_recommendations(self):
        """获取餐厅推荐信息"""
        start_time = time.time()
        
        try:
            # 验证token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    "success": False,
                    "message": "未授权的访问",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 401

            token = auth_header.split(' ')[1]
            
            try:
                data = request.get_json()
                location = data.get('location', '深圳')
                messages = data.get('messages', [])
                timestamp = data.get('timestamp')
                agent_id = data.get('agentId')
                
                print(f"当前agents: {self.agents.keys()}")  # 打印所有agent keys
                print(f"请求的agent_id: {agent_id}")  # 打印请求的agent_id
                
                # 获取agent的对话历史
                if agent_id not in self.agents:
                    print(f"未找到agent_id: {agent_id}")
                    return jsonify({
                        "success": False,
                        "message": f"未找到指定的agent: {agent_id}",
                        "response_time": f"{time.time() - start_time:.3f}s"
                    }), 404
                
                agent = self.agents[agent_id]
                chat_history = agent.memory
                print(f"对话历史: {chat_history}")
                
                # 分析用户意图
                memory_text = "\n".join([
                    f"用户: {msg['user_input']}\nAI: {msg['agent_output']}"
                    for msg in chat_history[-5:]  # 只使用最近5条记录
                ])
                
                # 使用agent的process_recommend_task方法分析意图
                intent_analysis = agent.process_recommend_task("intent_summary", memory_text)
                print(f"意图分析结果: {intent_analysis}")
                
                try:
                    # 将字符串形式的列表转换为Python列表
                    intent_list = eval(intent_analysis)
                    if not isinstance(intent_list, list):
                        raise ValueError("意图分析结果不是列表格式")
                except Exception as e:
                    print(f"意图分析结果格式错误: {str(e)}")
                    intent_list = ["用餐"]  # 默认意图
                
                recommendations = []
                images = []
                location = "深圳"
                # 根据每个意图进行搜索
                for intent in intent_list:
                    search_query = f"{intent} {location} 小红书推荐"
                    print(f"搜索关键词: {search_query}")
                    
                    # ���用Google搜索API
                    google_api_url = "https://google.serper.dev/search"
                    headers = {
                        'X-API-KEY': '5e0ade74a776ca00770d7155a6ed361f25fde09a',
                        'Content-Type': 'application/json'
                    }
                    search_data = {
                        "q": search_query,
                        "gl": "cn",
                        "hl": "zh-cn",
                        "location": "中国"
                    }
                    
                    try:
                        response = requests.post(google_api_url, headers=headers, json=search_data, timeout=5)
                        search_results = response.json()
                        print(f"搜索结果: {search_results}")
                        
                        # 处理搜索结果
                        processed_results = self._process_search_results(search_results, intent)
                        recommendations.extend(processed_results)
                        
                        # 处理图片结果
                        if 'images' in search_results:
                            for image in search_results['images'][:3]:  # 每个意图取前3张图
                                images.append({
                                    'title': image.get('title', ''),
                                    'imageUrl': image.get('imageUrl', ''),
                                    'link': image.get('link', ''),
                                    'type': intent
                                })
                            
                    except requests.RequestException as e:
                        print(f"搜索API请求错误: {str(e)}")
                        continue
                
                # 使用大模型整合结果
                if recommendations:
                    organized_results = self._organize_recommendations(recommendations, intent_list)
                else:
                    organized_results = {"error": "未找到相关推荐"}
                
                return jsonify({
                    "success": True,
                    "data": {
                        "intent_analysis": intent_list,
                        "recommendations": organized_results,
                        "images": images,
                        "searchParameters": {
                            "location": location,
                            "timestamp": timestamp
                        }
                    },
                    "response_time": f"{time.time() - start_time:.3f}s"
                })

            except Exception as e:
                print(f"处理推荐请求错误: {str(e)}")
                return jsonify({
                    "success": False,
                    "message": "获取推荐信息失败",
                    "details": str(e),
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 500

        except Exception as e:
            print(f"获取推荐信息错误: {str(e)}")
            return jsonify({
                "success": False,
                "message": "获取推荐信息失败",
                "details": str(e),
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 500

    def save_shared_session(self):
        """保存分享会话"""
        start_time = time.time()
        
        try:
            # 验证token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    "success": False,
                    "message": "未授权的访问",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 401

            token = auth_header.split(' ')[1]
            
            try:
                with sqlite3.connect('vibebite.db') as conn:
                    cursor = conn.cursor()
                    # 获取openid
                    cursor.execute('SELECT openid FROM sessions WHERE token = ?', (token,))
                    result = cursor.fetchone()
                    if not result:
                        return jsonify({
                            "success": False,
                            "message": "无效或过期的token",
                            "response_time": f"{time.time() - start_time:.3f}s"
                        }), 401
                    
                    openid = result[0]
                    
                    # 获取请求数据
                    data = request.get_json()
                    share_id = data.get('shareId')
                    messages = json.dumps(data.get('messages', []), ensure_ascii=False)
                    recommendations = json.dumps(data.get('recommendations', []), ensure_ascii=False)
                    timestamp = data.get('timestamp')
                    
                    # 保存分享会话
                    cursor.execute('''
                        INSERT OR REPLACE INTO shared_sessions 
                        (share_id, openid, messages, recommendations, timestamp, created_at)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (share_id, openid, messages, recommendations, timestamp))
                    
                    conn.commit()
                    
                    return jsonify({
                        "success": True,
                        "message": "分享会话保存成功",
                        "data": {
                            "shareId": share_id
                        },
                        "response_time": f"{time.time() - start_time:.3f}s"
                    })

            except sqlite3.Error as e:
                print(f"数据库操作错误: {str(e)}")
                return jsonify({
                    "success": False,
                    "message": "数据库操作失败",
                    "details": str(e),
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 500

        except Exception as e:
            print(f"保存分享会话错误: {str(e)}")
            return jsonify({
                "success": False,
                "message": "保存分享会话失败",
                "details": str(e),
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 500

    def get_shared_session(self, share_id):
        """获取分享会话"""
        start_time = time.time()
        
        try:
            with sqlite3.connect('vibebite.db') as conn:
                cursor = conn.cursor()
                
                # 获取分享会话数据
                cursor.execute('''
                    SELECT s.messages, s.recommendations, s.timestamp, 
                           u.nickname, u.avatar
                    FROM shared_sessions s
                    LEFT JOIN users u ON s.openid = u.openid
                    WHERE s.share_id = ?
                ''', (share_id,))
                
                result = cursor.fetchone()
                if not result:
                    return jsonify({
                        "success": False,
                        "message": "分享会话不存在",
                        "response_time": f"{time.time() - start_time:.3f}s"
                    }), 404
                
                messages = json.loads(result[0])
                recommendations = json.loads(result[1])
                timestamp = result[2]
                original_user = {
                    "nickName": result[3] or "匿名用户",
                    "avatarUrl": result[4] or ""
                }
                
                return jsonify({
                    "success": True,
                    "data": {
                        "messages": messages,
                        "recommendations": recommendations,
                        "timestamp": timestamp,
                        "originalUser": original_user
                    },
                    "response_time": f"{time.time() - start_time:.3f}s"
                })

        except Exception as e:
            print(f"获取分享会话错误: {str(e)}")
            return jsonify({
                "success": False,
                "message": "获取分享会话失败",
                "details": str(e),
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 500

    def _process_search_results(self, results: dict, result_type: str) -> list:
        """处理搜索结果,包括抓取网页内容"""
        processed_results = []
        if 'organic' in results:
            for result in results['organic'][:1]:  # 只取前1个结果
                try:
                    # 获取网页内容
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive'
                    }
                    response = requests.get(result.get('link', ''), headers=headers, timeout=5)
                    response.encoding = response.apparent_encoding  # 自动检测编码
                    
                    # 使用BeautifulSoup解析网页
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 基本信息提取
                    page_content = {
                        'title': soup.title.string if soup.title else result.get('title', ''),
                        'description': result.get('snippet', ''),
                        'link': result.get('link', ''),
                        'type': result_type,
                        'position': result.get('position', 0),
                        'details': {},
                        'metadata': {
                            'source': self._extract_domain(result.get('link', '')),
                            'last_updated': self._extract_date(soup),
                            'keywords': self._extract_meta_keywords(soup)
                        }
                    }
                    
                    # 根据不同网站类型提取信息
                    domain = self._extract_domain(result.get('link', ''))
                    if 'dianping.com' in domain:
                        page_content['details'] = self._extract_dianping_info(soup)
                    elif 'meituan.com' in domain:
                        page_content['details'] = self._extract_meituan_info(soup)
                    elif 'ctrip.com' in domain or 'trip.com' in domain:
                        page_content['details'] = self._extract_ctrip_info(soup)
                    elif 'xiaohongshu.com' in domain:
                        page_content['details'] = self._extract_xiaohongshu_info(soup)
                    else:
                        page_content['details'] = self._extract_general_info(soup)
                    
                    # 提取联系信息
                    contact_info = self._extract_contact_info(soup)
                    if contact_info:
                        page_content['details']['contact'] = contact_info
                    
                    # 提取位置信息
                    location_info = self._extract_location_info(soup)
                    if location_info:
                        page_content['details']['location'] = location_info
                    
                    # 提取营业时间
                    business_hours = self._extract_business_hours(soup)
                    if business_hours:
                        page_content['details']['business_hours'] = business_hours
                    
                    # 提取价格信息
                    price_info = self._extract_price_info(soup)
                    if price_info:
                        page_content['details']['price'] = price_info
                    
                    # 提取图片
                    images = self._extract_images(soup)
                    if images:
                        page_content['details']['images'] = images
                    
                    processed_results.append(page_content)
                    print(f"成功处理页面: {result.get('link', '')}")
                    
                except Exception as e:
                    print(f"处理页面失败: {str(e)}")
                    # 如果抓取失败,仍然添加基本信息
                    processed_results.append({
                        'title': result.get('title', ''),
                        'description': result.get('snippet', ''),
                        'link': result.get('link', ''),
                        'type': result_type,
                        'position': result.get('position', 0),
                        'details': {},
                        'error': str(e)
                    })
                    
        return processed_results

    def _extract_domain(self, url: str) -> str:
        """从URL中提取域名"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return url

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """提取页面更新日期"""
        try:
            # 尝试多种可能的日期标签
            date_tags = soup.find_all(['time', 'span', 'div'], class_=['date', 'time', 'update-time'])
            for tag in date_tags:
                if tag.string:
                    return tag.string.strip()
            return ""
        except:
            return ""

    def _extract_meta_keywords(self, soup: BeautifulSoup) -> list:
        """提取页面关键词"""
        try:
            keywords = soup.find('meta', {'name': 'keywords'})
            if keywords and keywords.get('content'):
                return [k.strip() for k in keywords['content'].split(',')]
            return []
        except:
            return []

    def _extract_contact_info(self, soup: BeautifulSoup) -> dict:
        """提取联系信息"""
        contact_info = {
            'phone': '',
            'email': '',
            'social_media': [],
            'website': ''
        }
        
        try:
            # 电话号码
            phone_patterns = [
                r'\d{3}[-.]?\d{3}[-.]?\d{4}',  # 标准电话格式
                r'\d{2,4}[-.]?\d{7,8}'  # 座机格式
            ]
            for pattern in phone_patterns:
                phones = re.findall(pattern, soup.text)
                if phones:
                    contact_info['phone'] = phones[0]
                    break
            
            # 邮箱
            email_pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
            emails = re.findall(email_pattern, soup.text)
            if emails:
                contact_info['email'] = emails[0]
            
            # 社交媒体链接
            social_patterns = ['weibo.com', 'weixin', 'douyin.com']
            for link in soup.find_all('a', href=True):
                for pattern in social_patterns:
                    if pattern in link['href']:
                        contact_info['social_media'].append(link['href'])
            
            return contact_info
        except:
            return contact_info

    def _extract_location_info(self, soup: BeautifulSoup) -> dict:
        """提取位置信息"""
        location_info = {
            'address': '',
            'district': '',
            'city': '',
            'coordinates': {'lat': '', 'lng': ''}
        }
        
        try:
            # 地址
            address_tags = soup.find_all(['div', 'span'], class_=['address', 'location', 'add'])
            for tag in address_tags:
                if tag.string and len(tag.string.strip()) > 5:
                    location_info['address'] = tag.string.strip()
                    break
            
            # 坐标
            map_div = soup.find('div', class_=['map', 'amap'])
            if map_div:
                lat = map_div.get('data-lat')
                lng = map_div.get('data-lng')
                if lat and lng:
                    location_info['coordinates'] = {'lat': lat, 'lng': lng}
            
            return location_info
        except:
            return location_info

    def _extract_business_hours(self, soup: BeautifulSoup) -> dict:
        """提取营业时间"""
        hours_info = {
            'regular_hours': {},
            'holiday_hours': '',
            'special_notes': ''
        }
        
        try:
            # 常规营业时间
            hours_tags = soup.find_all(['div', 'span'], class_=['hours', 'time', 'business-hours'])
            for tag in hours_tags:
                if tag.string and ('营业' in tag.string or '时间' in tag.string):
                    hours_info['regular_hours'] = tag.string.strip()
                    break
            
            # 节假日时间
            holiday_tags = soup.find_all(['div', 'span'], class_=['holiday', 'special-hours'])
            for tag in holiday_tags:
                if tag.string:
                    hours_info['holiday_hours'] = tag.string.strip()
                    break
            
            return hours_info
        except:
            return hours_info

    def _extract_price_info(self, soup: BeautifulSoup) -> dict:
        """提取价格信息"""
        price_info = {
            'price_range': '',
            'average_cost': '',
            'special_offers': []
        }
        
        try:
            # 价格区间
            price_tags = soup.find_all(['div', 'span'], class_=['price', 'cost', 'avg-price'])
            for tag in price_tags:
                if tag.string and ('元' in tag.string or '¥' in tag.string):
                    price_info['price_range'] = tag.string.strip()
                    break
            
            # 特别优惠
            offer_tags = soup.find_all(['div', 'span'], class_=['offer', 'discount', 'promotion'])
            for tag in offer_tags:
                if tag.string:
                    price_info['special_offers'].append(tag.string.strip())
            
            return price_info
        except:
            return price_info

    def _extract_images(self, soup: BeautifulSoup) -> list:
        """提取图片信息"""
        images = []
        try:
            # 查找所有图片标签
            img_tags = soup.find_all('img')
            for img in img_tags:
                # 过滤掉小图标和广告
                if img.get('src') and not any(x in img.get('src', '') for x in ['icon', 'logo', 'ad']):
                    image_info = {
                        'url': img.get('src', ''),
                        'alt': img.get('alt', ''),
                        'title': img.get('title', '')
                    }
                    # 检查图片尺寸
                    if img.get('width') and img.get('height'):
                        if int(img.get('width', 0)) > 100 and int(img.get('height', 0)) > 100:
                            images.append(image_info)
                    else:
                        images.append(image_info)
            
            return images[:5]  # 只返回前5张图片
        except:
            return images

    def _organize_recommendations(self, recommendations: list, intent_list: list) -> dict:
        """整合并组织推荐结果"""
        try:
            # 构建提示词
            organize_prompt = f"""基于以下用户意图和搜索结果，制定一个合理的行程安排：

用户意图：
{', '.join(intent_list)}

搜索结果：
{json.dumps(recommendations, ensure_ascii=False, indent=2)}

请提供：
1. 时间安排建议：-
2. 具体场所推荐（包含地址和特色）：-
3. 交通建议：-
4. 其他注意事项：-

请确保每个部分都以数字编号开头，突出重点信息。每个推荐地点要包含具体的地址和特色。"""

            # 调用大模型整合结果
            request_id = str(uuid.uuid4())
            self.llm_client.add_request("system", "", organize_prompt, request_id)
            
            organized_result = ""
            for _ in range(100):
                response = self.llm_client.get_chat(request_id)
                organized_result = response['response'].choices[0].message.content
                if organized_result != "没有找到响应":
                    break
                time.sleep(0.1)
            
            return {
                "original_recommendations": recommendations,
                "organized_plan": organized_result,
                "intents": intent_list
            }
            
        except Exception as e:
            print(f"整合推荐结果错误: {str(e)}")
            return {
                "error": "整合推荐结果失败",
                "details": str(e),
                "original_recommendations": recommendations,
                "intents": intent_list
            }

    def _extract_general_info(self, soup: BeautifulSoup) -> dict:
        """提取通用网页信息"""
        details = {
            'main_content': '',
            'images': [],
            'contact': '',
            'rating': '',
            'price': '',
            'address': '',
            'features': []
        }
        
        try:
            # 提取主要内容
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
            if main_content:
                details['main_content'] = main_content.text.strip()[:500]  # 限制长度
                
            # 提取图片
            img_elems = soup.find_all('img')
            details['images'] = [img.get('src') for img in img_elems if img.get('src')][:5]  # 只取前5张图
            
            # 提取评分
            rating_elem = soup.find(['div', 'span'], class_=['rating', 'score', 'star'])
            if rating_elem:
                details['rating'] = rating_elem.text.strip()
                
            # 提取价格
            price_elem = soup.find(['div', 'span'], class_=['price', 'cost'])
            if price_elem:
                details['price'] = price_elem.text.strip()
                
            # 提取地址
            address_elem = soup.find(['div', 'span'], class_=['address', 'location'])
            if address_elem:
                details['address'] = address_elem.text.strip()
                
            # 提取特色标签
            feature_elems = soup.find_all(['div', 'span'], class_=['tag', 'feature', 'label'])
            details['features'] = [elem.text.strip() for elem in feature_elems if elem.text.strip()][:5]
                
        except Exception as e:
            print(f"提取通用信息失败: {str(e)}")
            
        return details

    def _extract_dianping_info(self, soup: BeautifulSoup) -> dict:
        """提取大众点评页面信息"""
        details = {
            'rating': '',
            'price': '',
            'address': '',
            'categories': [],
            'popular_dishes': [],
            'business_hours': '',
            'reviews': []
        }
        
        try:
            # 提取评分
            rating_elem = soup.find('div', class_='star')
            if rating_elem:
                details['rating'] = rating_elem.text.strip()
                
            # 提取价格
            price_elem = soup.find('div', class_='price')
            if price_elem:
                details['price'] = price_elem.text.strip()
                
            # 提取地址
            address_elem = soup.find('div', class_='address')
            if address_elem:
                details['address'] = address_elem.text.strip()
                
            # 提取分类
            category_elems = soup.find_all('div', class_='tag')
            details['categories'] = [elem.text.strip() for elem in category_elems]
            
            # 提取热门菜品
            dish_elems = soup.find_all('div', class_='recommend-dish')
            details['popular_dishes'] = [elem.text.strip() for elem in dish_elems]
            
            # 提取营业时间
            hours_elem = soup.find('div', class_='business-hours')
            if hours_elem:
                details['business_hours'] = hours_elem.text.strip()
                
            # 提取评论
            review_elems = soup.find_all('div', class_='review-item')
            for elem in review_elems[:3]:  # 只取前3条评论
                review_text = elem.find('div', class_='review-text')
                if review_text:
                    details['reviews'].append(review_text.text.strip())
                    
        except Exception as e:
            print(f"提取大众点评信息失败: {str(e)}")
            
        return details

    def _extract_meituan_info(self, soup: BeautifulSoup) -> dict:
        """提取美团页面信息"""
        details = {
            'rating': '',
            'price': '',
            'address': '',
            'categories': [],
            'features': [],
            'business_hours': '',
            'promotions': []
        }
        
        try:
            # 提取评分
            rating_elem = soup.find(['div', 'span'], class_=['rating', 'score'])
            if rating_elem:
                details['rating'] = rating_elem.text.strip()
                
            # 提取价格
            price_elem = soup.find(['div', 'span'], class_=['price', 'avg-price'])
            if price_elem:
                details['price'] = price_elem.text.strip()
                
            # 提取地址
            address_elem = soup.find(['div', 'span'], class_=['address', 'location'])
            if address_elem:
                details['address'] = address_elem.text.strip()
                
            # 提取分类和特色
            tag_elems = soup.find_all(['div', 'span'], class_=['tag', 'label'])
            for elem in tag_elems:
                text = elem.text.strip()
                if text:
                    if len(text) <= 4:  # 短标签作为分类
                        details['categories'].append(text)
                    else:  # 长标签作为特色
                        details['features'].append(text)
                        
            # 提取营业时间
            hours_elem = soup.find(['div', 'span'], class_=['business-hours', 'time'])
            if hours_elem:
                details['business_hours'] = hours_elem.text.strip()
                
            # 提取优惠信息
            promo_elems = soup.find_all(['div', 'span'], class_=['promotion', 'discount'])
            details['promotions'] = [elem.text.strip() for elem in promo_elems if elem.text.strip()]
            
        except Exception as e:
            print(f"提取美团信息失败: {str(e)}")
            
        return details

    def _extract_xiaohongshu_info(self, soup: BeautifulSoup) -> dict:
        """提取小红书页面信息"""
        details = {
            'title': '',
            'author': '',
            'content': '',
            'likes': '',
            'comments': '',
            'tags': [],
            'images': []
        }
        
        try:
            # 提取标题
            title_elem = soup.find(['h1', 'div'], class_=['title', 'note-title'])
            if title_elem:
                details['title'] = title_elem.text.strip()
                
            # 提取作者
            author_elem = soup.find(['div', 'span'], class_=['author', 'nickname'])
            if author_elem:
                details['author'] = author_elem.text.strip()
                
            # 提取正文
            content_elem = soup.find('div', class_=['content', 'note-content'])
            if content_elem:
                details['content'] = content_elem.text.strip()
                
            # 提取互动数据
            likes_elem = soup.find(['div', 'span'], class_=['likes', 'like-count'])
            if likes_elem:
                details['likes'] = likes_elem.text.strip()
                
            comments_elem = soup.find(['div', 'span'], class_=['comments', 'comment-count'])
            if comments_elem:
                details['comments'] = comments_elem.text.strip()
                
            # 提取标签
            tag_elems = soup.find_all(['div', 'span'], class_=['tag', 'hashtag'])
            details['tags'] = [elem.text.strip() for elem in tag_elems if elem.text.strip()]
            
            # 提取图片
            img_elems = soup.find_all('img', class_=['note-img', 'image'])
            details['images'] = [img.get('src') for img in img_elems if img.get('src')]
            
        except Exception as e:
            print(f"提取小红书信息失败: {str(e)}")
            
        return details

# 创建服实例
service = AgentChatService()
service.clear_database()

if __name__ == '__main__':
    asyncio.run(service.run()) 
    service.run_flask(port=8080)
