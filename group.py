from typing import List, Dict, Any
from agent import Agent

class Group:
    def __init__(self, group_id: str, name: str):
        self.group_id = group_id
        self.name = name
        self.agents: Dict[str, Agent] = {}
        self.chat_history: List[Dict[str, Any]] = []
        
    def add_agent(self, agent: Agent):
        self.agents[agent.agent_id] = agent
        
    def remove_agent(self, agent_id: str):
        if agent_id in self.agents:
            del self.agents[agent_id]
            
    async def group_chat(self, initiator_id: str, message: str, task_name: str) -> List[Dict[str, Any]]:
        if initiator_id not in self.agents:
            return [{"error": "发起者不在群组中"}]
            
        responses = []
        # 记录初始消息
        chat_entry = {
            "sender_id": initiator_id,
            "message": message,
            "responses": []
        }
        
        # 获取其他agent的响应
        for agent_id, agent in self.agents.items():
            if agent_id != initiator_id:
                response = await agent.process_task(task_name, message)
                chat_entry["responses"].append({
                    "agent_id": agent_id,
                    "content": response
                })
                
        self.chat_history.append(chat_entry)
        return chat_entry["responses"]
    
    def summarize_chat(self, last_n: int = 10) -> str:
        # 简单的总结实现
        summary = f"最近 {last_n} 条群组对话总结:\n"
        for chat in self.chat_history[-last_n:]:
            summary += f"\n发送者 {chat['sender_id']}: {chat['message']}\n"
            for response in chat['responses']:
                summary += f"- {response['agent_id']} 回复: {response['content']}\n"
        return summary
