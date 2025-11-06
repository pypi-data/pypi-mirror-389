import csv
import h5py
import numpy as np
import os
from dataclasses import dataclass
from typing import Dict, Any, List
from xlwt import Workbook

from iocbio.fcs.lib.const import MEAN, UNIT, RES_TXT, STD, ANALYSIS_SUFF, FIT_SUFF
from iocbio.fcs.lib.utils import get_output_fname, output_suffix


ACF_KEY_GROUP = "acf keys"
ACF_PATH = "ACF file path"
DATA_ACF = "acf"
DATA_ACF_MODEL = "acf-model"
RESIDUAL = "residuals"
EXCL_ACF = "excluded acf data"
FIT_GROUP = "fit-results"
FIT_PROC = "fit procedure"
LINE_INDX = "line indexes (fit)"
RESULT_GROUP = "results"
RF = "reduction factor"


@dataclass
class Results:
    acf: np.ndarray  # Experimental ACF
    acf_model: np.ndarray  # ACF model (fitted data)
    line_indx: List[int]  # List of line indexes
    akid: Dict[str, List]  # ACF keys index dictionary (akid) > keys: speed, angle | values: ACF indexes
    prd: Dict[str, Dict]  # Parameter results dictionary (prd) > keys: parameter | values: results (mean, std, ...)
    resid: np.ndarray = None  # Standardized residuals
    ultranest_data: Dict[str, Any] = None  # Ultranest data (paramnames, samples, arviz, ...)

    def save_to_hdf5(self, group: h5py.Group, exclude_acf: int, reduction_factor: float, fit_procedure: str):
        # Create datasets
        group.create_dataset(DATA_ACF, data=self.acf)
        acf_model_dset = group.create_dataset(DATA_ACF_MODEL, data=self.acf_model)

        # Set attributes
        acf_model_dset.attrs[EXCL_ACF] = exclude_acf
        acf_model_dset.attrs[RF] = reduction_factor
        acf_model_dset.attrs[FIT_PROC] = fit_procedure

        # Save residuals
        if self.resid is None:
            # create an empty dataset
            group.create_dataset(RESIDUAL, shape=(0,), dtype=float)
        else:
            group.create_dataset(RESIDUAL, data=self.resid)

        # Save line indexes
        group.create_dataset(LINE_INDX, data=self.line_indx)

        # Save ACF keys
        acf_key_group = group.create_group(ACF_KEY_GROUP)
        for key, indexes in self.akid.items():
            acf_key_group.create_dataset(key, data=indexes)

        # Save parameter results
        result_group = group.create_group(RESULT_GROUP)
        for param, dictionary in self.prd.items():
            param_dset = result_group.create_dataset(param, data=dictionary[MEAN])
            for key in [MEAN, STD, UNIT, RES_TXT]:
                param_dset.attrs[key] = dictionary[key]

    @staticmethod
    def load_from_hdf5(group: h5py.Group, args) -> "Results":
        # Read "ACF" data used for fitting, "model ACF", and residuals
        acf = np.array(group[DATA_ACF])
        acf_model = np.array(group[DATA_ACF_MODEL])
        residual = np.array(group[RESIDUAL])
        if len(residual) == 0 and args.residuals:
            raise ValueError("Residuals were not saved: empty or missing data.")

        # Read line indexes
        line_indx = np.array(group[LINE_INDX])

        # Read ACF keys (speed, angle) and save ACF indexes in a dictionary (akid)
        # ACF keys index dictionary (akid) > keys: speed, angle | values: ACF index
        akid = {key: list(group[ACF_KEY_GROUP][key]) for key in group[ACF_KEY_GROUP]}

        # Read parameter results from HDF5 file and save them in a dictionary
        prd = {}  # parameter results dictionary (prd)
        result_group = group[RESULT_GROUP]
        for param in result_group:
            attrs = result_group[param].attrs
            prd[param] = {
                MEAN: attrs[MEAN],
                STD: attrs[STD],
                UNIT: attrs[UNIT],
                RES_TXT: attrs[RES_TXT],
            }

        return Results(acf=acf, acf_model=acf_model, line_indx=line_indx, akid=akid, prd=prd, resid=residual)


