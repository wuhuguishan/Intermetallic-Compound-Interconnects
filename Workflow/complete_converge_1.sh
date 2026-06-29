#!/bin/bash
#SBATCH -p kshcnormal
#SBATCH -N 2
#SBATCH --no-requeue
#SBATCH --ntasks-per-node=16
#SBATCH -t 04:00:00              # <<< 修改：时长
#SBATCH -o converge.out            # <<< 修改：输出文件

# 设置严格模式：任何命令失败立即退出
set -e
# 显示执行的每个命令
set -x

module purge
module load python/3.8.10

# 获取当前脚本所在目录
script_dir=$(pwd)

# 定义最大并行任务数
MAX_PARALLEL=4

# 设置超时时间（秒）
OPT_TIMEOUT=7200  # 2小时
SCF_TIMEOUT=7200  # 2小时
NSCF_TIMEOUT=7200 # 2小时

# 函数：检查作业状态 - 主要修改部分（第25-51行）
check_job_status() {
    local job_id=$1
    local timeout=$2
    local check_interval=60
    local elapsed=0
    local job_state
    local max_retries=3
    
    echo "等待作业 $job_id 完成..."
    
    while true; do
        # 修改点1：使用sacct替代squeue检查作业状态
        for ((retry=0; retry<max_retries; retry++)); do
            job_state=$(sacct -j $job_id -n -P -o State 2>/dev/null | tail -n 1)
            
            if [[ -n "$job_state" ]]; then
                break
            fi
            
            if [[ $retry -lt $((max_retries-1)) ]]; then
                echo "sacct未返回状态，等待后重试 ($((retry+1))/$max_retries)"
                sleep 10
            fi
        done
        
        # 修改点2：添加备选检查机制
        if [[ -z "$job_state" ]]; then
            echo "警告：无法获取作业 $job_id 的状态，将检查squeue作为备选"
            job_state=$(squeue -j $job_id -h -o %T 2>/dev/null || echo "COMPLETED")
        fi
        
        # 修改点3：使用case语句处理更详细的状态
        case "$job_state" in
            *COMPLETED*)
                echo "作业 $job_id 已完成"
                return 0
                ;;
            *FAILED*|*CANCELLED*|*NODE_FAIL*|*TIMEOUT*)
                echo "错误：作业 $job_id 失败，状态：$job_state"
                return 1
                ;;
            *RUNNING*|*PENDING*|*CONFIGURING*|*COMPLETING*)  
                echo "作业 $job_id 正在运行，状态：$job_state"
                ;;
            *)
                echo "未知状态：$job_state，继续监控"
                ;;
        esac
        
        # 检查是否超时
        if (( elapsed >= timeout )); then
            echo "错误：作业 $job_id 超出超时时间 ${timeout}秒"
            scancel $job_id 2>/dev/null || true
            return 1
        fi
        
        # 等待一段时间后再次检查
        sleep $check_interval
        ((elapsed += check_interval))
        echo "已等待 ${elapsed}秒"
    done
}

