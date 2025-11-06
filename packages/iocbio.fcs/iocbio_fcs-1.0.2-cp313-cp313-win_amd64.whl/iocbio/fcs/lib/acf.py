#!/usr/bin/env python3
import argparse
import h5py
import numpy as np
from dataclasses import dataclass

from iocbio.fcs.lib.const import (
    ATTR_ACF_KEY,
    ATTR_ANGLE,
    ATTR_ISX,
    ATTR_ISY,
    ATTR_LINETIME,
    ATTR_PIXTIME,
    ATTR_PROTOCOL,
    ATTR_PSX,
    ATTR_PSY,
    DATA_FILENAME,
    DATA_ENCODE,
    DATA_SECTOR_COORD,
    DATA_SELECTED_RANGE,
    DCN_CONCENTRATION,
    DCN_DIFFUSION,
    DEC_FCSPROTOCOL,
    DEC_RICSPROTOCOL,
    GROUP_ACF,
    NSX,
    NSY,
    SSX,
    SSY,
    GLS,
    WLS,
)
from iocbio.fcs.lib.filter_acquisition_attributes import filter_attr
from iocbio.fcs.lib.utils import error_structure, filtering, rotation_func


@dataclass
class FitData:
    acf: np.ndarray  # Autocorrelation function
    std: np.ndarray  # Standard deviation
    cov: np.ndarray  # Covariance
    dx: np.ndarray  # X-axis
    dy: np.ndarray  # Y-axis
    dt: np.ndarray  # Time
    line: np.ndarray  # Lines indexes


@dataclass
class PlotData:
    acf: np.ndarray  # Autocorrelation function
    std: np.ndarray  # Standard deviation
    dx_local: np.ndarray  # Local X-axis
    dt: np.ndarray  # Time
    line: np.ndarray  # Lines indexes


