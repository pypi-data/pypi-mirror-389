#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np

from iocbio.fcs.lib.const import FIG_SIZE_SAMPLES


# Plot shade and prediction band
def add_prediction_band(self, band_y_axis, line, ssr=None, k_indx=None):
    color = self.fit_color[line % len(self.fit_color)]
    qr = ["68.27 % Quantile Range", "95.45 % Quantile Range"]
    if ssr:
        var = f"L{line + 1} SSR = {ssr:.2f}"
        labels = [var, qr[0], qr[1]] if (line == 0 and k_indx == self.n_key - 1) else [var, None, None]
    else:
        labels = ["Fit (median)", qr[0], qr[1]] if line == 0 else [None, None, None]

    # Plot the median fit line
    band_y_axis.line(color=color, label=labels[0])

    # Plot 68.27% quantile range as shaded area (q = CDF(SD) - 0.5)
    band_y_axis.shade(q=0.3413, color="k", alpha=0.3, label=labels[1])

    # Plot 95.45% quantile range as shaded area (q = CDF(2 x SD) - 0.5)
    band_y_axis.shade(q=0.47725, color="k", alpha=0.2, label=labels[2])


# Plot samples (histogram)
def plot_samples(self):
    paramnames = self.ultranest["paramnames"]
    samples = self.ultranest["samples"]
    arviz_mean_f = self.ultranest["arviz_mean_f"]
    arviz_median_f = self.ultranest["arviz_median_f"]

    _, axes = plt.subplots(len(paramnames), 1, figsize=FIG_SIZE_SAMPLES)
    for i, parameter in enumerate(paramnames):
        ax, data = axes[i], samples[:, i]
        _, bin_edges = np.histogram(data, bins="auto")
        ax.hist(data, bins=bin_edges, alpha=0.3, color="k")
        mean, median = arviz_mean_f.loc[parameter, "mean"], arviz_median_f.loc[parameter, "median"]
        p3, p97 = arviz_mean_f.loc[parameter, ["hdi_3%", "hdi_97%"]]
        median_p_std, median_m_std = arviz_median_f.loc[parameter, ["eti_84.1%", "eti_15.9%"]]
        vertical_lines = [
            (p3, "c", f"hdi_3% = {p3:.3f}"),
            (median_m_std, "b", f"median - std = {median_m_std:.3f}"),
            (mean, "r", f"mean = {mean:.3f}"),
            (median, "teal", f"median = {median:.3f}"),
            (median_p_std, "b", f"median + std = {median_p_std:.3f}"),
            (p97, "c", f"hdi_97% = {p97:.3f}"),
        ]
        for x, color, label in vertical_lines:
            ax.axvline(x, color=color, label=label, lw=2 if color != "r" else 1, ls="--" if color == "teal" else "-")
        ax.set_xlabel(parameter, fontweight="bold")
        ax.set_ylabel("Frequency", fontweight="bold")
        ax.legend()
