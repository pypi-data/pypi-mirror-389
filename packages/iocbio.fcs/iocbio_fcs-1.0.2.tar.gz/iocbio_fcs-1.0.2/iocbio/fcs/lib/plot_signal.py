#!/usr/bin/env python3
import sys
import matplotlib.pyplot as plt
import numpy as np
import pyqtgraph as pg
from pyqtgraph.exporters import SVGExporter

from iocbio.fcs.lib.const import DEC_FCSPROTOCOL, DEC_RICSPROTOCOL, FIG_SIZE_SIGNAL
from iocbio.fcs.lib.input import analyze_input_file
from iocbio.fcs.lib.utils import get_output_fname, filtering, split_indx


def plot_signals(args, input_file, dcn_fr=None):
    data = analyze_input_file(input_file)
    pixel_time = data.pixel_time
    images_group = data.images_group
    data_filename = data.filenames

    if dcn_fr:
        data_filename = data_filename[dcn_fr[0] : dcn_fr[1]]

    selected_range = args.filter_range
    selected_indexes = [0]
    if selected_range:
        data_filename = filtering(data_filename, selected_range)
        selected_indexes = split_indx(selected_range)
    n_data = len(data_filename)  # number of dataset after filtering

    if n_data == 1 and not dcn_fr:
        if data.decoded_protocol == DEC_FCSPROTOCOL:
            # Plot FCS trace
            plot_trace(input_file, args, data, trace_index=selected_indexes[0])
            sys.exit(-1)
        if data.decoded_protocol == DEC_RICSPROTOCOL:
            raise ValueError("Only one image is available.")
    else:
        # Plot average intensity of each image/trace in RICS/FCS experiment
        mean_list = [np.mean(np.array(images_group[data_filename[i]])) for i in range(n_data)]
        mean_list = mean_list / pixel_time
        if dcn_fr:
            return mean_list
        plot_avg_signals(input_file, args, mean_list)


def plot_trace(input_file, args, data, trace_index):
    images_group = data.images_group
    dset = images_group[data.filenames[trace_index]]
    origin_signals = np.array(dset[0, :])
    time_step = data.pixel_time
    max_n = len(origin_signals)
    max_time = max_n * time_step
    origin_regular_time = np.linspace(0, max_time, int(max_time / time_step))

    # calc some stats: https://research.stowers.org/imagejplugins/fcs_pch_tutorial.html
    rate = origin_signals / time_step
    mean = np.mean(rate)
    delta = rate - mean
    shift, gamma = 10, 0.27
    cov = np.sqrt(np.mean(delta[shift:] * delta[:-shift]))
    g0 = (cov * cov) / mean / mean
    brightness = g0 * mean / gamma
    print(f"Rate mean value: {mean:0.0f};  COV: {cov:0.0f}; units: counts/s")
    print(f"G0: {g0:0.3f}")
    print(f"Molecular brightness: {brightness:0.0f} counts/s")

    nsamples = 2500
    dt = max_time / nsamples
    di = max(1, int(dt / time_step))
    n = int(max_n / di)
    time = origin_regular_time[: n * di].reshape((-1, di)).mean(axis=1)
    signal = origin_signals[: n * di].reshape((-1, di)).mean(axis=1) / time_step
    pg.setConfigOptions(antialias=True)

    pw = pg.plot(time, signal, autoDownsample=False)
    pw.setWindowTitle(input_file)
    pi = pw.getPlotItem()
    dataItem = pi.listDataItems()[0]
    pi.getAxis("left").setLabel("Signal rate", units="counts/s")
    pi.getAxis("bottom").setLabel("Time", units="s")

    def process_range_change(_, rng):
        # Adapt downsampling to axis change
        t0, t1 = rng
        trange = t1 - t0
        t0 -= trange / 10
        t1 += trange / 10
        n0 = int(max(t0, 0) / time_step)
        n1 = min(int(t1 / time_step), max_n)
        dn = n1 - n0

        if dn < nsamples * 2:  # show original signal
            t = origin_regular_time[n0:n1]
            s = origin_signals[n0:n1] / dt
        else:  # downsample
            ngr = dn // nsamples
            n = dn // ngr
            t = origin_regular_time[n0 : n0 + n * ngr].reshape((-1, ngr)).mean(axis=1)
            s = origin_signals[n0 : n0 + n * ngr].reshape((-1, ngr)).mean(axis=1) / time_step

        dataItem.setData(t, s)

    pi.sigXRangeChanged.connect(process_range_change)
    pg.exec()

    # Save plot if required (SVG)
    if args.pdf and not args.svg:
        raise Exception("\nTo save FCS trace use --svg")
    if args.svg:
        svg_path = get_output_fname(input_file, args.output, f"_trace_{trace_index}", ".svg")
        exporter = SVGExporter(pi)
        exporter.export(svg_path)
        print(f"Saved SVG to: {svg_path}")


def plot_avg_signals(input_file, args, mean_list):
    n_data = len(mean_list)
    print("Number of images/traces:", n_data)
    mean_value = np.mean(mean_list)
    min_value, max_value = min(mean_list), max(mean_list)

    # Plot average signals
    fig = plt.figure(figsize=FIG_SIZE_SIGNAL)
    sub1 = fig.add_subplot(111)

    marker = "o" if n_data < 20 else ""
    sub1.plot(np.arange(n_data), mean_list, c="k", marker=marker)
    sub1.axhline(mean_value, color="c", lw=0.9, ls="dashed", label="Average Intensity")

    plt.legend()
    plt.xlabel("Image number", fontweight="bold")
    plt.ylabel("Intensity", fontweight="bold")

    # Average, Min, Max
    print(f"Average of signals = {mean_value}")
    print(f"Minimum of signals = {min_value}")
    print(f"Maximum of signals = {max_value}")

    # Save plot if required
    if args.pdf:
        plt.savefig(get_output_fname(input_file, args.output, "-signals", ".pdf"))
