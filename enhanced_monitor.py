#!/usr/bin/env python3
"""
增强版Claude监控器
专门监控Claude Code窗口活动
"""
import time
import re
import os
import subprocess
import psutil
import requests
from datetime import datetime
from dotenv import load_dotenv
from plyer import notification
import win32gui
import win32process
import win32api


class EnhancedClaudeMonitor:
    """增强版Claude监控器"""

    def __init__(self):
        load_dotenv()
        import sys
        if sys.platform == 'win32':
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

        self.serverchan_key = os.getenv('SERVERCHAN_KEY')
        self.last_clipboard = ""
        self.last_notification_time = 0
        self.claude_windows = []
        self.running = True

        # 更全面的检测词
        self.patterns = [
            r"✅",
            r"完成",
            r"任务.*完成",
            r"代码.*完成",
            r"Successfully",
            r"Done",
            r"Completed",
            r"Finished",
            r"创建.*成功",
            r"已.*创建",
            r"文件.*创建",
            r"Generated",
            r"Created",
            r"Added",
            r"Updated",
            r"Fixed",
            r"Implemented",
            r"I.*created",
            r"I.*added",
            r"I.*updated",
            r"Here.*is.*the",
            r"项目.*完成",
            r"功能.*完成",
            r"开发.*完成"
        ]

        print("🔥 增强版Claude监控器启动")
        print("🎯 专门监控Claude Code活动")

    def find_claude_windows(self):
        """查找Claude相关窗口"""
        claude_windows = []

        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if any(keyword in window_title.lower() for keyword in ['claude', 'anthropic', 'ai']):
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(pid)
                        windows.append({
                            'hwnd': hwnd,
                            'title': window_title,
                            'pid': pid,
                            'process_name': process.name()
                        })
                    except:
                        pass

        win32gui.EnumWindows(enum_windows_callback, claude_windows)
        return claude_windows

    def get_clipboard(self):
        """获取剪贴板内容"""
        try:
            cmd = 'powershell -Command "Get-Clipboard"'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=1)
            content = result.stdout.strip()
            return content
        except:
            return ""

    def get_console_output(self):
        """获取控制台输出"""
        try:
            # 获取当前活动窗口的标题
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)

            # 如果是命令行窗口，尝试获取其内容
            if any(keyword in window_title.lower() for keyword in ['cmd', 'powershell', 'claude', 'terminal']):
                return window_title
        except:
            pass
        return ""

    def check_completion(self, text):
        """检查是否包含完成标志"""
        if not text or len(text) < 3:
            return False

        # 清理文本
        text = text.strip()

        # 检查每个模式
        for pattern in self.patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def send_notification(self, title, message, source=""):
        """发送通知"""
        current_time = time.time()
        if current_time - self.last_notification_time < 10:  # 10秒防重复
            return

        self.last_notification_time = current_time

        print(f"🎉 检测到Claude完成信号！")
        print(f"📍 来源: {source}")
        print(f"📝 内容: {message[:150]}...")

        # 桌面通知
        try:
            notification.notify(
                title=title,
                message=message[:200] + "..." if len(message) > 200 else message,
                timeout=20,
                app_name="Claude监控器"
            )
            print(f"🖥️ 桌面通知已发送")
        except Exception as e:
            print(f"❌ 桌面通知失败: {e}")

        # 微信通知
        if self.serverchan_key:
            try:
                url = f"https://sctapi.ftqq.com/{self.serverchan_key}.send"
                content = f"""
**🎉 Claude活动检测**

📍 **检测来源**: {source}
⏰ **检测时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📝 **活动内容**:
```
{message[:500]}
```

🤖 *自动监控系统*
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

    def monitor_clipboard_enhanced(self):
        """增强剪贴板监控"""
        print("🔍 启动增强剪贴板监控...")

        while self.running:
            try:
                current_clipboard = self.get_clipboard()

                if (current_clipboard != self.last_clipboard and
                    current_clipboard and
                    len(current_clipboard) > 10):

                    print(f"📋 检测到剪贴板更新: {current_clipboard[:50]}...")

                    if self.check_completion(current_clipboard):
                        self.send_notification(
                            "🎉 Claude任务完成",
                            current_clipboard,
                            "剪贴板监控"
                        )

                    self.last_clipboard = current_clipboard

                time.sleep(0.5)  # 更频繁检查

            except Exception as e:
                print(f"剪贴板监控错误: {e}")
                time.sleep(2)

    def monitor_windows(self):
        """监控Claude窗口"""
        print("🪟 启动窗口监控...")

        while self.running:
            try:
                # 查找Claude窗口
                claude_windows = self.find_claude_windows()

                for window in claude_windows:
                    if window not in self.claude_windows:
                        print(f"🆕 发现新Claude窗口: {window['title']} (PID: {window['pid']})")
                        self.claude_windows.append(window)

                # 检查活动窗口
                try:
                    hwnd = win32gui.GetForegroundWindow()
                    window_title = win32gui.GetWindowText(hwnd)

                    if window_title and any(keyword in window_title.lower() for keyword in ['claude', 'ai']):
                        console_output = self.get_console_output()
                        if console_output and self.check_completion(console_output):
                            self.send_notification(
                                "🎉 Claude窗口活动",
                                console_output,
                                "窗口监控"
                            )
                except:
                    pass

                time.sleep(2)

            except Exception as e:
                print(f"窗口监控错误: {e}")
                time.sleep(3)

    def test_detection(self):
        """测试检测功能"""
        test_texts = [
            "✅ 任务完成！",
            "代码已生成完成",
            "Successfully created the file",
            "Done! The implementation is complete",
            "文件创建成功",
            "项目开发完成"
        ]

        print("🧪 测试检测功能...")
        for text in test_texts:
            if self.check_completion(text):
                print(f"✅ 检测成功: {text}")
            else:
                print(f"❌ 检测失败: {text}")

    def run(self):
        """运行监控器"""
        try:
            print("🚀 启动多重监控...")

            # 测试检测功能
            self.test_detection()
            print()

            # 发送启动通知
            self.send_notification(
                "🤖 增强监控器启动",
                "Claude监控系统已启动，正在监控剪贴板和窗口活动",
                "系统启动"
            )

            import threading

            # 启动剪贴板监控线程
            clipboard_thread = threading.Thread(target=self.monitor_clipboard_enhanced)
            clipboard_thread.daemon = True
            clipboard_thread.start()

            # 启动窗口监控线程
            window_thread = threading.Thread(target=self.monitor_windows)
            window_thread.daemon = True
            window_thread.start()

            print("✅ 所有监控线程已启动")
            print("💡 提示: 复制Claude的任何输出都会被检测")
            print("⚠️  按 Ctrl+C 停止监控")

            # 主循环
            while self.running:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n⏹️ 停止监控...")
            self.running = False


def main():
    try:
        monitor = EnhancedClaudeMonitor()
        monitor.run()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("💡 请确保安装了 pywin32: pip install pywin32")


if __name__ == "__main__":
    main()