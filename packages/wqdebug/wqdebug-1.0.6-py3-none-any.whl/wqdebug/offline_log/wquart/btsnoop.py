from io import TextIOWrapper
import struct
import time
import datetime
class SnoopHeader():
    def __init__(self) -> None:
        self.version:int = 1
        self.datalink:int = 0x03ea
    def getbytes(self)->bytes:
        return struct.pack('>2I',self.version,self.datalink)
class SnoopRecord():
    def __init__(self,data:bytes) -> None:
        self.cumdrops:int=0
        self.data=data
        self.timestamp:datetime = datetime.datetime.now()
    def getincllen(self)->int:
        if self.data:
            return len(self.data)-1
        return 0
    def getoriglen(self)->int:
        if self.data:
            return len(self.data)-1
        return 0
    def getflags(self)->int:
        f0= 1 if self.data[0]==0 else 0
        f1= 1 if self.data[1]==1 or self.data[1]==4 else 0
        return f1<<1 | f0
    def gettimestamp(self)->int:
        stamp= time.time() + 8*3600 # 东八区  得加回8小时
        return round(stamp *1000*1000) + 0x00dcddb30f2f8000
    def getdata(self):
        return self.data[1:]
    def getbytes(self)->bytes:
        return struct.pack('>4Iq',self.getoriglen(),self.getincllen(),self.getflags(),self.cumdrops,self.gettimestamp()) +self.getdata()
class BTSnoop():
    def __init__(self) -> None:
        self.header= SnoopHeader()
        self.writer:TextIOWrapper=None
    def createHeader(self,file:str = 'snoop.cfa'):
        if not self.writer:
            self.writer= open(file,'wb+')
            btsnoop_magic = b'btsnoop\0'
            self.writer.write(btsnoop_magic)
            hb= self.header.getbytes()
            self.writer.write(hb)
            self.writer.flush()
    def addRecord(self,data:bytes):
        if not data or len(data)<2:
            return
        if self.writer:
            pkg= SnoopRecord(data)
            cfa= pkg.getbytes()
            self.writer.write(cfa)
    def close(self):
        if self.writer and not self.writer.closed:
            self.writer.close()
        
