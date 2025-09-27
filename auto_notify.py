#!/usr/bin/env python3
"""
简化版Claude自动通知器
监控剪贴板内容，检测Claude完成标志并发送通知
"""
import time
import re
import os
import subprocess
import requests
from datetime import datetime
from dotenv import load_dotenv
from plyer import notification

class SimpleClaudeNotifier:
    """简化版Claude通知器"""

    def __init__(self):
        load_dotenv()
        self.serverchan_key = os.getenv('SERVERCHAN_KEY')
        self.last_clipboard = ""
        self.last_notification_time = 0

        # 完成标识符
        self.patterns = [
            r"✅.*完成",
            r"完成.*代码",
            r"任务.*完成",
            r"Successfully.*",
            r"Done\.",
            r"完成！",
            r"代码已.*完成"
        ]

    def get_clipboard(self):
        """获取剪贴板内容"""
        try:
            cmd = 'powershell -Command "Get-Clipboard"'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=2)
            return result.stdout.strip()
        except:
            return ""

    def check_completion(self, text):
        """检查是否包含完成标志"""
        for pattern in self.patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def send_notification(self, message):
        """发送通知"""
        current_time = time.time()
        if current_time - self.last_notification_time < 30:  # 30秒防重复
            return

        self.last_notification_time = current_time

        # 桌面通知
        try:
            notification.notify(
                title="🎉 Claude任务完成",
                message=message[:100],
                timeout=10
            )
            print(f"🖥️ 桌面通知: {message[:50]}...")
        except Exception as e:
            print(f"桌面通知失败: {e}")

        # 微信通知
        if self.serverchan_key:
            try:
                url = f"https://sctapi.ftqq.com/{self.serverchan_key}.send"
                data = {
                    'title': "🎉 Claude任务完成",
                    'desp': f"{message}\n\n检测时间: {datetime.now().strftime('%H:%M:%S')}"
                }
                requests.post(url, data=data, timeout=5)
                print(f"💬 微信通知已发送")
            except Exception as e:
                print(f"微信通知失败: {e}")

    def run(self):
        """开始监控"""
        import sys
        if sys.platform == 'win32':
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

        print("🤖 简化版Claude通知器启动")
        print("🔍 正在监控剪贴板...")
        print("⚠️  按 Ctrl+C 停止")

        try:
            while True:
                current_clipboard = self.get_clipboard()

                if (current_clipboard != self.last_clipboard and
                    current_clipboard and
                    len(current_clipboard) > 10):  # 内容有意义

                    if self.check_completion(current_clipboard):
                        self.send_notification(current_clipboard)

                    self.last_clipboard = current_clipboard

                time.sleep(2)  # 每2秒检查一次

        except KeyboardInterrupt:
            print("\n👋 监控停止")

if __name__ == "__main__":
    notifier = SimpleClaudeNotifier()
    notifier.run()