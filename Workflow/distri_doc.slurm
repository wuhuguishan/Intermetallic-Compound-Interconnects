#!/bin/bash
#SBATCH -p kshcnormal
#SBATCH -N 2
#SBATCH --no-requeue
#SBATCH --ntasks-per-node=16

module purge
module load python/3.8.10

# 定义自动化脚本的路径
WORKFLOW_DIR="/public/home/jqyang/interconnect/resistance/workflow/add5"  
SCRIPTS=( "check_covergence.sh"  "job.slurm" "handle_INCAR_scf.py" "handle_INCAR_nscf.py" "IC-FZ-V.slurm" "IC-FZ-V.py" "yy.slurm" "zz.slurm" "vel.slurm" )

# 遍历所有子文件夹
for dir in */ ; do
    # 检查是否为目录
    if [ -d "$dir" ]; then
        echo "处理目录: $dir"
        # 复制脚本到子目录
        for script in "${SCRIPTS[@]}"; do
            cp "$WORKFLOW_DIR/$script" "$dir"
            dos2unix "$dir/$script" 2>/dev/null || true
        done
        # 进入子目录并提交任务
        cd "$dir"
        current_dir=$(basename "$dir")
        chmod +x  check_covergence.sh
        sbatch --job-name "IC-${current_dir}-check" check_covergence.sh
        cd ..
    fi
done

echo "所有任务已批量提交完成。"