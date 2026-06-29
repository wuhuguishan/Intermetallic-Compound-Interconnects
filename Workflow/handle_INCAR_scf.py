#!/usr/bin/env python3

# 用新文件，可以用在批量化过程中
import os
import shutil
# def find_incar_file():
#     # 检查各级目录
#     for i in range(4):
#         path = "../" * i
#         incar_path = os.path.join(path, 'incar', 'INCAR-scf')
#         if os.path.isfile(incar_path):
#             return incar_path
#     return None

# def main():
#     incar_file = find_incar_file()
#     if incar_file:
#         shutil.copy(incar_file, 'INCAR')
#         print(f"Copied INCAR file from {incar_file}")
#     else:
#         print("Error: INCAR file not found.")

# if __name__ == "__main__":
#     main()

# 主要用在不同的ENCUT设置中，部分修改参数的比较合理
def modify_incar(filename):
    # 读取INCAR文件内容
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # 修改参数
    modified_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith('NSW'):
            line = 'NSW = 0'
        elif line.startswith('LWAVE'):
            line = 'LWAVE = .TRUE.'
        elif line.startswith('LCHARG'):
            line = 'LCHARG = .TRUE.'
        modified_lines.append(line + '\n')
    
    # 添加新参数
    modified_lines.append('NCORE = 4\n')
    modified_lines.append('KPAR = 2\n')
    
    # 写回文件
    with open(filename, 'w') as f:
        f.writelines(modified_lines)

def main():
    if os.path.exists('INCAR'):
        modify_incar('INCAR')
        print("Modified INCAR parameters")
    else:
        print("Error: INCAR file not found in current directory.")


if __name__ == "__main__":
    main()
