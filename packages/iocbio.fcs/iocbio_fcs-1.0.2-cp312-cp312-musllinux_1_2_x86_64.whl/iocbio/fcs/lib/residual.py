import numpy as np
from scipy.linalg import cholesky, solve_triangular
from ultranest.plot import PredictionBand

from iocbio.fcs.lib.const import GLS, WLS, OLS
from iocbio.fcs.lib.plot_bayes import add_prediction_band


class Residual:
    def __init__(self, error_structure, residuals=None, cfo=None, n_params=None, cov_chol=None):
        self.error_structure = error_structure
        self.residuals = residuals
        self.cfo = cfo
        self.cov_chol = cov_chol
        self.n_params = n_params
        self.standardized_residuals = None

    def standardize_residuals(self):
        if self.error_structure == GLS:
            # Cholesky decomposition of the covariance matrix
            # This finds a lower triangular matrix "cov_matrix_chol" (L) such that: cov_matrix = L @ L.T
            # L is the matrix square root of Σ (covariance matrix), i.e., Σ = L Lᵀ
            cov_matrix_chol = self.cov_chol if self.cov_chol is not None else cholesky(self.cfo.acf_cov, lower=True)
            # Solve the triangular system L @ x = residuals for x
            # This gives: x = L⁻¹ @ residuals
            # These x values are the standardized residuals: x = Σ^(-1/2) · residuals
            # reference: Davidson, R.; MacKinnon, J. G. Econometric Theory and Methods; Oxford University
            # Press: New York, 2004, chapter 7, http://qed.econ.queensu.ca/ETM/ETM-davidson-mackinnon-2021.pdf

            self.standardized_residuals = solve_triangular(cov_matrix_chol, self.residuals, lower=True)
        elif self.error_structure == WLS:
            self.standardized_residuals = self.residuals / self.cfo.acf_std
        else:
            self.standardized_residuals = self.residuals
        return self.standardized_residuals

    def ssr_handler(self, line=False):
        if self.standardized_residuals is None:
            raise RuntimeError("Standardized residuals must be computed before calling ssr_handler.")

        # Chi-Square Statistic
        chi2 = np.sum(self.standardized_residuals**2)
        if line:
            return chi2

        if self.error_structure == GLS or self.error_structure == WLS:
            # Chi-Square Statistic (raw residuals)
            chi2_raw_residuals = np.sum(self.residuals**2)
            print(f"\u2211\u03c7\u00b2 (SSR, raw residuals) = {chi2_raw_residuals:.5f}")
        print(f"\u2211\u03c7\u00b2 (SSR, {self.error_structure} residuals) = {chi2:.5f}")
        chi2_red = chi2 / (len(self.residuals) - self.n_params)
        print(f"Reduced {self.error_structure} SSR          = {chi2_red:.5f}")

    @property
    def res_y_label(self):
        if self.error_structure == GLS:
            return "Σ⁻¹ᐟ² · residuals"
        elif self.error_structure == WLS:
            return "Residuals / SD"
        elif self.error_structure == OLS:
            return "Residuals"


# Plot residuals
def plot_residuals(self, line, x_axis, residuals, k_indx):
    sub = self.subplt_residuals
    sub.axhline(y=0, color="grey", linestyle="--", lw=0.5, alpha=1)
    color = self.fit_color[line % len(self.fit_color)]
    residual_class = Residual(error_structure=self.err_structure)
    if self.ultranest:
        band_resid = PredictionBand(x_axis)
        for resid in residuals:
            band_resid.add(resid)
        residual_class.standardized_residuals = np.median(residuals, axis=0)
        ssr = residual_class.ssr_handler(line=True)
        add_prediction_band(self, band_y_axis=band_resid, line=line, ssr=ssr, k_indx=k_indx)
    else:
        residual_class.standardized_residuals = residuals
        ssr = residual_class.ssr_handler(line=True)
        label = f"L{line + 1} \u2211\u03c7\u00b2 = {ssr:.2f}"
        sub.plot(x_axis, residuals, color, lw=1.2, label=label)

    sub.legend(loc="upper right", draggable=True)

    if self.args.log:
        sub.set_xscale("log")
