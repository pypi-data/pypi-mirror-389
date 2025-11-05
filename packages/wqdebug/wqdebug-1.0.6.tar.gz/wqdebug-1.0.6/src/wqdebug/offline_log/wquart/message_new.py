#!/usr/bin/python
# -*- coding: utf-8 -*-

import copy
import logging
import os
from typing import BinaryIO, Dict, Union, Optional, Callable, Any

from .log import ILogger, Log, LogLevel

from   .btsnoop import BTSnoop
import serial
import threading
import struct
import datetime
import time
from .decode_new import AudioDumpData, LogBase, UartDecode, Ack, DumpData,StreamLog,RawLog,CliLog,StringLog,audio_header_len,audio_header_fmt,AudioDumpDataHeader
from .cli import CommandBase, AncDumpStartRequest
from .utility import curent_time, getPrevNumber,  getRangeNumber
from enum import Enum
class Request:
    def __init__(self, clicmd: CommandBase, resmsgid: int = -1):
        self.clicmd:CommandBase= clicmd
        self.event = threading.Event()
        self.result = b''
        self.resmsgid = resmsgid  # 匹配回应的msgid
        self.check = False
        self.cliresult = -1
    def wait(self, timeout=5.0):
        return self.event.wait(timeout)

    def reset(self):
        self.event.set()


class Response:
    def __init__(self):
        self.success = False
        self.msg = ''
        self.cliresult = -1
        self.cmd:Optional[CommandBase] = None  # CommnadBase
class BufferMemoryStream:
    def __init__(self) -> None:
        self.buffsize = 20*1024*1024
        self.readindex = 0
        self.writeindex = 0
        self.data = bytearray(self.buffsize)
    def write(self,data:bytes):
        count = len(data)
        if self.length + count > self.buffsize:
            raise Exception('buff fulled.')
        wp = self.writeindex % self.buffsize
        if wp+count>self.buffsize:
            self.data[wp:] = data[0:self.buffsize-wp]
            self.data[0:wp+count-self.buffsize] = data[self.buffsize-wp:]
        else:
            self.data[wp:wp+count] = data
        self.writeindex +=count
    def read(self,length:int=-1)->bytes:
        len = length if length!=-1 else self.length
        rp = self.readindex % self.buffsize
        result = b''
        if rp + len > self.buffsize:
            result += self.data[rp:]
            result += self.data[0:rp + len - self.buffsize]
        else:
            result += self.data[rp:rp + len]
        self.readindex+=len
        return result

    @property
    def length(self)->int:
        return self.writeindex - self.readindex
