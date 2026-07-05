# PROGRESS — quantum-repo-to-paper 体检流水线

> 本文件由审计流程维护。约定：未实际运行/验证的内容一律标 TODO / PARTIAL / NOT RUN。

## Phase 0 — Intake（状态：完成）

- **仓库**：`class`（远程 `YuChenSSR/class`，fork 自 `Zhaoyilunnn/class`），README 自述为论文
  "CLASS: A Controller-Centric Layout Synthesizer for Dynamic Quantum Circuits" 的配套代码。
- **核心贡献一句话陈述**（从仓库提取；用户提供的 Phase 0 模板未填写，无人值守模式下按仓库内容确认）：
  针对动态量子电路（含测量-条件反馈）在多控制器量子控制系统上的编译问题，CLASS 在初始布局
  （KL 型图划分 mapper）与路由（修改版 SABRE，平局时用跨控制器反馈增量打分）两个阶段联合最小化
  跨控制器的测量→条件门反馈对（ICCS），从而降低反馈控制延迟（同控制器 ~50 ns vs 跨控制器 ~500 ns）。
- **结构**：
  - Python `dqcmap/`：`ControllerConfig`（比特→控制器分区）、`CircProperty`（提取 cif 对）、
    mappers（`kl_partition`/`heuristic`/`two_step`/`trivial`）、`Eval/EvalV2/EvalV3`（延迟评估器）、
    passes（`DqcMapLayout`/`DqcMapSwap`，注册为 qiskit 插件 `dqcmap`/`dqcswap`）。
  - Rust `rust/accelerate/`：fork 自 Qiskit 1.1.1 `_accelerate`，`sabre/route.rs` 的
    `choose_best_swap` 加入 `Heuristic::DM0/DM1`；`dqcmap/` 新增 `CifPairs`、`Ctrl2Pq`、`DqcMapState`。
  - 实验 `exp/`：`bench.py`（主基准脚本，Fake127QPulseV1）、表格/画图脚本、
    `fidelity_analysis.py`（需 IBM 账号）、`NonStar*.py`（控制器网络非星型布局，附加探索）。
  - 基准：veriq-benchmark 子模块（qft/pe 动态电路 QASM）、QASMBench 子模块（cc 电路，**未初始化**）。
- **已知问题（仓库观察 + 用户模板未填）**：
  - `exp/last_table_vis.py`（Fig 7/8）数据为脚本内硬编码数组，不读 CSV —— 待 Phase 1 核对。
  - `benchmarks/QASMBench` 子模块未检出（`git submodule status` 显示 `-`），cc 基准可能跑不了。
  - Fig 9/10 的输入 txt（`ctrl_num_impact.txt`、`runtime_analysis_same_ctrl.txt`）不在仓库中。
- **目标会议**：用户未指定，按 Phase 2 venue-playbook 路由。

## Phase 1 — Reality check（状态：完成）

- 环境：仓库自带 `.venv`（Python 3.11.13），`import dqcmap` 成功（Rust 扩展已编译）。
  为跑 cc 基准，补初始化了 `benchmarks/QASMBench` 子模块（浅克隆）。
- 已实际运行：
  - `pytest tests/`：25 passed（1 deprecation warning）。
  - `cargo test --no-default-features`：8 passed（需 `DYLD_LIBRARY_PATH` 指向 anaconda lib）。
  - Table II 主管线：`exp/bench.py --comp baseline,multi_ctrl --ctrl 4 --opt 6 --t 0.2 --rt dqcswap`
    全部 14 个基准 × 2 编译器 = 28 行，与 `exp/data/paper/*.csv` **逐行完全一致**（0 diff）。
    复现输出在 `exp/data/audit/merged_table2.csv`。
  - Fig 7/8：`exp/last_table_vis.py` 跑通出 PDF；其硬编码数组已核对与论文 CSV **完全一致**。
  - Fig 9：重新生成 `exp/data/audit/ctrl_num_impact.txt`（ctrl=4..8）并出图 `num_ctrl_impact.pdf`。
  - Fig 10：重新生成 `exp/data/audit/runtime_analysis_same_ctrl.txt`（qft 20–100）并出图。
  - `exp/NonStarControllerCentricLayout.py`（fork 新增的探索脚本）可运行。
