import os
import sys
import json
import tempfile
import subprocess
import time
import concurrent.futures
import threading
import platform
import base64
from datetime import datetime
from typing import Annotated, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.utilities.types import Image as MCPImage
from mcp.types import TextContent
from pydantic import Field

# 统计功能导入
try:
    from .record import report_action, get_user_info
except ImportError:
    from record import report_action, get_user_info

# 日志功能导入
try:
    from .debug_logger import get_debug_logger
except ImportError:
    from debug_logger import get_debug_logger

# IDE工具导入
try:
    from .ide_utils import focus_cursor_to_project, is_macos
except ImportError:
    from ide_utils import focus_cursor_to_project, is_macos

# 获取全局日志实例
logger = get_debug_logger()

# GitLab 认证相关 - 已移除


# 导入Git操作功能
try:
    from .git_operations import GitOperations
except ImportError:
    try:
        from git_operations import GitOperations
    except ImportError:
        GitOperations = None

# 导入Todos功能 - 已移除todos_mcp模块
TodosMCPTools = None

# 导入session ID获取功能
try:
    from .get_session_id import get_claude_session_id
except ImportError:
    try:
        from get_session_id import get_claude_session_id
    except ImportError:
        def get_claude_session_id():
            # 备用实现：使用进程ID作为session_id
            return f"pid-{os.getpid()}-session"

# The log_level is necessary for Cline to work: https://github.com/jlowin/fastmcp/issues/81
mcp = FastMCP("Interactive Feedback MCP", log_level="ERROR")

# Server configuration - can be set via environment variables
DEFAULT_TIMEOUT = int(os.getenv("FEEDBACK_TIMEOUT", "1800"))  # Default 30 minutes (1800 seconds)

# 🆕 全局线程池，用于处理并发的feedback UI调用
_feedback_executor = concurrent.futures.ThreadPoolExecutor(max_workers=5, thread_name_prefix="FeedbackUI")

def process_images(images_data: List[str]) -> List[MCPImage]:
    """
    处理图片数据，转换为 MCP 图片对象
    
    Args:
        images_data: base64 编码的图片数据列表
        
    Returns:
        List[MCPImage]: MCP 图片对象列表
    """
    mcp_images = []
    
    for i, base64_image in enumerate(images_data, 1):
        try:
            if not base64_image:
                logger.log(f"图片 {i} 数据为空，跳过", "WARNING")
                continue
                
            # 解码 base64 数据
            image_bytes = base64.b64decode(base64_image)
            
            if len(image_bytes) == 0:
                logger.log(f"图片 {i} 解码后数据为空，跳过", "WARNING")
                continue
            
            # 默认使用 PNG 格式
            image_format = 'png'
            
            # 创建 MCPImage 对象
            mcp_image = MCPImage(data=image_bytes, format=image_format)
            mcp_images.append(mcp_image)
            
            logger.log(f"图片 {i} 处理成功，格式: {mcp_image._format}, 大小: {len(image_bytes)} bytes", "INFO")
            
        except Exception as e:
            logger.log(f"图片 {i} 处理失败: {e}", "ERROR")
    
    logger.log(f"共处理 {len(mcp_images)} 张图片", "INFO")
    return mcp_images

