#!/usr/bin/python
# -*- coding: utf-8 -*-
from enum import Enum
import logging
from logging import handlers
import os
from typing import Optional

from .utility import curent_time

level_relations = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}


def getconsolelogger(name, param_format='%(message)s', level=logging.INFO):
    """
    Return a console logger with the specified name, creating it if necessary.

    If no name is specified, return the root logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    console = logging.StreamHandler()
    logger.addHandler(console)
    formatter = logging.Formatter(param_format)
    console.setFormatter(formatter)
    return logger


def getfilelogger(name, file, param_format='%(message)s', level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    garder = os.path.dirname(file)
    if not os.path.exists(garder):
        os.makedirs(garder)
    filehandle = logging.FileHandler(file)
    logger.addHandler(filehandle)
    formatter = logging.Formatter(param_format)
    filehandle.setFormatter(formatter)
    return logger


def getthfilelogger(name, file, log_format='%(message)s', level="info", when="D", interval=1, back_count=1000):
    logger = logging.getLogger(name)
    logger.setLevel(level_relations.get(level))
    th = handlers.TimedRotatingFileHandler(filename=file,
                                           when=when,
                                           backupCount=back_count,
                                           interval=interval,
                                           encoding="utf-8")
    logger.addHandler(th)
    formatter = logging.Formatter(log_format)
    th.setFormatter(formatter)
    return logger


def getbuflogger(name, file, log_format='%(message)s', level="info", log_mode="a", log_max_bytes=1024000, bk_count=100):
    logger = logging.getLogger(name)
    logger.setLevel(level_relations.get(level))
    th = handlers.RotatingFileHandler(filename=file,
                                      mode=log_mode,
                                      maxBytes=log_max_bytes,
                                      backupCount=bk_count,
                                      encoding="utf-8",
                                      delay=False)
    logger.addHandler(th)
    formatter = logging.Formatter(log_format)
    th.setFormatter(formatter)
    return logger


def logshutdown():
    logging.shutdown()


def close(log: logging.Logger):
    for h in log.handlers:
        if h:
            try:
                h.acquire()
                h.flush()
                h.close()
            except (OSError, ValueError):
                # Ignore errors which might be caused
                # because handlers have been closed but
                # references to them are still around at
                # application exit.
                pass
            finally:
                h.release()
   
RESET = "\033[0m"  # 重置颜色
class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    WARNING = 3
    CRITICAL = 4
    NONE = 5
color_map ={
    LogLevel.DEBUG:"\033[90m" ,
    LogLevel.INFO:"\033[36m" ,
    LogLevel.WARNING:'\033[38;5;214m',
    LogLevel.CRITICAL:"\033[38;2;255;99;71m",
}
class ILogger:
    def __init__(self):
        self.logger:Optional[logging.Logger] = None
        self.loglevel = LogLevel.INFO
    def _logger_inner(self,level:LogLevel,msg:str):
        if  not self.logger:
            print(f'{color_map[level]} >{curent_time()} - {level.name}: {msg} {RESET}')
            return
        if level == LogLevel.DEBUG:
            self.logger.debug(msg)
        elif level == LogLevel.INFO:
            self.logger.info(msg)
        elif level == LogLevel.WARNING:
            self.logger.warning(msg)
        elif level == LogLevel.CRITICAL:
            self.logger.critical(msg)
    def logger_debug(self, msg:any):
        if  self.loglevel.value > LogLevel.DEBUG.value:
            return
        self._logger_inner(LogLevel.DEBUG,f'{msg}')
    def D(self,msg:any):
        self.logger_debug(msg)
    def logger_info(self, msg:any):
        if  self.loglevel.value > LogLevel.INFO.value:
            return
        self._logger_inner(LogLevel.INFO,f'{msg}')
    def I(self,msg:any):
        self.logger_info(msg)
    def logger_warning(self, msg:any):
        if  self.loglevel.value > LogLevel.WARNING.value:
            return
        self._logger_inner(LogLevel.WARNING,f'{msg}')
    def W(self,msg:any):
        self.logger_warning(msg)
    def logger_critical(self, msg:any):
        if  self.loglevel.value > LogLevel.CRITICAL.value:
            return
        self._logger_inner(LogLevel.CRITICAL,f'{msg}')
    def E(self,msg:any):
        self.logger_critical(msg)
Log = ILogger()
Log.loglevel = LogLevel.NONE
# Log.D('log DEBUG')
# Log.I('log INFO')
# Log.W('log WARNING')
# Log.E('log CRITICAL')
