from mcp.server.fastmcp import FastMCP

# 创建主MCP实例
master_mcp = FastMCP("weather")

# 直接从各个模块导入工具函数
try:
    # 尝试直接导入（当作为包安装时）
    from tool_天气.tool1_get_jwt import get_jwt_token 
    from tool_天气.tool2_get_city_info import get_city_info
    from tool_天气.tool3_get_now_weather import get_now_weather
    from tool_天气.tool4_get_3_30day_weather import get_3_30day_weather
except ImportError:
    # 回退到相对导入（当在开发环境中运行时）
    try:
        from ..tool_天气.tool1_get_jwt import get_jwt_token 
        from ..tool_天气.tool2_get_city_info import get_city_info
        from ..tool_天气.tool3_get_now_weather import get_now_weather
        from ..tool_天气.tool4_get_3_30day_weather import get_3_30day_weather
    except ImportError:
        print("警告：无法导入必要的工具模块，请确保tool_天气包在Python路径中")
        raise



def initialize_master_mcp():
    """
    初始化主MCP实例，注册所有模块的工具函数
    """
    # 这里导入和风天气的JWT token MCP工具
    master_mcp.tool(name="get_jwt_token")(get_jwt_token)
    # 这里导入和风天气的城市搜索 MCP工具
    master_mcp.tool(name="get_city_info")(get_city_info)
    # 这里导入和风天气的实时天气 MCP工具
    master_mcp.tool(name="get_now_weather")(get_now_weather)
    # 这里导入和风天气的3-30天天气 MCP工具
    master_mcp.tool(name="get_3_30day_weather")(get_3_30day_weather)
  
    
    # 由于无法直接访问工具数量，我们返回预期的工具数量
    return 4

# 获取主MCP实例的函数
def get_master_mcp() -> FastMCP:
    """获取包含所有工具的主MCP实例。"""
    return master_mcp

def main():
    """MCP服务器的主入口点。"""
    try:
        print("正在初始化MCP工具...")
        
        # 初始化主MCP实例，合并所有工具
        tool_count = initialize_master_mcp()
        
        # 获取包含所有工具的主MCP实例
        master_mcp = get_master_mcp()
        
        print(f"服务器已初始化{tool_count}个天气工具")
        print("正在启动MCP服务器...")
        print("服务器已准备好通过标准输入接收JSON-RPC请求")
        
        # 运行服务器
        master_mcp.run(transport='stdio')
    except KeyboardInterrupt:
        print("\n服务器正在关闭...")
    except Exception as e:
        print(f"运行服务器时出错: {e}")
        print("注意: 此服务器期望通过标准输入接收JSON-RPC请求")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
