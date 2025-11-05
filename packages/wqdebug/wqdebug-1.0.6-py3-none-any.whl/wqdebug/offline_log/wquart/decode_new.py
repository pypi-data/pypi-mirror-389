#!/usr/bin/python
# -*- coding: utf-8 -*-

from io import BufferedReader, TextIOWrapper
import os
import re
import struct
import time
from enum import Enum
from typing import Dict, List, Tuple, Union

from .log import Log
from .crc import *
from .cli import CommandBase
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class MsgType(Enum):
    Default = 0
    Stream = 1
    Raw = 2
    CLI = 3
    AudioDump = 4
    CoreDump = 5
    String = 0x10
    Max = 255


magicword = bytes([0xD0, 0xD2, 0xC5, 0xC2])


def check(data: bytes, crc32: int):
    """
    check header & payload with crc32
    """
    crc = binascii.crc32(data)
    return crc == crc32


def createCommand(seq: int, cmd: CommandBase) -> bytes:
    data = cmd.getbytes()
    header = struct.pack('<BHBBH', 0, len(data) + 12, 3, 4, seq)
    crc8 = binascii.crc8(header)
    hp = header + struct.pack('<B', crc8) + data
    crc32 = binascii.crc32(hp)
    return magicword + hp + struct.pack('<I', crc32)


