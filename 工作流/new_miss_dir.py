#! /usr/bin/env python3
# -*- coding: UTF-8 -*-
import os
import shutil
from pathlib import Path

def find_folder_in_ancestors(folder_name, depth=3):
    current_path = Path.cwd()
    for _ in range(depth):
        folder_path = current_path / folder_name
        if folder_path.is_dir():
            return folder_path
        current_path = current_path.parent
    return None

def main():
    for file in os.listdir('.'):
        if file.endswith('.vasp'):
            with open(file, 'r') as f:
                folder_name = f.readline().strip()
            new_folder_path = Path(folder_name)
            new_folder_path.mkdir(exist_ok=True)

            # Rename and move POSCAR.txt
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

            # Run vaspkit command
            os.chdir(new_folder_path)
            vaspkit_input = "102\n2\n0.03\n"
            subprocess.run(['vaspkit'], input=vaspkit_input, text=True, shell=False)
            os.chdir('..')

if __name__ == '__main__':
    main()