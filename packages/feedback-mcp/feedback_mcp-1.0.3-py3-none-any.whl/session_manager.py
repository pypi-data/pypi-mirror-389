#!/usr/bin/env python3
"""
会话状态管理器
用于管理stop hook和feedback UI之间的会话状态，避免死循环
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

class SessionManager:
    """管理会话状态，避免stop hook死循环"""
    
    def __init__(self, state_file: Optional[str] = None):
        """初始化会话管理器
        
        Args:
            state_file: 状态文件路径，默认为脚本同目录的session_states.json
        """
        if state_file:
            self.state_file = Path(state_file)
        else:
            # 使用相对路径，与脚本在同一目录
            script_dir = Path(__file__).parent
            self.state_file = script_dir / 'session_states.json'
        
        self.sessions = self._load_sessions()
        self._cleanup_old_sessions()
    
    def _load_sessions(self) -> Dict[str, Dict[str, Any]]:
        """加载会话状态"""
        if not self.state_file.exists():
            return {"sessions": {}}
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {"sessions": {}}
        except (json.JSONDecodeError, IOError):
            return {"sessions": {}}
    
    def _save_sessions(self):
        """保存会话状态"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving sessions: {e}", file=sys.stderr)
    
    def _cleanup_old_sessions(self):
        """清理超过24小时的旧会话"""
        if "sessions" not in self.sessions:
            self.sessions["sessions"] = {}
            return
        
        current_time = datetime.now()
        sessions_to_remove = []
        
        for session_id, session_data in self.sessions["sessions"].items():
            if "timestamp" in session_data:
                try:
                    session_time = datetime.fromisoformat(session_data["timestamp"])
                    if current_time - session_time > timedelta(hours=24):
                        sessions_to_remove.append(session_id)
                except (ValueError, TypeError):
                    sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions["sessions"][session_id]
        
        if sessions_to_remove:
            self._save_sessions()
    
    def get_session_status(self, session_id: str) -> Optional[str]:
        """获取会话状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话状态: "user_closed", "active", "feedback_pending" 或 None
        """
        if "sessions" not in self.sessions:
            return None
        
        session = self.sessions["sessions"].get(session_id)
        if session:
            return session.get("status")
        return None
    
    def set_session_status(self, session_id: str, status: str, action: Optional[str] = None):
        """设置会话状态

        Args:
            session_id: 会话ID
            status: 状态 ("user_closed", "active", "feedback_pending")
            action: 最后的动作描述
        """
        if "sessions" not in self.sessions:
            self.sessions["sessions"] = {}

        # 保留现有的block_count（如果存在）
        existing_session = self.sessions["sessions"].get(session_id, {})
        block_count = existing_session.get("block_count", 0)

        self.sessions["sessions"][session_id] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "last_action": action or status,
            "block_count": block_count
        }
        self._save_sessions()
    
    def is_feedback_closed(self, session_id: str) -> bool:
        """检查会话是否因用户关闭feedback而结束
        
        Args:
            session_id: 会话ID
            
        Returns:
            True如果用户主动关闭了feedback窗口
        """
        status = self.get_session_status(session_id)
        return status == "user_closed"
    
    def mark_feedback_closed(self, session_id: str):
        """标记feedback被用户关闭
        
        Args:
            session_id: 会话ID
        """
        self.set_session_status(session_id, "user_closed", "feedback_window_closed_by_user")
    
    def get_block_count(self, session_id: str) -> int:
        """获取会话的阻止次数

        Args:
            session_id: 会话ID

        Returns:
            阻止次数
        """
        if "sessions" not in self.sessions:
            return 0

        session = self.sessions["sessions"].get(session_id, {})
        return session.get("block_count", 0)

    def increment_block_count(self, session_id: str) -> int:
        """增加会话的阻止次数

        Args:
            session_id: 会话ID

        Returns:
            更新后的阻止次数
        """
        if "sessions" not in self.sessions:
            self.sessions["sessions"] = {}

        if session_id not in self.sessions["sessions"]:
            self.sessions["sessions"][session_id] = {
                "status": "active",
                "timestamp": datetime.now().isoformat(),
                "block_count": 0
            }

        self.sessions["sessions"][session_id]["block_count"] = \
            self.sessions["sessions"][session_id].get("block_count", 0) + 1
        self.sessions["sessions"][session_id]["timestamp"] = datetime.now().isoformat()
        self._save_sessions()

        return self.sessions["sessions"][session_id]["block_count"]

    def clear_session(self, session_id: str):
        """清除会话状态

        Args:
            session_id: 会话ID
        """
        if "sessions" in self.sessions and session_id in self.sessions["sessions"]:
            del self.sessions["sessions"][session_id]
            self._save_sessions()


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='管理会话状态')
    parser.add_argument('action', choices=['get', 'set', 'check', 'mark_closed', 'clear'],
                        help='要执行的操作')
    parser.add_argument('session_id', help='会话ID')
    parser.add_argument('--status', help='设置的状态 (用于set操作)')
    parser.add_argument('--state-file', help='状态文件路径')
    
    args = parser.parse_args()
    
    manager = SessionManager(args.state_file)
    
    if args.action == 'get':
        status = manager.get_session_status(args.session_id)
        print(status if status else "none")
        
    elif args.action == 'set':
        if not args.status:
            print("Error: --status required for set action", file=sys.stderr)
            sys.exit(1)
        manager.set_session_status(args.session_id, args.status)
        print(f"Session {args.session_id} status set to {args.status}")
        
    elif args.action == 'check':
        is_closed = manager.is_feedback_closed(args.session_id)
        print("closed" if is_closed else "active")
        sys.exit(0 if not is_closed else 1)
        
    elif args.action == 'mark_closed':
        manager.mark_feedback_closed(args.session_id)
        print(f"Session {args.session_id} marked as closed by user")
        
    elif args.action == 'clear':
        manager.clear_session(args.session_id)
        print(f"Session {args.session_id} cleared")


if __name__ == "__main__":
    main()