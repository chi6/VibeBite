import json
from typing import List, Dict, Any
from llm_client import ChatGptClient
from prompt_manager import PromptManager
import asyncio
from rag_utils import RAGTools
import uuid
import time

class Agent:
    def __init__(
        self,
        agent_id: str,
        name: str,
        llm_client: ChatGptClient,
        prompt_manager: PromptManager,
        rag_tools: RAGTools = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager
        self.memory: List[Dict[str, Any]] = []
        self.rag_tools = rag_tools
        
    def construct_prompt(self, task_name, input_text) -> str:
        meta_prompt = self.prompt_manager.get_prompt(task_name)
        if not meta_prompt:
            return "prompt not found"
        
        system_prompt = {"role": "system", "content": ""}
        user_prompt = {"role": "user", "content": ""}

        user_prompt["content"] += meta_prompt
        # 添加 memory
        if self.memory:
            memory_text = ""
            for i, m in enumerate(self.memory[-5:]):
                memory_text += f"\n历史记录 {i+1}:\n用户输入: {m['user_input']}\nAI输出: {m['agent_output']}"
            user_prompt["content"] += memory_text

        # 添加RAG检索结果
        if self.rag_tools:
            relevant_contexts = self.rag_tools.get_relevant_contexts(input_text)
            if relevant_contexts:
                context_text = "\n".join(relevant_contexts)
        user_prompt["content"] += "\n当前用户的输入为：{}".format(input_text)

        return system_prompt, user_prompt


    def process_task(self, task_name: str, input_text: str) -> str:
        system_prompt, user_prompt = self.construct_prompt(task_name, input_text)
        if not system_prompt or not user_prompt:
            return "未找到对应任务的prompt"
            
        messages = [system_prompt, user_prompt]
        request_id = str(uuid.uuid4())
        print(user_prompt["content"])
        self.llm_client.add_request(self.agent_id, system_prompt["content"], user_prompt["content"], request_id)
        
        response = ""
        for _ in range(100):
            response = self.llm_client.get_chat(request_id)
            response_content = response['response'].choices[0].message.content
            if response_content != "没有找到响应":
                break
            time.sleep(0.1)

        res = response_content
        self.memory.append({
            "user_input": input_text,
            "agent_output": res 
        })

        return res
    
    async def get_status(self) -> Dict[str, str]:
        """获取代理的状态，包括mood, activity, thought"""
        task_name = "status_check"
        input_text = "获取当前状态"
        
        print(f"构建状态请求: task_name={task_name}, input_text={input_text}")
        
        system_prompt, user_prompt = self.construct_prompt(task_name, input_text)
        if not system_prompt or not user_prompt:
            print("未找到对应任务的prompt")
            return {"error": "未找到对应任务的prompt"}
        
        request_id = str(uuid.uuid4())
        print(f"发送请求: agent_id={self.agent_id}, request_id={request_id}, system_prompt={system_prompt['content']}, user_prompt={user_prompt['content']}")
        self.llm_client.add_request(self.agent_id, system_prompt["content"], user_prompt["content"], request_id)
        
        response = ""
        for _ in range(100):
            response = self.llm_client.get_chat(request_id)
            response_content = response['response'].choices[0].message.content
            print(f"收到响应: {response_content}")
            if response_content != "没有找到响应":
                break
            time.sleep(0.1)

        try:
            status = json.loads(response_content)
            print(f"解析状态: {status}")
        except json.JSONDecodeError:
            print("无法解析状态响应")
            status = {"error": "无法解析状态响应"}

        return status
    
    def _format_memory(self) -> str:
        return "\n".join([
            f"历史记录 {i+1}:\n输入: {m['input']}\n输出: {m['output']}"
            for i, m in enumerate(self.memory[-3:])  # 只使用最近3条记录
        ])
