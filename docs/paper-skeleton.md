# Manuscript Skeleton — Ablation & Reproducibility Hardening of CLASS

> Status: skeleton + abstract draft only. Venue-neutral by request (no venue
> targets or deadlines in this document). Written in English as a paper
> artifact; see `docs/reproduction-commands.md` for the evidence status of
> every command referenced here.
>
> Tagging convention (applies to every claim below):
> **SUPPORTED (small-scale)** = backed by an experiment actually run in this
> engagement (4 benchmarks x 3 seeds, or pe_20 sensitivity);
> **NOT YET SUPPORTED** = requires the full-scale runs listed as NOT RUN.

## Working title

*Where Does the Gain Come From? An Ablation and Reproducibility Study of
Controller-Centric Layout Synthesis for Dynamic Quantum Circuits*

## Improvement-claims statement (delta analogue, per-sentence tags)

1. CLASS's end-to-end improvement over the SABRE baseline in cross-controller
   feedback pairs (#ICCS) reproduces bit-for-bit from the released artifact on
   one machine. **SUPPORTED (small-scale + full Table II reproduction,
   2026-07-05)**
2. The layout-stage controller-aware tie-break (DM0 inside `DqcMapLayout`)
   contributes little or nothing to the final #ICCS: on structured benchmarks
   (pe_20, qft_20, cc_12) disabling it changes nothing across 3 seeds, and a
   static code-path analysis shows its score compares virtual-indexed cif
   pairs against physical swap indices under a non-trivial starting layout.
   **PARTIALLY SUPPORTED (small-scale; static analysis)** — full-suite,
   multi-seed confirmation **NOT YET SUPPORTED**.
3. The measured gains are therefore attributable to the KL-style initial
   partitioning plus the routing-stage DM0 tie-break (where coordinates are
   consistent). **NOT YET SUPPORTED** (requires the full ablation matrix,
   including a KL-off arm, i.e. comparing opt 3 / opt 6 / layout-decay arms
   at scale).
4. Making the device-evolution knob (`--t`) actually affect the evaluator
   strengthens, not weakens, the paper's motivation: as two-qubit gates get
   faster, the feedback-latency share of total runtime grows (pe_20: 34.0%
   at t=1.0 to 37.5% at t=0.2). **SUPPORTED (small-scale, single benchmark)**
   — trend across the full suite **NOT YET SUPPORTED**.
5. The baseline (Qiskit SABRE) is seed-sensitive (cc_12 #ICCS ranges 24-49
   over 3 seeds) while CLASS is seed-stable on structured benchmarks;
   single-seed headline numbers therefore under-report the robustness of the
   improvement on structured circuits and over-trust random-circuit numbers.
   **SUPPORTED (small-scale)** — full-suite variance statistics
   **NOT YET SUPPORTED**.
6. Run-to-run reproducibility of the released artifact depends on execution
   mode: parallel execution (one process per circuit, fresh module-seeded RNG)
   is bit-stable, while serial execution of a multi-circuit list drifts
   because the KL mapper's module-global RNG state and wall-clock restart
   budget couple circuits together. With the new opt-in deterministic KL
   options (fixed iteration budget + dedicated seeded RNG), same-machine
   determinism no longer depends on execution mode. **SUPPORTED
   (small-scale: two serial runs diverged on random_20/cc_12; two parallel
   runs identical; pinned unit test for the deterministic options)** —
   cross-machine bit-stability **NOT YET SUPPORTED** (needs a second machine).

## Figure plan (figures first; each names its data source)

| Fig | Content | Data | Status |
|---|---|---|---|
| F1 | #ICCS per benchmark, three arms: baseline / CLASS (layout DM0) / CLASS (layout decay), error bars over seeds | full-suite ablation (E1 full) | NOT RUN (small-scale TSVs in `exp/data/audit/phase4/E1_*.tsv`) |
| F2 | Feedback-latency share vs two-qubit gate-time scale t, per benchmark family | E2 full sweep | NOT RUN (pe_20 slice in `exp/data/audit/phase4/E2_teval.tsv`) |
| F3 | Seed-variance distribution (baseline vs CLASS), per benchmark | E3 full | NOT RUN (3-seed slice in `exp/data/audit/phase4/E3_*.tsv`) |
| F4 | Reproducibility matrix: execution mode x KL budget mode -> bit-stability | serial/parallel + deterministic-KL runs | small-scale evidence complete; cross-machine column NOT RUN |
| F5 | (carried over) Type-I/II improvement, now CSV-derived | `exp/last_table_vis_from_csv.py` | DONE (regenerated 2026-07-05) |

## Section outline (each section names its supporting evidence)

1. **Introduction** — dynamic circuits, controller partitioning, why
   feedback-latency share grows as gates get faster (F2; claim 4).
2. **Background: the CLASS pipeline** — KL partition mapper, DqcMapLayout
   (layout-stage DM0), DqcMapSwap (routing-stage DM0); coordinate systems of
   cif pairs in each stage (code refs: `dqcmap/passes/dm_layout.py`,
   `dm_swap.py`, `rust/accelerate/src/sabre/route.rs`, `dqcmap/state.rs`).
3. **The coordinate-consistency question** — static analysis of the
   layout-stage DM0 score (claim 2); minimal description of the ablation
   hook (`--layout-heuristic`).
4. **Ablation study** — F1; claims 2-3. Includes the KL-off arm
   (opt 3 vs opt 6) to isolate the mapper's contribution.
5. **Device-evolution sensitivity** — F2; claim 4; the `--t-eval` fix and
   why the legacy path was inert (S-1 in `docs/health-check-report.md`).
6. **Statistical robustness** — F3; claim 5.
7. **Reproducibility engineering** — F4; claim 6; deterministic KL options,
   CSV-derived figures, pinned regression tests (16 pins across
   `tests/audit_pins_test.py` and `tests/improvement_pins_test.py`).
8. **Discussion & limitations** — EvalV2's serial latency model remains a
   modeling simplification (unchanged here); no hardware runs; Fake127QPulseV1
   is a retired device model.

## Abstract draft (only claims with small-scale evidence; hedged accordingly)

> Controller-centric layout synthesis (CLASS) reduces cross-controller
> feedback in dynamic quantum circuits by combining a Kernighan-Lin-style
> initial partitioning with a controller-aware routing tie-break. Starting
> from the released CLASS artifact — whose headline table we reproduce
> bit-for-bit — we ask *which component produces the gain, and how robust is
> it?* A controlled ablation switch that disables only the layout-stage
> controller-aware scoring leaves the cross-controller feedback count
> unchanged on structured benchmarks (pe, qft, cc; three seeds), consistent
> with a coordinate-system analysis of the layout-stage score; preliminary
> evidence thus attributes the improvement chiefly to the initial
> partitioning and the routing-stage tie-break. Restoring the artifact's
> device-evolution knob shows that faster two-qubit gates *increase* the
> feedback-latency share of runtime (34% to 38% on pe-20 as gate time scales
> from 1.0x to 0.2x), reinforcing the original motivation. We further find
> the SABRE baseline seed-sensitive where CLASS is seed-stable on structured
> circuits, and we trace a run-to-run irreproducibility of the artifact's
> serial mode to a shared global RNG and wall-clock restart budget in the
> mapper, which we make deterministic behind opt-in options that leave all
> published defaults byte-identical. All findings above are from
> small-scale runs (four benchmarks, three seeds, one machine); full-suite
> confirmation commands ship with the artifact.

*(Every sentence in this abstract corresponds to claims 1-6; sentences
covering claims 2-3 are phrased as "preliminary/consistent-with" because the
full-scale arm is NOT RUN.)*

## Experiment matrix still owed (full scale, commands in reproduction-commands.md)

- E1 full: 14 benchmarks x >=3 seeds x {A, B} arms, plus opt-3 (KL-only) arm.
- E2 full: t in {1.0, 0.5, 0.2, 0.1} x 14 benchmarks x {baseline, CLASS}.
- E3 full: >=5 seeds, mean +/- std summary script (TODO, not written).
- Cross-machine determinism check for the deterministic-KL mode.
