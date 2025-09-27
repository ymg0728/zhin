#!/usr/bin/env python3
"""
直接测试监控器 - 立即测试通知功能
"""
import os
import sys
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from plyer import notification


def main():
    # 设置编码
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

    load_dotenv()
    serverchan_key = os.getenv('SERVERCHAN_KEY')

    print("🧪 直接测试Claude通知系统")
    print("=" * 50)

    # 1. 测试桌面通知
    print("🖥️ 测试桌面通知...")
    try:
        notification.notify(
            title="🎉 Vue后台开发完成",
            message="系统功能状态：✅ Vue 3 + Vite 正常运行",
            timeout=15,
            app_name="Claude监控测试"
        )
        print("✅ 桌面通知发送成功")
    except Exception as e:
        print(f"❌ 桌面通知失败: {e}")

    # 2. 测试微信通知
    if serverchan_key:
        print("💬 测试微信通知...")
        try:
            url = f"https://sctapi.ftqq.com/{serverchan_key}.send"
            content = f"""
**🎉 Claude开发完成检测**

📋 **系统功能状态**
- ✅ Vue 3 + Vite: 正常运行
- ✅ Vue Router: 路由功能完整
- ✅ Element Plus: UI组件可用
- ✅ 响应式布局: 移动端适配
- ✅ 依赖管理: 版本稳定

🎯 **下一步计划**
1. 立即测试 - 访问 http://localhost:8088/admin
2. 验证功能 - 点击左侧导航栏各个管理模块
3. 确认满意 - 如果功能正常，继续开发剩余页面

⏰ **检测时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🤖 *Claude通知系统测试*
            """

            data = {
                'title': "🎉 Vue后台系统开发完成",
                'desp': content
            }

            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                print("✅ 微信通知发送成功")
                print("📱 请检查微信是否收到通知")
            else:
                print(f"❌ 微信通知失败: HTTP {response.status_code}")

        except Exception as e:
            print(f"❌ 微信通知失败: {e}")
    else:
        print("⚠️ 未配置Server酱密钥，跳过微信通知")

    # 3. 验证监控逻辑
    print("\n🔍 验证监控检测逻辑...")
    test_text = """
    📋 系统功能状态
    - ✅ Vue 3 + Vite: 正常运行
    - ✅ Vue Router: 路由功能完整
    - ✅ Element Plus: UI组件可用
    重要提醒: 现在您可以正常访问后台管理系统，不再是空白页面！
    """

    patterns = [
        r"✅",
        r"完成",
        r"正常运行",
        r"功能.*完整",
        r"系统.*正常",
        r"开发.*完成"
    ]

    import re
    detected = []
    for pattern in patterns:
        if re.search(pattern, test_text, re.IGNORECASE):
            detected.append(pattern)

    print(f"📝 测试文本中检测到的关键词: {detected}")

    if detected:
        print("✅ 检测逻辑正常 - 应该会触发通知")
    else:
        print("❌ 检测逻辑异常 - 无法识别完成标志")

    print("\n📊 测试总结:")
    print("- 如果收到桌面通知 = 桌面通知系统正常")
    print("- 如果收到微信消息 = 微信通知系统正常")
    print("- 如果都没收到 = 需要检查配置或权限")


if __name__ == "__main__":
    main()