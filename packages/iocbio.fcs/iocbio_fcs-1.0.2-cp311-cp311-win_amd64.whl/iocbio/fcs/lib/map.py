#!/usr/bin/env python3
import sys
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass
from functools import cached_property
from mpl_toolkits.axes_grid1 import make_axes_locatable
from typing import Dict, Tuple, Any, List, Optional

from iocbio.fcs.lib.const import (
    ASPECT_RATIO,
    MEAN,
    NSX,
    NSY,
    FIG_SIZE_PRE_MAP,
    SSX,
    SSY,
    UNIT,
    MICROMETER,
    ARROW_LEFT,
    ARROW_RIGHT,
    ARROW_UP,
    ARROW_DOWN,
)
from iocbio.fcs.lib.plot import Plot
from iocbio.fcs.lib.utils import get_output_fname, output_suffix, select_option, rotation_func


@dataclass
class Fit:
    map_values: np.ndarray
    parameter: str
    unit: str


@dataclass
class Sector:
    nsx: int  # Number of sectors along x-axis
    nsy: int  # Number of sectors along y-axis
    ssx: float  # Sector size along x-axis
    ssy: float  # Sector size along y-axis
    rssx: float = None  # Reference sector size along x-axis, relative to sector
    rssy: float = None  # Reference sector size along y-axis, relative to sector


