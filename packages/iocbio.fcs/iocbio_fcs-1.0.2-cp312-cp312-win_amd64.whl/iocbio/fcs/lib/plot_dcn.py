#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np

from iocbio.fcs.lib.acf import ACF
from iocbio.fcs.lib.const import (
    GROUP_ACF,
    FIG_SIZE_DCN,
    UNIT_CONCENTRATION,
    UNIT_DIFF,
    DCN_DIFFUSION,
    DCN_CONCENTRATION,
)
from iocbio.fcs.lib.plot_signal import plot_signals
from iocbio.fcs.lib.utils import get_output_fname, split_indx


def print_stats(data, label):
    print(f"\n{label}:\nmin:    {min(data):.2f}\nmax:    {max(data):.2f}")
    print(f"mean:   {np.mean(data):.2f}\nmedian: {np.median(data):.2f}\nstd:    {np.std(data):.2f}")


def plot_dots(x, y, xlabel, ylabel, subplot, color="blue"):
    """Plot scatter plot of the given x and y data."""
    subplot.plot(x, y, ".", color=color, markersize=3)
    subplot.set_xlabel(xlabel, fontweight="bold")
    subplot.set_ylabel(ylabel, fontweight="bold")


def plot_diffusion_vs_concentration(args, input_file, acf_file):
    fig = plt.figure(figsize=FIG_SIZE_DCN)
    sector_acf_dict = ACF.load(input_file, args, individual_acf=True)
    for acf_dict in sector_acf_dict.values():
        concentration, diffusion = [], []
        for key in acf_dict:
            data = acf_file[f"/{GROUP_ACF}/" + key]
            concentration.append(data.attrs[DCN_CONCENTRATION])
            diffusion.append(data.attrs[DCN_DIFFUSION])

        selected_range = args.filter_range
        n_data_dcn = len(diffusion)
        if not selected_range:
            print(f"Number of images/traces: {n_data_dcn}")
        print_stats(concentration, "concentration")
        print_stats(diffusion, "diffusion")
        print("\n==========================================")
        print("Concentration mean - (2 x std): %.2f" % (np.mean(concentration) - 2 * np.std(concentration)))
        print("==========================================\n")
        rows = 4 if args.measurement_file else 3

        # Plot diffusion vs concentration
        ax1 = fig.add_subplot(rows, 1, 1)
        xlabel, ylabel = f"Concentration {UNIT_CONCENTRATION}", f"Diffusion [{UNIT_DIFF}]"
        plot_dots(concentration, diffusion, xlabel, ylabel, ax1)

        # Plot diffusion vs images
        ax2 = fig.add_subplot(rows, 1, 2)
        selected_indexes = [0]
        if selected_range:
            selected_indexes = split_indx(selected_range)

        start = selected_indexes[0]
        end = n_data_dcn + start
        x_axis = range(start, end)
        xlabel, ylabel = "Image number", f"Diffusion [{UNIT_DIFF}]"
        plot_dots(x_axis, diffusion, xlabel, ylabel, ax2, color="red")

        # Plot concentration vs images
        ax3 = fig.add_subplot(rows, 1, 3, sharex=ax2)
        xlabel, ylabel = "Image number", f"Concentration {UNIT_CONCENTRATION}"
        plot_dots(x_axis, concentration, xlabel, ylabel, ax3, color="maroon")

        if args.measurement_file:
            filter_range = acf_dict[key].fr
            mean_values = plot_signals(args, args.measurement_file, dcn_fr=filter_range)
            print(f"Selected range used in calc-acf is {filter_range} -> {filter_range[1]-filter_range[0]}")

            # Plot intensity vs images
            ax4 = fig.add_subplot(rows, 1, 4, sharex=ax2)
            ax4.plot(x_axis, mean_values, c="k")
            ax4.set_xlabel("Image number", fontweight="bold")
            ax4.set_ylabel("Intensity", fontweight="bold")

        fig_name = "_Diffusion vs Concentration"
        if args.pdf:
            plt.savefig(get_output_fname(input_file, args.output, fig_name, ".pdf"))