# 处理单个文件夹的函数
process_folder() {
    local dir=$1
    local full_path="$script_dir/$dir"
    
    echo "开始处理文件夹: $dir"
    
    # 进入文件夹
    if ! cd "$full_path"; then
        echo "错误：无法进入文件夹 $full_path"
        return 1
    fi
    
    local current_dir=$(basename $(pwd))
    echo "处理文件夹：$current_dir"
    
    # opt计算
    echo "开始OPT计算：$current_dir"
    chmod +x job.slurm
    OPT_JOB_ID=$(sbatch --parsable --job-name="IC-${current_dir}-opt" job.slurm)
    echo "提交的OPT作业ID：$OPT_JOB_ID"

    # 检查OPT作业状态
    if ! check_job_status "$OPT_JOB_ID" "$OPT_TIMEOUT"; then
        echo "错误：OPT计算失败，退出处理文件夹 $current_dir"
        return 1
    fi

    # 检查收敛输出
    if ! grep -q 'reached required accuracy - stopping structural energy minimisation' OUTCAR; then
        echo "错误：OPT计算未达到收敛条件"
        return 1
    fi
    echo "OPT计算收敛成功"

    # 将CONTCAR复制为新的POSCAR
    if ! cp CONTCAR POSCAR; then
        echo "错误：无法复制CONTCAR到POSCAR"
        return 1
    fi
    echo "已更新POSCAR文件"

    # 调用Python脚本处理INCAR
    if ! python handle_INCAR_scf.py; then
        echo "错误：调用handle_INCAR_scf.py失败"
        return 1
    fi
    echo "已处理SCF的INCAR文件"

    # scf计算
    echo "开始SCF计算：$current_dir"
    chmod +x job.slurm
    SCF_JOB_ID=$(sbatch --parsable --job-name="IC-${current_dir}-scf" job.slurm)
    echo "提交的SCF作业ID：$SCF_JOB_ID"

    # 检查SCF作业状态
    if ! check_job_status "$SCF_JOB_ID" "$SCF_TIMEOUT"; then
        echo "错误：SCF计算失败，退出处理文件夹 $current_dir"
        return 1
    fi

    # 检查SCF收敛
    if ! grep -q 'aborting loop because EDIFF is reached' OUTCAR; then
        echo "错误：SCF计算未达到收敛条件"
        return 1
    fi
    echo "SCF计算收敛成功"

    # 调用Python脚本处理INCAR
    if ! python handle_INCAR_nscf.py; then
        echo "错误：调用handle_INCAR_nscf.py失败"
        return 1
    fi
    echo "已处理NSCF的INCAR文件"

    # nscf计算
    echo "开始NSCF计算：$current_dir"
    chmod +x job.slurm
    NSCF_JOB_ID=$(sbatch --parsable --job-name="IC-${current_dir}-nscf" job.slurm)
    echo "提交的NSCF作业ID：$NSCF_JOB_ID"

    # 检查NSCF作业状态
    if ! check_job_status "$NSCF_JOB_ID" "$NSCF_TIMEOUT"; then
        echo "错误：NSCF计算失败，退出处理文件夹 $current_dir"
        return 1
    fi

    # 检查NSCF收敛
    if ! grep -q 'aborting loop because EDIFF is reached' OUTCAR; then
        echo "错误：NSCF计算未达到收敛条件"
        return 1
    fi
    echo "NSCF计算收敛成功"

    # 当前目录即为处理目录，不需要额外cd
    echo "当前工作目录：$current_dir"
    
    # 确保脚本有执行权限
    chmod +x complete_integral.slurm vel.slurm
    
    # 提交积分计算作业
    FZ_JOB_ID=$(sbatch --parsable --job-name="IC-${current_dir}-FZ" complete_integral.slurm)
    echo "提交的FZ作业ID：$FZ_JOB_ID"
    
    # 提交速度计算作业
    VEL_JOB_ID=$(sbatch --parsable --job-name="IC-${current_dir}-vel" vel.slurm)
    echo "提交的VEL作业ID：$VEL_JOB_ID"
    
    echo "文件夹 $current_dir 处理完成！"
    return 0
}

# 定义要处理的内部文件夹
readarray -t folders < <(find . -maxdepth 1 -type d -printf '%f/\n' 2>/dev/null)

# 检查是否有子文件夹
if [ ${#folders[@]} -eq 0 ]; then
    echo "警告：当前目录下没有找到子文件夹，将在当前目录执行计算"
    folders=(.)
fi

echo "找到的文件夹: ${folders[*]}"
echo "最大并行任务数: $MAX_PARALLEL"

# 循环处理文件夹
for dir in "${folders[@]}"; do
    # 检查当前运行的任务数
    while [ $(jobs -r | wc -l) -ge $MAX_PARALLEL ]; do
        # 等待任一后台任务完成
        wait -n
        echo "一个后台任务已完成，继续提交新任务"
    done
    
    # 在后台启动文件夹处理
    (process_folder "$dir") &
    echo "已启动文件夹 $dir 的处理任务（后台运行）"
    
    # 短暂延迟，避免同时提交过多任务
    sleep 5
done

# 等待所有后台任务完成
echo "所有任务已提交，等待全部完成..."
wait
echo "所有文件夹处理完成！"