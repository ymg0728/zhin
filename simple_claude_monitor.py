#!/usr/bin/env python3
"""
简单Claude监控器
监控Claude进程活动状态，停止输出时自动通知
"""
import time
import os
import psutil
import requests
from datetime import datetime
from dotenv import load_dotenv
from plyer import notification


class SimpleClaudeMonitor:
    """简单Claude监控器"""

    def __init__(self):
        load_dotenv()
        import sys
        if sys.platform == 'win32':
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

        self.serverchan_key = os.getenv('SERVERCHAN_KEY')
        self.running = True
        self.claude_processes = {}  # pid: {last_activity, cpu_usage}
        self.last_notification_time = 0

        print("🎯 简单Claude监控器")
        print("📊 监控Claude进程活动状态")
        print("⏹️ Claude停止输出时自动通知")

    def find_claude_processes(self):
        """查找Claude相关进程"""
        claude_procs = []

        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                name = proc.info['name'].lower()

                # 检测Claude相关进程
                if (any(keyword in cmdline.lower() for keyword in ['claude', 'anthropic']) or
                    any(keyword in name for keyword in ['claude', 'anthropic', 'python']) and
                    any(claude_keyword in cmdline.lower() for claude_keyword in ['claude', 'ai'])):

                    claude_procs.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu_percent': proc.cpu_percent(),
                        'cmdline': cmdline
                    })

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return claude_procs

    def send_notification(self, title, message):
        """发送通知"""
        current_time = time.time()
        if current_time - self.last_notification_time < 20:  # 20秒防重复
            return

        self.last_notification_time = current_time

        print(f"🎉 {title}")
        print(f"📝 {message}")
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")

        # 桌面通知
        try:
            notification.notify(
                title=title,
                message=message,
                timeout=15,
                app_name="Claude监控"
            )
            print("🖥️ 桌面通知已发送")
        except Exception as e:
            print(f"❌ 桌面通知失败: {e}")

        # 微信通知
        if self.serverchan_key:
            try:
                url = f"https://sctapi.ftqq.com/{self.serverchan_key}.send"
                data = {
                    'title': title,
                    'desp': f"{message}\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
                response = requests.post(url, data=data, timeout=5)
                if response.status_code == 200:
                    print("💬 微信通知已发送")
            except Exception as e:
                print(f"❌ 微信通知失败: {e}")

    def monitor_claude_activity(self):
        """监控Claude活动状态"""
        print("🔍 开始监控Claude活动...")

        idle_threshold = 3  # 连续3次检查CPU使用率低于1%认为空闲
        check_interval = 2  # 每2秒检查一次

        while self.running:
            try:
                current_procs = self.find_claude_processes()
                current_time = time.time()

                # 更新进程状态
                for proc in current_procs:
                    pid = proc['pid']
                    cpu_usage = proc['cpu_percent']

                    if pid not in self.claude_processes:
                        # 新发现的Claude进程
                        self.claude_processes[pid] = {
                            'name': proc['name'],
                            'cmdline': proc['cmdline'],
                            'last_activity': current_time,
                            'idle_count': 0,
                            'was_active': False
                        }
                        print(f"🆕 发现Claude进程: {proc['name']} (PID: {pid})")

                    else:
                        # 检查进程活动状态
                        proc_info = self.claude_processes[pid]

                        if cpu_usage > 1.0:  # CPU使用率大于1%认为活跃
                            proc_info['last_activity'] = current_time
                            proc_info['idle_count'] = 0
                            proc_info['was_active'] = True

                        else:  # CPU使用率低，可能空闲
                            proc_info['idle_count'] += 1

                            # 如果之前活跃过，现在连续空闲，可能任务完成
                            if (proc_info['was_active'] and
                                proc_info['idle_count'] >= idle_threshold):

                                idle_time = current_time - proc_info['last_activity']

                                if idle_time > 5:  # 空闲超过5秒
                                    self.send_notification(
                                        "✅ Claude任务完成",
                                        f"Claude进程 {proc['name']} (PID: {pid}) 已停止活动，任务可能完成"
                                    )

                                    # 重置状态，避免重复通知
                                    proc_info['was_active'] = False
                                    proc_info['idle_count'] = 0

                # 清理已结束的进程
                existing_pids = {proc['pid'] for proc in current_procs}
                ended_pids = set(self.claude_processes.keys()) - existing_pids

                for pid in ended_pids:
                    proc_info = self.claude_processes[pid]
                    print(f"🏁 Claude进程结束: {proc_info['name']} (PID: {pid})")

                    if proc_info['was_active']:
                        self.send_notification(
                            "🎯 Claude进程结束",
                            f"Claude进程 {proc_info['name']} 已结束，任务完成"
                        )

                    del self.claude_processes[pid]

                # 显示当前状态
                if current_procs:
                    status_info = []
                    for proc in current_procs:
                        pid = proc['pid']
                        cpu = proc['cpu_percent']
                        status = "🟢 活跃" if cpu > 1.0 else "🟡 空闲"
                        status_info.append(f"PID {pid}: {status} (CPU: {cpu:.1f}%)")

                    print(f"📊 [{datetime.now().strftime('%H:%M:%S')}] {' | '.join(status_info)}")
                else:
                    print(f"⚪ [{datetime.now().strftime('%H:%M:%S')}] 未发现Claude进程")

                time.sleep(check_interval)

            except Exception as e:
                print(f"❌ 监控错误: {e}")
                time.sleep(5)

    def run(self):
        """启动监控"""
        try:
            print("🚀 启动Claude活动监控...")

            # 发送启动通知
            self.send_notification(
                "🤖 Claude监控启动",
                "开始监控Claude进程活动状态"
            )

            print("📋 监控规则:")
            print("   - 🟢 CPU > 1% = Claude正在工作")
            print("   - 🟡 CPU < 1% 且持续5秒 = Claude停止工作")
            print("   - 🏁 进程结束 = 任务完成")
            print()
            print("⚠️  按 Ctrl+C 停止监控")

            # 开始监控
            self.monitor_claude_activity()

        except KeyboardInterrupt:
            print("\n⏹️ 停止监控")
            self.running = False


def main():
    try:
        monitor = SimpleClaudeMonitor()
        monitor.run()
    except Exception as e:
        print(f"❌ 启动失败: {e}")


if __name__ == "__main__":
    main()