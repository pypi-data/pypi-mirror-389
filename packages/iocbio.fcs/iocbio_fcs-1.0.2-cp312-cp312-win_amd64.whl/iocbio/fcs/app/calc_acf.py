#!/usr/bin/env python3
import argparse
import h5py
import numpy as np
from dataclasses import dataclass
from scipy.signal import correlate

from iocbio.fcs.lib.const import (
    ATTR_ACF_KEY,
    ATTR_ANGLE,
    ATTR_ISX,
    ATTR_ISY,
    ATTR_LINETIME,
    ATTR_ORIGINDATA,
    ATTR_PIXTIME,
    ATTR_PROTOCOL,
    ATTR_PSX,
    ATTR_PSY,
    CORR_MODE,
    DATA_ACF_KEY,
    DATA_FILENAME,
    DATA_ENCODE,
    DATA_SECTOR_COORD,
    DATA_SELECTED_RANGE,
    DEC_RICSPROTOCOL,
    DEC_FCSPROTOCOL,
    DEGREE,
    DELTA,
    GROUP_ACF,
    GROUP_AVG,
    GROUP_RICS,
    MICROMETER,
    UNIT_LINE_TIME,
    UNIT_PIXEL_TIME,
)

# Load Cupy and check if GPU is available
try:
    import cupy as cp
    from cupyx.scipy.signal import fftconvolve

    # Try a trivial GPU operation to check if a CUDA device is available
    _ = cp.zeros((1,))
    gpu_available = True
except:  # noqa: E722
    gpu_available = False

from iocbio.fcs.lib.input import analyze_input_file
from iocbio.fcs.lib.map import Map
from iocbio.fcs.lib.utils import filtering, get_output_fname, split_indx


@dataclass
class AcfAttrs:
    acf_key: str
    origin: str
    pixel_time: float
    angle: float = 0
    image_size_x: int = 0
    image_size_y: int = 0
    line_time: float = 0
    pixel_size_x: float = 0
    pixel_size_y: float = 0


"""---------- Utility Functions ----------"""


def apply_filter(array, selected_range, data_type=None):
    # Filter data according to a specified range
    if selected_range:
        array = filtering(array, selected_range)
        if data_type:
            n_data = len(array)  # number of dataset after filtering
            print(f"Number of {data_type} after filtering: ", n_data)
    return array


def array_info(start, end, n_sector, dataset_shape, sector_shape, acf_cropped_shape):
    print(f"Dataset from {start} to {end} ({end - start} images):")
    sd, spaces = "    Shape of dataset", ""
    if n_sector != 1:
        info = sd + " inside sectors: " + str(sector_shape)
        spaces = " " * 12
    else:
        info = None
    print(f"Shape of origin dataset:{spaces}", dataset_shape)
    if info:
        print(info)
    print(f"    Shape of ACF:       {spaces}", acf_cropped_shape, "\n")


# Function to produce unique ACF keys from attributes
def produce_key(pixel_time, lt=0, angle=0, px=0, py=0):
    acf_key = (
        f"line time {lt * 1000:.1f} [{UNIT_LINE_TIME}] | "
        + f"angle {angle:03.1f} {DEGREE} | "
        + f"{DELTA}x {px:.3f} [{MICROMETER}] | "
        + f"{DELTA}y {py:.3f} [{MICROMETER}] | "
        + f"pixel time {pixel_time:.2e} [{UNIT_PIXEL_TIME}]"
    )
    return acf_key


