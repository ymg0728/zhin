#!/usr/bin/env python3
"""
Claude AI Bot GUI - 图形化界面版本
当Claude完成代码任务时发送通知
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime
from claude_bot import ClaudeBot


class ClaudeBotGUI:
    """Claude AI Bot 图形化界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("Claude AI 代码通知机器人")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # 初始化机器人
        try:
            self.bot = ClaudeBot()
            self.status_var = tk.StringVar(value="✅ 已连接到Claude API")
        except Exception as e:
            self.bot = None
            self.status_var = tk.StringVar(value=f"❌ 连接失败: {str(e)}")

        self.setup_ui()
        self.update_task_list()

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
        title_label = ttk.Label(main_frame, text="🤖 Claude AI 代码通知机器人",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # 状态显示
        status_frame = ttk.LabelFrame(main_frame, text="连接状态", padding="5")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(0, weight=1)

        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=0, sticky=tk.W)

        # 添加任务区域
        task_frame = ttk.LabelFrame(main_frame, text="添加新任务", padding="10")
        task_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        task_frame.columnconfigure(1, weight=1)

        ttk.Label(task_frame, text="任务描述:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.task_desc_var = tk.StringVar()
        task_desc_entry = ttk.Entry(task_frame, textvariable=self.task_desc_var, width=50)
        task_desc_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))

        add_button = ttk.Button(task_frame, text="添加任务", command=self.add_task)
        add_button.grid(row=0, column=2)

        ttk.Label(task_frame, text="代码要求:").grid(row=1, column=0, sticky=(tk.W, tk.N), padx=(0, 10), pady=(10, 0))
        self.requirements_text = scrolledtext.ScrolledText(task_frame, height=3, width=50)
        self.requirements_text.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(10, 0))

        # 任务列表区域
        list_frame = ttk.LabelFrame(main_frame, text="任务列表", padding="10")
        list_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # 创建Treeview来显示任务
        columns = ('ID', '描述', '状态', '创建时间')
        self.task_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)

        # 设置列标题
        for col in columns:
            self.task_tree.heading(col, text=col)

        # 设置列宽
        self.task_tree.column('ID', width=100)
        self.task_tree.column('描述', width=300)
        self.task_tree.column('状态', width=100)
        self.task_tree.column('创建时间', width=150)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)

        self.task_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 操作按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(10, 0))

        ttk.Button(button_frame, text="处理选中任务", command=self.process_selected_task).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="查看结果", command=self.view_result).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="刷新列表", command=self.update_task_list).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="保存结果", command=self.save_results).pack(side=tk.LEFT, padx=(0, 10))

        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 绑定双击事件
        self.task_tree.bind('<Double-1>', self.on_task_double_click)

    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)

    def add_task(self):
        """添加新任务"""
        if not self.bot:
            messagebox.showerror("错误", "未连接到Claude API")
            return

        description = self.task_desc_var.get().strip()
        if not description:
            messagebox.showwarning("警告", "请输入任务描述")
            return

        requirements = self.requirements_text.get("1.0", tk.END).strip()

        try:
            task_id = self.bot.add_task(description, requirements)
            self.log_message(f"✅ 任务已添加: {description} (ID: {task_id})")

            # 清空输入框
            self.task_desc_var.set("")
            self.requirements_text.delete("1.0", tk.END)

            # 更新任务列表
            self.update_task_list()

        except Exception as e:
            self.log_message(f"❌ 添加任务失败: {str(e)}")
            messagebox.showerror("错误", f"添加任务失败: {str(e)}")

    def update_task_list(self):
        """更新任务列表"""
        if not self.bot:
            return

        # 清空现有项目
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        # 添加待处理任务
        for task in self.bot.tasks:
            self.task_tree.insert('', 'end', values=(
                task['id'],
                task['description'][:50] + '...' if len(task['description']) > 50 else task['description'],
                task['status'],
                task['created_at'][:16]
            ))

        # 添加已完成任务
        for task in self.bot.completed_tasks:
            self.task_tree.insert('', 'end', values=(
                task['id'],
                task['description'][:50] + '...' if len(task['description']) > 50 else task['description'],
                task['status'],
                task['created_at'][:16]
            ))

    def get_selected_task_id(self):
        """获取选中的任务ID"""
        selection = self.task_tree.selection()
        if not selection:
            return None

        item = self.task_tree.item(selection[0])
        return item['values'][0]

    def process_selected_task(self):
        """处理选中的任务"""
        task_id = self.get_selected_task_id()
        if not task_id:
            messagebox.showwarning("警告", "请选择要处理的任务")
            return

        if not self.bot:
            messagebox.showerror("错误", "未连接到Claude API")
            return

        # 在新线程中处理任务，避免界面卡死
        def process_task():
            try:
                self.log_message(f"🤖 开始处理任务: {task_id}")
                result = self.bot.process_code_request(task_id)

                if result:
                    self.log_message(f"✅ 任务完成: {task_id}")
                    self.root.after(0, self.update_task_list)  # 在主线程更新UI
                else:
                    self.log_message(f"❌ 任务处理失败: {task_id}")

            except Exception as e:
                self.log_message(f"❌ 处理任务时出错: {str(e)}")

        thread = threading.Thread(target=process_task)
        thread.daemon = True
        thread.start()

    def view_result(self):
        """查看任务结果"""
        task_id = self.get_selected_task_id()
        if not task_id:
            messagebox.showwarning("警告", "请选择要查看的任务")
            return

        if not self.bot:
            return

        result = self.bot.get_task_result(task_id)
        if result:
            # 创建新窗口显示结果
            result_window = tk.Toplevel(self.root)
            result_window.title(f"任务结果 - {task_id}")
            result_window.geometry("800x600")

            text_widget = scrolledtext.ScrolledText(result_window, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert("1.0", result)
            text_widget.config(state=tk.DISABLED)
        else:
            messagebox.showinfo("信息", "该任务尚未完成或无结果")

    def on_task_double_click(self, event):
        """双击任务项时查看结果"""
        self.view_result()

    def save_results(self):
        """保存所有结果"""
        if not self.bot:
            return

        try:
            self.bot.save_results()
            self.log_message("💾 结果已保存到 claude_results.json")
            messagebox.showinfo("成功", "结果已保存到 claude_results.json")
        except Exception as e:
            self.log_message(f"❌ 保存失败: {str(e)}")
            messagebox.showerror("错误", f"保存失败: {str(e)}")


def main():
    """主函数"""
    root = tk.Tk()
    app = ClaudeBotGUI(root)

    # 设置窗口图标和其他属性
    root.protocol("WM_DELETE_WINDOW", root.quit)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("程序被用户中断")


if __name__ == "__main__":
    main()