class WqUart(ILogger):
    def __init__(self,port: str ,baudrate: int = 2000000,**kwargs):
        self.port = port
        self.baudrate = baudrate
        self.readtimeout = 0.02
        self.writetimeout = 0.02
        self.decode:UartDecode = UartDecode()
        self.logger_bin_file_dir = 'logs'
        self.emptytime = 10
        self.onstop = None
        self.ondump : Optional[Callable[[Union[DumpData,AudioDumpData]], None]] = None
        self.onmessage = None
        self.on_exception = None
        self.on_unhandlehci= None
        self.logger:Optional[logging.Logger] = None
        self.writebin= False
        self.isdump_audio = False
        self.loglevel = LogLevel.NONE
        self.ischeckmiss = True
        self.writesnoop = False
        self.on_unhandlecli = None  # 处理未处理的cli
        #inner status field , don't change
        self._port:Optional[serial.Serial] = None
        self._task = None
        self._isstop = False
        self._buffstream = BufferMemoryStream()
        self._packages:Dict[int,DumpDataSort] = {}
        self._lock = threading.Lock()
        self._seqnum = 0
        self._requests:Dict[int,Request] = { } # k-v :seqnum:Request
        self._isdump = False
        self._fb:Optional[BinaryIO] = None
        self._logDictionary = {}
        self._btsnoop:Optional[BTSnoop] = None
        self._split_flag = False
        self.init(**kwargs)
    def init(self,**kwargs):
        for key,v in kwargs.items():
            # 兼容以前的写法
            if key == 'decode_obj' and isinstance(v, UartDecode):
                setattr(self, 'decode', v)
            if key == '__baudrate':
                setattr(self, 'baudrate', v)
            if key == '__readtimeout':
                setattr(self, 'readtimeout', v)
            if key == '__writetimeout':
                setattr(self, 'writetimeout', v)
            if not key.startswith('_'):
                setattr(self, key, v)
            self.logger_info(f'setattr key={key},v={v}')
    def inituart(self):
        if self._port is None:
            self._port = serial.Serial(self.port, self.baudrate)
            self._port.write_timeout = self.writetimeout
            self._port.timeout = self.readtimeout
            import platform
            os_name  = platform.system()
            if os_name.lower()=="windows":# ifsystem is linux ,do  nothing
                self._port.set_buffer_size(20*1024*1024)

    def open(self):
        self.inituart()
        if self._port and not self._port.is_open:
            self._port.open()
            self._port.dsrdtr = True

    def close(self):
        if self._port is not None and self._port.is_open:
            self._port.dsrdtr = False
            self._port.close()

    def load(self, file='dbglog_table.txt',romtable=''):
        self.decode.load(file,False,romtable)

    def init_logs(self):
        if (self.writebin or self.writesnoop) and self.logger_bin_file_dir:
            if not os.path.exists(self.logger_bin_file_dir):
                os.makedirs(self.logger_bin_file_dir)
        ct = curent_time('%Y-%m-%d-%H-%M-%S-%f')
        if self.writebin:
            binfile = os.path.join(self.logger_bin_file_dir, f'{ct}-{self.port}.bin')
            self._fb = open(binfile,'wb+')
        if self.writesnoop:
            cfafile = os.path.join(self.logger_bin_file_dir, f'{ct}-{self.port}.cfa')
            self._btsnoop = BTSnoop()
            self._btsnoop.createHeader(cfafile)
    def receive(self):
        flag = False
        lasttime = time.time()
        if self._port is None:
            return
        while not self._isstop:
            try:
                self.open()
                count = self._port.in_waiting
                if count > 0:
                    min_len= min(count,500)
                    rdata = self._port.read(min_len)
                    #print(f'wdata={rdata.hex()}')
                    self._buffstream.write(rdata)
                    if self._fb:
                        self._fb.write(rdata)
                    if flag:
                        cur = time.time()
                        if (cur - lasttime) > self.emptytime:
                            emptymsg = 'more than {0} seconds not read data'.format(cur - lasttime)
                            if self.onmessage:
                                self.onmessage(StringLog(emptymsg))
                    flag = False
                else:
                    time.sleep(0.001)
                    flag = True
                    lasttime = time.time()
            except BaseException as ex:
                print(ex)
                if self.on_exception:
                    self.on_exception(ex)
                time.sleep(0.001)
    def __del__(self):
        if self._fb:
            self._fb.close()
        if self.onstop:
            self.onstop()
    def handle(self, msg:LogBase):
        msgtype = msg.msgtype
        if isinstance(msg,CliLog):#msgtype == 3:  # cli
            Log.D(f'cli payload:{msg.payload.hex()},frag:{msg.frag}')
            if msg.header_check and msg.content_check:
                [moduleid, crc, msgid, value,cliresult, length,seqnum] = struct.unpack('<3H2B2H', msg.payload[2:14])
                autoack = value & 0b1
                tp = (value>>1) & 0b111 #
                self.logger_debug(f'receive cli response:moduleid={moduleid},msgid={msgid},seqnum={seqnum}({hex(seqnum)}),tp={tp},seqnum={seqnum},threadid={threading.get_ident()},data={msg.payload.hex()}')
                if self._split_flag:
                    reqs = list(self._requests.values())
                    if(len(reqs)==0):
                        return#没有请求
                    req = reqs[0] # 只有一个请求
                    req.result += msg.payload
                    if not msg.frag:
                        req.reset()
                        Log.I(f'cli split package notify event set')
                    return
                self._split_flag = msg.frag == 1
                if tp == 1:
                    if seqnum in self._requests:
                        req = self._requests[seqnum]
                        req.check =True
                        req.cliresult = cliresult
                        req.result += msg.payload
                        if not msg.frag:
                            req.reset()
                        self.logger_debug(f'notify event set ...')
                    else:
                        self.logger_debug(f'notify event set fail...')
                    return
                elif tp==2:
                    if self.on_unhandlehci:
                        self.on_unhandlehci(msg)
                    return
                if self.on_unhandlecli:
                    self.on_unhandlecli(msg)
                self.logger_warning(f'mismatch cli response:moduleid={moduleid}, msgid={msgid},seqnum={seqnum},type={tp}')
            else:
                self.logger_warning(f'receive cli response error:{msg.payload.hex()},hc={msg.header_check},cc={msg.content_check}')
        elif isinstance(msg,DumpData):#msgtype == 4:
            if self.ondump is None:
                return
            ack = Ack()
            ack.seq = msg.seqnum
            ack.tid = msg.tid
            ack.status = 1
            if not msg.header_check:
                return
            if msg.content_check:
                ack.status = 0
                self.sortdumpdata(msg,self.isdump_audio)
            wdata = ack.getbytes()
            if self.decode.ack and msg.ack and not self._isstop:
                self.write(wdata)
            if ack.status == 1:
                self.logger_debug('ack audio dump={0}'.format(wdata.hex()))

        elif isinstance(msg,(StreamLog,RawLog)):
            if msg.timespan < 0.5*32768:  # 重启过开启检测
                self.ischeckmiss = True
            if msgtype == 5:  # 出现异常 不检测
                self.ischeckmiss = False
            if msg.header_check:
                if msg.content_check:
                    if self.ischeckmiss:
                        self.checkmisslog(msg)
                    if self.onmessage:
                        self.onmessage(msg)
                    return
            self.logger_debug('stream or raw log error :{0}'.format(msg.getbytes().hex()))

        elif msgtype == 0x10:
            if 'WuQi - Second Bootloader' in msg.get_string():
                self._logDictionary.clear()
            if not self._isdump and self.onmessage:
                self.onmessage(msg)
        elif msgtype== 6:#hci log
            #print(msg.payload.hex())
            if self._btsnoop:
                self._btsnoop.addRecord(msg.payload)
        else:
            error = 'other msgtype error:{0},msgtype={1},payload={2}'.format(msg,msgtype,msg.payload.hex())
            if self.onmessage:
                self.onmessage(StringLog(error))
            self.logger_debug(error)

    def start(self, onmessage: Callable[..., Any]):
        self._isstop = False
        if onmessage:
            self.onmessage = onmessage
        self.init_logs()
        self.open()
        self._task = threading.Thread(target=self.receive, daemon=True)  # daemon = True退出进程，子线程自动退出
        self._task.start()
        self.ht = threading.Thread(target=self.handleth, daemon=True)  # daemon = True退出进程，子线程自动退出
        self.ht.start()
    def handleth(self):
        while not self._isstop:
            try:
                rdata = self._buffstream.read()
                if len(rdata) >0:
                    #print(f'rdata={rdata.hex()}')
                    self.decode.get_result(rdata, self.handle)
                    continue
                time.sleep(0.001)
            except BaseException as ex:
                print(ex)
                if self.on_exception:
                    self.on_exception(ex)
                time.sleep(0.001)
    def stop(self):
        if self._btsnoop:
            self._btsnoop.close()
        self._isstop = True
        self.close()

    def write(self, data:bytes):
        self._lock.acquire()
        if self._port is None or not self._port.is_open:
            return
        self._port.write(data)
        self._lock.release()

    def getnextid(self):
        seqid = self._seqnum
        self._seqnum += 1
        if self._seqnum > 0xFFFF:
            self._seqnum = 0
        return seqid
    def doRequest(self,
                   reqcmd: CommandBase,
                   timeout: float = 5.0,
                   maxResendCnt: int = 1,
                   resmsgid: int = -1) -> Response:
        return self.doRequsest(reqcmd,timeout,maxResendCnt,resmsgid)
    def doRequsest(self,
                   reqcmd: CommandBase,
                   timeout: float = 5.0,
                   maxResendCnt: int = 1,
                   resmsgid: int = -1) -> Response:
        self._requests.clear() # 只允许一个请求
        self._split_flag = False
        self._isdump = False
        self._isdump = isinstance(reqcmd, AncDumpStartRequest)
        self.logger_debug('IsAncDumpStartRequest={0}'.format(self._isdump))
        res = Response()
        retry = 0
        if maxResendCnt <= 0:
            maxResendCnt = 1
        reqcmd.seqnum = self.getnextid() #重传不自增
        while retry < maxResendCnt:
            #self.logger_debug(f'module id:{reqcmd.moduleid}, msg id:{reqcmd.msgid}, retry time:{retry},seqnum={reqcmd.seqnum}')
            req = Request(reqcmd, resmsgid)
            data = self.decode.getbytes(reqcmd.seqnum, reqcmd)  # reqcmd.getbytes()
            self._requests[reqcmd.seqnum] = req
            self.logger_debug(f'send cli request:moduleid={reqcmd.moduleid},msgid={reqcmd.msgid},seqnum={reqcmd.seqnum}({hex(reqcmd.seqnum)}),retry={retry},threadid={threading.get_ident()},data={data.hex()}')
            self.write(data)
            retry = retry + 1
             # 没有回复的请求
            if not reqcmd.hasresponse:
                res.success = True
                res.msg = 'the request suceess.'
                self.logger_debug(f'{res.msg}')
                return res
            suc = req.wait(timeout)
            res.success = suc and req.check
            res.cliresult =  req.cliresult
            if res.success and req.cliresult == 0:
                rescmd = reqcmd.getresponse()
                try:
                    rescmd.loadbytes(req.result)
                except Exception as ex:
                    self.logger_debug('exception:{0}'.format(ex))
                    self.logger_debug('error while receive module id: %d, msg id: %d' % (req.clicmd.moduleid, req.clicmd.msgid))
                    self.logger_debug('received raw data is %s' % req.result)
                    self.logger_debug('received data is %s' % rescmd.payload)
                    res.success = False
                    continue
                if not rescmd.check(req.clicmd):
                    res.success =False
                    res.msg =f'the request returned but check fail,response result={rescmd}.'
                    self.logger_critical(f'{res.msg}')
                    return res
                res.cmd=rescmd
                res.msg='the request suceess.'
                del self._requests[reqcmd.seqnum] #正确才删除
                return res
            elif req.cliresult !=-1:
                res.success =False
                res.msg =f'the request return error,result={req.cliresult}.'
                self.logger_critical(f'{res.msg}')
                return res
            else:
                res.msg = 'the request timeout.'
        return res
    def dump(self, ondump:  Callable[[Union[DumpData,AudioDumpData]], None]):
        self.ondump = ondump
        self._packages = {}

    def sortdumpdata(self, msg: DumpData,is_dump_audio =False):
        if msg.tid not in self._packages:
            self._packages[msg.tid] = DumpDataSort()
        self._packages[msg.tid].is_audio = is_dump_audio
        if self.ondump is None:
            return
        self._packages[msg.tid].sortdumpdata(msg, self.ondump)

    def cleardump(self):
        self._packages.clear()

    def checkmisslog(self, msg:Union[StreamLog,RawLog]):
        if msg.coreid != 255 and self.onmessage:
            if msg.coreid in self._logDictionary:
                lastseq = self._logDictionary[msg.coreid]
                if msg.timespan > 0.5*32768:
                    if getPrevNumber(msg.seqid) != lastseq:
                        #ls = ','.join([str(id) for id in getRangeNumber(msg.seqid, lastseq)])
                        misslog = f'[auto] miss log type={msg.msgtype},coreid={msg.coreid},seqid range({lastseq},{msg.seqid})...'
                        self.onmessage(StringLog(misslog))
            self._logDictionary[msg.coreid] = msg.seqid


