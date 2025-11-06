#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
from iocbio.fcs.lib.const import FIG_SIZE_COV
from iocbio.fcs.lib.utils import get_output_fname, output_suffix


# Utility to compute bin edges from center points
def compute_bin_edges(values):
    edges = np.zeros(len(values) + 1)
    edges[1:-1] = (values[1:] + values[:-1]) / 2
    edges[0] = values[0] - (edges[1] - values[0])
    edges[-1] = values[-1] + (values[-1] - edges[-2])
    return edges


# Plot 2D-covariance matrix using pcolormesh
def plot_2d_cov(f_name, args, acf_cov, lag_time):
    fig, ax = plt.subplots(figsize=FIG_SIZE_COV)

    if args.normalized_covariance:
        # To normalize the covariance matrix so that the diagonal values become 1,
        # each element is divided by the square root of the outer product
        # of the corresponding diagonal elements. (Pearson correlation coefficient)
        diag = np.sqrt(np.diag(acf_cov))
        normalization_matrix = np.outer(diag, diag)

        # Avoid division by zero
        with np.errstate(invalid="ignore", divide="ignore"):
            normalized_cov = acf_cov / normalization_matrix
            normalized_cov[np.isnan(normalized_cov)] = 0

        covariance_matrix = normalized_cov
    else:
        covariance_matrix = acf_cov

    # Compute bin edges
    x_edges = compute_bin_edges(lag_time)
    y_edges = compute_bin_edges(lag_time)

    # Plot with pcolormesh
    mesh = ax.pcolormesh(x_edges, y_edges, covariance_matrix, shading="auto", cmap="viridis")

    # Set axes
    if args.log:
        ax.set_xscale("log")
        ax.set_yscale("log")
    ax.set_aspect("equal")
    ax.invert_yaxis()  # https://pubs.acs.org/doi/10.1021/ac2034375

    # Labels
    ax.set_xlabel("Lag time (s)", fontsize=14, fontweight="bold")
    ax.set_ylabel("Lag time (s)", fontsize=14, fontweight="bold")

    # Colorbar
    cbar = plt.colorbar(mesh, ax=ax, shrink=0.75)
    cbar.set_label("Covariance", labelpad=20, fontsize=14, fontweight="bold")

    # Tight layout
    fig.tight_layout()

    # Save as PDF
    if args.pdf:
        osuf = output_suffix(args, "covariance")
        file_format = ".pdf" if args.output is None else "-2.pdf"
        fig.savefig(get_output_fname(f_name, args.output, osuf, file_format))
