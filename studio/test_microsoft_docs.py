#!/usr/bin/env python3
"""
测试Microsoft Docs MCP的使用
"""

import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage

async def test_microsoft_docs_mcp():
    """测试Microsoft Docs MCP"""
    
    # 创建MCP客户端
    client = MultiServerMCPClient({
        "microsoft.docs.mcp": {
            "autoApprove": [],
            "type": "streamableHttp",
            "url": "https://learn.microsoft.com/api/mcp"
        }
    })
    
    try:
        # 获取可用工具
        tools = await client.get_tools()
        print(f"✅ 成功获取到 {len(tools)} 个Microsoft Docs工具")
        
        # 打印工具信息
        for i, tool in enumerate(tools):
            print(f"\n工具 {i+1}: {tool.name}")
            print(f"描述: {tool.description}")
            print(f"参数: {tool.args_schema}")
        
        # 测试查询Microsoft文档
        print("\n🔍 测试查询Microsoft文档...")
        
        # 创建一个简单的查询
        query = "Python programming basics"
        
        # 这里需要根据实际的工具参数来调用
        # 由于Microsoft Docs MCP的具体API可能不同，这里提供通用示例
        print(f"查询: {query}")
        print("💡 注意: 具体的调用方式取决于Microsoft Docs MCP的实际API")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("可能的原因:")
        print("1. 网络连接问题")
        print("2. Microsoft Docs MCP服务不可用")
        print("3. API格式不正确")

def test_local_tools():
    """测试本地工具"""
    print("\n🔍 测试本地工具...")
    
    def find_document(type: str) -> str:
        try:
            if type == "frontend":
                with open("./tech_doc/frontend.md", "r", encoding="utf-8") as file:
                    return file.read()
            elif type == "backend":
                with open("./tech_doc/backend.md", "r", encoding="utf-8") as file:
                    return file.read()
            else:
                return "不支持的类型"
        except FileNotFoundError:
            return f"文档文件 {type}.md 不存在"
    
    # 测试前端文档
    result = find_document("frontend")
    print(f"前端文档长度: {len(result)} 字符")
    
    # 测试后端文档
    result = find_document("backend")
    print(f"后端文档长度: {len(result)} 字符")

if __name__ == "__main__":
    print("🚀 开始测试MCP工具...")
    
    # 测试本地工具
    test_local_tools()
    
    # 测试Microsoft Docs MCP
    asyncio.run(test_microsoft_docs_mcp())
    
    print("\n✅ 测试完成!") 