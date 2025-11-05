#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime


def curent_time(format='%Y-%m-%d %H:%M:%S %f'):
    return datetime.datetime.now().strftime(format)[:-3]

def getPrevNumber(num: int, param_max=0xFFF >> 2) -> int:
    if num < 0 or num > param_max:
        raise Exception('value is invalidd, must less than max')
    if num == 0:
        return param_max
    return num-1


def getNextNumber(num: int, param_max=0xFFF >> 2) -> int:
    if num < 0 or num > param_max:
        raise Exception('value is invalidd, must less than max')
    if num == param_max:
        return 0
    return num + 1


def getRangeNumber(num: int, prevNum: int, param_max=0xFFF >> 2) -> list:
    result = []
    if num < 0 or num > param_max:
        raise Exception('value is invalidd,must less than max')
    if prevNum < 0 or prevNum > param_max:
        raise Exception('prevNum is invalidd,must less than max')
    if num == prevNum:
        return result
    nextNum = prevNum
    while True:
        nextNum = getNextNumber(nextNum, param_max)
        if num == nextNum:
            break
        result.append(nextNum)
    return result