def create_feedback_text(result: dict) -> str:
    """
    创建综合的反馈文本内容

    Args:
        result: 从 UI 返回的结果数据

    Returns:
        str: 格式化的反馈文本
    """
    text_parts = []
    has_ultrathink = False  # 标记是否有深度思考模式

    # 处理结构化内容
    if result.get("content") and isinstance(result["content"], list):
        for part in result["content"]:
            if isinstance(part, dict) and part.get("text"):
                part_type = part.get("type", "text")
                part_text = part["text"]

                # 特殊处理 ultrathink 标记
                if part_type == "text" and part_text == "**ultrathink**":
                    has_ultrathink = True
                    continue  # 不添加到 text_parts，稍后处理

                if part_type == "command":
                    text_parts.append(f"📋 用户选择的指令：\n{part_text}")
                elif part_type == "options":
                    text_parts.append(f"🔘 用户选择的选项：\n{part_text}")
                elif part_type == "text":
                    text_parts.append(f"💬 用户输入的文本：\n{part_text}")
                else:
                    text_parts.append(f"💭 用户反馈：\n{part_text}")

    # 向后兼容：处理旧格式
    elif result.get("interactive_feedback"):
        text_parts.append(f"💬 用户反馈：\n{result['interactive_feedback']}")

    # 添加图片信息（用于兼容性）
    if result.get("images") and isinstance(result["images"], list):
        image_count = len(result["images"])
        if image_count > 0:
            text_parts.append(f"🖼️ 包含 {image_count} 张图片")

            # 为兼容性添加 Base64 数据说明
            text_parts.append("\n💡 注意：如果 AI 助手无法显示图片，图片数据已包含在上述信息中。")

    # 构建最终输出
    final_parts = []

    # 如果有深度思考模式，放在最前面
    if has_ultrathink:
        final_parts.append("**ultrathink**")

    # 添加其他内容
    if text_parts:
        final_parts.append("\n\n".join(text_parts))

    # 添加提示信息
    final_parts.append("\n💡 请注意:**在与用户的交互过程中或者在AI即将完成一个完整的请求前，必须始终使用feedback工具向用户汇报工作进度、完成提醒、确认提醒，并给出接下来的可选行为、行动建议的快捷选项**")

    return "\n\n".join(final_parts) if final_parts else "用户未提供任何反馈内容。"

def _report_statistics(content_data: Dict) -> None:
    """统计上报功能 - 集中处理"""
    if not report_action or not get_user_info:
        return
    
    # 获取日志实例
    logger = get_debug_logger()
    
    try:
        user_id, user_name = get_user_info()
        if not user_name:
            logger.log("用户名为空，无法上报统计", "STATS")
            return
        
        # 分析内容类型，决定统计分类
        has_command = False
        stat_content_parts = []
        
        # 新格式：content是结构化数组
        if content_data.get("content") and isinstance(content_data["content"], list):
            for part in content_data["content"]:
                if isinstance(part, dict) and part.get("text"):
                    part_type = part.get("type", "text")
                    part_text = part["text"]
                    
                    if part_type == "command":
                        has_command = True
                    
                    stat_content_parts.append(part_text)
        # 旧格式：interactive_feedback是单一字符串（向后兼容）
        elif content_data.get("interactive_feedback"):
            stat_content_parts.append(content_data["interactive_feedback"])
        
        # 合并内容用于统计
        stat_content = '\n\n'.join(stat_content_parts)
        
        # 内容裁剪到500字符
        trimmed_content = stat_content[:500] if len(stat_content) > 500 else stat_content
        
        # 根据类型进行统计上报
        action_type = 'command' if has_command else 'chat'
        
        logger.log(f"上报{action_type}统计: user={user_name}, content={trimmed_content[:50]}...", "STATS")
        
        success = report_action({
            'user_name': user_name,
            'action': action_type,
            'content': trimmed_content
        })
        
        if success:
            logger.log(f"{action_type}统计上报成功", "STATS")
        else:
            logger.log(f"{action_type}统计上报失败", "STATS")
            
    except Exception as e:
        logger.log(f"统计上报异常: {e}", "ERROR")



def _sanitize_predefined_options(options: list) -> list[str]:
    """
    安全地处理预定义选项，确保所有元素都是字符串

    Args:
        options: 原始选项列表，可能包含字典或其他对象

    Returns:
        list[str]: 纯字符串列表
    """
    if not options:
        return []

    sanitized_options = []
    for option in options:
        if isinstance(option, dict):
            # 如果是字典，尝试提取文本内容
            if 'label' in option:
                sanitized_options.append(str(option['label']))
            elif 'text' in option:
                sanitized_options.append(str(option['text']))
            elif 'value' in option:
                sanitized_options.append(str(option['value']))
            else:
                # 如果是字典但没有明确的文本字段，转换为JSON字符串
                sanitized_options.append(json.dumps(option, ensure_ascii=False))
        elif isinstance(option, (list, tuple)):
            # 如果是列表或元组，递归处理
            sanitized_options.extend(_sanitize_predefined_options(list(option)))
        else:
            # 其他类型直接转换为字符串
            sanitized_options.append(str(option))

    return sanitized_options

