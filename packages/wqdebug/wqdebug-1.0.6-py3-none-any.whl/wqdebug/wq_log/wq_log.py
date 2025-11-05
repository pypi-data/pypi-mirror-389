#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: wwdeng
import os
import sys
import glob
from .wq_log_replace import WqLogReplace
from .. import common

class WqLog: 
    CMD = "log"
    DESC = "分析日志文件"   
    def __init__(self):
        self.log = ""
        self.elf = []
        self.output = ""
        self.debug = False

    def add_argument(self, parser):
        parser.add_argument(
            "-l",
            "--log",
            help="log file path",
            type=str,
            default="",
        )

        parser.add_argument(
            "-e",
            "--elf",
            help="elf file path(s), can specify multiple files separated by comma or space",
            nargs="+",
            type=str,
            default=None,
        )

        parser.add_argument(
            "-o",
            "--output",
            help="output file path",
            type=str,
            default=None,
        )

        parser.add_argument(
            "-d",
            "--debug",
            help="debug mode",
            action="store_true",
            default=False,
        )

    def run(self, args):
        if not os.path.isfile(args.log):
            self.log = common.select_log_file(args.log)
        else:
            self.log = args.log
        
        # 处理elf参数，支持多个文件
        if args.elf:
            self.elf = args.elf
            print(f"使用ELF文件: {self.elf}")
        else:
            self.elf = glob.glob("*.elf")
        
        self.debug = args.debug
        print(f"parse log file: {self.log}")
        wq_log_replace = WqLogReplace(self.log, self.elf, self.debug)
        log_data = wq_log_replace.parse()

        if args.output:
            output_path = args.output
        else:
            # 获取输入文件的目录和文件名
            input_dir = os.path.dirname(self.log)
            input_filename = os.path.basename(self.log)
            output_filename = f"wqlog_parsed_{input_filename}"
            output_path = os.path.join(input_dir, output_filename)
            
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(log_data)
        print(f"log replace done: {output_path}")
