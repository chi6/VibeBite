from flask import Flask
import sqlite3
from datetime import datetime
import os

class BaseService:
    def __init__(self):
        self.app = Flask(__name__)
        
    def init_db(self):
        """初始化数据库连接"""
        db_path = os.path.join(os.getcwd(), 'vibebite.db')
        return sqlite3.connect(db_path)

    def get_db_connection(self):
        """获取数据库连接"""
        return sqlite3.connect('vibebite.db') 