- NOT RUN：`exp/fidelity_analysis.py`（模块顶层 `QiskitRuntimeService()` 需 IBM Quantum 账号凭据，无法无人值守运行）。
- REAL/FAKE/STUB 完整清单见 `docs/health-check-report.md` 第 2 节。

## Phase 2 — 新颖性检索与选会（状态：进行中）

- 已读 skill `references/venue-playbook.md`。
- **关键事实（已联网核实，访问日期 2026-07-05）**：README 所述论文
  "CLASS: A Controller-Centric Layout Synthesizer for Dynamic Quantum Circuits"
  已发表于 **ICCAD 2025**（DOI: 10.1109/ICCAD66269.2025.11240650；arXiv:2509.15742；
  作者 Yu Chen, Yilun Zhao, Bing Li, He Li, Mengdi Wang, Yinhe Han, Ying Wang；
  作者主页标注 Best Paper Candidate, 接收率 24.7%）。本仓库是官方代码库
  `Zhaoyilunnn/class` 的 fork，fork 增量为 mapper 变体、NonStar 布局探索脚本与复现数据。
- 近邻工作（均已联网核实，访问日期 2026-07-05）：
  - CLASS 本体：ICCAD 2025（CCF-B），DOI 10.1109/ICCAD66269.2025.11240650，arXiv:2509.15742。
  - Distributed-HISQ（同组）：MICRO 2025（CCF-A），DOI 10.1145/3725843.3756048，arXiv:2509.04798。
  - AC/DC（LBNL）：arXiv:2412.07969（预印本，未见正式发表）。
  - MERA（MCM 误差感知编译）：arXiv:2511.10921（预印本）。
  - Bäumer et al. 动态电路 QFT：arXiv:2403.09514。
  - QuPort（多 QPU 拓扑/端口感知编译）：arXiv:2605.12583（预印本）。
  - DQC 网络拓扑与比特分配联合优化：DOI 10.1109/QCNC64685.2025.00062。
- CCF 分级核实（ccf.org.cn 及镜像，访问 2026-07-05）：DAC=A、MICRO=A、TCAD=A（期刊）、ICCAD=B。
- DAC 2027：2027-07-10/16 圣何塞，CFP 未出（dac.com/2026/events/dac-2027，访问 2026-07-05）；
  参照 DAC 2026 节奏（摘要 2025-11-11、全文 2025-11-18/19），预计 2026 年 11 月截稿。
- **红绿灯：红灯**（对"把本仓库论文投 CCF-A"而言：论文已发表，不可重投）；
  delta 陈述与 pivot 方向见报告第 4 节。

## Phase 3 — 正确性审计（状态：完成）

- 已读 skill `references/correctness-audit.md`。审计深度：Phase 2 为红灯（对"原论文重投"而言），
  但 fork 增量方向（NonStar 等）仍有价值，故做了核心原语的完整审计而非最浅扫描。
- **钉子测试**：新增 `tests/audit_pins_test.py`（8 项，全部通过；连同原有测试共 33 passed）：
  - `EvalV2` 门延迟手算 anchor（2×1q+1×2q=80ns，measure 不计）。
  - `Eval.calc_ctrl_latency` 手算 anchor（trivial 分区 50ns/500ns 分类计数）。
  - `get_cif_qubit_pairs` 对 ClassicalRegister 级条件的语义（与已测入该 creg 的所有比特配对）。
  - 语义等价 oracle：隐形传态电路经 `MultiCtrlCompiler`（opt 6 + dqcswap + DM0）全流程编译后，
    Aer 模拟 4096 shots 输出比特恒为 1（编译前后一致）。
  - `EvalV2.num_cif_pairs` 与独立暴力重算一致（对编译后电路）。
  - `KLMapper` 不变量：输出为单射、值域合法；`evaluate_mapping` 与独立重算目标函数一致。
  - 主张级钉子：pe_20（4 控制器）CLASS 的跨控制器反馈对数严格少于 qiskit sabre baseline。
