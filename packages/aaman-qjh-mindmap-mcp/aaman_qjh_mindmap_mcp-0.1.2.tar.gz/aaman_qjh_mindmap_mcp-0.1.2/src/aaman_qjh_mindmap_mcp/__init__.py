
import json

import requests
# server.py
from mcp.server.fastmcp import FastMCP
server_url = "http://115.190.100.203/"
# server_url = "http://115.190.100.203:8001/"
# Create an MCP server
mcp = FastMCP("Demo")
# ======================================================================
#                               思维导图
# ======================================================================

def api_geturl_mindmap(payload):
    # 设置请求头为 application/json
    headers = {
        "Content-Type": "application/json"
    }
    # API 地址（确保你的 Django 服务正在运行）
    url = f"{server_url}chart/api/mindmap/"
    try:
        # 发送 POST 请求，data 需要 json.dumps 序列化，或使用 json 参数自动处理
        response = requests.post(url, data=json.dumps(payload), headers=headers)

        # 或者更简洁的方式：使用 json 参数（requests 会自动设置 Content-Type 和序列化）
        # response = requests.post(url, json=payload)

        # 检查响应状态码
        if response.status_code == 201 or response.status_code == 200:
            result = response.json()  # 解析返回的 JSON
            print("[SUCCESS]  成功生成思维导图！")
            print("链接:", result.get("url"))
            print("接收数据:", result.get("data_received"))
        else:
            print("[ERROR]  请求失败，状态码:", response.status_code)
            print("错误信息:", response.json().get("error", "未知错误"))

    except requests.exceptions.ConnectionError:
        print("[ERROR]  连接失败：请确保 Django 服务正在运行（python manage.py runserver）")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR]  请求发生错误: {e}")
    return result.get("url")

@mcp.tool()
def generate_mind_map(farmat_data: dict) -> str:
    """Generate a mind map based on the formatted data and return the link to the mind map. The input should be a valid JSON string and a title. If the reply language is not specified, use the language of the reference text. The format of the input data is as follows:
{"data":{"name":"flare","children":[{"name":"data","children":[{"name":"converters","children":[{"name":"Converters"},{"name":"DelimitedTextConverter"}]},{"name":"DataUtil"}]},{"name":"display","children":[{"name":"DirtySprite"},{"name":"LineSprite"},{"name":"RectSprite"}]},{"name":"flex","children":[{"name":"FlareVis"}]},{"name":"query","children":[{"name":"AggregateExpression"},{"name":"And"},{"name":"Arithmetic"},{"name":"Average"},{"name":"BinaryExpression"},{"name":"methods","children":[{"name":"add"},{"name":"and"},{"name":"average"},{"name":"count"},{"name":"distinct"}]},{"name":"Minimum"},{"name":"Not"}]},{"name":"scale","children":[{"name":"IScaleMap"},{"name":"LinearScale"},{"name":"LogScale"}]}]},"title":"数据库能力思维导图"}"""

    return api_geturl_mindmap(farmat_data)
# ======================================================================
#                               面积图
# ======================================================================

def api_geturl_area_basic(payload):
    # 设置请求头为 application/json
    headers = {
        "Content-Type": "application/json"
    }
    # API 地址（确保你的 Django 服务正在运行）
    url = f"{server_url}chart/api/area_basic/"
    try:
        # 发送 POST 请求，data 需要 json.dumps 序列化，或使用 json 参数自动处理
        response = requests.post(url, data=json.dumps(payload), headers=headers)

        # 或者更简洁的方式：使用 json 参数（requests 会自动设置 Content-Type 和序列化）
        # response = requests.post(url, json=payload)

        # 检查响应状态码
        if response.status_code == 201 or response.status_code == 200:
            result = response.json()  # 解析返回的 JSON
            print("[SUCCESS]  成功生成面积图！")
            print(" 链接:", result.get("url"))
            print("接收数据:", result.get("data_received"))
        else:
            print("[ERROR]  请求失败，状态码:", response.status_code)
            print("错误信息:", response.json().get("error", "未知错误"))

    except requests.exceptions.ConnectionError:
        print("[ERROR]  连接失败：请确保 Django 服务正在运行（python manage.py runserver）")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR]  请求发生错误: {e}")
    return result.get("url")

