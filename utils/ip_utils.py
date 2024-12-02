import requests

def get_public_ip():
    """获取公网IP地址"""
    try:
        # 使用多个IP查询服务，防止单个服务不可用
        ip_apis = [
            'https://api.ipify.org?format=json',
            'https://api.myip.com',
            'https://ip.seeip.org/jsonip',
            'https://api.ip.sb/ip',
        ]
        
        for api in ip_apis:
            try:
                response = requests.get(api, timeout=5)
                if response.status_code == 200:
                    if 'json' in api:
                        return response.json().get('ip')
                    return response.text.strip()
            except:
                continue
                
        return "无法获取公网IP"
        
    except Exception as e:
        print(f"获取公网IP出错: {str(e)}")
        return None

def get_ip_info():
    """获取IP详细信息"""
    try:
        response = requests.get('https://ipapi.co/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'ip': data.get('ip'),
                'city': data.get('city'),
                'region': data.get('region'),
                'country': data.get('country_name'),
                'isp': data.get('org')
            }
    except Exception as e:
        print(f"获取IP信息出错: {str(e)}")
        return None 