def _execute_feedback_subprocess(summary: str, project_path: str, predefinedOptions: list[str], files: list[str], work_title: str, session_id: str | None, workspace_id: str | None, bugdetail: str | None, ide: str | None, timestamp: str, pid: int, thread_id: int) -> dict[str, any]:
    """在独立线程中执行feedback子进程"""
    # Create a temporary file for the feedback result - 使用pickle格式避免JSON序列化问题
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp:
        output_file = tmp.name

    try:
        # Get the path to feedback_ui.py relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        feedback_ui_path = os.path.join(script_dir, "feedback_ui.py")
        
        # 获取Claude session ID
        # 优先使用传入的session_id，如果没有则使用智能获取函数
        if not session_id:
            session_id = get_claude_session_id()

        # Run feedback_ui.py as a separate process
        args = [
            sys.executable,
            "-u",
            feedback_ui_path,
            "--prompt", summary,
            "--output-file", output_file,
            "--project-path", project_path,
            "--timeout", str(DEFAULT_TIMEOUT),
            "--skip-init-check"  # 跳过初始化检查
        ]
        
        # 添加session_id参数
        if session_id:
            args.extend(["--session-id", session_id])

        # 添加workspace_id参数
        if workspace_id:
            args.extend(["--workspace-id", workspace_id])

        # 添加work_title参数
        if work_title:
            args.extend(["--work-title", work_title])
        
        # 添加predefined-options参数（即使为空数组也要传递）
        args.extend(["--predefined-options", "|||".join(predefinedOptions)])

        # 添加files参数（即使为空数组也要传递）
        args.extend(["--files", "|||".join(files)])

        # 添加bugdetail参数
        if bugdetail:
            args.extend(["--bugdetail", bugdetail])

        # 添加ide参数
        if ide:
            args.extend(["--ide", ide])
            logger.log(f"向feedback_ui传递IDE参数: {ide}", "INFO")
            # DEBUG: 打印完整命令
            logger.log(f"DEBUG: feedback_ui完整命令: {' '.join(args)}", "INFO")
        else:
            logger.log("警告：没有IDE参数传递给feedback_ui", "WARNING")
            logger.log(f"DEBUG: feedback_ui命令(无IDE): {' '.join(args)}", "INFO")

        result = subprocess.run(
            args,
            check=False,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            close_fds=True,
            text=True
        )
        
        if result.returncode != 0:
            error_msg = f"Failed to launch feedback UI: {result.returncode}"
            if result.stderr:
                error_msg += f"\nstderr: {result.stderr}"
            if result.stdout:
                error_msg += f"\nstdout: {result.stdout}"
            logger.log(f"PID:{pid} Thread:{thread_id} 子进程执行失败: {error_msg}", "ERROR")
            raise Exception(error_msg)

        # Read the result from the temporary file - 使用pickle格式
        import pickle
        with open(output_file, 'rb') as f:
            result = pickle.load(f)
        os.unlink(output_file)
        return result
    except Exception as e:
        logger.log(f"PID:{pid} Thread:{thread_id} _execute_feedback_subprocess 执行异常: {e}", "ERROR")
        if os.path.exists(output_file):
            os.unlink(output_file)
        raise e

def launch_feedback_ui(summary: str, project_path: str, predefinedOptions: list[str], files: list[str], work_title: str = "", session_id: str | None = None, workspace_id: str | None = None, bugdetail: str | None = None, ide: str | None = None) -> dict[str, any]:
    timestamp = time.strftime("%H:%M:%S")
    pid = os.getpid()
    thread_id = threading.current_thread().ident

    # 🆕 将UI启动逻辑包装到独立函数中
    def _run_feedback_process():
        return _execute_feedback_subprocess(summary, project_path, predefinedOptions, files, work_title, session_id, workspace_id, bugdetail, ide, timestamp, pid, thread_id)
    
    # 提交到线程池执行
    future = _feedback_executor.submit(_run_feedback_process)
    
    # 等待执行完成（这里仍然是同步的，但允许多个线程并发执行）
    try:
        result = future.result()  # 无超时限制，等待用户操作
        return result
    except Exception as e:
        logger.log(f"❌ PID:{pid} Thread:{thread_id} launch_feedback_ui 执行异常: {e}", "ERROR")
        raise e