@mcp.tool()
def generate_area_chart(farmat_data: dict) -> str:
    """
        Generate an area chart based on the provided data and return a URL to the rendered chart image.

    The input is a valid JSON object with the following fields:
    - data: A list of dictionaries containing the data points (e.g., time-series or category-value pairs).
    - title: The chart title.
    - axisXTitle: Label for the X-axis.
    - axisYTitle: Label for the Y-axis.
    - style: Optional. A dictionary specifying visual styles (e.g., color, line type). Can be omitted or empty.

    If the response language is not specified, the output should match the language of the input text.

    Example input:
    {
        "data": [
            {"name": "2025-10-14", "value": 12},
            {"name": "2025-10-15", "value": 15},
            {"name": "2025-10-16", "value": 18}
        ],
        "title": "Website Daily Unique Visitors Trend",
        "axisXTitle": "Date",
        "axisYTitle": "Visitors (in thousands)",
        "style": {}
    }
    The structure and keys must match the provided format precisely.
    Returns:
        str: A direct URL to the generated area chart image or interactive visualization.
"""
    return api_geturl_area_basic(farmat_data)



# ======================================================================
#                               柱状图
# ======================================================================

def api_geturl_bar_chart(payload):
    # 设置请求头为 application/json
    headers = {
        "Content-Type": "application/json"
    }
    # API 地址（确保你的 Django 服务正在运行）
    url = f"{server_url}chart/api/bar_chart/"
    try:
        # 发送 POST 请求，data 需要 json.dumps 序列化，或使用 json 参数自动处理
        response = requests.post(url, data=json.dumps(payload), headers=headers)

        # 或者更简洁的方式：使用 json 参数（requests 会自动设置 Content-Type 和序列化）
        # response = requests.post(url, json=payload)

        # 检查响应状态码
        if response.status_code == 201 or response.status_code == 200:
            result = response.json()  # 解析返回的 JSON
            print("[SUCCESS]  成功生成柱状图！")
            print(" 链接:", result.get("url"))
            print("接收数据:", result.get("data_received"))
        else:
            print("[ERROR]  请求失败，状态码:", response.status_code)
            print("错误信息:", response.json().get("error", "未知错误"))

    except requests.exceptions.ConnectionError:
        print("[ERROR]  连接失败：请确保 Django 服务正在运行（python manage.py runserver）")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR]  请求发生错误: {e}")
    return result.get("url")

@mcp.tool()
def generate_bar_chart(farmat_data: dict) -> str:
    """

    Generate a bar chart from the input JSON data.

    Input format:
    {
      "data": [{"name": "A", "value": 30}, {"name": "B", "value": 50}],  // array of objects
      "title": "Chart Title",
      "axisXTitle": "X Axis Label",
      "axisYTitle": "Y Axis Label",
      "style": {"palette":["#1E90FF","#3CB371"]  // optional, can be empty
    }
    The structure and keys must match the provided format precisely.
    Return a direct URL to the rendered bar chart image,is a html,not image.
    If response language is not specified, use the language of the input text.

"""
    return api_geturl_bar_chart(farmat_data)


# ======================================================================
#                               折线图
# ======================================================================