class ACFCalc:
    def __init__(self):
        self.norm = None

    def __call__(self, array, ref_array, nf):
        if gpu_available:
            return self._calc_gpu(array, ref_array, nf)
        return self._calc_cpu(array, ref_array, nf)

    def _calc_cpu(self, array, ref_array, nf):
        # Auto Correlation Function (ACF)
        acf = correlate(array, ref_array, mode=CORR_MODE)

        # Create an array of ones and compute its self-correlation
        # to normalize `scipy.signal.correlate` function:
        # https://docs.scipy.org/doc/scipy-1.15.2/reference/generated/scipy.signal.correlate.html
        if self.norm is None or self.norm.shape != acf.shape:
            ones_array = np.ones(acf.shape)
            ones_ref = np.ones(ref_array.shape)
            self.norm = correlate(ones_array, ones_ref, mode=CORR_MODE)

        """
        Normalization
        - Compute the variance of the background-subtracted array when background subtraction is needed
          (e.g., diffusion in cells).
        - Compute the mean of the original array for cases where background subtraction is not needed
          (e.g., diffusion in solution).
        - If the photon counts in each image follow Poisson statistics, the mean value approximates
          the variance.
        - Based on this assumption and literature, the ACF (Autocorrelation Function) can be
          normalized by dividing by either mean² or variance².
        - Reference: https://www.biophysics.org/Portals/0/BPSAssets/Articles/schwille.pdf
        """

        return acf / self.norm / nf / nf

    def _calc_gpu(self, array, ref_array, nf):
        # Flip to use fftconvolve
        flip = tuple(slice(None, None, -1) for _ in range(ref_array.ndim))

        # Auto Correlation Function (ACF)
        acf = fftconvolve(array, ref_array[flip], mode=CORR_MODE)

        # Create an array of ones and compute its self-correlation
        # to normalize data
        if self.norm is None or self.norm.shape != acf.shape:
            ones_array = cp.ones(acf.shape)
            ones_ref = cp.ones(ref_array.shape)  # ones don't have to be flipped
            self.norm = fftconvolve(ones_array, ones_ref, mode=CORR_MODE)

        return cp.asnumpy(acf / self.norm / nf / nf)


def save_acf_data(acf_dataset, acf_attributes):
    acf_dataset.attrs[ATTR_ACF_KEY] = acf_attributes.acf_key
    acf_dataset.attrs[ATTR_ANGLE] = acf_attributes.angle
    acf_dataset.attrs[ATTR_ISX] = acf_attributes.image_size_x
    acf_dataset.attrs[ATTR_ISY] = acf_attributes.image_size_y
    acf_dataset.attrs[ATTR_LINETIME] = acf_attributes.line_time
    acf_dataset.attrs[ATTR_ORIGINDATA] = acf_attributes.origin
    acf_dataset.attrs[ATTR_PSX] = acf_attributes.pixel_size_x
    acf_dataset.attrs[ATTR_PSY] = acf_attributes.pixel_size_y
    acf_dataset.attrs[ATTR_PIXTIME] = acf_attributes.pixel_time


"""---------- RICS Processing Function ----------"""


