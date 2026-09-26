"""
Generates the illustrative SOR baseline-vs-optimized bar chart used on the
Impact & Benefits slide. Values are ILLUSTRATIVE TARGETS (physics-model
based projection), not measured field results — labelled as such on the
chart itself per notes/BUILD_NOTES.md.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

labels = ["Industry-typical\nCSS baseline", "Optimizer target"]
values = [6.0, 3.2]
colors = ["#b0453f", "#2f7a4f"]

fig, ax = plt.subplots(figsize=(5.0, 3.2), dpi=200)
bars = ax.bar(labels, values, color=colors, width=0.5)

for bar, val in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 0.08, f"{val} t/m\u00b3",
            ha="center", va="bottom", fontsize=13, fontweight="bold", color="#222")

ax.set_ylabel("Steam-Oil Ratio (t/m\u00b3)", fontsize=11)
ax.set_ylim(0, 8.5)
ax.set_title("SOR: Literature Baseline vs Optimizer Target", fontsize=12, fontweight="bold")
ax.text(0.5, -0.30,
        "Baseline = literature CSS avg (3-8 range, Baghewala's own SOR not publicly reported).\n"
        "Target = physics-simulated (internal consistency-checked; field validation is next phase).",
        transform=ax.transAxes, ha="center", va="top", fontsize=7.5, color="#555", style="italic")

for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.tick_params(labelsize=10)

fig.tight_layout(rect=[0, 0.06, 1, 1])
fig.savefig(Path(__file__).resolve().parent / "assets" / "sor_chart.png",
            transparent=True)
print("chart saved")
