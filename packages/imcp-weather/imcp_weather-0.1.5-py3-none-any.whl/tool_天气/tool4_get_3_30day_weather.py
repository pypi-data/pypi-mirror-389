# 这份代码是用来获取3-30天每日天气预报的，用于查询指定地区的未来天气趋势。
# 调用时需要提供地区的LocationID或经纬度坐标作为location参数，以及预报天数(days参数，支持3d/7d/10d/15d/30d)。
# 返回值是包含每日天气预报信息的字典，包括日期、最高最低温度、天气状况、风向风力等详细数据。
# 依赖tool1_get_jwt.py生成的JWT token进行API认证，针对15天和30天数据做了特殊优化处理。
from typing import Any, Dict, List
import httpx
import json
import time
from mcp.server.fastmcp import FastMCP
# 导入get_jwt_token函数
from .tool1_get_jwt import get_jwt_token

# 初始化FastMCP服务器，使用与main.py一致的名称
mcp = FastMCP("weather")

# API配置
API_HOST = "na5ctux62n.re.qweatherapi.com"
BASE_API_URL = f"https://{API_HOST}/v7/weather/"

# 支持的预报天数选项
VALID_DAYS_OPTIONS = ["3d", "7d", "10d", "15d", "30d"]


@mcp.tool()
async def get_3_30day_weather(location: str, days: str = "3d") -> Dict[str, Any]:
    """获取3-30天每日天气预报
    
    Args:
        location: 需要查询地区的LocationID或以英文逗号分隔的经度,纬度坐标（十进制，最多支持小数点后两位）
        days: 预报天数，支持值：3d（默认）、7d、10d、15d、30d
        
    Returns:
        Dict: 包含每日天气预报信息的字典
    """
    # 验证days参数
    if days not in VALID_DAYS_OPTIONS:
        return {"error": f"无效的days参数，支持的值为: {', '.join(VALID_DAYS_OPTIONS)}"}
    
    # 验证location参数
    if not location or not isinstance(location, str):
        return {"error": "无效的location参数"}
    
    try:
        # 生成JWT token - 减少日志输出
        token_result = await get_jwt_token(show_log=False)
        if not token_result or "token" not in token_result:
            return {"error": "无法生成有效的token"}
        
        # 从返回的字典中获取token值
        token = token_result["token"]
        
        # 构建请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept-Encoding": "gzip"
        }
        
        # 构建请求URL
        API_URL = f"{BASE_API_URL}{days}"
        
        # 构建查询参数
        params = {
            "location": location
        }
        
        # 增加详细日志记录
        start_time = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] 开始查询{days}天气预报: {location}")
        print(f"[{time.strftime('%H:%M:%S')}] 请求URL: {API_URL}")
        
        # 根据天数动态调整超时时间
        timeout_seconds = 25.0 if days in ["15d", "30d"] else 15.0
        print(f"[{time.strftime('%H:%M:%S')}] 设置超时时间: {timeout_seconds}秒")
        
        # 发送请求 - 为15天和30天数据设置更长的超时时间
        async with httpx.AsyncClient(
            timeout=timeout_seconds,  # 根据数据量动态调整超时时间
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            follow_redirects=True
        ) as client:
            print(f"[{time.strftime('%H:%M:%S')}] 发送请求...")
            response = await client.get(API_URL, headers=headers, params=params)
            print(f"[{time.strftime('%H:%M:%S')}] 收到响应，状态码: {response.status_code}")
            response.raise_for_status()  # 检查HTTP错误
            
            # 解析响应
            print(f"[{time.strftime('%H:%M:%S')}] 开始解析响应数据...")
            data = response.json()
            print(f"[{time.strftime('%H:%M:%S')}] 解析完成，数据长度: {len(str(data))} 字符")
            
            # 标准化天气数据
            print(f"[{time.strftime('%H:%M:%S')}] 开始标准化天气数据...")
            result = standardize_daily_weather_data(data)
            end_time = time.time()
            print(f"[{time.strftime('%H:%M:%S')}] 查询完成，耗时: {end_time - start_time:.2f}秒")
            
            return result
    except httpx.TimeoutException:
        end_time = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] 请求超时: 无法连接到天气API服务器，耗时: {end_time - start_time:.2f}秒")
        return {"error": "请求超时: 无法连接到天气API服务器"}
    except httpx.HTTPStatusError as e:
        end_time = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] HTTP错误: {e.response.status_code}，耗时: {end_time - start_time:.2f}秒")
        try:
            error_detail = e.response.json()
            print(f"[{time.strftime('%H:%M:%S')}] 错误详情: {error_detail}")
            return {"error": f"HTTP错误: {e.response.status_code}，详情: {error_detail}"}
        except:
            return {"error": f"HTTP错误: {e.response.status_code}"}
    except httpx.NetworkError as ne:
        end_time = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] 网络错误: {str(ne)}，耗时: {end_time - start_time:.2f}秒")
        return {"error": f"网络错误: {str(ne)}"}
    except json.JSONDecodeError as jde:
        end_time = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] 解析错误: {str(jde)}，耗时: {end_time - start_time:.2f}秒")
        return {"error": f"解析错误: {str(jde)}"}
    except Exception as e:
        end_time = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] 请求错误: {str(e)}，耗时: {end_time - start_time:.2f}秒")
        return {"error": f"请求错误: {str(e)}"}