# magicword   header payload CRC32(header + payload)
# 4           4()              4
class UartDecode:
    def __init__(self):
        self.magicword = magicword
        self.datatemp = b''
        self.ack = True
        self.decoder_type = 0
        self.cache =''
    @staticmethod
    def loadaddress(data:bytes,offset:int = 0,startWord="core_dbglog_start"):
        while (True):
            mds = f"{startWord}\r\n".encode()
            index = data.find(mds, offset)
            if index < 0:
                mds = f"{startWord}".encode()
                index = data.find(mds, offset)
            if index < 0:
                break
            st = index + len(mds)
            fs = int.from_bytes(
                data[st:st+4], byteorder='little', signed=False)
            fe = int.from_bytes(
                data[st+4:st+8], byteorder='little', signed=False)
            cs = int.from_bytes(
                data[st+8:st+12], byteorder='little', signed=False)
            ce = int.from_bytes(data[st+12:st+16],
                                byteorder='little', signed=False)
            count = fe - fs
            offset = st + 16
            n = 0
            i = offset
            while True:
                if i > (offset + count):
                    break
                addr = int.from_bytes(
                    data[i:i+4], byteorder='little', signed=False)
                if (addr >= cs and addr <= ce):
                    coff = addr - cs
                    k = data.find(b'\0', offset + count + coff)
                    log = data[offset + count + coff:k+1]
                    #print(log)
                    fi = log.find(b'[Format:')
                    fed = log.rfind(b']')
                    #print(f'fi={fi},fed={fed}')
                    fmt = bytes.decode(log[fi+8:fed], encoding='utf-8', errors='ignore')
                    #rint(f'fmt={fmt}')
                    StreamLog.tablebplus[fs+4*n] = fmt
                    #print(fmt)
                i += 4
                n += 1
            StreamLog.stringtable.append((cs,ce,data[offset + count:offset+count+ce-cs]))
            offset += count
            offset += (ce - cs)
    def loadLines(data_line: List[str]):
        for line in data_line:
            if not line.strip('\0') or ',' not in line:
                continue
            lst = eval(line.strip('\0'))
            #print(f'line={line},t ={type(lst)}')
            StreamLog.table[lst[0]] = [lst[1], lst[2]]
    @staticmethod
    def loadbplus(data: bytes):
        StreamLog.tablebplus.clear()
        StreamLog.stringtable.clear()
        UartDecode.loadaddress(data)
        offset = 0
        #print(StreamLog.tablebplus)
        while (True):
            rommd = b"core_dbglog_fl_start\r\n"
            romindex = data.find(rommd, offset)
            if romindex<0:
                rommd = b"core_dbglog_fl_start"
                romindex = data.find(rommd, offset)
            b_rom_log = romindex >= 0
            if b_rom_log:
                romindex_end = data.find(b"core_dbglog_fl_end",offset)
                if romindex_end < 0:
                    break
                isJsonFmt = data.find(b'[',romindex+len(rommd), romindex+len(rommd)+5) > 0
                if isJsonFmt:
                    ld = data[romindex+ len(rommd):romindex_end -3]
                    lines = bytes.decode(ld, encoding='utf-8', errors='ignore').split('\n')
                    UartDecode.loadLines(lines)
                else:
                    UartDecode.loadaddress(data,romindex,'core_dbglog_fl_start')
                offset = romindex_end + len("core_dbglog_fl_end")#- romindex
            if not b_rom_log:
                    break
    @staticmethod
    def load(file='dbglog_table.txt', isBplus=False,romtable=''):
        if file is None or not os.path.exists(file):
            return
        data = b''
        StreamLog.table.clear()
        if "wpk" in file:
            import zipfile
            zfile = zipfile.ZipFile(file, 'r')
            StreamLog.table.clear()
            for filename in zfile.namelist():
                if filename == 'dbglog_table.txt':
                    data = zfile.read(filename)
                    break
        else:
            with open(file, 'rb') as f:
                data = f.read()
                if data is None or len(data)==0:
                    print('empty')
                    return
        if (data[0] != 91 and not isBplus):
            if romtable:
                UartDecode.load(romtable, True)
            UartDecode.loadbplus(data)
            return
        data_line = bytes.decode(
            data, encoding='utf-8', errors='ignore').split('\n')
        UartDecode.loadLines(data_line)
        #print(StreamLog.table)
        #print(StreamLog.tablebplus)
   

    def getbytes(self, seq: int, cmd: CommandBase) -> bytes:
        return createCommand(seq, cmd)

    def get_result(self, data: bytes, callback):
        self.datatemp += data
        while True:
            index = self.datatemp.find(self.magicword)
            if index >= 0:
                if index > 0:
                    avadata = self.datatemp[0: index]
                    txt = bytes.decode(avadata, encoding='utf-8', errors='ignore')
                    strlog = StringLog(self.get_rawstring(txt))
                    callback(strlog)
                    self.datatemp = self.datatemp[index:]
                if len(self.datatemp) >= LogBase.header_len:
                    header = LogBase()
                    header.loadbytes(self.datatemp[0: LogBase.header_len])
                    second = self.datatemp.find(magicword, len(magicword))

                    hc = header.checkheader()
                    if hc:
                        if len(self.datatemp) < header.len + len(magicword):
                            break
                        alllen = len(magicword) + header.len
                        alldata = self.datatemp[0:alllen]
                        header.loadbytes(alldata)
                        cc = header.check()
                        log = createLogBase(header.msgtype, alldata, True, cc)
                        callback(log)
                        if cc:
                            self.datatemp = self.datatemp[alllen:]
                            continue
                    if second > 0:
                        self.datatemp = self.datatemp[second:]
                        continue
            else:
                self.handlesbl(callback)
            break

    def handlesbl(self, callback, index=0):
        log = bytes.decode(self.datatemp, encoding='utf-8', errors='ignore')
        if len(self.datatemp) > 3:
            last3 = self.datatemp[-3:]
            words = [0xD0, 0xD2, 0xC5]
            index = 0
            if words[0] == last3[0] and words[1] == last3[1] and words[2] == last3[2]:
                index = 3
            elif words[0] == last3[1] and words[1] == last3[2]:
                index = 2
            elif words[0] == last3[2]:
                index = 1
            avadata = self.datatemp[0:len(self.datatemp)-index]
            txt = bytes.decode(avadata, encoding='utf-8', errors='ignore')
            strlog = StringLog(self.get_rawstring(txt))
            callback(strlog)
            self.datatemp = self.datatemp[len(self.datatemp)-index:]
    def get_rawstring(self,s:str):
        result =''
        self.cache +=s
        nl = self.cache.find('\n',-1)
        if nl>0:
            txt = self.cache[0:nl]
            remind = self.cache[nl+1:].strip()
            self.cache = ''
            if remind:
                self.cache+=remind
            result = txt

        return result

