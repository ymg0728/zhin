#!/usr/bin/env python3
"""
Claude自动监控器 - 自动启动版本
"""
import sys
import os
from claude_auto_monitor import ClaudeAutoMonitor

def main():
    """自动启动监控"""
    # 设置输出编码
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

    print("🤖 Claude自动监控器 - 自动启动")
    print("=" * 50)

    try:
        monitor = ClaudeAutoMonitor()
        print("✅ 监控器初始化成功")

        # 自动开始监控
        monitor.start_monitoring()
        print("🔍 自动监控已启动，正在后台运行...")
        print("💡 监控将检测以下完成标志：")
        print("   - ✅ 完成、任务完成、代码完成")
        print("   - Successfully、Done、Implementation complete")
        print("   - 等等...")
        print()
        print("📱 通知方式：")
        print(f"   - 桌面通知: {'✅ 启用' if monitor.enable_desktop else '❌ 禁用'}")
        print(f"   - 微信通知: {'✅ 启用' if monitor.enable_wechat else '❌ 禁用'}")
        print()
        print("⚠️  按 Ctrl+C 停止监控")

        # 保持程序运行
        try:
            while monitor.is_running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ 接收到停止信号")
            monitor.stop_monitoring()
            print("👋 监控已停止，再见！")

    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()