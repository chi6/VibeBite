from typing import List, Dict, Any
import openai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from config import Config

class RAGTools:
    def __init__(self, api_key: str = Config.OPENAI_API_KEY):
        self.embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        self.vector_store = Chroma(
            persist_directory=Config.VECTOR_DB_PATH,
            embedding_function=self.embeddings
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
    
    def add_documents(self, documents: List[str], metadata: List[Dict[str, Any]] = None):
        """添加文档到向量数据库"""
        chunks = self.text_splitter.create_documents(documents, metadata)
        self.vector_store.add_documents(chunks)
        
    async def get_relevant_contexts(self, query: str, top_k: int = Config.TOP_K_RESULTS) -> List[str]:
        """检索相关上下文"""
        results = self.vector_store.similarity_search(query, k=top_k)
        return [doc.page_content for doc in results]
    
    def clear_vector_store(self):
        """清空向量数据库"""
        self.vector_store.delete_collection()
        self.vector_store = Chroma(
            persist_directory=Config.VECTOR_DB_PATH,
            embedding_function=self.embeddings
        )
