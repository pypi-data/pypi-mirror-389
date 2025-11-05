#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
from wquart import message_new 
from wquart import log 
import sys
import os
from wquart.btsnoop import BTSnoop
from wquart.decode_new import UartDecode
console_logger=log.getconsolelogger(__name__)
btsnoop = BTSnoop()
coremap = {0:'A',1:'B',2:'D'}
def current_time(format='%Y-%m-%d %H:%M:%S,%f'):
    return datetime.datetime.now().strftime(format)[:-3]
def writelog(message=''):
    print(message.strip())
pos= 2450*50
end =  3040*50
def onmessage(msg):
    tp=msg.msgtype
    if(tp==1 or tp==2 or tp==5):#stream raw
        timespan=msg.timespan
        txt= msg.get_string()
        writelog(f'{current_time()} [{round(timespan/31.25,1)}] [{coremap[msg.coreid]}-{msg.seqid}]> {txt}')
        if(round(timespan/31.25,1)  == 754842.7):
            print(f'pos error start={pos}')
        elif round(timespan/31.25,1) == 758663.6:
            print(f'pos error end ={pos}')
    elif tp==0x10:#string
        txt=msg.get_string()
        writelog(f'{current_time()} > {txt}')
    elif tp==6:#hci log
        btsnoop.addRecord(msg.payload)
    elif tp ==4:#audio dump
        pass
def onstop():
    print('{1} {0}'.format("uart port is closed",datetime.datetime.now().strftime('%Y-%d-%m %H:%M:%S,%f')[:-3]))
if __name__ == "__main__":
    logdict = r"tws-ei-7035AX-B-1.0.0.0.wpk"
    binfile = r"L_703_8380416_8380416_2025-07-02-14-13-20.bin"
    decoder = UartDecode()
    decoder.load(logdict)
    with open(binfile,'rb') as fread:
        try:
            size = os.path.getsize(binfile)
            fread.seek(pos)
            while pos <= size:
                rdata = fread.read(1)
                decoder.get_result(rdata, onmessage)
                pos +=1
                if pos >= end:
                    break
        except Exception as e:
            print(f'exception={e},pos={pos}')
    print(f'main end')
    
        




    