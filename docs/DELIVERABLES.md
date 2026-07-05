# DELIVERABLES — 两轮工作全部产物清单

> 第一轮：Phase 0–3 + 体检报告（2026-07-05）。第二轮：Phase 4–6，项目改善定位
> （用户指示：不做发表建议）。全程无 git commit/push；`benchmarks/` 子模块只读
> （仅做过浅克隆初始化）。

## 1. 报告与文档

| 产物 | 路径 | 说明 |
|---|---|---|
| 体检报告（中文，六节） | `docs/health-check-report.md` | 第一轮 THE GATE 产物 |
| 进度日志 | `docs/PROGRESS.md` | Phase 0–6 全程状态、发现、NOT RUN 标注 |
| 决策记录 | `docs/DECISIONS.md` | Gate 决策（改善定位、无发表建议）、opt-in 改动原则 |
| 复现命令表 | `docs/reproduction-commands.md` | 每图/表一条命令；VERIFIED 带日期，NOT RUN 明确标注；含 E1–E3 全量命令 |
| 论文骨架 + 摘要草稿（英文，会场中立） | `docs/paper-skeleton.md` | 6 条主张逐句 SUPPORTED/NOT YET SUPPORTED；图先行计划；摘要只含小规模证据支撑的内容 |
| 本清单 | `docs/DELIVERABLES.md` | — |

## 2. 代码修复与改动（默认行为逐字节不变，均有回归验证）

| 改动 | 文件 | 性质 |
|---|---|---|
| BUG-1 修复：`--c > 1` IndexError | `exp/bench.py`（`qc_nq_lst = [n] * num_circuits`） | 已证明 bug（最小重现 + 修复后验证） |
| S-2 消融钩子：`--layout-heuristic` | `exp/bench.py`、`dqcmap/basecompiler.py`、`dqcmap/compilers/{multi_ctrl,baseline,single_ctrl}_compiler.py`、`dqcmap/passes/managers/__init__.py`、`dqcmap/passes/plugin.py` | opt-in；默认 None = 原行为 |
| S-1 修复：EvalV2 门时长参数化 + `--t-eval` | `dqcmap/evaluator.py`、`exp/bench.py` | opt-in；默认 20/40ns 不变 |
| KL mapper 确定性选项 | `dqcmap/mappers/iter_KL_mapper.py`（`max_iters`、`rng_seed` 参数） | opt-in；默认墙钟 4s + 模块 RNG 不变 |
| Fig 7/8 CSV 派生 + 自检脚本 | `exp/last_table_vis_from_csv.py`（新文件；原 `last_table_vis.py` 未动） | 消除硬编码数据负债 |

**未修（有意保留，证据在报告 S-1/S-2/S-3 条目）**：布局阶段 DM0 坐标系（仅做消融取证，
改 Rust 打分会使结果偏离已发表论文，留作者决定）；`check_swap_needed` 死代码；`EvalV3` stub。

## 3. 回归钉子测试（共 16 项新增；全量 41 passed @ 2026-07-05）

| 文件 | 内容 |
|---|---|
| `tests/audit_pins_test.py`（8 项，第一轮） | EvalV2/Eval 手算锚点、creg 条件语义、隐形传态语义等价 oracle、num_cif_pairs 暴力对账、KL 不变量与目标函数、pe_20 CLASS<baseline 主张级不等式 |
| `tests/improvement_pins_test.py`（8 项，第二轮） | EvalV2 参数化（默认不变 + 缩放正确）、KL 确定性（同种子同预算可重复 + 合法性）、`layout_heuristic`（None ≡ 同值 + decay 臂出合法电路） |

运行：`pytest tests/`（约 35 秒）。

## 4. 实验数据（最小规模，全部真实运行）

| 目录/文件 | 内容 |
|---|---|
| `exp/data/audit/merged_table2.csv` | Table II 28 行复现件（与论文 CSV 逐行一致） |
| `exp/data/audit/ctrl_num_impact.txt` + `num_ctrl_impact.pdf` | Fig 9 重生成 |
| `exp/data/audit/runtime_analysis_same_ctrl.txt` + `runtime_ctrl_fixed.pdf` | Fig 10 重生成 |
| `exp/data/audit/type_{i,ii}_improvement_percentage.pdf` | Fig 7/8 CSV 派生版 |
| `exp/data/audit/phase4/small.lst` | 小规模基准列表（pe_20/qft_20/random_20/cc_12） |
| `exp/data/audit/phase4/E1_A_*.tsv`, `E1_B_*.tsv` | S-2 消融 A/B 臂 × 3 种子；另含串行/并行稳定性对照（`E1_A_run{1,2}` vs `E1_A_par{1,2}`） |
| `exp/data/audit/phase4/E2_teval.tsv`, `E2_no_teval_t02.tsv` | `--t` 灵敏度（t=1.0/0.5/0.2）与死旋钮回归对照 |
| `exp/data/audit/phase4/E3_baseline_seed*.tsv` | baseline 三种子方差 |
| `exp/data/audit/pe20.lst`、`benchmarks_{cc,nocc}.lst*` | 第一轮审计辅助文件 |

## 5. 明确未完成（NOT RUN / TODO / PARTIAL）

- E1/E2/E3 **全量规模**实验（命令就绪，见 `docs/reproduction-commands.md` 第 2 节）。
- E3 均值±标准差汇总脚本（TODO，未编写）。
- KL 确定性选项接入 bench CLI（TODO，`mapping()` 已支持透传）。
- 跨机器逐位一致性验证（PARTIAL，需第二台机器）。
- `exp/fidelity_analysis.py`（NOT RUN，需 IBM Quantum 凭据）。