def api_geturl_line_chart(payload):
    # 设置请求头为 application/json
    headers = {
        "Content-Type": "application/json"
    }
    # API 地址（确保你的 Django 服务正在运行）
    url = f"{server_url}chart/api/line_chart/"
    try:
        # 发送 POST 请求，data 需要 json.dumps 序列化，或使用 json 参数自动处理
        response = requests.post(url, data=json.dumps(payload), headers=headers)

        # 或者更简洁的方式：使用 json 参数（requests 会自动设置 Content-Type 和序列化）
        # response = requests.post(url, json=payload)

        # 检查响应状态码
        if response.status_code == 201 or response.status_code == 200:
            result = response.json()  # 解析返回的 JSON
            print("[SUCCESS]  成功生成折现图！")
            print(" 链接:", result.get("url"))
            print("接收数据:", result.get("data_received"))
        else:
            print("[ERROR]  请求失败，状态码:", response.status_code)
            print("错误信息:", response.json().get("error", "未知错误"))

    except requests.exceptions.ConnectionError:
        print("[ERROR]  连接失败：请确保 Django 服务正在运行（python manage.py runserver）")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR]  请求发生错误: {e}")
    return result.get("url")

@mcp.tool()
def generate_line_chart(farmat_data: dict) -> str:
    """

    Generate a bar chart from the input JSON data.

    Input format:
    {
      "data": [{"name": "A", "value": 30}, {"name": "B", "value": 50}],  // array of objects
      "title": "Chart Title",
      "axisXTitle": "X Axis Label",
      "axisYTitle": "Y Axis Label",
    }
    The structure and keys must match the provided format precisely.
    Return a direct URL to the rendered bar chart image,is a html,not image.
    If response language is not specified, use the language of the input text.

"""
    return api_geturl_line_chart(farmat_data)


# ======================================================================
#                               饼图
# ======================================================================

def api_geturl_pie_chart(payload):
    # 设置请求头为 application/json
    headers = {
        "Content-Type": "application/json"
    }
    # API 地址（确保你的 Django 服务正在运行）
    url = f"{server_url}chart/api/pie_chart/"
    try:
        # 发送 POST 请求，data 需要 json.dumps 序列化，或使用 json 参数自动处理
        response = requests.post(url, data=json.dumps(payload), headers=headers)

        # 或者更简洁的方式：使用 json 参数（requests 会自动设置 Content-Type 和序列化）
        # response = requests.post(url, json=payload)

        # 检查响应状态码
        if response.status_code == 201 or response.status_code == 200:
            result = response.json()  # 解析返回的 JSON
            print("[SUCCESS]  成功生成饼图！")
            print(" 链接:", result.get("url"))
            print("接收数据:", result.get("data_received"))
        else:
            print("[ERROR]  请求失败，状态码:", response.status_code)
            print("错误信息:", response.json().get("error", "未知错误"))

    except requests.exceptions.ConnectionError:
        print("[ERROR]  连接失败：请确保 Django 服务正在运行（python manage.py runserver）")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR]  请求发生错误: {e}")
    return result.get("url")

@mcp.tool()
def generate_pie_chart(farmat_data: dict) -> str:
    """

    Generate a pie chart from the input JSON data.

    Input format:
    {
      "data": [{"name": "A", "value": 30}, {"name": "B", "value": 50}],  // array of objects
      "title": "Chart Title",
    }
    The structure and keys must match the provided format precisely.
    Return a direct URL to the rendered bar chart image,is a html,not image.
    If response language is not specified, use the language of the input text.

"""
    return api_geturl_pie_chart(farmat_data)


# ======================================================================
#                               横向条形图（柱状图）
# ======================================================================

def api_geturl_horizontal_bar_chart(payload):
    # 设置请求头为 application/json
    headers = {
        "Content-Type": "application/json"
    }
    # API 地址（确保你的 Django 服务正在运行）
    url = f"{server_url}chart/api/horizontal_bar_chart/"
    try:
        # 发送 POST 请求，data 需要 json.dumps 序列化，或使用 json 参数自动处理
        response = requests.post(url, data=json.dumps(payload), headers=headers)

        # 或者更简洁的方式：使用 json 参数（requests 会自动设置 Content-Type 和序列化）
        # response = requests.post(url, json=payload)

        # 检查响应状态码
        if response.status_code == 201 or response.status_code == 200:
            result = response.json()  # 解析返回的 JSON
            print("[SUCCESS]  成功生成横向条形图！")
            print(" 链接:", result.get("url"))
            print("接收数据:", result.get("data_received"))
        else:
            print("[ERROR]  请求失败，状态码:", response.status_code)
            print("错误信息:", response.json().get("error", "未知错误"))

    except requests.exceptions.ConnectionError:
        print("[ERROR]  连接失败：请确保 Django 服务正在运行（python manage.py runserver）")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR]  请求发生错误: {e}")
    return result.get("url")

