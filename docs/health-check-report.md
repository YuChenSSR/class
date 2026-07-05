# 体检报告：class（CLASS: Controller-Centric Layout Synthesizer for DQC）

> 生成于 quantum-repo-to-paper 流水线 Phase 0–3，按指令停在 THE GATE，未进入 Phase 4。
> 全部结论均以"实际运行/核对过"为准；未运行项明确标注 NOT RUN。引用均已联网核实（访问日期 2026-07-05）。

## 1. 结论

这个仓库**不是**一个待抢救的 vibe-coded 项目，而是一篇**已发表论文的官方代码库的 fork**：README 所述论文 "CLASS: A Controller-Centric Layout Synthesizer for Dynamic Quantum Circuits" 已由同组作者（含 Yu Chen）发表于 **ICCAD 2025**（CCF-B，Best Paper Candidate；DOI: 10.1109/ICCAD66269.2025.11240650，arXiv:2509.15742）。代码质量总体是真实的：主结果 Table II 我逐行复现且与仓库内论文数据**完全一致**，核心原语通过了手算锚点、隐形传态语义等价 oracle、不变量检查三类独立验证，审计中只发现一个已证明的工程 bug（已修）和两处不影响已发表结论的可疑点。因此对"把本仓库现有工作投 CCF-A"这一目标，红绿灯是**红灯**——同一工作不可重投；正确的路是**以本代码库为基础做增量研究**（fork 中已有的非星型控制器拓扑探索是现成起点），走 DAC/MICRO 新会议论文或 TCAD 期刊扩展两条线之一。建议：pivot（方向见第 6 节路线图，成本已沉没最少——这正是 cheapest-kill-first 想要的结果）。

## 2. 能不能跑

**环境**：仓库自带 `.venv`（Python 3.11.13，qiskit 1.1.1，Rust 扩展 `dqcmap._accelerate` 已编译可导入）。`pytest` 原有 25 项测试通过；`cargo test --no-default-features` 8 项通过。为跑 cc 基准补初始化了 `benchmarks/QASMBench` 子模块（浅克隆）。

**本次审计施加的修改**（无任何 git commit/push）：

- `exp/bench.py`：修复 `--c > 1` 崩溃 bug（见第 3 节 BUG-1）。
- 新增 `tests/audit_pins_test.py`（8 个回归钉子）、`docs/PROGRESS.md`、本报告、`exp/data/audit/`（复现产物）。

**结果产物清单（REAL vs FAKE/STUB）**：

| 产物 | 分类 | 证据 |
|---|---|---|
| Table II（主结果，14 基准 × 2 编译器） | **REAL** | 本机重跑 28/28 行与 `exp/data/paper/*.csv` 逐行一致，复现件 `exp/data/audit/merged_table2.csv` |
| Fig 7/8（Type-I/II 改善率） | **REAL（但硬编码）** | `exp/last_table_vis.py` 画图数据为脚本内联数组，不读 CSV——vibe-coding 典型模式；已逐值核对与论文 CSV 完全一致，故判 REAL，但属可复现性负债 |
| Fig 9（控制器数影响） | **REAL** | 输入 txt 原本缺失，已重新生成 `exp/data/audit/ctrl_num_impact.txt` 并出图 |
| Fig 10（运行时分析） | **REAL** | 同上，`runtime_analysis_same_ctrl.txt` 重新生成并出图 |
| `exp/fidelity_analysis.py` | **NOT RUN** | 模块顶层 `QiskitRuntimeService()` 需 IBM Quantum 账号凭据，无法无人值守运行 |
| `exp/NonStar*.py`（fork 新增探索） | **REAL（可运行）** | 实际运行通过；未接入基准管线，属初步探索 |
| `EvalV3` | **STUB（未使用）** | `get_init_layout_ctrl_latency` 是返回 0 的 TODO stub；基准全部用 `EvalV2`，EvalV3 仅单测引用 |

## 3. 正确性