class ACF:
    # static
    @staticmethod
    def config_parser(parser):
        # Filtering based on parameters
        parser.add_argument(
            "-fc",
            "--filter-concentration",
            nargs=2,
            type=float,
            default=None,
            metavar=("MIN", "MAX"),
            help="Define MIN and MAX values for concentration and filter out traces or images with concentrations"
            "outside the specified range (MIN ≤ C ≤ MAX)",
        )

        parser.add_argument(
            "-fdc",
            "--filter-diffusion-coefficient",
            nargs=2,
            type=float,
            default=None,
            metavar=("MIN", "MAX"),
            help="Define MIN and MAX values for diffusion coefficient and filter out traces or images with "
            "diffusion coefficients outside the specified range (MIN ≤ DC ≤ MAX)",
        )

        # Filtering based on ACF
        parser.add_argument(
            "-e",
            "--exclude-acf",
            type=int,
            default=0,
            help="Exclude first X ACF point(s)",
        )
        parser.add_argument(
            "-acfx",
            "--last-acf-x",
            type=int,
            default=None,
            help="Number of pixels taken into account on ACF line",
        )
        parser.add_argument(
            "-acfy",
            "--last-acf-y",
            type=int,
            default=3,
            help="Number of ACF lines taken into account for fitting",
        )
        parser.add_argument(
            "-fr",
            "--filter-range",
            type=str,
            default=None,
            help="Comma-separated list of start and end indexes for ranges (integer)."
            "Load images/traces between from start-index to end-index, and filter out rest"
            "For example: '-fr 10,20,500,1200' or for single FCS trace: '-fr 2'",
        )
        parser.add_argument(
            "-full",
            "--full-acf",
            action="store_true",
            help="By default, plots the X-axis from the middle to the end. "
            "Use --full-acf to plot both sides of the X-axis.",
        )
        parser.add_argument(
            "-srl",
            "--subtract-reference-line",
            type=int,
            default=0,
            help="Determine the reference ACF line and subtract it from other lines " "(default = 0: no subtraction)",
        )

        # Filtering based on line times, angles, and ...
        parser.add_argument(
            "-fk",
            "--filter-key",
            action="store_true",
            help="Exclude keys (line times and angles) that will be selected in the next step",
        )
        parser.add_argument(
            "-sk",
            "--select-key",
            action="store_true",
            help="Include only the keys (line times and angles) selected in the next step; exclude all others",
        )
        parser.add_argument(
            "--filtered-key",
            nargs="+",
            type=str,
            default=[None],
            help="List of keys to exclude (selected by curses)",
        )

        # Down sampling ACF points
        parser.add_argument(
            "-fs",
            "--first-step",
            type=float,
            default=0.5,
            help="First step, when ACF points reduction",
        )
        parser.add_argument(
            "-rf",
            "--reduction-factor",
            type=float,
            default=1.1,
            help="Reduction factor to reduce ACF points (in the cases larger than 1)",
        )

        # Covariance
        parser.add_argument(
            "-cov",
            "--covariance",
            action="store_true",
            help="Consider covariance of ACF data errors to fit data and plot 2D covariance matrix",
        )
        parser.add_argument(
            "-sh",
            "--shrinkage",
            action="store_true",
            help="Shrinkage covariance matrix by Target-B "
            "(article: https://doi.org/10.1021/ac2034375 "
            "Supporting Information PDF file: "
            "https://pubs.acs.org/doi/suppl/10.1021/ac2034375/suppl_file/ac2034375_si_001.pdf)",
        )
        parser.add_argument(
            "-norm",
            "--normalized-covariance",
            action="store_true",
            help="Normalize the covariance matrix for plotting.",
        )

        # Error
        parser.add_argument(
            "-err",
            "--error",
            action="store_true",
            help="Consider the standard deviation of ACF data to fit the data."
            "In Ultranest models, the fitter considers the standard deviation as a "
            "prior in the absence of this option.",
        )

        # Plot and print arguments
        parser.add_argument(
            "--map",
            action="store_true",
            help="Divide ACF into sectors, fit sectors separately, and plot a map of parameters",
        )
        parser.add_argument(
            "--print",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="The fit/plot apps display the number of ACF points "
            "and residuals (if --residuals is specified). "
            "Use `--no-print` to suppress ACF and residuals output",
        )

    # static
    @staticmethod
    def load(acf_file, args, individual_acf=False):
        # if individual_acf=True: Calculate diffusion and concentration for each ACF

        file = h5py.File(acf_file, "r")
        protocol = file.get(f"/{GROUP_ACF}").attrs.get(ATTR_PROTOCOL, DEC_FCSPROTOCOL)

        # Include or exclude acquisition attributes (speed, angle, ...) if specified
        if args.filter_key or args.select_key:
            filter_attr(args, file, protocol)

        # Filenames available in ACF file
        f_name = [name.decode(DATA_ENCODE) for name in file[f"/{GROUP_ACF}/{DATA_FILENAME}"][0]]
        n_data = len(f_name)

        # Error structure handling
        err_structure = error_structure(args)

        # Protocols
        if protocol == DEC_FCSPROTOCOL:
            # Set default `last_acf_x` based on protocol
            if args.last_acf_x is None:
                args.last_acf_x = 50000

            data_str = "traces"
            n_sector = nsx = nsy = ssx = ssy = 1

            if err_structure == GLS:
                if args.full_acf:
                    raise Exception("\nCovariance calculation is only supported for half ACF data.")
        elif protocol == DEC_RICSPROTOCOL:
            # Set default `last_acf_x` based on protocol
            if args.last_acf_x is None:
                args.last_acf_x = 201

            data_str = "images"
            nsx = file.get(f"/{GROUP_ACF}").attrs.get(NSX, 1)
            nsy = file.get(f"/{GROUP_ACF}").attrs.get(NSY, 1)
            ssx = file.get(f"/{GROUP_ACF}").attrs.get(SSX, 1)
            ssy = file.get(f"/{GROUP_ACF}").attrs.get(SSY, 1)
            n_sector = nsx * nsy  # number of sectors
            if err_structure == GLS:
                raise Exception("\nCovariance is not available for RICS experiments")
        else:
            raise Exception("\nProtocol is not FCS or RICS")

        # Splitting (handle sector data)
        sector_acf_dict = dict()
        if args.map:
            if protocol == DEC_FCSPROTOCOL:
                raise Exception("\nMAP is not available for FCS experiments")
            if n_sector == 1:
                raise Exception("\nImages in ACF file have not split --> Import split data ...")
            sector_coordinate_list = file[f"/{GROUP_ACF}/{DATA_SECTOR_COORD}"]

        # Filtering (filter traces or images by range if specified)
        selected_range = args.filter_range
        if selected_range:
            f_name = filtering(f_name, selected_range)
            if args.map:
                sector_coordinate_list = filtering(sector_coordinate_list, selected_range)
            print(f"Number of all {data_str}:     ", n_data)
            n_data = len(f_name)  # number of dataset after filtering
            print(f"Number of selected {data_str}:", n_data)
        else:
            print(f"Number of {data_str}:     ", n_data)

        if n_data == 1 and (err_structure in (WLS, GLS)):
            raise Exception("\nCovariance and error cannot be computed for a single image or trace.")

        # Get filter range used in calc acf (selected range)
        fr_used_in_calc_acf_str = f"/{GROUP_ACF}/{DATA_SELECTED_RANGE}"
        fr_used_in_calc_acf = list(file[fr_used_in_calc_acf_str]) if fr_used_in_calc_acf_str in file else [0, n_data]

        # Process each file name
        for index, name in enumerate(f_name):
            acfs = file[f"/{GROUP_ACF}/" + name]

            # Read attributes
            acf_key = acfs.attrs[ATTR_ACF_KEY]
            angle = acfs.attrs[ATTR_ANGLE]
            image_pixel_x = acfs.attrs[ATTR_ISX]
            image_pixel_y = acfs.attrs[ATTR_ISY]
            line_time = acfs.attrs[ATTR_LINETIME]
            pixel_time = acfs.attrs[ATTR_PIXTIME]
            pixel_x = acfs.attrs[ATTR_PSX]
            pixel_y = acfs.attrs[ATTR_PSY]

            if index == 0:
                image_size_x = pixel_x * image_pixel_x
                image_size_y = pixel_y * image_pixel_y

            # Filter out concentrations lower than the threshold (-fc)
            if args.filter_concentration is not None:
                concentration_3D = acfs.attrs[DCN_CONCENTRATION]
                if concentration_3D < args.filter_concentration[0] or concentration_3D > args.filter_concentration[1]:
                    continue  # skip loading

            # Filter out diffusions higher than the threshold (-fd)
            if args.filter_diffusion_coefficient is not None:
                diffusion_3D = acfs.attrs[DCN_DIFFUSION]
                if (
                    diffusion_3D < args.filter_diffusion_coefficient[0]
                    or diffusion_3D > args.filter_diffusion_coefficient[1]
                ):
                    continue  # skip loading

            acf_key = name if individual_acf else acf_key

            # Filter out keys
            if acf_key in args.filtered_key:
                continue  # skip loading

            sector_coordinate = [0, 0] if not args.map else sector_coordinate_list[index]

            # Initialize sector dictionary (key: coordinate of sector, value: ACF dictionary)
            sector_coordinate_str = str(sector_coordinate)

            if sector_coordinate_str not in sector_acf_dict:
                sector_acf_dict[sector_coordinate_str] = dict()

            current_sector = sector_acf_dict[sector_coordinate_str]

            # Initialize ACF dictionary (key: condition of experiment, value: ACF data) and append data
            if acf_key not in current_sector:
                current_sector[acf_key] = ACF(
                    filter_range=fr_used_in_calc_acf,
                    angle=angle,
                    pixel_x=pixel_x,
                    pixel_y=pixel_y,
                    pixel_time=pixel_time,
                    line_time=line_time,
                    image_size_x=image_size_x,
                    image_size_y=image_size_y,
                    sector_coordinate=sector_coordinate,
                    split=[nsx, nsy],
                    sector_size=[ssx, ssy],
                    args=args,
                    err_structure=err_structure,
                    individual_acf=individual_acf,
                )

            current_sector[acf_key]._append(np.array(acfs))

        # Finalize parameters for fitting and plotting, including:
        # acf, standard deviation, covariance, delta x, delta y, delta t, and lines
        for acf_dict in sector_acf_dict.values():
            for acf_key, acf_value in acf_dict.items():
                acf_value._finalize()
        return sector_acf_dict

    # Constructor
    def __init__(
        self,
        angle,
        pixel_x,
        pixel_y,
        pixel_time,
        line_time,
        image_size_x,
        image_size_y,
        sector_coordinate,
        filter_range,
        split,
        sector_size,
        args,
        err_structure,
        individual_acf,
    ):
        self.angle = angle
        self.pixel_x = pixel_x
        self.pixel_y = pixel_y
        self.pixel_time = pixel_time
        self.line_time = line_time
        self.image_size_x = image_size_x
        self.image_size_y = image_size_y
        self.sector_coordinate = sector_coordinate
        self.sector_coordinate_phys = [
            sector_coordinate[0] * image_size_x,
            sector_coordinate[1] * image_size_y,
        ]
        self.fr = filter_range
        self.split = split
        self.sector_size = sector_size
        self.last_x = args.last_acf_x
        self.last_y = args.last_acf_y
        self.first_step = args.first_step
        self.reduction_factor = args.reduction_factor
        self.print = args.print
        self.shrinkage = args.shrinkage
        self.err_structure = err_structure
        self.exclude = args.exclude_acf
        self.full = args.full_acf
        self.srl = args.subtract_reference_line
        self.individual_acf = individual_acf
        self._reduction_indexes = None
        self._corner_index_fit = None
        self.acf_cov_fit = None
        self.acf_std_fit = None
        self._acf = []
        self._line = []

    """----------------------- Public Methods --------------------"""

    def data_for_fit(self):
        fit_obj = FitData(
            acf=self.acf_mean_fit,
            std=self.acf_std_fit,
            cov=self.acf_cov_fit,
            dx=self.delta_x_fit,
            dy=self.delta_y_fit,
            dt=self.delta_t_fit,
            line=self.lines_fit,
        )
        return fit_obj

    def data_for_plot(self):
        plot_obj = PlotData(
            acf=self.acf_mean_plot,
            std=self.acf_std_plot,
            dx_local=self.delta_x_local_plot,
            dt=self.delta_t_plot,
            line=self.lines_plot,
        )
        return plot_obj

    """------------- Private Methods (in alphabetical order) ----------"""

    def _append(self, acf):
        self.origin_acf_shape = acf.shape

        # Reducing: Reduce the number of ACF data points using the _apply_reduction function
        # (if -rf > 1 and -fs > 0.0),
        # and consequently remove the reduced ACF data from the delta x-y-t and lines.
        if self.reduction_factor < 1 or self.first_step <= 0.0:
            raise ValueError("\nreduction factor must be greater than 1, and first step must be greater than 0.")
        elif self.reduction_factor > 1 and self.first_step > 0.0:
            # acf is appended in reduced form within the method below.
            # in addition, the other attributes (including _line) are set in reduced form as well.
            self._apply_reduction(acf)
        else:
            if len(self._line) == 0:
                # Create line indexes (needed for plotting)
                self._line = self._lines_index()
            self._acf.append(acf)

    def _apply_reduction(self, acf):
        if self._reduction_indexes is None:
            self._reduction_indexes = self._reduction_func()

            # Save the number of dataset in one line after reduction
            n_reduction_indexes = len(self._reduction_indexes)  # number of dataset in one line after reduction
            self.reduced_size = n_reduction_indexes - 1 if self.full else n_reduction_indexes // 2

            self._delta_func(self.origin_acf_shape)
            self._delta_x_local = self._delta_x_local[:, self._reduction_indexes]
            self._delta_y_local = self._delta_y_local[:, self._reduction_indexes]
            self._delta_t = self._delta_t[:, self._reduction_indexes]
            if len(self._line) == 0:
                self._line = self._lines_index()[:, self._reduction_indexes]

        reduced_acf = acf[:, self._reduction_indexes]
        self._acf.append(reduced_acf)

    def _corner(self, vector, fit=False):
        # Create a 2D boolean matrix for selecting the analysis region in RICS processing.
        # If `--full-acf` is enabled:
        # True is set for the entire bottom-half of the 2D array, possibly cutting edges in X:
        #  _______________
        #  |      |      |   ← Top-half rows ➜ False (excluded)
        #  |      |      |
        #  |------|------|
        #  |-------------|   ← Bottom-half rows ➜ True (included), all columns (or cut by start_x / end_x)
        #  |-------------|
        #
        #  ▶ Exception: line 0 (first row of True), at column `self.max_acf_index` ➜ remains False.
        #
        # If `--full-acf` is disabled (by dafault it is disabled):
        # True is set only for the bottom-right quadrant of the 2D array, possibly cutting edges in X:
        #  _______________
        #  |      |      |   ← Top-half rows ➜ False (excluded)
        #  |      |      |
        #  |      |------|   ← Bottom-half rows:
        #  |      -------|     - Left columns ➜ False (excluded)
        #  |      -------|     - Right columns ➜ True (included), starting from start_x to end_x
        #
        #  ▶ Exception: line 0 (first row of True), at column `self.max_acf_index` ➜ remains False.
        #
        # After setting the matrix, it is flattened to a 1D array to be used in further analysis.

        rows, cols = vector.shape

        # Find maximum ACF index
        max_acf_index = np.argmax(vector[self.middle_y])
        middle_acf_index = cols // 2

        if middle_acf_index != max_acf_index:
            raise ValueError(
                f"\nExpected the maximum ACF at the center index {middle_acf_index}, "
                f"but found it at index {max_acf_index}."
            )

        # Define start and end of x-axis
        start_x = -self.last_x - self.middle_x - 1 if self.full else self.middle_x
        end_x = self.last_x + self.middle_x

        # Define start and end of y-axis
        start_y = self.middle_y
        end_y = self.middle_y + self.last_y
        bottom_rows = slice(start_y, end_y)

        # Columns to set True (cutting the edges if needed)
        bottom_cols = slice(start_x, end_x)

        # Start with everything False
        corner_index = np.full((rows, cols), False, dtype=bool)

        # Set the region to True
        corner_index[bottom_rows, bottom_cols] = True

        # Exception: force line 0, max_acf_index to False
        corner_index[self.middle_y, max_acf_index] = False

        # Exclude a symmetric range of ACF points around the peak in the first line
        if self.exclude != 0 and fit is True:
            start, end = max_acf_index - self.exclude, max_acf_index + self.exclude + 1
            corner_index[self.middle_y, start:end] = False

        return corner_index

    def _covariance_func(self):
        # Consider half of ACFs in any trace for calculating covariance
        half_acf = (self.all_acf_shape[2] // 2) + 1
        #                                      [traces, first line, half ACFs]
        corner_reduced_acf = self._all_acf_data[:, 0, half_acf + self.exclude : half_acf + self.last_x - 1]
        cov_matrix = np.cov(corner_reduced_acf, rowvar=False)

        if self.shrinkage:
            mean_diag = np.mean(np.diag(cov_matrix))
            a = np.var(cov_matrix)
            b = np.sum([el**2 for idx, el in np.ndenumerate(cov_matrix) if idx[0] != idx[1]])
            c = np.sum([(el - mean_diag) ** 2 for el in np.diag(cov_matrix)])
            weight = a / (b + c)
            print(f"\nShrinkage weight: {weight:.2e}")

            # Create a uniform diagonal matrix with the mean value
            target_B = np.diag([mean_diag] * (cov_matrix.shape[0]))
            cov_matrix_star = (weight * target_B) + (1 - weight) * cov_matrix
        else:
            cov_matrix_star = cov_matrix
        return cov_matrix_star

    def _delta_func(self, acf_shape):
        x, y = acf_shape[1], acf_shape[0]
        matrix_xi, matrix_psi = np.meshgrid(np.arange(x) - x // 2, np.arange(y) - y // 2)
        self._delta_x_local = matrix_xi * self.pixel_x
        self._delta_y_local = matrix_psi * self.pixel_y
        self._delta_t = matrix_xi * self.pixel_time + matrix_psi * self.line_time

    def _finalize(self):
        self._all_acf_data = np.array(self._acf)
        self.all_acf_shape = self._all_acf_data.shape

        # Do not print ACF information when calc-dcn (individual_acf) is True
        if self.print and not self.individual_acf:
            self._print(line_points=True)

        # Define middle of ACF line
        self.middle_y, self.middle_x = (
            self.all_acf_shape[1] // 2,
            self.all_acf_shape[2] // 2,
        )

        if self.reduction_factor > 1:
            self._validate_reduction()
        else:
            self._delta_func(self.all_acf_shape[1:])

        # Final parameters (cut parameters using a 2D boolean matrix generated in _corner method)
        self.acf_mean_before_cut = np.mean(self._all_acf_data, axis=0)  # needed for plot 2D-ACF

        # Subtract reference ACF line (srl)
        if self.srl != 0:
            if self.srl == 1:
                raise Exception("\nCannot subtract the first line. Please choose the second or a higher line.")
            if self.srl > self.middle_y + 1:
                raise Exception(
                    f"\nLine {self.srl} does not exist for subtraction.\n"
                    f"There are only {self.middle_y + 1} lines available.\n"
                    f"If you need to subtract line {self.srl}, use '-ly {self.srl}'"
                    " or a higher number when calculating the ACF."
                )

            reference_line = self.srl + self.middle_y - 1
            self.acf_mean_before_cut = self.acf_mean_before_cut - self.acf_mean_before_cut[reference_line, :]
        if self._corner_index_fit is None:
            self._corner_index_fit = self._corner(self.acf_mean_before_cut, fit=True).flatten()
            self._corner_index_plot = self._corner(self.acf_mean_before_cut).flatten()

        # Data for fit (flat)
        self.acf_mean_fit = self.acf_mean_before_cut.flatten()[self._corner_index_fit]
        delta_x_local_flat = self._delta_x_local.flatten()[self._corner_index_fit]
        delta_y_local_flat = self._delta_y_local.flatten()[self._corner_index_fit]
        self.delta_t_fit = self._delta_t.flatten()[self._corner_index_fit]
        self.lines_fit = self._line.flatten()[self._corner_index_fit]

        # Rotation local delta-x and delta-y based on the angle
        self.delta_x_fit, self.delta_y_fit = rotation_func(self.angle, delta_x_local_flat, delta_y_local_flat)

        # Data for plot
        self.acf_mean_plot = self.acf_mean_before_cut.flatten()[self._corner_index_plot]
        self.delta_x_local_plot = self._delta_x_local.flatten()[self._corner_index_plot]
        self.delta_t_plot = self._delta_t.flatten()[self._corner_index_plot]
        self.lines_plot = self._line.flatten()[self._corner_index_plot]

        # Standard deviation and covariance of traces (Available for FCS)
        if self.err_structure in (WLS, GLS):
            acf_std_flatten = np.std(self._all_acf_data, axis=0).flatten()
        else:
            acf_std_flatten = np.zeros((self.all_acf_shape[1], self.all_acf_shape[2])).flatten()
        self.acf_std_fit = acf_std_flatten[self._corner_index_fit]
        self.acf_std_plot = acf_std_flatten[self._corner_index_plot]
        if self.err_structure == GLS:
            self.acf_cov_fit = self._covariance_func()
            if self.print:
                self._print()

    def _lines_index(self):
        lines = np.zeros(self.origin_acf_shape, dtype=int)
        line = 1
        for row in lines:
            row += line
            line += 1
        return lines

    def _print(self, line_points=None):
        if line_points:
            line_points = self.origin_acf_shape[1]
            n_data = self.all_acf_shape[0] // (self.split[0] * self.split[1])
            all_points = line_points if self.full else int(np.ceil(line_points / 2))
            last_x = 2 * self.last_x if self.full else self.last_x - 1
            cutted_line_points = min(all_points - 1, last_x)
            if self.line_time == 0:
                info = attrs = "Number of ACF points in the trace:"
            else:
                lt = round(self.line_time * 1000, 1)
                n_acf = "Number of ACF points in first line:"
                attrs = f"Images with angle {self.angle} [degree] and line time {lt} [ms] ({n_data} images)"
                info = attrs + "\n" + n_acf

            print("-" * len(attrs))
            print(info)
            print(f"before reduction and cutting:  {all_points}")
            print(f"after cutting:                 {cutted_line_points}")
            if self.reduction_factor > 1:
                n_data_for_fit = min(self.reduced_size, last_x)
                ratio = n_data_for_fit / cutted_line_points
                print(f"after reduction ({100 - (ratio * 100):.2f}%):      {n_data_for_fit}")
            else:
                n_data_for_fit = last_x
            if self.exclude != 0:
                print(f"after excluding {self.exclude} points:      {n_data_for_fit - self.exclude}")

        if self.acf_cov_fit is not None:
            print("---------------------------------------------------------------------")
            diag = np.diag(self.acf_cov_fit)
            print(f"Prod of diagonal elements:             {np.prod(diag):.3e}")
            print(f"Prod of variance:                      {np.prod(self.acf_cov_fit):.3e}")
            print(f"Determinant of covariance matrix:      {np.linalg.det(self.acf_cov_fit):.3e}")
            print(f"Condition number of covariance matrix: {np.linalg.cond(self.acf_cov_fit):.1f}")

            # Check correlation strength
            correlation_matrix = self.acf_cov_fit / np.sqrt(np.outer(diag, diag))
            max_correlation = np.max(np.abs(correlation_matrix - np.eye(len(correlation_matrix))))
            print(f"Maximum off-diagonal correlation: {max_correlation:.3f}\n")

    # Produce indexes for reduction
    def _reduction_func(self):
        line_points = self.origin_acf_shape[1]
        first_step, next_step = self.first_step, self.first_step
        half_points = line_points // 2
        end_range = half_points if line_points % 2 == 0 else half_points + 1

        p_half_indx = []
        for index in range(1, end_range):
            if index >= first_step:
                p_half_indx.append(index)
                next_step *= self.reduction_factor  # increase next step based on reduction factor
                first_step = index + next_step  # update first_step to reflect the next threshold
            if len(p_half_indx) >= min(half_points, self.last_x):
                break

        # Reduction indexes of negative side
        n_half_indx = (np.array(p_half_indx[::-1])) * -1
        reduction_indexes = np.concatenate((n_half_indx, [0], p_half_indx)) + half_points
        return reduction_indexes

    def _validate_reduction(self):
        n_data = self.all_acf_shape[0]  # number of traces
        n_acf = self.all_acf_shape[2]  # number of ACF points
        if self.reduced_size > n_data and self.err_structure == GLS and not self.shrinkage:
            raise ValueError(
                "\nThe number of traces must be greater than the number of ACF points.\n"
                f"Current number of traces: {n_data}  |  Current number of ACF points: {n_acf}\n"
                "Consider one of the following options:\n"
                "   - Use more traces\n"
                f"   - Increase the reduction factor (current: {self.reduction_factor}) "
                "to reduce the number of ACF points\n"
                "   - Enable shrinkage estimator for the covariance using the --shrinkage"
            )
