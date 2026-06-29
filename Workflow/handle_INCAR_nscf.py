#!/usr/bin/env python3
import subprocess
import os

# 主要用在不同的ENCUT设置中，部分修改参数的比较合理
def modify_incar(filename):
    # 读取INCAR文件内容
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # 修改参数
    modified_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith('ISTART'):
            line = 'ISTART = 1'
        elif line.startswith('ICHARG'):
            line = 'ICHARG = 11' 
        elif line.startswith('LWAVE'):
            line = 'LWAVE = .FALSE.'
        elif line.startswith('LCHARG'):
            line = 'LCHARG = .FALSE.'
        elif line.startswith('ISYM'):
            line = 'ISYM = 2'         
        modified_lines.append(line + '\n')
        
    # 写回文件
    with open(filename, 'w') as f:
        f.writelines(modified_lines)
        
def modify_kpoints():
    # 使用vaspkit生成KPOINTS文件
    try:
        # 调用vaspkit生成KPOINTS文件
        subprocess.run(['vaspkit'], input='102\n2\n0.01\n', text=True, check=True)
        print("Generated KPOINTS file using vaspkit")
    except subprocess.CalledProcessError as e:
        print(f"Error generating KPOINTS file: {e}")
    except FileNotFoundError:
        print("Error: vaspkit not found. Please ensure vaspkit is installed and in PATH")
        

def main():
    if os.path.exists('INCAR'):
        modify_incar('INCAR')
        print("Modified INCAR parameters")
    else:
        print("Error: INCAR file not found in current directory.")

        
    modify_kpoints()

if __name__ == "__main__":
    main()