class ResultsList:
    def __init__(self, input_file: str, args: Any = None, fit_procedure: str = None, acf_file_path: str = None):
        self.input_file = input_file
        self.args = args
        self.fit_procedure = fit_procedure
        self.acf_file_path = acf_file_path
        self.sector_results: Dict[str, Results] = {}  # keys: sector | values: Results dataclass
        self.output: str = None  # Name of result file
        self.n_excl: int = None  # Number of excluded ACF data
        self.rf: float = None  # Reduction factor to reduce ACF points

        # Generate the output filename for saved results (append fit-results suffix in the case of fitting)
        if self.acf_file_path:  # when saved fit-file is used for plotting
            self.f_name = input_file
        else:
            base = input_file.replace(ANALYSIS_SUFF, "") if ANALYSIS_SUFF in input_file else input_file
            self.f_name = get_output_fname(base, self.args.output, suffix=FIT_SUFF)

    def save(self):
        with h5py.File(self.f_name, "w") as hdf:
            fit_group = hdf.create_group(FIT_GROUP)

            # Save ACF file path
            fit_group.attrs[ACF_PATH] = os.path.abspath(self.input_file)

            for sector_key, results in self.sector_results.items():
                sector_group = fit_group.create_group(sector_key)
                results.save_to_hdf5(
                    sector_group,
                    exclude_acf=self.args.exclude_acf,
                    reduction_factor=self.args.reduction_factor,
                    fit_procedure=self.fit_procedure,
                )

    def save_table(self):
        args = self.args

        if args.excel:  # save results as `xlsx` file
            wb = Workbook()
            sheet1 = wb.add_sheet("Sheet 1")
            sheet1.write(0, 0, "Sector")
            sheet1.write(0, 1, "Parameter")
            sheet1.write(0, 2, "Mean")
            sheet1.write(0, 3, "Std")
            sheet1.write(0, 4, "Unit")
            row = 0
            for sector in self.sectors:
                result_cls = self.get_result(sector)
                n_parameter = len(result_cls.prd.keys())  # number of parameters
                for i, (parameter, data) in enumerate(result_cls.prd.items()):
                    sheet1.write(i + 1 + row, 0, sector)  # local coordinate of sector center
                    sheet1.write(i + 1 + row, 1, parameter)  # parameter
                    sheet1.write(i + 1 + row, 2, data[MEAN])  # result (mean value)
                    sheet1.write(i + 1 + row, 3, data[STD])  # standard deviation errors of results
                    sheet1.write(i + 1 + row, 4, data[UNIT])  # unit
                row += n_parameter + 1
            wb.save(get_output_fname(self.f_name, args.output, output_suffix(args, "results"), ".xlsx"))

        if args.csv:  # save results as `CSV` file
            csv_file = get_output_fname(self.f_name, args.output, output_suffix(args, "results"), ".csv")
            with open(csv_file, "w", newline="") as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(["Sector", "Parameter", "Mean", "Std", "Unit"])
                for sector in self.sectors:
                    result_cls = self.get_result(sector)
                    for parameter, data in result_cls.prd.items():
                        csv_writer.writerow(
                            [
                                sector,  # local coordinate of sector center
                                parameter,  # parameter
                                data[MEAN],  # result (mean value)
                                data[STD],  # standard deviation errors of results
                                data[UNIT],  # Unit
                            ],
                        )

    @classmethod
    def load(rlc, input_file, args: Any, fit_file: h5py.File) -> "ResultsList":
        if FIT_GROUP not in fit_file:
            raise KeyError(f"\nHDF5 file does not contain '{FIT_GROUP}'")

        fit_group = fit_file[FIT_GROUP]
        acf_file_path = fit_group.attrs[ACF_PATH]
        instance = rlc(input_file=input_file, args=args, acf_file_path=acf_file_path)

        for sector_key in fit_group:
            sector_group = fit_group[sector_key]
            results = Results.load_from_hdf5(sector_group, args)
            instance.add_result(sector_key, results)

        # Use last sector to get shared attrs (assuming consistency)
        last_sector = next(reversed(fit_group))
        model_attrs = fit_group[last_sector][DATA_ACF_MODEL].attrs
        instance.n_excl = model_attrs.get(EXCL_ACF, 0)
        instance.rf = model_attrs.get(RF, 1.0)
        instance.fit_procedure = model_attrs.get(FIT_PROC, "unknown")

        return instance

    def add_result(self, sector_key: str, results: Results):
        self.sector_results[sector_key] = results

    def get_result(self, sector_key: str) -> Results:
        return self.sector_results[sector_key]

    @property
    def sectors(self) -> List[str]:
        return list(self.sector_results.keys())

    @property
    def parameter_names(self):
        return list(next(iter(self.sector_results.values())).prd.keys())

    @property
    def parameter_values(self):
        return {sector: res.prd for sector, res in self.sector_results.items()}

    @staticmethod
    def is_loadable(file):
        return FIT_GROUP in file
