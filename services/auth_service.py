from .base_service import BaseService
from flask import request, jsonify
import hashlib
import time
import os
from dotenv import load_dotenv
import requests

class AuthService(BaseService):
    def __init__(self):
        super().__init__()
        load_dotenv()
        self.APP_ID = os.getenv('WX_APP_ID')
        self.APP_SECRET = os.getenv('WX_APP_SECRET')

    def wx_login(self):
        """处理微信小程序登录"""
        start_time = time.time()
        
        try:
            data = request.get_json()
            code = data.get('code')
            
            if not code:
                return self._error_response("Missing code", start_time)

            # 调用微信接口
            wx_response = self._call_wx_api(code)
            
            if 'errcode' in wx_response:
                return self._error_response(wx_response.get('errmsg', '未知错误'), start_time)

            # 处理登录
            token = self._handle_login(wx_response)
            
            return jsonify({
                "success": True,
                "token": token,
                "response_time": f"{time.time() - start_time:.3f}s"
            })

        except Exception as e:
            return self._error_response(str(e), start_time)

    def _call_wx_api(self, code):
        """调用微信登录API"""
        url = "https://api.weixin.qq.com/sns/jscode2session"
        params = {
            'appid': self.APP_ID,
            'secret': self.APP_SECRET,
            'js_code': code,
            'grant_type': 'authorization_code'
        }
        response = requests.get(url, params=params)
        return response.json()

    def _handle_login(self, wx_response):
        """处理登录逻辑"""
        openid = wx_response['openid']
        session_key = wx_response['session_key']
        token = self._generate_token(openid, session_key)
        
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO sessions (token, openid, created_at) VALUES (?, ?, ?)',
                (token, openid, datetime.now().isoformat())
            )
            conn.commit()
        
        return token

    def _generate_token(self, openid, session_key):
        """生成会话token"""
        token_str = f"{openid}{session_key}{time.time()}"
        return hashlib.sha256(token_str.encode()).hexdigest()
    
    def protected_resource(self):
        """处理受保护资源访问"""
        # 原protected_resource的实现...
        pass 