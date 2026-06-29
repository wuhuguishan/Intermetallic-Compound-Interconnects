#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
积分结果收集器

功能：扫描目录结构，收集每个文件夹中integral.out文件的xx、yy、zz分量积分结果，
      从文件夹名称中提取mp-id和化合物名称，将所有结果统一转换为1e-16次方形式，
      并整理到一个表格中。

使用方法：
    python collect_integral_results.py [--root_dir 根目录路径] [--output_file 输出文件名]

输出格式：CSV表格，包含mp-id、化合物名称和各方向分量的积分结果（已转换为1e-16次方形式）
"""

import os
import re
import argparse
import pandas as pd
from pathlib import Path

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='收集积分结果到表格')
    parser.add_argument('--root_dir', type=str, default=os.getcwd(),
                       help='要扫描的根目录路径（默认当前目录）')
    parser.add_argument('--output_file', type=str, default='integral_results_summary.csv',
                       help='输出的CSV文件名（默认integral_results_summary.csv）')
    return parser.parse_args()

def extract_mp_info(folder_name):
    """
    从文件夹名称中提取mp-id和化合物名称
    
    支持的格式：
    - mp-xxxx_CompoundName（例如：mp-1234_IrV）
    - comp_mp-xxxx_CompoundName（例如：comp_mp-1234_IrV）
    
    返回：(mp_id, compound_name)，如果无法提取则返回(None, None)
    """
    # 匹配 mp-数字_化合物名称 或 comp_mp-数字_化合物名称 的模式
    pattern = r'(?:comp_)?(mp-\d+)_(\w+)'  # 非捕获组 (?:comp_)? 用于匹配可选的"comp_"前缀
    match = re.search(pattern, folder_name)
    
    if match:
        mp_id = match.group(1)
        compound_name = match.group(2)
        return mp_id, compound_name
    return None, None

def extract_integral_results(file_path):
    """从integral.out文件中提取积分结果，并转换为1e-16次方形式"""
    results = {}
    scale_factor = 1e-16  # 统一使用1e-16作为缩放因子
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 匹配对角分量结果的模式
            # 匹配格式如: "xx: 1/(rho0 * lambda) = 1.2345 [1/(Ohm·m^2)] | rho0 * lambda = 0.809 [Ohm·m^2]"
            pattern = r'(xx|yy|zz):\s+1/(rho0\s\*\s+lambda)\s+=\s+([\d\.eE\+\-]+)\s+\[1\/(Ohm·m\^2)\]\s+\|\s+rho0\s\*\s+lambda\s+=\s+([\d\.eE\+\-]+)\s+\[Ohm·m\^2\]'
            matches = re.finditer(pattern, content)
            
            for match in matches:
                component = match.group(1)
                value_inv = float(match.group(3))
                value = float(match.group(5))
                
                # 转换为1e-16次方形式（除以1e-16，使结果以1e-16为单位）
                results[f"{component}_inv"] = value_inv / scale_factor  # 1/(rho0*lambda) / 1e-16
                results[f"{component}"] = value / scale_factor         # rho0*lambda / 1e-16
            
            # 也处理旧格式的输出（单分量输出）
            if not results:  # 如果没有找到对角分量格式，尝试匹配旧格式
                single_pattern = r'component\s+(xx|yy|zz):\s*\n\s+1/(rho0\s\*\s+lambda)\s+=\s+([\d\.eE\+\-]+)'
                single_match = re.search(single_pattern, content)
                if single_match:
                    component = single_match.group(1)
                    value_inv = float(single_match.group(3))
                    value = 1.0 / value_inv if value_inv != 0 else float('inf')
                    
                    # 转换为1e-16次方形式
                    results[f"{component}_inv"] = value_inv / scale_factor
                    results[f"{component}"] = value / scale_factor
    
    except Exception as e:
        print(f"解析文件 {file_path} 时出错: {e}")
    
    return results

def find_integral_files(root_dir):
    """递归查找所有integral.out文件"""
    integral_files = []
    
    for dirpath, _, filenames in os.walk(root_dir):
        if 'integral.out' in filenames:
            file_path = os.path.join(dirpath, 'integral.out')
            # 获取文件夹名称（用于提取mp-id和化合物名称）
            folder_name = os.path.basename(dirpath)
            # 获取相对于根目录的路径作为样本标识
            rel_path = os.path.relpath(dirpath, root_dir)
            sample_id = rel_path if rel_path != '.' else 'root'
            
            # 提取mp-id和化合物名称
            mp_id, compound_name = extract_mp_info(folder_name)
            
            integral_files.append((sample_id, folder_name, mp_id, compound_name, file_path))
    
    return integral_files

def main():
    args = parse_arguments()
    root_dir = os.path.abspath(args.root_dir)
    scale_factor = 1e-16  # 统一使用1e-16作为缩放因子
    
    print(f"正在扫描目录: {root_dir}")
    print(f"将所有积分结果统一转换为 {scale_factor} 的倍数形式")
    
    integral_files = find_integral_files(root_dir)
    
    if not integral_files:
        print("未找到任何integral.out文件")
        return
    
    print(f"找到 {len(integral_files)} 个integral.out文件")
    
    # 准备数据框
    all_results = []
    
    for sample_id, folder_name, mp_id, compound_name, file_path in integral_files:
        print(f"处理文件: {file_path}")
        print(f"  文件夹名称: {folder_name}")
        print(f"  提取的mp-id: {mp_id}")
        print(f"  提取的化合物名称: {compound_name}")
        
        results = extract_integral_results(file_path)
        
        if results:
            # 添加样本标识信息
            results['sample_id'] = sample_id
            results['folder_name'] = folder_name
            results['mp_id'] = mp_id if mp_id else folder_name  # 如果没有提取到mp-id，使用文件夹名称作为后备
            results['compound_name'] = compound_name if compound_name else "Unknown"  # 如果没有提取到化合物名称，使用"Unknown"
            
            all_results.append(results)
        else:
            print(f"警告: 文件 {file_path} 中未找到有效的积分结果")
    
    if not all_results:
        print("未找到任何有效的积分结果")
        return
    
    # 创建DataFrame
    df = pd.DataFrame(all_results)
    
    # 重新排序列，确保mp_id和compound_name在前面
    # 首先添加基本信息列
    basic_columns = ['sample_id', 'folder_name', 'mp_id', 'compound_name']
    # 然后添加数据列，按xx、yy、zz的顺序组织
    data_columns = []
    for comp in ['xx', 'yy', 'zz']:
        if f"{comp}_inv" in df.columns:
            data_columns.append(f"{comp}_inv")
        if f"{comp}" in df.columns:
            data_columns.append(f"{comp}")
    
    # 最终列顺序
    columns = basic_columns + data_columns
    
    # 确保所有列出现在df中
    existing_columns = [col for col in columns if col in df.columns]
    # 添加df中可能存在但不在我们预定义列表中的列
    remaining_columns = [col for col in df.columns if col not in existing_columns]
    
    df = df[existing_columns + remaining_columns]
    
    # 保存到CSV文件
    output_path = os.path.join(root_dir, args.output_file)
    df.to_csv(output_path, index=False)
    
    print(f"\n积分结果已保存到: {output_path}")
    print(f"共收集到 {len(df)} 个有效样本的积分结果")
    print(f"所有结果已统一转换为 {scale_factor} 的倍数形式")
    
    # 显示简要统计
    print("\n各分量数据统计:")
    components = ['xx', 'yy', 'zz']
    for comp in components:
        if f"{comp}_inv" in df.columns:
            valid_count = df[f"{comp}_inv"].count()
            # 显示一些示例值
            sample_values = df[f"{comp}_inv"].dropna().head(3).tolist()
            print(f"  {comp}_inv: {valid_count} 个有效值 | 示例值: {sample_values}")
        if f"{comp}" in df.columns:
            valid_count = df[f"{comp}"].count()
            sample_values = df[f"{comp}"].dropna().head(3).tolist()
            print(f"  {comp}: {valid_count} 个有效值 | 示例值: {sample_values}")
    
    # 显示mp-id和化合物名称提取情况
    mp_id_count = df['mp_id'].notna().sum()
    compound_name_count = df['compound_name'] != "Unknown".sum()
    print(f"\n信息提取统计:")
    print(f"  成功提取mp-id的样本数: {mp_id_count}")
    print(f"  成功提取化合物名称的样本数: {compound_name_count}")

if __name__ == "__main__":
    main()