def standardize_daily_weather_data(raw_data):
    """
    标准化每日天气数据
    将API返回的原始数据转换为统一格式，方便后续使用
    """
    if not raw_data or raw_data.get('code') != '200':
        print(f"错误: API返回失败，状态码: {raw_data.get('code')}")
        return {"error": f"API返回失败，状态码: {raw_data.get('code')}"}
    
    # 提取基本信息
    weather_data = {
        'code': raw_data.get('code', ''),  # 状态码
        'updateTime': raw_data.get('updateTime', ''),  # 当前API的最近更新时间
        'fxLink': raw_data.get('fxLink', ''),  # 当前数据的响应式页面
        'daily': []
    }
    
    # 提取daily数组数据
    daily_list = raw_data.get('daily', [])
    for day_data in daily_list:
        standardized_day = {
            'fxDate': day_data.get('fxDate', ''),  # 预报日期
            'sunrise': day_data.get('sunrise', ''),  # 日出时间
            'sunset': day_data.get('sunset', ''),  # 日落时间
            'moonrise': day_data.get('moonrise', ''),  # 当天月升时间
            'moonset': day_data.get('moonset', ''),  # 当天月落时间
            'moonPhase': day_data.get('moonPhase', ''),  # 月相名称
            'moonPhaseIcon': day_data.get('moonPhaseIcon', ''),  # 月相图标代码
            'tempMax': day_data.get('tempMax', ''),  # 最高温度
            'tempMin': day_data.get('tempMin', ''),  # 最低温度
            'iconDay': day_data.get('iconDay', ''),  # 白天天气状况的图标代码
            'textDay': day_data.get('textDay', ''),  # 白天天气状况的文字描述
            'iconNight': day_data.get('iconNight', ''),  # 夜间天气状况的图标代码
            'textNight': day_data.get('textNight', ''),  # 夜间天气状况的文字描述
            'wind360Day': day_data.get('wind360Day', ''),  # 白天风向360角度
            'windDirDay': day_data.get('windDirDay', ''),  # 白天风向
            'windScaleDay': day_data.get('windScaleDay', ''),  # 白天风力等级
            'windSpeedDay': day_data.get('windSpeedDay', ''),  # 白天风速，公里/小时
            'wind360Night': day_data.get('wind360Night', ''),  # 夜间风向360角度
            'windDirNight': day_data.get('windDirNight', ''),  # 夜间风向
            'windScaleNight': day_data.get('windScaleNight', ''),  # 夜间风力等级
            'windSpeedNight': day_data.get('windSpeedNight', ''),  # 夜间风速，公里/小时
            'humidity': day_data.get('humidity', ''),  # 相对湿度
            'precip': day_data.get('precip', ''),  # 降水量
            'pressure': day_data.get('pressure', ''),  # 大气压强
            'vis': day_data.get('vis', ''),  # 能见度
            'cloud': day_data.get('cloud', ''),  # 云量
            'uvIndex': day_data.get('uvIndex', '')  # 紫外线强度指数
        }
        weather_data['daily'].append(standardized_day)
    
    # 添加引用信息
    weather_data['refer'] = raw_data.get('refer', {})
    
    return weather_data


def get_mcp_instance():
    """返回MCP实例，用于与主应用程序集成。"""
    return mcp


# 测试功能，方便直接验证工具
@mcp.tool()
async def test_daily_weather_tool() -> str:
    """测试3-30天天气预报工具是否正常工作"""
    return "3-30天天气预报工具测试成功！可以被MCP正确识别。"