#!/usr/bin/env python3
import argparse
import copy
import arviz as az
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import ultranest
from scipy.linalg import cholesky, solve_triangular

from iocbio.fcs.lib.acf import ACF
from iocbio.fcs.lib.base_model import AbstractModel
from iocbio.fcs.lib.const import THREE_DIM_TRIP, ULTRANEST, GLS, WLS, OLS
from iocbio.fcs.lib.fit import collect_data_for_fit, fit_model_dict
from iocbio.fcs.lib.residual import Residual
from iocbio.fcs.lib.result import Results, ResultsList
from iocbio.fcs.lib.map import Map
from iocbio.fcs.lib.plot import Plot
from iocbio.fcs.lib.utils import error_structure, get_output_fname, output_suffix


def save_samples(args, acf_dict, cfo, acf_model, inferencedata, result_file, n_sector, sector_indx):
    sorted_acf_key_list = sorted(list(acf_dict.keys()))
    delta_x_local, angle_line, line_time_line = np.array([]), np.array([]), np.array([])

    # Collect data from each ACF key
    for sorted_acf_key in sorted_acf_key_list:
        acf_value = acf_dict[sorted_acf_key]
        plot_obj = acf_value.data_for_plot()
        dx_local = plot_obj.dx_local[args.exclude_acf :]
        angle, line_time = acf_value.angle, acf_value.line_time
        delta_x_local = np.append(delta_x_local, dx_local)
        for _ in range(len(dx_local)):
            angle_line = np.append(angle_line, angle)
            line_time_line = np.append(line_time_line, line_time)

    # Store data in xarray DataArrays
    constant_data_dict = {
        "time": xr.DataArray(cfo.t_fit, dims=["index"]),
        "x": xr.DataArray(delta_x_local, dims=["index"]),
        "acf": xr.DataArray(cfo.acf_fit, dims=["index"]),
        "acf-std": xr.DataArray(cfo.acf_std, dims=["index"]),
        "angle": xr.DataArray(angle_line, dims=["index"]),
        "line-time": xr.DataArray(line_time_line, dims=["index"]),
        "line-index": xr.DataArray(cfo.line_fit, dims=["index"]),
    }
    posterior_predictive_dict = {
        "acf-model": xr.DataArray(acf_model, dims=[f"index_{i}" for i in range(acf_model.ndim)])
    }
    constant_data = xr.Dataset(data_vars=constant_data_dict)
    posterior_predictive = xr.Dataset(data_vars=posterior_predictive_dict)
    inferencedata.add_groups(dict(constant_data=constant_data, posterior_predictive=posterior_predictive))

    # Determine file name format based on number of sectors
    file_format = ".nc" if n_sector == 1 else f"-{sector_indx}.nc"

    s_name = get_output_fname(result_file, args.output, output_suffix(args, "samples"), file_format)
    inferencedata.to_netcdf(s_name)
    print(f"\nSamples saved: {s_name}")


