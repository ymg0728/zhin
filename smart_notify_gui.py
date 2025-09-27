#!/usr/bin/env python3
"""
智能Claude通知器 - 图形界面版本
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import re
import os
import subprocess
import requests
from datetime import datetime
from dotenv import load_dotenv
from plyer import notification


class SmartNotifyGUI:
    """智能Claude通知器图形界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("🤖 智能Claude通知器")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # 加载配置
        load_dotenv()
        self.serverchan_key = os.getenv('SERVERCHAN_KEY')

        # 监控状态
        self.monitoring = False
        self.last_clipboard = ""
        self.last_notification_time = 0
        self.notification_count = 0

        # 完成标识符
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

        self.setup_ui()
        self.log_message("🤖 智能Claude通知器已初始化")
        self.update_status()

    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # 标题
        title_label = ttk.Label(main_frame, text="🤖 智能Claude通知器",
                               font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # 状态面板
        status_frame = ttk.LabelFrame(main_frame, text="监控状态", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)

        ttk.Label(status_frame, text="运行状态:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.status_var = tk.StringVar(value="⏸️ 未启动")
        ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 10, "bold")).grid(row=0, column=1, sticky=tk.W)

        ttk.Label(status_frame, text="通知计数:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.count_var = tk.StringVar(value="0")
        ttk.Label(status_frame, textvariable=self.count_var).grid(row=1, column=1, sticky=tk.W)

        ttk.Label(status_frame, text="微信通知:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        wechat_status = "✅ 已配置" if self.serverchan_key else "❌ 未配置"
        ttk.Label(status_frame, text=wechat_status).grid(row=2, column=1, sticky=tk.W)

        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(0, 10))

        self.start_button = ttk.Button(button_frame, text="🚀 开始监控", command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_button = ttk.Button(button_frame, text="⏹️ 停止监控", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(button_frame, text="🧪 测试通知", command=self.test_notification).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(button_frame, text="🗑️ 清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=(0, 10))

        # 监控配置
        config_frame = ttk.LabelFrame(main_frame, text="监控配置", padding="10")
        config_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)

        ttk.Label(config_frame, text="监控间隔(秒):").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.interval_var = tk.StringVar(value="1")
        interval_entry = ttk.Entry(config_frame, textvariable=self.interval_var, width=10)
        interval_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))

        self.desktop_notify_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="桌面通知", variable=self.desktop_notify_var).grid(row=0, column=2, sticky=tk.W, padx=(0, 10))

        self.wechat_notify_var = tk.BooleanVar(value=bool(self.serverchan_key))
        ttk.Checkbutton(config_frame, text="微信通知", variable=self.wechat_notify_var).grid(row=0, column=3, sticky=tk.W)

        # 检测关键词配置
        keywords_frame = ttk.LabelFrame(main_frame, text="检测关键词", padding="10")
        keywords_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        keywords_frame.columnconfigure(0, weight=1)

        self.keywords_text = scrolledtext.ScrolledText(keywords_frame, height=4, width=80)
        self.keywords_text.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # 填入默认关键词
        default_keywords = "✅\n完成\n任务完成\n代码完成\nSuccessfully\nDone\nCompleted\nFinished"
        self.keywords_text.insert("1.0", default_keywords)

        # 运行日志
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def update_status(self):
        """更新状态显示"""
        if self.monitoring:
            self.status_var.set("🔍 监控中...")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.status_var.set("⏸️ 已停止")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

        self.count_var.set(str(self.notification_count))

    def get_custom_patterns(self):
        """获取自定义关键词"""
        keywords = self.keywords_text.get("1.0", tk.END).strip()
        if keywords:
            return [k.strip() for k in keywords.split('\n') if k.strip()]
        return self.patterns

    def get_clipboard(self):
        """获取剪贴板内容"""
        try:
            cmd = 'powershell -Command "Get-Clipboard"'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=1)
            return result.stdout.strip()
        except:
            return ""

    def check_completion(self, text):
        """检查是否包含完成标志"""
        if not text or len(text) < 5:
            return False

        patterns = self.get_custom_patterns()
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def send_notification(self, title, message, source=""):
        """发送通知"""
        current_time = time.time()
        if current_time - self.last_notification_time < 15:  # 15秒防重复
            return

        self.last_notification_time = current_time
        self.notification_count += 1

        self.log_message(f"🎉 检测到完成信号！")
        self.log_message(f"📍 来源: {source}")
        self.log_message(f"📝 内容: {message[:100]}...")

        # 桌面通知
        if self.desktop_notify_var.get():
            try:
                notification.notify(
                    title=title,
                    message=message[:100] + "..." if len(message) > 100 else message,
                    timeout=15
                )
                self.log_message("🖥️ 桌面通知已发送")
            except Exception as e:
                self.log_message(f"❌ 桌面通知失败: {e}")

        # 微信通知
        if self.wechat_notify_var.get() and self.serverchan_key:
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
                    self.log_message("💬 微信通知已发送")
                else:
                    self.log_message(f"⚠️ 微信通知失败: HTTP {response.status_code}")
            except Exception as e:
                self.log_message(f"❌ 微信通知失败: {e}")

        # 更新计数显示
        self.root.after(0, self.update_status)

    def monitor_loop(self):
        """监控主循环"""
        self.log_message("🔍 开始监控剪贴板...")

        while self.monitoring:
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

                # 获取监控间隔
                try:
                    interval = float(self.interval_var.get())
                except:
                    interval = 1.0

                time.sleep(interval)

            except Exception as e:
                self.log_message(f"❌ 监控错误: {e}")
                time.sleep(3)

        self.log_message("⏹️ 监控已停止")

    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            return

        self.monitoring = True
        self.update_status()

        # 在新线程中启动监控
        monitor_thread = threading.Thread(target=self.monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()

        self.log_message("🚀 监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        self.update_status()
        self.log_message("⏹️ 停止监控")

    def test_notification(self):
        """测试通知功能"""
        self.log_message("🧪 发送测试通知...")
        self.send_notification(
            "🧪 测试通知",
            "这是一条测试通知，确认通知系统正常工作！✅ 完成",
            "测试功能"
        )

    def clear_log(self):
        """清空日志"""
        self.log_text.delete("1.0", tk.END)
        self.log_message("🗑️ 日志已清空")


def main():
    """主函数"""
    root = tk.Tk()
    app = SmartNotifyGUI(root)

    # 设置窗口关闭事件
    def on_closing():
        if app.monitoring:
            if messagebox.askokcancel("退出", "监控正在运行中，确定要退出吗？"):
                app.stop_monitoring()
                time.sleep(0.5)
                root.destroy()
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("程序被用户中断")


if __name__ == "__main__":
    main()