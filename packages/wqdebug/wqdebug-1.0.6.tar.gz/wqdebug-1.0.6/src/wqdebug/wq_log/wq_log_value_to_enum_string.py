#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: wwdeng
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from elftools.elf.descriptions import describe_e_type
from elftools.dwarf.descriptions import describe_DWARF_expr
from elftools.dwarf.die import DIE



def get_die_name(die):
    """获取DIE的名称"""
    name_attr = die.attributes.get('DW_AT_name', None)
    if name_attr:
        return name_attr.value.decode() if isinstance(name_attr.value, bytes) else name_attr.value
    return None

def find_enum_type_die(die, dwarf_info):
    """递归查找枚举类型DIE"""
    print(f"find_enum_type_die: {die.tag}")
    if die.tag == 'DW_TAG_enumeration_type':
        return die

    type_attr = die.attributes.get('DW_AT_type', None)
    if type_attr:
        # 直接使用type_attr.value作为偏移量
        type_offset = type_attr.value + die.cu.cu_offset
        print(f"type_offset: 0x{type_offset:08X}")

        # 遍历所有编译单元查找目标DIE
        for CU in dwarf_info.iter_CUs():
            for target_die in CU.iter_DIEs():
                # print(f"target_die: {target_die.offset}")
                if target_die.offset == type_offset:
                    # print(f"find_die: {target_die.offset}")
                    return find_enum_type_die(target_die, dwarf_info)
    return None

def extract_from_elf(elf_path:str='tws_core0.elf', symbols:list[str]=['bt_cmd_t'], is_debug:bool=False):
    """从ELF文件中提取bt_cmd_t枚举信息"""
    print(f"extract_from_elf: {elf_path} symbols:{symbols}")
    try:
        symbols_enum_values = {}
        with open(elf_path, 'rb') as f:
            print(f"打开文件: {elf_path}")
            elf = ELFFile(f)

            if not elf.has_dwarf_info():
                print("ELF文件没有DWARF调试信息")
                return None

            print("开始处理DWARF信息...")
            dwarf = elf.get_dwarf_info()

            # 遍历所有编译单元
            for CU in dwarf.iter_CUs():
                # 遍历当前编译单元中的所有DIE
                for die in CU.iter_DIEs():
                    name = get_die_name(die)
                    # print(f"DIE名称: {name}")
                    if name not in symbols:
                        continue
                    print(f"\n编译单元: {CU.get_top_DIE().get_full_path()}")
                    if is_debug:
                        print(f"die: {die}")

                    if die.tag == 'DW_TAG_typedef':
                        # 获取实际的枚举类型
                        die = find_enum_type_die(die, dwarf)
                        if die is None:
                            continue
                        if is_debug:
                            print(f"find die: {die}")

                    if die.tag == 'DW_TAG_enumeration_type':
                        enum_values = {}
                        for child in die.iter_children():
                            if child.tag == 'DW_TAG_enumerator':
                                name_attr = child.attributes.get('DW_AT_name', None)
                                value_attr = child.attributes.get('DW_AT_const_value', None)
                                if name_attr and value_attr:
                                    enum_name = name_attr.value.decode() if isinstance(name_attr.value, bytes) else name_attr.value
                                    enum_value = value_attr.value
                                    if is_debug:
                                        print(f"  {enum_name} = {enum_value}")
                                    enum_values[str(enum_value)] = enum_name
                                    
                        symbols_enum_values[name] = enum_values
                        print(f"remove symbol: {name}")
                        symbols.remove(name)
        return symbols_enum_values

    except Exception as e:
        print(f"处理ELF文件时出错: {str(e)}")
        return None

if __name__ == '__main__':
    elf_path = '../test2/tws_acore.elf'
    obj_names = ['bt_cmd_t', 'app_msg_type_t']
    for obj_name in obj_names:
        enum_values = extract_from_elf(elf_path, obj_name)

        if enum_values:
            print(f"\n{obj_name}找到的枚举值:")
            for value, name in sorted(enum_values.items()):
                print(f"{value}: {name}")


# readelf --debug-dump=info tws_core0.elf | grep -A 5 -B 5 "bt_cmd_t"
# readelf --debug-dump=info tws_core0.elf | grep -A 50 "<0x912ae>"
# readelf --debug-dump=info tws_core0.elf | grep -A 50 "DW_TAG_enumeration_type" | grep -B 1 "BT_CMD_"
