from typing import Dict, Any

class Config:
    OPENAI_API_KEY = "your-api-key"
    DEFAULT_MODEL = "gpt-3.5-turbo"
    MAX_TOKENS = 2000
    TEMPERATURE = 0.7
    
    # 存储路径配置
    MEMORY_PATH = "./memory"
    PROMPT_PATH = "./prompts"

    # RAG配置
    VECTOR_DB_PATH = "./vector_db"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    EMBEDDING_MODEL = "text-embedding-ada-002"
    TOP_K_RESULTS = 3
