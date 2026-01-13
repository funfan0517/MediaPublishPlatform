"""
Facebook平台配置文件
"""

class Facebook_Locator:
    """Facebook平台元素定位器"""
    
    # 默认定位器
    default = {
        "login_button": "button[name='login']",
        "username_input": "input[name='email']",
        "password_input": "input[name='pass']",
        "upload_button": "//span[text()='Photo/Video']",
        "file_input": "input[type='file']",
        "title_input": "[contenteditable='true']",
        "tags_input": "[contenteditable='true']",
        "publish_button": "//span[text()='Post']"
    }
    
    # 特定场景下的定位器
    pages = {
        "upload_button": "//span[text()='Create Post']",
        "video_upload_option": "//span[text()='Upload Video']"
    }
