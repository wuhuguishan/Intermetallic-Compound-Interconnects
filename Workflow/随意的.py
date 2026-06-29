#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import os
import shutil
import subprocess
from pathlib import Path
import re

def find_folder_in_ancestors(folder_name, depth=3):
    current_path = Path.cwd()
    for _ in range(depth):
        folder_path = current_path / folder_name
        if folder_path.is_dir():
            return folder_path
        current_path = current_path.parent
    return None

def modify_slurm_job_name(slurm_file, new_job_name):
    with open(slurm_file, 'r') as f:
        content = f.read()
    
    content = re.sub(
        r'(#SBATCH\s+(?:--job-name=|-J\s+))\S+',
        rf'\1{new_job_name}',
        content
    )
    
    with open(slurm_file, 'w') as f:
        f.write(content)

def main():
    original_dir = Path.cwd()
    
    slurm_template = original_dir / 'vasp.slurm'
    if not slurm_template.exists():
        print("Error: vasp.slurm template file not found in current directory")
        return
    
    for file in os.listdir('.'):
        if file.endswith('.vasp'):

            # ------- 新增：根据文件名生成文件夹名 -------
            base = file[:-5]  # 去掉 .vasp
            if base.startswith("mp-"):
                folder_name = base[3:]  # 去掉 mp-
            else:
                folder_name = base
            # -------------------------------------------

            new_folder_path = Path(folder_name)
            new_folder_path.mkdir(exist_ok=True)

            # Move POSCAR
            new_poscar_path = new_folder_path / 'POSCAR'
            shutil.move(file, new_poscar_path)

            # Copy INCAR
            incar_folder = find_folder_in_ancestors('incar')
            if incar_folder:
                shutil.copy(incar_folder / 'INCAR-opt', new_folder_path / 'INCAR')

            # Copy KPOINTS
            vaspkit_command_folder = find_folder_in_ancestors('vaspkit_command')
            if vaspkit_command_folder:
                shutil.copy(vaspkit_command_folder / 'KPOINTS', new_folder_path / 'KPOINTS')

            # Copy & modify slurm
            target_slurm = new_folder_path / 'vasp.slurm'
            shutil.copy(slurm_template, target_slurm)

            new_job_name = f"IC-{folder_name}-opt"
            modify_slurm_job_name(target_slurm, new_job_name)
            print(f"Created job: {new_job_name}")

            # Run vaspkit
            os.chdir(new_folder_path)
            vaspkit_input = "102\n2\n0.03\n"
            try:
                subprocess.run(['vaspkit'],
                               input=vaspkit_input,
                               text=True,
                               check=True)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"Warning: vaspkit failed in {folder_name}: {e}")
            finally:
                os.chdir(original_dir)

if __name__ == '__main__':
    main()
