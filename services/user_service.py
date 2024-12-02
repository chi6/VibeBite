from .base_service import BaseService
from flask import request, jsonify
import time
import json
from datetime import datetime
import uuid
from llm_client import ChatGptClient

class UserService(BaseService):
    def __init__(self):
        super().__init__()
        self.llm_client = ChatGptClient()

    def user_profile(self):
        """处理用户档案的获取和更新"""
        if request.method == 'GET':
            return self.get_user_profile()
        else:  # POST
            return self.update_user_profile()

    def user_preferences(self):
        """处理用户偏好的获取和更新"""
        if request.method == 'GET':
            return self.get_preferences()
        else:  # POST
            return self.update_preferences()

    def get_preferences_summary(self):
        """获取用户餐饮喜好总结"""
        start_time = time.time()
        
        try:
            openid = self._validate_token()
            if not openid:
                return self._error_response("未授权访问", start_time)

            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                preferences = self._get_user_preferences(cursor, openid)
                
                if not preferences:
                    return jsonify({
                        "success": True,
                        "data": {
                            "summary": "您还没有设置饮食偏好，请先完成偏好设置。",
                            "hasPreferences": False
                        }
                    })

                # 生成AI总结
                summary = self._generate_preferences_summary(preferences)
                
                # 保存总结
                self._save_preferences_summary(cursor, openid, summary)
                
                return jsonify({
                    "success": True,
                    "data": {
                        "summary": summary,
                        "hasPreferences": True
                    }
                })

        except Exception as e:
            return self._error_response(str(e), start_time)

    def _validate_token(self):
        """验证token并返回openid"""
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
            
        token = auth_header.split(' ')[1]
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT openid FROM sessions WHERE token = ?', (token,))
            result = cursor.fetchone()
            return result[0] if result else None

    def _get_user_preferences(self, cursor, openid):
        """获取用户偏好数据"""
        cursor.execute('''
            SELECT * FROM user_preferences WHERE openid = ?
        ''', (openid,))
        return cursor.fetchone()

    def _generate_preferences_summary(self, preferences):
        """使用AI生成偏好总结"""
        prompt = self._build_summary_prompt(preferences)
        request_id = str(uuid.uuid4())
        self.llm_client.add_request("", "", prompt, request_id)
        
        for _ in range(100):
            response = self.llm_client.get_chat(request_id)
            summary = response['response'].choices[0].message.content
            if summary != "没有找到响应":
                return summary
            time.sleep(0.1)
        
        return "无法生成总结"

    def _save_preferences_summary(self, cursor, openid, summary):
        """保存偏好总结到数据库"""
        cursor.execute('''
            INSERT OR REPLACE INTO preference_summaries 
            (openid, summary, created_at, updated_at)
            VALUES (?, ?, 
                COALESCE((SELECT created_at FROM preference_summaries WHERE openid = ?), CURRENT_TIMESTAMP),
                CURRENT_TIMESTAMP)
        ''', (openid, summary, openid)) 