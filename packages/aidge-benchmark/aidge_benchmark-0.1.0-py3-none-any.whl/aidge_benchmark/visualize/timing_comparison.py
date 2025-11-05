"""
Copyright (c) 2023 CEA-List

This program and the accompanying materials are made available under the
terms of the Eclipse Public License 2.0 which is available at
http://www.eclipse.org/legal/epl-2.0.

SPDX-License-Identifier: EPL-2.0
"""

import numpy as np
import matplotlib.pyplot as plt

import copy


def compute_pairwise_ratios(
    values: np.ndarray, reference_values: np.ndarray
) -> np.ndarray:
    """Compute all pairwise ratios a_i / b_j."""
    ratios = np.ravel(np.divide.outer(values, reference_values))

    return ratios


def compute_median_of_pairwise_ratios(
    values: np.ndarray, reference_values: np.ndarray
) -> float:
    ratios = compute_pairwise_ratios(values, reference_values)
    return np.median(ratios)


def fill_ax_with_ratio(
    ax, data: dict[str, dict[str, float]], x: str, *, palette: str = "Set3"
):
    """
    Plot grouped bar chart from dictionary of values.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axis to plot into.
    data : dict
        {x_value: {library: ratio, ...}, ...}
    x : str
        Label for the x-axis (e.g., param name).
    palette : str, optional
        Matplotlib colormap name (default: 'tab10').
    """

    # Extract categories
    x_vals = list(data.keys())
    libraries = list(next(iter(data.values())).keys())
    x_pos = np.arange(len(x_vals))
    width = 0.8 / len(libraries)

    # Build a colormap
    cmap = plt.get_cmap(palette)
    colors = [cmap(i) for i in range(len(libraries))]

    # Plot grouped bars
    for i, (lib, color) in enumerate(zip(libraries, colors)):
        ratios = [data[val][lib] for val in x_vals]
        bars = ax.bar(
            x_pos + i * width,
            ratios,
            width,
            label=lib,
            color=color,
            edgecolor="black",
            linewidth=1,
        )
        ax.legend(libraries)
        # Add bar labels
        ax.bar_label(bars, labels=[f"{r:.2f}" for r in ratios], padding=3, rotation=55)

    # Styling
    ax.axhline(1.0, color="k", ls="--", alpha=0.8)
    ax.set_yticks([1.0])
    ax.set_yticklabels(["1.0"])
    ax.set_xticks(x_pos + width * (len(libraries) - 1) / 2)
    ax.set_xticklabels(x_vals)
    ax.set_xlabel(x)
    ax.set_ylabel("Ratio")
    ax.grid(True, axis="y", alpha=0.5)
    ax.set_ylim(0, max(ax.get_ylim()[1] * 1.05, 1.05))

    return ax


def ratio_plot(timings, reference_library_name: str, palette: str = "Set3"):
    """
    Create ratio plots comparing backends to a reference backend.

    Parameters
    ----------
    timings : dict
        Benchmark results as {label -> {backend -> list of timings}}.
    reference_library_name : str
        The backend used as the reference for speed ratio comparisons.
    palette : str
        Matplotlib color palette name.

    Returns
    -------
    fig, axes
        The matplotlib figure and axes with the ratio plots.
    """

    # Reorganize timings into grouped structure by "label_start.label_end" for ploting legend
    grouped_timings: dict = {}

    for label, dict_lib_times in timings.items():
        split = label.split(".")
        label_start, label_end = ".".join(split[:-1]), split[-1]

        grouped_timings.setdefault(label_start, {})
        grouped_timings[label_start].setdefault(label_end, {})

        for lib, times in dict_lib_times.items():
            grouped_timings[label_start][label_end][lib] = np.array(times)

    # ------------------------------------------------------------------
    # Setup subplots
    # ------------------------------------------------------------------
    n_params = len(grouped_timings)
    n_cols = 1 if n_params == 1 else (2 if n_params <= 4 else 3)
    n_rows = (n_params + n_cols - 1) // n_cols

    fig, axes = plt.subplots(
        n_rows, n_cols, figsize=(10 if n_params == 1 else 15, 5 * n_rows)
    )
    # Ensure axes is always iterable
    axes = np.atleast_1d(axes).flatten()


    # ------------------------------------------------------------------
    # Compute ratios per label
    # ------------------------------------------------------------------
    for idx, (label_start, data) in enumerate(grouped_timings.items()):
        ratios: dict = {}
        for label_end, dict_lib_times in data.items():
            ratios[label_end] = {}
            for lib, times in dict_lib_times.items():
                if lib == reference_library_name:
                    continue
                ratios[label_end][lib] = compute_median_of_pairwise_ratios(
                    dict_lib_times[lib],
                    dict_lib_times[reference_library_name],
                )

        axes[idx] = fill_ax_with_ratio(axes[idx], ratios, label_start, palette=palette)

    # ------------------------------------------------------------------
    # Clean up extra subplots & layout
    # ------------------------------------------------------------------
    for idx in range(n_params, len(axes)):
        fig.delaxes(axes[idx])

    plt.tight_layout(rect=[0, 0.02, 0.98, 0.93])

    # ------------------------------------------------------------------
    # Global legend
    # ------------------------------------------------------------------
    common_handles, common_labels = None, None
    for ax in fig.axes:
        leg = ax.get_legend()
        if leg is not None:
            common_handles, common_labels = ax.get_legend_handles_labels()
            break
    if common_handles and common_labels:
        fig.legend(
            common_handles,
            common_labels,
            loc="upper center",
            ncol=len(common_labels),
            bbox_to_anchor=(0.5, 0.99),
            title="Library",
        )
    for ax in axes:
        if ax.get_legend() is not None:
            ax.get_legend().remove()

    return fig, axes