import asyncio
from service import AgentChatService
from typing import List, Dict, Any
import json

class TaskSimulation:
    def __init__(self):
        self.service = AgentChatService()
        self.service.init_components()
        
    async def init_agents(self):
        """初始化两个专门的Agent"""
        # 创建问题分析专家
        analyzer_prompt = """你是一个问题分析专家。你的职责是：
                        1. 分析用户提出的问题的关键点
                        2. 提出解决问题需要考虑的各个方面
                        3. 与解决方案专家讨论，确保方案的可行性
                        请用简洁专业的语言进行沟通。"""
        
        # 创建解决方案专家
        solver_prompt = """你是一个解决方案专家。你的职责是：
                        1. 根据问题分析专家的分析，提出具体的解决方案
                        2. 说明方案的可行性和潜在风险
                        3. 与问题分析专家讨论，优化解决方案
                        请用清晰条理的方式描述解决方案。"""
        
        # 添加prompts
        self.service.prompt_manager.add_prompt("analyzer", analyzer_prompt)
        self.service.prompt_manager.add_prompt("solver", solver_prompt)
        
        # 创建agents
        self.analyzer = self.service.agents["1"]  # 使用已有的Agent 1
        self.solver = self.service.agents["2"]    # 使用已有的Agent 2
        
    async def simulate_discussion(self, task: str, rounds: int = 3):
        """模拟两个Agent的讨论过程"""
        print(f"\n开始讨论任务: {task}\n")
        
        # 第一轮：分析专家分析问题
        print("=== 第1轮：问题分析 ===")
        analysis = await self.analyzer.process_task("analyzer", 
            f"请分析这个任务的关键点和需要考虑的方面：{task}")
        print(f"分析专家：{analysis}\n")
        
        """# 第二轮：解决方案专家提出初步方案
        print("=== 第2轮：初步方案 ===")
        initial_solution = await self.solver.process_task("solver", 
            f"基于以下分析，请提出初步解决方案：\n{analysis}\n原始任务：{task}")
        print(f"方案专家：{initial_solution}\n")
        
        # 后续轮次：讨论优化
        for i in range(3, rounds + 1):
            print(f"=== 第{i}轮：方案优化 ===")
            
            # 分析专家评估方案
            analysis_feedback = await self.analyzer.process_task("analyzer",
                f"请评估这个解决方案，指出潜在问题和改进建议：\n{initial_solution}")
            print(f"分析专家：{analysis_feedback}\n")
            
            # 方案专家优化方案
            improved_solution = await self.solver.process_task("solver",
                f"根据以下反馈优化解决方案：\n{analysis_feedback}")
            print(f"方案专家：{improved_solution}\n")
            
            initial_solution = improved_solution
        """
        print("=== 讨论结束 ===")
        return {
            "task": task,
            "final_solution": initial_solution,
            "discussion_rounds": rounds
        }

async def main():
    # 创建模拟器
    #simulation = TaskSimulation()
    service = AgentChatService()
    service.init_components()
    # 初始化agents
    #await simulation.init_agents()
    print(service.agents)
    # 模拟讨论任务
    task = "我不知道今晚该吃什么。"
    #result = await simulation.simulate_discussion(task, rounds=4)
    print("=== 第1轮：问题分析 ===")
    analysis = await service.agents["1"].process_task("chat", f"请分析这个任务的关键点和需要考虑的方面：{task}")
    print(f"分析专家：{analysis}\n")
    
    # 保存结果
    with open('discussion_result.json', 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(main()) 