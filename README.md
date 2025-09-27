# Claude AI Bot - 代码完成通知机器人

这是一个Python机器人，当Claude完成代码任务时会自动发送通知。

## 功能特性

- 🤖 与Claude AI集成，处理代码请求
- 🔔 代码完成后自动发送系统通知
- 📋 任务管理和状态跟踪
- 💾 结果保存和查询
- 🖥️ 交互式命令行界面

## 安装步骤

1. 克隆项目到本地
2. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置环境变量：
   - 复制 `.env.example` 为 `.env`
   - 在 `.env` 文件中填入你的Claude API密钥

4. 运行机器人：
   ```bash
   python claude_bot.py
   ```

## 使用方法

启动后，可以使用以下命令：

- `add <任务描述>` - 添加新的代码任务
- `process <task_id>` - 让Claude处理指定任务
- `list` - 查看所有任务状态
- `result <task_id>` - 查看任务完成结果
- `save` - 保存所有结果到JSON文件
- `quit` - 退出程序

## 示例使用

```
🤖 Claude代码通知机器人已启动!

请输入命令: add 写一个Python函数来计算斐波那契数列
✅ 任务已添加: 写一个Python函数来计算斐波那契数列
任务ID: task_1695123456

请输入命令: process task_1695123456
🤖 Claude正在处理任务: 写一个Python函数来计算斐波那契数列
✅ 任务完成: 写一个Python函数来计算斐波那契数列
🔔 通知已发送: 写一个Python函数来计算斐波那契数列

📝 代码结果:
[Claude生成的代码会显示在这里]
```

## 配置说明

在 `.env` 文件中需要配置：

- `ANTHROPIC_API_KEY`: 你的Claude API密钥
- `NOTIFICATION_EMAIL`: 通知邮箱（可选）

## 注意事项

- 需要有效的Claude API密钥才能使用
- 系统通知功能在Windows/Mac/Linux上都支持
- 所有任务结果会保存在本地JSON文件中