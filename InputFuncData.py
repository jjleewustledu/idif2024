# The MIT License (MIT)
#
# Copyright (c) 2024 - Present: John J. Lee.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from copy import deepcopy

import numpy as np
from numpy.typing import NDArray

from DynestyData import DynestyData
from IOImplementations import BaseIO
from PETUtilities import PETUtilities


class InputFuncData(DynestyData):
    """Class for handling input function data from PET imaging.

    This class extends DynestyData to provide specialized handling of input functions,
    including decay correction, data interpolation, and measurement access. All input
    function data is assumed to be decay-corrected, consistent with tomography.

    Args:
        context: The context object containing solver, data, and IO information.
        data_dict (dict, optional): Dictionary containing configuration and data. Defaults to {}.

    Attributes:
        halflife (float): Radiotracer half-life in seconds.
        input_func_fqfn (str): Fully qualified filename for input function data.
        nlive (int): Number of live points for nested sampling.
        pfrac (float): Plasma fraction for input function.
        rho (NDArray): Normalized input function values.
        sigma (float): Measurement uncertainty.

    Example:
        >>> context = MyContext()
        >>> data = {"input_func_fqfn": "input.nii"}
        >>> input_data = InputFuncData(context, data)
        >>> halflife = input_data.halflife
    """

    """ input function data assumed to be decay-corrected, consistent with tomography """

    def __init__(self, context, data_dict: dict = {}):
        super().__init__(context, data_dict)

        assert "input_func_fqfn" in self.data_dict, "data_dict missing required key 'input_func_fqfn'"

        niid = self.nii_load(self.data_dict["input_func_fqfn"])
        self._data_dict["halflife"] = niid["halflife"]
        self._data_dict["rho"] = niid["img"] / np.max(niid["img"])
        self._data_dict["timesMid"] = niid["timesMid"]
        self._data_dict["taus"] = niid["taus"]
        self._data_dict["times"] = niid["times"]
        self._data_dict["sigma"] = 0.1

        if "sample" not in self._data_dict:
            self._data_dict["sample"] = "rslice"
        if "nlive" not in self._data_dict:
            self._data_dict["nlive"] = 300
        if "rstate" not in self._data_dict:
            self._data_dict["rstate"] = np.random.default_rng(916301)
        if "tag" not in self._data_dict:
            self._data_dict["tag"] = ""
        if "pfrac" not in self._data_dict:
            self._data_dict["pfrac"] = 1.0

    @property
    def input_func_fqfn(self) -> str:
        return self.data_dict["input_func_fqfn"]

    @property
    def input_func_measurement(self) -> dict:
        if hasattr(self, "__input_func_measurement"):
            return deepcopy(self.__input_func_measurement)

        self.__input_func_measurement = self.context.io.nii_load(self.input_func_fqfn)
        return deepcopy(self.__input_func_measurement)

    @property
    def halflife(self) -> float:
        return self.data_dict["halflife"]

    @property
    def nlive(self) -> int:
        return self.data_dict["nlive"]

    @property
    def pfrac(self) -> float:
        return self.data_dict["pfrac"]

    @property
    def rstate(self) -> np.random.Generator:
        return self.data_dict["rstate"]

    @property
    def sample(self) -> str:
        return self.data_dict["sample"]

    @property
    def rho(self) -> NDArray:
        return self.data_dict["rho"].copy()

    @property
    def sigma(self) -> float:
        return self.data_dict["sigma"]

    @property
    def tag(self) -> str:
        return self.data_dict["tag"]

    @tag.setter
    def tag(self, tag: str):
        self._data_dict["tag"] = tag

    @property
    def taus(self) -> NDArray:
        return self.data_dict["taus"].copy()

    @property
    def timesIdeal(self) -> NDArray:
        if hasattr(self, "__timesIdeal"):
            return deepcopy(self.__timesIdeal)

        self.__timesIdeal = PETUtilities.data2timesInterp(self.data_dict)
        return deepcopy(self.__timesIdeal)

    @property
    def timesMid(self) -> NDArray:
        return self.data_dict["timesMid"].copy()

    @staticmethod
    def decay_correct(
        fqfn: str,
        output_format: str = "fqfn"
    ) -> str:
        """ Decay corrects an input function.  Returns dict or fqfn. """

        niid = BaseIO().nii_load(fqfn)
        niid = PETUtilities.decay_correct(niid)

        if output_format == "fqfn":
            fqfn = niid["fqfp"] + "-decaycorr.nii.gz"
            BaseIO().nii_save(niid, fqfn)
            return fqfn
        elif output_format == "niid":
            niid["fqfp"] = niid["fqfp"] + "-decaycorr"
            return niid
        else:
            raise ValueError(f"Invalid output format: {output_format}")

    @staticmethod
    def nii_hstack(
        fqfn1: str,
        fqfn2: str,
        t_crossover: float | None = None,
        output_format: str = "fqfn"
    ) -> str:
        """ Horizontally stacks two nii input functions and saves the result. """

        niid1 = BaseIO().nii_load(fqfn1)
        niid2 = BaseIO().nii_load(fqfn2)

        niid = deepcopy(niid1)
        if not t_crossover:
            niid["img"] = np.hstack((niid1["img"], niid2["img"]))
            niid["timesMid"] = np.hstack((niid1["timesMid"], niid2["timesMid"]))
            niid["taus"] = np.hstack((niid1["taus"], niid2["taus"]))
            niid["times"] = np.hstack((niid1["times"], niid2["times"]))
            niid["json"]["timesMid"] = niid["timesMid"].tolist()
            niid["json"]["taus"] = niid["taus"].tolist()
            niid["json"]["times"] = niid["times"].tolist()
        else:
            idx_crossover = np.where(niid1["timesMid"] >= t_crossover)[0][0]
            niid["img"] = np.hstack((niid1["img"][:idx_crossover], niid2["img"][idx_crossover:]))
            niid["timesMid"] = np.hstack((niid1["timesMid"][:idx_crossover], niid2["timesMid"][idx_crossover:]))
            niid["taus"] = np.hstack((niid1["taus"][:idx_crossover], niid2["taus"][idx_crossover:]))
            niid["times"] = np.hstack((niid1["times"][:idx_crossover], niid2["times"][idx_crossover:]))
            niid["json"]["timesMid"] = niid["timesMid"].tolist()
            niid["json"]["taus"] = niid["taus"].tolist()
            niid["json"]["times"] = niid["times"].tolist()

        # Check for duplicates using vectorized operations
        times = niid["times"]
        timesMid = niid["timesMid"]
        if len(np.unique(times)) != len(times):
            raise ValueError("Duplicate entries found in times array")
        if len(np.unique(timesMid)) != len(timesMid):
            raise ValueError("Duplicate entries found in timesMid array")

        if output_format == "fqfn":
            fqfn = niid["fqfp"] + f"-nii-hstack-t{t_crossover}.nii.gz"
            BaseIO().nii_save(niid, fqfn)
            return fqfn
        elif output_format == "niid":
            niid["fqfp"] = niid["fqfp"] + f"-nii-hstack-t{t_crossover}"
            return niid
        else:
            raise ValueError(f"Invalid output format: {output_format}")
