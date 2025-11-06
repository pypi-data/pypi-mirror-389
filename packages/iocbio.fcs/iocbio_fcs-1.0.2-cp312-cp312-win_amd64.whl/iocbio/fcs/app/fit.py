#!/usr/bin/env python3
import argparse
import matplotlib.pyplot as plt
import numpy as np

from iocbio.fcs.lib.acf import ACF
from iocbio.fcs.lib.base_model import AbstractModel
from iocbio.fcs.lib.const import LEAST_SQUARES, THREE_DIM_TRIP
from iocbio.fcs.lib.fit import collect_data_for_fit, curve_fit_func, fit_model_dict
from iocbio.fcs.lib.result import Results, ResultsList
from iocbio.fcs.lib.map import Map
from iocbio.fcs.lib.plot import Plot
from iocbio.fcs.lib.utils import error_structure


def process_sector(model, cfo, akid, err_structure, calc_residual):
    # collected fit objectives (cfo) and ACF keys indexes dictionary (akid)
    optim, pcov, acf_model, standardized_residuals = curve_fit_func(
        model=model, cfo=cfo, calc_residual=calc_residual, err_structure=err_structure
    )
    model.set_parameters(*optim)
    std_results = np.sqrt(np.diag(pcov))
    prd = model.result_process(optim, std_results)  # parameter result dictionary
    result_dataclass = Results(
        acf=cfo.acf_fit, acf_model=acf_model, line_indx=cfo.line_fit, akid=akid, prd=prd, resid=standardized_residuals
    )
    return result_dataclass


def fit(args, input_file):
    # Load ACF dictionary from acf class (use it for fitting and plotting)
    sector_acf_dict = ACF.load(input_file, args)
    n_sector = len(sector_acf_dict)  # number of sectors
    if n_sector == 0:
        raise Exception("All ACF data are filtered")
    if args.full_acf:
        raise Exception("\nThe program cannot fit Full-ACF data.")

    # Error structure handling
    err_structure = error_structure(args)

    # Results List Class
    rlc = ResultsList(input_file, args=args, fit_procedure=LEAST_SQUARES)

    # Model
    model_fit = args.model
    if model_fit in fit_model_dict:
        model = fit_model_dict[model_fit](args)
    else:
        raise Exception(f"\nModel is unknown. Available models: {', '.join(fit_model_dict.keys())}")

    for sector_indx, (sector_key, acf_dict) in enumerate(sector_acf_dict.items()):
        # Collected fit objectives (cfo) > acf_fit, acf_std, acf_cov, x_fit, y_fit, t_fit, line_fit
        # ACF keys indexes dictionary (akid) > keys: speed, angle | value: ACF indexes
        cfo, akid = collect_data_for_fit(acf_dict, verbose=True if sector_indx == 0 else False)
        if n_sector > 1:
            print(f"\n-------------- sector {sector_key} --------------")
        result_dataclass = process_sector(
            model=model, cfo=cfo, akid=akid, err_structure=err_structure, calc_residual=args.residuals
        )
        rlc.add_result(sector_key, result_dataclass)

    # Save results in HDF file
    if args.save_results:
        rlc.save()

    # Save results in a table (available formats: .xlsx and .csv)
    if args.excel or args.csv:
        rlc.save_table()

    if args.show or args.pdf:
        if n_sector == 1:  # plot results of fit
            Plot(args, sector_acf_dict, rlc=rlc)
        else:  # plot results of the fit on map(s)
            Map.map_data(args, sector_acf_dict, rlc=rlc)
        if args.show:
            plt.show()


def main():
    # Arguments
    parser = argparse.ArgumentParser(
        description="Analysis and fit of ACF-data by `curve_fit`",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Input files
    parser.add_argument("filename", nargs="+", help="ACF file name")

    # Select Model (3D, 3D triple, 2 components, and ...)
    parser.add_argument(
        "--model",
        default=THREE_DIM_TRIP,
        help="Model for fitting. Available models: %s" % (", ".join(fit_model_dict.keys())),
    )

    ACF.config_parser(parser)
    AbstractModel.config_parser(parser)
    Plot.config_parser(parser)
    args = parser.parse_args()
    for input_file in args.filename:
        print("Analyzing:", input_file)
        fit(args, input_file)
        print()


if __name__ == "__main__":
    main()
