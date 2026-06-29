#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compute 1/(rho0 * lambda) by Brillouin-zone volume integral from VASP bands using IFermi/pymatgen.

[修改] 本脚本仅实现体积分（BZ，任意 T>0）。请使用均匀网格 NSCF 的 vasprun.xml。
[修改] IFermi 返回的群速度单位为 m/s（见你给出的 FourierInterpolator 源码），因此不再做单位换算。
[修改] 现在支持同时计算 xx、yy、zz 三个方向的输运积分。

输出单位：SI 的 1/(Ohm·m^2)

用法示例：
  python compute_rho0lambda_bz.py --vasprun vasprun.xml -T 300 --interpolation-factor 6 --mu auto
"""

from __future__ import annotations
import argparse
import numpy as np
from dataclasses import dataclass

# ---------------- 物理常数（SI） ----------------
e_charge = 1.602176634e-19      # C
hbar_Js  = 1.054571817e-34      # J*s
kB_eV    = 8.617333262145e-5    # eV/K
Ainv_to_minv = 1e10             # (1/Å)->(1/m)

# ---------------- 依赖库 ----------------
from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.electronic_structure.bandstructure import BandStructureSymmLine
from ifermi.interpolate import FourierInterpolator

# ======================== 参数 ========================
@dataclass
class Args:
    vasprun: str
    mu: float | str
    T: float
    interpolation_factor: int
    spin_factor: int | None
    alpha: str
    beta: str

# ======================== 工具函数 ========================
def fermi_derivative_eV(epsilon_eV: np.ndarray, mu_eV: float, T_K: float) -> np.ndarray:
    """-df/de (单位 1/eV)；要求 T>0。"""
    beta = 1.0 / (kB_eV * T_K)
    x = beta * (epsilon_eV - mu_eV)
    return beta / (4.0 * np.cosh(0.5 * x)**2)

def component_index(lbl: str) -> int:
    idx = {"x":0, "y":1, "z":2}.get(lbl.lower(), None)
    if idx is None:
        raise ValueError(f"分量 '{lbl}' 非 x/y/z.")
    return idx

def tensor_labels(alpha: str, beta: str):
    ia = component_index(alpha); ib = component_index(beta)
    return ia, ib, f"{alpha}{beta}"

# ======================== 数据准备 ========================
def prepare_band_data(args: Args):
    """准备能带结构和速度数据，避免重复计算"""
    # 读取并获取"网格版"BandStructure
    vr = Vasprun(args.vasprun, parse_projected_eigen=False)
    bs = vr.get_band_structure(line_mode=False)  # [修改] 强制非路径
    if isinstance(bs, BandStructureSymmLine):
        raise RuntimeError("检测到是高对称路径的能带（BandStructureSymmLine）。"
                           "请提供 NSCF 均匀网格的 vasprun.xml 作为输入。")

    # IFermi 傅里叶插值（BoltzTraP2）
    inter = FourierInterpolator(bs)
    # [修改] 统一用 interpolate_bands，得到致密均匀网格的 {Spin: bands}, {Spin: velocities}
    interp_bs, velocities = inter.interpolate_bands(
        interpolation_factor=args.interpolation_factor,
        return_velocities=True
    )
    bands = interp_bs.bands  # dict: {spin: (nbands, Nk)}
    spins = list(bands.keys())

    # 化学势（eV）
    mu_eV = float(vr.efermi) if (isinstance(args.mu, str) and args.mu.lower() == "auto") else float(args.mu)
    if args.T <= 0:
        raise ValueError("BZ 体积分需要 T>0 K；T≈0 时建议做费米面面积分（本脚本未实现 FS）。")

    # 倒易基矢（含 2π，单位 1/Å）
    B_Ainv = vr.final_structure.lattice.reciprocal_lattice.matrix  # (3,3)
    detB_Ainv3 = abs(np.linalg.det(B_Ainv))                        # BZ 体积（1/Å^3）
    detB_minv3 = detB_Ainv3 * (Ainv_to_minv**3)                    # 换算到 1/m^3

    # 自动自旋简并因子
    if args.spin_factor is None:
        g_s = 2 if len(spins) == 1 else 1
    else:
        g_s = int(args.spin_factor)

    return {
        'bands': bands,
        'velocities': velocities,
        'spins': spins,
        'mu_eV': mu_eV,
        'detB_minv3': detB_minv3,
        'g_s': g_s,
        'vr': vr
    }

# ======================== 核心步骤（仅 BZ 积分） ========================
def compute_rho0lambda_bz(data, alpha, beta, T):
    """计算特定方向的 BZ 体积分"""
    bands = data['bands']
    velocities = data['velocities']
    spins = data['spins']
    mu_eV = data['mu_eV']
    detB_minv3 = data['detB_minv3']
    g_s = data['g_s']

    ia, ib, lab = tensor_labels(alpha, beta)

    # 逐自旋累加体积分核
    F_sum = 0.0
    F_sum_v = 0.0

    Nk_ref = None
    for s in spins:
        eps_eV = np.asarray(bands[s])          # (nb, Nk)
        vel_mps = np.asarray(velocities[s])    # (nb, Nk, 3) —— 已是 m/s

        if Nk_ref is None:
            Nk_ref = eps_eV.shape[1]
        else:
            if eps_eV.shape[1] != Nk_ref:
                raise RuntimeError("不同自旋通道的 Nk 数不一致，无法积分。")

        v2 = np.sum(vel_mps**2, axis=-1) + 1e-50          # (nb, Nk)
        v   = np.sqrt(v2)   
        dfdE_1eV = fermi_derivative_eV(eps_eV, mu_eV, T)  # (nb, Nk)
        # (v_a v_b / |v|^2) * (-df/de) ；将 1/eV -> 1/J 乘 1/e_charge
        integrand_v = ((vel_mps[..., ia] * vel_mps[..., ib] )/(v + 1e-50)) * (dfdE_1eV / e_charge)  # (1/J)
        integrand = ((vel_mps[..., ia] * vel_mps[..., ib] )/(v2 + 1e-50)) * (dfdE_1eV / e_charge)
        F_sum += np.sum(integrand)  # 累加所有带和所有 k
        F_sum_v += np.sum(integrand_v)

    # 均匀网格体元
    d3k = detB_minv3 / Nk_ref   # (1/m^3) * per-kpoint 体元

    # pref = g_s * 2 e^2 / (2π)^3  （与 B_Ainv 的 2π 定义相容）
    pref =  (e_charge**2) * 2.0 / (2.0 * np.pi)**3

    value = pref * F_sum * d3k   # SI: 1/(Ohm·m^2)
    value_v = pref * F_sum_v * d3k   # SI: 1/(Ohm·m^2)
    return value_v, pref, d3k, F_sum_v, F_sum, dict(mu_eV=mu_eV, label=lab, g_s=g_s, Nk=Nk_ref)

# ======================== CLI/入口 ========================
def parse_args() -> Args:
    p = argparse.ArgumentParser(description="Compute 1/(rho0*lambda) by BZ volume integral (NSCF uniform grid).")
    p.add_argument("--vasprun", required=True, help="NSCF 均匀网格的 vasprun.xml 或 vasprun.h5 路径")
    p.add_argument("--mu", default="auto", help="化学势 eV；默认 auto 使用 VASP Efermi")
    p.add_argument("-T","--temperature", type=float, default=300.0, help="温度 K（必须 > 0）")
    p.add_argument("--interpolation-factor", type=int, default=8, help="[修改] IFermi 傅里叶插值加密倍率")
    p.add_argument("--spin-factor", type=int, default=2,
                   help="[修改] 自旋简并因子：缺省自动判断（非自旋极化=2；自旋分辨=1），也可手动指定覆盖")
    p.add_argument("--alpha", default="x", help="张量分量 α∈{x,y,z}")
    p.add_argument("--beta",  default="x", help="张量分量 β∈{x,y,z}")
    p.add_argument("--all-diagonal", action="store_true", help="同时计算 xx、yy、zz 三个方向的积分")
    a = p.parse_args()
    return Args(
        vasprun=a.vasprun, mu=a.mu, T=a.temperature,
        interpolation_factor=a.interpolation_factor,
        spin_factor=a.spin_factor,
        alpha=a.alpha, beta=a.beta
    ), a.all_diagonal

def main():
    args, all_diagonal = parse_args()
    
    # 准备能带数据（只需执行一次）
    data = prepare_band_data(args)
    
    if all_diagonal:
        # 计算所有对角方向 (xx, yy, zz)
        directions = [('x', 'x'), ('y', 'y'), ('z', 'z')]
        results = {}
        
        for alpha, beta in directions:
            results[(alpha, beta)] = compute_rho0lambda_bz(data, alpha, beta, args.T)
        
        # 输出结果
        print(f"[μ = {results[('x', 'x')][5]['mu_eV']:.6f} eV, g_s={results[('x', 'x')][5]['g_s']}, Nk={results[('x', 'x')][5]['Nk']}]")
        print("所有对角方向的输运积分结果:")
        
        for alpha, beta in directions:
            value_v, pref, d3k, F_sum_v, F_sum, info = results[(alpha, beta)]
            print(f"\n分量 {info['label']}:")
            print(f"  1/(rho0 * lambda) = {value_v}  [1/(Ohm·m^2)]")
            print(f"  rho0 * lambda = {1/value_v}  [Ohm·m^2]")
            # 可选：仅显示主要结果，隐藏中间计算参数
            # print(f" pref = {pref}  ")
            # print(f" d3k = {d3k}  ")
            # print(f" F_sum = {F_sum}  ")
            # print(f" F_sum_v = {F_sum_v}  ")
    else:
        # 仅计算指定方向（保持原有功能）
        value_v, pref, d3k, F_sum_v, F_sum, info = compute_rho0lambda_bz(data, args.alpha, args.beta, args.T)
        
        print(f"[μ = {info['mu_eV']:.6f} eV, g_s={info['g_s']}, Nk={info['Nk']}]  component {info['label']}:")
        print(f"  1/(rho0 * lambda) = {value_v}  [1/(Ohm·m^2)]")
        print(f"  rho0 * lambda = {1/value_v}  [Ohm·m^2]")
        print(f" pref = {pref}  ")
        print(f" d3k = {d3k}  ")
        print(f" F_sum = {F_sum}  ")
        print(f" F_sum_v = {F_sum_v}  ")

if __name__ == "__main__":
    main()
