from .base_service import BaseService
from flask import request, jsonify
import requests
import time
import json

class RecommendationService(BaseService):
    def __init__(self):
        super().__init__()
        self.GOOGLE_API_KEY = '5e0ade74a776ca00770d7155a6ed361f25fde09a'

    def get_recommendations(self):
        """获取餐厅推荐"""
        start_time = time.time()
        
        try:
            openid = self._validate_token()
            if not openid:
                return self._error_response("未授权访问", start_time)

            data = request.get_json()
            location = data.get('location', 'China')
            messages = data.get('messages', [])
            timestamp = data.get('timestamp')

            # 搜索餐厅
            search_results = self._search_restaurants(location)
            recommendations = self._process_search_results(search_results, location, timestamp)

            return jsonify({
                "success": True,
                "data": {
                    "recommendations": recommendations,
                    "images": self._process_images(search_results),
                    "searchParameters": search_results.get('searchParameters', {})
                }
            })

        except Exception as e:
            return self._error_response(str(e), start_time)

    def save_shared_session(self):
        """保存分享会话"""
        start_time = time.time()
        
        try:
            openid = self._validate_token()
            if not openid:
                return self._error_response("未授权访问", start_time)

            data = request.get_json()
            share_id = data.get('shareId')
            messages = json.dumps(data.get('messages', []))
            recommendations = json.dumps(data.get('recommendations', []))
            timestamp = data.get('timestamp')

            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO shared_sessions 
                    (share_id, openid, messages, recommendations, timestamp, created_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (share_id, openid, messages, recommendations, timestamp))
                conn.commit()

            return jsonify({
                "success": True,
                "data": {"shareId": share_id}
            })

        except Exception as e:
            return self._error_response(str(e), start_time)

    def _search_restaurants(self, location):
        """调用Google搜索API"""
        url = "https://google.serper.dev/search"
        headers = {
            'X-API-KEY': self.GOOGLE_API_KEY,
            'Content-Type': 'application/json'
        }
        search_data = {
            "q": f"餐厅 美食 推荐 {location}",
            "location": location,
            "gl": "cn",
            "hl": "zh-cn"
        }
        response = requests.post(url, headers=headers, json=search_data, timeout=5)
        return response.json()

    def _process_search_results(self, results, location, timestamp):
        """处理搜索结果"""
        recommendations = []
        if 'organic' in results:
            for result in results['organic'][:5]:
                recommendations.append({
                    'title': result.get('title', ''),
                    'description': result.get('snippet', ''),
                    'link': result.get('link', ''),
                    'type': 'restaurant',
                    'position': result.get('position', 0),
                    'date': result.get('date', ''),
                    'location': location,
                    'timestamp': timestamp
                })
        return recommendations

    def _process_images(self, results):
        """处理图片结果"""
        images = []
        if 'images' in results:
            for image in results['images'][:5]:
                images.append({
                    'title': image.get('title', ''),
                    'imageUrl': image.get('imageUrl', ''),
                    'link': image.get('link', '')
                })
        return images 