@mcp.tool()
def generate_horizontal_bar_chart(farmat_data: dict) -> str:
    """

    Generate a horizontal bar chart based on the input JSON data..

    Input format:
    {
      "data": [{"name": "A", "value": 30}, {"name": "B", "value": 50}],  // array of objects
      "title": "Chart Title",
      "axisXTitle": "X Axis Label",
      "axisYTitle": "Y Axis Label",
      "style": {"palette":["#1E90FF","#3CB371"]  // optional, can be empty
    }
    The structure and keys must match the provided format precisely.
    Return a direct URL to the rendered bar chart image,is a html,not image.
    If response language is not specified, use the language of the input text.

"""
    return api_geturl_horizontal_bar_chart(farmat_data)


# ======================================================================
#                               箱式图（盒须图）
# ======================================================================

def api_geturl_boxplot_chart(payload):
    # 设置请求头为 application/json
    headers = {
        "Content-Type": "application/json"
    }
    # API 地址（确保你的 Django 服务正在运行）
    url = f"{server_url}chart/api/boxplot_chart/"
    try:
        # 发送 POST 请求，data 需要 json.dumps 序列化，或使用 json 参数自动处理
        response = requests.post(url, data=json.dumps(payload), headers=headers)

        # 或者更简洁的方式：使用 json 参数（requests 会自动设置 Content-Type 和序列化）
        # response = requests.post(url, json=payload)

        # 检查响应状态码
        if response.status_code == 201 or response.status_code == 200:
            result = response.json()  # 解析返回的 JSON
            print("[SUCCESS]  成功生成横向条形图！")
            print(" 链接:", result.get("url"))
            print("接收数据:", result.get("data_received"))
        else:
            print("[ERROR]  请求失败，状态码:", response.status_code)
            print("错误信息:", response.json().get("error", "未知错误"))

    except requests.exceptions.ConnectionError:
        print("[ERROR]  连接失败：请确保 Django 服务正在运行（python manage.py runserver）")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR]  请求发生错误: {e}")
    return result.get("url")

@mcp.tool()
def generate_boxplot_chart(farmat_data: dict) -> str:
    """
        箱式图
        Generate a box plot chart based on the input JSON data.

        Input format:
        {
        "title": "Chart Main Title",                        // required
        "subtitle": "Optional subtitle (e.g., IQR rule)",   // optional
        "axisXTitle": "X Axis Label",                       // required
        "axisYTitle": "Y Axis Label with unit",             // required
        "data": [[850, 740, ...], [960, 940, ...], ...],    // required, array of numeric arrays
        "groupNames": ["expr 1", "expr 2", ...],            // optional, labels for each group
        "showOutliers": true,                               // optional, default true
        "iqrMultiplier": 1.5,                               // optional, default 1.5
        }
        The structure and keys must match the provided format precisely.
        Return a direct URL to the rendered box plot image,is a html,not image.
        If response language is not specified, use the language of the input text.

"""
    return api_geturl_boxplot_chart(farmat_data)
# ======================================================================
#                               折线柱状混合图
# ======================================================================

def api_geturl_mix_line_bar_chart(payload):
    # 设置请求头为 application/json
    headers = {
        "Content-Type": "application/json"
    }
    # API 地址（确保你的 Django 服务正在运行）
    url = f"{server_url}chart/api/mix_line_bar_chart/"
    try:
        # 发送 POST 请求，data 需要 json.dumps 序列化，或使用 json 参数自动处理
        response = requests.post(url, data=json.dumps(payload), headers=headers)

        # 或者更简洁的方式：使用 json 参数（requests 会自动设置 Content-Type 和序列化）
        # response = requests.post(url, json=payload)

        # 检查响应状态码
        if response.status_code == 201 or response.status_code == 200:
            result = response.json()  # 解析返回的 JSON
            print("[SUCCESS]  成功生成折线柱状混合图！")
            print(" 链接:", result.get("url"))
            print("接收数据:", result.get("data_received"))
        else:
            print("[ERROR]  请求失败，状态码:", response.status_code)
            print("错误信息:", response.json().get("error", "未知错误"))

    except requests.exceptions.ConnectionError:
        print("[ERROR]  连接失败：请确保 Django 服务正在运行（python manage.py runserver）")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR]  请求发生错误: {e}")
    return result.get("url")

