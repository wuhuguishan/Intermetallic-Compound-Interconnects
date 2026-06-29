#!/bin/bash
#SBATCH -p kshcnormal
#SBATCH -N 2
#SBATCH --no-requeue
#SBATCH --ntasks-per-node=16
#SBATCH -t 04:00:00


module purge
module load python/3.8.10

# opt计算
current_dir=$(basename $(pwd))
chmod +x job.slurm
sbatch --job-name="IC-${current_dir}-opt" job.slurm

# 等待20秒
sleep 20
# 循环检查第一次任务是否收敛
while true; do
    if grep -q 'reached required accuracy - stopping structural energy minimisation' OUTCAR; then
        echo "opt converged."
        break
    fi
    sleep 60 # 每60秒检查一次
done

# 将CONTCAR复制为新的POSCAR
cp CONTCAR POSCAR

# 调用Python脚本处理INCAR
python handle_INCAR_scf.py

# scf计算
current_dir=$(basename $(pwd))
chmod +x job.slurm
sbatch --job-name="IC-${current_dir}-scf" job.slurm

# 等待20秒

sleep 20

# 循环检查第二次任务是否收敛
while true; do
    if grep -q 'aborting loop because EDIFF is reached' OUTCAR;then
        echo "scf converged."
        break
        break
    fi
    sleep 60
done

# 调用Python脚本处理INCAR
python handle_INCAR_nscf.py

# nscf计算
current_dir=$(basename $(pwd))
chmod +x job.slurm
sbatch --job-name="IC-${current_dir}-nscf" job.slurm


# 等待20秒
sleep 20

# 循环检查第二次任务是否收敛
while true; do
    if grep -q 'aborting loop because EDIFF is reached' OUTCAR;then
        echo "nscf converged."
        break
        break
    fi
    sleep 60
done

cd "$dir"
current_dir=$(basename $(pwd))
chmod +x IC-FZ-V.slurm  yy.slurm zz.slurm vel.slurm
sbatch --job-name="IC-${current_dir}-FZ" IC-FZ-V.slurm
sbatch --job-name="IC-${current_dir}-FZ-yy" yy.slurm
sbatch --job-name="IC-${current_dir}-FZ-zz" zz.slurm
sbatch --job-name="IC-${current_dir}-vel" vel.slurm