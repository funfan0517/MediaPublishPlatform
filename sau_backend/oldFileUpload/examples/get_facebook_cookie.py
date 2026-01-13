"""
Facebook平台Cookie获取示例
"""
import asyncio
import json
from pathlib import Path
from conf import BASE_DIR

async def get_facebook_cookie():
    """
    获取Facebook平台Cookie
    """
    try:
        from playwright.async_api import async_playwright
        
        # 创建cookie保存目录
        cookie_dir = Path(BASE_DIR / "cookiesFile")
        cookie_dir.mkdir(parents=True, exist_ok=True)
        
        cookie_file = cookie_dir / "facebook_cookie.json"
        
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            print("正在打开Facebook登录页面，请手动登录...")
            
            # 导航到登录页面
            await page.goto("https://www.facebook.com/login")
            
            # 等待用户手动登录完成
            print("请在浏览器中完成登录操作")
            
            # 等待登录成功的标识（Facebook登录成功后会重定向到主页）
            await page.wait_for_url("https://www.facebook.com/", timeout=300000)  # 5分钟超时
            
            # 获取并保存Cookie
            cookies = await page.context.cookies()
            
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Facebook Cookie已成功保存到: {cookie_file}")
            
            # 关闭浏览器
            await browser.close()
            
    except Exception as e:
        print(f"❌ 获取Facebook Cookie失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(get_facebook_cookie())
