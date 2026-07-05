# 复现命令表（每图/表一条命令）

> 约定：**VERIFIED (日期)** = 本审计在本机实际运行并核对过输出；**NOT RUN** = 命令就绪但未在本轮执行
> （通常因超出"单条命令 ≤ 30 分钟 / 最小可验证规模"预算），结果不得被引用为已验证。
> 运行环境基线：仓库 `.venv`（Python 3.11.13，qiskit 1.1.1，Rust 扩展已编译），
> macOS，命令均在仓库根目录执行。注意 KL mapper 默认为 4 秒墙钟预算、
> `DqcMapSwap` trials 由 `--rt-trial`（默认 5）控制：同机可重复，跨机不保证逐位一致。

## 0. 环境与测试

| 目的 | 命令 | 状态 |
|---|---|---|
| Python 测试（41 项 = 原 25 + 审计钉子 8 + 改善钉子 8） | `pytest tests/` | VERIFIED (2026-07-05) |
| Rust 测试 | `export DYLD_LIBRARY_PATH=<conda>/envs/class/lib/ && cargo test --no-default-features` | VERIFIED (2026-07-05，8 passed；跑完记得 unset，否则会破坏 venv 的 numpy 导入) |
| QASMBench 子模块（cc 基准依赖） | `git submodule update --init --depth 1 benchmarks/QASMBench` | VERIFIED (2026-07-05) |

## 1. 论文图表（原始口径）

| 产物 | 命令 | 状态 |
|---|---|---|
| Table II（14 基准 × 2 编译器） | `python exp/bench.py --comp baseline,multi_ctrl --ctrl 4 --parallel 1 --opt 6 --t 0.2 --rt dqcswap --bench exp/benchmarks.lst --wr 1 --wr-path exp/data/paper` | VERIFIED (2026-07-05，28/28 行与论文 CSV 一致；审计复现件 `exp/data/audit/merged_table2.csv`) |
| Table II LaTeX | `python exp/gen_main_res_table.py exp/data/paper/benchmarks.lst_baseline_multi_ctrl_dqcswap_dqcmap_opt_6_ctrl_4.csv` | VERIFIED (2026-07-05) |
| Fig 7/8（原版，硬编码数组） | `python exp/last_table_vis.py` | VERIFIED (2026-07-05) |
| **Fig 7/8（新增：CSV 派生 + 一致性自检）** | `python exp/last_table_vis_from_csv.py`（默认读论文 CSV，输出到 `exp/data/audit/`；数组与原脚本硬编码不一致时非零退出） | VERIFIED (2026-07-05，`[OK]` ×2) |
| Fig 9（控制器数影响） | `for c in 4 5 6 7 8; do python exp/bench.py --n 30 --p 0.5 --c 1 --comp baseline,multi_ctrl --opt 6 --t 0.1 --bench random --parallel 1 --ctrl $c; done \| tee exp/data/paper/ctrl_num_impact.txt && python exp/plot_num_ctrl_impact.py exp/data/paper/ctrl_num_impact.txt` | VERIFIED (2026-07-05，Phase 1 重生成 `exp/data/audit/ctrl_num_impact.txt` 与 PDF) |
| Fig 10（mapper 运行时） | `python exp/bench.py --n 20,40,60,80,100 --p 0.9 --comp multi_ctrl --bench qft --c 1 --st 1 --parallel 0 --ctrl 5 \| tee exp/data/paper/runtime_analysis_same_ctrl.txt && python exp/plot_runtime_analysis.py exp/data/paper/runtime_analysis_same_ctrl.txt` | VERIFIED (2026-07-05，Phase 1 重生成) |
| 保真度分析（真机） | `python exp/fidelity_analysis.py` | NOT RUN（需 IBM Quantum 账号凭据） |

## 2. Phase 4 改善实验（E1–E3）

小规模基准列表：`exp/data/audit/phase4/small.lst`（pe_20 / qft_20 / random_20 / cc_12）。

### E1 — 布局阶段 DM0 消融（S-2 取证）

A 臂 = 布局与路由均 DM0（论文原配置）；B 臂 = 布局 decay、路由 DM0（新开关 `--layout-heuristic decay`）。

