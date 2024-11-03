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
    
    async def group_simulation(self, initiator_id: str, message: str, task: str) -> List[Dict[str, Any]]:
        """模拟两个Agent的讨论过程"""
        print(f"\n开始讨论任务: {task}\n")
        
        # 第一轮：分析专家分析问题
        print("=== 第1轮：问题分析 ===")
        analysis = await self.agents["1"].process_task("analyzer", 
            f"请分析这个任务的关键点和需要考虑的方面：{task}")
        print(f"分析专家：{analysis}\n")
        
        # 第二轮：解决方案专家提出初步方案
        print("=== 第2轮：初步方案 ===")
        initial_solution = await self.agents["2"].process_task("solver", 
            f"基于以下分析，请提出初步解决方案：\n{analysis}\n原始任务：{task}")
        print(f"方案专家：{initial_solution}\n")
        
        # 后续轮次：讨论优化
        for i in range(3, 3 + 1):
            print(f"=== 第{i}轮：方案优化 ===")
            
            # 分析专家评估方案
            analysis_feedback = await self.agents["1"].process_task("analyzer",
                f"请评估这个解决方案，指出潜在问题和改进建议：\n{initial_solution}")
            print(f"分析专家：{analysis_feedback}\n")
            
            # 方案专家优化方案
            improved_solution = await self.agents["2"].process_task("solver",
                f"根据以下反馈优化解决方案：\n{analysis_feedback}")
            print(f"方案专家：{improved_solution}\n")
            
            initial_solution = improved_solution
        
        print("=== 讨论结束 ===")

    def summarize_chat(self, last_n: int = 10) -> str:
        # 简单的总结实现
        summary = f"最近 {last_n} 条群组对话总结:\n"
        for chat in self.chat_history[-last_n:]:
            summary += f"\n发送者 {chat['sender_id']}: {chat['message']}\n"
            for response in chat['responses']:
                summary += f"- {response['agent_id']} 回复: {response['content']}\n"
        return summary
