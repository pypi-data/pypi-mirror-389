# 这份代码是用来生成JWT的，用于天气API的认证token申请，是接下来所有操作的前提。
# 需要登录和风天气的管理后台，地址：https://dev.qweather.com
# private_key 是openssl生成的EdDSA私钥，生成这个执行下面两条命令：
# openssl genpkey -algorithm Ed25519 -out private_key.pem
# openssl pkey -in private_key.pem -pubout -out public_key.pem
# 公钥 public_key.pem 是在和风天气里添加项目时用到的。
# 私钥 private_key.pem 是用与填充下面的private_key变量的。（主要要复制全部内容，包括-----BEGIN PRIVATE KEY-----和-----END PRIVATE KEY-----，不让会被识别为字符串）
# sub 是和风天气里添加项目时的项目ID
# kid 是和风天气里添加项目时的项目凭据ID
import sys
import time
import jwt
from datetime import datetime, timedelta
import pytz
from typing import Optional, Any
import httpx
from mcp.server.fastmcp import FastMCP

# 初始化FastMCP服务器，使用与main.py一致的名称
mcp = FastMCP("weather")

# Open PEM
private_key = """
                -----BEGIN PRIVATE KEY-----
                MC4CAQAwBQYDK2VwBCIEIJg4I0Ucj20Eqe5NIgoMsQz7hGmIYDkR1IuRnLREJwGe
                -----END PRIVATE KEY-----
            """

headers = {
    'kid': 'TKB32RJ7GH',
    # 显式设置typ为None，防止PyJWT自动添加
    'typ': None
}

@mcp.tool()
async def get_jwt_token(expiration_seconds: int = 300, show_log: bool = True) -> dict:
    """
    生成JWT token用于API认证
    
    Args:
        expiration_seconds: token过期时间间隔（秒），默认300秒
        show_log: 是否显示日志信息，默认True
        
    Returns:
        包含生成的JWT token和相关信息的字典
    """
    # 获取当前时间并转换为北京时间(UTC+8)
    now_utc = datetime.now(pytz.UTC)
    now_cst = now_utc.astimezone(pytz.timezone('Asia/Shanghai'))
    
    # 计算签发时间(iat)和过期时间(exp) - 使用北京时间调整
    # 签发时间: 当前北京时间减去30秒
    issued_time = now_cst - timedelta(seconds=30)
    # 过期时间: 当前北京时间加上指定秒数
    expiration_time = now_cst + timedelta(seconds=expiration_seconds)
    
    # 转换回UTC时间戳用于JWT
    issued_timestamp = int(issued_time.astimezone(pytz.UTC).timestamp())
    expiration_timestamp = int(expiration_time.astimezone(pytz.UTC).timestamp())
    
    # 打印当前北京时间以便调试
    if show_log:
        print(f"当前北京时间: {now_cst.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"签发时间(北京时间): {issued_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"过期时间(北京时间): {expiration_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"过期时间间隔: {expiration_seconds}秒")
    
    payload = {
        'iat': issued_timestamp,
        'exp': expiration_timestamp,
        'sub': '4MDWNAXWK9'
    }
    
    # Generate JWT
    encoded_jwt = jwt.encode(payload, private_key, algorithm='EdDSA', headers=headers)
    
    if show_log:
        print(f"JWT:  {encoded_jwt}")
    
    return {
        "token": encoded_jwt,
        "issued_time": issued_time.strftime('%Y-%m-%d %H:%M:%S'),
        "expiration_time": expiration_time.strftime('%Y-%m-%d %H:%M:%S'),
        "expiration_seconds": expiration_seconds
    }
    
def get_mcp_instance():
    """返回MCP实例，用于与主应用程序集成。"""
    return mcp


# 测试功能，方便直接验证工具
@mcp.tool()
async def test_jwt_tool() -> str:
    """测试JWT工具是否正常工作"""
    return "JWT工具测试成功！可以被MCP正确识别。"