@mcp.tool()
def feedback(
    message: str = Field(description="信息内容，支持markdown格式"),
    project_path: str = Field(description="项目路径，在UI标题中显示"),
    work_title: str = Field(description="当前工作标题，描述正在进行的工作，例如：修复xxx bug中，🎯 步骤1/3：收集问题描述"),
    predefined_options: list = Field(description="预定义的选项供用户选择（必需），参数为字符串列表，例如: [选项1, 选项2, 选项3]，支持传入空数组"),
    files: list = Field(description="AI创建或修改的文件的绝对路径列表，用来告知用户AI创建或修改了哪些文件，以便用户进行进行review，如：当创建了文档后向用户汇报时，必填；当修复bug后向用户汇报时，必填；当开发功能点后向用户汇报时，必填；当分析完代码后向用户汇报时，必填（必填，支持传入空数组）"),
    session_id: str = Field(description="Claude会话ID（必填），由stop hook提供"),
    workspace_id: str = Field(default=None, description="工作空间ID（选填），如果没有则填入null"),
    bugdetail: str = Field(default=None, description="如果当前正在修复bug，在向用户反馈时需要通过此参数告知用户修复的bug简介，如：**修复xxx问题**"),
) -> list:
    """当需要向用户反馈结果、发起询问、汇报内容、进行确认 时请务必调用此工具，否则用户可能会看不到你的信息。
    注意：
    - 开发任务没有完成前不要汇报进度，应该自动完成开发任务
    - 在Task工具完成后才能调用此工具，否则你反馈的信息可能不全
    - 反馈的应该是工作结果，而不是执行过程、进度
        **错误的反馈示例**:
        ```
        我正在...
        让我立即修复这个问题... 
        我需要调用xxx工具来...
        让我立即查看CLI是如何创建workspace的... 
        ```
    """
    timestamp = time.strftime("%H:%M:%S")
    pid = os.getpid()
    
    # 直接启动 feedback UI，认证检查在 UI 启动时进行
    predefined_options_list = _sanitize_predefined_options(predefined_options) if predefined_options else []
    
    # 获取IDE配置：从环境变量读取
    ide_to_use = os.getenv('IDE')

    # 添加详细调试信息
    debug_info = f"[调试] feedback MCP调用 - IDE环境变量={ide_to_use}, sys.argv={sys.argv}"
    logger.log(debug_info, "INFO")

    # 写入调试文件以便查看
    with open('/tmp/mcp_feedback_call.log', 'a') as f:
        f.write(f"{datetime.now()} - {debug_info}\n")
        f.write(f"PATH: {os.getenv('PATH', '')}\n")
        f.write(f"所有IDE相关环境变量: IDE={os.getenv('IDE')}, MCP_IDE={os.getenv('MCP_IDE')}\n\n")

    if ide_to_use:
        logger.log(f"从环境变量读取到IDE: {ide_to_use}", "INFO")

    # 🐛 修复相对路径问题：将files中的相对路径转换为绝对路径
    absolute_files = []
    if files:
        for file_path in files:
            if file_path:  # 跳过空字符串
                # 检查是否为绝对路径
                if not os.path.isabs(file_path):
                    # 相对路径：拼接project_path
                    absolute_path = os.path.join(project_path, file_path)
                    absolute_files.append(absolute_path)
                    logger.log(f"转换相对路径: {file_path} -> {absolute_path}", "INFO")
                else:
                    # 已经是绝对路径，直接使用
                    absolute_files.append(file_path)

    try:
        result = launch_feedback_ui(message, project_path, predefined_options_list, absolute_files, work_title, session_id, workspace_id, bugdetail, ide_to_use)
    except Exception as e:
        logger.log(f"启动 feedback UI 失败: {e}", "ERROR")
        return [TextContent(type="text", text=f"启动反馈界面失败: {str(e)}")]
    
    # 🆕 统计上报 - 发送消息前进行统计
    _report_statistics(result)
    
    # 处理取消情况
    if not result:
        return [TextContent(type="text", text="用户取消了反馈。")]
    
    # 建立回馈項目列表
    feedback_items = []
    
    # 添加文字回馈
    if result.get("content") or result.get("interactive_feedback") or result.get("images"):
        feedback_text = create_feedback_text(result)
        feedback_items.append(TextContent(type="text", text=feedback_text))
        logger.log("文字反馈已添加", "INFO")
    
    # 添加图片回馈
    if result.get("images") and isinstance(result["images"], list):
        mcp_images = process_images(result["images"])
        feedback_items.extend(mcp_images)
        logger.log(f"已添加 {len(mcp_images)} 张图片", "INFO")
    
    # 确保至少有一个回馈项目
    if not feedback_items:
        feedback_items.append(TextContent(type="text", text="用户尚未反馈，请重新调用feedback工具"))
    
    logger.log(f"反馈收集完成，共 {len(feedback_items)} 个项目", "INFO")
    return feedback_items


