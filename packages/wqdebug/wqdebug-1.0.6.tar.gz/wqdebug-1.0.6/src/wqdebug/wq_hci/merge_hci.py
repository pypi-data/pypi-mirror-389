import os
import struct

class merge_btsnoop:
    CMD = "merge_hci"
    DESC = "合并btsnoop日志文件"  
    def __init__(self):
        pass

    def read_btsnoop_header(file):
        # 读取8字节标识符
        ident = file.read(8)
        if ident != b'btsnoop\x00':
            raise ValueError("Invalid BTSnoop file format")

        # 读取版本号(4字节)和数据链路类型(4字节)
        version = struct.unpack('>I', file.read(4))[0]
        datalink_type = struct.unpack('>I', file.read(4))[0]
        return version, datalink_type

    def write_btsnoop_header(file, version, datalink_type):
        # 写入文件头
        file.write(b'btsnoop\x00')
        file.write(struct.pack('>I', version))
        file.write(struct.pack('>I', datalink_type))

    def merge_btsnoop_files():
        output_file = 'merged_btsnoop.log'
        first_file = True

        # 遍历当前目录下的所有.log文件
        for filename in os.listdir('.'):
            if not filename.endswith('.log'):
                continue

            with open(filename, 'rb') as f:
                try:
                    # 读取文件头
                    version, datalink_type = read_btsnoop_header(f)

                    # 如果是第一个文件，创建新文件并写入文件头
                    if first_file:
                        with open(output_file, 'wb') as out:
                            write_btsnoop_header(out, version, datalink_type)
                        first_file = False

                    # 复制包记录
                    with open(output_file, 'ab') as out:
                        while True:
                            # 读取24字节的包记录头
                            record_header = f.read(24)
                            if not record_header or len(record_header) < 24:
                                break

                            # 获取包数据长度
                            included_length = struct.unpack('>I', record_header[4:8])[0]

                            # 读取包数据
                            packet_data = f.read(included_length)
                            if not packet_data or len(packet_data) < included_length:
                                break

                            # 写入完整的包记录
                            out.write(record_header)
                            out.write(packet_data)

                except Exception as e:
                    print(f"处理文件 {filename} 时出错: {str(e)}")
                    continue

if __name__ == '__main__':
    merge_btsnoop()