审计方法：每个核心原语至少两种独立方法（手算锚点 / oracle 模拟 / 暴力重算 / 文档核对），全部钉入 `tests/audit_pins_test.py`（8 项，与原有测试合计 **33 passed**）。

| # | 审计项 | 分类 | 证据 |
|---|---|---|---|
| 1 | `EvalV2.calc_orig_latency`（1q=20ns、2q=40ns 串行求和，measure 不计） | **VERIFIED** | 手算锚点：2×H + CX + measure = 80ns，钉子通过。注意这是"门数串行和"模型，不考虑并行调度——是建模选择而非 bug，但审稿人会挑战（见第 5 节） |
| 2 | `Eval.calc_ctrl_latency`（同控制器 50ns / 跨控制器 500ns 分类计数） | **VERIFIED** | 手算锚点：127 比特 trivial 分区下对 [1,0]（同）与 [3,15]（跨）的分类与求和逐项核对；`num_cif_pairs` 只计跨控制器对 |
| 3 | `get_cif_qubit_pairs` 的 ClassicalRegister 级条件语义 | **VERIFIED** | 手工推导：creg 级条件应与所有已测入该 creg 的比特配对；构造电路验证得 [[2,0],[2,1]]，钉子通过 |
| 4 | 全流程编译语义等价（`MultiCtrlCompiler` opt 6 + dqcswap + DM0） | **VERIFIED** | 隐形传态 oracle：编译前后 Aer 模拟 4096 shots，被传态比特恒为 1；解析锚点 + 模拟器两法独立 |
| 5 | `EvalV2.num_cif_pairs` 记账 | **VERIFIED** | 对编译后电路与独立暴力重算逐对比对一致 |
| 6 | `KLMapper` 输出合法性与目标函数 | **VERIFIED** | 不变量：输出单射、值域⊆控制器比特并集；`evaluate_mapping` 与独立重算一致。（KL 是启发式，无最优性主张，不测最优性） |
| 7 | Rust `CifPairs`/`DqcMapState`/路由 | **VERIFIED（部分）** | cargo 单测 8 项通过；端到端语义由第 4 项 oracle 覆盖。DM1 打分权重 0.1 为魔数，论文未消融 |
| 8 | 主张级关系：pe_20（4 控制器）CLASS < baseline 的跨控制器反馈对数 | **VERIFIED** | 钉子以不等式固定论文核心关系（精确值受 KL 墙钟预算与 CPU 数影响，跨机不逐位保证，故不钉常数） |
| BUG-1 | `exp/bench.py --c > 1` 且 `--bench` 非文件时 IndexError | **BUG（已修）** | 最小重现：`--n 6 --c 2` 修复前必崩（`qc_nq_lst = nq_lst` 长度错配，上游 commit 705414c 引入）；修复为 `[n] * num_circuits`，修复后运行正常、pytest 全绿。不影响任何论文数据（论文路径走 `--bench` 文件分支） |
| S-1 | `--t` 旋钮（README 称模拟先进器件的 2q 门时间缩放）在主基准路径**无效** | **SUSPICIOUS（死旋钮，实验证明，未修）** | pe_20 在 `--t 0.2` 与 `--t 1.0` 输出逐字节一致；代码链：`update_backend_cx_time_v2` 改 backend 脉冲属性，但 `EvalV2` 硬编码 20/40ns 不读 backend。修复需作者裁定评估器语义（换回脉冲级 `Eval` 会改变全部数字），不擅改 |
| S-2 | `DqcMapLayout`（opt 6 布局阶段）DM0 打分坐标系疑似错配 | **SUSPICIOUS（未修）** | cif_pairs 按**虚拟**比特索引提取（`dm_layout.py::_build_sabre_dag`），布局 trial 初始布局非平凡（随机/KL 部分布局，`layout.rs::layout_trial`），而 `route.rs::choose_best_swap` 的 DM0 tie-break 把**物理** swap 索引直接和虚拟标号的 pair 匹配（`ctrl2pq` 又是物理坐标）。routing-only 路径（`DqcMapSwap`，post-ApplyLayout 平凡初始布局）坐标一致、正确；且 opt 6 下 `skip_routing=True`，布局内部路由被丢弃——所以只影响布局选择的启发式质量，不影响电路语义（第 4 项 oracle 佐证）。**补证需要**：布局阶段禁用 DM0 tie-break 的受控 A/B，或非平凡布局下的 Rust 单测。若坐实，含义是论文增益主要来自 KL 初始布局 + 路由阶段 DM0，布局阶段的控制器感知打分可能在做无规律 tie-break |
| S-3 | `check_swap_needed` | **SUSPICIOUS（轻微，死代码）** | 只检查 2q 门（代码内 FIXME 自认），bench.py 中算完未使用、不入 CSV |