fre = re.compile(
    r"\[auto\]\s*(?P<fileid>\d{1,}):(?P<linenum>\d{1,})\s*Asserted", flags=re.I)
# log='[auto]200:300 Asserted'
# rr = fre.search(log)
# if rr:
#     print(rr.group('fileid'))
#     print(rr.group('linenum'))

"""
uint32 magicword ->4
#header
uint8 version; -> 1
uint16 len; ->2
uint8 msgtype;->1 6bits for type, 2bits for ctrl

uint8:3 tid
uint8:4 reserved
uint8:1 ack; 

uint16 seqnum;->2
uint8 crc8;->1 ->header
#payload
payload:bytes
#crc32 ->header + payload
crc32
"""


class LogBase:
    header_struct = '<IBHBBHB'  # 4+8
    header_len = struct.calcsize(header_struct)

    def __init__(self):
        self.magicword = magicword
        self.version = 0
        self.len = 0
        self._msgtype = 0
        # self.tid = 0
        self._value = 0  # tid ack
        self.seqnum = 0
        self.crc8 = 0
        self.payload = b''
        self.crc32 = 0

        self.header_check = False
        self.content_check = False

    def loadbytes(self, data: bytes):
        """
        parse total data, deviced object must override the method.
        """
        if len(data) < LogBase.header_len:
            return
            raise Exception(
                f'error:hc={self.header_check},cc={self.content_check}')
        else:
            result = struct.unpack(LogBase.header_struct,
                                   data[0:LogBase.header_len])
            [self.magicword, self.version, self.len, self._msgtype,
                self._value, self.seqnum, self.crc8] = result

        if len(data) >= len(magicword) + self.len:
            self.payload = data[LogBase.header_len:len(data)-4]
            self.crc32 = int.from_bytes(
                data[-4:], byteorder='little', signed=False)

    def checkheader(self):
        """
        check header with crc8
        """
        data = struct.pack('<BHBBH', self.version, self.len,
                           self._msgtype, self._value, self.seqnum)
        crc = binascii.crc8(data)
        return crc == self.crc8

    def check(self):
        """
        check header & payload with crc32
        """
        data = struct.pack('<BHBBHB', self.version, self.len, self._msgtype,
                           self._value, self.seqnum, self.crc8) + self.payload
        crc = binascii.crc32(data)
        return crc == self.crc32

    def getbytes(self):
        self.len = self.getlen()
        headerData = struct.pack(
            '<BHBBH', self.version, self.len, self._msgtype, self._value, self.seqnum)
        self.crc8 = Crc.crc8_calc(headerData)
        # header + payload
        hp = struct.pack('<BHBBHB', self.version, self.len, self._msgtype,
                         self._value, self.seqnum, self.crc8) + self.getpayload()
        crc32 = binascii.crc32(hp)
        return magicword + hp + crc32.to_bytes(4, byteorder='little')

    def getpayload(self):
        return self.payload

    def getlen(self):
        return 8+len(self.getpayload()) + 4

    @property
    def tid(self):
        return self._value & (0xF >> 1)

    @tid.setter
    def tid(self, val: int):
        self._value = val if not self.ack else (0x1 << 7) & val

    @property
    def ack(self):
        return (self._value >> 7) == 1

    @property
    def frag(self):
        return (self._value >> 3) & 0b11
    @ack.setter
    def ack(self, val: bool):
        self._value = self.tid if not val else (0x1 << 7) & self.tid

    @property
    def msgtype(self):
        return self._msgtype & (0xFF >> 2)

    @msgtype.setter
    def msgtype(self, val: int):
        self._msgtype = (self.ctrl << 6) | val

    @property
    def ctrl(self):
        return self._msgtype >> 6

    @ctrl.setter
    def ctrl(self, val: int):
        self._msgtype = self.msgtype & (val << 6)
    def get_string(self)->str:
        if self.payload:
          return self.payload.hex()
        return ''