| 规模 | 命令 | 状态 |
|---|---|---|
| 小规模 A 臂 | `python exp/bench.py --comp multi_ctrl --ctrl 4 --parallel 1 --opt 6 --t 0.2 --rt dqcswap --bench exp/data/audit/phase4/small.lst`（另加 `--seed 42` / `--seed 7` 两组） | VERIFIED (2026-07-05，结果见 `exp/data/audit/phase4/E1_A_*.tsv`) |
| 小规模 B 臂 | 同上加 `--layout-heuristic decay` | VERIFIED (2026-07-05，`exp/data/audit/phase4/E1_B_*.tsv`) |
| **全量 14 基准 × 3+ 种子 A/B 臂** | `for s in 1900 42 7; do python exp/bench.py --comp multi_ctrl --ctrl 4 --parallel 1 --opt 6 --t 0.2 --rt dqcswap --seed $s --bench exp/benchmarks.lst --wr 1 --wr-path exp/data/ablation_A; python exp/bench.py --comp multi_ctrl --ctrl 4 --parallel 1 --opt 6 --t 0.2 --rt dqcswap --seed $s --layout-heuristic decay --bench exp/benchmarks.lst --wr 1 --wr-path exp/data/ablation_B; done` | NOT RUN（预计约 1–2 小时；注意 `--wr` 会按固定文件名追加，需按种子分目录或事后区分） |

### E2 — `--t` 器件演进灵敏度（S-1 修复验证）

新开关 `--t-eval` 使 `--t` 真实作用于 EvalV2 的 2q 门时长（`t_2q = 40ns × t`）；不加该开关时行为与论文完全一致。

| 规模 | 命令 | 状态 |
|---|---|---|
| 小规模（pe_20，t ∈ {1.0, 0.5, 0.2}） | `python exp/bench.py --comp multi_ctrl --ctrl 4 --parallel 1 --opt 6 --t <t> --t-eval --rt dqcswap --bench exp/data/audit/pe20.lst` | VERIFIED (2026-07-05，`exp/data/audit/phase4/E2_teval.tsv`) |
| 死旋钮回归对照（不加 `--t-eval`） | 同上去掉 `--t-eval`，t=0.2 与 t=1.0 输出应逐字节一致 | VERIFIED (2026-07-05) |
| **全量 14 基准 × t 扫描** | `for t in 1.0 0.5 0.2 0.1; do python exp/bench.py --comp baseline,multi_ctrl --ctrl 4 --parallel 1 --opt 6 --t $t --t-eval --rt dqcswap --bench exp/benchmarks.lst; done` | NOT RUN（预计约 1–2 小时） |

### E3 — 多种子方差

| 规模 | 命令 | 状态 |
|---|---|---|
| 小规模（4 基准 × 3 种子 × baseline/CLASS） | E1 的 A 臂三种子 + `python exp/bench.py --comp baseline --ctrl 4 --parallel 1 --t 0.2 --seed <s> --bench exp/data/audit/phase4/small.lst` | VERIFIED (2026-07-05，`exp/data/audit/phase4/E3_baseline_seed*.tsv`) |
| **全量 14 基准 × ≥5 种子 + 均值±标准差汇总** | 以 E1 全量命令为模板扩展种子集（如 1900/42/7/123/2024），汇总脚本 TODO（尚未编写） | NOT RUN |

## 3. 可复现性选项（新增，全部 opt-in）

| 目的 | 用法 | 状态 |
|---|---|---|
| KL mapper 确定性预算 | `KLMapper(conf, prop, max_iters=20, rng_seed=123)`（Python API；固定迭代数替代 4 秒墙钟，专用 RNG 替代模块级全局种子） | VERIFIED (2026-07-05，钉子 `tests/improvement_pins_test.py::TestKLMapperDeterminismOptions`)。跨机器逐位一致性 PARTIAL：需第二台机器验证，本轮无法执行 |
| KL 确定性接入 bench CLI | 未接入（需再加一个 bench 参数并穿透 `mapping()`；`mapping()` 已支持 `**mapper_config` 透传，改动很小） | TODO |
| EvalV2 门时长参数化 | `EvalV2(conf, t_1q=..., t_2q=...)`；bench 侧用 `--t-eval` | VERIFIED (2026-07-05) |
| 布局阶段启发式开关 | `--layout-heuristic {decay,dqcmap,dm1}`（bench CLI）或 `MultiCtrlCompiler.run(..., layout_heuristic=...)` | VERIFIED (2026-07-05，默认路径 pe_20 逐字节回归 + 钉子) |