**可复现性注记**：`iter_KL_mapper.py` 模块级 `random.seed(111)` + **4 秒墙钟预算**、`DqcMapLayout` 默认 trials=CPU_COUNT——同机逐位确定（我三次重跑一致），跨机器/核数不保证。这在论文口径下可接受，但做期刊扩展时应改为迭代数预算 + 显式种子。

## 4. 新颖性与定位

**关键事实**：本工作已发表——Chen, Zhao, Li, Li, Wang, Han, Wang, "CLASS: A Controller-Centric Layout Synthesizer for Dynamic Quantum Circuits," **ICCAD 2025**, DOI: 10.1109/ICCAD66269.2025.11240650, arXiv:2509.15742（访问 2026-07-05）。**同一内容不可再投任何会议，红灯。** 以下 delta 分析针对"以本代码库为基础的下一篇工作"。

**近邻工作**（均已核实 ID，访问 2026-07-05）：

- Distributed-HISQ（同组），MICRO 2025（CCF-A），DOI: 10.1145/3725843.3756048，arXiv:2509.04798 —— 分布式指令集与控制器架构层面，与 CLASS 互补，也是最需要区分的"自家人"。
- AC/DC，arXiv:2412.07969（预印本）—— 动态电路的经典控制资源问题。
- MERA，arXiv:2511.10921（预印本）—— MCM 误差感知编译；与延迟感知正交，可做联合优化对比。
- Bäumer et al. 动态电路 QFT，arXiv:2403.09514 —— 动态电路应用侧的标准参照。
- QuPort，arXiv:2605.12583（预印本）—— 多 QPU 拓扑/端口感知编译。
- DQC 网络拓扑与比特分配联合优化，DOI: 10.1109/QCNC64685.2025.00062。

**下一篇工作的 delta 陈述（草案，待用户选方向后收紧）**：CLASS（ICCAD'25）假设控制器间通信为星型/均匀代价，且只在给定控制器分区下做布局与路由；Distributed-HISQ（MICRO'25）解决的是指令与控制架构而非布局综合。本仓库 fork 中的 NonStar 探索指向一个两者都没覆盖的问题：**当控制器间网络拓扑非均匀（链、树、mesh）时，控制器分区、网络拓扑与布局/路由的联合优化**。若加上真机动态电路验证与周期精确的延迟模型（修掉 S-1 的死旋钮、回应第 5 节的评估模型质疑），构成一篇独立的系统/EDA 论文。

**目标会场与截稿**（CCF 分级经 ccf.org.cn 及镜像核实，访问 2026-07-05）：

- 首选 **DAC 2027**（CCF-A）：2027-07-10/16 圣何塞；CFP 未出（dac.com/2026/events/dac-2027），按 DAC 2026 节奏（摘要 2025-11-11、全文 2025-11-18/19）推算 **2026 年 11 月中截稿**——距今约 4 个月，紧但可行。
- 备选 **MICRO 2026**（CCF-A，偏体系结构叙事）或 **TCAD**（CCF-A 期刊，滚动投稿）：TCAD 走"ICCAD'25 扩展 ≥30% 新内容"的常规通道，风险最低。

