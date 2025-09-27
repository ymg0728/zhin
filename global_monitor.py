#!/usr/bin/env python3
"""
全局Claude监控器
监控所有窗口的Claude活动，无需手动复制
"""
import os
import sys
import time
import subprocess
import psutil
import requests
import win32gui
import win32process
import win32api
import win32con
from datetime import datetime
from dotenv import load_dotenv
from plyer import notification
import threading


class GlobalClaudeMonitor:
    """全局Claude监控器"""

    def __init__(self):
        # 设置编码
        if sys.platform == 'win32':
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

        load_dotenv()
        self.serverchan_key = os.getenv('SERVERCHAN_KEY')
        self.running = True
        self.last_notification_time = 0
        self.monitored_windows = set()
        self.claude_processes = {}

        print("🌍 全局Claude监控器启动")
        print("🔍 监控所有窗口的Claude活动")
        print("📊 无需手动复制，自动检测完成状态")

    def find_all_windows(self):
        """查找所有可能的Claude窗口"""
        windows = []

        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and len(title) > 3:
                    # 检查可能包含Claude活动的窗口
                    claude_keywords = [
                        'claude', 'anthropic', 'ai', 'code', 'terminal',
                        'cmd', 'powershell', 'vscode', 'cursor', 'ide',
                        'browser', 'chrome', 'firefox', 'edge'
                    ]

                    if any(keyword in title.lower() for keyword in claude_keywords):
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            windows.append({
                                'hwnd': hwnd,
                                'title': title,
                                'pid': pid
                            })
                        except:
                            pass

        win32gui.EnumWindows(enum_callback, None)
        return windows

    def check_process_activity(self):
        """检查进程活动状态"""
        active_changes = []

        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name'].lower()
                    cpu_usage = proc.cpu_percent()

                    # 检查可能的Claude相关进程
                    if any(keyword in name for keyword in ['python', 'node', 'chrome', 'cursor', 'code']):

                        if pid not in self.claude_processes:
                            self.claude_processes[pid] = {
                                'name': name,
                                'last_cpu': 0,
                                'active_time': 0,
                                'last_check': time.time()
                            }

                        proc_info = self.claude_processes[pid]
                        current_time = time.time()

                        # 检测CPU使用率变化
                        if proc_info['last_cpu'] > 5 and cpu_usage < 1:
                            # 从活跃状态变为空闲状态
                            idle_duration = current_time - proc_info['last_check']
                            if idle_duration > 3:  # 空闲超过3秒
                                active_changes.append({
                                    'type': 'process_completed',
                                    'pid': pid,
                                    'name': name,
                                    'duration': idle_duration
                                })

                        proc_info['last_cpu'] = cpu_usage
                        proc_info['last_check'] = current_time

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            print(f"进程监控错误: {e}")

        return active_changes

    def check_window_changes(self):
        """检查窗口标题变化"""
        changes = []
        current_windows = self.find_all_windows()

        for window in current_windows:
            window_id = f"{window['hwnd']}_{window['pid']}"
            title = window['title']

            if window_id not in self.monitored_windows:
                self.monitored_windows.add(window_id)

                # 检查窗口标题是否包含完成标志
                completion_indicators = [
                    '完成', 'done', 'finished', 'completed', 'success',
                    '✅', '成功', 'ok', 'ready', '就绪'
                ]

                if any(indicator in title.lower() for indicator in completion_indicators):
                    changes.append({
                        'type': 'window_completion',
                        'title': title,
                        'pid': window['pid']
                    })

        return changes

    def monitor_file_system(self):
        """监控文件系统变化"""
        # 简单的文件创建检测
        recent_files = []
        try:
            # 检查当前目录下的新文件
            for root, dirs, files in os.walk('.'):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        # 检查最近1分钟内创建的文件
                        if time.time() - os.path.getctime(file_path) < 60:
                            if any(ext in file.lower() for ext in ['.py', '.js', '.html', '.css', '.md']):
                                recent_files.append(file_path)
                    except:
                        continue
                break  # 只检查当前目录
        except:
            pass

        return recent_files

    def send_notification(self, title, message, source=""):
        """发送通知"""
        current_time = time.time()
        if current_time - self.last_notification_time < 15:  # 15秒防重复
            return

        self.last_notification_time = current_time

        print(f"🎉 检测到活动变化！")
        print(f"📍 来源: {source}")
        print(f"📝 信息: {message}")
        print(f"⏰ 时间: {datetime.now().strftime('%H:%M:%S')}")

        # 桌面通知
        try:
            notification.notify(
                title=title,
                message=message,
                timeout=15,
                app_name="全局Claude监控"
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

📍 **检测来源**: {source}
⏰ **检测时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📝 **活动信息**:
{message}

🌍 *全局Claude监控系统*
                """

                data = {
                    'title': title,
                    'desp': content
                }
                response = requests.post(url, data=data, timeout=5)
                if response.status_code == 200:
                    print(f"💬 微信通知已发送")
            except Exception as e:
                print(f"❌ 微信通知失败: {e}")

    def monitor_loop(self):
        """主监控循环"""
        print("🔍 开始全局监控...")

        while self.running:
            try:
                # 1. 检查进程活动
                process_changes = self.check_process_activity()
                for change in process_changes:
                    self.send_notification(
                        "🔄 进程活动完成",
                        f"进程 {change['name']} (PID: {change['pid']}) 可能完成了任务",
                        "进程监控"
                    )

                # 2. 检查窗口变化
                window_changes = self.check_window_changes()
                for change in window_changes:
                    self.send_notification(
                        "🪟 窗口状态变化",
                        f"窗口标题显示完成状态: {change['title']}",
                        "窗口监控"
                    )

                # 3. 检查文件变化
                new_files = self.monitor_file_system()
                if new_files:
                    file_list = '\n'.join(new_files[:5])  # 最多显示5个文件
                    self.send_notification(
                        "📁 新文件创建",
                        f"检测到新创建的文件:\n{file_list}",
                        "文件系统监控"
                    )

                time.sleep(5)  # 每5秒检查一次

            except Exception as e:
                print(f"监控错误: {e}")
                time.sleep(10)

    def run(self):
        """启动全局监控"""
        try:
            # 发送启动通知
            self.send_notification(
                "🌍 全局Claude监控启动",
                "全局监控系统已启动，将自动检测所有窗口的Claude活动",
                "系统启动"
            )

            print("📋 监控范围:")
            print("   - 🔄 所有进程的CPU活动变化")
            print("   - 🪟 所有窗口标题变化")
            print("   - 📁 文件系统新建文件")
            print("   - 🎯 无需手动复制任何内容")
            print("⚠️  按 Ctrl+C 停止监控")

            # 启动监控
            self.monitor_loop()

        except KeyboardInterrupt:
            print("\n⏹️ 停止全局监控")
            self.running = False


def main():
    try:
        monitor = GlobalClaudeMonitor()
        monitor.run()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("💡 请确保安装了 pywin32: pip install pywin32")


if __name__ == "__main__":
    main()