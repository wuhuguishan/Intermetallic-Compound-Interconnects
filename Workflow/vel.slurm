#!/bin/bash
#SBATCH -p kshcnormal
#SBATCH -N 4
#SBATCH --ntasks-per-node=16
#SBATCH --exclusive
#SBATCH -o vel
#SBATCH -t 01:00:00


module purge
source /public/home/jqyang/apprepo/IFermi/v0.3.4-conda/scripts/env.sh

ifermi info --property velocity