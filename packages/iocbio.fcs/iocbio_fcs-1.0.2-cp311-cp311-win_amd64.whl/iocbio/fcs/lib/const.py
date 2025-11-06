#!/usr/bin/env python3


# Basic Symbols and Characters
ALPHA = "\u03b1"
ARROW_DOWN = "\u2193"
ARROW_LEFT = "\u2190"
ARROW_RIGHT = "\u2192"
ARROW_UP = "\u2191"
DEGREE = "\u00b0"
DELTA = "\u0394"
MICRO = "\u03bc"

# Constants values
AVOGADRO_CONST = 6.02214076e23
PIXEL_TIME = 1e-6

# Correlation Mode
CORR_MODE = "same"

# Experiment Protocol
DATA_ENCODE = "utf-8"
DEC_FCSPROTOCOL = b"ConfocalFCS".decode(DATA_ENCODE)
DEC_RICSPROTOCOL = b"ConfocalRICS".decode(DATA_ENCODE)
EXP_FCSPROTOCOL = b"ConfocalFCS"
EXP_RICSPROTOCOL = b"ConfocalRICS"

# Figures Size
FIG_SIZE = (18, 11)
FIG_SIZE_COV = (10, 10)
FIG_SIZE_DCN = (24, 14)
FIG_SIZE_PAA = (18, 9)
FIG_SIZE_PRE_MAP = (12, 12)
FIG_SIZE_SAMPLES = (14, 10)
FIG_SIZE_SIGNAL = (20, 10)

# Fit Procedure
LEAST_SQUARES = "least squares"
ULTRANEST = "ultranest"

# HDF5 Attributes
ATTR_ACF_KEY = "acf key"
ATTR_ANGLE = "angle [degree]"
ATTR_ISX = "image size x [pixels]"
ATTR_ISY = "image size y [pixels]"
ATTR_LINETIME = "line time with flyback [second]"
ATTR_ORIGINDATA = "origin experimental data"
ATTR_PIXTIME = "pixel time [second]"
ATTR_PROTOCOL = "protocol"
ATTR_PSX = "pixelsizex [um]"
ATTR_PSY = "pixelsizey [um]"

# HDF5 Dataset
DATA_ACF_KEY = "acf key"
DATA_FILENAME = "filename"
DATA_SECTOR_COORD = "sector_coordinate"
DATA_SELECTED_RANGE = "selected_range"

# HDF5 Groups
GROUP_ACF = "ACF"
GROUP_AVG = "Averages"
GROUP_RICS = "ProtocolConfocalRICS/rics"

# Map Attributes
ASPECT_RATIO = 4
NSX = "number of sectors along x-axis"
NSY = "number of sectors along y-axis"
SSX = "size of sectors along x-axis"
SSY = "size of sectors along y-axis"

# Model for Fitting
THREE_DIM = "3D"
THREE_DIM_2COMP = "3D-2comp"
THREE_DIM_2COMP_PSF = "3D-2comp-psf"
THREE_DIM_2COMP_TRIP = "3D-2comp-trip"
THREE_DIM_2COMP_TRIP_PSF = "3D-2comp-trip-psf"
THREE_DIM_PSF = "3D-psf"
THREE_DIM_TRIP = "3D-trip"
THREE_DIM_TRIP_PSF = "3D-trip-psf"

# DCN Attributes
DCN_CONCENTRATION = f"concentration, model:{THREE_DIM}"
DCN_DIFFUSION = f"diffusion, model:{THREE_DIM}"

# Model for Output File Names
ANALYSIS_SUFF = "-analysis"
FIT_SUFF = "-fit-results"

# Parameter Unit
MICROMETER = f"{MICRO}m"
MICROSECOND = f"{MICRO}s"
UNIT_CONCENTRATION = "nM"
UNIT_DIFF = f"{MICRO}m\N{SUPERSCRIPT TWO}/s"
UNIT_LINE_TIME = "ms"
UNIT_PIXEL_TIME = "s"

# Results Attributes
MEAN = "mean"
RES_TXT = "result text"
STD = "std"
UNIT = "unit"

# Error structure
GLS, WLS, OLS = "GLS", "WLS", "OLS"
