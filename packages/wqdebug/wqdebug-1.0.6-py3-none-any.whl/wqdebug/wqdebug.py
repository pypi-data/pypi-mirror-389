#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: wwdeng
import os
import sys
import argparse
import traceback
from .wq_gdb.wq_gdb import WqGdb
from .wq_log.wq_log import WqLog
from .offline_log.offline_log import OfflineLog
from . import __version__


def main():
    print(f"wq debug v:{__version__}")    
    print(sys.argv)
    try:
        parser = argparse.ArgumentParser(description=f"wq debug v:{__version__}")
        subparsers = parser.add_subparsers(dest="command", help="可用命令")
        
        # gdb子命令
        wq_gdb = WqGdb()            
        wq_gdb.add_argument(subparsers.add_parser(WqGdb.CMD, help=WqGdb.DESC))

        # log子命令
        wq_log = WqLog()
        wq_log.add_argument(subparsers.add_parser(WqLog.CMD, help=WqLog.DESC))

        # offline log子命令
        offline_Log = OfflineLog()
        offline_Log.add_argument(subparsers.add_parser(OfflineLog.CMD, help=OfflineLog.DESC))
        
        args = parser.parse_args()
        
        if args.command == "gdb":
            wq_gdb.run(args)
        elif args.command == WqLog.CMD:
            wq_log.run(args)
        elif args.command == OfflineLog.CMD:
            offline_Log.run(args)
        else:
            parser.print_help()
            
    except Exception as e:
        print(e)
        traceback.print_exc()
        input("请按下回车键退出...")

if __name__ == "__main__":
    main()