# 这份代码是用来获取实时天气数据的，用于查询指定地区的当前天气状况。
# 调用时需要提供地区的LocationID或经纬度坐标作为location参数。
# 返回值是包含实时天气信息的字典，包括温度、体感温度、天气状况、风向风力等数据。
# 依赖tool1_get_jwt.py生成的JWT token进行API认证。
from typing import Any, Dict
import httpx
import json
from mcp.server.fastmcp import FastMCP
# 导入get_jwt_token函数
from .tool1_get_jwt import get_jwt_token

# 初始化FastMCP服务器，使用与main.py一致的名称
mcp = FastMCP("weather")

# API配置
API_HOST = "na5ctux62n.re.qweatherapi.com"
API_ENDPOINT = "/v7/weather/now"
API_URL = f"https://{API_HOST}{API_ENDPOINT}"


@mcp.tool()
async def get_now_weather(location: str) -> Dict[str, Any]:
    """获取实时天气数据
    
    Args:
        location: 需要查询地区的LocationID或以英文逗号分隔的经度,纬度坐标（十进制，最多支持小数点后两位）
        
    Returns:
        Dict: 包含实时天气信息的字典
    """
    # 生成JWT token
    token_result = await get_jwt_token()
    if not token_result or "token" not in token_result:
        return {"error": "无法生成有效的token"}
    
    # 从返回的字典中获取token值
    token = token_result["token"]
    
    # 构建请求头
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept-Encoding": "gzip"
    }
    
    # 构建查询参数
    params = {
        "location": location
    }
    
    print(f"查询实时天气: {location}")
    print(f"请求URL: {API_URL}")
    
    # 发送请求
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(API_URL, headers=headers, params=params)
            response.raise_for_status()  # 检查HTTP错误
            
            # 解析响应
            data = response.json()
            print(f"响应状态码: {response.status_code}")
            print(f"原始响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 标准化天气数据
            return standardize_weather_data(data)
            
    except httpx.HTTPStatusError as e:
            print(f"HTTP错误: {e.response.status_code} - {e.response.text}")
            return {"error": f"HTTP错误: {e.response.status_code}"}
    except Exception as e:
            print(f"请求错误: {e}")
            return {"error": f"请求错误: {str(e)}"}


def standardize_weather_data(raw_data):
    """
    标准化天气数据
    将API返回的原始数据转换为统一格式，方便后续使用
    """
    if not raw_data or raw_data.get('code') != '200':
        print(f"错误: API返回失败，状态码: {raw_data.get('code')}")
        return {"error": f"API返回失败，状态码: {raw_data.get('code')}"}
    
    # 提取实时天气数据
    weather_data = {
        'code': raw_data.get('code', ''),  # 状态码
        'updateTime': raw_data.get('updateTime', ''),  # 当前API的最近更新时间
        'fxLink': raw_data.get('fxLink', ''),  # 当前数据的响应式页面
        'now': {}
    }
    
    # 提取now字段的数据
    now_data = raw_data.get('now', {})
    weather_data['now'] = {
        'obsTime': now_data.get('obsTime', ''),  # 数据观测时间
        'temp': now_data.get('temp', ''),  # 温度，默认单位：摄氏度
        'feelsLike': now_data.get('feelsLike', ''),  # 体感温度，默认单位：摄氏度
        'icon': now_data.get('icon', ''),  # 天气状况的图标代码
        'text': now_data.get('text', ''),  # 天气状况的文字描述
        'wind360': now_data.get('wind360', ''),  # 风向360角度
        'windDir': now_data.get('windDir', ''),  # 风向
        'windScale': now_data.get('windScale', ''),  # 风力等级
        'windSpeed': now_data.get('windSpeed', ''),  # 风速，公里/小时
        'humidity': now_data.get('humidity', ''),  # 相对湿度，百分比数值
        'precip': now_data.get('precip', ''),  # 过去1小时降水量，默认单位：毫米
        'pressure': now_data.get('pressure', ''),  # 大气压强，默认单位：百帕
        'vis': now_data.get('vis', ''),  # 能见度，默认单位：公里
        'cloud': now_data.get('cloud', ''),  # 云量，百分比数值
        'dew': now_data.get('dew', '')  # 露点温度
    }
    
    # 添加refer信息
    weather_data['refer'] = {
        'sources': raw_data.get('refer', {}).get('sources', []),  # 原始数据来源
        'license': raw_data.get('refer', {}).get('license', [])  # 数据许可或版权声明
    }
    
    return weather_data

