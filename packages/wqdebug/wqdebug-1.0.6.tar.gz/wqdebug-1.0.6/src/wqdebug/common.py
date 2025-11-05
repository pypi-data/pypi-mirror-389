import os
import sys

def get_test_dir(test_dir="test"):
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 查找所有测试目录
    test_dirs = []
    for item in os.listdir(current_dir):
        if item.startswith("test"):
            full_path = os.path.join(current_dir, item)
            if os.path.isdir(full_path):
                test_dirs.append(item)
    
    if not test_dirs:
        print("未找到任何测试目录")
        sys.exit(1)
    
    # 如果指定了具体的测试目录
    if test_dir != "test":
        if test_dir not in test_dirs:
            print(f"测试目录 '{test_dir}' 不存在")
            print(f"可用的测试目录: {', '.join(test_dirs)}")
            sys.exit(1)
        selected_dir = test_dir
    else:
        # 如果只有一个测试目录，直接使用
        if len(test_dirs) == 1:
            selected_dir = test_dirs[0]
        else:
            # 让用户选择测试目录
            print("可用的测试目录:")
            for i, dir_name in enumerate(test_dirs):
                print(f"{i + 1}. {dir_name}")
            
            while True:
                try:
                    choice = input(f"请选择测试目录 (1-{len(test_dirs)}, 默认1): ").strip()
                    if not choice:
                        choice = 1
                    else:
                        choice = int(choice)
                    
                    if 1 <= choice <= len(test_dirs):
                        selected_dir = test_dirs[choice - 1]
                        break
                    else:
                        print(f"请输入 1 到 {len(test_dirs)} 之间的数字")
                except ValueError:
                    print("请输入有效的数字")
    
    test_dir = os.path.join(current_dir, selected_dir)
    return test_dir


def input_log_file(log: str = ""):
    user_input = input(
        f"log:\n{log}\n请拖入LOG文件或输入文件路径, 输入回车Enter使用推荐文件:\n"
    )
    if user_input == "":
        user_input = log
    
    while not os.path.isfile(user_input):
        print("文件路径不存在，请重新输入。")
        user_input = input_log_file(user_input)
    return user_input

def select_log_file(log: str = ""):
    if not os.path.isfile(log):
        # print(f"os.getcwd()={os.getcwd()}")
        # print(f"os.listdir('.')={os.listdir('.')}")
        log_files = []
        for file in os.listdir("."):
            if file.endswith(".log"):
                full_path = os.path.join(os.getcwd(), file)
                log_files.append((full_path, os.path.getmtime(full_path)))
        
        if log_files:
            # 按修改时间排序，使用最新的文件
            log_files.sort(key=lambda x: x[1], reverse=True)
            log = log_files[0][0]

    return input_log_file(log)