**红绿灯：红**（对重投既有工作）；对上述 pivot 方向，初判**黄**（近邻密集但联合优化空档真实存在），需在选定方向后做一轮针对性检索确认。

## 5. 审稿人视角的缺口（直说）

1. **"这不就是你们 ICCAD'25 的论文吗？"**——致命且无法辩解。任何投稿必须有明确的、量化的新增量；NonStar 两个脚本目前只是玩具（未接入基准、无对照、无数据）。
2. **评估模型太弱**：`EvalV2` 是"门数×固定时长的串行和 + 反馈次数×固定延迟"，无并行调度、无真实脉冲时长；且 `--t`（器件演进敏感性分析的旋钮）在该路径下是死的（S-1）。DAC/MICRO 审稿人会要求周期精确模拟或真机验证，尤其 IBM 已开放动态电路真机。
3. **基线偏弱**：只比 Qiskit 1.1.1 SABRE（固定 seed 1900，单种子无误差棒）；没有 tket、没有更新版 Qiskit、没有对 KL-初始布局/路由-DM0 的组件消融（论文有 map/map+route/full 三档，但 S-2 说明布局阶段贡献存疑，恰恰需要这组消融来自证）。
4. **可复现性负债**：KL 的 4 秒墙钟预算和 CPU_COUNT 相关 trials 意味着"换台机器数字就变"；Fig 7/8 画图数据硬编码。artifact evaluation 会扣分。
5. **S-2 若被审稿人发现**（开源代码，会被读），"控制器感知布局"这一卖点的机制解释会被质疑。下一篇工作应当先自己做 A/B 把它坐实或修掉。

## 6. 路线图（Gate 后待选，按序排列）

| # | 任务 | 工作量估计 | kill 判据 |
|---|---|---|---|
| 1 | **选方向**：A = TCAD 期刊扩展（低风险）；B = NonStar 联合优化投 DAC 2027（高收益）。二选一，不要并行 | 决策，0.5 天 | — |
| 2 | 针对所选方向做一轮聚焦新颖性检索（尤其 Distributed-HISQ 的后续、2026 年 DAC/ICCAD 在投/已发的控制器拓扑工作） | 2–3 天 | 若已有工作做了"非均匀控制器网络下的布局综合"，方向 B 终止，退回方向 A |
| 3 | 补 S-2 的 A/B 实验（布局阶段 DM0 tie-break 开/关，全基准），坐实或修正坐标系 | 3–5 天 | 若关掉后结果不变差，论文叙事改为"KL 布局 + 路由感知"，布局阶段卖点删除 |
| 4 | 修 S-1：评估器改为可配置（脉冲级 `Eval` 或参数化 `EvalV2`），让 `--t` 真实生效，重跑器件演进敏感性 | 1 周 | 若在真实门时长下增益消失（反馈延迟占比过小），需重新定位贡献场景（如长程反馈/大规模 MCM 电路） |
| 5 | NonStar 原型转正：控制器网络拓扑（链/树/mesh）建模 + 分区-布局联合优化算法 + 接入 bench 管线 | 3–4 周 | 若相对星型假设的增益 < ~5%，方向 B 终止 |
| 6 | 强基线与统计：tket + 最新 Qiskit、多种子 + 误差棒、组件消融矩阵 | 2 周 | — |
| 7 | 真机验证（IBM 动态电路）或周期精确控制器模拟器二选一 | 2–4 周 | 无真机额度且模拟器不可行 → 降级投 TCAD 而非 DAC |
| 8 | 可复现性加固：KL 改迭代预算、种子入配置、Fig 7/8 改读 CSV、每图一命令 | 1 周 | — |
| 9 | 论文骨架（Phase 6）：图先行，delta 逐句对应实验 | 2 周 | — |

**Gate 决定权在你**：读完本报告后选方向 1-A 或 1-B（或都不做），我再进 Phase 4。
