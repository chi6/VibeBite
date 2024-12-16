import os
from volcenginesdkarkruntime import Ark
from quart import Quart, request, jsonify
import uuid
import time

class ChatGptClient:
    def __init__(self):
        self.endpoint_id = 'ep-20241216130717-vvktd'#os.getenv('ENDPOINT_ID')  # 从环境变量获取模型 ID
        self.responses = {}  # 存储请求的响应
        self.client = Ark()

    def query(self, system_message, user_message, request_id):
        """发送用户消息并获取响应"""
        print("----- standard request -----")
        completion = self.client.chat.completions.create(
            model=self.endpoint_id,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
        )
        # 存储响应
        self.responses[request_id] = completion
        return completion

    def add_request(self, uid, system_message, user_message, request_id):
        """处理请求并立即返回响应"""
        print(f"Processing request: {uid}, {system_message}, {user_message}, {request_id}")
        self.query(system_message, user_message, request_id)

    def get_chat(self, request_id):
        """获取聊天响应"""
        # 从存储中获取响应
        if request_id in self.responses:
            response = self.responses[request_id]
            del self.responses[request_id]  # 可选：删除已获取的响应
            return {"request_id": request_id, "response": response}
        else:
            return {"request_id": request_id, "response": "没有找到响应"}

# 创建 Quart 应用
app = Quart(__name__)
client = ChatGptClient()

@app.route('/chat_agent', methods=['POST'])
async def chat_agent():
    data = await request.get_json()
    if not data:
        return jsonify({
            "uniqueId": int(time.time() * 1000000),
            "taskInvoker": None,
            "response": "Invalid JSON"
        }), 400

    agent_id = data.get('agentId')
    message = data.get('message')
    request_id = str(uuid.uuid4())

    # 处理请求并立即返回响应
    client.add_request(agent_id, message, request_id)

    # 获取响应
    response = client.get_chat(request_id)
    # 提取响应内容
    response_content = response['response'].choices[0].message.content
    print(response_content)
    return jsonify({
        "uniqueId": int(time.time() * 1000000),
        "taskInvoker": None,
        "response": response_content
    })

def main():
    # 使用 Quart 的内置方法运行应用
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()