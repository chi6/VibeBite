import json
from typing import List, Dict, Any
from llm_client import ChatGptClient
from prompt_manager import PromptManager
import asyncio
from rag_utils import RAGTools

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


    async def process_task(self, task_name: str, input_text: str) -> str:
        #TODO: some query to qwen cannot get response
        #prompt = self.prompt_manager.get_prompt(task_name)
        system_prompt, user_prompt = self.construct_prompt(task_name, input_text)
        if not system_prompt or not user_prompt:
            return "未找到对应任务的prompt"
            
        messages = [system_prompt, user_prompt]
        # 使用新的ChatGptClient处理请求
        request_id = f"{self.agent_id}_{task_name}_{len(self.memory)}"
        print(messages)
        self.llm_client.proc_chat(self.agent_id, messages, "", "", request_id)
        
        # 等待响应
        response = ""
        for _ in range(100):  # 最多等待100次
            res = self.llm_client.get_chat(request_id)
            if len(res) != 0:
                response = res[0].get("text", "")['response']['output']['text']
                break
            await asyncio.sleep(0.1)
        
        # 保存到记忆
        self.memory.append({
            "user_input": input_text,
            "agent_output": response
        })
        print(response)
        return response
    
    def _format_memory(self) -> str:
        return "\n".join([
            f"历史记录 {i+1}:\n输入: {m['input']}\n输出: {m['output']}"
            for i, m in enumerate(self.memory[-3:])  # 只使用最近3条记录
        ])