def process_rics(args, acf_file, data):
    group = data.group
    images_group = data.images_group
    data_filename = data.filenames
    pixel_time = data.pixel_time
    n_data = len(data_filename)  # number of dataset (images in RICS)

    print("Number of images: ", n_data)
    selected_range = args.filter_range
    selected_indexes = split_indx(selected_range) if selected_range else [0, n_data]
    data_filename = apply_filter(data_filename, selected_range, data_type="images")
    n_data = len(data_filename)  # # number of dataset after filtering

    # Read attributes
    rics_group = group[GROUP_RICS]
    angle = apply_filter(rics_group["angle"], selected_range)
    reltime = apply_filter(rics_group["relative time"], selected_range)
    line_time = apply_filter(rics_group["line scan time"], selected_range)
    flyback = apply_filter(rics_group["flyback"], selected_range)
    image_size_x = apply_filter(rics_group["pixels per line"], selected_range)
    image_size_y = group["Configuration"].attrs.get("CONFOCAL_ImageSizeY", 0)

    # Calculate line time with flyback
    lt = np.array(line_time) * (1 + np.array(flyback))

    # Generate ACF keys based on the attributes
    acf_key_list, pixel_size_x_list, pixel_size_y_list = [], [], []
    for i in range(n_data):
        # Collect pixel sizes [dx, dy]
        dset = images_group[data_filename[i]]
        pixel_size_x = dset.attrs["PixelSizeX"]
        pixel_size_y = dset.attrs["PixelSizeY"]
        pixel_size_x_list.append(pixel_size_x)
        pixel_size_y_list.append(pixel_size_y)
        acf_key = produce_key(pixel_time, lt=lt[i], angle=angle[i], px=pixel_size_x, py=pixel_size_y)
        acf_key_list.append(acf_key)

    # Create ACF group
    acf_group = acf_file.create_group(GROUP_ACF)

    # Splitting and Sectors
    split = Map.splitting_data(args, n_data, angle, acf_group)
    n_sector = split.n_sector

    if n_sector != 1 and args.show_sectors:
        split.plot_split_image()
    print("________________________________________\n")

    # Slots (grouping images with similar features into slots)
    max_image_per_slot = args.max_num_image_per_slot
    borders, last_slot_i = [], 0
    for i in range(n_data):
        if (
            acf_key_list[i] != acf_key_list[i - 1]
            or round(reltime[i], 3) != round(reltime[i - 1], 3)
            or i == max_image_per_slot + last_slot_i
        ):
            borders.append(i)
            last_slot_i = i
    if len(borders) == 0:
        borders.append(0)
    borders.append(n_data)

    # Zipping borders
    slots = list(zip(borders[:-1], borders[1:]))
    first_image_index = slots[0][0]

    # Subtract background -> collect images of slots and calculate average for each slot (2D-array)
    # and save as background-slots
    has_background = args.background

    # Check number of images in slots
    if args.check_slots and has_background:
        slot_min = min(np.diff(slots))[0]
        slot_max = max(np.diff(slots))[0]
        ignore_check_slots = "To skip checking slots, use --no-check-slots."

        if max_image_per_slot != 0 and slot_min != max_image_per_slot:
            slot_min_indx = np.where(np.diff(slots) == slot_min)[0][0]
            fe = selected_indexes[0]  # first element
            le = selected_indexes[-1]  # last element

            if slot_min_indx == 0:
                suggestion = (
                    f"Please change the first element of the filter range "
                    f"({fe} -> {fe - (max_image_per_slot - slot_min)} "
                    f"or {fe + slot_min}). {ignore_check_slots}"
                )
            elif slots[slot_min_indx] == slots[-1]:
                suggestion = (
                    "Please change the last element of the filter range "
                    f"({le} -> {le - slot_min + max_image_per_slot} "
                    f"or {le - slot_min}). {ignore_check_slots}"
                )
            else:
                suggestion = f"Please change the filter range. {ignore_check_slots}"

            raise ValueError(
                f"\nSelected maximum number of images in a slot is {max_image_per_slot}.\n"
                f"But there are {slot_min} images in the slot {slots[slot_min_indx]}.\n"
                f"{suggestion}"
            )

        if slot_max != slot_min and selected_range:
            raise ValueError(
                f"\nThe number of images in the selected slots differs: {np.diff(slots).tolist()}.\n"
                f"Please adjust the filter ranges.\n{ignore_check_slots}"
            )

        if slot_max != slot_min and max_image_per_slot == 0:
            raise ValueError(
                f"\nThe number of images in the slots differs: {np.diff(slots).tolist()}.\n"
                "Please determine the maximum number of images per slot (For example -mi 30).\n"
                f"{ignore_check_slots}"
            )

    if has_background:
        print("Number of slots:", len(slots))
        print("Collect images of slots and subtract background ... \n")
        average_group = acf_file.create_group(GROUP_AVG)

    # Correlation
    filename_list, sector_center_list = [], []

    # Save X-number of dataset in a HDF5 subgroup
    n_data_subgroup = args.num_data_in_subgroup

    if gpu_available:
        used_array = cp.array
        used_mean = cp.mean
        used_var = cp.var
    else:
        used_array = np.array
        used_mean = np.mean
        used_var = np.var

    for slot_index, (start, end) in enumerate(slots):
        images_in_slot = None

        if has_background:
            images_in_slot = []
            for i in range(start, end):
                dataset_array = used_array(images_group[data_filename[i]])
                images_in_slot.append(dataset_array)

            images_in_slot = used_array(images_in_slot)

            # Average of images in one slot
            avg_slot = used_mean(images_in_slot, axis=0)

            # Save average-slots in HDF file
            average_group.create_dataset(
                f"Slot {slot_index}: average of images from {start} to {end}",
                data=avg_slot.get() if gpu_available else avg_slot,
            )

        # Calc engine
        calculate_acf = ACFCalc()

        for i in range(start, end):
            if images_in_slot is not None:
                dataset_array = images_in_slot[i - start]
            else:
                dataset_array = used_array(images_group[data_filename[i]])

            if has_background:
                dataset_array = dataset_array - avg_slot

            # split into sectors
            split_dset = split.split_image_into_sectors(dataset_array)
            split_dset = used_array(split_dset)

            # Subtract mean value as background if slot bg subtraction is not used
            if has_background:
                background_corrected = split_dset
            else:
                sector_mean = used_mean(split_dset, axis=(1, 2))
                background_corrected = split_dset - sector_mean[:, np.newaxis, np.newaxis]

            # Normalization factor
            nf = used_var(background_corrected, axis=(1, 2), ddof=1) if has_background else sector_mean

            subgroup_name = f"{i // n_data_subgroup}"  # name of ACF subgroup

            if i % n_data_subgroup == 0 or i == first_image_index:
                acf_subgroup = acf_group.create_group(subgroup_name)

            for sector_index in range(n_sector):
                bc = background_corrected[sector_index]

                # Compute the normalized ACF
                ref_split_dset = split.get_ref_split_dset(bc)
                normalized_acf = calculate_acf(bc, ref_split_dset, nf[sector_index])

                acf_shape = normalized_acf.shape
                middle_y, middle_x = acf_shape[0] // 2, acf_shape[1] // 2

                # Crop ACF using args.limit_y and args.limit_x
                cropped_acf = normalized_acf[
                    max(0, middle_y - args.limit_y) : min(acf_shape[0], middle_y + args.limit_y + 1),
                    max(0, middle_x - args.limit_x) : min(acf_shape[1], middle_x + args.limit_x + 1),
                ]

                # Print shape of arrays
                if sector_index == 0 and i == start:
                    dataset_shape, sector_shape = dataset_array.shape, split_dset[0].shape
                    array_info(start, end, n_sector, dataset_shape, sector_shape, cropped_acf.shape)

                # Save and find location of sector center after rotation
                location = split.sector_centers[f"{angle[i]}-{split.sector_centers_local[sector_index]}"]
                sector_center_list.append(location)

                # Save data and attributes
                dset_name = f"{GROUP_ACF}_{i:07d}_{sector_index}"  # name of ACF dataset, e.g., ACF_0000100_0
                acf_dataset = acf_subgroup.create_dataset(dset_name, data=cropped_acf)
                filename_list.append(bytes(subgroup_name + "/" + dset_name, encoding=DATA_ENCODE))
                acf_attributes = AcfAttrs(
                    acf_key=acf_key_list[i],
                    angle=angle[i],
                    image_size_x=image_size_x[i],
                    image_size_y=image_size_y,
                    line_time=lt[i],
                    origin=data_filename[i],
                    pixel_size_x=pixel_size_x_list[i],
                    pixel_size_y=pixel_size_y_list[i],
                    pixel_time=pixel_time,
                )
                save_acf_data(acf_dataset, acf_attributes)

    acf_group.create_dataset(DATA_ACF_KEY, data=list(set(acf_key_list)))
    acf_group.create_dataset(DATA_FILENAME, data=np.array([filename_list]))
    acf_group.create_dataset(DATA_SECTOR_COORD, data=sector_center_list)
    acf_group.create_dataset(DATA_SELECTED_RANGE, data=selected_indexes)
    acf_group.attrs[ATTR_PROTOCOL] = DEC_RICSPROTOCOL  # decoded protocol


