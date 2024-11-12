import pytest
import httpx
import asyncio

@pytest.mark.asyncio
async def test_chat_agent():
    url = "http://0.0.0.0:5000/chat_agent"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "message": "你好，AI助手！",
        "agentId": "1",
        "taskName": "chat",
        "groupId": "main_group"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
    print(response)
    assert response.status_code == 200
    json_response = response.json()
    assert "uniqueId" in json_response
    assert "response" in json_response
    print("Response:", json_response)

# 运行测试
if __name__ == "__main__":
    asyncio.run(test_chat_agent())