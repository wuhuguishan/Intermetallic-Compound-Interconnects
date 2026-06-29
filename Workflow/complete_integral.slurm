#!/bin/bash
#SBATCH -p kshcnormal                # <<< 修改：你的队列
#SBATCH -N 4
#SBATCH --ntasks-per-node=16
#SBATCH -t 02:00:00              # <<< 修改：时长
#SBATCH -o integral.out            # <<< 修改：输出文件



module purge
source /public/home/jqyang/apprepo/IFermi/v0.3.4-conda/scripts/env.sh

# 使用 --all-diagonal 参数同时计算三个对角方向的积分
python complete_integral.py --vasprun vasprun.xml --temperature 300 --interpolation-factor 8 --mu auto --all-diagonal