- **BUG（已证明并修复）**：`exp/bench.py` `--c > 1` 且 `--bench` 非文件时 `qc_nq_lst = nq_lst`
  长度错配导致 IndexError（上游 commit 705414c 引入）。最小重现：`--n 6 --c 2` 修复前必崩。
  修复：`qc_nq_lst = [n] * num_circuits`。修复后同命令正常运行，pytest 全绿。
- **死旋钮（实验证明，未修）**：`--t`（2q 门时间缩放，README 声称模拟先进器件）对主基准无效：
  pe_20 在 `--t 0.2` 与 `--t 1.0` 下输出逐字节一致。原因：`update_backend_cx_time_v2` 改的是
  backend 脉冲属性，而 bench 用的 `EvalV2` 硬编码 20/40ns、不读 backend。修复需作者决定评估器语义，不擅改。
- **SUSPICIOUS（不修，留证据缺口说明）**：
  - `DqcMapLayout`（opt 6 布局阶段）DM0 打分坐标系不匹配：cif_pairs 按虚拟比特索引提取
    （dm_layout.py `_build_sabre_dag`），布局 trial 的初始布局为随机/KL 部分布局（非平凡，layout.rs
    `layout_trial`），而 route.rs `choose_best_swap` 的 DM0 tie-break 把物理 swap 索引直接与虚拟标号
    的 pair 匹配、ctrl2pq 又是物理坐标。routing-only 路径（DqcMapSwap，post-ApplyLayout 平凡初始布局）
    坐标一致、无此问题；且 opt 6 下 skip_routing=True，布局内部 routing 结果被丢弃，故只影响布局选择的
    启发式质量，不影响最终电路语义（隐形传态 oracle 佐证）。补证需要：受控 A/B（布局阶段禁用 DM0
    tie-break）或非平凡布局下的 Rust 单测。
  - `check_swap_needed`：只查 2q 门（代码内 FIXME），bench.py 中计算后未使用（死代码，不入 CSV）。
  - `EvalV3.get_init_layout_ctrl_latency` 返回 0 的 TODO stub；EvalV3 未被基准使用（仅单测引用）。
- 可复现性注记（承 Phase 1）：`iter_KL_mapper.py` 模块级 `random.seed(111)` + 4 秒墙钟预算；
  `DqcMapLayout` 默认 trials=CPU_COUNT——同机确定、跨机不保证逐位一致。
- 产物：`tests/audit_pins_test.py`、`exp/data/audit/pe20.lst`、修复后的 `exp/bench.py`。

## THE GATE — Health Check Report（状态：完成）

- 报告：`docs/health-check-report.md`（中文，六节结构照 skill 模板）。
- 用户已读报告并过 Gate。**用户决定（2026-07-05）**：本工作为其已发表论文，
  不再做任何发表/选会建议；本轮定位为"项目改善"。决策记录见 `docs/DECISIONS.md`。

## Phase 4 — 证据构建（状态：完成，最小规模）

- 预算约束：单条命令 ≤ 30 分钟；完整规模一律 NOT RUN，命令写入 `docs/reproduction-commands.md`。
- **新增实验基础设施（全部 opt-in，默认行为逐字节不变）**：
  - `--layout-heuristic {decay,dqcmap,dm1}`：仅布局阶段的启发式开关（S-2 消融钩子），
    穿透链 bench.py → 各 Compiler.run → generate_dqcmap_pass_manager → DqcMapLayoutPlugin。
  - `--t-eval` + `EvalV2(conf, t_1q=…, t_2q=…)`：使 `--t` 真实作用于评估器（修 S-1 死旋钮）。
  - `KLMapper(…, max_iters=…, rng_seed=…)`：固定迭代预算 + 专用 RNG（可复现性选项）。