def createLogBase(msgtype: int, data: bytes, hc=False, cc=False) -> LogBase:
    """
    type to LogBase
    """
    result = None
    if msgtype == 1:
        result = StreamLog()
    elif msgtype == 2:
        result = RawLog()
    elif msgtype == 5:
        result = RawLog()
    elif msgtype == 3:
        result = CliLog()
    elif msgtype == 4:
        result = DumpData()
    elif msgtype == 6:
        result = LogBase()
    else:
        result = LogBase()
    if result:
        result.header_check = hc
        result.content_check = cc
        result.loadbytes(data)
    return result

audio_header_fmt='<2H4B2I2BH'
audio_header_len = struct.calcsize(audio_header_fmt) + 4
class DumpData(LogBase):
    def __init__(self):
        super().__init__()
        ct = time.time()
        local_time = time.localtime(ct)
        data_ms = (ct - int(ct)) * 1000
        self.time = time.strftime(
            "%Y%m%d-%H%M%S-", local_time) + str('%03d' % data_ms)
   
    def __str__(self):
        return 'seqnum={0},msgtype={1},tid={2},ack={3},payloadlen={4},time={5}'.format(self.seqnum,
                                                                                        self.msgtype,
                                                                                        self.tid,
                                                                                        self.ack,
                                                                                        len(self.payload),
                                                                                        self.time)
class AudioDumpData():
    """
    audio dump data
    """
    def __init__(self, adk_audio:'AudioDumpDataHeader' =None):
        super().__init__()
        self.adk_audio:AudioDumpDataHeader  = adk_audio
        self.payload:bytes =b''
    def loadbytes(self, data: bytes):
        self.payload = data
        if data[0:4] == bytes([0x55,0xAA,0x70,0x36]):
            self.adk_audio  = AudioDumpDataHeader(data[0:audio_header_len])
    def getpayload(self):
        return self.payload[audio_header_len:]
    def __str__(self):
        return f'header={self.adk_audio },payload len ={len(self.getpayload())}'

class AudioDumpDataHeader:
    def __init__(self,data:bytes):
        self.bitwide :int= 0
        [self.point_map,self.length,self.coreid,self.channels,self.bitwide,self.location,self.ts,self.samplerate,self.format,_,self.seqid] = struct.unpack(audio_header_fmt,data[4:audio_header_len])

    def __str__(self) -> str:
        return f'point_map={self.point_map},seqid={self.seqid},len={self.length},ts={self.ts},sample_rate={self.samplerate},channel={self.channels},bitwide={self.bitwide}'

class Ack(LogBase):
    def __init__(self, seq=0, status=0, tid=0):
        super().__init__()
        self._msgtype = 0x41
        self.seq = seq
        self.status = status
        self.tid = tid

    def getpayload(self):
        return struct.pack('<HHBB', self.seq, self.status, 4, self.tid)


