# AI Agent Chat Service

这是一个基于Flask的AI Agent聊天服务，使用OpenAI的API进行自然语言处理。该服务支持通过POST请求与多个智能体进行交互。

## 功能

- 支持多智能体对话
- 使用RAG（检索增强生成）框架
- 提供友好的助手和数据分析功能

## 目录结构

- `app.py`：Flask应用的主文件
- `config.py`：配置文件
- `llm_client.py`：与OpenAI API交互的客户端
- `prompt_manager.py`：管理不同任务的prompt
- `agent.py`：定义智能体类
- `group.py`：定义群组类
- `rag_utils.py`：RAG工具类
- `start.py`：初始化和启动脚本

## 安装

1. 克隆仓库：

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. 创建并激活虚拟环境（可选）：

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

## 配置

在`config.py`中设置你的OpenAI API密钥和其他配置参数。

## 运行服务

启动Flask服务： 