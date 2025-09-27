#!/usr/bin/env python3
"""
Claude自动监控器
自动监控CMD窗口中的Claude活动并发送通知
"""
import os
import time
import re
import threading
import psutil
import subprocess
from datetime import datetime
from typing import List, Dict, Set
from dotenv import load_dotenv
from plyer import notification
import requests


class ClaudeAutoMonitor:
    """Claude自动监控器"""

    def __init__(self):
        load_dotenv()

        # 通知配置
        self.serverchan_key = os.getenv('SERVERCHAN_KEY')
        self.enable_desktop = os.getenv('ENABLE_DESKTOP_NOTIFICATION', 'true').lower() == 'true'
        self.enable_wechat = os.getenv('ENABLE_WECHAT_NOTIFICATION', 'false').lower() == 'true'

        # 监控配置
        self.check_interval = 5  # 检查间隔(秒)
        self.monitored_processes: Set[int] = set()
        self.last_notifications: Dict[str, float] = {}

        # Claude完成标识符
        self.completion_patterns = [
            r"✅.*完成",
            r"完成.*代码",
            r"任务.*完成",
            r"Successfully.*",
            r"Done\.",
            r"完成！",
            r"✅",
            r"代码已.*完成",
            r"Implementation.*complete",
            r"Task.*completed"
        ]

        # 运行状态
        self.is_running = False
        self.monitor_thread = None

        print("🤖 Claude自动监控器初始化完成")
        print(f"✅ 桌面通知: {'启用' if self.enable_desktop else '禁用'}")
        print(f"💬 微信通知: {'启用' if self.enable_wechat else '禁用'}")

    def find_claude_processes(self) -> List[Dict]:
        """查找Claude相关进程"""
        claude_processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''

                # 检查是否为Claude相关进程
                if any(keyword in cmdline.lower() for keyword in ['claude', 'anthropic']):
                    claude_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': cmdline
                    })

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return claude_processes

    def find_cmd_windows(self) -> List[Dict]:
        """查找CMD窗口进程"""
        cmd_processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'].lower() in ['cmd.exe', 'powershell.exe', 'python.exe', 'node.exe']:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''

                    cmd_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': cmdline,
                        'create_time': proc.create_time()
                    })

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return cmd_processes

    def check_completion_in_output(self, text: str) -> bool:
        """检查文本中是否包含完成标识"""
        for pattern in self.completion_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def get_recent_console_output(self) -> str:
        """获取最近的控制台输出"""
        try:
            # 使用PowerShell获取最近的控制台历史
            cmd = 'powershell -Command "Get-History | Select-Object -Last 10 | Out-String"'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=5)
            return result.stdout
        except:
            return ""

    def monitor_clipboard(self) -> str:
        """监控剪贴板内容变化"""
        try:
            # 使用PowerShell获取剪贴板内容
            cmd = 'powershell -Command "Get-Clipboard"'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=2)
            return result.stdout
        except:
            return ""

    def send_notification(self, title: str, message: str, details: str = "") -> None:
        """发送通知"""
        current_time = time.time()

        # 防止重复通知(60秒内不重复发送相同标题的通知)
        if title in self.last_notifications:
            if current_time - self.last_notifications[title] < 60:
                return

        self.last_notifications[title] = current_time

        # 桌面通知
        if self.enable_desktop:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    timeout=10
                )
                print(f"🖥️ 桌面通知已发送: {title}")
            except Exception as e:
                print(f"⚠️ 桌面通知失败: {e}")

        # 微信通知
        if self.enable_wechat and self.serverchan_key:
            try:
                self.send_wechat_notification(title, message, details)
                print(f"💬 微信通知已发送: {title}")
            except Exception as e:
                print(f"⚠️ 微信通知失败: {e}")

    def send_wechat_notification(self, title: str, message: str, details: str = "") -> None:
        """发送微信通知"""
        url = f"https://sctapi.ftqq.com/{self.serverchan_key}.send"

        content = f"""
{message}

📋 **监控详情**
- ⏰ 检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 🖥️ 来源: 自动监控系统

💻 **活动详情**
```
{details[:500] if details else '无详细信息'}
```
        """

        data = {
            'title': title,
            'desp': content
        }

        response = requests.post(url, data=data, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Server酱请求失败: {response.status_code}")

    def monitor_loop(self):
        """监控主循环"""
        print("🔍 开始监控Claude活动...")

        last_clipboard = ""
        last_console_output = ""

        while self.is_running:
            try:
                # 1. 监控剪贴板变化
                current_clipboard = self.monitor_clipboard()
                if current_clipboard != last_clipboard and current_clipboard.strip():
                    if self.check_completion_in_output(current_clipboard):
                        self.send_notification(
                            "🎉 Claude任务完成",
                            "检测到Claude完成了一个任务",
                            current_clipboard
                        )
                    last_clipboard = current_clipboard

                # 2. 监控控制台输出
                current_console = self.get_recent_console_output()
                if current_console != last_console_output and current_console.strip():
                    if self.check_completion_in_output(current_console):
                        self.send_notification(
                            "🎉 Claude任务完成",
                            "检测到Claude在控制台完成了任务",
                            current_console
                        )
                    last_console_output = current_console

                # 3. 检查Claude进程状态
                claude_processes = self.find_claude_processes()
                for proc in claude_processes:
                    if proc['pid'] not in self.monitored_processes:
                        self.monitored_processes.add(proc['pid'])
                        print(f"📍 发现新的Claude进程: PID {proc['pid']}")

                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ 监控循环错误: {e}")
                time.sleep(self.check_interval)

    def start_monitoring(self):
        """开始监控"""
        if self.is_running:
            print("⚠️ 监控已经在运行中")
            return

        self.is_running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

        print("✅ 自动监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("⏹️ 监控已停止")

    def show_status(self):
        """显示监控状态"""
        print(f"\n📊 监控状态:")
        print(f"- 运行状态: {'🟢 运行中' if self.is_running else '🔴 已停止'}")
        print(f"- 检查间隔: {self.check_interval}秒")
        print(f"- 监控进程数: {len(self.monitored_processes)}")
        print(f"- 桌面通知: {'✅' if self.enable_desktop else '❌'}")
        print(f"- 微信通知: {'✅' if self.enable_wechat else '❌'}")

        # 显示当前Claude进程
        claude_processes = self.find_claude_processes()
        if claude_processes:
            print(f"\n🤖 检测到的Claude进程:")
            for proc in claude_processes:
                print(f"  - PID: {proc['pid']}, 名称: {proc['name']}")


def main():
    """主函数"""
    # 设置输出编码
    import sys
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

    print("🤖 Claude自动监控器")
    print("=" * 50)

    monitor = ClaudeAutoMonitor()

    print("\n可用命令:")
    print("  start  - 开始监控")
    print("  stop   - 停止监控")
    print("  status - 查看状态")
    print("  quit   - 退出程序")

    while True:
        try:
            command = input("\n请输入命令: ").strip().lower()

            if command == "start":
                monitor.start_monitoring()
            elif command == "stop":
                monitor.stop_monitoring()
            elif command == "status":
                monitor.show_status()
            elif command == "quit":
                monitor.stop_monitoring()
                print("👋 再见!")
                break
            else:
                print("❌ 未知命令")

        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("\n👋 程序被中断")
            break
        except Exception as e:
            print(f"❌ 程序错误: {e}")


if __name__ == "__main__":
    main()