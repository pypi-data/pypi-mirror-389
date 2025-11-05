#!/usr/bin/python
# -*- coding: utf-8 -*-

import struct
import binascii
import sys
from abc import ABCMeta
from enum import IntEnum
from typing import List


class CLI_DATA_OPERATION_TYPE(IntEnum):
    REG = 0
    RAM = 1
    FLASH = 2
    REG_GROUP = 3
    MAX = 4

class CLI_DEST(IntEnum):
    LOCAL = 0
    MASTER_ONLY = 1
    SLAVE_ONLY = 2
    MASTER_AND_SLAVE = 3
    MAX = 4


start = bytes([0x23, 0x23])
end = bytes([0x40, 0x40])
header_struct = '<2s3H2B2H'  # 12+6*2 24
header_len = struct.calcsize(header_struct)

# def parseCommand(data=b''):
#     """
#     return an object instanct of CommandBase
#     """
#     rep = CommandBase()
#     if len(data) >= header_len:
#         lst=struct.unpack(header_struct, data[0:header_len])
#         [start, moduleid, crc, msgid, ack, length, seqnum.end]=lst
#         if len(data) >= header_len + length:
#             payload=data[header_len:]
#         if(moduleid==4 and msgid==1):
#             rep=GetVersionResponse()
#     return rep

# 扩展cli步骤
# 1.继承基类CommandBase
# 2.请求类名以Requset结尾，响应类以Response结尾
# 3.如果不在cli模块里面实现，就得重写基类的get_moduleName方法
# 4.如果类名不按照命名约定，需重写基类的get_instanceName方法
# 5.payload内容解析自行实现，参照GetVersionResponse


class CommandBase:
    """
    Derived classes come in pairs, with Request and Response classes ending in Request and Response, respectively
    """
    __metaclass__ = ABCMeta

    def __init__(self):
        self.start = start
        self.moduleid = 0
        # self.crc = 0
        self.msgid = 0
        self.ack = 0
        self.result = 0
        # self.len=0
        self.seqnum = 0
        self.payload = b''
        self.end = end

        self.hasresponse = True

    @property
    def length(self):
        pl = self.getpayload()
        return len(pl) if pl else 0

    @property
    def crc(self):
        if self.length > 0:
            return binascii.crc32(self.getpayload()) & 0xFFFF
        return 0

    def loadbytes(self, data: bytes):
        if len(data) >= header_len:
            lst = struct.unpack(header_struct, data[0: header_len])
            [self.start, self.moduleid, crc, self.msgid,
                self.ack, self.result, length, self.seqnum] = lst
        if len(data) >= header_len + self.length:
            self.payload = data[header_len: len(data) - 2]

    def getbytes(self):
        return (self.start +
                struct.pack('<3H2B2H', self.moduleid, self.crc, self.msgid, self.ack,self.result, self.length, self.seqnum) +
                self.getpayload() +
                self.end)

    def check(self, cmd: 'CommandBase'):
        return True

    def getpayload(self):
        """
        子类重写,默认返回payload
        """
        return self.payload

    def getresponse(self) ->'CommandBase':
        """
        return an Response object instance of CommandBase by the Request
        """
        modulename = self.get_moduleName()
        insName = self.get_instanceName()
        objaddr = getattr(modulename, insName)
        obj = objaddr()
        return obj

    def get_moduleName(self):
        """
        模块名，默认实现为本类中的模块，如果不在本模块扩展，则需派生类重写此方法
        """
        modulename = sys.modules[__name__]
        return modulename

    def get_instanceName(self):
        """
        响应类名，默认约定请求类为Request结束，响应类为Response结束，如不是以此命名，则需派生类重写此方法,返回对应响应类的类名
        """
        name = self.__class__.__name__
        resname = name.replace('Request', 'Response')
        return resname

    def __str__(self):
        return 'moduleid:{0}, msgid:{1}, len={2}, payload:{3},seqnum={4}'.format(self.moduleid,
                                                                      self.msgid,
                                                                      self.length,
                                                                      self.getpayload().hex(),self.seqnum)


class GetVersionRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 4
        self.msgid = 0


class GetVersionResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.sw_ver = 0
        self.soc_id = []
        self.reserver = bytes([0] * 72)

    def loadbytes(self, data):
        super().loadbytes(data)
        [self.sw_ver, *self.soc_id] = struct.unpack('<3I', self.payload[0:12])

    def __str__(self):
        # print(self.payload[0:12].hex())
        return 'moduleid:{0}, msgid:{1}, len={2}, sw_ver:{3}, soc_id:{4}'.format(self.moduleid,
                                                                                 self.msgid,
                                                                                 self.length,
                                                                                 '%#x' % self.sw_ver,
                                                                                 self.soc_id)


class ReadNTCRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 6
        self.msgid = 19


class ReadNTCResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.ntc = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        [self.ntc] = struct.unpack('<H', self.payload)


class SwitchRoleRequest(CommandBase):
    def __init__(self, role=57):
        super().__init__()
        self.moduleid = 6
        self.msgid = 2
        self.payload = struct.pack('<I', role)


class SwitchRoleResponse(CommandBase):
    def __init__(self):
        super().__init__()


# 读取寄存器
class ReadRegisterRequest(CommandBase):
    def __init__(self, address: int = 0x03070028):  # result -> 3C003C00
        super().__init__()
        self.moduleid = 4
        self.msgid = 4
        self.address = address
        self.readtype = 0  # 寄存器
        self.readlen = 4  # 长度4
        self.payload = struct.pack(
            '<IHB', address, self.readlen, self.readtype)

    def getpayload(self):
        return struct.pack('<IHB', self.address, self.readlen, self.readtype)


class ReadRegisterResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.addr = 0
        self.readtype = 0
        self.readvalue = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        [self.addr, self.readtype, self.readvalue] = struct.unpack(
            '<IBI', self.payload)

    def __str__(self):
        return 'addr={0:#X}, type={1}, value={2:#X}, paylaodlen={3}'.format(self.addr,
                                                                            self.readtype,
                                                                            self.readvalue,
                                                                            len(self.payload))


# 写寄存器
class WriteRegisterRequest(CommandBase):
    def __init__(self, address: int, data: int):
        super().__init__()
        self.moduleid = 4
        self.msgid = 6
        self.writetype = 0
        self.address = address
        self.value = data
        self.payload = self.getpayload()

    def getpayload(self):
        return struct.pack('<IBI', self.address, self.writetype, self.value)


class WriteRegisterResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.address = 0
        self.len = 0
        self.type = 0
        self.result = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        [self.addr, self.len, self.type, self.result] = struct.unpack(
            '<IHBB', self.payload)

    def __str__(self):
        return 'addr={0:#X}, len={1}, type={2}, value={3}, paylaodlen={4}'.format(self.addr,
                                                                                  self.len,
                                                                                  self.type,
                                                                                  self.result,
                                                                                  len(self.payload))


# 写寄存器組
class WriteRegisterGroupRequest(CommandBase):
    def __init__(self, address: int, data: list):
        super().__init__()
        self.moduleid = 4
        self.msgid = 6
        self.writetype = 3
        self.address = address
        self.value = data
        self.len = 4 * len(data)
        self.payload = self.getpayload()

    def getpayload(self):
        return struct.pack('<IBH%dI' % len(self.value), self.address, self.writetype, self.len, *self.value)


class WriteRegisterGroupResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.address = 0
        self.len = 0
        self.type = 0
        self.result = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        [self.addr, self.len, self.type, self.result] = struct.unpack(
            '<IHBB', self.payload)

    def __str__(self):
        return 'addr={0:#X}, len={1}, type={2}, value={3}, paylaodlen={4}'.format(
            self.addr, self.len, self.type, self.result, len(self.payload))


# 读取寄存器组
class ReadRegisterGroupRequest(CommandBase):
    def __init__(self, address: int = 0x03080000, regCnt: int = 4):  # result -> 3C003C00
        super().__init__()
        self.moduleid = 4
        self.msgid = 4
        self.address = address
        self.readtype = CLI_DATA_OPERATION_TYPE.REG_GROUP  # 寄存器组
        if regCnt > 62:
            regCnt = 62
        self.readlen = 4 * regCnt  # 寄存器个数的4的倍数
        self.payload = struct.pack(
            '<IHB', address, self.readlen, self.readtype)

    def getpayload(self):
        return struct.pack('<IHB', self.address, self.readlen, self.readtype)


class ReadRegisterGroupResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.addr = 0
        self.readtype = 0
        self.reglen = 0  # 寄存器所占字节数
        self.regvalueLst = list()  # 寄存器值
        self.regCnt = 0  # 实际寄存器个数

    def loadbytes(self, data):
        super().loadbytes(data)
        [self.addr, self.readtype, self.reglen] = struct.unpack(
            '<IBH', self.payload[0:7])
        self.regCnt = self.reglen // 4
        self.regvalueLst = [0] * self.regCnt
        [self.addr, self.readtype, self.reglen, *self.regvalueLst] = struct.unpack('<IBH%dI' % self.regCnt,
                                                                                   self.payload)

    def __str__(self):
        ret_str = 'addr={0:#X}, type={1}, paylaodlen={2}, registerCnt={3}'.format(self.addr,
                                                                                  self.readtype,
                                                                                  len(self.payload),
                                                                                  self.regCnt)
        regvalue_str = '\nregister:value\n'
        for i in range(len(self.regvalueLst)):
            regvalue_str += '0x%x:0x%x\n' % (self.addr + i, self.regvalueLst[i])
        ret_str = ret_str + regvalue_str
        return ret_str