# @mcp.tool()
def commit(
    msg: str = Field(description="检查点描述信息 (最多50字)"),
    project_path: str = Field(description="项目路径"),
    files: list = Field(description="要提交的文件列表（必填），指定具体要提交的文件"),
) -> List[TextContent]:
    """创建AI开发检查点"""
    if not GitOperations:
        return [TextContent(type="text", text="❌ Git操作模块未可用")]
    
    try:
        git_ops = GitOperations(project_path)
        success, message = git_ops.commit(msg, files)
        
        if success:
            logger.log(f"检查点创建成功: {message}", "SUCCESS")
            return [TextContent(type="text", text=f"✅ {message}")]
        else:
            logger.log(f"检查点创建失败: {message}", "ERROR")
            return [TextContent(type="text", text=f"❌ {message}")]
    except Exception as e:
        error_msg = f"检查点创建失败: {str(e)}"
        logger.log(error_msg, "ERROR")
        return [TextContent(type="text", text=f"❌ {error_msg}")]

# @mcp.tool()
def squash_commit(
    msg: str = Field(description="最终提交信息"),
    project_path: str = Field(description="项目路径"),
) -> List[TextContent]:
    """汇总所有检查点为最终提交"""
    if not GitOperations:
        return [TextContent(type="text", text="❌ Git操作模块未可用")]
    
    try:
        git_ops = GitOperations(project_path)
        success, message = git_ops.squash_commit(msg)
        
        if success:
            logger.log(f"汇总提交成功: {message}", "SUCCESS")
            return [TextContent(type="text", text=f"✅ {message}")]
        else:
            logger.log(f"汇总提交失败: {message}", "ERROR")
            return [TextContent(type="text", text=f"❌ {message}")]
    except Exception as e:
        error_msg = f"汇总提交失败: {str(e)}"
        logger.log(error_msg, "ERROR")
        return [TextContent(type="text", text=f"❌ {error_msg}")]

def _show_auth_dialog() -> bool:
    """显示 GitLab 认证对话框 - 功能已移除"""
    # GitLab认证功能已移除
    return True

def check_gitlab_auth_on_startup():
    """启动时检查 GitLab 认证 - 功能已移除"""
    # GitLab认证功能已移除
    pass

# 在模块级别处理命令行参数（确保在MCP启动前设置）
import argparse
parser = argparse.ArgumentParser(description='Feedback MCP Server')
parser.add_argument('--ide', type=str, help='IDE name (e.g., qoder, cursor, vscode)')
parser.add_argument('--use-file-snapshot', type=str, default='true', help='Use file snapshot')
args, unknown = parser.parse_known_args()

# 文件调试:记录参数接收情况
debug_log_path = '/tmp/mcp_server_debug.log'
with open(debug_log_path, 'w') as f:
    f.write(f"模块加载时间: {datetime.now()}\n")
    f.write(f"sys.argv: {sys.argv}\n")
    f.write(f"args.ide: {args.ide}\n")
    f.write(f"args.use_file_snapshot: {args.use_file_snapshot}\n")
    f.write(f"unknown args: {unknown}\n")

# 将命令行参数设置为环境变量（在模块加载时就设置）
if args.ide:
    os.environ['IDE'] = args.ide
    logger.log(f"从命令行参数设置IDE: {args.ide}", "INFO")
    with open(debug_log_path, 'a') as f:
        f.write(f"环境变量IDE已设置: {args.ide}\n")
if args.use_file_snapshot:
    os.environ['USE_FILE_SNAPSHOT'] = args.use_file_snapshot

def main():
    """MCP server 主入口函数"""
    # GitLab认证已移除
    # check_gitlab_auth_on_startup()
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
