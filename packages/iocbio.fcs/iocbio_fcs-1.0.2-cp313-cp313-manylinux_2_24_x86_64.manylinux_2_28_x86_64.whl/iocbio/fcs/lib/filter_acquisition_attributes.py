#!/usr/bin/env python3
import os
import sys

from iocbio.fcs.lib.const import DATA_ACF_KEY, DATA_ENCODE, DEC_FCSPROTOCOL, GROUP_ACF
from iocbio.fcs.lib.utils import select_option


def filter_attr(args, file, protocol):
    if protocol == DEC_FCSPROTOCOL:
        raise Exception("\nFCS protocol does not support keys (speeds, angles, and ...)")

    command = f'{os.path.basename(sys.argv[0])} {" ".join(sys.argv[1:])}'

    # Update command
    if args.select_key and args.filter_key:
        raise Exception("\nSelecting keys and filtering keys cannot be used at the same time.")
    elif args.select_key:  # update command line for selected keys
        command = command.replace("--select-key", "--filtered-key").replace("-sk", "--filtered-key")
    elif args.filter_key:  # update command line for filtered keys
        command = command.replace("--filter-key", "--filtered-key").replace("-fk", "--filtered-key")

    acf_keys_data = file[f"/{GROUP_ACF}/{DATA_ACF_KEY}"]
    acf_keys = [i.decode(DATA_ENCODE) for i in acf_keys_data]
    filterout_keys = select_option(acf_keys, args=args)  # select keys to filter out
    if args.select_key:  # select keys to count in
        selected_key = [key for key in acf_keys if key not in filterout_keys]
        selected_key.remove("Quit")
        filterout_keys = selected_key
    print(f"{len(filterout_keys)} key(s) filtered from {len(acf_keys) - 1} keys:")
    if len(filterout_keys) == len(acf_keys) - 1:
        raise ValueError("\nAll keys are filtered")
    print("\n".join(filterout_keys))

    command += " " + " ".join(f'"{key}"' for key in filterout_keys)
    print(f"\n\nCopy and run: \n\n{command}")
    sys.exit(-1)
