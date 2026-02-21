import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from esg_standards import ESG_METRICS


class Dashboard:
    """
    matplotlib-based ESG data quality dashboard with multiple sections:
    (A) Category-wise extraction bars
    (B) Quality radar chart
    (C) Metric-level completeness grid
    (D) Confidence distribution histogram
    (E) Validation check pass rates
    """

    C = {
        "Environmental": "#27ae60", "Social": "#2980b9",
        "Governance": "#8e44ad",
        "green": "#27ae60", "yellow": "#f39c12", "red": "#e74c3c",
        "blue": "#2980b9", "dark": "#2c3e50", "bg": "#f8f9fa",
    }

    def __init__(self, df, scores, company="Sample Corp"):
        self.df = df
        self.scores = scores
        self.company = company

    def render(self, save_path=None):
        fig = plt.figure(figsize=(20, 24), facecolor=self.C["bg"])
        gs = GridSpec(3, 2, figure=fig, hspace=0.32, wspace=0.28,
                      top=0.93, bottom=0.03, left=0.07, right=0.96)

        fig.suptitle(
            f"ESG Data Extraction & Quality Dashboard — {self.company}",
            fontsize=22, fontweight="bold", color=self.C["dark"], y=0.97,
        )

        self._category_bars(fig.add_subplot(gs[0, 0]))
        self._radar(fig.add_subplot(gs[0, 1], polar=True))
        self._completeness_grid(fig.add_subplot(gs[1, :]))
        self._confidence_hist(fig.add_subplot(gs[2, 0]))
        self._check_bars(fig.add_subplot(gs[2, 1]))

        # 

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight",
                        facecolor=fig.get_facecolor())
            print(f"  ✓ Saved → {save_path}")
        plt.show()
        return fig

    # (A) Category-wise extraction bars
    def _category_bars(self, ax):
        cats = ["Environmental", "Social", "Governance"]
        found_ids = set(self.df["metric_id"].unique()) if len(self.df) else set()
        ext, mis = [], []
        for cat in cats:
            tgt = {m["id"] for m in ESG_METRICS if m["category"] == cat}
            ext.append(len(found_ids & tgt))
            mis.append(len(tgt) - len(found_ids & tgt))

        x = np.arange(len(cats))
        ax.bar(x, ext, 0.55, label="Extracted",
               color=[self.C[c] for c in cats], alpha=0.85,
               edgecolor="white", linewidth=1.5)
        ax.bar(x, mis, 0.55, bottom=ext, label="Missing",
               color=[self.C[c] for c in cats], alpha=0.25,
               edgecolor="white", linewidth=1.5, hatch="///")

        for i, (e, m) in enumerate(zip(ext, mis)):
            if e: ax.text(i, e / 2, str(e), ha="center", va="center",
                          fontweight="bold", fontsize=14, color="white")
            if m: ax.text(i, e + m / 2, str(m), ha="center", va="center",
                          fontsize=12, color="#7f8c8d")

        ax.set_xticks(x)
        ax.set_xticklabels(cats, fontsize=11)
        ax.set_ylabel("Metrics", fontsize=11)
        ax.set_title("Extraction Coverage by Category",
                      fontsize=14, fontweight="bold", pad=12)
        ax.legend(fontsize=10)
        ax.set_ylim(0, max(e + m for e, m in zip(ext, mis)) * 1.25 + 0.5)
        ax.spines[["top", "right"]].set_visible(False)

    # (B) Quality radar chart
    def _radar(self, ax):
        labels = list(self.scores.keys())
        vals = list(self.scores.values())
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        vals_c = vals + [vals[0]]
        angles_c = angles + [angles[0]]

        ax.set_facecolor(self.C["bg"])
        ax.plot(angles_c, vals_c, "o-", lw=2.5, color=self.C["blue"], ms=8)
        ax.fill(angles_c, vals_c, alpha=0.18, color=self.C["blue"])
        ax.set_xticks(angles)
        ax.set_xticklabels([l.upper() for l in labels], fontsize=9,
                           fontweight="bold")
        ax.set_ylim(0, 1)
        ax.set_yticks([.2, .4, .6, .8, 1.0])
        ax.set_yticklabels(["20%", "40%", "60%", "80%", "100%"],
                           fontsize=7, color="#95a5a6")
        ax.set_title("Data Quality Dimensions",
                      fontsize=14, fontweight="bold", pad=24)

        for a, v in zip(angles, vals):
            ax.annotate(f"{v:.0%}", xy=(a, v), fontsize=10,
                        fontweight="bold", ha="center", va="bottom",
                        color=self.C["dark"],
                        xytext=(0, 10), textcoords="offset points")

    # (C) Metric-level completeness grid
    def _completeness_grid(self, ax):
        cat_order = ["Environmental", "Social", "Governance"]
        sorted_m = sorted(ESG_METRICS,
                          key=lambda m: cat_order.index(m["category"]))
        found = set(self.df["metric_id"].unique()) if len(self.df) else set()

        labels, statuses = [], []
        for m in sorted_m:
            labels.append(f"{m['id']}  {m['name_en']}")
            if m["id"] not in found:
                statuses.append(0.0)
            else:
                row = self.df[self.df["metric_id"] == m["id"]].iloc[0]
                statuses.append(1.0 if row["validation_score"] >= 0.8 else 0.5)

        color_map = {1.0: self.C["green"],
                     0.5: self.C["yellow"],
                     0.0: self.C["red"]}
        status_txt = {1.0: "✓ Valid", 0.5: "⚠ Review", 0.0: "✗ Missing"}
        y = np.arange(len(labels))

        ax.barh(y, [1] * len(labels),
                color=[color_map[s] for s in statuses],
                alpha=0.82, edgecolor="white", linewidth=2.5, height=0.72)

        for i, (lbl, s) in enumerate(zip(labels, statuses)):
            ax.text(0.015, i, lbl, va="center", fontsize=9.5,
                    color="white", fontweight="bold")
            ax.text(0.985, i, status_txt[s], va="center", ha="right",
                    fontsize=9.5, color="white", fontweight="bold")

            mid = sorted_m[i]["id"]
            if mid in found:
                row = self.df[self.df["metric_id"] == mid].iloc[0]
                val_str = f'{row["value"]:,.1f} {row["unit"]}'
                ax.text(0.55, i, val_str, va="center", ha="center",
                        fontsize=9, color="white", fontstyle="italic")

        ax.set_xlim(0, 1); ax.set_ylim(-0.5, len(labels) - 0.5)
        ax.set_yticks([]); ax.set_xticks([])
        ax.invert_yaxis()
        ax.set_title("Metric-Level Completeness & Validation",
                      fontsize=14, fontweight="bold", pad=12)
        ax.spines[:].set_visible(False)

        legend_items = [
            mpatches.Patch(color=self.C["green"], alpha=.82, label="Valid (≥80%)"),
            mpatches.Patch(color=self.C["yellow"], alpha=.82, label="Needs Review"),
            mpatches.Patch(color=self.C["red"], alpha=.82, label="Missing"),
        ]
        ax.legend(handles=legend_items, loc="lower right", fontsize=9)

    # (D) Confidence distribution histogram
    def _confidence_hist(self, ax):
        if self.df.empty:
            ax.text(.5, .5, "No data", ha="center", transform=ax.transAxes)
            return
        conf = self.df["confidence"].dropna()
        bins = np.arange(0, 1.1, 0.1)
        n, b, patches = ax.hist(conf, bins=bins, edgecolor="white", lw=1.5)
        for patch, left in zip(patches, b[:-1]):
            if left >= 0.8:   patch.set_facecolor(self.C["green"])
            elif left >= 0.5: patch.set_facecolor(self.C["yellow"])
            else:             patch.set_facecolor(self.C["red"])
            patch.set_alpha(0.82)

        mu = conf.mean()
        ax.axvline(mu, color=self.C["dark"], ls="--", lw=2,
                   label=f"Mean: {mu:.2f}")
        ax.set_xlabel("Confidence", fontsize=11)
        ax.set_ylabel("Count", fontsize=11)
        ax.set_title("LLM Confidence Distribution",
                      fontsize=14, fontweight="bold", pad=12)
        ax.legend(fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)

    # (E) Validation check pass rates
    def _check_bars(self, ax):
        if self.df.empty:
            ax.text(.5, .5, "No data", ha="center", transform=ax.transAxes)
            return
        cols = [c for c in self.df.columns if c.startswith("chk_")]
        names = [c.replace("chk_", "").replace("_", " ").title() for c in cols]
        passes = [self.df[c].mean() for c in cols]
        y = np.arange(len(names))

        ax.barh(y, passes, color=self.C["green"], alpha=.82,
                label="Pass", edgecolor="white", lw=1.5)
        ax.barh(y, [1 - p for p in passes], left=passes,
                color=self.C["red"], alpha=.4, label="Fail",
                edgecolor="white", lw=1.5)

        for i, p in enumerate(passes):
            ax.text(p / 2, i, f"{p:.0%}", ha="center", va="center",
                    fontsize=11, fontweight="bold", color="white")

        ax.set_yticks(y)
        ax.set_yticklabels(names, fontsize=10)
        ax.set_xlim(0, 1)
        ax.set_title("Validation Check Pass Rates",
                      fontsize=14, fontweight="bold", pad=12)
        ax.legend(loc="lower right", fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
        ax.invert_yaxis()