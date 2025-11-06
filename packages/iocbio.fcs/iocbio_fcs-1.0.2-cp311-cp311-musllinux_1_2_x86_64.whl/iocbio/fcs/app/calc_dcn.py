#!/usr/bin/env python3
import argparse
import h5py
import numpy as np
from dataclasses import dataclass

from iocbio.fcs.lib.acf import ACF
from iocbio.fcs.lib.base_model import AbstractModel
from iocbio.fcs.lib.const import GROUP_ACF, DCN_DIFFUSION, DCN_CONCENTRATION
from iocbio.fcs.lib.fit import curve_fit_func
from iocbio.fcs.models.analytical.diff3D import Diff3D


@dataclass
class CollectFitData:
    acf_fit: np.ndarray  # Autocorrelation function
    x_fit: np.ndarray  # X-axis
    y_fit: np.ndarray  # Y-axis
    t_fit: np.ndarray  # Time


def calc_dcn(args, input_file):
    # Error handling
    if args.map:
        raise ValueError(
            "The 'map' option (plot parameter maps) is not supported when calculating concentration and diffusion."
        )

    if not args.isotropic:
        raise ValueError("Only the isotropic model is supported when calculating concentration and diffusion.")

    if args.error or args.covariance:
        raise ValueError(
            "Only the OLS fitting method (single dataset) is supported when calculating concentration and diffusion."
        )

    # Select the `3D-diffusion` model for fitting
    model = Diff3D(args)  # this model calculates only the diffusion coefficient and concentration

    sector_acf_dict = ACF.load(input_file, args, individual_acf=True)
    try:
        with h5py.File(input_file, "a") as f:
            for acf_dict in sector_acf_dict.values():
                for acf_name, acf_array in acf_dict.items():
                    # Parameters needed for fitting
                    collected_fit_obj = CollectFitData(
                        acf_fit=acf_array.acf_mean_fit,
                        x_fit=acf_array.delta_x_fit,
                        y_fit=acf_array.delta_y_fit,
                        t_fit=acf_array.delta_t_fit,
                    )

                    # Attempt model fitting
                    optim, _, _, _ = curve_fit_func(model=model, cfo=collected_fit_obj)

                    # Update the ACF data with the calculated diffusion and concentration
                    acf_data = f[f"{GROUP_ACF}/" + acf_name]
                    concentration, diffusion = optim[0], optim[1]
                    acf_data.attrs[DCN_DIFFUSION] = diffusion
                    acf_data.attrs[DCN_CONCENTRATION] = concentration

    except RuntimeError as err:
        if "Optimal parameters not found" in str(err):
            print(
                "Fitting failed: Optimal parameters were not found because the maximum number of "
                "function evaluations was exceeded.\n"
                "Suggestion: Try increasing --reduction-factor (or -rf) > 1, "
                "or exclude initial ACF points using --exclude-acf (or -e)."
            )
        else:
            raise  # Propagate unexpected RuntimeErrors


def main():
    # Arguments
    parser = argparse.ArgumentParser(
        description="Calculate diffusion and concentration for using in dcn-plot (available for RICS)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Input files
    parser.add_argument("filename", nargs="+", help="ACF file name")

    ACF.config_parser(parser)
    AbstractModel.config_parser(parser)
    args = parser.parse_args()
    for input_file in args.filename:
        print("Analyzing:", input_file)
        calc_dcn(args, input_file)
        print()


if __name__ == "__main__":
    main()