class DumpDataSort:
    def __init__(self):
        self.tid = 0xFF
        self.lastnum = -1
        self._packages = {}
        self.audiodata :bytes = b''
        self.is_audio = False
        self.audio_seqid =-1
    def cleardump(self):
        self.lastnum = -1
        self._packages.clear()
        self.audiodata = b''
    def getnextid(self,curid:int,maxid:int=0xFFFF)->int:
        if curid==maxid:
            return 0
        return curid + 1
    def cachecache(self):

        pass
    def sortdumpdata(self, msg: DumpData, ondump: Callable[[Union[DumpData,AudioDumpData]], None]):
        maxseqnum = 0xFFFF  # if msg.version==0 else 0xFFFF>>4
        if self.lastnum == -1:
            self.handle_dumpdata(msg,ondump)
            self.lastnum = msg.seqnum
        else:
            #print(f'other1  data ,msg.seqnum = {msg.seqnum},self.lastnum={self.lastnum}')
            nextid  = self.getnextid(self.lastnum,maxseqnum)
            if not msg.ack and isinstance(msg, AudioDumpData): #ack 不需要排序,且需要补包
                self.handle_dumpdata(msg,ondump)
                self.lastnum = msg.seqnum
                return
            if msg.seqnum ==nextid:
                self.handle_dumpdata(msg,ondump)
                self.lastnum = msg.seqnum
                while True:
                    nextid  =self.getnextid(self.lastnum,maxseqnum)
                    if nextid in self._packages:
                        self.handle_dumpdata(self._packages[nextid],ondump)
                        del self._packages[nextid]
                        self.lastnum  =nextid
                        continue
                    break
            else:
                self._packages[msg.seqnum] = msg
    def handle_dumpdata(self, msg: DumpData, ondump: Callable[[Union[DumpData,AudioDumpData]], None]):
        if not self.is_audio:
            ondump(msg)
            return
        # if  self.audiodata[0:4] != bytes([0x55,0xAA,0x70,0x36]) and msg.payload[0:4] != bytes([0x55,0xAA,0x70,0x36]):
        #     return
        self.audiodata += msg.payload
        index = self.audiodata.find(bytes([0x55,0xAA,0x70,0x36]))
        if index >=0 and index + len(self.audiodata)>=audio_header_len:
            adk_audio  = AudioDumpDataHeader(self.audiodata[index:audio_header_len])
            if len(self.audiodata)>=adk_audio.length +index:
                dd = AudioDumpData()
                dd.loadbytes(self.audiodata[index:adk_audio.length])
                ## 制造丢包
                # if (dd.adk_audio.seqid+1) % 88 ==0:
                #     print(f'skip audio seqid={dd.adk_audio.seqid}')
                #     self.audiodata = self.audiodata[adk_audio.length:]
                #     return
                if self.audio_seqid !=-1 and dd.adk_audio.seqid !=  self.audio_seqid + 1:
                    fillValue = 1 << (dd.adk_audio.bitwide - 1)
                    fillBytes = fillValue.to_bytes(dd.adk_audio.bitwide // 8, 'little')
                    for i in range(1,dd.adk_audio.seqid - self.audio_seqid):
                        hd = copy.deepcopy(dd.adk_audio)
                        hd.seqid = self.audio_seqid + i
                        md = AudioDumpData(hd)
                        md.payload = dd.payload[0:audio_header_len] + fillBytes * ((dd.adk_audio.length - audio_header_len) // len(fillBytes))
                        ondump(md)
                        print(f'fill data seqid={hd.seqid}')
                ondump(dd)
                self.audio_seqid = dd.adk_audio.seqid
                self.audiodata = self.audiodata[index + adk_audio.length:]
