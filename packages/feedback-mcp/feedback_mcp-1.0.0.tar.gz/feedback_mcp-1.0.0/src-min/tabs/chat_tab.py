"""
聊天标签页 - 包含反馈输入、预定义选项、指令管理等功能
"""
import sys
import os
import json
from datetime import datetime
from typing import Optional, List, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QGridLayout,
    QCheckBox, QPushButton, QProgressBar, QSizePolicy, QFileDialog, QMessageBox, QLabel
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint
from PySide6.QtGui import QFont, QTextCursor

try:
    from .base_tab import BaseTab
except ImportError:
    from base_tab import BaseTab

try:
    from ..components.feedback_text_edit import FeedbackTextEdit
    from ..components.markdown_display import MarkdownDisplayWidget
except ImportError:
    try:
        from components.feedback_text_edit import FeedbackTextEdit
        from components.markdown_display import MarkdownDisplayWidget
    except ImportError:
        # 如果导入失败，使用原始组件
        from PySide6.QtWidgets import QTextEdit
        FeedbackTextEdit = QTextEdit
        MarkdownDisplayWidget = QTextEdit

# 导入指令管理组件
try:
    from ..components.command_tab import CommandTabWidget
except ImportError:
    try:
        from components.command_tab import CommandTabWidget
    except ImportError:
        CommandTabWidget = None

# 导入历史记录弹窗组件
try:
    from ..components.history_popup import HistoryPopup
    HISTORY_POPUP_AVAILABLE = True
except ImportError:
    try:
        from components.history_popup import HistoryPopup
        HISTORY_POPUP_AVAILABLE = True
    except ImportError:
        HISTORY_POPUP_AVAILABLE = False
        print("Warning: HistoryPopup component not available")


