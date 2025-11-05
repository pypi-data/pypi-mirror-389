#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: wwdeng
import os
import json
import re
import sys
import time
from . import wq_log_value_to_enum_string

class WqLogReplace:
    def __init__(self, log_file:str, elf_path:list=None, is_debug:bool=False):
        print(f"log_file:{log_file} elf_path:{elf_path}")
        self.is_debug = is_debug
        self.log_file = log_file
        self.cfg_file = os.path.join(os.path.dirname(__file__), "wq_log_cfg.json")
        self.dict_file = os.path.join(os.path.dirname(__file__), "wq_log_dict_default.json")
        self.dict_file_gen = os.path.join(os.path.dirname(__file__), "wq_log_dict_gen.json")
        self.cfg = {}
        self.dict = {}  
        # 预编译的正则表达式
        self.compiled_patterns = []

        if os.path.exists(self.dict_file_gen) and elf_path is None:
            self.dict_file = self.dict_file_gen
        print(f"dict_file:{self.dict_file}")
        with open(self.cfg_file, "r", encoding="utf-8") as f:
            self.cfg = json.load(f)
        with open(self.dict_file, "r", encoding="utf-8") as f:
            self.dict = json.load(f)
        if elf_path is not None:
            for elf in elf_path:
                t = time.time()
                value = wq_log_value_to_enum_string.extract_from_elf(elf, list(self.dict.keys()))
                print(f"extract_from_elf time:{time.time() - t} s")
                if value is not None:
                    self.dict.update(value)
            with open(os.path.join(os.path.dirname(__file__), "wq_log_dict_gen.json"), "w", encoding="utf-8") as f:
                json.dump(self.dict, f, ensure_ascii=False, indent=4)
        
        # 预编译正则表达式
        self._compile_patterns()
        
        self._print(self.cfg)
        self._print(self.dict)
    
    def _compile_patterns(self):
        """预编译正则表达式规则"""
        for rule in self.cfg["regex_replace"]:
            pattern = rule[0]
            types = rule[1]
            compiled_pattern = re.compile(pattern)
            self.compiled_patterns.append((compiled_pattern, types))
    
    def _print(self, msg):
        if self.is_debug:
            print(msg)

    def _print_progress(self, current, total, prefix="处理进度"):
        """打印进度条"""
        if not self.is_debug:
            bar_length = 50
            filled_length = int(round(bar_length * current / float(total)))
            percents = round(100.0 * current / float(total), 1)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            sys.stdout.write(f'\r{prefix}: [{bar}] {percents}% ({current}/{total})')
            sys.stdout.flush()
            if current == total:
                print()  # 换行

    def _process_line(self, line):
        """处理单行日志，返回处理后的行"""
        for compiled_pattern, types in self.compiled_patterns:
            match = compiled_pattern.match(line)
            if match:
                groups = match.groups()
                new_line = line
                self._print(f"groups:{groups}")
                self._print(f"types:{types}")
                
                # 收集所有需要替换的位置和内容
                replacements = []
                
                for idx, type_name in enumerate(types):
                    if idx < len(groups):
                        value = groups[idx]
                        # 查找字典解释
                        explain = self.dict[type_name].get(value)
                        self._print(explain)
                        if explain:
                            group_start = match.start(idx + 1)  # 捕获组从1开始
                            group_end = match.end(idx + 1)
                            
                            # 记录替换信息
                            replacements.append((group_start, group_end, f'{value}({explain})'))
                        else:
                            self._print(f"not found {value} in {self.dict[type_name]}")
                
                # 从后往前替换，避免位置偏移
                replacements.sort(key=lambda x: x[0], reverse=True)
                for start, end, replacement in replacements:
                    new_line = new_line[:start] + replacement + new_line[end:]
                
                self._print(new_line)
                return new_line
        return line

    def parse(self):
        if self.log_file is None:
            return ""
        
        # 记录开始时间
        start_time = time.time()
        
        # 首先计算总行数用于进度显示
        with open(self.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        print(f"开始处理日志文件，共 {total_lines} 行")
        
        # 使用列表收集结果，避免字符串拼接
        result_lines = []
        
        for i, line in enumerate(lines, 1):
            # 显示进度条
            self._print_progress(i, total_lines, "处理日志")
            
            self._print(line)
            # 处理当前行
            processed_line = self._process_line(line)
            result_lines.append(processed_line)
        
        # 使用join连接所有行，比字符串拼接更高效
        log_data = ''.join(result_lines)
        
        # 记录结束时间并计算耗时
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 格式化耗时显示
        if elapsed_time < 1:
            time_str = f"{elapsed_time * 1000:.1f} 毫秒"
        elif elapsed_time < 60:
            time_str = f"{elapsed_time:.2f} 秒"
        else:
            minutes = int(elapsed_time // 60)
            seconds = elapsed_time % 60
            time_str = f"{minutes} 分 {seconds:.2f} 秒"
        
        # 计算处理速度
        lines_per_second = total_lines / elapsed_time if elapsed_time > 0 else 0
        
        print(f"日志处理完成！")
        print(f"处理耗时: {time_str}")
        print(f"处理速度: {lines_per_second:.1f} 行/秒")
        
        return log_data 