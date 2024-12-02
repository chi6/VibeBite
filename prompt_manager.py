import os
import json
from typing import Dict, Optional
from config import Config  # 确保导入 Config 类或模块

class PromptManager:
    def __init__(self):
        self.prompts = {}
        self.user_prompts = {}  # 存储用户特定的prompt
        
    def add_prompt(self, task_name: str, prompt: str):
        """添加基础prompt"""
        self.prompts[task_name] = prompt
        
    def get_prompt(self, task_name: str, openid: str = None) -> str:
        """获取prompt,优先返回用户特定的prompt"""
        if openid and openid in self.user_prompts:
            print(f"用户特定的prompt: {self.user_prompts[openid]}")
            user_prompts = self.user_prompts[openid]
            if task_name in user_prompts:
                return user_prompts[task_name]
        return self.prompts.get(task_name, "")
        
    def update_user_prompt(self, openid: str, task_name: str, prompt: str):
        """更新用户特定的prompt"""
        if openid not in self.user_prompts:
            self.user_prompts[openid] = {}
        self.user_prompts[openid][task_name] = prompt
        print(f"更新用户特定的prompt: {prompt}")
