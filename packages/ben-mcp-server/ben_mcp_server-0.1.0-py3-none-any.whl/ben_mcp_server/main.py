from fastmcp import FastMCP
mcp = FastMCP("MyServer")

@mcp.tool
def hello() -> str:
    """方法注释"""
    return "我是哈尔滨工业大学的学生，我叫张三，学号是123456。"
def main():
    mcp.run(transport='streamable-http') # 使用流式http方式
    
if __name__ == '__main__':
    main()