@mcp.tool()
def generate_mix_line_bar_chart(farmat_data: dict) -> str:
    """
        Generate a line and column mixed chart based on the input JSON data.

        Input format:
        {
        "title": "Chart Title",
        "categories": ["Jan", "Feb", "Mar"], // array of strings
        "series": [
        {
        "type": "column",
        "data": [10, 20, 30], // array of numbers
        "axisYTitle": "Column Axis Title"
        },
        {
        "type": "line",
        "data": [5, 10, 15], // array of numbers
        "axisYTitle": "Line Axis Title"
        }
        ],
        "axisXTitle": "X Axis Title"
        }
        The structure and keys must match the provided format precisely.
        Return a direct URL to the rendered line and column mixed chart image,is a html,not image.
        If response language is not specified, use the language of the input text.

"""
    print(api_geturl_mix_line_bar_chart(farmat_data))
    return api_geturl_mix_line_bar_chart(farmat_data)

# ======================================================================
#                               雷达图
# ======================================================================

def api_geturl_radar_chart(payload):
    # 设置请求头为 application/json
    headers = {
        "Content-Type": "application/json"
    }
    # API 地址（确保你的 Django 服务正在运行）
    url = f"{server_url}chart/api/radar_chart/"
    try:
        # 发送 POST 请求，data 需要 json.dumps 序列化，或使用 json 参数自动处理
        response = requests.post(url, data=json.dumps(payload), headers=headers)

        # 或者更简洁的方式：使用 json 参数（requests 会自动设置 Content-Type 和序列化）
        # response = requests.post(url, json=payload)

        # 检查响应状态码
        if response.status_code == 201 or response.status_code == 200:
            result = response.json()  # 解析返回的 JSON
            print("[SUCCESS]  成功生成雷达图！")
            print(" 链接:", result.get("url"))
            print("接收数据:", result.get("data_received"))
        else:
            print("[ERROR]  请求失败，状态码:", response.status_code)
            print("错误信息:", response.json().get("error", "未知错误"))

    except requests.exceptions.ConnectionError:
        print("[ERROR]  连接失败：请确保 Django 服务正在运行（python manage.py runserver）")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR]  请求发生错误: {e}")
    return result.get("url")

@mcp.tool()
def generate_radar_chart(farmat_data: dict) -> str:
    """
        Generate a radar chart to display multi - dimensional data (four or more dimensions).

        Input format:
        {
            "title": "Radar Chart Title",
            "data": [
                {
                "value": [100, 200...], // array of numbers representing values for each dimension
                "name": "Data Series 1"
                },
                {
                "value": [150, 250...],
                "name": "Data Series 2"
                }
            ],
            "indicator": [
                {
                "name": "Dimension 1",
                "max": 600
                },
                {
                "name": "Dimension 2",
                "max": 700
                }...
            ]
        }
        The structure and keys must match the provided format precisely.
        Return a direct URL to the rendered radar chart,is a html,not image.
        If response language is not specified, use the language of the input text.
"""
    return api_geturl_radar_chart(farmat_data)


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

# if __name__ == "__main__":
#     # mcp.settings.host = "0.0.0.0"
#     # mcp.run(transport='sse')
#     mcp.run(transport='streamable-http')
#     # mcp.run(transport='stdio')

def main() -> None:
    # print("Hello from aaman-qjh-echarts-mcp!")
    mcp.run(transport='stdio')