class StreamLog(LogBase):
    table = {}
    tablebplus = {}
    stringtable:List[Tuple[int,int,bytes]] = []
    def __init__(self):
        super().__init__()
        self.headerlen = 12
        self.timespan = 0
        self.coreid = 255
        self.seqid = 0  # 12
        self.logversion = 0  # 4
        self.payloadlen = 0
        self.__value = 0
        self.level = 0xFF
        self.logtype = 0
        self.moduleid = 0xFF
        self.fileid = 0
        self.linemun = 0
        self.addr = 0xFFFF
        self.content = b''

    def loadbytes(self, data: bytes):
        super().loadbytes(data)
        self.headerlen = 12 if self.version == 0 else 13
        if self.version == 0:
            [self.timespan, self.seqid, self.payloadlen, self.__value] = struct.unpack('<IHHI',
                                                                                       self.payload[0:self.headerlen])
            self.fileid = self.__value >> 8 & 0xFFF
            self.linemun = self.__value >> 20 & 0xFFF
        else:
            [self.timespan, core_seq_ver, self.payloadlen] = struct.unpack(
                '<I2H', self.payload[0:8])
            self.logversion = core_seq_ver >> 12
            if self.logversion == 0:
                if len(self.payload) < self.headerlen:
                    return
                self.seqid = 0xFFFF >> 4 & core_seq_ver
                [self.__value, self.fileid, self.linemun] = struct.unpack(
                    '<B2H', self.payload[8:self.headerlen])
                self.level = self.__value & 0xF >> 1
                self.moduleid = self.__value >> 3 & 0xFF >> 3
            elif self.logversion == 1:
                if len(self.payload) < self.headerlen:
                    return
                self.coreid = (0xF >> 2) & core_seq_ver
                self.seqid = (0xFFF >> 2) & (core_seq_ver >> 2)
                [self.__value, self.fileid, self.linemun] = struct.unpack(
                    '<B2H', self.payload[8:self.headerlen])
                self.level = self.__value & 0xF >> 1
                self.moduleid = self.__value >> 3 & 0xFF >> 3
            else:
                self.headerlen = 14
                if len(self.payload) < self.headerlen:
                    return
                self.coreid = (0xF >> 2) & core_seq_ver
                self.seqid = (0xFFF >> 2) & (core_seq_ver >> 2)
                self.level = self.payload[8]
                self.logtype = (self.level >> 3) & 1
                [self.moduleid, self.fileid, self.linemun] = struct.unpack(
                        '<B2H', self.payload[9:self.headerlen])
                if self.logtype == 1:
                    [self.moduleid, self.addr] = struct.unpack(
                        '<BI', self.payload[9:self.headerlen])

        self.content = self.payload[self.headerlen:]

    def get_level(self):
        return self.level

    def get_moduleid(self):
        return self.moduleid

    def get_fileid(self):
        return self.fileid

    def get_linenum(self):
        return self.linemun

    def get_bstring(self):
        if self.addr in StreamLog.tablebplus:
            fmt = StreamLog.tablebplus[self.addr]
            return self.get_totlestring(fmt, self.content)
        return f"can't resolver stream log file,coreid={self.coreid},addr={self.addr},payload={self.content.hex()}"

    def get_string(self):
        if not self.content_check:
            return f"cc-false:{self.getpayload().hex()}"
        if self.logtype == 1 and len(StreamLog.tablebplus)>0:
            return self.get_bstring()
        fileid = self.get_fileid()
        linenum = self.get_linenum()
        if fileid in StreamLog.table:
            lines = StreamLog.table[fileid][1]
            if linenum in lines:
                log = self.get_stringwithoutfunc(lines[linenum], self.content)
                if log:
                    result = fre.match(log)
                    if result:
                        fid = int(result.group('fileid'))
                        lnum = result.group('linenum')
                        if fid in StreamLog.table:
                            fn = StreamLog.table[fid][0]
                            return f'[auto] {fn}:{lnum} Asserted!'
                    return log
                else:
                    return "resolver fail:[{0}] [{1}]: {2} [{3}] ".format(StreamLog.table[fileid][0],
                                                                          linenum,
                                                                          lines[linenum],
                                                                          self.content.hex())
        return "resolver fail:fileid= [{0}] , linenum=[{1}]".format(fileid, linenum)

    def get_stringwithoutfunc(self, logwithfun: str, payload: bytes):
        start = logwithfun.find('"')
        end = logwithfun.rfind('"')
        log = logwithfun[start:end+1]
        return self.get_totlestring(log, payload)

    def get_totlestring(self, log: str, payload: bytes):
        agrcount = len(payload) // 4
        lst = re.findall(r"%[.|l(\d)#]*[c|defiopsux]", log, flags=re.I)
        if agrcount != len(lst):
            return '{0}={1}'.format(log, payload.hex())
            # log.endswith()
        for f in lst:
            if f.endswith('p') or f.endswith('P'):
                rep = f
                np = rep[0:-1] + 'x'
                log = log.replace(f, np, 1)
        values = self.getvalue(lst, payload)
        last = log.replace('"\\"', '', -1)
        last = last.replace('%llu', '%lu', -1)
        if(last.startswith('"')):
            return eval(last.strip()) % tuple(values)
        if agrcount != len(lst) or agrcount!=len(values):
            print(f'log={log},payload={payload.hex()},lst={lst},values={values}')
        return last % tuple(values)

    @staticmethod
    def getvalue(formatlist, payload: bytes):
        result = []
        for i, f in enumerate(formatlist):
            data = payload[i*4:(i+1)*4]
            if f.endswith('d') or f.endswith('D') or f.endswith('i'):
                value = int.from_bytes(data, byteorder='little', signed=True)
                result.append(value)
            elif f.endswith('o') or f.endswith('O') or f.endswith('x') or f.endswith('X') or f.endswith('u') or f.endswith('U') or f.endswith('p') or f.endswith('P'):
                value = int.from_bytes(data, byteorder='little', signed=False)
                result.append(value)
            elif f.endswith('e') or f.endswith('E') or f.endswith('f') or f.endswith('F') or f.endswith('g') or f.endswith('G'):
                [value] = struct.unpack('f', data)
                result.append(value)
            elif f.endswith('c') or f.endswith('C'):
                [cs] = struct.unpack('<I', data)
                result.append(cs)
            elif f.endswith('s') or f.endswith('S'): #%s
                [addr] = struct.unpack('<I', data)
                flag = False
                for cs,ce,fmt in StreamLog.stringtable:
                    if addr >= cs and addr <= ce:
                        offset = addr - cs
                        endindex = fmt.find(b'\0', offset)
                        value = fmt[offset:endindex].decode(encoding='utf-8', errors='ignore')
                        result.append(value)
                        flag = True
                        break
                if not flag:
                    Log.E(f'str {hex(addr)} not found')
                    #result.append(f'str {hex(addr)} not found')
                    result.append('')

            else:  # %c 
                result.append(data.decode(encoding='utf-8', errors='ignore'))
        return result


