#!/usr/bin/env python3
"""
交互式监控器 - 监控Claude的交互式提示
专门检测 "Do you want to proceed?" 等需要用户选择的情况
"""
import os
import sys
import time
import subprocess
import requests
import re
from datetime import datetime
from dotenv import load_dotenv
from plyer import notification


class InteractiveMonitor:
    """交互式提示监控器"""

    def __init__(self):
        # 设置编码
        if sys.platform == 'win32':
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

        load_dotenv()
        self.serverchan_key = os.getenv('SERVERCHAN_KEY')
        self.last_clipboard = ""
        self.last_notification_time = 0
        self.running = True

        # 交互式提示关键词
        self.interactive_patterns = [
            r"Do you want to proceed\?",
            r">\s*1\.\s*Yes",
            r">\s*2\.\s*Yes.*don't ask again",
            r">\s*3\.\s*No.*tell Claude",
            r"选择.*操作",
            r"请选择",
            r"Continue\?",
            r"Proceed\?",
            r"是否继续",
            r"确认.*操作",
            r"Press.*continue",
            r"Enter.*choice",
            r"选项.*：",
            r"Options.*:",
            r"Choose.*option",
            r"\(y/n\)",
            r"\[Y/n\]",
            r"\[y/N\]"
        ]

        # 完成状态关键词
        self.completion_patterns = [
            r"✅",
            r"完成",
            r"任务.*完成",
            r"代码.*完成",
            r"Successfully",
            r"Done",
            r"Completed",
            r"Finished",
            r"正常运行",
            r"功能.*完整",
            r"系统.*正常",
            r"开发.*完成",
            r"创建.*成功",
            r"已.*创建"
        ]

        print("🎯 交互式Claude监控器启动")
        print("🔍 专门监控交互式提示和完成状态")
        print("📋 监控内容:")
        print("   - 📝 Do you want to proceed? 提示")
        print("   - 🎛️ 选择菜单 (1. Yes, 2. Yes and don't ask, 3. No)")
        print("   - ✅ 任务完成状态")
        print("   - 🔄 其他交互式提示")

    def get_clipboard(self):
        """获取剪贴板内容"""
        try:
            cmd = 'powershell -Command "Get-Clipboard"'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=1)
            return result.stdout.strip()
        except:
            return ""

    def check_interactive_prompt(self, text):
        """检查是否包含交互式提示"""
        if not text or len(text) < 5:
            return False

        for pattern in self.interactive_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def check_completion(self, text):
        """检查是否包含完成标志"""
        if not text or len(text) < 5:
            return False

        for pattern in self.completion_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def send_notification(self, title, message, category="通用"):
        """发送通知"""
        current_time = time.time()
        if current_time - self.last_notification_time < 10:  # 10秒防重复
            return

        self.last_notification_time = current_time

        print(f"🎉 检测到{category}提示！")
        print(f"📝 内容: {message[:100]}...")
        print(f"⏰ 时间: {datetime.now().strftime('%H:%M:%S')}")

        # 桌面通知
        try:
            notification.notify(
                title=title,
                message=message[:200] + "..." if len(message) > 200 else message,
                timeout=20,
                app_name="Claude交互监控"
            )
            print(f"🖥️ 桌面通知已发送")
        except Exception as e:
            print(f"❌ 桌面通知失败: {e}")

        # 微信通知
        if self.serverchan_key:
            try:
                url = f"https://sctapi.ftqq.com/{self.serverchan_key}.send"
                content = f"""
**{title}**

📍 **类型**: {category}
⏰ **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📝 **内容**:
```
{message[:500]}
```

💡 **提示**: 需要您进行选择或确认操作

🤖 *Claude交互式监控系统*
                """

                data = {
                    'title': title,
                    'desp': content
                }
                response = requests.post(url, data=data, timeout=5)
                if response.status_code == 200:
                    print(f"💬 微信通知已发送")
                else:
                    print(f"⚠️ 微信通知失败: {response.status_code}")
            except Exception as e:
                print(f"❌ 微信通知失败: {e}")

    def monitor_clipboard(self):
        """监控剪贴板内容"""
        print("🔍 开始监控剪贴板...")

        while self.running:
            try:
                current_clipboard = self.get_clipboard()

                if (current_clipboard != self.last_clipboard and
                    current_clipboard and
                    len(current_clipboard) > 10):

                    print(f"📋 检测到剪贴板更新: {current_clipboard[:50]}...")

                    # 检查交互式提示
                    if self.check_interactive_prompt(current_clipboard):
                        self.send_notification(
                            "🤖 Claude需要您的选择",
                            current_clipboard,
                            "交互式提示"
                        )

                    # 检查完成状态
                    elif self.check_completion(current_clipboard):
                        self.send_notification(
                            "✅ Claude任务完成",
                            current_clipboard,
                            "完成状态"
                        )

                    self.last_clipboard = current_clipboard

                time.sleep(0.5)  # 每0.5秒检查一次

            except Exception as e:
                print(f"剪贴板监控错误: {e}")
                time.sleep(2)

    def test_detection(self):
        """测试检测功能"""
        print("🧪 测试检测功能...")

        test_cases = [
            ("Do you want to proceed?", "交互式提示"),
            ("> 1. Yes", "交互式提示"),
            ("> 2. Yes, and don't ask again", "交互式提示"),
            ("> 3. No, and tell Claude what to do differently", "交互式提示"),
            ("✅ 任务完成", "完成状态"),
            ("Successfully created", "完成状态"),
            ("请选择操作", "交互式提示"),
            ("Continue? (y/n)", "交互式提示")
        ]

        for text, expected_type in test_cases:
            is_interactive = self.check_interactive_prompt(text)
            is_completion = self.check_completion(text)

            if expected_type == "交互式提示" and is_interactive:
                print(f"✅ 交互式检测: {text}")
            elif expected_type == "完成状态" and is_completion:
                print(f"✅ 完成状态检测: {text}")
            else:
                print(f"❌ 检测失败: {text}")

    def run(self):
        """启动监控"""
        try:
            # 测试检测功能
            self.test_detection()
            print()

            # 发送启动通知
            self.send_notification(
                "🤖 交互式监控器启动",
                "Claude交互式监控系统已启动，将监控选择提示和完成状态",
                "系统启动"
            )

            print("🚀 监控已启动")
            print("💡 使用说明:")
            print("   1. 当Claude显示选择菜单时，复制相关内容")
            print("   2. 当Claude完成任务时，复制完成信息")
            print("   3. 系统会自动检测并发送通知")
            print("⚠️  按 Ctrl+C 停止监控")

            # 开始监控
            self.monitor_clipboard()

        except KeyboardInterrupt:
            print("\n⏹️ 停止监控")
            self.running = False


def main():
    try:
        monitor = InteractiveMonitor()
        monitor.run()
    except Exception as e:
        print(f"❌ 启动失败: {e}")


if __name__ == "__main__":
    main()