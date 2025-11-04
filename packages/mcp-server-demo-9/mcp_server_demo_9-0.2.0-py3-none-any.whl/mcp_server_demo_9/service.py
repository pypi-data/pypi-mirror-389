"""
我的MCP服务器
"""

from mcp.server.fastmcp import FastMCP
import asyncio
import sys

# 创建MCP服务器实例
mcp = FastMCP("DemoServer")

@mcp.tool()
def add(a: int, b: int) -> int:
    """将两个数字相加"""
    print(f"🔢 计算: {a} + {b} = {a + b}")
    return a + b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """将两个数字相乘"""
    result = a * b
    print(f"🔢 计算: {a} × {b} = {result}")
    return result

@mcp.tool()
def greet(name: str) -> str:
    """向用户问候"""
    greeting = f"👋 你好，{name}！欢迎使用MCP服务器。"
    print(greeting)
    return greeting


def main():
    print("🚀 MCP服务器启动中...")
    print("📡 等待 MCP 客户端连接...")
    mcp.run(transport="stdio")
    # """主入口函数"""
    # if len(sys.argv) > 1 and sys.argv[1] == "run":
    #     print("🚀 MCP服务器启动中...")
    #     print("📡 等待 MCP 客户端连接...")
    #     # ✅ 简单修复：直接运行
    #     asyncio.run(mcp.run(transport="stdio"))
    # else:
    #     print("=" * 60)
    #     print("🤖 MCP服务器")
    #     print("=" * 60)
    #     print("使用方法:")
    #     print("  uv run mcp-server-demo-8 run    # 启动服务器")
    #     print("  uv run mcp-server-demo-8        # 显示帮助")
    #     print()
    #     print("🛠️  可用工具:")
    #     print("  • add - 加法计算器")
    #     print("  • multiply - 乘法计算器")
    #     print("  • greet - 问候工具")
    #     print()
    #     print("📚 可用资源:")
    #     print("  • info://{topic} - 获取信息")
    #     print("=" * 60)

if __name__ == "__main__":
    main()