"""
UI 模块 - 导出UI组件
"""

# 紧凑反馈界面
try:
    from .compact_feedback_ui import CompactFeedbackUI
except ImportError:
    CompactFeedbackUI = None

__all__ = [
    'CompactFeedbackUI'
] 