def fit_bayes(args, input_file):
    # Model
    model_fit = args.model

    # Error structure handling
    err_structure = error_structure(args)

    if model_fit in fit_model_dict:
        model = fit_model_dict[model_fit](args)
    else:
        raise Exception(f"\nModel is unknown. Available models: {', '.join(fit_model_dict.keys())}")

    # Load ACF data
    sector_acf_dict = ACF.load(input_file, args)
    n_sector = len(sector_acf_dict)  # number of sectors

    if n_sector == 0:
        raise Exception("All ACF data are filtered")
    if args.full_acf:
        raise Exception("\nThe program cannot fit Full-ACF data.")

    # Results List Class
    rlc = ResultsList(input_file, args=args, fit_procedure=ULTRANEST)

    # Fit the data collected by the "collect_data_for_fit" method separately for each sector
    for sector_indx, (sector_key, acf_dict) in enumerate(sector_acf_dict.items()):
        verbose = True if sector_indx == 0 else False

        # Collected fit objectives (cfo) > acf_fit, acf_std, acf_cov, x_fit, y_fit, t_fit, line_fit
        # ACF keys indexes dictionary (akid) > keys: speed, angle | value: ACF indexes
        cfo, akid = collect_data_for_fit(acf_dict, verbose)
        n_acf = cfo.acf_fit.size
        z_fit = np.zeros(cfo.y_fit.shape)  # z = [0, 0, 0, ...]

        # Error structure (Covariance)
        if err_structure == GLS:
            # Compute log(det(C)) using Cholesky decomposition for numerical stability.
            # If C = L @ L.T (where L is lower triangular from Cholesky), then:
            # log(det(C)) = 2 * sum(log(diag(L)))
            # This avoids numerical instability from direct determinant calculation.
            # Reference: Murphy, K. P, MIT Press, March 2022, "Probabilistic Machine Learning: An Introduction",
            # Section 7.1.4.2 Determinant of a square matrix
            # https://probml.github.io/pml-book/book1.html
            cov_matrix_chol = cholesky(cfo.acf_cov, lower=True)
            log_det_cov_matrix = 2 * np.sum(np.log(np.diag(cov_matrix_chol)))
        else:
            cov_matrix_chol = None

        def prior_transform(cube):
            if err_structure in (WLS, GLS):
                return model.prior_transform(cube)
            params = cube.copy()

            params[0] = cube[0] * 5  # use uniform prior std ∈ [0, 5]
            params[1:] = model.prior_transform(cube[1:])
            return params

        def log_likelihood(paramsfull):
            if err_structure == OLS:
                std, params = paramsfull[0], paramsfull[1:]
            else:
                std, params = cfo.acf_std, paramsfull
            y_model = model.calc_acf_fit([cfo.x_fit, cfo.y_fit, z_fit, cfo.t_fit], *params)

            # Compute likelihood
            part_a = 0.5 * n_acf * np.log(2 * np.pi)
            if err_structure == GLS:
                part_b = 0.5 * log_det_cov_matrix
                sol_dy = solve_triangular(cov_matrix_chol, y_model - cfo.acf_fit, lower=True)
                part_c = 0.5 * (sol_dy**2).sum()
            else:
                part_b = np.log(std).sum() if err_structure == WLS else n_acf * np.log(std)
                part_c = 0.5 * (((y_model - cfo.acf_fit) / std) ** 2).sum()
            loglike = -part_a - part_b - part_c
            return loglike

        parameters = copy.copy(model.parameters)

        # The fitter takes into account the standard deviation of the ACF data across different traces
        # when either args.error or args.covariance is provided.
        # Otherwise, the standard deviation is treated as a separate parameter by the fitter.
        if err_structure == OLS:
            parameters.insert(0, "std")

        # Run sampler
        sampler = ultranest.ReactiveNestedSampler(parameters, log_likelihood, prior_transform)
        viz_callback = "auto" if args.live_point_visualisations else False
        sampler_run = sampler.run(viz_callback=viz_callback, min_num_live_points=args.live_points)

        # Give summary of marginal likelihood and parameter posteriors
        sampler.print_results()

        # Process results
        samples = sampler_run["samples"]
        paramnames = sampler_run["paramnames"]

        # Plot traces and marginalized posteriors for each parameter
        if args.plot_trace:
            sampler.plot_trace()

        # Corner plot (pairwise correlations between parameters)
        if args.plot_corner:
            sampler.plot_corner()

        # Convert to inference data
        inferencedata = az.convert_to_inference_data(
            {p: samples[:, i] for i, p in enumerate(sampler_run["paramnames"])}
        )

        # Compute the summary for the required statistics (Highest Density Interval (HDI))
        stat_funcs = ["mean", "sd", "hdi_3%", "hdi_97%", "ess_bulk", "ess_tail"]
        arviz_summary_mean = az.summary(inferencedata)
        arviz_summary_mean = arviz_summary_mean.loc[paramnames, stat_funcs]
        print(f"\n{arviz_summary_mean.loc[paramnames, stat_funcs]}\n")

        # Compute the median and Equal-Tailed Interval (ETI)
        ci = 0.682  # confidence interval for 15.9% and 84.1%
        stat_funcs_median = ["median", "eti_15.9%", "eti_84.1%"]
        arviz_summary_median = az.summary(inferencedata, stat_focus="median", hdi_prob=ci, var_names=paramnames)
        arviz_summary_median = arviz_summary_median.loc[paramnames, stat_funcs_median]
        print(arviz_summary_median.loc[paramnames, stat_funcs_median], "\n")

        # Log model and result info
        print(f"model: {args.model}\nlogz: {sampler_run['logz']}\n")

        # Store the processed results in the dictionary
        sector_ultranest_data = {
            "paramnames": paramnames,
            "samples": samples,
            "arviz_mean_f": arviz_summary_mean,
            "arviz_median_f": arviz_summary_median,
        }

        # Process results and standard deviations
        arviz_mean = sector_ultranest_data["arviz_mean_f"]
        param = sector_ultranest_data["paramnames"]

        results = arviz_mean.loc[param, "mean"].tolist()
        std_results = arviz_mean.loc[param, "sd"].tolist()

        # Determine parameter index based on error/covariance settings
        param_index = 1 if err_structure == OLS else 0

        # Calculate model values for each parameter set
        acf_model = []
        xdata = [cfo.x_fit, cfo.y_fit, z_fit, cfo.t_fit]
        for param_results in sector_ultranest_data["samples"]:
            cacf = model.calc_acf_fit(xdata, *param_results[param_index:])
            acf_model.append(cacf)

        acf_model = np.array(acf_model)

        # Residuals
        standardized_residuals_of_samples = []
        if args.residuals:
            residuals = cfo.acf_fit - acf_model
            residual_class = Residual(
                error_structure=err_structure, cfo=cfo, n_params=len(parameters), cov_chol=cov_matrix_chol
            )

            if residuals.ndim != 1:
                for sample in residuals[:,]:
                    residual_class.residuals = sample
                    standardized_residuals_of_samples.append(residual_class.standardize_residuals())
                standardized_residuals_of_samples = np.array(standardized_residuals_of_samples)

                # SSR (sum of squared residuals). In Bayesian inference, both ACF and residuals are 2D arrays
                # with dimensions (number of samples, number of ACFs).
                # For SSR calculation 'median' of samples is considered.
                residuals = np.median(residuals, axis=0)

            # Standardized residuals for SSR
            residual_class.residuals = residuals
            residual_class.standardize_residuals()
            residual_class.ssr_handler()

        # Print and save results
        parameter_result_dict = model.result_process(results[param_index:], std_results[param_index:])

        # Save results
        result_dataclass = Results(
            acf=cfo.acf_fit,
            acf_model=acf_model,
            line_indx=cfo.line_fit,
            akid=akid,
            prd=parameter_result_dict,
            resid=standardized_residuals_of_samples,
            ultranest_data=sector_ultranest_data,
        )
        rlc.add_result(sector_key, result_dataclass)

        if args.save_sample:
            save_samples(args, acf_dict, cfo, acf_model, inferencedata, input_file, n_sector, sector_indx)

    # Save results in HDF file
    if args.save_results:
        rlc.save()

    # Save results in a table (available formats: .xlsx and .csv)
    if args.excel or args.csv:
        rlc.save_table()

    if args.pdf or args.show:
        if n_sector == 1:  # plot results of fit
            Plot(args, sector_acf_dict, rlc=rlc)
        else:  # plot results of the fit on map(s)
            Map.map_data(args, sector_acf_dict, rlc=rlc)

        if args.show:
            plt.show()


def main():
    # Arguments
    parser = argparse.ArgumentParser(
        description="Analysis and fit of ACF-data by Ultranest models",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Input files
    parser.add_argument("filename", nargs="+", help="ACF file name")

    # Save samples
    parser.add_argument("--save-sample", action="store_true", help="Save samples as `nc` file")

    # Plot arguments
    parser.add_argument(
        "-pt", "--plot-trace", action="store_true", help="Plot traces and marginalized posteriors for each parameter"
    )
    parser.add_argument("-pc", "--plot-corner", action="store_true", help="Make a healthy corner plot with corner")

    # Sampling arguments
    parser.add_argument(
        "-lp",
        "--live-points",
        type=int,
        default=400,
        help="Minimum number of live points",
    )
    parser.add_argument(
        "-lv",
        "--live-point-visualisations",
        action="store_true",
        help="Shows where the live points are currently in parameter space; disabled by default",
    )

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
        fit_bayes(args, input_file)
        print()


if __name__ == "__main__":
    main()
