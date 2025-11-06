#!/usr/bin/env python3
import argparse
import h5py
import matplotlib.pyplot as plt

from iocbio.fcs.lib.acf import ACF
from iocbio.fcs.lib.const import GROUP_ACF
from iocbio.fcs.lib.map import Map
from iocbio.fcs.lib.plot import Plot
from iocbio.fcs.lib.plot_signal import plot_signals
from iocbio.fcs.lib.plot_dcn import plot_diffusion_vs_concentration
from iocbio.fcs.lib.result import ResultsList


def plot_acf_data(args, input_file, fit_file=None):
    if fit_file:
        # Results List Class
        rlc = ResultsList.load(input_file, args=args, fit_file=fit_file)
        acf_file_path = rlc.acf_file_path
        n_excl, rf = rlc.n_excl, rlc.rf  # number of excluded acf data and reduction factor

        # Check number of excluded acf data and reduction factor
        if args.exclude_acf != n_excl:
            print(f"\nNumber of excluded acf data used for fitting is {n_excl}\n")
        if args.reduction_factor != rf:
            print(f"\nThe reduction factor used for fitting is {rf}\n")
        args.exclude_acf, args.reduction_factor = n_excl, rf
    else:
        rlc, acf_file_path = None, input_file

    # Load ACF dictionary from acf class (use it for fitting and plotting)
    sector_acf_dict = ACF.load(acf_file_path, args)
    n_sector = len(sector_acf_dict)  # number of sectors

    # Check if images are split (RICS)
    if n_sector == 1:
        sector_key = next(iter(sector_acf_dict))
        Plot(args, sector_acf_dict, rlc=rlc, sector_key=sector_key, file_name=input_file)
    else:
        Map.map_data(args, sector_acf_dict, rlc=rlc, file_name=input_file)

    # Save results in a table (available formats: .xlsx and .csv)
    if fit_file and (args.excel or args.csv):
        rlc.save_table()


# Main plotting function that determines plotting based on input type
def plot_app(args, input_file):
    with h5py.File(input_file, "r") as file:
        fit_file, acf_file = ResultsList.is_loadable(file), GROUP_ACF in file  # boolean

        if args.dcn:
            if acf_file:  # Plot Diffusion Coefficient VS Concentration
                plot_diffusion_vs_concentration(args, input_file, acf_file=file)
            else:
                raise Exception(f"\ninput file does not include {GROUP_ACF} group")
        else:
            if acf_file:  # Plot ACF data or 2D-ACF (RICS) without fit results
                plot_acf_data(args, input_file)
            elif fit_file:  # Plot ACF data with fit results
                plot_acf_data(args, input_file, fit_file=file)
            else:  # Plot signals (average intensity or FCS trace)
                plot_signals(args, input_file)

    if args.show:
        plt.tight_layout()
        plt.show()


def main():
    # Arguments
    parser = argparse.ArgumentParser(
        description="Plot data (RICS images (average), FCS traces (average), single trace, "
        "ACF-data, or Diffusion Coefficient VS Concentration per image (RICS))",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Input files
    parser.add_argument(
        "filename",
        nargs="+",
        help="Name of input file (RICS, FCS, ACF-data)",
    )
    ACF.config_parser(parser)
    Plot.config_parser(parser)
    args = parser.parse_args()
    for input_file in args.filename:
        print("Analyzing:", input_file)
        plot_app(args, input_file)
        print()


# if run as a script
if __name__ == "__main__":
    main()