class RawLog(LogBase):
    def __init__(self):
        super().__init__()
        self.headerlen = 9
        self.timespan = 0
        self.coreid = 255
        self.seqid = 0  # 12
        self.logversion = 0  # 4
        self.payloadlen = 0
        self.__value = 0
        self.level = 0xFF
        self.moduleid = 0xFF
        self.content = b''

    def loadbytes(self, data: bytes):
        super().loadbytes(data)
        if self.version == 0:
            if len(self.payload)<self.headerlen:
                return
            [self.timespan, self.seqid, self.payloadlen, self.__value] = struct.unpack('<IHHB',
                                                                                       self.payload[0:self.headerlen])
        else:
            [self.timespan, core_seq_ver, self.payloadlen] = struct.unpack(
                '<I2H', self.payload[0:8])
            self.logversion = core_seq_ver >> 12
            if self.logversion == 0:
                self.seqid = 0xFFFF >> 4 & core_seq_ver
                self.__value = self.payload[8]
                self.level = self.__value & 0xF >> 1
                self.moduleid = self.__value >> 3 & 0xFF >> 3
            elif self.logversion == 1:
                self.coreid = (0xF >> 2) & core_seq_ver
                self.seqid = (0xFFF >> 2) & (core_seq_ver >> 2)

                self.__value = self.payload[8]
                self.level = self.__value & 0xF >> 1
                self.moduleid = self.__value >> 3 & 0xFF >> 3
            elif self.logversion == 2:
                self.headerlen = 10
                self.coreid = (0xF >> 2) & core_seq_ver
                self.seqid = (0xFFF >> 2) & (core_seq_ver >> 2)
                [self.level, self.moduleid] = struct.unpack(
                    '<BB', self.payload[8:self.headerlen])
                pass
        self.content = self.payload[self.headerlen:]

    def get_level(self):
        return self.level

    def get_moduleid(self):
        return self.moduleid

    def get_string(self) -> str:
        log = bytes.decode(self.content, encoding='utf-8',
                           errors='ignore').strip()
        result = fre.match(log)
        if result:
            fileid = result.group('fileid')
            linenum = result.group('linenum')
            fid = int(fileid)
            if fid in StreamLog.table:
                fn = StreamLog.table[fid][0]
                return f'[auto] {fn}:{linenum} Asserted!'
        return log


class CliLog(LogBase):
    def __init__(self):
        super().__init__()
        self.__value = 0
        self._msgtype = 3
        self.content = b''


class StringLog:
    def __init__(self, msg=''):
        self.msg = msg
        self.msgtype = 0x10

    def get_string(self) -> str:
        return self.msg

    def __str__(self):
        return self.msg
