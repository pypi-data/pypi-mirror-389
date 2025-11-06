import curses
import os
import sys
import numpy as np
from pathlib import Path

from iocbio.fcs.lib.const import ANALYSIS_SUFF, ARROW_DOWN, ARROW_UP, GLS, WLS, OLS


""" Alphabetical order """


def error_structure(args):
    # Correlated errors
    if getattr(args, "covariance", False):
        err_structure = GLS
    # Weighted errors
    elif getattr(args, "error", False):
        err_structure = WLS
    # Uniform errors
    else:
        err_structure = OLS
    return err_structure


def filtering(array, selected_range):
    result = []

    if len(array) == 1:
        raise ValueError("\nThere is one image/trace. Do not use filter range.")

    if type(selected_range) is list:
        selected_indexes = selected_range
    else:
        selected_indexes = split_indx(selected_range)

    if len(selected_indexes) % 2 != 0:
        if len(selected_indexes) == 1:
            result.append(array[selected_indexes[0]])
            return result
        else:
            raise ValueError("\nProvide an even number of indices; e.g., '-fr 10 20' or '-fr 100 200 1000 2000'")
    for i in range(0, len(selected_indexes), 2):
        start_index = selected_indexes[i]
        end_index = selected_indexes[i + 1]
        if end_index <= start_index and end_index > 0:
            raise ValueError(f"\nEnd index must be greater than start index (start: {start_index}, end: {end_index})")
        if end_index == -1:
            end_index = len(array)
        result.extend(array[start_index:end_index])
    return result


def get_output_fname(input_fname, args_output, suffix=ANALYSIS_SUFF, file_format=".h5"):
    input_fname = str(Path(input_fname).with_suffix(""))
    prefixed_input = input_fname + suffix
    if args_output:
        args_output = Path(args_output)
        if args_output.is_dir() and args_output.exists():
            directory_path = args_output
            output_file_name = prefixed_input
        else:
            dir_parent = args_output.parent
            dir_name = args_output.name
            par = str(dir_parent)
            if dir_parent.is_dir() and dir_parent.exists():
                if par == "/":
                    if Path(dir_name).is_dir() and Path(dir_name).exists():
                        directory_path = dir_name
                    else:
                        os.makedirs(dir_name, exist_ok=True)
                        directory_path = dir_name
                    output_file_name = prefixed_input
                else:
                    directory_path = dir_parent
                    output_file_name = dir_name
            else:
                new_directory = Path(par[1:]) if par[0] == "/" else Path(par)
                os.makedirs(new_directory, exist_ok=True)
                directory_path = new_directory
                output_file_name = dir_name
    else:
        directory_path = ""
        output_file_name = prefixed_input
    output = os.path.join(directory_path, output_file_name + file_format)
    return output


def output_suffix(args, fig_name):
    suffix = "_" + fig_name
    if args.filter_concentration is not None:
        start_c, end_c = args.filter_concentration
        suffix = suffix + f"_filtered-concentration-{start_c}-{end_c}"
    if args.filter_diffusion_coefficient is not None:
        start_dc, end_dc = args.filter_diffusion_coefficient
        suffix = suffix + f"_filtered-diffusion-{start_dc}-{end_dc}"
    if getattr(args, "psf_scale", False):
        suffix = suffix + "_psf_scale"

    if args.reduction_factor > 1:
        suffix = suffix + f"_rf-{args.reduction_factor}"
    if args.exclude_acf:
        suffix += f"_excluded-first-{args.exclude_acf}-data" if args.exclude_acf > 1 else "_excluded-first-data"
    return suffix


def rotation_func(angle_i, x_local, y_local):
    # Direction of the turn is anticlockwise
    angle_radian = np.radians(angle_i)
    x_physical = x_local * np.cos(angle_radian) - y_local * np.sin(angle_radian)
    y_physical = y_local * np.cos(angle_radian) + x_local * np.sin(angle_radian)
    return x_physical, y_physical


def select_option(options, map=False, args=None):
    selected_options = []

    def screen(stdscr):
        stdscr.clear()
        stdscr.refresh()

        # Initialize screen
        curses.curs_set(0)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

        # Check terminal size
        min_height = len(options) + 15  # minimum height needed for the menu and additional messages
        min_width = max(len(option) for option in options) + 10  # extra space for padding
        h, w = stdscr.getmaxyx()

        if h < min_height or w < min_width:
            stdscr.addstr(0, 0, "Error: Terminal window is too small. Please resize it or zoom out and try again.")
            stdscr.refresh()
            stdscr.getch()  # wait for user input before exiting
            sys.exit(1)

        # Menu options
        options.append("Quit")
        current_row = 0

        def print_options(stdscr, selected_row_idx):
            h, w = stdscr.getmaxyx()
            for idx, row in enumerate(options):
                x = w // 2 - len(row) // 2
                y = h // 2 - len(options) // 2 + idx
                if idx == selected_row_idx:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, x, row)
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(y, x, row)
            stdscr.refresh()

        def print_selected_options(stdscr):
            h, w = stdscr.getmaxyx()
            y = h // 2 + len(options) // 2 + 1
            stdscr.addstr(y, 0, "Selected options: " + ", ".join(selected_options))
            stdscr.refresh()

        def print_message(stdscr):
            _, w = stdscr.getmaxyx()
            if map:
                option, action = "parameters", "plotted"
            else:
                if args:
                    if args.select_key:
                        action = "included"
                    elif args.filter_key:
                        action = "excluded"
                option = "keys"

            message = [
                "***************************************************",
                f"         Select the {option} that must be {action}     ",
                f"   using the {ARROW_UP} and {ARROW_DOWN} , then press 'Enter'.        ",
                "   After making selection, choose 'Quit' to finish. ",
                "***************************************************",
            ]
            y = 2
            for idx, line in enumerate(message):
                x = w // 2 - len(line) // 2
                stdscr.addstr(y + idx, x, line, curses.color_pair(1))
            stdscr.refresh()

        print_message(stdscr)
        print_options(stdscr, current_row)
        print_selected_options(stdscr)

        while True:
            key = stdscr.getch()
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(options) - 1:
                current_row += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                selected_key = options[current_row]
                if selected_key != "Quit" and selected_key not in selected_options:
                    selected_options.append(selected_key)
                    stdscr.addstr(len(options) + 2, 0, f"'{selected_key}' is selected")
                    stdscr.refresh()
                    stdscr.getch()
                    stdscr.addstr(len(options) + 2, 0, " " * (len(selected_key) + 16))
                    print_selected_options(stdscr)
                elif selected_key == "Quit":
                    break
            print_options(stdscr, current_row)

    curses.wrapper(screen)
    if not selected_options:
        sys.exit(-1)
    return selected_options


def split_indx(indexes):
    result = []
    for x in indexes.split(","):
        x = x.strip()
        if "." in x:  # check if x is a float
            raise ValueError(f"\nFloat detected in filter range: '{x}'")
        result.append(int(x))
    return result
