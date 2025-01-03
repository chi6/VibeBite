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
import random
from urllib.parse import urlparse, urljoin

class AgentChatService:
    def __init__(self):
        self.app = Flask(__name__)
        self.llm_client = None
        self.prompt_manager = None
        self.rag_tools = None
        self.agents: Dict[str, Agent] = {}
        self.groups: Dict[str, Group] = {}
        self.location = None
        
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
        self.app.route('/ai_status', methods=['POST'])(self.ai_status)
        self.app.route('/api/login', methods=['POST'])(self.wx_login)
        self.app.route('/api/protected_resource', methods=['GET'])(self.protected_resource)
        self.app.route('/api/user/profile', methods=['GET', 'POST'])(self.user_profile)
        self.app.route('/api/preferences', methods=['POST'])(self.update_preferences)
        self.app.route('/api/preferences/summary', methods=['POST'])(self.get_preferences_summary)
        self.app.route('/api/recommendations', methods=['POST'])(self.get_recommendations)
        self.app.route('/api/share/save', methods=['POST'])(self.save_shared_session)
        self.app.route('/api/share/<share_id>', methods=['GET'])(self.get_shared_session)
        self.app.route('/api/update_pref', methods=['POST'])(self.update_user_preferences)
        self.app.route('/api/wx/openid', methods=['POST'])(self.get_wx_openid)
        self.app.route('/api/ai/get_settings', methods=['POST'])(self.get_ai_settings)
        self.app.route('/api/ai/update_settings', methods=['POST'])(self.update_ai_settings)
        self.app.route('/api/feedback', methods=['POST'])(self.save_feedback)
        self.app.route('/api/preferences/history', methods=['POST'])(self.get_preferences_history)

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
            "status_check": """请根据你的设定返回当前AI状态,包含mood, activity, thought, 分别表示心情、活跃度、正在思考的内容。
请用json格式返回，注意：
1. 每一个字段都要是中文且有值
2. 返回的内容要符合你的性格特征和说话风格
3. 在thought中可以提到你的重要记忆""",
            "intent_summary": "你是一个意图分析专家，请根据对话历史，分析用户的意图，提取用户今天的约会期望内容，注意不要出现具体店名，输出大方向类别，结果用list格式返回。如：['吃三文鱼']或['喝鸡尾酒']，要求容易被输入到谷歌搜索。"
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
        try:
            # 创建默认agents - 使用openid_agent_id作为key
            system_openid = "system"
            default_agents = [
                Agent("1", "通用助手", self.llm_client, self.prompt_manager, openid=system_openid),
                Agent("2", "分析专家", self.llm_client, self.prompt_manager, openid=system_openid),
                Agent("3", "领域专家", self.llm_client, self.prompt_manager, openid=system_openid)
            ]
            
            for agent in default_agents:
                # 使用openid_agent_id格式作为key
                agent_key = f"{system_openid}_{agent.agent_id}"
                self.agents[agent_key] = agent
                print(f"初始化agent: {agent_key}")  # 添加日志
                
            # 创建默认group
            default_group = Group("main_group", "主群组")
            for agent in default_agents:
                default_group.add_agent(agent)
            self.groups[default_group.group_id] = default_group
            
            print(f"已初始化的agents: {list(self.agents.keys())}")  # 打印所有初始化的agent keys
            
        except Exception as e:
            print(f"初始化默认agents失败: {str(e)}")
            raise

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
        
        # 使用openid_agent_id格式作为key
        agent_key = f"{openid}"
        print(f"创建agent, key: {agent_key}")  # 添加日志
        
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
        print(f"当前所有agents: {list(self.agents.keys())}")  # 添加日志
        
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
        if not data:
            return jsonify({
                "uniqueId": int(time.time() * 1000000),
                "taskInvoker": None,
                "response": "Invalid JSON"
            }), 400
        
        openid = data.get('openid')  # 直接使用openid
        message = data.get('message')
        task_name = data.get('taskName', 'chat')
        group_id = data.get('groupId', 'main_group')
        
        if openid not in self.agents:
            print(f"未找到openid: {openid}")
            return jsonify({
                "uniqueId": int(time.time() * 1000000),
                "taskInvoker": None,
                "response": f"未找到指定的agent: {openid}"
            }), 404
        
        # 获取响应
        print(f"开始处理任务: {task_name}, 消息: {message}")
        responses = self.agents[openid].process_task(task_name, message)
        
        # 过滤大众点评链接
        if isinstance(responses, str):
            # 移除大众点评链接
            responses = re.sub(r'https?://[^\s]*dianping\.com[^\s]*', '', responses)
            # 移除链接后可能产生的多余空格
            responses = re.sub(r'\s+', ' ', responses).strip()
        
        # 异步触发意图分析
        asyncio.create_task(self.analyze_intent(self.agents[openid], openid))
        
        print(responses)
        return jsonify({
            "uniqueId": int(time.time() * 1000000),
            "taskInvoker": None,
            "response": responses
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
        
        openid = data.get('openid')  # 直接使用openid
        print("agent ids:", self.agents.keys(), "openid:", openid)
        if openid not in self.agents:
            return jsonify({
                "error": "Agent not found",
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 404
        
        status = await self.agents[openid].get_status()
        
        # 从数据库中获取AI名称
        try:
            with sqlite3.connect('vibebite.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM ai_settings WHERE openid = ?', (openid,))
                result = cursor.fetchone()
                ai_name = result[0] if result and result[0] else 'AI智能助手'
        except sqlite3.Error as e:
            print(f"获取AI名称失败: {str(e)}")
            ai_name = 'AI智能助手'  # 如果发生错误，使用默认名称

        return jsonify({
            "name": ai_name,
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
            # 如果数据库文件已存在，先删除
            if os.path.exists(db_path):
                os.remove(db_path)
                print("已删除旧的数据库文件")
            
            # 确保目录存在
            db_dir = os.path.dirname(db_path)
            if not os.path.exists(db_dir):
                print(f"创建目录: {db_dir}")
                os.makedirs(db_dir)
            
            print(f"正在初始化数据库...")
            
            # 创建数据库连接
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
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
                        openid TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (openid) REFERENCES users (openid)
                    )
                ''')
                
                # 添加索引以提高查询性能
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_sessions_openid 
                    ON sessions (openid)
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
                
                # 创建用户偏好表
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
                
                # 创建分享会话表
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
                
                # 创建AI设置表
                print("- 创建 ai_settings 表")
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_settings (
                        openid TEXT PRIMARY KEY,
                        name TEXT,
                        personality TEXT,
                        speaking_style TEXT,
                        memories TEXT,
                        created_at TEXT,
                        updated_at TEXT,
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

    def _save_user_session(self, token: str, openid: str) -> bool:
        """保存用户会话信息到数据库"""
        try:
            with sqlite3.connect('vibebite.db') as conn:
                cursor = conn.cursor()
                # 先删除旧的session
                cursor.execute('DELETE FROM sessions WHERE openid = ?', (openid,))
                # 插入新的session
                cursor.execute(
                    'INSERT INTO sessions (token, openid, created_at) VALUES (?, ?, ?)',
                    (token, openid, datetime.now().isoformat())
                )
                conn.commit()
                print(f"保存session成功: token={token}, openid={openid}")  # 添加日志
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

    def update_preferences(self):
        """更新用户偏好"""
        start_time = time.time()
        
        try:
            data = request.get_json()
            openid = data.get('openid')
            preferences_data = data.get('preferences', {})
            user_input = preferences_data.get('userInput', '')
            timestamp = data.get('timestamp')
            
            if not openid:
                return jsonify({
                    "success": False,
                    "message": "缺少openid参数",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 400
            
            try:
                # 提取关键词
                keywords = [word.strip() for word in user_input.split() if word.strip()]
                keywords_str = ','.join(keywords)
                
                # 更新数据库
                with sqlite3.connect('vibebite.db') as conn:
                    cursor = conn.cursor()
                    
                    # 更新用户偏好,只保存用户输入和关键词
                    cursor.execute('''
                        INSERT OR REPLACE INTO user_preferences 
                        (openid, custom_description, extracted_keywords, created_at, updated_at)
                        VALUES (?, ?, ?,
                            COALESCE((SELECT created_at FROM user_preferences WHERE openid = ?), CURRENT_TIMESTAMP),
                            CURRENT_TIMESTAMP)
                    ''', (
                        openid,
                        user_input,  # 保存原始用户输入
                        keywords_str,  # 保存提取的关键词
                        openid
                    ))
                    
                    conn.commit()
                    
                    return jsonify({
                        "success": True,
                        "message": "用户偏好更新成功",
                        "data": {
                            "originalInput": user_input,
                            "extractedKeywords": keywords
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


    def update_user_preferences(self):
        """更新用户偏好并更新agent的prompt"""
        start_time = time.time()
        print("更新用户偏好")
        try:
            data = request.get_json()
            openid = data.get('openid')  # 直接使用openid
            summary = data.get('summary')
            print("summary: ", summary)
        
            if not openid:
                return jsonify({
                    "success": False,
                    "message": "缺少openid参数",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 400
            
            # 如果有新的summary传入，更新数据库
            if summary:
                try:
                    with sqlite3.connect('vibebite.db') as conn:
                        cursor = conn.cursor()
                        # 更新或插入新的summary
                        cursor.execute('''
                            INSERT OR REPLACE INTO preference_summaries 
                            (openid, summary, created_at, updated_at)
                            VALUES (?, ?, 
                                COALESCE((SELECT created_at FROM preference_summaries WHERE openid = ?), CURRENT_TIMESTAMP),
                                CURRENT_TIMESTAMP)
                        ''', (openid, summary, openid))
                        conn.commit()
                        print(f"已更新用户 {openid} 的偏好总结")
                except sqlite3.Error as e:
                    print(f"更新偏好总结数据库错误: {str(e)}")
                    return jsonify({
                        "success": False,
                        "message": "更新偏好总结失败",
                        "details": str(e),
                        "response_time": f"{time.time() - start_time:.3f}s"
                    }), 500
            
            # 获取用户偏好总结
            with sqlite3.connect('vibebite.db') as conn:
                cursor = conn.cursor()
                
                # 获取用户偏好总结
                cursor.execute('''
                    SELECT summary FROM preference_summaries WHERE openid = ?
                ''', (openid,))
                
                summary_result = cursor.fetchone()
                if not summary_result:
                    return jsonify({
                        "success": False,
                        "message": "请先设置用户偏好",
                        "response_time": f"{time.time() - start_time:.3f}s"
                    }), 404
                
                user_summary = summary_result[0]
                
                # 构建新的system prompt
                new_system_prompt = f"""你是一个智能助手。

用户偏好总结:
{user_summary}

请在回答时考虑用户的以上偏好特征,提供更加个性化的建议。"""

                # 更新agent的prompt
                if openid in self.agents:
                    status_check_prompt = self.prompt_manager.get_prompt("status_check", openid)
                    split_prompt = status_check_prompt.split("请返回")
                    new_system_prompt = split_prompt[0] + "\n" + new_system_prompt
                    self.agents[openid].update_system_prompt("chat", new_system_prompt)
                    print(f"已更新agent {openid}的prompt")
                else:
                    print(f"未找到与用户{openid}关联的agent")
                
                return jsonify({
                    "success": True,
                    "message": "用户偏好已更新到AI系统",
                    "data": {
                        "summary": user_summary,
                        "updatedAgents": 1 if openid in self.agents else 0
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
                        print(f"证败: 无效的token: {token}")
                        return jsonify({
                            "success": False,
                            "message": "无效或过期的token",
                            "response_time": f"{time.time() - start_time:.3f}s"
                        }), 401
                    
                    openid = result[0]
                    
                    # 获取并验证请求数据
                    try:
                        profile_data = request.get_json()
                        print("解析的求数据:", profile_data)
                        
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
                        
                        # 将数组转换为字符
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
            code = data.get('code')
            self.location = data.get('location')
            print("location: ", self.location)
            print("data: ", data)
            if not code:
                return jsonify({
                    "success": False,
                    "message": "缺少code参数",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 400

            # 从环境变量获取小程序配置
            load_dotenv()
            APP_ID = os.getenv('WX_APP_ID')
            APP_SECRET = os.getenv('WX_APP_SECRET')
            print("APP_ID: ", APP_ID, ", APP_SECRET: ", APP_SECRET)
            APP_SECRET = "660e8e6bbcf4fd39490e674fa4bad349"
            
            # 调用微信接口获取openid
            url = "https://api.weixin.qq.com/sns/jscode2session"
            params = {
                'appid': APP_ID,
                'secret': APP_SECRET,
                'js_code': code,
                'grant_type': 'authorization_code'
            }
            
            response = requests.get(url, params=params)
            wx_data = response.json()
            
            if 'errcode' in wx_data:
                return jsonify({
                    "success": False,
                    "message": wx_data.get('errmsg', '获取openid失败'),
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 400
            
            openid = wx_data.get('openid')
            
            # 生成token
            token = self._generate_session_token(openid, wx_data.get('session_key'))
            print(f"生成新token: {token} 对应openid: {openid}")  # 添加日志
            
            # 存储会话信息到数据库
            try:
                with sqlite3.connect('vibebite.db') as conn:
                    cursor = conn.cursor()
                    # 先删除旧的session
                    cursor.execute('DELETE FROM sessions WHERE openid = ?', (openid,))
                    # 插入新的session
                    cursor.execute(
                        'INSERT INTO sessions (token, openid, created_at) VALUES (?, ?, ?)',
                        (token, openid, datetime.now().isoformat())
                    )
                    conn.commit()
                    print(f"保存session成功: token={token}, openid={openid}")
            except Exception as e:
                print(f"保存session失败: {str(e)}")
                return jsonify({
                    "success": False,
                    "message": "保存会话信息失败",
                    "details": str(e),
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 500

            # 检查session是否保存成功
            cursor.execute('SELECT openid FROM sessions WHERE token = ?', (token,))
            if not cursor.fetchone():
                print(f"验证session保存失败: 未找到token {token}")
                return jsonify({
                    "success": False,
                    "message": "会话信息保存验证失败",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 500
            
            # 检查是否已经存在该用户的agent
            agent_key = f"{openid}"  # 默认创建id为1的agent
            if agent_key not in self.agents:
                print(f"为新用户{openid}创建agent")
                # 创建新的agent
                new_agent = Agent(
                    agent_id="1",
                    name="默认助手",
                    llm_client=self.llm_client,
                    prompt_manager=self.prompt_manager,
                    openid=openid
                )
                self.agents[agent_key] = new_agent
                print(f"创建agent成功: {agent_key}")
            
            return jsonify({
                "success": True,
                "token": token,
                "agent_id": "1",  # 返回创建的agent_id
                "response_time": f"{time.time() - start_time:.3f}s"
            })
            
        except Exception as e:
            print(f"登录处理异常: {str(e)}")
            return jsonify({
                "success": False,
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

    def clear_database(self):
        """清空据库中的所有数据"""
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
            data = request.get_json()
            openid = data.get('openid')
            
            if not openid:
                return jsonify({
                    "success": False,
                    "message": "缺少openid参数",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 400
            
            try:
                with sqlite3.connect('vibebite.db') as conn:
                    cursor = conn.cursor()
                    
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
                    
                    # 获取用户偏好数据
                    cursor.execute('''
                        SELECT custom_description, extracted_keywords
                        FROM user_preferences 
                        WHERE openid = ?
                    ''', (openid,))
                    
                    result = cursor.fetchone()
                    
                    if not result or (not result[0] and not result[1]):
                        return jsonify({
                            "success": True,
                            "data": {
                                "summary": "您还没有设置饮食偏好，请先完成偏好设置，以获取个性化推荐。",
                                "hasPreferences": False
                            },
                            "response_time": f"{time.time() - start_time:.3f}s"
                        })
                    
                    user_input = result[0]
                    keywords = result[1].split(',') if result[1] else []
                    
                    # 构建提示词
                    prompt = f"""请根据用户输入，为用户的偏好生成 {self.location} 本地有特点的推荐搭配。猜你喜欢部分：要求根据用户的输入进行扩充和思考，分析用户饮食偏好（口味、场景、风格），喜欢什么样餐厅（环境、菜品、服务），可以有什么样子的行程（时间、地点、活动）。

                    奇思妙想部分：要求根据用户的输入，推荐几个具体餐厅、饮品、活动等，内容多一些，每一段用；分隔。

用户输入：{user_input}
关键词：{', '.join(keywords)}

示例格式：
- **猜你喜欢**：

- **奇思妙想**：

请按照这个格式生成推荐。"""

                    # 调用大模型生成总结
                    request_id = str(uuid.uuid4())
                    self.llm_client.add_request(openid, "", prompt, request_id)
                    
                    summary = ""
                    for _ in range(100):
                        response = self.llm_client.get_chat(request_id)
                        summary = response['response'].choices[0].message.content
                        if summary != "没有找到响应":
                            break
                        time.sleep(0.1)
                    
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
                            "hasPreferences": True,
                            "preferences": {
                                "userInput": user_input,
                                "keywords": keywords
                            }
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
            data = request.get_json()
            location = data.get('location')
            timestamp = data.get('timestamp')
            openid = data.get('openid')
            
            print(f"当前agents: {self.agents.keys()}")
            print(f"请求的openid: {openid}")
            
            if openid not in self.agents:
                print(f"未找到openid: {openid}")
                return jsonify({
                    "success": False,
                    "message": f"未找到指定的agent: {openid}",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 404
            
            agent = self.agents[openid]
            
            # 使用存储的意图分析结果
            intent_list = agent.intent_analysis if agent.intent_analysis else ["用餐"]
            print(f"使用存储的意图分析结果: {intent_list}")
            
            recommendations = []
            images = []
            location = self.location
            # 根据每个意图进行搜索
            for idx, intent in enumerate(intent_list[:3]):
                search_query = f"{intent} {location} 推荐"
                print(f"搜索关键词: {search_query}")
                if True:
                    # 用Google搜索API
                    google_api_url = "https://google.serper.dev/search"
                    headers = {
                        'X-API-KEY': '5e0ade74a776ca00770d7155a6ed361f25fde09a',
                        'Content-Type': 'application/json'
                    }
                    search_data = {
                        "q": search_query,
                        "gl": "cn",
                        "hl": "zh-cn",
                        "location": "中国",
                        "num": 1
                    }
                
                    try:
                        response = requests.post(google_api_url, headers=headers, json=search_data, timeout=5)
                        search_results = response.json()
                        print(f"搜索结果: {search_results}")
                        
                        # 处理搜索结果
                        processed_results = self._process_search_results(search_results, intent)
                        recommendations.extend(processed_results)
                            
                    except requests.RequestException as e:
                            print(f"搜索API请求错误: {str(e)}")
                            continue
                else:
                    recommendations.append(intent)
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
                    "message": "数据库作失败",
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
        """处理搜索结果,包括抓取网页内容和快照"""
        processed_results = []
        if 'organic' in results:
            for result in results['organic'][:1]:  # 只取前1个结果
                try:
                    # 更新请求头,模拟真实浏览器
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Cache-Control': 'max-age=0',
                        'Upgrade-Insecure-Requests': '1'
                    }
                    
                    # 添加随机延迟避免被封
                    time.sleep(random.uniform(1, 3))
                    
                    # 获取网页内容
                    response = requests.get(result.get('link', ''), headers=headers, timeout=5)
                    response.encoding = response.apparent_encoding
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 提取页面基本信息
                    page_content = {
                        'title': soup.title.string if soup.title else result.get('title', ''),
                        'description': result.get('snippet', ''),
                        'link': result.get('link', ''),
                        'type': result_type,
                        'position': result.get('position', 0),
                    }
                    
                    # 提取图片
                    images = []
                    for img in soup.find_all('img'):
                        src = img.get('src', '')
                        if src and not src.startswith('data:'):  # 排除base64图片
                            if not src.startswith(('http://', 'https://')):
                                # 处理相对路径
                                base_url = result.get('link', '')
                                src = urljoin(base_url, src)
                            images.append({
                                'url': src,
                                'alt': img.get('alt', ''),
                                'title': img.get('title', '')
                            })
                    page_content['images'] = images[:5]  # 只保留前5张图片
                    
                    # 提取主要内容
                    main_content = ''
                    content_tags = soup.find_all(['article', 'main', 'div'], class_=re.compile(r'content|article|main|text'))
                    for tag in content_tags:
                        # 清理内容
                        text = tag.get_text(separator='\n', strip=True)
                        text = re.sub(r'\n+', '\n', text)  # 合并多个换行
                        text = re.sub(r'\s+', ' ', text)   # 合并多个空格
                        if len(text) > len(main_content):
                            main_content = text
                    page_content['main_content'] = main_content[:1000]  # 限制长度
                    
                    # 提取结构化数据
                    structured_data = []
                    for script in soup.find_all('script', type='application/ld+json'):
                        try:
                            data = json.loads(script.string)
                            structured_data.append(data)
                        except:
                            continue
                    page_content['structured_data'] = structured_data
                    
                    # 提取联系方式
                    contact_info = {
                        'phone': None,
                        'email': None,
                        'address': None
                    }
                    # 电话号码匹配
                    phone_pattern = re.compile(r'1[3-9]\d{9}|0\d{2,3}-\d{7,8}')
                    phones = phone_pattern.findall(str(soup))
                    if phones:
                        contact_info['phone'] = phones[0]
                        
                    # 邮箱匹配    
                    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
                    emails = email_pattern.findall(str(soup))
                    if emails:
                        contact_info['email'] = emails[0]
                        
                    # 地址匹配
                    address_tags = soup.find_all(['div', 'span', 'p'], class_=re.compile(r'address|location'))
                    if address_tags:
                        contact_info['address'] = address_tags[0].get_text(strip=True)
                        
                    page_content['contact_info'] = contact_info
                    
                    # 提取营业时间
                    hours_tags = soup.find_all(['div', 'span', 'p'], class_=re.compile(r'hours|time|营业时间'))
                    if hours_tags:
                        page_content['business_hours'] = hours_tags[0].get_text(strip=True)
                    
                    # 提取价格信息
                    price_tags = soup.find_all(['div', 'span', 'p'], class_=re.compile(r'price|cost|价格'))
                    if price_tags:
                        page_content['price_info'] = price_tags[0].get_text(strip=True)
                    
                    # 提取评分和评论
                    reviews = []
                    review_tags = soup.find_all(['div', 'article'], class_=re.compile(r'review|comment|评论'))
                    for review in review_tags[:5]:  # 只取前5条评论
                        review_text = review.get_text(strip=True)
                        if len(review_text) > 10:  # 过滤太短的评论
                            reviews.append(review_text)
                    page_content['reviews'] = reviews
                    
                    # 保存网页快照
                    page_content['snapshot'] = {
                        'html': str(soup)[:10000],  # 限制快照大小
                        'timestamp': datetime.now().isoformat()
                    }
                    
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
                        'error': str(e)
                    })
                    
        return processed_results

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

    def get_wx_openid(self):
        """获取微信openid"""
        start_time = time.time()
        
        try:
            data = request.get_json()
            code = data.get('code')
            if not code:
                return jsonify({
                    "success": False,
                    "message": "缺少code参数",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 400

            # 从环境变量获取小程序配置
            load_dotenv()
            APP_ID = os.getenv('WX_APP_ID')
            APP_SECRET = os.getenv('WX_APP_SECRET')
            APP_SECRET = "660e8e6bbcf4fd39490e674fa4bad349"
            
            # 调用微信口获取openid
            url = "https://api.weixin.qq.com/sns/jscode2session"
            params = {
                'appid': APP_ID,
                'secret': APP_SECRET,
                'js_code': code,
                'grant_type': 'authorization_code'
            }
            
            response = requests.get(url, params=params)
            wx_data = response.json()
            
            if 'errcode' in wx_data:
                return jsonify({
                    "success": False,
                    "message": wx_data.get('errmsg', '获取openid失败'),
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 400
            
            return jsonify({
                "success": True,
                "openid": wx_data.get('openid'),
                "response_time": f"{time.time() - start_time:.3f}s"
            })
            
        except Exception as e:
            print(f"获取openid错误: {str(e)}")
            return jsonify({
                "success": False,
                "message": "获取openid失败",
                "details": str(e),
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 500

    def update_ai_settings_prompt(self, openid: str, name: str, personality: str, speaking_style: str, memories: str):
        """更新AI设置"""
        system_prompt = f"""你是一个名叫{name}的AI助手。

性格特征：
{personality}

说话风格：
{speaking_style}

重要记忆：
{memories}

请在对话中始终保持这些特征，提供友好且个性化的回答。"""

        # 构建status_check的特定prompt
        status_check_prompt = f"""你是一个名叫{name}的AI助手。

性格特征：
{personality}

说话风格：
{speaking_style}

重要记忆：
{memories}

请返回当前AI状态,包含mood, activity, thought, 分别表示心情、活跃度、正在思考的内容。
请用json格式返回，注意：
1. 每一个字段都要是中文且有值
2. 返回的内容要符合你的性格特征和说话风格
3. 在thought中可以提到你的重要记忆"""

        # 更新所有与该用户关联的agent的prompts
        agent_keys = [key for key in self.agents.keys() if str(key).startswith(openid)]
        print(f"agent_keys: {agent_keys}")
        for agent_key in agent_keys:
            agent = self.agents[agent_key]
            # 更新通用prompt
            agent.update_system_prompt("status_check", status_check_prompt)
            print(f"已更新agent {agent_key}的prompts")
                
        return system_prompt, status_check_prompt

    def update_ai_settings(self):
        """更新AI设置"""
        start_time = time.time()
        
        try:
            data = request.get_json()
            openid = data.get('openid')
            timestamp = data.get('timestamp')
            name = data.get('name')
            personality = data.get('personality')
            speaking_style = data.get('speaking_style')
            memories = data.get('memories')
            # 将memories列表转换为字符串
            memories_str = json.dumps(memories, ensure_ascii=False) if isinstance(memories, list) else str(memories)
            if not openid:
                return jsonify({
                    "success": False,
                    "message": "缺少openid参数",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 400

            # 构建新的system prompt
            system_prompt = f"""你是一个名叫{name}的AI助手。

性格特征：
{personality}

说话风格：
{speaking_style}

重要记忆：
{memories_str}

请在对话中始终保持这些特征，提供友好且个性化的回答。"""

            # 构建status_check的特定prompt
            status_check_prompt = f"""你是一个名叫{name}的AI助手。

性格特征：
{personality}

说话风格：
{speaking_style}

重要记忆：
{memories_str}

请返回当前AI状态,包含mood, activity, thought, 分别表示心情、活跃度、正在思考的内容。
请用json格式返回，注意：
1. 每一个字段都要是中文且有值
2. 返回的内容要符合你的性格特征和说话风格
3. 在thought中可以提到你的重要记忆"""
            
            # 更新数据库中的AI设置
            with sqlite3.connect('vibebite.db') as conn:
                cursor = conn.cursor()
                
                # 创建ai_settings表（如果不存在）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_settings (
                        openid TEXT PRIMARY KEY,
                        name TEXT,
                        personality TEXT,
                        speaking_style TEXT,
                        memories TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (openid) REFERENCES users (openid)
                    )
                ''')
                # 更新AI设置
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_settings 
                    (openid, name, personality, speaking_style, memories, 
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?,
                        COALESCE((SELECT created_at FROM ai_settings WHERE openid = ?), CURRENT_TIMESTAMP),
                        CURRENT_TIMESTAMP)
                ''', (openid, name, personality, speaking_style, memories_str, openid))
                
                conn.commit()
                
                # 更新所有与该用户关联的agent的prompts
                agent_keys = [key for key in self.agents.keys() if str(key).startswith(openid)]
                print(f"agent_keys: {agent_keys}")
                for agent_key in agent_keys:
                    agent = self.agents[agent_key]
                    # 更新通用prompt
                    agent.update_system_prompt("status_check", status_check_prompt)
                    # 更新status_check的特定prompt
                    #agent.prompt_manager.update_user_prompt(openid, "status_check", status_check_prompt)
                    print(f"已更新agent {agent_key}的prompts")
                
                return jsonify({
                    "success": True,
                    "message": "AI设置更新成功",
                    "data": {
                        "openid": openid,
                        "name": name,
                        "updatedAgents": len(agent_keys)
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
            print(f"更新AI设置错误: {str(e)}")
            return jsonify({
                "success": False,
                "message": "更新AI设置失败",
                "details": str(e),
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 500

    def get_ai_settings(self):
        """获取AI设置"""
        start_time = time.time()
        
        try:
            # 从POST请求体中获取数据，而不是GET参数
            data = request.get_json()
            openid = data.get('openid')
            
            if not openid:
                return jsonify({
                    "success": False,
                    "message": "缺少openid参数",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 400
            
            # 从数据库获取AI设置
            with sqlite3.connect('vibebite.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT name, personality, speaking_style, memories
                    FROM ai_settings 
                    WHERE openid = ?
                ''', (openid,))
                
                result = cursor.fetchone()
                
                if result:
                    settings = {
                        'name': result[0],
                        'personality': result[1],
                        'speakingStyle': result[2],
                        'memories': result[3]
                    }
                else:
                    # 如果没有设置，返回默认值
                    settings = {
                        'name': '默认助手',
                        'personality': '友好、耐心、专业',
                        'speakingStyle': '正式但亲切',
                        'memories': '我是一个AI助手，我的目标是帮助用户解决问题。'
                    }
                
                # 更新AI设置的prompt
                self.update_ai_settings_prompt(
                    openid, 
                    settings['name'], 
                    settings['personality'], 
                    settings['speakingStyle'], 
                    settings['memories']
                )
                print(f"已更新用户 {openid} 的AI设置", settings)
                
                return jsonify({
                    "success": True,
                    "data": settings,
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

    async def analyze_intent(self, agent: Agent, openid: str):
        """异步分析用户意图"""
        try:
            chat_history = agent.memory
            current_count = len(chat_history)
            
            # 检查是否需要更新意图分析（每5条消息更新一次）
            if current_count >= agent.last_analysis_count + 2 or agent.last_analysis_count == 0:
                # 获取最近的对话记录
                memory_text = "\n".join([
                    f"用户: {msg['user_input']}\nAI: {msg['agent_output']}"
                    for msg in chat_history[-2:]
                ])
                
                # 分析意图
                intent_analysis = agent.process_recommend_task("intent_summary", memory_text)
                print(f"新的意图分析结果: {intent_analysis}")
                
                try:
                    # 将字符串形式的列表转换为Python列表
                    intent_list = eval(intent_analysis)
                    if isinstance(intent_list, list):
                        # 更新agent中的意图分析结果
                        agent.intent_analysis = intent_list
                        agent.last_analysis_count = current_count
                        print(f"意图分析已更新: {intent_list}")
                    else:
                        print("意图分析结果格式错误")
                except Exception as e:
                    print(f"处理意图分析结果错误: {str(e)}")
        except Exception as e:
            print(f"意图分析过程错误: {str(e)}")

    def _extract_keywords_from_title(self, title: str) -> list:
        """从标题中提取关键词"""
        # 移除特殊字符和标点
        title = re.sub(r'[【】\[\]()（）]', ' ', title)
        # 分词
        words = title.split()
        # 移除停用词和空字符串
        return [w for w in words if w and len(w) > 1]

    def _organize_recommendations(self, recommendations: list, intent_list: list) -> dict:
        """整合并组织推荐结果"""
        recommendations_str = ""    
        for recommendation in recommendations:
            if "main_content" in recommendation and recommendation["main_content"]:
                print(f"recommendation['main_content']: {recommendation['main_content']}")
                recommendations_str += recommendation["main_content"]
            elif "description" in recommendation and recommendation["description"]:
                print(f"recommendation['description']: {recommendation['description']}")
                recommendations_str += recommendation["description"]
        
        try:
            # 构建提示词
            organize_prompt = f"""基于以下用户意图和搜索结果，制定一个合理的推荐计划：

用户意图：
{', '.join(intent_list)}

搜索结果：
{recommendations_str}

请提供：
1. 具体场所推荐（特色）：- 内容
2. 推荐搭配规划：- 内容

每个推荐要包含具体的店名和特色。"""

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

    def _extract_domain(self, url: str) -> str:
        """从URL中提取域名"""
        try:
            domain = urlparse(url).netloc
            return domain
        except Exception as e:
            print(f"提取域名失败: {str(e)}")
            return "未知域名"

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """从网页中提取日期信息"""
        try:
            # 假设日期信息在<meta>标签中，或者在某个特定的<div>或<span>中
            date_meta = soup.find('meta', {'name': 'date'})
            if date_meta and date_meta.get('content'):
                return date_meta['content']
            
            # 其他可能的日期提取逻辑
            date_div = soup.find('div', class_='date')
            if date_div:
                return date_div.text.strip()
            
            # 如果没有找到，返回默认值
            return "未知日期"
        except Exception as e:
            print(f"提取日期失败: {str(e)}")
            return "未知日期"

    def _extract_meta_keywords(self, soup: BeautifulSoup) -> list:
        """从网页中提取meta关键词"""
        try:
            # 查找<meta>标签中的keywords
            keywords_meta = soup.find('meta', {'name': 'keywords'})
            if keywords_meta and keywords_meta.get('content'):
                keywords = keywords_meta['content'].split(',')
                return [keyword.strip() for keyword in keywords]
            
            # 如果没有找到，返回空列表
            return []
        except Exception as e:
            print(f"提取meta关键词失败: {str(e)}")
            return []

    def save_feedback(self):
        """保存用户反馈"""
        start_time = time.time()
        
        try:
            data = request.get_json()
            openid = data.get('openid')
            content = data.get('content')
            contact = data.get('contactInfo')
            timestamp = data.get('timestamp')
            
            # 记录详细日志
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message = (
                f"\n=== 用户反馈 ===\n"
                f"时间: {current_time}\n"
                f"用户ID: {openid}\n"
                f"反馈内容: {content}\n"
                f"联系方式: {contact}\n"
                f"客户端时间戳: {timestamp}\n"
                f"==================\n"
            )
            
            # 确保日志目录存在
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            # 写入日志文件
            log_file = os.path.join(log_dir, f"feedback_{datetime.now().strftime('%Y%m')}.log")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_message)
            
            if not openid or not content:
                print(f"反馈参数缺失: openid={openid}, content={content}")
                return jsonify({
                    "success": False,
                    "message": "缺少必要参数",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 400
                
            try:
                with sqlite3.connect('vibebite.db') as conn:
                    cursor = conn.cursor()
                    
                    # 创建反馈表（如果不存在）
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS user_feedback (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            openid TEXT NOT NULL,
                            content TEXT NOT NULL,
                            contact TEXT,
                            timestamp TEXT,
                            created_at TEXT NOT NULL,
                            FOREIGN KEY (openid) REFERENCES users (openid)
                        )
                    ''')
                    
                    # 保存反馈
                    cursor.execute('''
                        INSERT INTO user_feedback 
                        (openid, content, contact, timestamp, created_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (openid, content, contact, str(timestamp)))
                    
                    conn.commit()
                    
                    # 记录成功保存的日志
                    print(f"反馈保存成功: {log_message}")
                    
                    return jsonify({
                        "success": True,
                        "message": "反馈已保存",
                        "response_time": f"{time.time() - start_time:.3f}s"
                    })
                    
            except sqlite3.Error as e:
                error_message = f"保存反馈到数据库错误: {str(e)}"
                print(error_message)
                # 记录错误日志
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"错误: {error_message}\n")
                return jsonify({
                    "success": False,
                    "message": "保存反馈失败",
                    "details": str(e),
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 500
                
        except Exception as e:
            error_message = f"处理反馈请求错误: {str(e)}"
            print(error_message)
            # 记录错误日志
            log_file = os.path.join("logs", f"feedback_{datetime.now().strftime('%Y%m')}.log")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"错误: {error_message}\n")
            return jsonify({
                "success": False,
                "message": "处理反馈失败",
                "details": str(e),
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 500

    def get_preferences_history(self):
        """获取用户偏好历史记录"""
        start_time = time.time()
        
        try:
            # 从请求参数获取openid
            openid = request.get_json().get('openid')
            if not openid:
                return jsonify({
                    "success": False,
                    "message": "缺少openid参数",
                    "response_time": f"{time.time() - start_time:.3f}s"
                }), 400
            
            try:
                with sqlite3.connect('vibebite.db') as conn:
                    cursor = conn.cursor()
                    
                    # 直接使用openid查询历史记录
                    cursor.execute('''
                        SELECT custom_description, extracted_keywords, created_at, updated_at
                        FROM user_preferences 
                        WHERE openid = ?
                        ORDER BY updated_at DESC
                    ''', (openid,))
                    
                    history = []
                    for row in cursor.fetchall():
                        history.append({
                            'description': row[0],
                            'keywords': row[1].split(',') if row[1] else [],
                            'createdAt': row[2],
                            'updatedAt': row[3]
                        })
                    
                    return jsonify({
                        "success": True,
                        "data": {
                            "history": history
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
            print(f"获取偏好历史记录错误: {str(e)}")
            return jsonify({
                "success": False,
                "message": "获取偏好历史记录失败",
                "details": str(e),
                "response_time": f"{time.time() - start_time:.3f}s"
            }), 500

# 创建服实例
service = AgentChatService()
service.clear_database()
if __name__ == '__main__':
    asyncio.run(service.run()) 
    service.run_flask(port=8080)