class AncDumpInitRequest(CommandBase):
    def __init__(self, mic_bitmap: int, dumpMicGain, beetle_plus_flag=False):
        super().__init__()
        self.beetle_plus_flag = beetle_plus_flag
        self.moduleid = 8
        self.msgid = 15
        if self.beetle_plus_flag is False:
            self.mic_bitmap = mic_bitmap
        else:
            self.mic_bitmap0 = mic_bitmap & 0xff
            self.mic_bitmap1 = mic_bitmap >> 8
        self.dumpMicGain = dumpMicGain

    def getpayload(self):
        if self.beetle_plus_flag is False:
            return struct.pack('<Bh', self.mic_bitmap, self.dumpMicGain)
        else:
            return struct.pack('<2Bh', self.mic_bitmap0, self.mic_bitmap1, self.dumpMicGain)


class AncDumpInitResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.result = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        if len(self.payload) == 1:
            self.result = struct.unpack('<B', self.payload)
        else:
            self.result = 1

    def __str__(self):
        return 'payload={0}'.format(self.payload)
class IPoint:
    def getbytes(self):
        return b''*4
class ACorePoint(IPoint):
    def __init__(self,srcid:int,sampleid:int,channel:int) -> None:
        self.srcid = srcid
        self.sampleid = sampleid
        self.channel = channel
    def getbytes(self):
        return struct.pack('<H2B', self.srcid,self.channel,self.sampleid)
class DCorePoint(IPoint):
    def __init__(self,streamid:int,processorid:int,channel:int) -> None:
        self.streamid= streamid
        self.processorid= processorid
        self.channel = channel
    def getbytes(self):
        return struct.pack('<H2B', self.streamid,self.channel,self.processorid)
class AudioDumpStartRequest(CommandBase):
    def __init__(self,dumpway:int,core:int,ack:bool,points:List[IPoint] = []):
        super().__init__()
        self.moduleid = 8
        self.msgid = 320
        self.dumpway = dumpway
        self.core = core
        self.ack = ack
        self.points = points
    @property
    def count(self):
        return len(self.points)
    def getpayload(self):
        pl = b''
        for point in self.points:
            pl+=point.getbytes()
        return struct.pack('<4B', self.dumpway,self.core,1 if self.ack else 0,self.count) + pl
class AudioDumpStartResponse(CommandBase):
    def __init__(self):
        super().__init__()
 # anc dump stop
class AudioDumpStopRequest(CommandBase):
    def __init__(self, isStopOrPause: int = 0):
        super().__init__()
        self.moduleid = 8
        self.msgid = 321
class AudioDumpStopResponse(CommandBase):
    def __init__(self):
        super().__init__()

# anc dump start
class AncDumpStartRequest(CommandBase):
    def __init__(self, dumpPkgCnt):
        super().__init__()
        self.moduleid = 8
        self.msgid = 5
        self.dumpPkgCnt = dumpPkgCnt

    def getpayload(self):
        return struct.pack('<H', self.dumpPkgCnt)


class AncDumpStartResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.result = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        self.result = struct.unpack('<B', self.payload)

    def __str__(self):
        return 'payload={0}'.format(self.payload)


# anc dump stop
class AncDumpStopRequest(CommandBase):
    def __init__(self, isStopOrPause: int = 0):
        super().__init__()
        self.moduleid = 8
        self.msgid = 6
        self.isStopOrPause = isStopOrPause

    def getpayload(self):
        return struct.pack('<B', self.isStopOrPause)


class AncDumpStopResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.result = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        self.result = struct.unpack('<B', self.payload)

    def __str__(self):
        return 'payload={0}'.format(self.payload)


# anc play sweep start
class AncPlaySweepStartRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 8
        self.msgid = 7
        self.payload = self.getpayload()

    def getpayload(self):
        return struct.pack('<B', 0)


class AncPlaySweepStartResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.result = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        self.result = struct.unpack('<B', self.payload)

    def __str__(self):
        return 'payload={0}'.format(self.payload)


# anc play sweep stop
class AncPlaySweepStopRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 8
        self.msgid = 8
        self.payload = self.getpayload()

    def getpayload(self):
        return struct.pack('<B', 0)


class AncPlaySweepStopResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.result = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        self.result = struct.unpack('<B', self.payload)

    def __str__(self):
        return 'payload={0}'.format(self.payload)


class AdkGetAncDumpPortMapRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 8
        self.msgid = 51


class AdkGetAncDumpPortMapResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.anc_dump_port_map = 0
        self.total_path_num = -1
        self.dig_gain_list = []

        self.fb_R_idx = [7, 7, 7, 7]
        self.ff_R_idx = [7, 7, 7, 7]

        self.fb_L_idx = [7, 7, 7, 7]
        self.ff_L_idx = [7, 7, 7, 7]

        self.ref_L = 255
        self.ref_R = 255

    def loadbytes(self, data):
        super().loadbytes(data)
        if len(self.payload) == 1:
            fmt = '<B'  # for (uint8_t path)
            self.anc_dump_port_map, = struct.unpack(fmt, self.payload)
        elif len(self.payload) == 2:
            fmt = '<H'
            self.anc_dump_port_map, = struct.unpack(fmt, self.payload)
        elif len(self.payload) == 4:
            fmt = '<I'  # for (uint32_t path)
            self.anc_dump_port_map, = struct.unpack(fmt, self.payload)
        elif len(self.payload) == 23:
            fb_L_val = [255, 255]
            ff_L_val = [255, 255]
            fb_R_val = [255, 255]
            ff_R_val = [255, 255]

            # for (uint32_t path) + (uint8_t total_path_num) + (int8_t dig_gain[6]) + (struct anc_dump_index_info_t(12B))
            fmt = '<IB6b10BH'
            (self.anc_dump_port_map, self.total_path_num, *self.dig_gain_list,
             fb_L_val[0], fb_L_val[1], ff_L_val[0], ff_L_val[1],
             fb_R_val[0], fb_R_val[1], ff_R_val[0], ff_R_val[1],
             self.ref_L, self.ref_R, _
             ) = struct.unpack(fmt, self.payload)

            for i in range(4):
                if i % 2 == 0:
                    self.fb_R_idx[i] = fb_R_val[i // 2] & 0x7
                    self.ff_R_idx[i] = ff_R_val[i // 2] & 0x7
                    self.fb_L_idx[i] = fb_L_val[i // 2] & 0x7
                    self.ff_L_idx[i] = ff_L_val[i // 2] & 0x7
                else:
                    self.fb_R_idx[i] = (fb_R_val[i // 2] >> 3) & 0x7
                    self.ff_R_idx[i] = (ff_R_val[i // 2] >> 3) & 0x7
                    self.fb_L_idx[i] = (fb_L_val[i // 2] >> 3) & 0x7
                    self.ff_L_idx[i] = (ff_L_val[i // 2] >> 3) & 0x7


class AdkAncDumpRequest(CommandBase):
    def __init__(self, content: bytes):
        super().__init__()
        self.moduleid = 8
        self.msgid = 50
        self.content = content

    def getpayload(self):
        return self.content


class AdkAncDumpResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.result = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        self.result = struct.unpack('<B', self.payload)

    def __str__(self):
        return 'payload={0}'.format(self.payload)

class AdkAncOnlineDumpSwitchRequest(CommandBase):
    def __init__(self, enable_flag: bool, streamid: int, sample_rate_idx: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 52
        self.enable_flag = int(enable_flag)
        self.streamid = streamid
        self.sample_rate_idx = sample_rate_idx

    def getpayload(self):
        return struct.pack('<3B', self.enable_flag,  self.streamid, self.sample_rate_idx)

class AdkAncOnlineDumpSwitchResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.total_path_num = -1
        self.sample_rate_idx = 0

        self.fb_R_idx = [7, 7, 7, 7]
        self.ff_R_idx = [7, 7, 7, 7]

        self.fb_L_idx = [7, 7, 7, 7]
        self.ff_L_idx = [7, 7, 7, 7]

        self.ref_L = 255
        self.ref_R = 255

    def loadbytes(self, data):
        super().loadbytes(data)
        if len(self.payload) == 9:
            (_, _,
             self.fb_R_idx[0], self.fb_L_idx[0],
             self.ff_R_idx[0], self.ff_R_idx[1],
             self.ff_L_idx[0], self.ff_L_idx[1],
             self.total_path_num) = struct.unpack('<9B', self.payload)
        elif len(self.payload) == 10:
            (_, _, self.total_path_num, self.sample_rate_idx,
             self.fb_R_idx[0], self.fb_L_idx[0],
             self.ff_R_idx[0], self.ff_R_idx[1],
             self.ff_L_idx[0], self.ff_L_idx[1]) = struct.unpack('<10B', self.payload)
        elif len(self.payload) == 16:
            fb_L_val = [255, 255]
            ff_L_val = [255, 255]
            fb_R_val = [255, 255]
            ff_R_val = [255, 255]
            (_, _, self.total_path_num, self.sample_rate_idx,
             fb_L_val[0], fb_L_val[1], ff_L_val[0], ff_L_val[1],
             fb_R_val[0], fb_R_val[1], ff_R_val[0], ff_R_val[1],
             self.ref_L, self.ref_R, _
             ) = struct.unpack('<14BH', self.payload)

            for i in range(4):
                if i % 2 == 0:
                    self.fb_R_idx[i] = fb_R_val[i // 2] & 0x7
                    self.ff_R_idx[i] = ff_R_val[i // 2] & 0x7
                    self.fb_L_idx[i] = fb_L_val[i // 2] & 0x7
                    self.ff_L_idx[i] = ff_L_val[i // 2] & 0x7
                else:
                    self.fb_R_idx[i] = (fb_R_val[i // 2] >> 3) & 0x7
                    self.ff_R_idx[i] = (ff_R_val[i // 2] >> 3) & 0x7
                    self.fb_L_idx[i] = (fb_L_val[i // 2] >> 3) & 0x7
                    self.ff_L_idx[i] = (ff_L_val[i // 2] >> 3) & 0x7

    def __str__(self):
        return 'payload={0}'.format(self.payload)

class AncPlaySweepInitRequest(CommandBase):
    def __init__(self, mic_bitmap: int, use_sin_wav: int, high_sample_rate: int, only_dump_receive_data: int,
                 spk_idx: int=0, not_dump_mic_data: int=0, both_spk_flag: int=0, gain: int=0, beetle_plus_flag=False):
        # spk_idx. 0: right spk; 1: left spk
        # both_spk_flag: 0: sweep spk depend on spk_idx; 1: both spk sweep
        # use_sin_wav： 0： cosine wave; 1: sin wave
        # high_sample_rate: 0: 16k sweep; 1: 48k sweep
        # only_dump_receive_data: 0: dump tx data; 1: not dump tx data
        # not_dump_mic_data: 0: dump rx data; 1: not dump rx data
        super().__init__()
        self.beetle_plus_flag = beetle_plus_flag
        self.moduleid = 8
        self.msgid = 13
        if self.beetle_plus_flag is False:
            self.byte0 = mic_bitmap + use_sin_wav * (1 << 7)
            self.byte1 = high_sample_rate + only_dump_receive_data * 2 + spk_idx * 2 ** 2 + both_spk_flag * 2 ** 3 + not_dump_mic_data * 2 ** 4
            self.byte2 = gain
        else:
            self.byte0 = mic_bitmap & 0xff
            self.byte1 = (mic_bitmap >> 8) | (use_sin_wav << 7)
            self.byte2 = high_sample_rate + only_dump_receive_data * 2 + spk_idx * 2 ** 2 + both_spk_flag * 2 ** 3 + not_dump_mic_data * 2 ** 4
            self.byte3 = gain

    def getpayload(self):
        if self.beetle_plus_flag is False:
            if self.byte1 == 0:
                return struct.pack('<B', self.byte0)
            else:
                return struct.pack('<2B', self.byte0, self.byte1)
        else:
            return struct.pack('<3Bb', self.byte0, self.byte1, self.byte2, self.byte3)


class AncPlaySweepInitResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.result = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        self.result = struct.unpack('<B', self.payload)

    def __str__(self):
        return 'payload={0}'.format(self.payload)


class ResetRequest(CommandBase):
    def __init__(self, por_reset=0, reset_delay=100):
        super().__init__()
        self.moduleid = 0x4
        self.msgid = 0x17
        if reset_delay < 0:
            reset_delay = 0
        if reset_delay > 255:
            reset_delay = 255
        if por_reset:
            self.payload = bytes([reset_delay, 0, 1])
        else:
            self.payload = bytes([reset_delay, 0])
        self.hasresponse = True


class ResetResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def loadbytes(self, data):
        super().loadbytes(data)

    def __str__(self):
        return self.payload.hex()


class SendNewEventRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 6
        self.msgid = 7
        # self.eventid = eventid
        self.payload = self.getpayload()

    def getpayload(self):
        return struct.pack('<B', 1)


class SendNewEventResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.result = 0


class SendEventRequest(CommandBase):
    def __init__(self, eventid=1005, delay_ms=0):
        super().__init__()
        self.moduleid = 6
        self.msgid = 0
        self.eventid = eventid
        self.delay_ms = delay_ms

    def getpayload(self):
        if self.delay_ms:
            return struct.pack('<2H', self.eventid, self.delay_ms)
        else:
            return struct.pack('<H', self.eventid)


class SendEventResponse(CommandBase):
    def __init__(self):
        super().__init__()


class WriteAncCoeffToFlashRequest(CommandBase):
    def __init__(self, pkg_size: int, idx: int, data: bytes):
        super().__init__()
        self.moduleid = 8
        self.msgid = 9
        self.idx = idx
        self.len = pkg_size + 1
        self.payload = data

    def getpayload(self):
        return struct.pack('<B', self.idx) + self.payload

    def __str__(self):
        return 'payload={0}'.format(self.payload.hex())


class WriteAncCoeffToFlashResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def loadbytes(self, data):
        return super().loadbytes(data)

    def __str__(self):
        return self.payload.hex()


class AncSetCoeffParamRequest(CommandBase):
    def __init__(self, section_idx: int, ramp_cnt: int, offset: int, data_len: int, data: bytes):
        super().__init__()
        self.moduleid = 8
        self.msgid = 0
        self.section_idx = section_idx
        self.ramp_cnt = ramp_cnt
        self.offset = offset
        self.len = data_len
        self.payload = data

    def getpayload(self):
        return struct.pack('<BBHH', self.section_idx, self.ramp_cnt, self.offset, self.len) + self.payload

    def __str__(self):
        return 'payload={0}'.format(self.payload.hex())


class AncSetCoeffParamResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def loadbytes(self, data):
        return super().loadbytes(data)

    def __str__(self):
        return self.payload.hex()


class ReadAncCoeffFromFlashRequest(CommandBase):
    def __init__(self, idx: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 16
        self.idx = idx

    def getpayload(self):
        return struct.pack('<B', self.idx)

    def __str__(self):
        return 'payload={0}'.format(self.payload.hex())


class ReadAncCoeffFromFlashResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def loadbytes(self, data):
        return super().loadbytes(data)

    def __str__(self):
        return self.payload.hex()


# check anc coeff
class CheckAncCoeffFromFlashRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 8
        self.msgid = 10
        self.payload = self.getpayload()

    def getpayload(self):
        return struct.pack('<B', 0)


class CheckAncCoeffFromFlashResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.result = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        self.result = struct.unpack(
            '<B', self.payload)

    def __str__(self):
        return 'payload={0}'.format(self.payload)


# open anc port
class AncPortOpenRequest(CommandBase):
    def __init__(self, ancMode: int = 3, switch_mode=0, chip_mode=0):
        super().__init__()
        self.moduleid = 8
        self.msgid = 11
        self.ancMode = ancMode
        self.switch_mode = switch_mode
        self.chip_mode = chip_mode
        self.payload = self.getpayload()

    def getpayload(self):
        if self.chip_mode == 0:
            return struct.pack('<B', self.ancMode)
        else:
            return struct.pack('<2B', self.ancMode, self.switch_mode)


class AncPortOpenResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.result = 0

    def loadbytes(self, data):
        super().loadbytes(data)

    def __str__(self):
        return 'payload={0}'.format(self.payload)


# close anc port
class AncPortCloseRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 8
        self.msgid = 12

    def getpayload(self):
        return struct.pack('<B', 0)


class AncPortCloseResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.result = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        self.result = struct.unpack('<B', self.payload)

    def __str__(self):
        return 'payload={0}'.format(self.payload)


class SendImproveFreq(CommandBase):
    def __init__(self, freq_mode: int = 4):
        super().__init__()
        self.moduleid = 4
        self.msgid = 24
        self.freq_mode = freq_mode

    def getpayload(self):
        return struct.pack('<B', self.freq_mode)


class SendImproveFreqResponse(CommandBase):
    def __init__(self):
        super().__init__()


class CloseDeepsleepRequest(CommandBase):
    def __init__(self, core_id: int):
        super().__init__()
        self.moduleid = 5
        self.msgid = 4
        self.core_id = core_id

    def getpayload(self):
        return struct.pack('<IIB', 0xFFFFFFFF, 0xFFFFFFFF, self.core_id)


class CloseDeepsleepResponse(CommandBase):
    def __init__(self):
        super().__init__()


class EnableDeepsleepRequest(CommandBase):
    def __init__(self, core_id: int):
        super().__init__()
        self.moduleid = 5
        self.msgid = 4
        self.core_id = core_id

    def getpayload(self):
        return struct.pack('<IIB', 0x3C, 0xFFFFFFFF, self.core_id)


class EnableDeepsleepResponse(CommandBase):
    def __init__(self):
        super().__init__()


class AdkEnterAudioTestModeRequest(CommandBase):
    def __init__(self, disable_bt_flag=0, disable_tone_flag=0):
        super().__init__()
        self.moduleid = 6
        self.msgid = 45
        self.info = disable_bt_flag + disable_tone_flag * 2

    def getpayload(self):
        return struct.pack('<B', self.info)


class AdkEnterAudioTestModeResponse(CommandBase):
    def __init__(self):
        super().__init__()


class AdkGetAudioTestStateRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 6
        self.msgid = 46


class AdkGetAudioTestStateResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.is_in_audio_test_mode = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        if len(self.payload) == 1:
            tmp = struct.unpack('<B', self.payload)
            self.is_in_audio_test_mode = tmp[0]

# TwsPairing
class EnterTwsPairingRequest(CommandBase):
    def __init__(self, magic: int):
        super().__init__()
        self.moduleid = 6
        self.msgid = 5
        self.magic = magic

    def getpayload(self):
        return struct.pack('<B', self.magic)


class EnterTwsPairingResponse(CommandBase):
    def __init__(self):
        super().__init__()


class SendRFDUTYRequest(CommandBase):
    def __init__(self, powerlevel: int = 2, duty_mode: int = 0):
        super().__init__()
        self.moduleid = 6
        self.msgid = 3
        # self.eventid = eventid
        self.powerlevel = powerlevel
        self.duty_mode = duty_mode
        self.payload = self.getpayload()

    def getpayload(self):
        if self.duty_mode == 1:
            on_duty = 1
            off_duty = 1
        else:
            if self.duty_mode == 2:
                on_duty = 2
                off_duty = 6
            else:
                on_duty = 2
                off_duty = 5
        return struct.pack('<HBBBBBHHH', 64677, 10, 0, 1, self.powerlevel, 10, on_duty, off_duty, 100)


class SendRFDUTYResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.result = 0


class SendLogRequest(CommandBase):
    def __init__(self, module: int = 0, loglevel: int = 0):
        super().__init__()
        self.moduleid = 4
        self.msgid = 25
        self.module = module
        self.loglevel = loglevel
        self.payload = self.getpayload()
        # print(self.payload)

    def getpayload(self):
        return struct.pack('<BBH', self.module, self.loglevel, 0)


class SendLogResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.result = 0


class HandshakeRequest(CommandBase):
    def __init__(self, hs_pld: bytes):
        super().__init__()
        self.moduleid = 8
        self.msgid = 14
        self.len = 3
        self.payload = hs_pld


class HandshakeResponse(CommandBase):
    def __init__(self):
        super().__init__()


class SetLogLvlRequest(CommandBase):
    def __init__(self, lvl_pld: int):
        super().__init__()
        self.moduleid = 4
        self.msgid = 25
        self.len = 4
        self.payload = lvl_pld


class SetLogLvlResponse(CommandBase):
    def __init__(self):
        super().__init__()


class SetLogSwitchRequest(CommandBase):
    '''
    @mid： moduleid
    @level: log velvel
    '''

    def __init__(self, mid: int = 1, level: int = 1):
        super().__init__()
        self.moduleid = 4
        self.msgid = 25
        self.mid = mid
        self.level = level

    def getpayload(self):
        return struct.pack('<4B', self.mid, self.level, 0, 0)


class SetLogSwitchResponse(CommandBase):
    pass


class VadStartRequest(CommandBase):
    def __init__(self, dumpFlg: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 300
        self.len = 1
        self.dumpFlg = dumpFlg

    def getpayload(self):
        return struct.pack('<B', self.dumpFlg)


class VadStartResponse(CommandBase):
    def __init__(self):
        super().__init__()


class VadStopRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 8
        self.msgid = 301


class VadStopResponse(CommandBase):
    def __init__(self):
        super().__init__()


class EncMicSwitchRequest(CommandBase):
    def __init__(self, pld: bytes):
        super().__init__()
        self.moduleid = 8
        self.msgid = 250
        self.len = 4
        self.payload = pld


class EncMicSwitchResponse(CommandBase):
    def __init__(self):
        super().__init__()


class VoiceAlgrithmEnableControlSetRequest(CommandBase):
    def __init__(self, pld: bytes):
        super().__init__()
        self.moduleid = 8
        self.msgid = 212
        self.len = 4
        self.payload = pld


class VoiceAlgrithmEnableControlSetResponse(CommandBase):
    def __init__(self):
        super().__init__()


class GetBdAddrRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 6
        self.msgid = 4


class GetBdAddrResponse(CommandBase):
    def __init__(self):
        super().__init__()


class GetBatteryStateRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 6
        self.msgid = 9


class GetBatteryStateResponse(CommandBase):
    def __init__(self):
        super().__init__()


class WriteEsCoeffToFlashRequest(CommandBase):
    def __init__(self, pkg_size: int, idx: int, data: bytes):
        super().__init__()
        self.moduleid = 8
        self.msgid = 252
        self.idx = idx
        self.len = pkg_size + 1
        self.data = data

    def getpayload(self):
        return struct.pack('<B', self.idx) + self.data

    def __str__(self):
        return 'payload={0}'.format(self.payload.hex())


class WriteEsCoeffToFlashResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def loadbytes(self, data):
        return super().loadbytes(data)

    def __str__(self):
        return self.payload.hex()


class ReadEsCoeffFromFlashRequest(CommandBase):
    def __init__(self, idx: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 251
        self.len = 1
        self.idx = idx

    def getpayload(self):
        return struct.pack('<B', self.idx)


class ReadEsCoeffFromFlashResponse(CommandBase):
    def __init__(self):
        super().__init__()


class BeetlePlusWriteRespOemRequest(CommandBase):
    def __init__(self, offset: int, byte_len: int, data: bytes):
        super().__init__()
        self.moduleid = 8
        self.msgid = 259
        self.offset = offset
        self.byte_len = byte_len
        self.data = data

    def getpayload(self):
        return struct.pack('<2H', self.offset, self.byte_len) + self.data

    def __str__(self):
        return 'payload={0}'.format(self.payload.hex())


class BeetlePlusWriteRespOemResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def loadbytes(self, data):
        return super().loadbytes(data)

    def __str__(self):
        return self.payload.hex()


class BeetlePlusReadRespOemRequest(CommandBase):
    def __init__(self, offset: int, byte_len: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 260
        self.offset = offset
        self.byte_len = byte_len

    def getpayload(self):
        return struct.pack('<2H', self.offset, self.byte_len)


class BeetlePlusReadRespOemResponse(CommandBase):
    def __init__(self):
        super().__init__()

class SetAncStateRequest(CommandBase):
    '''don't use this instead of SetAncModeAndLevelRequest
    '''
    def __init__(self, ancState: int):
        super().__init__()
        self.moduleid = 6
        self.msgid = 1
        self.app_msg_type = 4
        self.app_msg_id = 1
        self.app_param = ancState

    def getpayload(self):
        return struct.pack('<HHB', self.app_msg_type, self.app_msg_id, self.app_param)


class SetAncStateResponse(CommandBase):
    def __init__(self):
        super().__init__()


class SetAncLevelRequest(CommandBase):
    '''don't use this instead of SetAncModeAndLevelRequest
    '''
    def __init__(self, anc_strategy: int, level: int):
        assert anc_strategy == 2 or anc_strategy == 3  # 2: set anc level; 3: set trans level
        super().__init__()
        self.moduleid = 6
        self.msgid = 1
        self.app_msg_type = 4
        self.app_msg_id = anc_strategy
        self.app_param = level

    def getpayload(self):
        return struct.pack('<HHB', self.app_msg_type, self.app_msg_id, self.app_param)


class SetAncLevelResponse(CommandBase):
    def __init__(self):
        super().__init__()

class SetAncModeAndLevelRequest(CommandBase):
    def __init__(self,mode:int,level:int):
        super().__init__()
        self.moduleid = 6
        self.msgid = 37
        self.mode = mode
        self.level = level
    def getpayload(self):
        return struct.pack('<2B', self.mode, self.level)
class SetAncModeAndLevelResponse(CommandBase):
    def __init__(self):
        super().__init__()

class TriggerLeakAncRequest(CommandBase):
    def __init__(self,mode:int = 1):
        super().__init__()
        self.moduleid = 6
        self.msgid = 38
        self.mode = mode
    def getpayload(self):
        return struct.pack('<B', self.mode)
class TriggerLeakAncResponse(CommandBase):
    def __init__(self):
        super().__init__()

class EnableHciPassthroughRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 0x6
        self.msgid = 0x7
        self.payload = bytes([0x01])


class EnableHciPassthroughResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def loadbytes(self, data):
        return super().loadbytes(data)

    def __str__(self):
        return self.payload.hex()


class GetTwsStateRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 0x6
        self.msgid = 0x8


class GetTwsStateResponse(CommandBase):
    def __init__(self):
        super().__init__()


class TurnOffBtSleepRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 0x6
        self.msgid = 0x3
        self.payload = bytes([0x69, 0xfc, 0x00])


class TurnOffBtSleepResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def loadbytes(self, data):
        return super().loadbytes(data)

    def __str__(self):
        return self.payload.hex()


# 获取oem Mac Address
class GetOEMAddrRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 6
        self.msgid = 14


class GetOEMAddrResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.address = b''

    def loadbytes(self, data: bytes):
        super().loadbytes(data)
        self.address = self.payload

    def __str__(self):
        return self.address[::-1].hex()  # 倒序


# 设置对端地址
class SetPEERAddrRequest(CommandBase):
    def __init__(self, peerMAC: bytes):
        super().__init__()
        self.moduleid = 6
        self.msgid = 13
        self.peerMAC = peerMAC

    def getpayload(self):
        return self.peerMAC


class SetPEERAddrResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.address = b''

    def loadbytes(self, data: bytes):
        super().loadbytes(data)
        self.address = self.payload

    def __str__(self):
        return self.address[::-1].hex()  # 倒序


# 获取 fw 版本信息
class GetFWVersionRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 4
        self.msgid = 27


class GetFWVersionResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.versioninfo = ''

    def loadbytes(self, data: bytes):
        super().loadbytes(data)
        self.versioninfo = bytes.decode(
            self.payload, encoding='utf-8', errors='ignore').strip('\0')

# 获取ate 版本信息


class GetATEVerRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 4
        self.msgid = 28


class GetATEVerResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.ate_ver_major = 0
        self.ate_ver_minor = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        if len(self.payload) == 4:
            self.ate_ver_major, self.ate_ver_minor = struct.unpack(
                '<HH', self.payload[0:4])


class GetDeviceIdRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 4
        self.msgid = 38


class GetDeviceIdResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.device_id_idx = -1

    def loadbytes(self, data):
        super().loadbytes(data)
        if len(self.payload) == 1:
            self.device_id_idx = struct.unpack('<B', self.payload)[0]


class GetCustomVerRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 6
        self.msgid = 23


class GetCustomVerResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.custom_ver = 0
        self.custom_peer_ver = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        if len(self.payload) == 4:
            self.custom_ver, self.custom_peer_ver = struct.unpack(
                '<HH', self.payload[0:4])


class ReadKVRequest(CommandBase):
    def __init__(self, kv_module_id: int, key_id: int):
        super().__init__()
        self.moduleid = 4
        self.msgid = 18
        self.kv_module_id = kv_module_id
        self.key_id = key_id

    def getpayload(self):
        return struct.pack('<II', self.kv_module_id, self.key_id)


class ReadKVResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.kv_module_id = 0
        self.key_id = 0
        self.kv_length = 0
        self.kv_data = b''
        self.updated = False

    def loadbytes(self, data):
        super().loadbytes(data)
        if len(self.payload) > 12:
            self.kv_module_id, self.key_id, self.kv_length = struct.unpack(
                '<III', self.payload[0:12])
            self.kv_data = self.payload[12:]
            self.updated = True

    def check(self, mykvrequest):
        if self.updated and (self.key_id == mykvrequest.key_id):
            return True
        return False


class SetKVRequest(CommandBase):
    def __init__(self, kv_module_id: int, key_id: int, data: bytes):
        super().__init__()
        self.moduleid = 4
        self.msgid = 17
        self.kv_module_id = kv_module_id
        self.key_id = key_id
        self.data = data
        self.datalen = len(data)

    def getpayload(self):
        return struct.pack('<III', self.kv_module_id, self.key_id, self.datalen) + self.data


class SetKVResponse(CommandBase):
    def __init__(self):
        super().__init__()


class StoreDumpProcRequest(CommandBase):
    def __init__(self, mic_idx: int, mode_16bit: int, dump_time: int, beetle_plus_flag=False):
        super().__init__()
        self.beetle_plus_flag = beetle_plus_flag
        self.moduleid = 8
        self.msgid = 19
        if self.beetle_plus_flag is False:
            self.mic_idx = mic_idx
        else:
            self.mic_idx = mic_idx & 0xff
            self.mic_idx1 = mic_idx >> 8
            self.dump_time = dump_time
        self.mode_16bit = mode_16bit

    def getpayload(self):
        if self.beetle_plus_flag is False:
            return struct.pack('<BB', self.mic_idx, self.mode_16bit)
        else:
            return struct.pack('<4B', self.mic_idx, self.mic_idx1, self.mode_16bit, self.dump_time)


class StoreDumpProcResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.result = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        if len(self.payload) == 1:
            self.result = struct.unpack('<B', self.payload)
        else:
            self.result = 1

    def __str__(self):
        return 'payload={0}'.format(self.payload)


class HciRequest(CommandBase):
    def __init__(self, payload: bytes = b''):
        super().__init__()
        self.moduleid = 6
        self.msgid = 3
        self.payload = payload


class HciResponse(CommandBase):
    def __init__(self):
        super().__init__()


class SetTxPowerRequest(CommandBase):
    def __init__(self, powerlevel: int = 2):
        super().__init__()
        self.moduleid = 6
        self.msgid = 2
        self.rpcid = 0x2f #rpc id :set fix tx power
        self.type = 0  # type
        self.powerlevel = powerlevel #range[0,5]

    def getpayload(self):
        return struct.pack('<I2B', self.rpcid, self.type, self.powerlevel)


class SetTxPowerResponse(CommandBase):
    def __init__(self):
        super().__init__()


class AncGainCalibrationRequest(CommandBase):
    def __init__(self, set_flag: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 28
        self.set_flag = set_flag

    def getpayload(self):
        return struct.pack('<B', self.set_flag)


class AncGainCalibrationResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class AncGainCalibrationParamConfigRequest(CommandBase):
    def __init__(self, detect_frame_num: int, work_mode: int, target_freq_idx: int, reserved: int = 0):
        super().__init__()
        self.moduleid = 8
        self.msgid = 34
        self.detect_frame_num = detect_frame_num
        self.work_mode = work_mode
        self.target_freq_idx = target_freq_idx
        self.reserved = reserved

    def getpayload(self):
        return struct.pack('<4B',
                           self.detect_frame_num,
                           self.work_mode,
                           self.target_freq_idx,
                           self.reserved)


class AncGainCalibrationParamConfigResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class FitTestSetRequest(CommandBase):
    def __init__(self, set_flag: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 25
        self.set_flag = set_flag

    def getpayload(self):
        return struct.pack('<B', self.set_flag)


class FitTestSetResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class FitTestParamConfigRequest(CommandBase):
    def __init__(self, ten_frame_cnt: int, high_thr_hw: int, low_thr_hw: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 26
        self.ten_frame_cnt = ten_frame_cnt
        self.high_thr_hw = high_thr_hw
        self.low_thr_hw = low_thr_hw

    def getpayload(self):
        return struct.pack('<5B',
                           self.ten_frame_cnt,
                           self.high_thr_hw // 256,
                           self.high_thr_hw % 256,
                           self.low_thr_hw // 256,
                           self.low_thr_hw % 256)


class FitTestParamConfigResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class FitTestAppStartRequest(CommandBase):
    def __init__(self, start_flag: int):
        # start_flag: 0:stop ; 1: start
        super().__init__()
        self.moduleid = 6
        self.msgid = 40
        self.start_flag = start_flag

    def getpayload(self):
        return struct.pack('<B', self.start_flag)


class FitTestAppStartResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class ToneDetAppStartRequest(CommandBase):
    def __init__(self, start_flag: int):
        # start_flag: 0:stop ; 1: start
        super().__init__()
        self.moduleid = 6
        self.msgid = 42
        self.start_flag = start_flag

    def getpayload(self):
        return struct.pack('<B', self.start_flag)


class ToneDetAppStartResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class AncFunctionStartRequest(CommandBase):
    def __init__(self, func_id: int, start_flag: int, param: int):
        # start_flag: 0:stop ; 1: start
        super().__init__()
        self.moduleid = 8
        self.msgid = 36
        self.func_id = func_id
        self.start_flag = start_flag
        self.param = param

    def getpayload(self):
        return struct.pack('<3B', self.func_id, self.start_flag, self.param)


class AncFunctionStartResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class AncFunctionParamCfgRequest(CommandBase):
    def __init__(self, func_id: int, param_payload: bytes):
        super().__init__()
        self.moduleid = 8
        self.msgid = 37
        self.func_id = func_id
        self.payload = param_payload

    def getpayload(self):
        return struct.pack('<B', self.func_id) + self.payload


class AncFunctionParamCfgResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class AncFunctionResultGetRequest(CommandBase):
    def __init__(self, func_id):
        super().__init__()
        self.moduleid = 8
        self.msgid = 38
        self.func_id = func_id
        self.payload = self.getpayload()

    def getpayload(self):
        return struct.pack('<B', self.func_id)


class AncFunctionResultGetResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class AdaptiveAncEnvStartRequest(CommandBase):
    def __init__(self, start_flag: int, channel: int = 0xFF):
        # set_flag: 0:stop ; 1: start
        super().__init__()
        self.moduleid = 8
        self.msgid = 30
        self.start_flag = start_flag
        self.channel = channel

    def getpayload(self):
        if self.channel == 0xFF:
            return struct.pack('<B', self.start_flag)
        else:
            return struct.pack('<2B', self.start_flag, self.channel)


class AdaptiveAncEnvStartResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class AdaptiveAncEnvParamConfigRequest(CommandBase):
    def __init__(self,
                 detect_period: int,
                 a_weight_flag: int,
                 low_freq_ratio: int,
                 mic_data_packet_num: int,
                 low_thr: int,
                 low_freq_db_thr: int,
                 pingpong_val: int,
                 high_thr: int):
        # detect_period: unit s
        super().__init__()
        self.moduleid = 8
        self.msgid = 31
        self.detect_period = detect_period
        self.a_weight_flag = a_weight_flag
        self.low_freq_ratio = low_freq_ratio
        self.mic_data_packet_num = mic_data_packet_num
        self.low_thr = low_thr
        self.low_freq_db_thr = low_freq_db_thr
        self.pingpong = pingpong_val
        self.high_thr = high_thr

    def getpayload(self):
        return struct.pack('<3BH5B',
                           self.detect_period,
                           self.a_weight_flag,
                           self.low_freq_ratio,
                           self.mic_data_packet_num,
                           self.low_thr,
                           self.low_freq_db_thr,
                           self.pingpong,
                           self.high_thr,
                           0)


class AdaptiveAncEnvParamConfigResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class FitTestResultGetRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 8
        self.msgid = 27
        self.payload = self.getpayload()

    def getpayload(self):
        return struct.pack('<B', 0)


class FitTestResultGetResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class GainCalibrationResultGetRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 8
        self.msgid = 35
        self.payload = self.getpayload()

    def getpayload(self):
        return struct.pack('<B', 0)


class GainCalibrationResultGetResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class MicBiasSetRequest(CommandBase):
    def __init__(self, mic_bias_cfg):
        super().__init__()
        self.moduleid = 8
        self.msgid = 29
        self.mic_bias_cfg = mic_bias_cfg

    def getpayload(self):
        return struct.pack('<B', self.mic_bias_cfg)


class MicBiasSetResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class StartSignalToneRequest(CommandBase):
    def __init__(self, freq_high: int, freq_low: int, range_high: int, range_low: int,
                 spk_idx: int=0, both_spk_flag: int=0):
        super().__init__()
        self.moduleid = 8
        self.msgid = 17
        self.freq_high = freq_high + both_spk_flag * 2 ** 6 + spk_idx * 2 ** 7
        self.freq_low = freq_low
        self.range_high = range_high
        self.range_low = range_low

    def getpayload(self):
        return struct.pack('<4B', self.freq_high, self.freq_low, self.range_high, self.range_low)


class StartSignalToneResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class StartSignalToneAdkRequest(CommandBase):
    def __init__(self, signal_freq: int = 0, signal_type: int = 0, signal_gain: int = 0):
        super().__init__()
        self.moduleid = 8
        self.msgid = 17
        self.signal_freq = signal_freq
        self.signal_gain = signal_gain
        self.signal_type = signal_type

    def getpayload(self):
        return struct.pack('<HhB', self.signal_freq, self.signal_gain, self.signal_type)


class StartSignalToneAdkResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class StopSignalToneRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 8
        self.msgid = 18


class StopSignalToneResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class SwitchToneRequest(CommandBase):
    def __init__(self, StopTone_flag_val: int):
        super().__init__()
        self.moduleid = 6
        self.msgid = 18
        self.StopTone_flag = StopTone_flag_val

    def getpayload(self):
        return struct.pack('<B', self.StopTone_flag)


class SwitchToneResponse(CommandBase):
    def __init__(self):
        super().__init__()


class EsEqBypassRequest(CommandBase):
    def __init__(self, bypass_flag: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 214
        self.bypass_flag = bypass_flag

    def getpayload(self):
        return struct.pack('<B', self.bypass_flag)


class EsEqBypassResponse(CommandBase):
    def __init__(self):
        super().__init__()


class SetPDLRequest(CommandBase):
    def __init__(self, peerMAC: str):
        super().__init__()
        self.moduleid = 4
        self.msgid = 17
        self.peerMAC = peerMAC

    def getpayload(self):
        return bytes.fromhex(f'000D0000020D00003100000001{self.peerMAC}000000000000000000000000000000000000000000000000000000000000000000000000000000000000')


class SetPDLResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def loadbytes(self, data):
        return super().loadbytes(data)

    def __str__(self):
        return self.payload.hex()


class SetLinkKeyRequest(CommandBase):
    def __init__(self, peerMAC: str, linkkey: str):
        super().__init__()
        self.moduleid = 4
        self.msgid = 17
        self.peerMAC = peerMAC
        self.linkkey = linkkey

    def getpayload(self):
        return bytes.fromhex(f'000C0000600C000016000000{self.peerMAC}{self.linkkey}')


class SetLinkKeyResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def loadbytes(self, data):
        return super().loadbytes(data)

    def __str__(self):
        return self.payload.hex()


class SpkMicDumpEnableRequest(CommandBase):
    def __init__(self, enable_flag: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 215
        self.enable_flag = enable_flag

    def getpayload(self):
        return struct.pack('<B', self.enable_flag)


class SpkMicDumpEnableResponse(CommandBase):
    def __init__(self):
        super().__init__()


class GetMusicParamqRequest(CommandBase):
    def __init__(self, type: int = 0, param_payload=None):
        super().__init__()
        self.moduleid = 8
        self.msgid = 206
        self.type = type
        self.param_payload = param_payload

    def getpayload(self):
        if self.param_payload is not None:
            return struct.pack('<B', self.type) + self.param_payload
        else:
            return struct.pack('<B', self.type)


class GetMusicParamqResponse(CommandBase):
    def __init__(self):
        super().__init__()


class CommitMusicParamqRequest(CommandBase):
    def __init__(self, type: int, data: bytes):
        super().__init__()
        self.moduleid = 8
        self.msgid = 210
        self.type = type
        self.data = data

    def getpayload(self):
        return struct.pack('<B', self.type) + self.data


class CommitMusicParamqResponse(CommandBase):
    def __init__(self):
        super().__init__()


class TryMusicParamqRequest(CommandBase):
    def __init__(self, type: int, data: bytes, dest: CLI_DEST=CLI_DEST.LOCAL):
        super().__init__()
        self.moduleid = 8
        self.msgid = 208
        self.type = type
        self.data = data
        self.ack = dest << 4

    def getpayload(self):
        return struct.pack('<B', self.type) + self.data


class TryMusicParamqResponse(CommandBase):
    def __init__(self):
        super().__init__()


# set audio dump transmission io method
class SetAudioDumpTransIoMethodRequest(CommandBase):
    def __init__(self, trans_io_mode: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 20
        self.trans_io_mode = trans_io_mode

    def getpayload(self):
        return struct.pack('<B', self.trans_io_mode)


class SetAudioDumpTransIoMethodResponse(CommandBase):
    def __init__(self):
        super().__init__()


# set spp audio dump parameter
class SetSppAudioDumpParamRequest(CommandBase):
    def __init__(self, dump_delay_ms: int, need_ack: int, pkt_size: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 23
        self.dump_delay_ms = dump_delay_ms
        self.need_ack = need_ack
        self.pkt_size = pkt_size

    def getpayload(self):
        byte1 = self.dump_delay_ms & 0x7f
        byte1 = byte1 + ((self.need_ack << 7) & 0x80)
        return struct.pack('<BH', byte1, self.pkt_size)


class SetSppAudioDumpParamResponse(CommandBase):
    def __init__(self):
        super().__init__()


# set adaptive ANC dump parameter
class AncSwitchDelayTimeSetRequest(CommandBase):
    def __init__(self, delay_time: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 24
        self.delay_time = delay_time

    def getpayload(self):
        return struct.pack('<2B', self.delay_time // 256, self.delay_time % 256)


class AncSwitchDelayTimeSetResponse(CommandBase):
    def __init__(self):
        super().__init__()


class StartAudioLoopBackRequest(CommandBase):
    def __init__(self, bitmap, spk_info=0, sample_rate=0):
        super().__init__()
        self.moduleid = 8
        self.msgid = 21
        self.bitmap = bitmap
        self.spk_info = spk_info
        self.sample_rate = sample_rate

    def getpayload(self):
        if self.sample_rate <= 16000:
            return struct.pack('<BB', self.bitmap, self.spk_info)
        else:
            return struct.pack('<BBI', self.bitmap, self.spk_info, self.sample_rate)


class StartAudioLoopBackResponse(CommandBase):
    def __init__(self):
        super().__init__()


class StopAudioLoopBackRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 8
        self.msgid = 22


class StopAudioLoopBackResponse(CommandBase):
    def __init__(self):
        super().__init__()


class EnableTouchCDCTestRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 6
        self.msgid = 16


class EnableTouchCDCTestResponse(CommandBase):
    def __init__(self):
        super().__init__()


class EqSoftDrcParamSetRequest(CommandBase):
    def __init__(self,
                 thr_high: int,
                 thr_middle: int,
                 thr_low: int,
                 release_high: int,
                 release_low: int,
                 attack: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 216
        self.thr_high = thr_high
        self.thr_middle = thr_middle
        self.thr_low = thr_low
        self.release_high = release_high
        self.release_low = release_low
        self.attack = attack

    def getpayload(self):
        return struct.pack('<6B',
                           self.thr_high, self.thr_middle, self.thr_low,
                           self.release_high, self.release_low, self.attack)


class EqSoftDrcParamSetResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class EqSoftDrcParamSetAdkRequest(CommandBase):
    def __init__(self,
                 en: int,
                 thr: int,
                 release: int,
                 attack: int,
                 makeup_gain: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 216
        self.en = en
        self.thr = thr
        self.rel = release
        self.att = attack
        self.makeup = makeup_gain

    def getpayload(self):
        drc_reserved = [0 for _ in range(2)]
        drc_reserved_data = struct.pack("<2B", *drc_reserved)
        drc_cfg_data = struct.pack("<BBHHhh", self.en, 0, self.rel, self.att,
                                    int(self.thr * 100), int(self.makeup * 100))
        drc_cfg_data = drc_cfg_data + drc_reserved_data
        return drc_cfg_data


class EqSoftDrcParamSetAdkResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()

class SpkStreamGainSetRequest(CommandBase):
    def __init__(self,
                 stream_id: int,
                 gain_value: int,
                 force_gain: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 217
        assert 0 <= stream_id < 4
        self.stream_id = stream_id
        assert -128 <= gain_value <= 127
        if gain_value < 0:
            gain_value += 256
        self.gain_value = gain_value
        assert force_gain == 1 or force_gain == 0
        self.force_gain = force_gain

    def getpayload(self):
        return struct.pack('<BBB',
                           self.stream_id, self.gain_value, self.force_gain)


class SpkStreamGainSetResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class AncCallBackBypassRequest(CommandBase):
    def __init__(self, bypass_flag):
        super().__init__()
        self.moduleid = 8
        self.msgid = 218
        self.bypass_flag = bypass_flag

    def getpayload(self):
        return struct.pack('<B', self.bypass_flag)


class AncCallBackBypassResponse(CommandBase):
    def __init__(self):
        super().__init__()


class AncConfigFfFbLimitThrRequest(CommandBase):
    def __init__(self, ff_limit_thr, fb_limit_thr):
        super().__init__()
        self.moduleid = 8
        self.msgid = 40
        self.ff_limit_thr = ff_limit_thr
        self.fb_limit_thr = fb_limit_thr

    def getpayload(self):
        return struct.pack('<2f', self.ff_limit_thr, self.fb_limit_thr)


class AncConfigFfFbLimitThrResponse(CommandBase):
    def __init__(self):
        super().__init__()

class AncConfigSmoothSwitchRequest(CommandBase):
    def __init__(self, switch_frame_cnt_list, switch_done_wait_frame_cnt_list):
        super().__init__()
        self.moduleid = 8
        self.msgid = 55
        self.switch_frame_cnt_list = switch_frame_cnt_list
        self.switch_done_wait_frame_cnt_list = switch_done_wait_frame_cnt_list

    def getpayload(self):
        return (struct.pack('<7B', *self.switch_frame_cnt_list) +
                struct.pack('<7B', *self.switch_done_wait_frame_cnt_list))


class AncConfigSmoothSwitchResponse(CommandBase):
    def __init__(self):
        super().__init__()


class AncSetDrcTimeRequest(CommandBase):
    def __init__(self, lm_at_us, lm_rt_us, gm_at_us, gm_rt_us):
        super().__init__()
        self.moduleid = 8
        self.msgid = 53
        self.lm_at_us = lm_at_us
        self.lm_rt_us = lm_rt_us
        self.gm_at_us = gm_at_us
        self.gm_rt_us = gm_rt_us

    def getpayload(self):
        return struct.pack('<4I', self.lm_at_us, self.lm_rt_us, self.gm_at_us, self.gm_rt_us)


class AncSetDrcTimeResponse(CommandBase):
    def __init__(self):
        super().__init__()


class AncGetDrcTimeRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 8
        self.msgid = 54

    def getpayload(self):
        return struct.pack('<B', 0)


class AncGetDrcTimeResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.lm_at_us = 0
        self.lm_rt_us = 0
        self.gm_at_us = 0
        self.gm_rt_us = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        if len(self.payload) == 16:
            (self.lm_at_us, self.lm_rt_us, self.gm_at_us, self.gm_rt_us) = struct.unpack('<4I', self.payload)


class AncGetFfFbLimitThrRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 8
        self.msgid = 41

    def getpayload(self):
        return struct.pack('<B', 0)


class AncGetFfFbLimitThrResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.ff_limit_thr = 1
        self.fb_limit_thr = 1

    def loadbytes(self, data):
        super().loadbytes(data)
        if len(self.payload) == 8:
            tmp = struct.unpack('<2f', self.payload)
            self.ff_limit_thr = tmp[0]
            self.fb_limit_thr = tmp[1]


class GetChannelIdRequest(CommandBase):
    def __init__(self, path_id):
        super().__init__()
        self.moduleid = 8
        self.msgid = 253
        self.path_id = path_id

    def getpayload(self):
        return struct.pack('<B',
                           self.path_id)


class GetChannelIdResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.channel_id = -1

    def loadbytes(self, data):
        super().loadbytes(data)
        if len(self.payload) == 1:
            tmp = struct.unpack('<B', self.payload)
            self.channel_id = tmp[0]


# module ID 0x400 is special manament package for wuqi passthrough board###########################
# CMCPassthroughRequest send the payload with the intended baudrate to semi line no matter what the current
# semi baudrate is
#
class CMCPassthroughRequest(CommandBase):
    def __init__(self, baudrate: int, data_len: int, raw_string: str):
        super().__init__()
        self.moduleid = 0x400
        self.msgid = 1
        self.baudrate = baudrate
        self.data_len = data_len
        self.raw_string = raw_string
        self.hasresponse = False

    def getpayload(self):
        return struct.pack('<IB', self.baudrate, self.data_len) + bytes(self.raw_string, encoding='utf8')


class CMCPassthrougResponse(CommandBase):
    def __init__(self):
        super().__init__()


# SetPassthroughPortRateRequest set semi line baudrate
class SetPassthroughPortRateRequest(CommandBase):
    def __init__(self, baudrate: int):
        super().__init__()
        self.moduleid = 0x400
        self.msgid = 2
        self.baudrate = baudrate
        self.hasresponse = False

    def getpayload(self):
        return struct.pack('<I', self.baudrate)


class SetPassthroughPortRateResponse(CommandBase):
    def __init__(self):
        super().__init__()


# GetPassthroughFWVersionRequest get the passthrough board FW version
class GetPassthroughFWVersionRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 0x400
        self.msgid = 3


class GetPassthroughFWVersionResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.versioninfo = ''

    def loadbytes(self, data: bytes):
        super().loadbytes(data)
        # print(self.payload)
        if len(self.payload) > 1:
            self.versioninfo = bytes.decode(
                self.payload[1:], encoding='utf-8', errors='ignore').strip('\0')


# GetPassthroughPortRateRequest get the passthrough board semi port baudrate
class GetPassthroughPortRateRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 0x400
        self.msgid = 4


class GetPassthroughPortRateResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.portrate = 0

    def loadbytes(self, data):
        super().loadbytes(data)
        # print(self.payload)
        if len(self.payload) >= 4:
            [self.portrate] = struct.unpack('<I', self.payload)

# module ID 0x400 is special manament package for wuqi passthrough board###########################


class HowlingCfgRequest(CommandBase):
    def __init__(self, howling_en: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 219
        self.howling_en = howling_en

    def getpayload(self):
        return struct.pack('<B', self.howling_en)


class HowlingCfgResponse(CommandBase):
    def __init__(self):
        super().__init__()


class WindDetCfgRequest(CommandBase):
    def __init__(self, wind_detect_en: int):
        super().__init__()
        self.moduleid = 6
        self.msgid = 36
        self.wind_detect_en = wind_detect_en

    def getpayload(self):
        return struct.pack('<B', self.wind_detect_en)


class WindDetCfgResponse(CommandBase):
    def __init__(self):
        super().__init__()


class MusicFroceStreamGainLevelRequest(CommandBase):
    def __init__(self, gain_type: int, gain_level: int, force_en: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 220
        self.gain_type = gain_type
        self.gain_level = gain_level
        self.force_en = force_en

    def getpayload(self):
        return struct.pack('<3B', self.gain_type, self.gain_level, self.force_en)


class MusicFroceStreamGainLevelResponse(CommandBase):
    def __init__(self):
        super().__init__()


class GetChargeRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 6
        self.msgid = 15
        self.payload = bytes([0x00])


class GetChargeResponse(CommandBase):
    def __init__(self):
        super().__init__()


class TriggerCrashRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 4
        self.msgid = 4
        self.hasresponse = False
        self.payload = bytes([0x0, 0x0, 0x0, 0x0, 0x04, 0x04, 0x01])


class TriggerCrashResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def loadbytes(self, data):
        super().loadbytes(data)


class TriggerBTCrashRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 6
        self.msgid = 2
        self.hasresponse = False
        self.payload = bytes([0x01, 0x0, 0x0, 0x0, 0x01, 0x01, 0x01, 0x01])


class TriggerBTCrashResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def loadbytes(self, data):
        super().loadbytes(data)


class GetBatteryLevelRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 6
        self.msgid = 24


class GetBatteryLevelResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.bat_lvl = 0
        self.chg_stat = 0
        self.peer_bat_lvl = 0
        self.peer_chg_stat = 0
        self.updated = False

    def loadbytes(self, data):
        super().loadbytes(data)
        if len(self.payload) >= 4:
            [self.bat_lvl, self.chg_stat, self.peer_bat_lvl, self.peer_chg_stat] = struct.unpack('<BBBB', self.payload)
            self.updated = True


class EsReadFromFlashRefreshToRamRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 8
        self.msgid = 254


class EsReadFromFlashRefreshToRamResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class GetAncModeRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 8
        self.msgid = 33


class GetAncModeResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.anc_mode = -1

    def loadbytes(self, data):
        super().loadbytes(data)
        if len(self.payload) == 1:
            tmp = struct.unpack('<B', self.payload)
            self.anc_mode = tmp[0]


class DspTrParamCfgRequest(CommandBase):
    def __init__(self, switch_time: int, param_payload: bytes):
        super().__init__()
        self.moduleid = 8
        self.msgid = 39
        self.switch_time = switch_time
        self.payload = param_payload

    def getpayload(self):
        return struct.pack('<B', self.switch_time) + self.payload


class DspTrParamCfgResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()


class BeetlePlusSetAncCoeffRequest(CommandBase):
    def __init__(self, section_idx:int, end_flag:int, coeff_list:List[int], param_len:int, switch_frame_cnt:int, switch_mode:int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 42
        self.byte0 = section_idx + end_flag * 2 ** 7
        self.switch_mode = switch_mode
        self.param_len = param_len
        self.switch_frame_cnt = switch_frame_cnt
        self.coeff_list = coeff_list

    def getpayload(self):
        payload = (struct.pack('BBHH', self.byte0, self.switch_mode, self.switch_frame_cnt, self.param_len) +
                   struct.pack('%dI' % (len(self.coeff_list)), *self.coeff_list))
        return payload


class BeetlePlusSetAncCoeffResponse(CommandBase):
    def __init__(self):
        super().__init__()


class BeetlePlusWriteAncCoeffToFlashRequest(CommandBase):
    def __init__(self, section_idx: int, end_flag: int, data: bytes, param_len: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 9
        self.byte0 = section_idx + end_flag * 2 ** 7
        self.payload = data
        self.param_len = param_len

    def getpayload(self):
        payload = struct.pack('BBHH', self.byte0, 0, 0, self.param_len) + self.payload
        return payload


class BeetlePlusWriteAncCoeffToFlashResponse(CommandBase):
    def __init__(self):
        super().__init__()

class SwithLhdcLdacRequest(CommandBase):
    def __init__(self, ldac_or_lhdc: int, enable: bool = True):
        super().__init__()
        self.moduleid = 6
        self.msgid = 44
        self.switch = ldac_or_lhdc
        self.enable = enable
    def getpayload(self):
        return struct.pack('<2B', self.switch,1 if self.enable else 0)


class SwithLhdcLdacResponse(CommandBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.payload.hex()
class DCoreStream:
    def __init__(self,id:int,num:int,name :str) -> None:
        self.id :int = id
        self.num :int = num
        self.name :str = name
        self.processorlist:List[Processor]=[]
    def __str__(self) -> str:
        # for d in self.processorlist:
        #     print(f'{d}')
        return f'id={self.id},name={self.name},num={self.num}'
class Processor:
    def __init__(self,id:int,name :str) -> None:
        self.id:int = id
        self.name = name
    def __str__(self) -> str:
        return f'{self.name}({hex(self.id)})'
class SyncDCoreStreamRequest(CommandBase):
    def __init__(self,):
        super().__init__()
        self.moduleid = 8
        self.msgid = 322
class SyncDCoreStreamResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.dumpnames= ['TONE','MUSIC','CALL_UP','CALL_DOWN','AANC','LOOPBACK','FEEDBACK','REOORD','MIC','SIGNAL','LOOPBACK_RX','USB']
        self.dcorelist :List[DCoreStream]= []
    def loadbytes(self, data: bytes):
        super().loadbytes(data)
        if not self.payload:
            return
        index = 0
        while index < len(self.payload):
            id = int.from_bytes(self.payload[index:index+1],byteorder='little')
            num = int.from_bytes(self.payload[index+1:index+2],byteorder='little')
            #print(f'num={num}')
            name = self.dumpnames[id-1] if id>0 and id <= len( self.dumpnames) else 'unknown'
            ds =DCoreStream(id,num,name)
            index += 2
            for i in range(num):
                pid = i
                e_index = self.payload.find(b'\0',index)
                #print(f'e_index={e_index}')
                pname = bytes.decode(self.payload[index:e_index])
                p = Processor(pid,pname)
                ds.processorlist.append(p)
                index = e_index + 1
            self.dcorelist.append(ds)
    def __str__(self):
        # for d in self.dcorelist:
        #     print(f'{d}')
        return f''

class AdaptiveEQRequest(CommandBase):
    def __init__(self, param_payload: bytes):
        super().__init__()
        self.moduleid = 8
        self.msgid = 262
        self.payload = param_payload
    def getpayload(self):
        return self.payload
class AdaptiveEQResponse(CommandBase):
    def __init__(self):
        super().__init__()

class HearingProtectionRequest(CommandBase):
    def __init__(self,switch = True):
        super().__init__()
        self.moduleid = 6
        self.msgid = 43
        self.switch = switch
    def getpayload(self):
        return struct.pack('<B',1 if self.switch else 0)
class HearingProtectionResponse(CommandBase):
    def __init__(self):
        super().__init__()

class UsbInitRequest(CommandBase):
    def __init__(self,enable = True):
        super().__init__()
        self.moduleid = 4
        self.msgid = 43
        self.enable = enable
    def getpayload(self):
        return struct.pack('<B',1 if self.enable else 0)
class UsbInitResponse(CommandBase):
    def __init__(self):
        super().__init__()
class AUD_SV_Audio_SF(IntEnum):
    AUD_SV_AUDIO_SF_8000 = 1
    AUD_SV_AUDIO_SF_11025 = 2
    AUD_SV_AUDIO_SF_12000 = 3
    AUD_SV_AUDIO_SF_16000 = 4
    AUD_SV_AUDIO_SF_22050 = 5
    AUD_SV_AUDIO_SF_24000 = 6
    AUD_SV_AUDIO_SF_32000 = 7
    AUD_SV_AUDIO_SF_44100 = 8
    AUD_SV_AUDIO_SF_48000 = 9
    AUD_SV_AUDIO_SF_64000 = 10
    AUD_SV_AUDIO_SF_88200 = 11
    AUD_SV_AUDIO_SF_96000 = 12
    AUD_SV_AUDIO_SF_176400 = 13
    AUD_SV_AUDIO_SF_192000 = 14
    AUD_SV_AUDIO_SF_MAX = 15
class  SetAncSampleRateRequest(CommandBase):
    def __init__(self,sample_enum_val: int):
        super().__init__()
        self.moduleid = 8
        self.msgid = 46
        self.sample_rate = sample_enum_val
    def getpayload(self):
        return struct.pack('<B',self.sample_rate)
class SetAncSampleRateResponse(CommandBase):
    def __init__(self):
        super().__init__()


class WritePtGainToFlashRequest(CommandBase):
    def __init__(self, mode: int, filter_type: int, pt_gain: int):
        super().__init__()
        """
        mode: only support mode A B C D.
        filter type: ff -- 0, fb -- 1, ec -- 2.
        pt gain:For example, setting 1000 means setting 10.0db.
        """
        assert 0 <= mode <= 3
        assert filter_type in [0, 1, 2]
        self.moduleid = 8
        self.msgid = 43
        self.mode = mode
        self.filter_type = filter_type
        self.pt_gain = pt_gain

    def getpayload(self):
        return struct.pack('<2Bi', self.mode, self.filter_type, self.pt_gain)


class WritePtGainToFlashResponse(CommandBase):
    def __init__(self):
        super().__init__()


class ReadPtGainFromFlashRequest(CommandBase):
    def __init__(self, mode: int, filter_type: int):
        super().__init__()
        """
        mode: only support mode A B C D.
        filter type: ff -- 0, fb -- 1, ec -- 2.
        pt gain:For example, setting 1000 means setting 10.0db.
        """
        self.moduleid = 8
        self.msgid = 44
        assert 0 <= mode <= 3
        assert filter_type in [0, 1, 2]
        self.mode = mode
        self.filter_type = filter_type

    def getpayload(self):
        return struct.pack('<2B', self.mode, self.filter_type)


class ReadPtGainFromFlashResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.pt_gain = 0

    def loadbytes(self, data: bytes):
        super().loadbytes(data)
        if self.payload:
            self.pt_gain = struct.unpack('<i', self.payload)[0]


class AncUndateCoeffRequest(CommandBase):
    def __init__(self):
        super().__init__()
        self.moduleid = 8
        self.msgid = 45


class AncUndateCoeffResponse(CommandBase):
    def __init__(self):
        super().__init__()


class ReadAncCoeffParamRequest(CommandBase):
    def __init__(self,secnum = 0):
        super().__init__()
        self.moduleid = 8
        self.msgid = 47
        self.secnum = secnum
    def getpayload(self):
        return struct.pack('<B',self.secnum & 0x7F)

class ReadAncCoeffParamResponse(CommandBase):
    def __init__(self):
        super().__init__()
        self.section_num = 0
        self.end_section = 0
        self.ff_smooth_swith = 0
        self.switch_mode = 0
        self.switch_frame_cnt_l = 0
        self.switch_frame_cnt_h = 0
        self.total_len = 0
        self.param = b''
    def loadbytes(self, data):
        super().loadbytes(data)
        if not self.payload or len(self.payload) < 6:
            raise Exception(f'{self.__class__.__name__} Payload Len < 6')
        self.section_num = self.payload[0] &  0x7F
        self.end_section = self.payload[0] >> 7
        self.ff_smooth_swith = self.payload[1] &  1
        self.switch_mode = self.payload[1] >> 1
        self.switch_frame_cnt_l = self.payload[2]
        self.switch_frame_cnt_h = self.payload[3]
        [self.total_len] = struct.unpack('<H',self.payload[4:6])
        self.param = self.payload[6:]

class OTAReadAncCoeffParamRequest(ReadAncCoeffParamRequest):
    def __init__(self,secnum = 0):
        super().__init__(secnum)
        self.msgid = 60
class OTAReadAncCoeffParamResponse(ReadAncCoeffParamResponse):
    def __init__(self):
        super().__init__()

class OTAWriteAncCoeffParamRequest(BeetlePlusWriteAncCoeffToFlashRequest):
    def __init__(self, section_idx:int, end_flag:int, data:bytes, param_len:int):
        super().__init__(section_idx, end_flag, data, param_len)
        self.msgid = 61
class OTAWriteAncCoeffParamResponse(BeetlePlusWriteAncCoeffToFlashResponse):
    def __init__(self):
        super().__init__()
