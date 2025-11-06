import argparse
import numpy as np
from dataclasses import dataclass
from functools import cached_property

from iocbio.fcs.lib.const import (
    ALPHA,
    AVOGADRO_CONST,
    MEAN,
    MICROSECOND,
    RES_TXT,
    STD,
    UNIT,
    UNIT_CONCENTRATION,
    UNIT_DIFF,
)


@dataclass
class Parameter:
    name: str
    unit: str
    min: float
    max: float
    init: float


# Base model: AbstractModel serves as a base class for modeling and fitting processes
# Derived classes (models) must implement the following methods:
# - `set_parameters(self, *parameters)`: list of parameters of model.
# - `calc_acf(self, delta_x, delta_y, delta_z, delta_t)`:
#       a function for computing the autocorrelation function (ACF)
#       based on the provided parameters.
# The names of parameters and their attributes should be defined in `self.parameters_attrs`.
class AbstractModel:
    # static
    @staticmethod
    def config_parser(parser):
        # PSF (Point Spread Function) parameters
        parser.add_argument("--wx", type=float, default=0.3, help="PSF width along X-axis [W(x)]")
        parser.add_argument("--wy", type=float, default=0.3, help="PSF width along Y-axis [W(y)]")
        parser.add_argument("--wz", type=float, default=1.1, help="PSF width along Z-axis [W(z)]")
        parser.add_argument("-ps", "--psf-scale", action="store_true", help="Calculate `psf_scale`")
        parser.add_argument("-pf", "--psf-file", default="average-psf.h5", help="PSF file name")
        parser.add_argument(
            "-dxy",
            "--downscale-xy",
            type=int,
            default=1,
            help="Downscale factor for the X and Y axes of the PSF. "
            "This reduces the resolution of the PSF in the lateral (XY) plane. "
            "The PSF is first smoothed using a box-shaped convolution filter "
            "then downsampled by the given factor. "
            "This mimics how the PSF would appear in a system with lower lateral resolution. "
            "For example, using --downscale-xy 2 halves the PSF size in X and Y.",
        )
        parser.add_argument(
            "-dz",
            "--downscale-z",
            type=int,
            default=1,
            help="Downscale factor for the Z axis of the PSF. "
            "This reduces the resolution of the PSF along the axial (Z) direction. "
            "For example, using --downscale-z 2 halves the PSF size in Z.",
        )

        # Model (isotropic or anisotropic)
        parser.add_argument(
            "-iso",
            "--isotropic",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Model of diffusion is isotropic in the case of `--isotropic` (default) "
            "Use `--no-isotropic` or `--no-iso`, to apply anisotropic model",
        )

        # Priors for parameters (minimum and maximum boundaries)
        parser.add_argument(
            "-dc",
            "--diffusion-coefficient-range",
            nargs=2,
            type=float,
            default=[1e-4, 5000],
            metavar=("MIN", "MAX"),
            help="Minimum and maximum boundaries for diffusion coefficient [µm²/s]."
            "Example: -dc 0 100  (values must be separated by a space)",
        )

        parser.add_argument(
            "-c",
            "--concentration-range",
            nargs=2,
            type=float,
            default=[0, 1000],
            metavar=("MIN", "MAX"),
            help="Minimum and maximum boundaries for concentration [nM]." "Example: -c 0 100",
        )
        parser.add_argument(
            "-trip",
            "--triplet-amplitude-range",
            nargs=2,
            type=float,
            default=[0, 1],
            metavar=("MIN", "MAX"),
            help="Minimum and maximum boundaries for triplet state amplitude [0<T<1]" "Example: -trip 0 0.6",
        )
        parser.add_argument(
            "-tau",
            "--triplet-tau-range",
            nargs=2,
            type=float,
            default=[1e-2, 1e4],
            metavar=("MIN", "MAX"),
            help="Minimum and maximum boundaries for triplet state relaxation time (tau) [µs]" "Example: -tau 0 5",
        )
        parser.add_argument(
            "-psf",
            "--psfscale-range",
            nargs=2,
            type=float,
            default=[0, 2],
            metavar=("MIN", "MAX"),
            help="Minimum and maximum boundaries for PSF scale [0<alpha<2]" "Example: -psf 0.5 1.5",
        )

        # Initial guess for parameters (a value between minimum and maximum boundaries)
        parser.add_argument(
            "-initdc",
            "--initial-diffusion-coefficient",
            type=float,
            default=1,
            help="Initial guess for diffusion coefficient [µm²/s] " "(a value between minimum and maximum boundaries)",
        )
        parser.add_argument(
            "-initc",
            "--initial-concentration",
            type=float,
            default=1,
            help="Initial guess for concentration [nM] " "(a value between minimum and maximum boundaries)",
        )
        parser.add_argument(
            "-inittrip",
            "--initial-triplet-amplitude",
            type=float,
            default=0.01,
            help="Initial guess for triplet state amplitude [0<T<1] "
            "(a value between minimum and maximum boundaries)",
        )
        parser.add_argument(
            "-inittau",
            "--initial-triplet-tau",
            type=float,
            default=1,
            help="Initial guess for triplet state relaxation time (tau) [µs] "
            "(a value between minimum and maximum boundaries)",
        )
        parser.add_argument(
            "-initpsf",
            "--initial-psf-scale",
            type=float,
            default=1,
            help="Initial guess for PSF scale [0<alpha<2] " "(a value between minimum and maximum boundaries)",
        )

    def __init__(self, args):
        self.args = args
        self.convert_c = AVOGADRO_CONST / 1e24
        self.wx, self.wy, self.wz = args.wx, args.wy, args.wz
        diff_unit = UNIT_DIFF  # diffusion unit
        conc_unit = UNIT_CONCENTRATION  # concentration unit
        trip_amp_unit = "0<T<1"  # triplet amplitude unit
        trip_tau_unit = MICROSECOND  # triplet tau unit
        psf_scale_unit = f"0<{ALPHA}<2"

        # Define range and initial value of parameters
        conc, init_conc = args.concentration_range, args.initial_concentration
        dc, init_dc = args.diffusion_coefficient_range, args.initial_diffusion_coefficient
        ta, init_ta = args.triplet_amplitude_range, args.initial_triplet_amplitude
        tt, init_tt = args.triplet_tau_range, args.initial_triplet_tau
        psf, initpsf = args.psfscale_range, args.initial_psf_scale

        # Define parameters and their attributes include: names, units, [min, max], initial value using @dataclass
        self.parameters_attrs = {
            # Parameter name in model: Parameter(name to present, unit, [min, max], init)
            "concentration_nanomolar": Parameter("Concentration", conc_unit, *conc, init_conc),
            "diffusion": Parameter("Diffusion coefficient", diff_unit, *dc, init_dc),
            "diffusion_x": Parameter("Diffusion along x", diff_unit, *dc, init_dc),
            "diffusion_y": Parameter("Diffusion along y", diff_unit, *dc, init_dc),
            "diffusion1": Parameter("Diffusion coefficient 1", diff_unit, *dc, init_dc),
            "diffusion2 - diffusion1": Parameter(
                "Diffusion coefficient 2 - Diffusion coefficient 1", diff_unit, *dc, init_dc
            ),
            "concentration1_nanomolar": Parameter("Concentration 1", conc_unit, *conc, init_conc),
            "diffusion1_x": Parameter("Diffusion 1 along x", diff_unit, *dc, init_dc),
            "diffusion1_y": Parameter("Diffusion 1 along y", diff_unit, *dc, init_dc),
            "concentration2_nanomolar": Parameter("Concentration 2", conc_unit, *conc, init_conc),
            "diffusion2_x - diffusion1_x": Parameter(
                "Diffusion 2 along x - Diffusion 1 along x", diff_unit, *dc, init_dc
            ),
            "diffusion2_y - diffusion1_y": Parameter(
                "Diffusion 2 along y - Diffusion 1 along y", diff_unit, *dc, init_dc
            ),
            "triplet_amplitude": Parameter("Triplet amplitude", trip_amp_unit, *ta, init_ta),
            "triplet_tau": Parameter("Triplet relaxation time", trip_tau_unit, *tt, init_tt),
            "psf_scale": Parameter("PSF scale", psf_scale_unit, *psf, initpsf),
        }

    # Initial value for fitting
    @cached_property
    def p0(self):
        p0_list = []
        for param in self.parameters:
            min, max = self.parameters_attrs[param].min, self.parameters_attrs[param].max
            init, name = self.parameters_attrs[param].init, self.parameters_attrs[param].name
            if not min <= init <= max:
                raise ValueError(
                    f"\nInitial guess of {name} (= {init}) is not between {min} and {max} \n"
                    "Change `initial guess` or `minimum and maximum boundaries`"
                )
            p0_list.append(init)
        return p0_list

    # Create bounds by min and max values for fitting
    @cached_property
    def bound(self):
        b = [
            [self.parameters_attrs[param].min for param in self.parameters],
            [self.parameters_attrs[param].max for param in self.parameters],
        ]
        return np.array(b)

    # Methods below have to be implemented in derived models
    def set_parameters(self, *parameters):
        raise NotImplementedError(
            f"\n{self.__class__.__name__} must implement the 'set_parameters' method in derived models."
        )

    def calc_acf(self, delta_x, delta_y, delta_z, delta_t):
        raise NotImplementedError(
            f"\n{self.__class__.__name__} must implement the 'calc_acf' method in derived models."
        )

    # Transformation of priors for Ultranest models
    def prior_transform(self, cube):
        return (self.bound[1, :] - self.bound[0, :]) * cube + self.bound[0, :]

    def result_process(self, results, std_results, verbose=True):
        parameter_result_dict = {}  # dictionary for saving results per parameter
        for i in range(len(results)):
            p = self.get_parameter_description(i)
            if p.name == "Concentration":  # show number of particles (available in single component models)
                n_particle = results[i] * self.convert_c
                focal_vol = (np.pi**1.5) * self.wx * self.wy * self.wz
                print(f"\nNumber of particles [in μm³]:          {n_particle:.3f}")
                print(f"Number of particles [in focal volume]: {n_particle * focal_vol:.3f}")

            # Generate a text for the results of parameters
            mean_std = [f"{results[i]:.3f}", f"{std_results[i]:.3f}"]
            result_text = f"\n{p.name} [{p.unit}]: {mean_std[0]} ± {mean_std[1]}"
            if verbose:
                print(f"{result_text}")
            parameter_result_dict[p.name] = {}
            parameter_result_dict[p.name][MEAN] = results[i]
            parameter_result_dict[p.name][STD] = std_results[i]
            parameter_result_dict[p.name][UNIT] = p.unit
            parameter_result_dict[p.name][RES_TXT] = result_text
        print()
        return parameter_result_dict

    def get_parameter_description(self, index):
        param = self.parameters[index]
        p = self.parameters_attrs[param]
        return p

    # Calculate ACF data for fitting
    def calc_acf_fit(self, delta, *parameters):
        self.set_parameters(*parameters)
        delta_x = delta[0]
        delta_y = delta[1]
        delta_z = delta[2]
        delta_t = delta[3]
        return self.calc_acf(delta_x, delta_y, delta_z, delta_t)
