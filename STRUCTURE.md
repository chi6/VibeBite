# 项目结构说明

```
ai-agent-chat-service/
├── app.py              # Flask应用入口
├── service.py          # 主服务类
├── config.py           # 配置文件
├── requirements.txt    # 项目依赖
├── .env               # 环境变量（不提交到git）
├── .gitignore         # Git忽略文件
│
├── components/         # 核心组件
│   ├── agent.py       # Agent类定义
│   ├── group.py       # Group类定义
│   ├── llm_client.py  # LLM客户端
│   ├── prompt_manager.py  # Prompt管理器
│   └── rag_utils.py   # RAG工具类
│
├── memory/            # 记忆存储目录
├── prompts/           # Prompt模板目录
└── vector_db/         # 向量数据库目录
``` 