import os
import json
from typing import Dict, Optional

class PromptManager:
    def __init__(self, prompt_path: str = Config.PROMPT_PATH):
        self.prompt_path = prompt_path
        self.prompts: Dict[str, str] = {}
        self._load_prompts()
    
    def _load_prompts(self):
        if not os.path.exists(self.prompt_path):
            os.makedirs(self.prompt_path)
        
        for file in os.listdir(self.prompt_path):
            if file.endswith('.json'):
                with open(os.path.join(self.prompt_path, file), 'r', encoding='utf-8') as f:
                    self.prompts.update(json.load(f))
    
    def get_prompt(self, task_name: str) -> Optional[str]:
        return self.prompts.get(task_name)
    
    def add_prompt(self, task_name: str, prompt: str):
        self.prompts[task_name] = prompt
        self._save_prompts()
    
    def _save_prompts(self):
        with open(os.path.join(self.prompt_path, 'prompts.json'), 'w', encoding='utf-8') as f:
            json.dump(self.prompts, f, ensure_ascii=False, indent=2)
