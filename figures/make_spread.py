#!/usr/bin/env python3
"""Per-isolate cross-species spread figure for NanoSpecies-50 (Bonito sup)."""
import csv, statistics
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "logs" / "bonito_sup_all.csv"
rows = list(csv.DictReader(open(CSV)))

# group by genus
genus = {}
for r in rows:
    g = r["isolate"].split("_")[0]
    genus.setdefault(g, []).append(float(r["median"]) * 100.0)

# order genera by median
order = sorted(genus, key=lambda g: statistics.median(genus[g]))
data = [genus[g] for g in order]

fig, ax = plt.subplots(figsize=(3.4, 3.4))
parts = ax.boxplot(
    data, vert=False, widths=0.6, patch_artist=True,
    showfliers=True, medianprops=dict(color="black"),
)
for pc in parts["boxes"]:
    pc.set_facecolor("#9ecae1")
    pc.set_alpha(0.8)

# overlay individual isolates
for i, vals in enumerate(data, start=1):
    ax.scatter(vals, [i] * len(vals), s=8, color="#08519c", alpha=0.6, zorder=3)

overall = statistics.median([float(r["median"]) * 100 for r in rows])
ax.axvline(overall, color="red", ls="--", lw=1, label=f"pooled median {overall:.1f}\\%")

ax.set_yticks(range(1, len(order) + 1))
ax.set_yticklabels(order, fontsize=7)
ax.set_xlabel("Median read identity (\\%)")
ax.set_xlim(86, 96)
ax.grid(True, axis="x", ls=":", alpha=0.4)
ax.legend(fontsize=7, loc="lower right")
fig.tight_layout(pad=0.3)
fig.savefig(ROOT / "figures" / "spread.pdf", bbox_inches="tight")
print("wrote spread.pdf; overall median=%.2f" % overall)
