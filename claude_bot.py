#!/usr/bin/env python3
"""
Claude AI Bot - 代码完成通知机器人
当Claude完成代码任务时发送通知
"""
import os
import time
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
import anthropic
from dotenv import load_dotenv
from plyer import notification
import requests


class ClaudeBot:
    """Claude AI Bot for code completion notifications"""

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.notification_email = os.getenv('NOTIFICATION_EMAIL')

        # 邮件配置
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')

        # 微信通知配置（Server酱）
        self.serverchan_key = os.getenv('SERVERCHAN_KEY')

        # 通知方式配置
        self.enable_desktop = os.getenv('ENABLE_DESKTOP_NOTIFICATION', 'true').lower() == 'true'
        self.enable_email = os.getenv('ENABLE_EMAIL_NOTIFICATION', 'false').lower() == 'true'
        self.enable_wechat = os.getenv('ENABLE_WECHAT_NOTIFICATION', 'false').lower() == 'true'

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.tasks: List[Dict] = []
        self.completed_tasks: List[Dict] = []

    def add_task(self, task_description: str, code_requirements: str = "") -> str:
        """添加新的代码任务"""
        task_id = f"task_{int(time.time())}"
        task = {
            "id": task_id,
            "description": task_description,
            "code_requirements": code_requirements,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "result": None
        }
        self.tasks.append(task)
        print(f"✅ 任务已添加: {task_description}")
        return task_id

    def process_code_request(self, task_id: str) -> Optional[str]:
        """处理代码请求并获取Claude的响应"""
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if not task:
            return None

        print(f"🤖 Claude正在处理任务: {task['description']}")
        task["status"] = "processing"

        try:
            # 构建提示
            prompt = f"""
请帮我完成以下代码任务：

任务描述：{task['description']}
代码要求：{task['code_requirements']}

请提供完整的代码实现，并在最后添加注释说明代码的功能。
"""

            # 调用Claude API
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )

            result = response.content[0].text

            # 更新任务状态
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
            task["result"] = result

            # 移动到已完成列表
            self.tasks.remove(task)
            self.completed_tasks.append(task)

            # 发送通知
            self.send_notification(task)

            print(f"✅ 任务完成: {task['description']}")
            return result

        except Exception as e:
            task["status"] = "failed"
            task["error"] = str(e)
            print(f"❌ 任务失败: {e}")
            return None

    def send_notification(self, task: Dict) -> None:
        """发送任务完成通知"""
        title = "Claude代码任务完成"
        message = f"任务: {task['description']}\n完成时间: {task['completed_at']}"

        notification_sent = False

        # 1. 桌面通知
        if self.enable_desktop:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    timeout=10
                )
                print(f"🖥️ 桌面通知已发送")
                notification_sent = True
            except Exception as e:
                print(f"⚠️ 桌面通知发送失败: {e}")

        # 2. 邮件通知
        if self.enable_email and self.sender_email and self.sender_password:
            try:
                self.send_email_notification(title, message, task)
                print(f"📧 邮件通知已发送")
                notification_sent = True
            except Exception as e:
                print(f"⚠️ 邮件通知发送失败: {e}")

        # 3. 微信通知（Server酱）
        if self.enable_wechat and self.serverchan_key:
            try:
                self.send_wechat_notification(title, message, task)
                print(f"💬 微信通知已发送")
                notification_sent = True
            except Exception as e:
                print(f"⚠️ 微信通知发送失败: {e}")

        if notification_sent:
            print(f"🔔 通知已发送: {task['description']}")
        else:
            print(f"⚠️ 未发送任何通知，请检查配置")

    def send_email_notification(self, title: str, message: str, task: Dict) -> None:
        """发送邮件通知"""
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = self.notification_email
        msg['Subject'] = title

        body = f"""
{message}

任务详情：
- 任务ID: {task['id']}
- 描述: {task['description']}
- 状态: {task['status']}
- 完成时间: {task['completed_at']}

代码结果预览：
{task['result'][:500] if task['result'] else '无结果'}...
        """

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.starttls()
        server.login(self.sender_email, self.sender_password)
        text = msg.as_string()
        server.sendmail(self.sender_email, self.notification_email, text)
        server.quit()

    def send_wechat_notification(self, title: str, message: str, task: Dict) -> None:
        """通过Server酱发送微信通知"""
        url = f"https://sctapi.ftqq.com/{self.serverchan_key}.send"

        content = f"""
{message}

📋 **任务详情**
- 🆔 任务ID: `{task['id']}`
- 📝 描述: {task['description']}
- ✅ 状态: {task['status']}
- ⏰ 完成时间: {task['completed_at']}

💻 **代码结果预览**
```
{task['result'][:300] if task['result'] else '无结果'}...
```
        """

        data = {
            'title': title,
            'desp': content
        }

        response = requests.post(url, data=data)
        if response.status_code != 200:
            raise Exception(f"Server酱请求失败: {response.status_code}")

    def list_tasks(self) -> None:
        """列出所有任务"""
        print("\n📋 当前任务:")
        for task in self.tasks:
            status_icon = "⏳" if task["status"] == "pending" else "🔄"
            print(f"  {status_icon} [{task['id']}] {task['description']} - {task['status']}")

        print("\n✅ 已完成任务:")
        for task in self.completed_tasks:
            print(f"  ✅ [{task['id']}] {task['description']} - 完成于 {task['completed_at']}")

    def get_task_result(self, task_id: str) -> Optional[str]:
        """获取任务结果"""
        task = next((t for t in self.completed_tasks if t["id"] == task_id), None)
        if task and task["result"]:
            return task["result"]
        return None

    def save_results(self, filename: str = "claude_results.json") -> None:
        """保存所有结果到文件"""
        all_tasks = self.tasks + self.completed_tasks
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_tasks, f, ensure_ascii=False, indent=2)
        print(f"💾 结果已保存到 {filename}")


def main():
    """主函数 - 交互式界面"""
    try:
        # 设置输出编码
        import sys
        if sys.platform == 'win32':
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

        bot = ClaudeBot()
        print("🤖 Claude代码通知机器人已启动!")
        print("可用命令:")
        print("  1. add <描述> - 添加新任务")
        print("  2. process <task_id> - 处理指定任务")
        print("  3. list - 列出所有任务")
        print("  4. result <task_id> - 查看任务结果")
        print("  5. save - 保存所有结果")
        print("  6. quit - 退出程序")

        while True:
            command = input("\n请输入命令: ").strip().split()

            if not command:
                continue

            cmd = command[0].lower()

            if cmd == "add":
                if len(command) < 2:
                    print("请提供任务描述")
                    continue
                description = " ".join(command[1:])
                requirements = input("代码要求 (可选): ").strip()
                task_id = bot.add_task(description, requirements)
                print(f"任务ID: {task_id}")

            elif cmd == "process":
                if len(command) < 2:
                    print("请提供任务ID")
                    continue
                result = bot.process_code_request(command[1])
                if result:
                    print(f"\n📝 代码结果:\n{result}")

            elif cmd == "list":
                bot.list_tasks()

            elif cmd == "result":
                if len(command) < 2:
                    print("请提供任务ID")
                    continue
                result = bot.get_task_result(command[1])
                if result:
                    print(f"\n📝 任务结果:\n{result}")
                else:
                    print("未找到该任务的结果")

            elif cmd == "save":
                bot.save_results()

            elif cmd == "quit":
                print("👋 再见!")
                break

            else:
                print("未知命令，请重试")

    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
    except Exception as e:
        print(f"❌ 程序错误: {e}")


if __name__ == "__main__":
    main()