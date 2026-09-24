"""Create compact, reproducible figures for the portfolio README."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
FIGURES = ROOT / "docs" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


def _style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "#f7f9fc",
            "axes.edgecolor": "#cbd5e1",
            "axes.labelcolor": "#243447",
            "axes.titleweight": "bold",
            "font.size": 10,
            "text.color": "#243447",
            "xtick.color": "#475569",
            "ytick.color": "#475569",
        }
    )


def _save(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIGURES / name, dpi=180, bbox_inches="tight")
    plt.close(fig)


def make_availability_figure() -> None:
    frame = pd.read_csv(OUTPUTS / "sf_vs_league.csv")
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.plot(frame["season"], frame["out_per_observed_game"], marker="o", linewidth=2.5, color="#b91c1c", label="San Francisco")
    ax.plot(frame["season"], frame["other_31_mean"], marker="o", linewidth=2.5, color="#2563eb", label="Other 31 teams")
    ax.set_xlabel("Season")
    ax.set_ylabel("Players designated Out per observed game")
    ax.set_title("Public injury-report designations: San Francisco versus league")
    ax.set_xticks(frame["season"])
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, loc="upper left")
    fig.text(0.01, 0.01, "Out is a reporting designation, not an incident-injury or exposure measure.", fontsize=8, color="#64748b")
    _save(fig, "availability_benchmark.png")


def make_model_figure() -> None:
    metrics = pd.read_csv(OUTPUTS / "test_metrics.csv")
    labels = metrics["model"].str.replace("_", " ").str.title()
    colors = ["#0f766e" if bool(selected) else "#64748b" for selected in metrics["selected_by_validation"]]
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    bars = ax.bar(labels, metrics["mae"], color=colors)
    ax.set_ylabel("2025 test MAE")
    ax.set_title("Temporal model comparison")
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="x", rotation=15)
    for bar, value in zip(bars, metrics["mae"]):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.03, f"{value:.2f}", ha="center", weight="bold")
    fig.text(0.01, 0.01, "Lower is better; the selected model was chosen on earlier validation seasons.", fontsize=8, color="#64748b")
    _save(fig, "model_performance.png")


def make_decision_figure() -> None:
    grid = pd.read_csv(OUTPUTS / "decision_sensitivity.csv")
    surface = grid.pivot(index="hazard_probability", columns="attributable_fraction", values="Relocate")
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    image = ax.imshow(
        surface.values,
        origin="lower",
        aspect="auto",
        extent=[surface.columns.min(), surface.columns.max(), surface.index.min(), surface.index.max()],
        cmap="RdYlGn",
    )
    ax.set_xlabel("Attributable fraction of measured burden")
    ax.set_ylabel("Hypothetical hazard probability")
    ax.set_title("Relocation action value under explicit assumptions ($ millions)")
    colorbar = fig.colorbar(image, ax=ax)
    colorbar.set_label("Relocation NPV ($ millions)")
    fig.text(0.01, 0.01, "Negative values favor staying under the illustrative cost and benefit assumptions.", fontsize=8, color="#64748b")
    _save(fig, "decision_surface.png")


def main() -> None:
    _style()
    make_availability_figure()
    make_model_figure()
    make_decision_figure()


if __name__ == "__main__":
    main()
