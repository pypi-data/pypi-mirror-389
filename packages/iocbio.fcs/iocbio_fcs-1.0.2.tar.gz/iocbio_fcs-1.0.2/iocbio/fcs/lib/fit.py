import numpy as np
from dataclasses import dataclass
from scipy.optimize import curve_fit
from iocbio.fcs.lib.const import (
    THREE_DIM,
    THREE_DIM_TRIP,
    THREE_DIM_2COMP,
    THREE_DIM_2COMP_TRIP,
    THREE_DIM_PSF,
    THREE_DIM_TRIP_PSF,
    THREE_DIM_2COMP_PSF,
    THREE_DIM_2COMP_TRIP_PSF,
    GLS,
    WLS,
    OLS,
)
from iocbio.fcs.lib.residual import Residual
from iocbio.fcs.models.analytical.diff3D import Diff3D
from iocbio.fcs.models.analytical.diff3D_2comp import Diff3D_2comp
from iocbio.fcs.models.analytical.diff3D_2comp_triplet import Diff3D_2comp_triplet
from iocbio.fcs.models.analytical.diff3D_triplet import Diff3D_triplet
from iocbio.fcs.models.psf.diff3D_2comp_psf import Diff3D_2comp_psf
from iocbio.fcs.models.psf.diff3D_2comp_triplet_psf import Diff3D_2comp_triplet_psf
from iocbio.fcs.models.psf.diff3D_psf import Diff3D_psf
from iocbio.fcs.models.psf.diff3D_triplet_psf import Diff3D_triplet_psf

fit_model_dict = {
    THREE_DIM: Diff3D,
    THREE_DIM_TRIP: Diff3D_triplet,
    THREE_DIM_2COMP: Diff3D_2comp,
    THREE_DIM_2COMP_TRIP: Diff3D_2comp_triplet,
    THREE_DIM_PSF: Diff3D_psf,
    THREE_DIM_TRIP_PSF: Diff3D_triplet_psf,
    THREE_DIM_2COMP_PSF: Diff3D_2comp_psf,
    THREE_DIM_2COMP_TRIP_PSF: Diff3D_2comp_triplet_psf,
}


@dataclass
class CollectFitData:
    acf_fit: np.ndarray  # Autocorrelation function
    acf_std: np.ndarray  # Standard deviation
    acf_cov: np.ndarray  # Covariance
    x_fit: np.ndarray  # X-axis
    y_fit: np.ndarray  # Y-axis
    t_fit: np.ndarray  # Time
    line_fit: np.ndarray  # Line indexes


# A method collecting data from different keys (speeds and angles)
# that exist within the sectors of "sector_acf_dict" (created in the ACF class)
def collect_data_for_fit(acf_dict: dict, verbose: bool) -> tuple[CollectFitData, dict]:
    acf_keys_indx_dict, count = dict(), 0
    sorted_acf_key_list = sorted(list(acf_dict.keys()))
    acf_fit, acf_std, x_fit, y_fit, t_fit, line_fit = (
        np.array([]),
        np.array([]),
        np.array([]),
        np.array([]),
        np.array([]),
        np.array([], dtype=int),
    )

    # Collecting parameters needed for fitting
    for sorted_acf_key in sorted_acf_key_list:
        acf_value = acf_dict[sorted_acf_key]
        fit_obj = acf_value.data_for_fit()
        acf_fit = np.append(acf_fit, fit_obj.acf)
        acf_std = np.append(acf_std, fit_obj.std)
        x_fit = np.append(x_fit, fit_obj.dx)
        y_fit = np.append(y_fit, fit_obj.dy)
        t_fit = np.append(t_fit, fit_obj.dt)
        line_fit = np.append(line_fit, fit_obj.line)
        acf_keys_indx_dict[sorted_acf_key] = [count, count + len(fit_obj.acf)]
        count += len(fit_obj.acf)
    if verbose:
        print("\n-------------------------------------------------")
        print(f"Total ACF points to analyze: {acf_fit.size}")
        print("-------------------------------------------------\n")
    collected_fit_obj = CollectFitData(
        acf_fit=acf_fit,
        acf_std=acf_std,
        acf_cov=fit_obj.cov,
        x_fit=x_fit,
        y_fit=y_fit,
        t_fit=t_fit,
        line_fit=line_fit,
    )
    return collected_fit_obj, acf_keys_indx_dict


def curve_fit_func(model, cfo, calc_residual=False, err_structure=OLS):
    z_fit = np.zeros(cfo.y_fit.shape)  # z = [0, 0, 0, ...]
    xdata = [cfo.x_fit, cfo.y_fit, z_fit, cfo.t_fit]
    ydata = cfo.acf_fit

    # Error structure handling
    if err_structure == GLS:
        sigma = cfo.acf_cov
    elif err_structure == WLS:
        sigma = cfo.acf_std
    elif err_structure == OLS:
        sigma = None
    else:
        raise ValueError(f"Unknown error structure: {err_structure}")

    optim, pcov = curve_fit(model.calc_acf_fit, xdata=xdata, ydata=ydata, sigma=sigma, p0=model.p0, bounds=model.bound)
    acf_model = model.calc_acf_fit(xdata, *optim)

    # Residuals
    standardized_residuals = None
    if calc_residual:
        residuals = ydata - acf_model
        residual_class = Residual(error_structure=err_structure, residuals=residuals, cfo=cfo, n_params=len(optim))
        standardized_residuals = residual_class.standardize_residuals()
        residual_class.ssr_handler()

    return optim, pcov, acf_model, standardized_residuals
