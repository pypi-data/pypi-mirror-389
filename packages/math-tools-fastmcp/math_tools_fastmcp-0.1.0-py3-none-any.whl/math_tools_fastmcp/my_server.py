from fastmcp import FastMCP

mcp = FastMCP("My MCP Server")

#使用 @mcp.tool 装饰器将其注册到服务器
@mcp.tool
def greet(name: str) -> str:
    """问候语的工具"""
    return f"Hello, {name}!"

#本地服务器
if __name__ == "__main__":
    mcp.run()

#远程访问
# if __name__ == "__main__":
#     mcp.run(transport="http", port=8000)