import os
import asyncio
from volcenginesdkarkruntime import Ark

class ChatGptClient:
    def __init__(self):
        self.client = Ark()  # 初始化 Ark 客户端
        self.endpoint_id = os.getenv('ENDPOINT_ID')  # 从环境变量获取模型 ID
        self.request_queue = asyncio.Queue()  # 使用 asyncio.Queue 来管理请求
        self.responses = {}  # 存储请求的响应

    async def start(self):
        """初始化并启动worker"""
        asyncio.create_task(self.worker())

    async def query(self, user_message, request_id):
        """发送用户消息并获取响应"""
        print("----- standard request -----")
        completion = self.client.chat.completions.create(
            model=self.endpoint_id,
            messages=[
                {"role": "system", "content": "你是徐老师，是徐佳铭的AI分身"},
                {"role": "user", "content": user_message},
            ],
        )
        # 存储响应
        self.responses[request_id] = completion
        return completion

    async def worker(self):
        """工作线程，从队列中获取请求并处理"""
        while True:
            uid, user_message, request_id = await self.request_queue.get()
            await self.query(user_message, request_id)
            self.request_queue.task_done()

    async def add_request(self, uid, user_message, request_id):
        """将请求添加到队列"""
        await self.request_queue.put((uid, user_message, request_id))

    def proc_chat(self, uid, messages, conversation_id, parent_id, request_id, uri=None, api_type=4, fake_message=None):
        """处理聊天请求"""
        if isinstance(messages, str):
            input_messages = [{"role": "user", "content": messages}]
        elif isinstance(messages, list):
            input_messages = messages
        else:
            raise Exception("messages must be str or list")

        # 将请求添加到队列
        asyncio.create_task(self.add_request(uid, input_messages, request_id))

    def get_chat(self, request_id):
        """获取聊天响应"""
        # 从存储中获取响应
        if request_id in self.responses:
            response = self.responses[request_id]
            del self.responses[request_id]  # 可选：删除已获取的响应
            return {"request_id": request_id, "response": response}
        else:
            return {"request_id": request_id, "response": "没有找到响应"}

async def main():
    volcengines_client = ChatGptClient()
    
    # 启动工作线程
    asyncio.create_task(volcengines_client.start())

    # 添加多个请求到队列
    await volcengines_client.add_request("user1", "常见的十字花科植物有哪些？", "request1")
    #await volcengines_client.add_request("user2", "你能告诉我关于长安的历史吗？", "request2")
    
    # 等待所有请求处理完成
    #await volcengines_client.request_queue.join()

    # 获取响应
    for _ in range(100):  # 最多等待100次
        print(volcengines_client.get_chat("request1"))
        #print(volcengines_client.get_chat("request2"))
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(main())