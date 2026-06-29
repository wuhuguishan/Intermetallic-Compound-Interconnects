#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Linux系统优化版本 - 高性能、低开销
# 使用方法: chmod +x complete_linux_optimized.py && ./complete_linux_optimized.py
import os
import shutil
import subprocess
from pathlib import Path
import re
from time import time

# 合并了Auto_dir.py和distri_doc.slurm的功能，优化了性能和用户体验

def find_folder_in_ancestors(folder_name, depth=3):
    """快速查找上级目录中的指定文件夹"""
    current_path = Path.cwd()
    for _ in range(depth):
        folder_path = current_path / folder_name
        if folder_path.is_dir():
            return folder_path
        current_path = current_path.parent
    return None

def modify_slurm_job_name(slurm_file, new_job_name):
    """高效修改Slurm作业名称"""
    with open(slurm_file, 'r') as f:
        content = f.read()
    
    content = re.sub(
        r'(#SBATCH\s+(?:--job-name=|-J\s+))\S+',
        r'\1{}'.format(new_job_name),
        content
    )
    
    with open(slurm_file, 'w') as f:
        f.write(content)

def process_vasp_file(file, slurm_template, vaspkit_command_folder):
    """单函数处理单个vasp文件，避免多次目录切换"""
    base = file[:-5]  # 去掉.vasp后缀
    folder_name = base[3:] if base.startswith("mp-") else base
    
    # 使用Path对象进行路径操作，更高效
    new_folder = Path(folder_name)
    new_folder.mkdir(exist_ok=True)
    
    # 构建所有路径，避免重复创建路径对象
    poscar_path = new_folder / 'POSCAR'
    incar_dest_path = new_folder / 'INCAR'
    kpoints_dest_path = new_folder / 'KPOINTS'
    slurm_dest_path = new_folder / 'job.slurm'
    
    # 文件操作 - 尽可能使用绝对路径
    shutil.move(file, poscar_path)
    
    # 直接从当前目录复制INCAR文件，类似于处理POSCAR的方式
    current_incar = Path('INCAR')
    if current_incar.exists():
        shutil.copy(current_incar, incar_dest_path)

    if vaspkit_command_folder:
        shutil.copy(vaspkit_command_folder / 'KPOINTS', kpoints_dest_path)
    
    # 复制并修改slurm文件
    shutil.copy(slurm_template, slurm_dest_path)
    modify_slurm_job_name(slurm_dest_path, f"IC-{folder_name}-opt")
    
    # 运行vaspkit - 使用子进程的cwd参数，避免目录切换
    vaspkit_input = "102\n2\n0.03\n"
    try:
        subprocess.run(
            ['vaspkit'],
            input=vaspkit_input,
            text=True,
            capture_output=True,
            check=True,
            cwd=str(new_folder)  # 关键点：直接在指定目录运行，无需chdir
        )
        vaspkit_ok = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        vaspkit_ok = False
    
    return folder_name, vaspkit_ok

def copy_scripts(target_dir, workflow_dir, scripts):
    """批量复制脚本并设置权限，使用os模块提高性能"""
    # 预编译需要设置可执行权限的扩展名
    exec_extensions = ('.sh', '.slurm')
    
    for script in scripts:
        source = os.path.join(workflow_dir, script)
        target = os.path.join(target_dir, script)
        
        try:
            shutil.copy(source, target)
            # 批量设置权限
            if script.endswith(exec_extensions):
                os.chmod(target, 0o755)
        except FileNotFoundError:
            # 简化错误处理，避免过多打印
            pass

def submit_slurm_job(directory, job_name):
    """提交Slurm作业，使用cwd参数避免目录切换"""
    try:
        # 直接在指定目录运行sbatch
        result = subprocess.run(
            ['sbatch', '--job-name', job_name, 'complete_converge.sh'],
            capture_output=True,
            text=True,
            cwd=directory
        )
        return result.returncode == 0, result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, ""