class Map:
    """
    A class to handle the creation and visualization of parameter maps
    for Raster Image Correlation Spectroscopy (RICS) data analysis.
    """

    def __init__(
        self,
        sector: Sector,
        rlc: Any = None,  # Results List Class
        angle: Optional[List[float]] = None,  # List of angles
        acf_group: Any = None,  # h5py group
        img_size_x: float = None,  # Image size in x dimension (μm)
        img_size_y: float = None,  # Image size in y dimension (μm)
        sector_acf_dict: Dict = None,  # Dictionary containing ACF data for each sector
        sector_coordinates: np.ndarray = None,  # Array of sector centers (saved in HDF5 file)
    ):
        self.nsx, self.nsy = sector.nsx, sector.nsy
        self.ssx, self.ssy = sector.ssx, sector.ssy
        self.rssx, self.rssy = sector.rssx, sector.rssy
        self.rlc = rlc
        self.angle = angle if angle is not None else [0]
        self.acf_group = acf_group
        self.sector_acf_dict = sector_acf_dict
        self.sector_coordinates = sector_coordinates
        self.img_size_x = img_size_x
        self.img_size_y = img_size_y
        # model -> True: plot map of parameters; False: plot a map for selection sector
        self.model = True if rlc else False
        self.shorter_y_axis = False

        if self.img_size_y != self.img_size_x:
            shorter_axis = min(self.img_size_y, self.img_size_x)
            longer_axis = max(self.img_size_y, self.img_size_x)

            # Check for extreme aspect ratio
            if shorter_axis < longer_axis / ASPECT_RATIO:
                if self.img_size_y == shorter_axis:
                    self.shorter_y_axis = True
                    if self.img_size_y == 0.0:
                        self.img_size_y = self.img_size_x / 10
                        print(
                            "\n***********************************************\n"
                            "Warning: The image size along the Y-axis is zero.\n"
                            f"For demonstration map, the width is set to {self.img_size_y:.2f}.\n"
                            "***********************************************"
                        )
                else:
                    if self.img_size_x == 0.0:
                        self.img_size_x = self.img_size_y / 10

        # Calculate and store local center coordinates
        self.local_center_x, self.local_center_y = self._calculate_local_centers()

        if self.sector_acf_dict:
            # Create a 2D grid for pcolormesh
            self.mesh_ax_x, self.mesh_ax_y = self._mesh()

            # Show sector grid in terminal (if the number of sectors along x-y-axes < 15)
            if self.nsx < 15 and self.nsy < 15:
                self._show_sector_grid()
        else:
            # Calculate the central coordinates for each sector
            self.sector_centers_local = self._calculate_local_sector_centers()

            # Calculate the coordinates of local centers after rotation
            self.sector_centers = self._calculate_sector_centers()

            # Save splitting attributes to HDF5 file
            self._save_attributes(acf_group)

    @cached_property
    def n_sector(self):
        return self.nsx * self.nsy

    """----------------- Private Methods --------------"""

    def _calculate_local_centers(self) -> Tuple[np.ndarray, np.ndarray]:
        # Calculate the local center coordinates for each sector
        coords_x = np.linspace(-0.5 + self.ssx / 2, 0.5 - self.ssx / 2, self.nsx)
        coords_y = np.linspace(-0.5 + self.ssy / 2, 0.5 - self.ssy / 2, self.nsy)
        return coords_x, coords_y

    def _calculate_local_sector_centers(self) -> np.ndarray:
        """
         Calculate the central coordinates for each sector in an N*K grid,
         (start from top-left corner [x, y], column by column).
         The center of the image is assumed to be [0, 0], and each axis has a unit length (1, 1).
         For example, in a 2x2 grid of sectors, the central coordinates are:

            -0.5 <─ x ─> 0.5
         0.5┌─────────────┐                  ┌─────┐ ┌─────┐
          | │             │             0.25 │  .  │ │  .  │
          │ │             │     -sp          └─────┘ └─────┘
          y │      .      │     ==>
          │ │    [0,0]    │     2x2          ┌─────┐ ┌─────┐
          | │             │            -0.25 │  .  │ │  .  │
        -0.5└─────────────┘                  └─────┘ └─────┘
                                             -0.25    0.25

         The sector overlap allows sectors to extend beyond their standard boundaries,
         capturing features that might span multiple sectors. This prevents information
         loss at sector edges and provides ACF continuity across neighboring sectors."
        """

        # Calculate the spacing between sector centers
        # This ensures sectors are evenly distributed across the image
        spacing_x = (1 - self.ssx) / (self.nsx - 1) if self.nsx > 1 else 0
        spacing_y = (1 - self.ssy) / (self.nsy - 1) if self.nsy > 1 else 0

        start_x = -0.5 + self.ssx / 2
        start_y = 0.5 - self.ssy / 2

        # Generate centers in column-by-column order
        sector_centers = []
        for i in range(self.nsx):
            x = start_x + i * spacing_x
            for j in range(self.nsy):
                y = start_y - j * spacing_y
                sector_centers.append([x, y])

        return np.array(sector_centers)

    def _calculate_sector_centers(self) -> Dict:
        available_angles = set(self.angle)
        # Save angles and coordinates of centers after rotation in a dictionary:
        # {angle-local_coordinate: coordinate after rotation}
        sector_center = dict()
        for center_coordinate in self.sector_centers_local:
            for angle in available_angles:
                # Use negative angle to reverse the rotation and recover coordinates
                # in the reference frame at angle 0
                x, y = rotation_func(-angle, center_coordinate[0], center_coordinate[1])
                x_y_array = np.array([x, y])

                # Find closest element (calculate Euclidean distances
                # from physical coordinates to local coordinates of center)
                distances = np.linalg.norm(self.sector_centers_local - x_y_array, axis=1)

                # Find the index of the minimum distance and find the closest element
                closest_index = np.argmin(distances)
                closest_element = self.sector_centers_local[closest_index]

                sector_center[f"{angle}-{center_coordinate}"] = closest_element
        return sector_center

    def _click_event(self, event: Any, fit_obj: Any = None):
        args = self.args
        if fit_obj:
            # Determine the clicked sector by finding the closest grid point
            x_index = np.argmin(np.abs((self.local_center_x * self.img_size_x) - event.xdata))
            y_index = np.argmin(np.abs((self.local_center_y * self.img_size_y) - event.ydata))

            # Retrieve the result value from the map
            clicked_value = fit_obj.map_values[y_index, x_index]
        else:
            clicked_value = None
        if event.inaxes:  # make sure the click was within the axes
            for sector in self.sector_coordinates:
                x, y = sector
                x_edge_min = (x - 0.5 / self.nsx) * self.img_size_x
                x_edge_max = (x + 0.5 / self.nsx) * self.img_size_x
                y_edge_min = (y - 0.5 / self.nsy) * self.img_size_y
                y_edge_max = (y + 0.5 / self.nsy) * self.img_size_y
                sector_key = str(sector)

                if x_edge_min <= event.xdata <= x_edge_max and y_edge_min <= event.ydata <= y_edge_max:
                    if fit_obj:
                        # Fitting process
                        if event.dblclick:
                            print(
                                f"→ Fitting sector centered at:\n"
                                f"   • X = {(sector[0] * self.img_size_x):.2f}\n"
                                f"   • Y = {(sector[1] * self.img_size_y):.2f}\n"
                            )
                            Plot(args, self.sector_acf_dict, rlc=self.rlc, sector_key=sector_key)
                            if args.show:
                                plt.show()
                    else:
                        Plot(args, self.sector_acf_dict, sector_key=sector_key, file_name=self.f_name)
                        plt.tight_layout()
                        plt.show()

                    # Print the selected sector coordinate and the corresponding value by click
                    self._display_selected_sector_info(
                        x_edge_min, x_edge_max, y_edge_min, y_edge_max, clicked_value, fit_obj
                    )

    def _display_selected_sector_info(
        self,
        x_edge_min,
        x_edge_max,
        y_edge_min,
        y_edge_max,
        clicked_value=None,
        fit_obj=None,
    ):
        if fit_obj:
            print(
                f"{fit_obj.parameter} at the following coordinates [{MICROMETER}]: \
                    {clicked_value:.2f} [{fit_obj.unit}]\n"
            )
        else:
            print(f"Selected sector with the following coordinates [{MICROMETER}]:\n")
        print(f"{x_edge_min:.2f}  {ARROW_LEFT}{ARROW_RIGHT}  {x_edge_max:.2f}\n")
        spaces = " " * 3
        print(f"{spaces}┌─────────┐{spaces}{y_edge_max:.2f}")
        print(f"{spaces}│         │")
        print(f"{spaces}│         │ {spaces}{ARROW_UP}")
        print(f"{spaces}│         │ {spaces}{ARROW_DOWN}")
        print(f"{spaces}│         │")
        print(f"{spaces}└─────────┘{spaces}{y_edge_min:.2f}")
        print("\n ---------------------------------------")

    def _mesh(self):
        # Convert sector central coordinates to real-world sizes based on the image size
        center_x = self.local_center_x * self.img_size_x
        center_y = self.local_center_y * self.img_size_y

        if self.nsx == 1 or self.nsy == 1:
            # Calculate edges
            if self.nsx == 1:
                dx = self.img_size_x / 2.0
                edges_x = np.array([center_x[0] - dx, center_x[0] + dx])
            else:
                dx = np.diff(center_x) / 2.0
                edges_x = np.concatenate(([center_x[0] - dx[0]], center_x[:-1] + dx, [center_x[-1] + dx[-1]]))

            if self.nsy == 1:
                dy = self.img_size_y / 2.0
                edges_y = np.array([center_y[0] - dy, center_y[0] + dy])
            else:
                dy = np.diff(center_y) / 2.0
                edges_y = np.concatenate(([center_y[0] - dy[0]], center_y[:-1] + dy, [center_y[-1] + dy[-1]]))

            # Create a 2D grid for pcolormesh
            mesh_ax_x, mesh_ax_y = np.meshgrid(edges_x, edges_y)
        else:
            mesh_ax_x, mesh_ax_y = center_x, center_y

        return mesh_ax_x, mesh_ax_y

    def _plot_map(self, args, file_name: str = None):
        self.args = args
        if self.model:
            if self.n_sector == 1:
                raise ValueError("\nImages in result file have not split --> Import split data ...")
            self.f_name = self.rlc.f_name
            all_parameters = self.rlc.parameter_names
            self.sector_parameters_dict = self.rlc.parameter_values

            # Determine which parameter(s) to plot map(s)
            selected_parameter = select_option(["All parameters"] + all_parameters, map=True)
            if "All parameters" in selected_parameter:
                selected_parameter = all_parameters

            n_maps = len(selected_parameter)
            fig_scale = (8 / n_maps) + n_maps

        else:  # Plot single map to select one sector for plotting ACF data or signals average
            selected_parameter, fig_scale = [1], 6
            self.f_name = file_name

        # Plot each selected parameter
        for param in selected_parameter:
            self._plot_single_parameter_map(param, fig_scale)

    def _populate_map_values(self, param: str) -> Tuple[np.ndarray, str]:
        # Initialize an empty map with NaN values to store parameter results for each sector
        map_values, unit = np.full((self.nsy, self.nsx), np.nan), ""

        # Fill the map with the parameter values for each sector based on their coordinates
        for sector in self.sector_coordinates:
            # Find the corresponding sector on the map using central coordinates
            x, y = sector
            x_index = np.where(np.isclose(self.local_center_x, x, atol=1e-3))[0]
            y_index = np.where(np.isclose(self.local_center_y, y, atol=1e-3))[0]

            # Find the corresponding result and unit of the parameter
            map_values[y_index, x_index] = self.sector_parameters_dict[str(sector)][param][MEAN]
            unit = self.sector_parameters_dict[str(sector)][param][UNIT]
        return map_values, unit

    # Generate one map per selected parameter (assuming the center of the map is at the coordinates [0, 0])
    def _plot_single_parameter_map(self, parameter, fig_scale: float):
        # Create figure and define sizes
        imgx, imgy = self.img_size_x / 2, self.img_size_y / 2
        imgydoubleclick, imgyclick = imgy + imgy / 5, imgy + imgy / 3
        fig_scale_x = fig_scale_y = fig_scale
        if self.shorter_y_axis:
            imgydoubleclick, imgyclick = imgydoubleclick + imgx / 7, imgyclick + imgx / 5
            fig_scale_y = fig_scale / 2
        fig_map, ax = plt.subplots(figsize=(fig_scale_x, fig_scale_y))
        ax.set_xlabel(f"X [{MICROMETER}]", fontsize=14, fontweight="bold")
        ax.set_ylabel(f"Y [{MICROMETER}]", fontsize=14, fontweight="bold")
        ax.set_aspect("equal", "box")

        if self.model:
            # Get map values and unit
            map_values, unit = self._populate_map_values(parameter)
            print(f"{parameter}:")
            for row in np.flip(map_values, axis=0):
                print(" ".join(f"{elem:<{8}.2f}" for elem in row))
            print()
            fit_obj = Fit(map_values, parameter, unit)
            title = parameter + " map"
            if self.ssx != 1 / self.nsx or self.ssy != 1 / self.nsy:
                title += f" (overlap: [X ➜ {(self.ssx-1/self.nsx)*100:.0f}%," f"Y ➜ {(self.ssy-1/self.nsy)*100:.0f}%])"
            click_handler = lambda event: self._click_event(event, fit_obj)  # noqa: E731
            click_txt = f"Click on the desired sector to display the result of {parameter}"
            double_click_txt = "Double-click on the desired sector to plot fitted data"
            if not self.args.pdf:
                ax.text(-imgx, imgydoubleclick, double_click_txt, fontsize=fig_scale, c="k")
        else:
            map_values = np.random.rand(self.nsy, self.nsx)
            title = "Sector Selection Map"
            click_handler = lambda event: self._click_event(event)  # noqa: E731
            click_txt = "Click on the desired sector to display the ACF data"

        # Plot map
        parameter_map = ax.pcolormesh(self.mesh_ax_x, self.mesh_ax_y, map_values)
        if not self.args.pdf:
            ax.set_title(title, color="r", fontsize=11, fontweight="bold", loc="right")
            ax.text(-imgx, imgyclick, click_txt, fontsize=fig_scale, c="k")
        fig_map.canvas.mpl_connect("button_press_event", click_handler)

        if self.model:
            # Add color bar
            if self.shorter_y_axis:
                cbar = plt.colorbar(parameter_map, ax=ax)
            else:
                divider = make_axes_locatable(ax)
                cax = divider.append_axes("right", size="5%", pad=0.1)
                cbar = plt.colorbar(parameter_map, cax=cax)
            cbar.set_label(f"{parameter} [{unit}]", fontsize=14, fontweight="bold")

            # Save map(s) as a PDF file
            if self.args.pdf:
                parameter = str(parameter).replace(" ", "-")
                file_format = ".pdf" if self.args.output is None else f"-{parameter}.pdf"
                osuf = output_suffix(self.args, f"{parameter}_map")
                plt.savefig(get_output_fname(self.f_name, self.args.output, osuf, file_format))
        else:
            plt.show()
            sys.exit()

    def _save_attributes(self, acf_group):
        acf_group.attrs[NSX] = self.nsx
        acf_group.attrs[NSY] = self.nsy
        acf_group.attrs[SSX] = self.ssx
        acf_group.attrs[SSY] = self.ssy

    def _show_sector_grid(self):
        print("\n*********** Map of sectors with local central coordinates (axes-length is unit) ************\n")
        for y in self.local_center_y[::-1]:  # reverse the y-coordinates for display from top to bottom
            print("        " + " ".join("┌─────┐" for _ in self.local_center_x))
            print(f"{y:>6.2f}  " + " ".join("│  .  │" for _ in self.local_center_x))
            print("        " + " ".join("└─────┘" for _ in self.local_center_x))
        print("       ", end="".join(f" {x:>6.2f} " for x in self.local_center_x) + "\n")
        print("\n*******************************************************************************************\n")

    """----------------- Public Methods --------------"""

    def get_ref_split_dset(self, array):
        if not np.isclose(self.rssx, 1) or not np.isclose(self.rssy, 1):
            h, w = array.shape[-2:]
            edge_y, edge_x = map(lambda x: int(round(x)), (h * self.rssy, w * self.rssx))
            diff_y, diff_x = (h - edge_y) // 2, (w - edge_x) // 2
            if diff_y == 0 and diff_x == 0:
                ref_split_dset = array
            else:
                y_slice = slice(None) if diff_y == 0 else slice(diff_y, -diff_y)
                x_slice = slice(None) if diff_x == 0 else slice(diff_x, -diff_x)
                ref_split_dset = array[..., y_slice, x_slice]
        else:
            ref_split_dset = array
        return ref_split_dset

    def plot_split_image(self):
        def rectangle(x, y, width, height, ec, lw, label=None, ls="-", alpha=1):
            return plt.Rectangle(
                (x, y),
                width,
                height,
                ec=ec,
                lw=lw,
                label=label,
                fc="none",
                ls=ls,
                alpha=alpha,
            )

        random_array = np.random.rand(1000, 1000)
        fig = plt.figure(figsize=FIG_SIZE_PRE_MAP)
        sub = fig.add_subplot(111)
        sub.imshow(random_array, aspect="equal", alpha=0.3)
        sub.set_xlabel("X")
        sub.set_ylabel("Y")

        # Original width-height of each sector without overlap
        ssx_orig, ssy_orig = 1 / self.nsx, 1 / self.nsy

        ssx, ssy, rssx, rssy = self.ssx, self.ssy, self.rssx, self.rssy
        dx, dy = ssx * 999, ssy * 999  # sector size in 1000x1000 scale
        vl = f"Split image to into {self.nsx}x{self.nsy} sectors"
        x = np.arange(0, 999, 999 / self.nsx)[1:]
        y = np.arange(0, 999, 999 / self.nsy)[1:]
        sub.vlines(x, ymin=0, ymax=999, colors="k", lw=1, label=vl)
        sub.hlines(y, xmin=0, xmax=999, colors="k", lw=1)

        if not (np.isclose(ssx, ssx_orig, rtol=1e-4) and np.isclose(ssy, ssy_orig, rtol=1e-4)):
            lbl = f"Sector with overlap: [{(ssx - ssx_orig)*100:.0f}%, {(ssy - ssy_orig)*100:.0f}%]"
            lbla = "Adjacent sectors"
            ss_square = rectangle(0, 0, dx, dy, "red", 2, lbl, "--", 0.6)
            sub.add_patch(ss_square)

            shift_x = (ssx_orig - ((ssx - ssx_orig) / (self.nsx - 1))) * 999 if self.nsx > 1 else 0
            shift_y = (ssy_orig - ((ssy - ssy_orig) / (self.nsy - 1))) * 999 if self.nsy > 1 else 0
            ss_square_2 = rectangle(shift_x, 0, dx, dy, "salmon", 2, lbla, "--", 0.45)
            sub.add_patch(ss_square_2)
            ss_square_3 = rectangle(0, shift_y, dx, dy, "salmon", 2, ls="--", alpha=0.45)
            sub.add_patch(ss_square_3)

            # Centers
            cl, cll = self.sector_centers_local, "Sector centers after overlap"
            centers_x, centers_y = (cl[:, 0] + 0.5), (cl[:, 1] + 0.5)
            sub.scatter(centers_x * 999, centers_y * 999, color="k", marker="x", s=1000 / self.n_sector, label=cll)

        # Reference sector -> pair correlation
        if not np.isclose(self.rssx, 1) or not np.isclose(self.rssy, 1):
            drx, dry = rssx * ssx * 999, rssy * ssy * 999  # reference sector size in 1000x1000 scale
            diff_x, diff_y = (ssx - (rssx * ssx)) * 499, (ssy - (rssy * ssy)) * 499
            ref_lbl = "Reference sector size"
            ss_square = rectangle(diff_x, diff_y, drx, dry, "b", 2, label=ref_lbl)
            sub.add_patch(ss_square)

        sub.text(10, -10, "To continue the calculation process, close the figure.", fontsize=15)
        plt.legend()
        plt.tight_layout()
        plt.show()

    def split_image_into_sectors(self, array: np.ndarray) -> np.ndarray:
        # Get image dimensions
        height, width = array.shape

        # Calculate sector dimensions in pixels
        sector_width = int(round(width * self.ssx))
        sector_height = int(round(height * self.ssy))

        # Calculate the spacing between sector centers in pixels
        spacing_x = int((width - sector_width) / (self.nsx - 1)) if self.nsx > 1 else 0
        spacing_y = int((height - sector_height) / (self.nsy - 1)) if self.nsy > 1 else 0

        # Generate sectors
        sectors = []
        for i in range(self.nsx):
            start_x = i * spacing_x

            for j in range(self.nsy):
                start_y = j * spacing_y

                # Calculate end coordinates (handling boundary cases)
                end_x = min(start_x + sector_width, width)
                end_y = min(start_y + sector_height, height)

                # Extract the sector
                sector = array[start_y:end_y, start_x:end_x]
                sectors.append(sector)
        return sectors

    """----------------- Static Methods --------------"""

    # static
    @staticmethod
    def splitting_data(args, n_data, angle, acf_group) -> "Map":
        def parse_dimensions(error_message, args_attr, attr_type):
            try:
                values = [attr_type(x.strip()) for x in args_attr.split(",")]
            except ValueError:
                print("The values must be comma-separated")
            # Parse dimension values that can be provided as either a single value or a pair
            if len(values) == 2:
                return values[0], values[1]  # unpack values along x and y axes
            elif len(values) == 1:
                return values[0], values[0]  # use the same value for both axes
            else:
                raise ValueError(f"\n{error_message}")

        split_img, sector_size = args.split_image, args.sector_size
        ref_sector_size = args.reference_sector_size
        if split_img == 1:
            nsx = nsy = ssx = ssy = rssx = rssy = ssx_orig = ssy_orig = 1
            if sector_size or ref_sector_size:
                sp_error = "\nFirst, split the images using -sp or --split-image, then determine the sector size."
                raise Exception(sp_error)
        else:
            error = "Provide either two indices (e.g., `-sp 2,3`) or a single number (e.g., `-sp 2`)."
            nsx, nsy = parse_dimensions(error, split_img, int)
            print(f"Images are split into {nsx} x {nsy} sectors")
            n_sector = nsx * nsy  # total number of sectors
            print(f"Number of images after splitting: {n_data * n_sector}")

            # Original width-height of each sector without overlap
            ssx_orig, ssy_orig, ov = 1 / nsx, 1 / nsy, None

            # Process sector size
            ssx, ssy = ssx_orig, ssy_orig  # default values

            if sector_size:
                ss_error = "Provide either two indices (e.g., `-ss 2,3`) or a single number (e.g., `-ss 2`)."
                ssx, ssy = parse_dimensions(ss_error, sector_size, float)

                # Validate sector_size
                if not (0 < ssx <= 1 and 0 < ssy <= 1):
                    raise ValueError("\nSector size must be between 0 and 1")

                if ssx < ssx_orig or ssy < ssy_orig:
                    raise ValueError(
                        "\nExpanded sector size must be larger than the original sector size: "
                        f"{[ssx_orig, ssy_orig]}."
                    )
                if ssx == ssx_orig and ssy == ssy_orig:
                    raise ValueError(
                        "\nAt least one sector dimension must increase after expansion. "
                        f"Current size: {[ssx_orig, ssy_orig]}."
                    )
                if ssx > 1 or ssy > 1:
                    raise ValueError("\nSector size is larger than selected main sector")
                ovx, ovy = ssx - ssx_orig, ssy - ssy_orig
                ov = f"The overlap along X-Y axes: [{ovx * 100:.0f}%, {ovy * 100:.0f}%]"
            print(
                f"Sector size along X-Y axes: [{ssx * 100:.0f}%, {ssy * 100:.0f}%] of image size",
                f"\n{ov}" if ov else "",
            )

            # Process reference sector size (ref_sector_size)
            rssx, rssy = 1, 1
            if ref_sector_size:
                rss_error = "Provide either two values (e.g., `-rss 0.5,0.5`) or a single number (e.g., `-rss 0.5`)."
                rssx, rssy = parse_dimensions(rss_error, ref_sector_size, float)

                # Validate reference sector size
                if not (0 < rssx <= 1 and 0 < rssy <= 1):
                    raise ValueError("\nReference sector size must be between 0 and 1.")

                if np.isclose(rssx, 1) and np.isclose(rssy, 1):
                    raise ValueError("\nReference sector size is equal to the main sector size.")
                inf = f"[{rssx * ssx * 100:.0f}%, {rssy * ssy * 100:.0f}%]"
                print(f"Reference sector size along X-Y axes: {inf} of image size")
        sector = Sector(nsx, nsy, ssx, ssy, rssx, rssy)
        return Map(sector=sector, angle=angle, acf_group=acf_group)

    # static
    @staticmethod
    def map_data(args, sector_acf_dict: Dict, rlc=None, file_name=None) -> "Map":
        sector_coordinates = [acf_dict[next(iter(acf_dict))].sector_coordinate for acf_dict in sector_acf_dict.values()]
        first_acf_dict = sector_acf_dict[next(iter(sector_acf_dict))]
        first_acf = first_acf_dict[next(iter(first_acf_dict))]
        img_size_x, img_size_y = first_acf.image_size_x, first_acf.image_size_y
        nsx, nsy = first_acf.split
        ssx, ssy = first_acf.sector_size
        map_class = Map(
            sector=Sector(nsx, nsy, ssx, ssy),
            rlc=rlc,
            img_size_x=img_size_x,
            img_size_y=img_size_y,
            sector_acf_dict=sector_acf_dict,
            sector_coordinates=sector_coordinates,
        )
        map_class._plot_map(args, file_name=file_name)
