#!/bin/bash
#SBATCH -p kshcnormal
#SBATCH -N 4
#SBATCH -o stdout.%j
#SBATCH -e stderr.%j
#SBATCH --no-requeue
#SBATCH --ntasks-per-node=16

module purge
source /public/home/jqyang/apprepo/vasp/6.3.0-ioptcell_intelmpi2017_hdf5_libxc/scripts/env.sh

export MKL_DEBUG_CPU_TYPE=5 #加速代码
export MKL_CBWR=AVX2 #使cpu默认支持avx2
export I_MPI_PIN_DOMAIN=numa #内存位置与cpu位置绑定，加速内存读取。对于内存带宽要求高的计算提速明显

srun --mpi=pmi2 vasp_std