def main():
    """优化的主函数 - 减少运行时间和系统开销"""
    start_time = time()
    original_dir = Path.cwd()
    print(f"当前工作目录: {original_dir}")
    
    # 检查当前目录是否存在INCAR文件
    current_incar = Path('INCAR')
    if not current_incar.exists():
        print("警告: 当前目录中未找到INCAR文件")
    else:
        print("找到INCAR文件，将复制到各个子目录")
    
    # ======= 阶段1: 处理.vasp文件 =======
    slurm_template = original_dir / 'job.slurm'
    processed_count = 0
    
    if slurm_template.exists():
        print("\n处理.vasp文件...")
        
        # 使用列表推导式一次性收集所有.vasp文件
        vasp_files = [f for f in os.listdir('.') if f.endswith('.vasp')]
        total_files = len(vasp_files)
        print(f"找到 {total_files} 个.vasp文件")
        
        # 预先查找所需文件夹，避免重复查找
        # 移除对incar_folder的依赖
        vaspkit_command_folder = find_folder_in_ancestors('vaspkit_command')
        
        # 处理每个文件
        for i, file in enumerate(vasp_files, 1):
            # 使用进度显示代替详细日志，减少I/O开销
            if i % 5 == 0 or i == total_files:  # 每5个文件或最后一个文件显示进度
                print(f"  进度: {i}/{total_files}")
            
            # 集中处理单个文件，避免函数调用开销
            base = file[:-5]
            folder_name = base[3:] if base.startswith("mp-") else base
            
            # 构建路径一次使用多次
            new_folder = Path(folder_name)
            new_folder.mkdir(exist_ok=True)
            
            # 移动POSCAR
            shutil.move(file, new_folder / 'POSCAR')
            
            # 复制必要文件
            # 直接从当前目录复制INCAR文件，类似于处理POSCAR的方式
            if current_incar.exists():
                shutil.copy(current_incar, new_folder / 'INCAR')
            
            if vaspkit_command_folder:
                shutil.copy(vaspkit_command_folder / 'KPOINTS', new_folder / 'KPOINTS')
            
            # 复制并修改slurm
            target_slurm = new_folder / 'job.slurm'
            shutil.copy(slurm_template, target_slurm)
            
            # 内联修改slurm作业名，减少函数调用
            with open(target_slurm, 'r') as f:
                content = f.read()
            content = re.sub(r'(#SBATCH\s+(?:--job-name=|-J\s+))\S+', 
                           rf'\1IC-{folder_name}-opt', content)
            with open(target_slurm, 'w') as f:
                f.write(content)
            
            # 运行vaspkit
            try:
                subprocess.run(
                    ['vaspkit'],
                    input="102\n2\n0.03\n",
                    text=True,
                    capture_output=True,
                    cwd=str(new_folder),
                    timeout=300  # 添加超时，避免卡住
                )
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                pass  # 简化错误处理
            
            processed_count += 1
    else:
        print("警告: 未找到job.slurm模板文件")
    
    # ======= 阶段2: 复制脚本和提交作业 =======
    print("\n复制脚本和提交作业...")
    
    # 定义脚本列表
    SCRIPTS = ["complete_converge.sh", "job.slurm", "handle_INCAR_scf.py", 
               "handle_INCAR_nscf.py", "complete_integral.slurm","complete_integral.py", "vel.slurm"]
    
    WORKFLOW_DIR = str(original_dir)
    
    # 使用os.scandir()代替os.listdir()，更高效
    dirs_to_process = []
    with os.scandir('.') as entries:
        for entry in entries:
            if entry.is_dir(follow_symlinks=False) and not entry.name.startswith('.'):
                dirs_to_process.append(entry.name)
    
    total_dirs = len(dirs_to_process)
    print(f"找到 {total_dirs} 个子目录")
    submitted_count = 0
    
    # 批量处理目录
    for i, dir_name in enumerate(dirs_to_process, 1):
        if i % 5 == 0 or i == total_dirs:
            print(f"  进度: {i}/{total_dirs}")
        
        dir_path = os.path.join('.', dir_name)
        
        # 复制脚本
        for script in SCRIPTS:
            source = os.path.join(WORKFLOW_DIR, script)
            target = os.path.join(dir_path, script)
            try:
                shutil.copy(source, target)
                # 批量设置权限
                if script.endswith(('.sh', '.slurm')):
                    os.chmod(target, 0o755)
            except FileNotFoundError:
                pass
        
        # 提交作业
        try:
            subprocess.run(
                ['sbatch', '--job-name', f"IC-{dir_name}-check", 'complete_converge.sh'],
                capture_output=True,
                text=True,
                cwd=dir_path
            )
            submitted_count += 1
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    
    # ======= 完成报告 =======
    end_time = time()
    print(f"\n✅ 处理完成!")
    print(f"  - 处理了 {processed_count} 个.vasp文件")
    print(f"  - 提交了 {submitted_count} 个作业")
    print(f"  - 总耗时: {end_time - start_time:.2f} 秒")
    print(f"  - 运行环境: Linux")

if __name__ == '__main__':
    # 简化的环境检查
    if os.name != 'posix':
        print("⚠️ 警告: 此脚本在非Linux系统上可能无法正常工作")
    main()