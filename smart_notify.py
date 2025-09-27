#!/usr/bin/env python3
"""
智能Claude通知器
监控多种来源检测Claude完成状态
"""
import time
import re
import os
import subprocess
import requests
import threading
from datetime import datetime
from dotenv import load_dotenv
from plyer import notification

class SmartClaudeNotifier:
    """智能Claude通知器"""

    def __init__(self):
        load_dotenv()
        import sys
        if sys.platform == 'win32':
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

        self.serverchan_key = os.getenv('SERVERCHAN_KEY')
        self.last_clipboard = ""
        self.last_notification_time = 0
        self.running = True

        # 扩展的完成标识符
        self.patterns = [
            r"✅",
            r"完成",
            r"任务.*完成",
            r"代码.*完成",
            r"Successfully",
            r"Done",
            r"Completed",
            r"Finished",
            r"Task.*complete",
            r"Implementation.*complete",
            r"Generated.*code",
            r"Here.*is.*the.*code",
            r"I.*have.*created",
            r"机器人.*完成",
            r"已.*完成",
        ]

        print("🤖 智能Claude通知器启动")
        print("🔍 正在监控多种来源...")
        print("📋 监控内容：剪贴板、控制台输出")
        print("⚠️  按 Ctrl+C 停止")

    def get_clipboard(self):
        """获取剪贴板内容"""
        try:
            cmd = 'powershell -Command "Get-Clipboard"'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=1)
            return result.stdout.strip()
        except:
            return ""

    def get_recent_console_history(self):
        """获取最近的控制台历史"""
        try:
            # 获取PowerShell历史
            cmd = 'powershell -Command "(Get-History | Select-Object -Last 5).CommandLine"'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=2)
            return result.stdout.strip()
        except:
            return ""

    def check_completion(self, text):
        """检查是否包含完成标志"""
        if not text or len(text) < 5:
            return False

        for pattern in self.patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def send_notification(self, title, message, source=""):
        """发送通知"""
        current_time = time.time()
        if current_time - self.last_notification_time < 20:  # 20秒防重复
            return

        self.last_notification_time = current_time

        print(f"🎉 检测到完成信号！")
        print(f"📍 来源: {source}")
        print(f"📝 内容: {message[:100]}...")

        # 桌面通知
        try:
            notification.notify(
                title=title,
                message=message[:100] + "..." if len(message) > 100 else message,
                timeout=15
            )
            print(f"🖥️ 桌面通知已发送")
        except Exception as e:
            print(f"❌ 桌面通知失败: {e}")

        # 微信通知
        if self.serverchan_key:
            try:
                url = f"https://sctapi.ftqq.com/{self.serverchan_key}.send"
                content = f"""
**Claude任务完成检测**

📍 **来源**: {source}
⏰ **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📝 **内容预览**:
```
{message[:300]}
```
                """

                data = {
                    'title': title,
                    'desp': content
                }
                response = requests.post(url, data=data, timeout=5)
                if response.status_code == 200:
                    print(f"💬 微信通知已发送")
                else:
                    print(f"⚠️ 微信通知失败: HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ 微信通知失败: {e}")

    def monitor_clipboard(self):
        """监控剪贴板"""
        while self.running:
            try:
                current_clipboard = self.get_clipboard()

                if (current_clipboard != self.last_clipboard and
                    current_clipboard and
                    len(current_clipboard) > 20):  # 有意义的内容

                    if self.check_completion(current_clipboard):
                        self.send_notification(
                            "🎉 Claude任务完成",
                            current_clipboard,
                            "剪贴板"
                        )

                    self.last_clipboard = current_clipboard

                time.sleep(1)  # 每秒检查

            except Exception as e:
                print(f"剪贴板监控错误: {e}")
                time.sleep(3)

    def monitor_console(self):
        """监控控制台输出"""
        last_history = ""

        while self.running:
            try:
                current_history = self.get_recent_console_history()

                if (current_history != last_history and
                    current_history and
                    len(current_history) > 10):

                    if self.check_completion(current_history):
                        self.send_notification(
                            "🎉 Claude控制台完成",
                            current_history,
                            "控制台历史"
                        )

                    last_history = current_history

                time.sleep(3)  # 每3秒检查

            except Exception as e:
                print(f"控制台监控错误: {e}")
                time.sleep(5)

    def test_notification(self):
        """测试通知功能"""
        print("📧 测试通知功能...")
        self.send_notification(
            "🧪 测试通知",
            "这是一条测试通知，确认通知系统正常工作",
            "测试"
        )

    def run(self):
        """启动监控"""
        try:
            # 先测试通知
            self.test_notification()
            time.sleep(2)

            print("🚀 启动多线程监控...")

            # 启动剪贴板监控线程
            clipboard_thread = threading.Thread(target=self.monitor_clipboard)
            clipboard_thread.daemon = True
            clipboard_thread.start()
            print("✅ 剪贴板监控已启动")

            # 启动控制台监控线程
            console_thread = threading.Thread(target=self.monitor_console)
            console_thread.daemon = True
            console_thread.start()
            print("✅ 控制台监控已启动")

            print("🔍 智能监控运行中...")
            print("💡 提示：当Claude完成任务时会自动通知")

            # 主循环保持程序运行
            while self.running:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n⏹️ 接收到停止信号")
            self.running = False
            print("👋 监控已停止")

if __name__ == "__main__":
    notifier = SmartClaudeNotifier()
    notifier.run()