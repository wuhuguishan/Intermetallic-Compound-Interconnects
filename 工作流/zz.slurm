#!/bin/bash
#SBATCH -p kshcnormal                # <<< 修改：你的队列
#SBATCH -N 4
#SBATCH --ntasks-per-node=16
#SBATCH -t 01:00:00              # <<< 修改：时长
#SBATCH -o zz.out


module purge
source /public/home/jqyang/apprepo/IFermi/v0.3.4-conda/scripts/env.sh

python IC-FZ-V.py  --vasprun vasprun.xml --temperature 300 --interpolation-factor 8 --mu auto --alpha z --beta z
