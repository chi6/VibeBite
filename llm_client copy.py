import os
import asyncio
import aiohttp
import queue

class VolcenginesClient:
    def __init__(self):
        self.endpoint_id = os.getenv('ENDPOINT_ID')
        self.url = "https://api.volcengine.com/chat/completions"  # 替换为实际的 API URL
        self.request_queue = asyncio.Queue()  # 使用 asyncio.Queue 来管理请求

    async def query(self, user_message):
        """发送用户消息并获取响应"""
        print("----- standard request -----")
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, json={
                "model": self.endpoint_id,
                "messages": [
                    {"role": "system", "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手"},
                    {"role": "user", "content": user_message},
                ],
            }) as response:
                return await response.json()

    async def worker(self):
        """工作线程，从队列中获取请求并处理"""
        while True:
            user_message = await self.request_queue.get()
            response = await self.query(user_message)
            print(f"Response: {response}")
            self.request_queue.task_done()

    async def add_request(self, user_message):
        """将请求添加到队列"""
        await self.request_queue.put(user_message)

async def main():
    volcengines_client = VolcenginesClient()
    
    # 启动工作线程
    asyncio.create_task(volcengines_client.worker())

    # 添加多个请求到队列
    await volcengines_client.add_request("常见的十字花科植物有哪些？")
    await volcengines_client.add_request("你能告诉我关于长安的历史吗？")
    
    # 等待所有请求处理完成
    await volcengines_client.request_queue.join()

if __name__ == "__main__":
    asyncio.run(main())
