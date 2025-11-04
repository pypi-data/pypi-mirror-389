#!/usr/bin/env python3
"""
Stop Hook处理脚本
智能处理stop事件，避免死循环
"""
import sys
import json
import os
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from session_manager import SessionManager
from workspace_manager import WorkspaceManager, get_session_title_for_session


def load_task_list(session_id: str, project_path: str = None) -> list:
    """加载任务列表

    Args:
        session_id: 会话ID
        project_path: 项目路径

    Returns:
        任务列表，每个任务包含 id, title, state
    """
    try:
        if not project_path:
            project_path = Path.cwd()
        else:
            project_path = Path(project_path)

        task_file = project_path / '.workspace' / 'tasks' / f'{session_id}.json'
        if not task_file.exists():
            return []

        with open(task_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('tasks', [])
    except Exception:
        return []


def format_context_info(session_id: str, project_path: str = None) -> str:
    """格式化上下文信息

    Args:
        session_id: 会话ID
        project_path: 项目路径

    Returns:
        格式化的上下文信息字符串
    """
    lines = []
    has_content = False

    # 获取会话标题
    session_title = get_session_title_for_session(session_id, project_path)

    # 获取阶段信息
    workspace_mgr = WorkspaceManager(project_path)
    stage_info = workspace_mgr.get_stage_info(session_id)

    # 获取任务列表
    tasks = load_task_list(session_id, project_path)

    # 只有在有阶段信息或任务列表时才显示
    if stage_info or tasks or session_title:
        lines.append("# 当前上下文相关信息：")
        lines.append("")
        has_content = True

    # 显示会话标题（仅当有值时）
    if session_title:
        # 检查是否为默认的新会话标题（包含"新会话"或以"New conversation"开头）
        if "新会话" in session_title or session_title.startswith("New conversation"):
            lines.append("## 当前会话标题：" + session_title)
            lines.append("⚠️ **提醒：请根据工作内容及时更新会话标题**")
            lines.append("")
        else:
            lines.append("## 当前会话标题：" + session_title)
            lines.append("")

    # 显示阶段信息（仅当有值时）
    if stage_info:
        current_stage = stage_info.get('current_stage', {})
        next_stage = stage_info.get('next_stage', {})

        if current_stage and current_stage.get('title'):
            lines.append(f"## 当前阶段：{current_stage.get('title')}")

        if next_stage and next_stage.get('title'):
            lines.append(f"## 下一个阶段：{next_stage.get('title')}")
        elif current_stage:  # 有当前阶段但没有下一阶段
            lines.append("## 下一个阶段：已完成所有阶段")

    # 显示任务列表（仅当有任务时）
    if tasks:
        lines.append("## 任务列表：")

        for task in tasks:
            state = task.get('state', 'pending')
            title = task.get('title', '未命名任务')
            task_id = task.get('id', '')

            # 简化标题显示
            if '(执行前请查看该步骤的详细规则)' in title:
                title = title.replace('(执行前请查看该步骤的详细规则)', '').strip()

            if state == 'completed':
                checkbox = '[x]'
            elif state == 'in_progress':
                checkbox = '[~]'
            else:
                checkbox = '[ ]'

            lines.append(f"- {checkbox} {task_id}. {title}")

        lines.append("")

    # 添加提示信息
    if has_content:
        lines.append("请分析接下来的行动计划，是继续自动工作还是使用 feedback 工具向用户反馈/请示")
        lines.append("")
        lines.append(f"当前的 session_id:{session_id}")
    else:
        # 没有上下文信息时的简化提示
        lines.append("请使用 feedback 工具向用户反馈/请示")
        lines.append("")
        lines.append(f"当前的 session_id:{session_id}")

    return "\n".join(lines)


def main():
    """主函数"""
    try:
        # 从stdin读取JSON输入
        input_data = json.load(sys.stdin)

        # 提取关键信息
        session_id = input_data.get('session_id', '')
        stop_hook_active = input_data.get('stop_hook_active', False)

        # 创建会话管理器
        manager = SessionManager()

        # 决策逻辑
        if session_id:
            # 1. 检查用户是否已关闭feedback窗口
            if manager.is_feedback_closed(session_id):
                # 清理会话状态，为下次使用做准备
                manager.clear_session(session_id)
                # 用户已关闭feedback窗口，不返回任何内容（静默允许停止）
                return 0

            # 2. 检查阻止次数，避免死循环
            current_block_count = manager.get_block_count(session_id)
            MAX_BLOCK_COUNT = 2  # 最多阻止2次

            if current_block_count >= MAX_BLOCK_COUNT:
                # 超过最大阻止次数，允许停止以避免死循环
                manager.clear_session(session_id)  # 清理会话状态
                result = {
                    "decision": "approve",
                    "reason": f"已达到最大重试次数({MAX_BLOCK_COUNT}次)，允许停止以避免循环。如feedback工具不可用，请检查MCP服务状态。"
                }
                print(json.dumps(result, ensure_ascii=False))
                return 0

            # 3. 增加阻止计数
            new_block_count = manager.increment_block_count(session_id)

        # 4. 默认行为：阻止停止并提示使用feedback工具
        # 使用新的格式化上下文信息
        if session_id:
            # 获取项目路径
            project_path = os.getcwd()
            reason_text = format_context_info(session_id, project_path)
        else:
            reason_text = "请你调用 feedback mcp tool 向用户反馈/请示。示例：使用 mcp__feedback__feedback 工具向用户汇报当前工作进度、完成状态或请求下一步指示。"

        result = {
            "decision": "block",
            "reason": reason_text
        }
        print(json.dumps(result, ensure_ascii=False))
        return 0
        
    except Exception as e:
        # 发生错误时，默认允许停止（避免卡死）
        error_result = {
            "decision": "approve",
            "reason": f"Hook处理出错: {str(e)}"
        }
        print(json.dumps(error_result, ensure_ascii=False), file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())