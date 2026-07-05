"""CSV-derived replacement for the hardcoded arrays in ``last_table_vis.py``.

``last_table_vis.py`` (Fig. 7/8: Type-I/II improvement percentages) draws its
bars from arrays written inline in the script. This script derives the same
data from the committed results CSV instead, cross-checks it against the
inline arrays of the original script (parsed via ``ast``, without executing
it), and then renders the same two figures.

Usage:
    python exp/last_table_vis_from_csv.py \
        [--csv exp/data/paper/benchmarks.lst_baseline_multi_ctrl_dqcswap_dqcmap_opt_6_ctrl_4.csv] \
        [--out exp/data/audit]

Exits non-zero if the CSV-derived arrays disagree with the original script's
hardcoded ones, so it doubles as a consistency check.
"""

import argparse
import ast
import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

DEFAULT_CSV = (
    "exp/data/paper/benchmarks.lst_baseline_multi_ctrl_dqcswap_dqcmap_opt_6_ctrl_4.csv"
)
ORIGINAL_SCRIPT = os.path.join(os.path.dirname(__file__), "last_table_vis.py")

# Type-I: dynamic circuits whose feedback can (ideally) be fully localized
TYPE_I = [("qft", 20), ("qft", 30), ("qft", 40), ("qft", 50)]
# Type-II: the rest, in the display order used by the paper figure
TYPE_II = [
    ("cc", 12),
    ("cc", 32),
    ("pe", 20),
    ("pe", 30),
    ("pe", 40),
    ("pe", 50),
    ("random", 20),
    ("random", 30),
    ("random", 40),
    ("random", 50),
]


def load_num_cif_pairs(csv_path):
    """Return {(bench, nq, compiler): num_cif_pairs} from a bench.py CSV."""
    table = {}
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            key = (
                row["bench_name"],
                int(row["num_qubits"]),
                row["compiler_type"],
            )
            table[key] = int(float(row["num_cif_pairs"]))
    return table


def derive(csv_path):
    table = load_num_cif_pairs(csv_path)

    def series(benches, compiler):
        return [table[(b, n, compiler)] for b, n in benches]

    type_i_data = {
        "name": [f"{b}-{n}" for b, n in TYPE_I],
        "baseline": series(TYPE_I, "baseline"),
        "class": series(TYPE_I, "multi_ctrl"),
    }
    type_ii_data = {
        "name": [f"{b}-{n}" for b, n in TYPE_II],
        "baseline": series(TYPE_II, "baseline"),
        "class": series(TYPE_II, "multi_ctrl"),
    }
    return type_i_data, type_ii_data


def hardcoded_from_original(script_path):
    """Parse type_i_data / type_ii_data literals out of last_table_vis.py."""
    with open(script_path) as f:
        tree = ast.parse(f.read())
    found = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in (
                "type_i_data",
                "type_ii_data",
            ):
                found[target.id] = ast.literal_eval(node.value)
    return found.get("type_i_data"), found.get("type_ii_data")


def improvements(data):
    """Same arithmetic as last_table_vis.py, including the aggregate average."""
    imp = []
    for base, cls in zip(data["baseline"], data["class"]):
        imp.append(0 if base == 0 else (base - cls) / base * 100)
    total_base = sum(data["baseline"])
    total_cls = sum(data["class"])
    imp.append((total_base - total_cls) / total_base * 100)
    return data["name"] + ["Average"], imp


def plot(names, imp, color, avg_color, out_path):
    fig_size = (10, 4)
    fontsize = 27
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.weight"] = "bold"
    plt.rcParams["xtick.labelsize"] = fontsize - 6
    plt.rcParams["ytick.labelsize"] = fontsize - 2
    plt.rcParams["axes.labelsize"] = fontsize
    plt.rcParams["axes.labelweight"] = "bold"
    plt.rcParams["legend.fontsize"] = fontsize - 5

    plt.figure(figsize=fig_size)
    x = np.arange(len(names))
    bars = plt.bar(x, imp, width=0.7, color=color, edgecolor="black", linewidth=1)
    bars[-1].set_color(avg_color)
    for i, bar in enumerate(bars):
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height() + 1,
            f"{imp[i]:.2f}%",
            ha="center",
            va="bottom",
            fontsize=fontsize - 15,
            fontweight="bold",
            rotation=45,
        )
    plt.ylabel("Improvement (%)", fontsize=fontsize - 5)
    plt.xticks(x, names, rotation=45, ha="right")
    plt.ylim(0, 105)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--out", default="exp/data/audit")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    type_i, type_ii = derive(args.csv)
    orig_i, orig_ii = hardcoded_from_original(ORIGINAL_SCRIPT)

    ok = True
    for label, derived, orig in (
        ("type_i_data", type_i, orig_i),
        ("type_ii_data", type_ii, orig_ii),
    ):
        if orig is None:
            print(f"[WARN] could not locate {label} in {ORIGINAL_SCRIPT}")
            continue
        if derived != orig:
            ok = False
            print(f"[MISMATCH] {label}:")
            print(f"  CSV-derived: {derived}")
            print(f"  hardcoded  : {orig}")
        else:
            print(f"[OK] {label}: CSV-derived data matches hardcoded arrays")

    names_i, imp_i = improvements(type_i)
    names_ii, imp_ii = improvements(type_ii)
    plot(
        names_i,
        imp_i,
        "#3366cc",
        "#00008B",
        os.path.join(args.out, "type_i_improvement_percentage.pdf"),
    )
    plot(
        names_ii,
        imp_ii,
        "#ff7300",
        "#B22222",
        os.path.join(args.out, "type_ii_improvement_percentage.pdf"),
    )
    print(f"[OK] figures written to {args.out}")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
