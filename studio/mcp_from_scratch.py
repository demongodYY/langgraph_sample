import asyncio
import json
import logging
import sys
import traceback
from typing import Any, Dict, List, Optional
import os
current_file_path = os.path.abspath(__file__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPHandler:
    """MCP协议处理器"""
    
    def __init__(self):
        """初始化MCP处理器"""
        self.tools = {"read_document_with_mcp":{
                "name": "read_document_with_mcp",
                "description": """
                Finds the tech document based on the layer.
                Args:
                    layer: the layer of tech document to find only include "frontend", "backend"
                """,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "layer": {"type": "string"},
                    }
                }
            }}
    def read_document_with_mcp(self, layer: str) -> str:
        try:
            if layer == "frontend":
                with open(os.path.join(os.path.dirname(current_file_path), "tech_doc/frontend.md"), "r", encoding="utf-8") as file:
                    return file.read()  # 从 frontend.md 读取文件
            elif layer == "backend":
                with open(os.path.join(os.path.dirname(current_file_path), "tech_doc/backend.md"), "r", encoding="utf-8") as file:
                    return file.read()  # 从 backend.md 读取文件
            else:
                raise ValueError("Unsupported layer. Only 'frontend' and 'backend' are allowed.")
        except FileNotFoundError:
            return f"文档文件 {layer}.md 不存在"
        except Exception as e:
            return f"读取文档时出错: {str(e)}"
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP请求"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "aiworkshop-mcp-server",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": list(self.tools.values())
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name not in self.tools:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {tool_name}"
                        }
                    }
                
                # 调用对应的工具方法
                if tool_name == "read_document_with_mcp":
                    result = self.read_document_with_mcp(**arguments)
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    }
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, ensure_ascii=False, indent=2)
                            }
                        ]
                    }
                }
            
            elif method == "notifications/initialized":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {}
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
async def main():
    """主函数"""
    handler = MCPHandler()
    
    # 读取标准输入
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue
            
            # 解析JSON请求
            try:
                request = json.loads(line)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                continue
            
            # 处理请求
            response = await handler.handle_request(request)
            
            # 输出响应
            print(json.dumps(response, ensure_ascii=False))
            sys.stdout.flush()
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            break

if __name__ == "__main__":
    asyncio.run(main()) 