class ChatTab(BaseTab):
    """聊天标签页 - 处理用户反馈输入和交互"""
    
    # 信号定义
    feedback_submitted = Signal(list, list)  # 结构化内容数组, 图片列表
    command_executed = Signal(str)  # 指令内容
    option_executed = Signal(int)  # 选项索引
    text_changed = Signal()  # 文本变化
    
    def __init__(self, prompt: str, predefined_options: Optional[List[str]] = None,
                 project_path: Optional[str] = None, work_title: Optional[str] = None,
                 timeout: int = 60, files: Optional[List[str]] = None, bugdetail: Optional[str] = None,
                 session_id: Optional[str] = None, workspace_id: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.predefined_options = predefined_options or []
        self.project_path = project_path
        self.work_title = work_title or ""
        self.timeout = timeout
        self.elapsed_time = 0
        self.files = files or []  # 保存文件列表
        self.bugdetail = bugdetail  # 保存bug详情
        self.session_id = session_id  # 保存会话ID
        self.workspace_id = workspace_id  # 保存工作空间ID

        # 阶段信息
        self.stage_info = None
        self._load_stage_info()

        # 工作空间信息
        self.workspace_goal = None
        self.dialog_title = None
        self._load_workspace_context()

        # 任务信息
        self.current_task = None
        self.next_task = None
        self._load_task_info()

        # 深度思考模式状态 - 从设置中恢复
        self.deep_thinking_mode = self._load_deep_thinking_mode()

        # UI组件
        self.description_display = None
        self.option_checkboxes = []
        self.command_widget = None
        self.feedback_text = None
        self.submit_button = None
        self.progress_bar = None
        self.image_button = None  # 图片选择按钮
        self.history_button = None  # 历史记录按钮
        self.deep_thinking_button = None  # 深度思考按钮

        # 指令标签相关属性
        self.selected_command = None  # 当前选中的指令信息
        self.command_label_widget = None  # 指令标签组件

        # 历史记录相关属性
        self.max_history_records = 10  # 最大保存记录数

        self.create_ui()

        # 初始化完成后更新深度思考按钮状态
        if hasattr(self, 'deep_thinking_button') and self.deep_thinking_button:
            self.deep_thinking_button.setChecked(self.deep_thinking_mode)

        # 保存AI发送的消息（prompt）到历史记录
        if prompt and prompt.strip():
            self.save_response_to_history(prompt)
    
    def create_ui(self):
        """创建聊天标签页UI"""
        layout = QVBoxLayout(self)

        # 第一行：显示工作空间goal（如果有）
        if self.workspace_goal:
            workspace_label = QLabel(f"当前工作空间: {self.workspace_goal}")
            workspace_label.setWordWrap(True)
            workspace_label.setAlignment(Qt.AlignCenter)
            workspace_label.setStyleSheet("""
                QLabel {
                    font-size: 13px;
                    font-weight: bold;
                    color: #8AB4F8;
                    padding: 6px;
                    background-color: rgba(138, 180, 248, 8);
                    border: 1px solid rgba(138, 180, 248, 25);
                    border-radius: 4px;
                    margin: 5px 0px;
                }
            """)
            layout.addWidget(workspace_label)

        # 第二行：显示当前阶段信息（如果有）
        if self.stage_info and self.stage_info.get('current_stage'):
            current_stage = self.stage_info['current_stage']
            stage_label = QLabel(f"当前阶段: {current_stage.get('title', '')}")
            stage_label.setWordWrap(True)
            stage_label.setAlignment(Qt.AlignCenter)
            stage_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #FF8C00;
                    padding: 8px;
                    background-color: rgba(255, 140, 0, 10);
                    border: 1px solid rgba(255, 140, 0, 30);
                    border-radius: 4px;
                    margin: 5px 0px;
                }
            """)
            layout.addWidget(stage_label)

        # 显示当前任务（如果有）
        if self.current_task:
            self._create_current_task_label(layout)

        # 第三行：显示对话标题（如果有）
        if self.dialog_title:
            dialog_label = QLabel(f"当前对话: {self.dialog_title}")
            dialog_label.setWordWrap(True)
            dialog_label.setStyleSheet("""
                QLabel {
                    font-size: 15px;
                    font-weight: bold;
                    color: white;
                    padding: 10px 0px;
                    background-color: transparent;
                }
            """)
            layout.addWidget(dialog_label)

        # 如果有bugdetail，将其添加到prompt前面
        display_prompt = self.prompt
        if self.bugdetail:
            display_prompt = f"🐛 **当前正在修复bug:**\n{self.bugdetail}\n\n---\n\n{self.prompt}"

        # 使用支持Markdown的显示组件 - 简化布局，去掉外围框架
        self.description_display = MarkdownDisplayWidget()
        self.description_display.setMarkdownText(display_prompt)
        # 设置合适的高度，默认250px，最大400px
        self.description_display.setMinimumHeight(250)
        self.description_display.setMaximumHeight(400)
        layout.addWidget(self.description_display)
        
        # 创建一个反馈布局容器（只包含其他元素，不包含markdown显示）
        feedback_container = QWidget()
        feedback_layout = QVBoxLayout(feedback_container)
        feedback_layout.setContentsMargins(5, 5, 5, 5)

        # 添加预定义选项
        if self.predefined_options:
            self._create_predefined_options(feedback_layout)

        # 添加阶段切换按钮（如果有）
        if self.stage_info:
            self._create_stage_buttons(feedback_layout)

        # 添加下一任务按钮（独立显示，不依赖stage_info）
        if self.next_task:
            self._create_next_task_button(feedback_layout)

        # 添加文件列表显示
        if self.files:
            self._create_files_list(feedback_layout)

        # 使用新的指令管理组件（隐藏固定显示区域）
        if CommandTabWidget:
            self.command_widget = CommandTabWidget(self.project_path, self)
            self.command_widget.command_executed.connect(self._handle_command_execution)
            # 隐藏固定显示的指令区域，用户通过 / // /// 弹窗使用指令
            self.command_widget.hide()

        # 自由文本反馈输入
        self._create_feedback_input(feedback_layout)
        
        # 提交按钮布局
        self._create_submit_section(feedback_layout)
        
        # 进度条布局
        if self.timeout > 0:
            self._create_progress_section(feedback_layout)

        # 添加反馈容器到主布局
        layout.addWidget(feedback_container)

    def _create_files_list(self, layout):
        """创建文件列表显示区域"""
        import subprocess
        import platform
        from functools import partial

        # 创建紧凑的文件列表容器（使用水平布局）
        files_container = QWidget()
        files_container.setMaximumHeight(40)  # 限制高度，更紧凑
        files_container_layout = QHBoxLayout(files_container)
        files_container_layout.setContentsMargins(5, 5, 5, 5)
        files_container_layout.setSpacing(10)

        # 添加文件图标标题
        title_label = QLabel("📝")
        title_label.setToolTip("AI创建或修改的文件")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #888;
                background-color: transparent;
            }
        """)
        files_container_layout.addWidget(title_label)

        # 为每个文件创建紧凑的可点击标签
        for file_path in self.files:
            file_name = os.path.basename(file_path)
            # 如果文件名太长，截断显示
            display_name = file_name if len(file_name) <= 20 else file_name[:17] + "..."

            file_btn = QPushButton(display_name)
            # 获取IDE名称
            ide_name = os.getenv('IDE', 'cursor')
            # IDE显示名称映射
            ide_display_names = {
                'cursor': 'Cursor',
                'kiro': 'Kiro',
                'vscode': 'VSCode',
                'code': 'VSCode'
            }
            display_ide = ide_display_names.get(ide_name.lower(), ide_name)
            file_btn.setToolTip(f"点击在{display_ide}中打开: {file_path}")
            file_btn.setCursor(Qt.PointingHandCursor)  # 设置手形光标
            file_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(76, 175, 80, 20);
                    color: #4CAF50;
                    border: 1px solid rgba(76, 175, 80, 40);
                    padding: 3px 8px;
                    border-radius: 3px;
                    font-size: 11px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: rgba(76, 175, 80, 40);
                    border: 1px solid #4CAF50;
                }
                QPushButton:pressed {
                    background-color: rgba(76, 175, 80, 60);
                }
            """)

            # 使用partial函数绑定参数，避免闭包问题
            def open_with_ide(file_path):
                try:
                    # 导入ide_utils模块
                    import sys
                    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if parent_dir not in sys.path:
                        sys.path.insert(0, parent_dir)
                    from ide_utils import open_project_with_ide

                    # 获取IDE名称
                    ide_name = os.getenv('IDE', 'cursor')

                    # 使用通用的IDE打开函数
                    success = open_project_with_ide(file_path, ide_name)

                    if not success:
                        # 如果失败，使用系统默认编辑器打开
                        if platform.system() == "Darwin":
                            subprocess.run(["open", file_path], check=True)
                        elif platform.system() == "Windows":
                            os.startfile(file_path)
                        else:
                            subprocess.run(["xdg-open", file_path], check=True)

                except Exception as e:
                    # 使用系统默认编辑器打开作为最终后备
                    try:
                        if platform.system() == "Darwin":
                            subprocess.run(["open", file_path], check=True)
                        elif platform.system() == "Windows":
                            os.startfile(file_path)
                        else:
                            subprocess.run(["xdg-open", file_path], check=True)
                    except Exception as e2:
                        QMessageBox.warning(self, "打开失败",
                            f"无法打开文件: {file_name}\n"
                            f"路径: {file_path}\n"
                            f"错误: {str(e2)}")

            file_btn.clicked.connect(partial(open_with_ide, file_path))
            files_container_layout.addWidget(file_btn)

        # 添加弹簧使按钮靠左对齐
        files_container_layout.addStretch()

        layout.addWidget(files_container)
    
    def _create_predefined_options(self, layout):
        """创建预定义选项区域 - 与原始版本样式保持一致"""
        options_frame = QFrame()
        options_frame.setMinimumHeight(100)  # 设置可选项区域最小高度为100
        # 使用网格布局实现两列显示，与原版保持一致
        options_layout = QGridLayout(options_frame)
        options_layout.setContentsMargins(0, 10, 0, 10)
        options_layout.setSpacing(5)  # 设置间距
        
        # 计算网格的行列布局
        total_options = len(self.predefined_options)
        columns = 2  # 两列布局
        rows = (total_options + columns - 1) // columns  # 向上取整
        
        for i, option in enumerate(self.predefined_options):
            # 计算当前项目在网格中的位置
            row = i // columns
            col = i % columns
            
            # Create horizontal layout for each option (checkbox + button)
            option_item_frame = QFrame()
            option_item_layout = QHBoxLayout(option_item_frame)
            option_item_layout.setContentsMargins(5, 2, 5, 2)
            
            # Checkbox
            checkbox = QCheckBox(option)
            self.option_checkboxes.append(checkbox)
            option_item_layout.addWidget(checkbox)
            
            # Add stretch to push button to the right
            option_item_layout.addStretch()
            
            # Execute button for this option - 使用与原始版本相同的样式
            execute_btn = QPushButton("立即执行")
            execute_btn.setMaximumWidth(80)
            execute_btn.setProperty('option_index', i)
            execute_btn.clicked.connect(lambda checked, idx=i: self._execute_option_immediately(idx))
            execute_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
                QPushButton:pressed {
                    background-color: #E65100;
                }
            """)
            option_item_layout.addWidget(execute_btn)
            
            # Add frame to grid layout
            options_layout.addWidget(option_item_frame, row, col)
        
        layout.addWidget(options_frame)
    
    def _create_feedback_input(self, layout):
        """创建反馈输入区域"""
        # 创建指令标签区域（默认隐藏）
        self._create_command_label_section(layout)
        
        self.feedback_text = FeedbackTextEdit()
        
        # 设置项目路径，启用指令弹窗功能
        if self.project_path:
            self.feedback_text.set_project_path(self.project_path)
        
        # 设置自定义指令选择处理器
        self.feedback_text.set_command_handler(self._on_command_selected_new)
        
        # 设置输入框的大小策略，让它能够随窗口拉伸自适应高度
        self.feedback_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        font_metrics = self.feedback_text.fontMetrics()
        row_height = font_metrics.height()
        # Calculate height for 5 lines + some padding for margins
        padding = self.feedback_text.contentsMargins().top() + self.feedback_text.contentsMargins().bottom() + 5
        self.feedback_text.setMinimumHeight(5 * row_height + padding)

        self.feedback_text.setPlaceholderText("请在此输入您的反馈内容 (Ctrl+Enter 或 Cmd+Enter，输入/打开项目指令; 输入//打开个人指令；输入///打开系统指令；输入指令对应的字母选中指令)")
        
        # 监听文本变化，动态改变发送按钮颜色
        self.feedback_text.textChanged.connect(self._on_text_changed)
        
        layout.addWidget(self.feedback_text)
    
    def _create_command_label_section(self, layout):
        """创建紧凑型Element UI Tag风格的指令标签区域"""
        self.command_label_widget = QFrame()
        # 默认样式，会在显示时根据类型动态设置
        self.command_label_widget.setStyleSheet("""
            QFrame {
                background: #409EFF;
                border: 1px solid #409EFF;
                border-radius: 4px;
                margin: 2px 0px;
                padding: 0px;
            }
        """)
        self.command_label_widget.hide()  # 默认隐藏
        
        label_layout = QHBoxLayout(self.command_label_widget)
        label_layout.setContentsMargins(6, 4, 6, 4)
        label_layout.setSpacing(6)
        
        # 关闭按钮 - 在容器内左侧
        close_button = QPushButton("×")
        close_button.setFixedSize(16, 16)
        close_button.setToolTip("清除选中的指令 (或按ESC键)")
        close_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(255, 255, 255, 0.8);
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                color: white;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        close_button.clicked.connect(self._clear_selected_command)
        label_layout.addWidget(close_button)
        
        # 指令标题标签
        self.command_title_label = QLabel()
        self.command_title_label.setStyleSheet("""
            QLabel {
                color: white; 
                font-weight: 500;
                font-size: 12px;
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        label_layout.addWidget(self.command_title_label)
        
        # 编辑按钮 - 小图标
        edit_button = QPushButton("✏️")
        edit_button.setFixedSize(16, 16)
        edit_button.setToolTip("编辑当前指令")
        edit_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(255, 255, 255, 0.8);
                border: none;
                border-radius: 8px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                color: white;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        edit_button.clicked.connect(self._edit_selected_command)
        label_layout.addWidget(edit_button)
        
        layout.addWidget(self.command_label_widget)
    
    def _on_command_selected_new(self, command_content: str, command_data: dict = None):
        """新的指令选择处理方法 - 显示标签而不是替换文本"""
        # 使用直接传递的指令数据，避免通过弹窗获取可能不准确的数据
        if command_data:
            self.selected_command = {
                'title': command_data.get('title', '未知指令'),
                'content': command_content,
                'type': command_data.get('type', 'unknown')
            }
            self._show_command_label()

        # 关闭弹窗但不修改输入框内容
        self.feedback_text._close_command_popup()
    
    def _show_command_label(self):
        """显示紧凑型Element UI Tag风格的指令标签"""
        if not self.selected_command:
            return
            
        # Element UI Tag的类型配色
        type_config = {
            'project': {
                'bg_color': '#409EFF',
                'border_color': '#409EFF'
            },
            'personal': {
                'bg_color': '#67C23A', 
                'border_color': '#67C23A'
            },
            'system': {
                'bg_color': '#E6A23C',
                'border_color': '#E6A23C'
            }
        }
        
        config = type_config.get(self.selected_command['type'], {
            'bg_color': '#909399',
            'border_color': '#909399'
        })
        
        # 更新整个容器的Element UI Tag样式
        self.command_label_widget.setStyleSheet(f"""
            QFrame {{
                background: {config['bg_color']};
                border: 1px solid {config['border_color']};
                border-radius: 4px;
                margin: 2px 0px;
                padding: 0px;
            }}
        """)
        
        # 设置标题
        self.command_title_label.setText(self.selected_command['title'])
        
        # 显示标签
        self.command_label_widget.show()
    
    def _clear_selected_command(self):
        """清除选中的指令"""
        self.selected_command = None
        self.command_label_widget.hide()
    
    def _select_image(self):
        """选择图片文件"""
        try:
            file_dialog = QFileDialog(self)
            file_dialog.setFileMode(QFileDialog.ExistingFiles)  # 允许选择多个文件
            file_dialog.setNameFilter("图片文件 (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;所有文件 (*)")
            file_dialog.setWindowTitle("选择图片文件")
            
            if file_dialog.exec():
                selected_files = file_dialog.selectedFiles()
                
                for file_path in selected_files:
                    # 检查文件大小
                    try:
                        import os
                        file_size = os.path.getsize(file_path)
                        file_size_mb = file_size / (1024 * 1024)
                        
                        if file_size_mb > 50:  # 限制原始文件大小不超过50MB
                            QMessageBox.warning(
                                self, 
                                "文件过大", 
                                f"文件 {os.path.basename(file_path)} 大小为 {file_size_mb:.1f}MB，超过50MB限制。\n"
                                "请选择更小的图片文件。"
                            )
                            continue
                        
                        # 添加图片到编辑器
                        self.feedback_text.add_image_file(file_path)
                        
                    except Exception as e:
                        QMessageBox.warning(
                            self, 
                            "添加图片失败", 
                            f"无法添加图片 {file_path}: {str(e)}"
                        )
                        
        except Exception as e:
            QMessageBox.critical(
                self, 
                "选择图片失败", 
                f"选择图片时发生错误: {str(e)}"
            )
    
    def _create_submit_section(self, layout):
        """创建提交按钮区域"""
        submit_layout = QHBoxLayout()
        
        # 深度思考按钮 - 放在最左边
        self.deep_thinking_button = QPushButton("🧠")
        self.deep_thinking_button.setToolTip("深度思考模式")
        self.deep_thinking_button.setCheckable(True)  # 可切换状态
        self.deep_thinking_button.setChecked(self.deep_thinking_mode)
        self.deep_thinking_button.clicked.connect(self._toggle_deep_thinking)
        self.deep_thinking_button.setMaximumWidth(30)
        self.deep_thinking_button.setObjectName("deep_thinking_btn")
        self.deep_thinking_button.setStyleSheet("""
            QPushButton#deep_thinking_btn {
                background-color: #404040;
                color: white;
                border: 1px solid #555;
                height: 30px;
                width: 30px;
                line-height: 30px;
                text-align: center;
                border-radius: 4px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton#deep_thinking_btn:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border: 2px solid #667eea;
            }
            QPushButton#deep_thinking_btn:hover {
                background-color: #505050;
            }
            QPushButton#deep_thinking_btn:checked:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #7788ff, stop:1 #8755b2);
            }
            QPushButton#deep_thinking_btn:pressed {
                background-color: #303030;
            }
        """)
        submit_layout.addWidget(self.deep_thinking_button)
        
        # 添加一些间距
        submit_layout.addSpacing(5)
        
        # 指令按钮 - 快速打开指令弹层
        self.command_button = QPushButton("⚡")
        self.command_button.setToolTip("打开指令列表 (相当于输入 / 触发)")
        self.command_button.clicked.connect(self._show_command_popup)
        self.command_button.setMaximumWidth(30)
        self.command_button.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border: none;
                height:30px;
                width:30px;
                line-height:30px;
                text-align:center;
                border-radius: 4px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #777777;
            }
            QPushButton:pressed {
                background-color: #555555;
            }
        """)
        submit_layout.addWidget(self.command_button)
        
        # 添加一些间距
        submit_layout.addSpacing(5)
        
        # 图片选择按钮 - 只保留图标，与发送按钮并排
        self.image_button = QPushButton("📷")
        self.image_button.setToolTip("选择图片文件 (支持 PNG、JPG、JPEG、GIF、BMP、WebP)")
        self.image_button.clicked.connect(self._select_image)
        # 设置最小宽度，让高度自动匹配发送按钮
        self.image_button.setMaximumWidth(30)
        self.image_button.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border: none;
                height:30px;
                width:30px;
                line-height:30px;
                text-align:center;
                border-radius: 4px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #777777;
            }
            QPushButton:pressed {
                background-color: #555555;
            }
        """)
        submit_layout.addWidget(self.image_button)
        
        # 添加一些间距
        submit_layout.addSpacing(5)
        
        # 历史记录按钮
        self.history_button = QPushButton("📝")
        self.history_button.setToolTip("查看历史记录 (最近10条)")
        self.history_button.clicked.connect(self._show_history)
        self.history_button.setMaximumWidth(30)
        self.history_button.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border: none;
                height:30px;
                width:30px;
                line-height:30px;
                text-align:center;
                border-radius: 4px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #777777;
            }
            QPushButton:pressed {
                background-color: #555555;
            }
        """)
        submit_layout.addWidget(self.history_button)
        
        # 添加一些间距
        submit_layout.addSpacing(5)
        
        # Submit button
        self.submit_button = QPushButton("发送反馈(Ctrl+Enter 或 Cmd+Enter 提交)")
        self.submit_button.clicked.connect(self._submit_feedback)
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border: none;
                height:30px;
                line-height:30px;
                text-align:center;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
            QPushButton:pressed {
                background-color: #555555;
            }
        """)
        submit_layout.addWidget(self.submit_button)
        
        layout.addLayout(submit_layout)
    
    def _create_progress_section(self, layout):
        """创建进度条区域"""
        progress_layout = QHBoxLayout()
        
        # Countdown progress bar section
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.timeout)
        self.progress_bar.setValue(self.elapsed_time)
        self.progress_bar.setFormat(self._format_time(self.elapsed_time))
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 2px;
                background-color: #2b2b2b;
                height: 2px;
                color: white;
                font-size: 11px;
                text-align: right;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                                  stop: 0 #4CAF50, stop: 0.5 #45a049, stop: 1 #4CAF50);
                border-radius: 2px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)
    
    def _handle_command_execution(self, command_content: str):
        """处理指令执行"""
        if command_content:
            self.command_executed.emit(command_content)
    
    def _execute_option_immediately(self, option_index: int):
        """立即执行选项"""
        self.option_executed.emit(option_index)
    
    def _show_command_popup(self):
        """显示指令弹窗"""
        try:
            # 确保输入框有焦点
            if self.feedback_text:
                self.feedback_text.setFocus()
                
                # 触发指令弹窗（默认显示项目指令）
                if hasattr(self.feedback_text, '_show_command_popup'):
                    self.feedback_text._show_command_popup("", "project")
                else:
                    QMessageBox.information(self, "提示", "指令功能暂不可用")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"显示指令弹窗失败: {str(e)}")

    def _show_history(self):
        """显示历史记录"""
        try:
            # 加载历史记录
            history = self.get_recent_history()

            if not history:
                QMessageBox.information(self, "历史记录", "暂无历史记录")
                return

            # 检查弹窗组件是否可用
            if not HISTORY_POPUP_AVAILABLE:
                QMessageBox.critical(self, "错误", "历史记录弹窗组件不可用")
                return

            # 创建弹窗
            popup = HistoryPopup(self)

            # 设置历史记录数据
            popup.set_history_records(history, self)

            # 连接信号
            popup.content_inserted.connect(lambda content: self.feedback_text.insertPlainText(content))
            popup.content_copied.connect(lambda content: QApplication.clipboard().setText(content))
            popup.popup_closed.connect(lambda: None)  # 静默处理关闭事件

            # 获取主窗口（FeedbackUI）的位置和大小
            main_window = self.window()
            if main_window:
                # 获取主窗口的全局位置
                window_pos = main_window.mapToGlobal(QPoint(0, 0))
                # 弹窗左边缘与主窗口左边缘对齐
                popup_pos = QPoint(window_pos.x(), window_pos.y())
            else:
                # 如果找不到主窗口，使用按钮位置
                if hasattr(self, 'history_button') and self.history_button:
                    button = self.history_button
                    button_pos = button.mapToGlobal(button.rect().bottomLeft())
                    popup_pos = QPoint(button_pos.x() - 200, button_pos.y() + 5)
                else:
                    popup_pos = QPoint(100, 100)

            # 显示弹窗
            popup.show_at_position(popup_pos)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"显示历史记录失败: {str(e)}")
    
    def _on_text_changed(self):
        """文本变化处理"""
        if self.feedback_text and self.submit_button:
            # 根据文本内容动态改变按钮颜色 - 与原版保持一致
            has_text = bool(self.feedback_text.toPlainText().strip())
            if has_text:
                # 有内容时，按钮变为蓝色（与原版一致）
                self.submit_button.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        border: none;
                        height:30px;
                        line-height:30px;
                        text-align:center;
                        border-radius: 4px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #1976D2;
                    }
                    QPushButton:pressed {
                        background-color: #0D47A1;
                    }
                """)
            else:
                # 无内容时，按钮为灰色（与原版一致）
                self.submit_button.setStyleSheet("""
                    QPushButton {
                        background-color: #666666;
                        color: white;
                        border: none;
                        height:30px;
                        line-height:30px;
                        text-align:center;
                        border-radius: 4px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #777777;
                    }
                    QPushButton:pressed {
                        background-color: #555555;
                    }
                """)

        self.text_changed.emit()

    def _get_text_with_image_placeholders(self):
        """获取包含图片占位符的文本

        遍历文档内容，在图片位置插入占位符 [图片1]、[图片2] 等
        """
        if not self.feedback_text:
            return ""

        document = self.feedback_text.document()
        cursor = QTextCursor(document)
        cursor.movePosition(QTextCursor.Start)

        result_text = ""
        image_index = 1
        block = document.begin()

        # 遍历所有文本块
        while block.isValid():
            # 获取当前块的迭代器
            it = block.begin()

            # 遍历块中的所有片段
            while not it.atEnd():
                fragment = it.fragment()
                if fragment.isValid():
                    char_format = fragment.charFormat()

                    # 检查是否是图片格式
                    if char_format.isImageFormat():
                        # 插入图片占位符
                        result_text += f"[图片{image_index}]"
                        image_index += 1
                    else:
                        # 添加普通文本
                        result_text += fragment.text()

                it += 1

            # 添加块之间的换行符（除了最后一个块）
            block = block.next()
            if block.isValid():
                result_text += "\n"

        return result_text.strip()

    def _submit_feedback(self):
        """提交反馈"""
        if not self.feedback_text:
            return

        # 获取包含图片占位符的文本内容
        text_content = self._get_text_with_image_placeholders()
        images = self.feedback_text.get_pasted_images() if hasattr(self.feedback_text, 'get_pasted_images') else []
        
        # 获取选中的预定义选项
        selected_options = []
        for i, checkbox in enumerate(self.option_checkboxes):
            if checkbox.isChecked():
                selected_options.append(self.predefined_options[i])
        
        # 检查已选中的指令（优先使用新的指令标签机制）
        selected_command_content = ""
        if self.selected_command:
            # 使用新的指令标签机制
            selected_command_content = self.selected_command['content']
        elif hasattr(self, 'command_widget') and self.command_widget:
            # 兼容原有的指令选择方式
            for i in range(self.command_widget.count()):
                tab = self.command_widget.widget(i)
                # 检查是否有command_button_group（所有指令选项卡都有）
                if hasattr(tab, 'command_button_group'):
                    checked_button = tab.command_button_group.checkedButton()
                    if checked_button:
                        command_index = checked_button.property('command_index')
                        # 检查是否有commands数组（所有指令选项卡都有）
                        if (command_index is not None and
                            hasattr(tab, 'commands') and
                            0 <= command_index < len(tab.commands)):
                            selected_command_content = tab.commands[command_index]['content']
                            break  # 找到就停止查找
        
        # 构建结构化内容数组
        content_parts = []
        
        # 如果开启深度思考模式，在最前面添加提示
        if self.deep_thinking_mode:
            content_parts.append({
                "type": "text",
                "text": "**ultrathink**"
            })
        
        # 添加选中的预定义选项
        if selected_options:
            content_parts.append({
                "type": "options", 
                "text": "; ".join(selected_options)
            })
        
        # 添加选中的指令内容
        if selected_command_content:
            content_parts.append({
                "type": "command", 
                "text": selected_command_content
            })
        
        # 添加用户输入的文本
        if text_content:
            content_parts.append({
                "type": "text", 
                "text": text_content
            })
        
        # 保存到历史记录（保存用户发送的消息）
        if text_content:
            self.save_to_history(text_content, 'sent')
        
        # 始终发送信号，即使content_parts为空（允许发送空反馈）
        self.feedback_submitted.emit(content_parts, images)
    
    def _format_time(self, seconds: int) -> str:
        """格式化时间显示"""
        if seconds < 60:
            return f"AI已等待: {seconds}秒"
        else:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"AI已等待: {minutes}分{remaining_seconds}秒"
    
    def update_progress(self, elapsed_time: int):
        """更新进度条"""
        self.elapsed_time = elapsed_time
        if self.progress_bar:
            self.progress_bar.setValue(elapsed_time)
            self.progress_bar.setFormat(self._format_time(elapsed_time))
    
    def get_feedback_text(self) -> str:
        """获取反馈文本"""
        if self.feedback_text:
            return self.feedback_text.toPlainText().strip()
        return ""
    
    def get_selected_options(self) -> List[str]:
        """获取选中的预定义选项"""
        selected = []
        for i, checkbox in enumerate(self.option_checkboxes):
            if checkbox.isChecked():
                selected.append(self.predefined_options[i])
        return selected
    
    def _toggle_deep_thinking(self):
        """切换深度思考模式"""
        self.deep_thinking_mode = self.deep_thinking_button.isChecked()
        
        # 保存状态到设置
        self._save_deep_thinking_mode(self.deep_thinking_mode)
        
        # 更新工具提示
        if self.deep_thinking_button:
            if self.deep_thinking_mode:
                self.deep_thinking_button.setToolTip("深度思考模式已开启 (点击关闭)")
            else:
                self.deep_thinking_button.setToolTip("深度思考模式 (点击开启)")
    
    def _load_stage_info(self):
        """加载工作空间阶段信息"""
        # 如果没有session_id和workspace_id，直接返回
        if not self.session_id and not self.workspace_id:
            return

        try:
            # 导入工作空间管理器
            import sys
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from workspace_manager import WorkspaceManager

            # 创建管理器实例
            manager = WorkspaceManager(self.project_path)

            # 优先使用workspace_id，如果没有则使用session_id
            self.stage_info = manager.get_stage_info(
                session_id=self.session_id,
                workspace_id=self.workspace_id
            )
        except Exception as e:
            # 静默处理加载失败，不影响主流程
            self.stage_info = None

    def _load_workspace_context(self):
        """加载工作空间上下文信息（goal和对话标题）"""
        if not self.session_id:
            return

        try:
            # 导入工作空间管理器函数
            import sys
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from workspace_manager import get_workspace_goal_for_session, get_session_title_for_session

            # 获取工作空间goal
            self.workspace_goal = get_workspace_goal_for_session(self.session_id, self.project_path)

            # 获取对话标题（优先从workspace.yml的sessions获取，如果没有再使用work_title）
            session_title = get_session_title_for_session(self.session_id, self.project_path)
            if session_title:
                self.dialog_title = session_title
            else:
                self.dialog_title = self.work_title

        except Exception as e:
            # 静默处理加载失败，不影响主流程
            pass
            self.workspace_goal = None
            self.dialog_title = self.work_title

    def _create_stage_buttons(self, layout):
        """创建阶段切换按钮"""
        if not self.stage_info:
            return

        # 创建按钮容器
        stage_buttons_container = QWidget()
        stage_buttons_layout = QHBoxLayout(stage_buttons_container)
        stage_buttons_layout.setContentsMargins(5, 5, 5, 5)
        stage_buttons_layout.setSpacing(10)

        # 创建上一阶段按钮
        if self.stage_info.get('prev_stage'):
            prev_stage = self.stage_info['prev_stage']
            # 截断过长的标题
            title = prev_stage.get('title', '')
            if len(title) > 10:
                title = title[:10] + "..."
            prev_btn = QPushButton(f"上一阶段: {title}")
            prev_btn.setToolTip(prev_stage.get('description', ''))
            prev_btn.setCursor(Qt.PointingHandCursor)
            prev_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 水平扩展
            prev_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(200, 200, 200, 25);
                    color: #AAA;
                    border: 1px solid rgba(200, 200, 200, 45);
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 13px;
                    text-align: center;
                    min-width: 0px;
                }
                QPushButton:hover {
                    background-color: rgba(200, 200, 200, 40);
                    border: 1px solid #BBB;
                    color: #888;
                }
                QPushButton:pressed {
                    background-color: rgba(200, 200, 200, 55);
                }
            """)
            prev_btn.clicked.connect(lambda: self._on_stage_button_clicked("请进入上一阶段"))
            stage_buttons_layout.addWidget(prev_btn, 1)  # 权重1，占50%
        else:
            # 如果没有上一阶段，添加一个占位空间
            stage_buttons_layout.addStretch(1)

        # 创建下一阶段按钮
        if self.stage_info.get('next_stage'):
            next_stage = self.stage_info['next_stage']
            # 截断过长的标题
            title = next_stage.get('title', '')
            if len(title) > 10:
                title = title[:10] + "..."
            next_btn = QPushButton(f"下一阶段: {title}")
            next_btn.setToolTip(next_stage.get('description', ''))
            next_btn.setCursor(Qt.PointingHandCursor)
            next_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 水平扩展
            next_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(76, 175, 80, 30);
                    color: #4CAF50;
                    border: 1px solid rgba(76, 175, 80, 50);
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 13px;
                    text-align: center;
                    min-width: 0px;
                }
                QPushButton:hover {
                    background-color: rgba(76, 175, 80, 50);
                    border: 1px solid #4CAF50;
                }
                QPushButton:pressed {
                    background-color: rgba(76, 175, 80, 70);
                }
            """)
            next_btn.clicked.connect(lambda: self._on_stage_button_clicked("请进入下一阶段"))
            stage_buttons_layout.addWidget(next_btn, 1)  # 权重1，占50%
        else:
            # 如果没有下一阶段，添加一个占位空间
            stage_buttons_layout.addStretch(1)

        layout.addWidget(stage_buttons_container)

    def _create_next_task_button(self, layout):
        """创建下一任务按钮（独立方法）"""
        if not self.next_task:
            return

        next_task_title = self.next_task.get('title', '')
        # 如果标题过长，截断
        if len(next_task_title) > 20:
            next_task_title = next_task_title[:20] + "..."

        next_task_btn = QPushButton(f"下一任务: {next_task_title}")
        next_task_btn.setCursor(Qt.PointingHandCursor)
        next_task_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        next_task_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 30);
                color: #4CAF50;
                border: 1px solid rgba(76, 175, 80, 50);
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 13px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(76, 175, 80, 50);
                border: 1px solid #4CAF50;
            }
            QPushButton:pressed {
                background-color: rgba(76, 175, 80, 70);
            }
        """)
        next_task_btn.clicked.connect(self._on_next_task_clicked)
        layout.addWidget(next_task_btn)

    def _on_stage_button_clicked(self, message):
        """处理阶段切换按钮点击"""
        # 作为文本内容提交
        content_parts = [{
            "type": "text",
            "text": message
        }]
        self.feedback_submitted.emit(content_parts, [])
        # 关闭窗口（如果有父窗口）
        if self.parent() and hasattr(self.parent(), 'close'):
            self.parent().close()

    def _load_deep_thinking_mode(self) -> bool:
        """从设置中加载深度思考模式状态"""
        from PySide6.QtCore import QSettings
        
        # 优先尝试加载项目级设置
        if self.project_path:
            project_settings_file = os.path.join(self.project_path, '.feedback_settings.json')
            if os.path.exists(project_settings_file):
                try:
                    with open(project_settings_file, 'r') as f:
                        settings = json.load(f)
                        return settings.get('deep_thinking_mode', False)
                except Exception:
                    pass  # 如果读取失败，使用全局设置
        
        # 使用全局QSettings
        settings = QSettings("FeedbackUI", "ChatTab")
        return settings.value("deep_thinking_mode", False, type=bool)
    
    def _save_deep_thinking_mode(self, enabled: bool):
        """保存深度思考模式状态到设置"""
        from PySide6.QtCore import QSettings
        
        # 保存到项目级设置（如果有项目路径）
        if self.project_path:
            project_settings_file = os.path.join(self.project_path, '.feedback_settings.json')
            settings = {}
            
            # 读取现有设置
            if os.path.exists(project_settings_file):
                try:
                    with open(project_settings_file, 'r') as f:
                        settings = json.load(f)
                except Exception:
                    settings = {}
            
            # 更新深度思考模式设置
            settings['deep_thinking_mode'] = enabled
            
            # 保存回文件
            try:
                with open(project_settings_file, 'w') as f:
                    json.dump(settings, f, indent=2)
            except Exception:
                pass  # 如果保存失败，至少保存到全局设置
        
        # 同时保存到全局QSettings
        settings = QSettings("FeedbackUI", "ChatTab")
        settings.setValue("deep_thinking_mode", enabled)
    
    def get_history_file_path(self) -> str:
        """获取历史记录文件路径"""
        if self.project_path:
            return os.path.join(self.project_path, '.agent', 'chat_history.json')
        else:
            # 如果没有项目路径，使用脚本目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(script_dir, '..', 'chat_history.json')
    
    def save_to_history(self, content: str, message_type: str = 'sent', ai_response: str = None) -> bool:
        """保存内容到历史记录

        Args:
            content: 要保存的内容
            message_type: 消息类型 ('sent' 或 'received')
            ai_response: AI的回复内容（如果有）

        Returns:
            bool: 保存是否成功
        """
        if not content.strip() and not ai_response:
            return False

        try:
            # 获取历史记录文件路径
            history_file = self.get_history_file_path()

            # 读取现有历史记录
            history = self.load_history_from_file()

            # 创建对话记录
            new_record = {
                'type': 'dialogue',  # 标记为对话类型
                'timestamp': datetime.now().isoformat(),
                'time_display': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'messages': []
            }

            # 添加用户消息
            if content.strip():
                new_record['messages'].append({
                    'role': 'user',
                    'content': content.strip(),
                    'time': datetime.now().strftime('%H:%M:%S')
                })

            # 添加AI回复（如果有）
            if ai_response:
                new_record['messages'].append({
                    'role': 'assistant',
                    'content': ai_response.strip(),
                    'time': datetime.now().strftime('%H:%M:%S')
                })

            history.append(new_record)

            # 只保留最新的记录
            history = history[-self.max_history_records:]

            # 保存到文件
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)

            return True

        except Exception:
            # 静默处理保存失败，不影响主流程
            return False

    def save_response_to_history(self, response: str) -> bool:
        """保存AI回复到当前对话历史

        Args:
            response: AI的回复内容

        Returns:
            bool: 保存是否成功
        """
        if not response.strip():
            return False

        try:
            # 获取历史记录文件路径
            history_file = self.get_history_file_path()

            # 读取现有历史记录
            history = self.load_history_from_file()

            if history and history[-1].get('type') == 'dialogue':
                # 在最后一个对话记录中添加AI回复
                history[-1]['messages'].append({
                    'role': 'assistant',
                    'content': response.strip(),
                    'time': datetime.now().strftime('%H:%M:%S')
                })
            else:
                # 创建新的对话记录（仅包含AI回复）
                new_record = {
                    'type': 'dialogue',
                    'timestamp': datetime.now().isoformat(),
                    'time_display': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'messages': [{
                        'role': 'assistant',
                        'content': response.strip(),
                        'time': datetime.now().strftime('%H:%M:%S')
                    }]
                }
                history.append(new_record)

            # 只保留最新的记录
            history = history[-self.max_history_records:]

            # 保存到文件
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)

            return True

        except Exception:
            # 静默处理保存失败，不影响主流程
            return False
    
    def load_history_from_file(self) -> List[Dict]:
        """从文件加载历史记录"""
        try:
            history_file = self.get_history_file_path()

            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    if isinstance(history, list):
                        # 兼容旧格式：将旧格式转换为新的对话格式
                        converted_history = []
                        for record in history:
                            if 'type' not in record:  # 旧格式
                                converted_record = {
                                    'type': 'dialogue',
                                    'timestamp': record.get('timestamp', ''),
                                    'time_display': record.get('time_display', ''),
                                    'messages': [{
                                        'role': 'user',
                                        'content': record.get('content', ''),
                                        'time': record.get('time_display', '').split(' ')[-1] if 'time_display' in record else ''
                                    }]
                                }
                                converted_history.append(converted_record)
                            else:
                                converted_history.append(record)
                        return converted_history
                    return []
            return []
        except Exception:
            # 静默处理加载失败，不影响主流程
            return []
    
    def get_recent_history(self, count: Optional[int] = None) -> List[Dict]:
        """获取最近的历史记录
        
        Args:
            count: 获取记录数量，默认为最大记录数
            
        Returns:
            List[Dict]: 历史记录列表
        """
        history = self.load_history_from_file()
        if count is None:
            count = self.max_history_records
        return history[-count:]
    
    def save_input_to_history(self):
        """保存输入框内容到历史记录（用于超时时自动保存）"""
        if not self.feedback_text:
            return

        # 获取输入框中的文本内容
        text_content = self.feedback_text.toPlainText().strip()

        # 如果有内容，则保存到历史记录
        if text_content:
            self.save_to_history(text_content, 'sent')
    
    def clear_feedback(self):
        """清空反馈内容"""
        if self.feedback_text:
            self.feedback_text.clear()
            if hasattr(self.feedback_text, 'clear_images'):
                self.feedback_text.clear_images()
        
        # 清空选项
        for checkbox in self.option_checkboxes:
            checkbox.setChecked(False)
        
        # 清空选中的指令
        self._clear_selected_command() 

    def _edit_selected_command(self):
        """编辑选中的指令"""
        if not self.selected_command:
            return
            
        # 导入编辑对话框
        try:
            from ..add_command_dialog import EditCommandDialog
        except ImportError:
            try:
                from add_command_dialog import EditCommandDialog
            except ImportError:
                QMessageBox.warning(self, "功能不可用", "编辑功能暂时不可用")
                return
        
        # 构造指令数据
        command_data = {
            'title': self.selected_command['title'],
            'content': self.selected_command['content'],
            'type': self.selected_command['type'],
            'full_path': ''  # 需要根据指令类型和标题查找文件路径
        }
        
        # 查找指令文件路径
        command_data['full_path'] = self._find_command_file_path(command_data)
        
        if not command_data['full_path']:
            QMessageBox.warning(self, "编辑失败", "无法找到指令文件")
            return
        
        # 打开编辑对话框
        try:
            dialog = EditCommandDialog(self.project_path, command_data, self)
            if dialog.exec():
                # 编辑成功，清除当前选中的指令标签
                self._clear_selected_command()
                QMessageBox.information(self, "编辑成功", "指令已更新")
        except Exception as e:
            QMessageBox.critical(self, "编辑失败", f"编辑指令时发生错误: {str(e)}")
    
    def _find_command_file_path(self, command_data):
        """查找指令文件路径"""
        import os
        
        title = command_data['title']
        if title.endswith('.mdc'):
            title = title[:-4]
        
        # 根据指令类型确定搜索目录
        if command_data['type'] == 'project':
            search_dirs = [
                os.path.join(self.project_path, "_agent-local", "prompts"),
                os.path.join(self.project_path, ".cursor", "rules")
            ]
        elif command_data['type'] == 'personal':
            search_dirs = [
                os.path.join(self.project_path, "prompts")
            ]
        else:  # system
            search_dirs = [
                os.path.join(self.project_path, "src-min")
            ]
        
        # 在各个目录中搜索文件
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue

            # 尝试不同的文件扩展名
            for ext in ['.mdc', '.md', '.txt']:
                file_path = os.path.join(search_dir, f"{title}{ext}")
                if os.path.exists(file_path):
                    return file_path

        return None

    def _load_task_info(self):
        """加载任务信息"""
        if not self.session_id:
            return

        try:
            if not self.project_path:
                return

            # 构建任务文件路径
            task_file = os.path.join(self.project_path, '.workspace', 'tasks', f'{self.session_id}.json')
            if not os.path.exists(task_file):
                return

            # 读取任务文件
            with open(task_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                tasks = data.get('tasks', [])

            # 查找当前任务（state == "in_progress"）
            for task in tasks:
                if task.get('state') == 'in_progress':
                    self.current_task = {
                        'id': task.get('id'),
                        'title': task.get('title', ''),
                        'state': task.get('state')
                    }
                    break

            # 查找下一个任务（state == "pending"）
            for task in tasks:
                if task.get('state') == 'pending':
                    self.next_task = {
                        'id': task.get('id'),
                        'title': task.get('title', ''),
                        'state': task.get('state')
                    }
                    break

        except Exception:
            # 静默处理加载失败，不影响主流程
            pass

    def _create_current_task_label(self, layout):
        """创建当前任务显示标签"""
        if not self.current_task:
            return

        task_title = self.current_task.get('title', '')
        task_label = QLabel(f"📌 当前任务: {task_title}")
        task_label.setWordWrap(True)
        task_label.setAlignment(Qt.AlignCenter)
        task_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #FF8C00;
                padding: 6px;
                background-color: rgba(255, 140, 0, 10);
                border: 1px solid rgba(255, 140, 0, 30);
                border-radius: 4px;
                margin: 5px 0px;
            }
        """)
        layout.addWidget(task_label)

    def _on_next_task_clicked(self):
        """处理下一任务按钮点击"""
        content_parts = [{
            "type": "text",
            "text": "请开始下一个任务"
        }]
        self.feedback_submitted.emit(content_parts, [])
        # 关闭窗口（如果有父窗口）
        if self.parent() and hasattr(self.parent(), 'close'):
            self.parent().close()