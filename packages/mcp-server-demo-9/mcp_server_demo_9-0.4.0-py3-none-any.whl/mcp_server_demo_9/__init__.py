# # src/mcp_server_demo_9/__init__.py
# """
# mcp_server_demo_9 包的入口点
#
# 此文件将 service.py 中的功能暴露给外部导入。
# """
#
# # 导入服务模块
# from .service import mcp, main
#
# # 将工具函数也暴露到包的顶层命名空间
# # 这样测试脚本才能直接通过 `from mcp_server_demo_9 import add, multiply, greet` 导入
# from .service import add, multiply, greet
#
# # 可选：定义 __all__ 来明确指定哪些名称可以被 `from mcp_server_demo_9 import *` 导入
# __all__ = [
#     "mcp",
#     "main",
#     "add",
#     "multiply",
#     "greet"
# ]