

import json

import requests
# server.py
from mcp.server.fastmcp import FastMCP
# server_url = "http://127.0.0.1:8002/"
server_url = "http://115.190.100.203/"
# server_url = "http://115.190.100.203:8001/"
# Create an MCP server
mcp = FastMCP("Demo")
import json
import requests

def make_api_request(url_path, payload):
    """
    发送POST请求到指定的url_path，并尝试解析响应。
    :param url_path: API路径后缀（例如："chart/api/mindmap/"）
    :param payload: 请求体数据
    :return: 成功时返回结果中的URL，失败时打印错误信息并返回None
    """
    headers = {"Content-Type": "application/json"}
    print('url_path:', url_path)
    print('payload:', payload)
    url = f"{server_url}{url_path}"

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"成功生成思维导图！\n 链接: {result.get('url')}\n 接收数据: {result.get('data_received')}")
            return result.get("url")
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}\n错误信息: {response.json().get('error', '未知错误')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求发生错误: {e}")
        return None

@mcp.tool()
def generate_mind_map(farmat_data: dict) -> str:
    """Generate a mind map based on the formatted data and return the link to the mind map. The input should be a valid JSON string and a title. If the reply language is not specified, use the language of the reference text. The format of the input data is as follows:
{"data":{"name":"flare","children":[{"name":"data","children":[{"name":"converters","children":[{"name":"Converters"},{"name":"DelimitedTextConverter"}]},{"name":"DataUtil"}]},{"name":"display","children":[{"name":"DirtySprite"},{"name":"LineSprite"},{"name":"RectSprite"}]},{"name":"flex","children":[{"name":"FlareVis"}]},{"name":"query","children":[{"name":"AggregateExpression"},{"name":"And"},{"name":"Arithmetic"},{"name":"Average"},{"name":"BinaryExpression"},{"name":"methods","children":[{"name":"add"},{"name":"and"},{"name":"average"},{"name":"count"},{"name":"distinct"}]},{"name":"Minimum"},{"name":"Not"}]},{"name":"scale","children":[{"name":"IScaleMap"},{"name":"LinearScale"},{"name":"LogScale"}]}]},"title":"数据库能力思维导图"}"""

    # json_str = json.dumps(farmat_data, ensure_ascii=False, indent=2)
    print("mindmap 被调用了！")
    print(f"收到的数据: {farmat_data}")
    return make_api_request("mindmap/api/mindmap/", farmat_data)

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

# if __name__ == "__main__":
#     # mcp.settings.host = "0.0.0.0"
#     # mcp.run(transport='sse')
#     mcp.settings.host = "127.0.0.1"  # 设置host为127.0.0.1
#     mcp.run(transport='streamable-http')
#     # mcp.run(transport='stdio')

def main() -> None:
    mcp.run(transport='stdio')