"""---------- FCS Processing Function ----------"""


def process_fcs(args, acf_file, data):
    images_group = data.images_group
    data_filename = data.filenames
    pixel_time = data.pixel_time
    n_data = len(data_filename)  # number of dataset (traces in FCS)
    selected_indexes = [0, n_data]

    if args.background:
        raise Exception("\nSubtract background is not available for FCS protocol")
    if n_data > 1:
        selected_range = args.filter_range
        print("Number of traces: ", n_data)
        data_filename = apply_filter(data_filename, selected_range, data_type="traces")
        n_data = len(data_filename)
        selected_indexes = split_indx(selected_range) if selected_range else selected_indexes

    filename_list, acf_key_list, acf_group = [], [], None
    calculate_acf = ACFCalc()
    for trace_index, name in enumerate(data_filename):
        trace = images_group[name]
        trace_array = np.array(trace[0, :])

        # Cutting trace
        start_time = round(args.t0 / pixel_time)
        start_time_index = int(start_time)
        if args.t1 is None:
            end_time_index = None
        else:
            end_time = round(args.t1 / pixel_time)
            end_time_index = int(end_time)
        cut_trace = trace_array[start_time_index:end_time_index]
        if gpu_available:
            cut_trace = cp.asarray(cut_trace)

        if trace_index == 0:
            print("Number of steps:", len(cut_trace))

        if n_data > 1:
            print(
                "\n-----------------",
                f"trace {trace_index}",
                "----------------------",
            )

        mean_trace = np.mean(cut_trace, axis=0)
        print("Mean photon count rate [counts/s]:", f"{mean_trace / pixel_time:.3f}")
        array = cut_trace - mean_trace
        normalized_acf = calculate_acf(array, array, nf=mean_trace)

        dset_name = f"{GROUP_ACF}_{trace_index:07d}"  # name of ACF dataset, e.g., ACF_0000100
        if acf_group is None:
            acf_group = acf_file.create_group(GROUP_ACF)
            acf_subgroup = acf_group.create_group("0")
        cut_points = (len(normalized_acf) // 2) - args.crop_acf
        cropped_acf = normalized_acf[cut_points:-cut_points] if cut_points > 0 else normalized_acf

        # Save data and attributes
        acf_dataset = acf_subgroup.create_dataset(dset_name, data=[cropped_acf])
        filename_list.append(bytes(f"0/{dset_name}", encoding=DATA_ENCODE))
        acf_key = produce_key(pixel_time=pixel_time)
        acf_key_list.append(acf_key)
        acf_attributes = AcfAttrs(
            acf_key=acf_key,
            origin=name,
            pixel_time=pixel_time,
        )
        save_acf_data(acf_dataset, acf_attributes)

    acf_group.create_dataset(DATA_ACF_KEY, data=list(set(acf_key_list)))
    acf_group.create_dataset(DATA_FILENAME, data=np.array([filename_list]))
    acf_group.attrs[ATTR_PROTOCOL] = DEC_FCSPROTOCOL  # decoded protocol
    acf_group.create_dataset(DATA_SELECTED_RANGE, data=selected_indexes)


"""---------- Main Processing Functions for RICS/FCS ----------"""


def acf_analysis(args, input_file):
    # Import data
    data = analyze_input_file(input_file)

    # Create HDF file
    acf_file = h5py.File(get_output_fname(input_file, args.output), "w")

    if data.decoded_protocol == DEC_RICSPROTOCOL:
        process_rics(args, acf_file, data)
    elif data.decoded_protocol == DEC_FCSPROTOCOL:
        process_fcs(args, acf_file, data)
    else:
        raise Exception(f"\nProtocol ({data.protocol}) is not FCS or RICS")


def main():
    global gpu_available

    # Arguments
    parser = argparse.ArgumentParser(
        description="Calculate Auto-correlation of data (RICS/FCS)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Input file(s)
    parser.add_argument("filename", nargs="+", help="Input file name (RICS/FCS file)")

    # Filtering parameters
    parser.add_argument(
        "-fr",
        "--filter-range",
        type=str,
        default=None,
        help="Comma-separated list of start and end indexes for ranges (integer)."
        "Load images/traces between from start-index to end-index, and filter out rest"
        "For example: '-fr 10,20,500,1200' or for single FCS trace: '-fr 2'",
    )
    parser.add_argument("--t0", type=float, default=0, help="Time from t0 to t1 [second] (only FCS)")
    parser.add_argument("--t1", type=float, default=None, help="Time from t0 to t1 [second] (only FCS)")

    # Background subtraction and slots (available only for RICS)
    parser.add_argument(
        "-bg",
        "--background",
        action="store_true",
        help="Subtract slot background (only RICS)",
    )
    parser.add_argument(
        "-mi",
        "--max-num-image-per-slot",
        type=int,
        default=0,
        help="Maximum number of images per slot (only RICS)",
    )
    parser.add_argument(
        "-cs",
        "--check-slots",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable or disable checking the number of images per slot " "(enabled by default when max-slot > 0)",
    )

    # Splitting images to sectors (available only for RICS)
    parser.add_argument(
        "-sp",
        "--split-image",
        type=str,
        default=1,
        help="Comma-separated list of integers to divide images into N x K sectors. "
        "Specify N (number of sectors along X-axis) and "
        "K (number of sectors along Y-axis) as integers. "
        "Examples: "
        "`-sp 2,3` splits the image into 2 x 3 sectors "
        "`-sp 2` or `-sp 2,2` splits the image into 2 x 2 sectors (when N = K)"
        "Default is 1 x 1 (no splitting)",
    )
    parser.add_argument(
        "-ss",
        "--sector-size",
        type=str,
        default=None,
        help="Comma-separated list of floats to specify sector size as a fraction of "
        "the full image dimensions (= [1, 1]), creating overlap between adjacent sectors. "
        "Provide values for X and Y axes (float numbers between 0 and 1). "
        "Examples: "
        "`-ss 0.6` creates sectors of size 0.6 x 0.6 (with 0.1 overlap along X and Y axes in a 2 x 2 grid)."
        "`-ss 0.3,0.5` creates sectors of size 0.3 x 0.5 (with 0.1 overlap along X axis and 0.3 overlap "
        "along Y axis in a 5 x 5 grid). "
        "In the cases that images divided into N x K sectors, sector-size values should be > 0 and "
        "larger than 1/N (1/K) to create overlap. Default is no overlap (sectors sized exactly 1/N x 1/K).",
    )
    parser.add_argument(
        "-rss",
        "--reference-sector-size",
        type=str,
        default=None,
        help="Comma-separated list of floats to specify the size of the reference sector as a "
        "fraction of the sector dimensions. For example, [1, 1] means the reference sector is the same "
        "size as the main sector (autocorrelation).\n"
        "Used for pairwise correlation calculations between a main sector (defined by `--sector-size`) and "
        "a reference sector (defined by `--reference-sector-size`). The reference sector must be smaller "
        "than or equal to the main sector.\n"
        "Values must be floats between 0 and 1. Example:\n"
        "  `-ss 0.4,0.4 -rss 0.6,0.6` → correlates a 0.4x0.4 sector with a reference of size 0.24x0.24 "
        "(0.6 x 0.4 in each dimension).\n"
        "Default = None: autocorrelation.",
    )
    parser.add_argument(
        "--show-sectors",
        action="store_true",
        help="Shows splitting details (disabled by default)",
    )

    # Choose computation mode: GPU (default) or CPU (if GPU is disabled)
    parser.add_argument(
        "--disable-gpu",
        action="store_true",
        help="Disable GPU support and use CPU for calculations",
    )

    # Output parameters
    parser.add_argument(
        "-num",
        "--num-data-in-subgroup",
        type=int,
        default=100,
        help="Limit the number of dataset saved per subgroup in HDF5 (only RICS)",
    )
    parser.add_argument(
        "-ly",
        "--limit-y",
        type=int,
        default=4,
        help="Crop the ACF data by setting a vertical limit from" "the center to the top and bottom edges (only RICS)",
    )
    parser.add_argument(
        "-lx",
        "--limit-x",
        type=int,
        default=200,
        help="Crop the ACF data by setting a horizontal limit from"
        "the center to the left and right edges (only RICS)",
    )
    parser.add_argument(
        "-c",
        "--crop-acf",
        type=int,
        default=40000,
        help="Crop the ACF data by setting a limit from the center to the left and right edges (only FCS)",
    )
    parser.add_argument("-o", "--output", default=None, help="Prefix for output files")

    args = parser.parse_args()

    if args.disable_gpu:
        gpu_available = False

    if gpu_available:
        print("\nUsing GPU for calculations\n")
    else:
        print("\nCalculations performed on CPU\n")

    for input_file in args.filename:
        print("Analyzing:", input_file)
        acf_analysis(args, input_file)
        print()


if __name__ == "__main__":
    main()
