import requests
import json
import os
import sys
from datetime import datetime

"""
简易API接口测试工具
功能：测试和可视化调用系统提供的所有API接口
使用方法：python api_tester.py [api_name] [params_json]
"""

# API基础URL
BASE_URL = "http://localhost:5409"

# 系统API接口定义
API_ENDPOINTS = {
    # 账号管理API
    "get_valid_accounts": {"url": "/getValidAccounts", "method": "GET", "description": "获取有效账号列表（带验证）"},
    "get_accounts": {"url": "/getAccounts", "method": "GET", "description": "获取账号列表（不带验证，快速加载）"},
    "add_account": {"url": "/account", "method": "POST", "description": "添加账号"},
    "update_account": {"url": "/updateUserinfo", "method": "POST", "description": "更新账号"},
    "delete_account": {"url": "/deleteAccount", "method": "GET", "description": "删除账号"},
    
    # 素材管理API
    "get_all_materials": {"url": "/getFiles", "method": "GET", "description": "获取所有素材"},
    "upload_material": {"url": "/uploadSave", "method": "POST", "description": "上传素材"},
    "delete_material": {"url": "/deleteFile", "method": "GET", "description": "删除素材"},
    
    # 用户相关API
    "get_user_info": {"url": "/user/{id}", "method": "GET", "description": "获取用户信息"},
    "get_user_list": {"url": "/user/list", "method": "GET", "description": "获取用户列表"},
    "create_user": {"url": "/user", "method": "POST", "description": "创建用户"},
    "update_user": {"url": "/user/{id}", "method": "PUT", "description": "更新用户信息"},
    "delete_user": {"url": "/user/{id}", "method": "DELETE", "description": "删除用户"},
    "login": {"url": "/auth/login", "method": "POST", "description": "用户登录"},
    "register": {"url": "/auth/register", "method": "POST", "description": "用户注册"},
    "logout": {"url": "/auth/logout", "method": "POST", "description": "用户登出"},
    "refresh_token": {"url": "/auth/refresh", "method": "POST", "description": "刷新token"}
}

def print_usage():
    """打印使用帮助信息"""
    print("\n简易API接口测试工具")
    print("使用方法:")
    print("  python api_tester.py               - 显示所有可用API")
    print("  python api_tester.py [api_name]    - 执行指定API（使用默认参数）")
    print("  python api_tester.py [api_name] '{\"param1\": \"value1\"}' - 执行指定API（使用自定义参数）")
    print("\n可用API列表:")
    
    # 按类别分组显示API
    categories = {}
    for api_name, info in API_ENDPOINTS.items():
        category = api_name.split('_')[0]
        if category not in categories:
            categories[category] = []
        categories[category].append((api_name, info))
    
    for category, apis in categories.items():
        print(f"\n{category.upper()} 相关API:")
        for api_name, info in apis:
            print(f"  {api_name} - {info['description']} [{info['method']}] {info['url']}")

def format_response(response):
    """格式化API响应输出"""
    print(f"\nHTTP 状态码: {response.status_code}")
    print(f"响应时间: {response.elapsed.total_seconds():.2f} 秒")
    print("响应头:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    print("\n响应内容:")
    try:
        # 尝试以JSON格式显示
        data = response.json()
        formatted_json = json.dumps(data, ensure_ascii=False, indent=2)
        
        # 如果JSON内容太长，只显示前1000个字符
        if len(formatted_json) > 1000:
            print(formatted_json[:1000] + "...")
            print(f"\n(显示部分内容，完整响应长度: {len(formatted_json)} 字符)")
        else:
            print(formatted_json)
    except json.JSONDecodeError:
        # 如果不是JSON，直接显示文本内容
        text = response.text
        if len(text) > 1000:
            print(text[:1000] + "...")
            print(f"\n(显示部分内容，完整响应长度: {len(text)} 字符)")
        else:
            print(text)

def export_response(api_name, response):
    """导出API响应到文件"""
    # 确保导出目录存在
    export_dir = "api_responses"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    
    # 准备导出数据
    export_data = {
        "api_name": api_name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "url": response.url,
        "status_code": response.status_code,
        "response_time": response.elapsed.total_seconds(),
        "headers": dict(response.headers)
    }
    
    # 尝试解析响应内容
    try:
        export_data["content"] = response.json()
    except:
        export_data["content"] = response.text
    
    # 导出到JSON文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(export_dir, f"{api_name}_{timestamp}.json")
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n响应已导出到: {filename}")

def execute_api(api_name, params=None):
    """执行指定的API"""
    if api_name not in API_ENDPOINTS:
        print(f"错误: API '{api_name}' 不存在!")
        print_usage()
        return
    
    api_info = API_ENDPOINTS[api_name]
    url = BASE_URL + api_info["url"]
    method = api_info["method"]
    
    print(f"\n{'='*60}")
    print(f"执行API: {api_name}")
    print(f"描述: {api_info['description']}")
    print(f"URL: {url}")
    print(f"方法: {method}")
    if params:
        print(f"参数: {json.dumps(params, ensure_ascii=False, indent=2)}")
    print(f"{'='*60}")
    
    try:
        # 处理URL中的路径参数（如 /user/{id}）
        if params and '{' in url:
            for key, value in params.items():
                if f"{{{key}}}" in url:
                    url = url.replace(f"{{{key}}}", str(value))
                    # 从params中移除已处理的路径参数
                    params.pop(key)
        
        # 发送请求
        if method == "GET":
            response = requests.get(url, params=params, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=params, timeout=30)
        elif method == "PUT":
            response = requests.put(url, json=params, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, timeout=30)
        else:
            print(f"不支持的请求方法: {method}")
            return
        
        # 格式化显示响应
        format_response(response)
        
        # 询问是否导出响应
        export_choice = input("\n是否将响应导出为文件? (y/n): ")
        if export_choice.lower() == 'y':
            export_response(api_name, response)
            
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到API服务器!")
        print(f"请确认服务器正在运行: {BASE_URL}")
    except Exception as e:
        print(f"请求执行出错: {str(e)}")

def main():
    print(f"\n简易API接口测试工具 v1.0")
    print(f"API基础URL: {BASE_URL}")
    
    # 检查命令行参数
    if len(sys.argv) == 1:
        # 没有参数，显示帮助信息
        print_usage()
        return
    
    api_name = sys.argv[1]
    params = None
    
    # 解析参数
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            print("错误: 参数格式不正确，请使用JSON格式!")
            print("示例: '{\"param1\": \"value1\", \"param2\": 123}'")
            return
    
    # 执行API
    execute_api(api_name, params)

if __name__ == "__main__":
    main()