#!/usr/bin/env python3
"""
被动监控器 - 无需复制的Claude监控
通过进程、窗口标题、文件变化等方式检测
"""
import time
import os
import psutil
import requests
from datetime import datetime
from dotenv import load_dotenv
from plyer import notification
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class PassiveClaudeMonitor:
    """被动Claude监控器 - 无需用户复制"""

    def __init__(self):
        load_dotenv()
        import sys
        if sys.platform == 'win32':
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

        self.serverchan_key = os.getenv('SERVERCHAN_KEY')
        self.last_notification_time = 0
        self.running = True
        self.claude_processes = set()

        print("🎯 被动Claude监控器 - 无需复制")
        print("🔍 监控方式：进程活动 + 文件变化 + 窗口标题")

    def send_notification(self, title, message, source=""):
        """发送通知"""
        current_time = time.time()
        if current_time - self.last_notification_time < 30:  # 30秒防重复
            return

        self.last_notification_time = current_time

        print(f"🎉 检测到Claude活动！")
        print(f"📍 来源: {source}")
        print(f"⏰ 时间: {datetime.now().strftime('%H:%M:%S')}")

        # 桌面通知
        try:
            notification.notify(
                title=title,
                message=message,
                timeout=15,
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
📝 **活动描述**: {message}

🤖 *被动监控系统 - 无需复制*
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

    def monitor_processes(self):
        """监控Claude相关进程"""
        print("🔍 启动进程监控...")

        while self.running:
            try:
                current_processes = set()

                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                    try:
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''

                        # 检测Claude相关进程
                        if any(keyword in cmdline.lower() for keyword in ['claude', 'anthropic']):
                            pid = proc.info['pid']
                            current_processes.add(pid)

                            # 新进程检测
                            if pid not in self.claude_processes:
                                self.claude_processes.add(pid)
                                self.send_notification(
                                    "🤖 Claude进程启动",
                                    f"检测到新的Claude进程 (PID: {pid})",
                                    "进程监控"
                                )

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                # 检测进程结束
                ended_processes = self.claude_processes - current_processes
                for pid in ended_processes:
                    self.claude_processes.remove(pid)
                    self.send_notification(
                        "✅ Claude进程完成",
                        f"Claude进程已结束 (PID: {pid})，可能任务已完成",
                        "进程监控"
                    )

                time.sleep(5)  # 每5秒检查一次

            except Exception as e:
                print(f"进程监控错误: {e}")
                time.sleep(10)

    def monitor_file_changes(self):
        """监控文件系统变化"""
        print("📁 启动文件变化监控...")

        class FileChangeHandler(FileSystemEventHandler):
            def __init__(self, monitor):
                self.monitor = monitor

            def on_created(self, event):
                if not event.is_directory:
                    file_path = event.src_path
                    # 检测代码文件创建
                    if any(ext in file_path.lower() for ext in ['.py', '.js', '.html', '.css', '.md', '.txt']):
                        self.monitor.send_notification(
                            "📄 新文件创建",
                            f"检测到新文件: {os.path.basename(file_path)}",
                            "文件监控"
                        )

            def on_modified(self, event):
                if not event.is_directory:
                    file_path = event.src_path
                    # 检测重要文件修改
                    if any(ext in file_path.lower() for ext in ['.py', '.js']):
                        # 避免频繁通知，只通知大文件修改
                        try:
                            size = os.path.getsize(file_path)
                            if size > 1000:  # 大于1KB的文件修改
                                self.monitor.send_notification(
                                    "✏️ 文件更新",
                                    f"文件已更新: {os.path.basename(file_path)}",
                                    "文件监控"
                                )
                        except:
                            pass

        try:
            # 监控当前目录
            event_handler = FileChangeHandler(self)
            observer = Observer()
            observer.schedule(event_handler, ".", recursive=True)
            observer.start()

            while self.running:
                time.sleep(1)

            observer.stop()
            observer.join()

        except Exception as e:
            print(f"文件监控错误: {e}")

    def monitor_system_activity(self):
        """监控系统活动指标"""
        print("📊 启动系统活动监控...")

        last_cpu_usage = 0

        while self.running:
            try:
                # 检测CPU使用率变化（可能表示处理任务）
                cpu_usage = psutil.cpu_percent(interval=1)

                # 如果CPU使用率从高突然降低，可能任务完成
                if last_cpu_usage > 50 and cpu_usage < 20:
                    self.send_notification(
                        "💻 系统活动变化",
                        f"CPU使用率从 {last_cpu_usage:.1f}% 降至 {cpu_usage:.1f}%，可能任务已完成",
                        "系统监控"
                    )

                last_cpu_usage = cpu_usage
                time.sleep(10)  # 每10秒检查

            except Exception as e:
                print(f"系统监控错误: {e}")
                time.sleep(15)

    def start_manual_trigger(self):
        """手动触发接口"""
        print("⌨️ 启动手动触发监听...")
        print("💡 在任何时候按回车键表示'任务完成'")

        while self.running:
            try:
                input("按回车键表示任务完成...")
                self.send_notification(
                    "✅ 手动确认完成",
                    "用户手动确认任务已完成",
                    "手动触发"
                )
            except KeyboardInterrupt:
                break

    def run(self):
        """启动被动监控"""
        try:
            print("🚀 启动被动监控系统...")

            # 发送启动通知
            self.send_notification(
                "🤖 被动监控器启动",
                "Claude被动监控系统已启动，无需复制任何内容",
                "系统启动"
            )

            import threading

            # 启动进程监控
            process_thread = threading.Thread(target=self.monitor_processes)
            process_thread.daemon = True
            process_thread.start()

            # 启动文件监控
            file_thread = threading.Thread(target=self.monitor_file_changes)
            file_thread.daemon = True
            file_thread.start()

            # 启动系统监控
            system_thread = threading.Thread(target=self.monitor_system_activity)
            system_thread.daemon = True
            system_thread.start()

            print("✅ 所有监控已启动")
            print("📝 监控内容：")
            print("   - 🔍 Claude进程启动/结束")
            print("   - 📁 代码文件创建/修改")
            print("   - 💻 系统活动变化")
            print("   - ⌨️ 手动触发（按回车）")
            print()
            print("⚠️  按 Ctrl+C 停止监控")

            # 手动触发界面
            self.start_manual_trigger()

        except KeyboardInterrupt:
            print("\n⏹️ 停止监控...")
            self.running = False


def main():
    try:
        monitor = PassiveClaudeMonitor()
        monitor.run()
    except Exception as e:
        print(f"❌ 启动失败: {e}")


if __name__ == "__main__":
    main()