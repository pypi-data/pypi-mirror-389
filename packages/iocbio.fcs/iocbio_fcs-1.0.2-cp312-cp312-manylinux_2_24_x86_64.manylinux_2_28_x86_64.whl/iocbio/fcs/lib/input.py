import h5py
import numpy as np
from dataclasses import dataclass
from functools import cached_property
from typing import List

from iocbio.fcs.lib.const import (
    EXP_RICSPROTOCOL,
    EXP_FCSPROTOCOL,
    DATA_ENCODE,
    PIXEL_TIME,
    DEC_FCSPROTOCOL,
    DEC_RICSPROTOCOL,
)


@dataclass
class DataContainer:
    group: h5py.File
    protocol: np.bytes_  # expected FCS or RICS
    pixel_time_raw: float  # raw value to be scaled

    @cached_property
    def decoded_protocol(self) -> str:
        if self.protocol == EXP_FCSPROTOCOL:
            return DEC_FCSPROTOCOL
        elif self.protocol == EXP_RICSPROTOCOL:
            return DEC_RICSPROTOCOL
        else:
            raise ValueError("\nUnsupported protocol (expected FCS or RICS)")

    @cached_property
    def confocal_type(self) -> str:
        return "Confocal_data" if self.decoded_protocol == DEC_FCSPROTOCOL else "Confocal"

    @cached_property
    def confocal_data_path(self) -> str:
        return f"ImageStream/{self.confocal_type}"

    @cached_property
    def filenames(self) -> List[str]:
        raw_filenames = self.group[f"{self.confocal_data_path}/filename"]
        return [name.decode(DATA_ENCODE) for name in raw_filenames]

    @cached_property
    def images_group(self) -> h5py.Group:
        return self.group[f"{self.confocal_data_path}/Images"]

    @cached_property
    def pixel_time(self) -> float:
        return self.pixel_time_raw * PIXEL_TIME


def analyze_input_file(input_file):
    file, group = h5py.File(input_file, "r"), None

    if "Configuration" in file:
        # Check if protocol channels are enabled and find the correct group
        if file["Configuration"].attrs.get("PROTOCOL_CHANNELS_Enable", False):
            for k in file.keys():
                if k.startswith("channel-"):
                    channel_protocol = file[f"/{k}/Configuration"].attrs.get("main_protocol_mode", None)
                    if channel_protocol in (EXP_FCSPROTOCOL, EXP_RICSPROTOCOL):
                        group, protocol = file[k], channel_protocol
                        break
        else:
            main_protocol_mode = file["Configuration"].attrs.get("main_protocol_mode", None)
            if main_protocol_mode in (EXP_FCSPROTOCOL, EXP_RICSPROTOCOL):
                group, protocol = file, main_protocol_mode
    else:
        raise Exception("\nThe configuration is not defined")

    # If the group is not found, exit with an error
    if group is None:
        raise Exception("\nThe group is not found")

    configuration = group["Configuration"]
    pixel_time_raw = configuration.attrs.get("CONFOCAL_PixelAcqusitionTime", None)
    if pixel_time_raw is None:
        raise Exception("\nCONFOCAL_PixelAcquisitionTime attribute not found in the file configuration.")

    return DataContainer(group=group, protocol=protocol, pixel_time_raw=pixel_time_raw)
