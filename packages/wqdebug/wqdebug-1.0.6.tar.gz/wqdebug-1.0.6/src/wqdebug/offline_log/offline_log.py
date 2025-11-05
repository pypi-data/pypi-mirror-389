"""
离线日志解析模块

该模块提供离线日志文件的解析功能，支持单个文件和目录递归解析。
解析后的日志会保存为.log文件，并保持原始的时间戳和格式信息。
"""

import os
import datetime
from typing import Optional, TextIO, Any
from .wquart.decode_new import UartDecode
# from wquart.decode import UartDecode


import colorama
from colorama import Fore, Style
# 初始化colorama
colorama.init(autoreset=True)


class OfflineLog:
    """离线日志解析器

    负责解析离线日志文件，支持单个文件和目录递归解析。
    输出文件保存为.log格式，包含时间戳、核心信息和消息内容。
    """

    # 类常量
    CMD = "offline"
    DESC = "离线日志解析"
    CORE_MAP = {0: 'A', 1: 'B', 2: 'D'}
    SUPPORTED_EXTENSIONS = ('.bin', '.txt')
    DEFAULT_OUTPUT_SUBDIR = "out"
    TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

    def __init__(self) -> None:
        """初始化离线日志解析器"""
        self._output_file: Optional[TextIO] = None
        self._output_dir: Optional[str] = None
        self._decoder: Optional[UartDecode] = None

    def _colorize(self, text: str, color: str = "GREEN") -> str:
        """使用colorama为文本添加颜色

        Args:
            text: 要着色的文本
            color: colorama颜色名称 (GREEN, RED, YELLOW, BLUE, MAGENTA, CYAN, WHITE)

        Returns:
            着色后的文本
        """
        # 映射颜色名称到colorama常量
        color_map = {
            "GREEN": Fore.GREEN,
            "RED": Fore.RED,
            "YELLOW": Fore.YELLOW,
            "BLUE": Fore.BLUE,
            "MAGENTA": Fore.MAGENTA,
            "CYAN": Fore.CYAN,
            "WHITE": Fore.WHITE,
        }

        color_code = color_map.get(color.upper(), Fore.GREEN)
        return f"{color_code}{text}{Style.RESET_ALL}"

    def add_argument(self, parser: Any) -> None:
        """添加命令行参数

        Args:
            parser: 参数解析器对象
        """
        parser.add_argument(
            "-l", "--log",
            help="日志文件或目录路径",
            type=str,
            default="",
        )

        parser.add_argument(
            "-w", "--wpk",
            help="WUQI WPK文件路径",
            type=str,
            default=None,
        )

        parser.add_argument(
            "-o", "--output",
            help=f"输出目录路径 (默认: 输入文件目录/{self.DEFAULT_OUTPUT_SUBDIR})",
            type=str,
            default=None,
        )

    def run(self, args: Any) -> None:
        """运行离线日志解析

        Args:
            args: 命令行参数对象
        """
        print(f"解析离线日志文件: {args.log} {args.wpk} {args.output}")

        # 获取并验证输入路径
        input_path = self._get_input_path(args.log)
        if not input_path:
            return

        # 获取并验证WPK文件路径
        wpk_path = self._get_wpk_path(args.wpk)
        if not wpk_path:
            return

        # 设置输出目录
        if not self._setup_output_directory(input_path, args.output):
            return

        # 初始化解码器
        self._decoder = UartDecode()
        try:
            self._decoder.load(wpk_path)
        except Exception as e:
            print(f"错误: 加载WPK文件失败: {e}")
            return

        # 处理输入路径
        if os.path.isfile(input_path):
            self._process_single_file(input_path)
        elif os.path.isdir(input_path):
            self._process_directory(input_path)
        else:
            print(f"错误: 无效的日志路径: {input_path}")

    def _get_input_path(self, log_path: str) -> Optional[str]:
        """获取并验证输入路径

        Args:
            log_path: 命令行指定的日志路径

        Returns:
            验证后的输入路径，如果验证失败返回None
        """
        if not log_path:
            log_path = input("请输入或拖入离线日志文件或目录路径: ").strip("'\"")

        if not os.path.exists(log_path):
            print(f"错误: 日志文件或目录不存在: {log_path}")
            return None

        return log_path

    def _get_wpk_path(self, wpk_path: Optional[str]) -> Optional[str]:
        """获取并验证WPK文件路径

        Args:
            wpk_path: 命令行指定的WPK文件路径

        Returns:
            验证后的WPK文件路径，如果验证失败返回None
        """
        if not wpk_path:
            wpk_path = input("请输入或拖入WUQI WPK文件路径: ").strip("'\"")

        if not os.path.isfile(wpk_path):
            print(f"错误: WPK文件不存在: {wpk_path}")
            return None

        return wpk_path

    def _setup_output_directory(self, input_path: str, output_dir: Optional[str]) -> bool:
        """设置输出目录

        Args:
            input_path: 输入文件或目录路径
            output_dir: 指定的输出目录路径

        Returns:
            设置成功返回True，失败返回False
        """
        if output_dir:
            self._output_dir = output_dir
            print(f"使用指定的输出目录: {self._output_dir}")
        else:
            default_output_dir = self._get_default_output_dir(input_path)
            user_input = input(f"请输入或拖入输出目录 (直接回车使用默认值 {default_output_dir}): ").strip("'\"")

            if user_input:
                self._output_dir = user_input
                print(f"使用用户指定的输出目录: {self._output_dir}")
            else:
                self._output_dir = default_output_dir
                print(f"使用默认输出目录: {self._output_dir}")
                os.makedirs(self._output_dir, exist_ok=True)

        return self._ensure_output_directory_exists()

    def _get_default_output_dir(self, input_path: str) -> str:
        """获取默认输出目录路径

        Args:
            input_path: 输入文件或目录路径

        Returns:
            默认输出目录路径
        """
        if os.path.isfile(input_path):
            input_dir = os.path.dirname(input_path)
            return os.path.join(input_dir, self.DEFAULT_OUTPUT_SUBDIR)
        else:
            return os.path.join(input_path, self.DEFAULT_OUTPUT_SUBDIR)

    def _ensure_output_directory_exists(self) -> bool:
        """确保输出目录存在

        Returns:
            目录存在或创建成功返回True，否则返回False
        """
        if not self._output_dir:
            return False

        if os.path.exists(self._output_dir):
            return True

        print(f"输出目录不存在: {self._output_dir}")
        choice = input("是否创建目录？(y/n): ").lower()

        if choice in ('y', 'yes', '是'):
            try:
                os.makedirs(self._output_dir, exist_ok=True)
                print(f"已创建输出目录: {self._output_dir}")
                return True
            except OSError as e:
                print(f"错误: 无法创建目录 {self._output_dir}: {e}")
                return False
        else:
            print(f"操作已取消，未创建目录。")
            return False

    def _process_single_file(self, filepath: str) -> None:
        """处理单个日志文件

        Args:
            filepath: 日志文件路径
        """
        print(f"读取文件: {filepath}")
        self._parse_log_file(filepath)

    def _process_directory(self, dirpath: str) -> None:
        """处理目录中的所有日志文件

        Args:
            dirpath: 目录路径
        """
        print(f"读取目录: {dirpath}")

        # 首先扫描所有符合条件的文件
        files_to_process = []
        for root, _, files in os.walk(dirpath):
            for filename in files:
                filepath = os.path.join(root, filename)
                if filepath.lower().endswith(self.SUPPORTED_EXTENSIONS):
                    files_to_process.append(filepath)

        total_files = len(files_to_process)
        if total_files == 0:
            print(f"在目录 {dirpath} 中未找到支持的可处理文件")
            return

        print(f"找到 {total_files} 个可处理的文件 (.bin, .txt)")
        print("开始处理文件...")

        # 逐个处理文件
        for current_index, filepath in enumerate(files_to_process, 1):
            rel_path = os.path.relpath(filepath, dirpath)  # 显示相对路径，更清晰
            # 使用颜色辅助方法显示进度
            progress_text = f"[{current_index}/{total_files}] 处理文件: {rel_path}"
            print(self._colorize(progress_text, "GREEN"))
            self._parse_log_file(filepath)

        print(f"目录处理完成！共处理了 {total_files} 个文件")

    def _parse_log_file(self, filepath: str) -> None:
        """解析单个日志文件

        Args:
            filepath: 日志文件路径
        """
        output_filepath = self._get_output_filepath(filepath)

        try:
            self._open_output_file(output_filepath)
            self._read_and_decode_file(filepath)
        except Exception as e:
            print(f"解析文件 {filepath} 时发生异常: {e}")
        finally:
            self._close_output_file(output_filepath)

    def _open_output_file(self, output_filepath: str) -> None:
        """打开输出文件

        Args:
            output_filepath: 输出文件路径
        """
        if self._output_file:
            self._output_file.close()

        self._output_file = open(output_filepath, 'w', encoding='utf-8')
        print(f"输出文件: {output_filepath}")

    def _read_and_decode_file(self, filepath: str) -> None:
        """读取并解码文件，显示进度条

        Args:
            filepath: 输入文件路径
        """
        if not self._decoder:
            raise RuntimeError("解码器未初始化")

        with open(filepath, "rb") as f:
            # 获取文件大小
            file_size = f.seek(0, 2)  # 移动到文件末尾
            f.seek(0)  # 移回文件开头

            if file_size == 0:
                print("文件为空，跳过处理")
                return

            # 计算每次读取的块大小（1%的数据）
            chunk_size = max(file_size // 100, 1024)  # 至少1KB，避免太小影响性能

            # 初始化进度条
            progress_bar = self._create_progress_bar(filepath, file_size)
            bytes_read = 0

            try:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    # 处理数据块
                    self._decoder.get_result(chunk, self._on_message)
                    bytes_read += len(chunk)

                    # 更新进度条
                    self._update_progress_bar(progress_bar, bytes_read, file_size)

            finally:
                # 确保进度条完成并换行
                self._finish_progress_bar(progress_bar)

    def _create_progress_bar(self, filepath: str, file_size: int) -> dict:
        """创建进度条

        Args:
            filepath: 文件路径
            file_size: 文件大小

        Returns:
            进度条信息字典
        """
        filename = os.path.basename(filepath)
        file_size_mb = file_size / (1024 * 1024)

        return {
            'filename': filename,
            'file_size': file_size,
            'file_size_mb': file_size_mb,
            'start_time': None,
            'last_update': 0
        }

    def _update_progress_bar(self, progress_bar: dict, bytes_read: int, total_bytes: int) -> None:
        """更新进度条显示

        Args:
            progress_bar: 进度条信息
            bytes_read: 已读取字节数
            total_bytes: 总字节数
        """
        # 计算进度百分比
        progress = (bytes_read / total_bytes) * 100

        # 只在进度变化时更新（避免过于频繁的更新）
        if progress - progress_bar['last_update'] < 1 and bytes_read < total_bytes:
            return

        progress_bar['last_update'] = progress

        # 创建进度条显示，已完成部分使用绿色
        bar_width = 50
        filled_width = int(bar_width * progress / 100)
        empty_width = bar_width - filled_width

        # 使用颜色辅助方法：绿色(92)用于已完成，白色(37)用于未完成
        filled_part = self._colorize('=' * filled_width, 'GREEN') if filled_width > 0 else ""
        empty_part = self._colorize('-' * empty_width, 'WHITE') if empty_width > 0 else ""
        bar = filled_part + empty_part

        # 计算已读取的大小
        bytes_read_mb = bytes_read / (1024 * 1024)

        # 显示进度条
        print(f"\r[{bar}] {progress:5.1f}% "
              f"({bytes_read_mb:6.2f}/{progress_bar['file_size_mb']:6.2f} MB)",
              end='', flush=True)

    def _finish_progress_bar(self, progress_bar: dict) -> None:
        """完成进度条显示

        Args:
            progress_bar: 进度条信息
        """
        filename = progress_bar['filename']
        file_size_mb = progress_bar['file_size_mb']

        # 使用颜色辅助方法显示绿色完成的进度条
        green_bar = self._colorize('=' * 50, '92')  # 绿色
        print(f"\r[{green_bar}] 100.00% "
              f"({file_size_mb:6.2f}/{file_size_mb:6.2f} MB) "
              f"DONE", flush=True)

    def _close_output_file(self, output_filepath: str) -> None:
        """关闭输出文件

        Args:
            output_filepath: 输出文件路径
        """
        if self._output_file:
            self._output_file.close()
            self._output_file = None
            print(f"完成解析文件: {output_filepath}")

    def _get_output_filepath(self, input_filepath: str) -> str:
        """生成输出文件路径

        Args:
            input_filepath: 输入文件路径

        Returns:
            输出文件路径
        """
        filename = os.path.basename(input_filepath)
        name_without_ext = os.path.splitext(filename)[0]
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        output_filename = f"{name_without_ext}-parsed-{timestamp}.log"

        if self._output_dir:
            return os.path.join(self._output_dir, output_filename)
        else:
            return output_filename

    def _on_message(self, msg: Any) -> None:
        """处理解码后的消息

        Args:
            msg: 解码后的消息对象
        """
        msg_type = msg.msgtype

        if msg_type in (1, 2, 5):  # stream raw
            self._handle_stream_message(msg)
        elif msg_type == 0x10:  # string
            self._handle_string_message(msg)
        elif msg_type == 6:  # hci log
            pass  # 暂不处理
        elif msg_type == 4:  # audio dump
            pass  # 暂不处理

    def _handle_stream_message(self, msg: Any) -> None:
        """处理流消息

        Args:
            msg: 流消息对象
        """
        timestamp = self._get_current_time()
        core_id = self.CORE_MAP.get(msg.coreid, '?')
        seq_id = msg.seqid
        timespan_ms = round(msg.timespan / 31.25, 1)
        text = msg.get_string()

        log_message = f"{timestamp} [{core_id}-{seq_id:<4}] [{timespan_ms}]>{text}"
        self._write_log(log_message)

    def _handle_string_message(self, msg: Any) -> None:
        """处理字符串消息

        Args:
            msg: 字符串消息对象
        """
        timestamp = self._get_current_time()
        text = msg.get_string()
        log_message = f"{timestamp} {text}"
        self._write_log(log_message)

    def _get_current_time(self, format_str: Optional[str] = None) -> str:
        """获取当前时间戳字符串

        Args:
            format_str: 时间格式字符串，默认使用类常量定义的格式

        Returns:
            格式化的时间戳字符串
        """
        if format_str is None:
            format_str = self.TIMESTAMP_FORMAT

        timestamp = datetime.datetime.now().strftime(format_str)
        # 只对默认格式截断毫秒数（保留两位毫秒）
        if format_str == self.TIMESTAMP_FORMAT:
            timestamp = timestamp[:-3]

        return timestamp

    def _write_log(self, message: str) -> None:
        """写入日志消息

        Args:
            message: 日志消息
        """
        formatted_message = message.strip()
        # print(formatted_message)

        if self._output_file:
            try:
                self._output_file.write(formatted_message + '\n')
                self._output_file.flush()
            except Exception as e:
                print(f"警告: 写入输出文件失败: {e}")

    # 保持向后兼容的公共方法
    @property
    def output_file(self) -> Optional[TextIO]:
        """输出文件对象（向后兼容）"""
        return self._output_file

    @property
    def output_dir(self) -> Optional[str]:
        """输出目录路径（向后兼容）"""
        return self._output_dir

    def current_time(self, format: str = "%Y-%m-%d %H:%M:%S.%f") -> str:
        """获取当前时间（向后兼容）"""
        return self._get_current_time(format)

    def writelog(self, message: str = "") -> None:
        """写入日志（向后兼容）"""
        self._write_log(message)

    def get_output_filepath(self, input_filepath: str) -> str:
        """获取输出文件路径（向后兼容）"""
        return self._get_output_filepath(input_filepath)

    def onmessage(self, msg: Any) -> None:
        """处理消息（向后兼容）"""
        self._on_message(msg)

    def parse_log_file(self, filepath: str, decoder: Any) -> None:
        """解析日志文件（向后兼容）"""
        self._decoder = decoder
        self._parse_log_file(filepath)

    def setup_output_directory(self, input_path: str, output_dir: Optional[str]) -> bool:
        """设置输出目录（向后兼容）"""
        return self._setup_output_directory(input_path, output_dir)

    @property
    def coremap(self) -> dict:
        """核心映射（向后兼容）"""
        return self.CORE_MAP
