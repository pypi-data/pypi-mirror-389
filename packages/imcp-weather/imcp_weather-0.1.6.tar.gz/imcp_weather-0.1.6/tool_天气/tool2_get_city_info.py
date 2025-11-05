# 这份代码是用来搜索城市信息的，用于天气API的城市查询功能。
# 调用时需要提供城市名称或关键词作为location参数。
# 返回值是包含城市信息的列表，每个城市信息包括ID、名称、经纬度等详细信息。
# 依赖tool1_get_jwt.py生成的JWT token进行API认证。
from typing import Any, List, Dict
import httpx
import json
from mcp.server.fastmcp import FastMCP
# 导入get_jwt_token函数
from .tool1_get_jwt import get_jwt_token

# 初始化FastMCP服务器，使用与main.py一致的名称
mcp = FastMCP("weather")

# API配置
API_HOST = "na5ctux62n.re.qweatherapi.com"
API_ENDPOINT = "/geo/v2/city/lookup"
API_URL = f"https://{API_HOST}{API_ENDPOINT}"


@mcp.tool()
async def get_city_info(location: str) -> List[Dict[str, Any]]:
    """搜索城市
    
    Args:
        location: 要搜索的城市名称或关键词
        
    Returns:
        List[Dict]: 包含城市信息的列表
    """
    # 生成JWT token
    token_result = await get_jwt_token()
    if not token_result or "token" not in token_result:
        return [{"error": "无法生成有效的token"}]
    
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
    
    print(f"搜索城市: {location}")
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
            
            # 标准化城市数据
            return standardize_city_data(data)
            
    except httpx.HTTPStatusError as e:
            print(f"HTTP错误: {e.response.status_code} - {e.response.text}")
            return [{"error": f"HTTP错误: {e.response.status_code}"}]
    except Exception as e:
            print(f"请求错误: {e}")
            return [{"error": f"请求错误: {str(e)}"}]


def standardize_city_data(raw_data):
    """
    标准化城市数据
    将API返回的原始数据转换为统一格式，方便后续使用
    """
    if not raw_data or raw_data.get('code') != '200':
        print(f"错误: API返回失败，状态码: {raw_data.get('code')}")
        return []
    
    standardized_cities = []
    
    # 处理城市列表
    for city in raw_data.get('location', []):
        # 按照官方返回数据的字段名称和顺序进行标准化
        standardized_city = {
            'name': city.get('name', ''),  # 地区/城市名称
            'id': city.get('id', ''),      # 地区/城市ID
            'lat': city.get('lat', ''),    # 地区/城市纬度
            'lon': city.get('lon', ''),    # 地区/城市经度
            'adm2': city.get('adm2', ''),  # 地区/城市的上级行政区划名称
            'adm1': city.get('adm1', ''),  # 地区/城市所属一级行政区域
            'country': city.get('country', ''),  # 地区/城市所属国家名称
            'tz': city.get('tz', ''),      # 地区/城市所在时区
            'utcOffset': city.get('utcOffset', ''),  # 地区/城市目前与UTC时间偏移的小时数
            'isDst': city.get('isDst', ''),  # 地区/城市是否当前处于夏令时（1表示是，0表示否）
            'type': city.get('type', ''),  # 地区/城市的属性
            'rank': city.get('rank', ''),  # 地区评分
            'fxLink': city.get('fxLink', '')  # 该地区的天气预报网页链接
        }
        standardized_cities.append(standardized_city)
    
    print(f"标准化后的城市数据 ({len(standardized_cities)} 个):")
    for city in standardized_cities:
        print(f"  - {city['name']} ({city['adm1']}, {city['country']}) - ID: {city['id']}")
    
    return standardized_cities

def get_mcp_instance():
    """返回MCP实例，用于与主应用程序集成。"""
    return mcp