- **默认路径回归**：pe_20 审计命令输出与 Phase 3 基线逐字节一致（DEFAULT_PATH_UNCHANGED）；
  全量 pytest 41 passed（原 25 + 审计钉 8 + 改善钉 8）。
- **E1（S-2 布局阶段 DM0 消融，小规模 4 基准 × 3 种子）**：pe_20/qft_20/cc_12 的 #ICCS
  在 A 臂（布局 DM0）与 B 臂（布局 decay）完全相同（19/0/6，三种子皆然）；仅 random_20
  有差异且方差巨大（A: 39/30/99，B: 81/141/18，n=3 不可区分）。与"布局阶段 DM0 打分坐标
  错配、增益主要来自 KL + 路由 DM0"假设一致；全量确认 NOT RUN。
- **E2（S-1 修复验证，pe_20）**：`--t-eval` 下 t=1.0/0.5/0.2 → 总延迟 27.97/26.33/25.35 µs，
  跨控制器占比 34.0%/36.1%/37.5%（器件越快反馈占比越高）；不加开关时与论文路径逐字节一致。
- **E3（多种子，小规模）**：baseline 种子敏感（cc_12 #ICCS 24/43/49），CLASS 结构化基准
  三种子稳定；random 电路双方都高方差。全量统计 NOT RUN。
- **新发现（可复现性）**：`--parallel 0` 串行跑多电路列表时结果漂移（两次运行 random_20/cc_12
  不同），原因是 KL 的模块级全局 RNG 状态 + 墙钟重启预算跨电路耦合；`--parallel 1` 每电路
  独立进程、逐字节稳定（论文 Table II 走的是并行路径，这正是它可复现的原因）。
  证据：`exp/data/audit/phase4/E1_A_run{1,2}.tsv`（串行，diff 非空）vs `E1_A_par{1,2}.tsv`（并行，diff 空）。
- 产物：`exp/data/audit/phase4/`（E1/E2/E3 全部 TSV）、`tests/improvement_pins_test.py`。

## Phase 5 — 可复现性加固（状态：完成，跨机验证除外）

- Fig 7/8 硬编码负债消除：新增 `exp/last_table_vis_from_csv.py`（从论文 CSV 派生数据，
  AST 解析原脚本硬编码数组做一致性自检，不一致即非零退出）。已运行：两组数组 `[OK]`，
  PDF 输出到 `exp/data/audit/`。原脚本未动。
- 每图/表一条命令：`docs/reproduction-commands.md`（VERIFIED 带日期 / NOT RUN 明确标注）。
- 种子与预算显式化：KL 确定性选项已实现并有钉子；接入 bench CLI 为 TODO（`mapping()`
  已支持 kwargs 透传，改动很小）。
- PARTIAL：跨机器逐位一致性无法在本机验证（需第二台机器）。
- NOT RUN：`exp/fidelity_analysis.py`（需 IBM 凭据）。

## Phase 6 — 写作骨架（状态：完成，按用户要求会场中立）

- `docs/paper-skeleton.md`（英文）：工作标题、6 条改善主张（逐句标
  SUPPORTED (small-scale) / PARTIALLY SUPPORTED / NOT YET SUPPORTED）、图先行计划
  （F1–F5，各图注明数据来源与 NOT RUN 状态）、章节-证据映射、摘要草稿
  （只含有小规模证据支撑的句子，措辞降级为 preliminary/consistent-with）。
- 无任何 venue/deadline 内容（遵用户指令）。

## 收尾

- 产物总清单：`docs/DELIVERABLES.md`。
