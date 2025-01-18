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
import os

import nibabel as nib
import numpy as np

from DynestyData import DynestyData
from PETUtilities import PETUtilities

class RadialArteryData(DynestyData):
    """ input function data assumed to be decay-corrected, consistent with tomography """
    
    def __init__(self, context, data_dict: dict = {}):
        super().__init__(context, data_dict)

        assert "input_func_fqfn" in self.data_dict, "data_dict missing required key 'input_func_fqfn'"
        assert "kernel_fqfn" in self.data_dict, "data_dict missing required key 'kernel_fqfn'"
     
        niid = self.context.io.load_nii(self.data_dict["input_func_fqfn"])
        self._data_dict["halflife"] = niid["halflife"]
        self._data_dict["rho"] = niid["img"] / np.max(niid["img"])
        self._data_dict["timesMid"] = niid["timesMid"]
        self._data_dict["taus"] = niid["taus"]
        self._data_dict["times"] = niid["times"]
        self._data_dict["sigma"] = 0.1
        self._data_dict["kernel"] = self.context.io.load_kernel(self.data_dict["kernel_fqfn"])["img"]   

        if "sample" not in self._data_dict:
            self._data_dict["sample"] = "rslice"
        if "nlive" not in self._data_dict:
            self._data_dict["nlive"] = 300
        if "rstate" not in self._data_dict:
            self._data_dict["rstate"] = np.random.default_rng(916301)
        if "tag" not in self._data_dict:
            self._data_dict["tag"] = ""

    @property
    def input_func_fqfn(self):
        return self.data_dict["input_func_fqfn"]

    @property
    def input_func_measurement(self):
        if hasattr(self, "__input_func_measurement"):
            return deepcopy(self.__input_func_measurement)

        self.__input_func_measurement = self.load_nii(self.input_func_fqfn)
        return deepcopy(self.__input_func_measurement)    

    @property
    def halflife(self):
        return self.data_dict["halflife"]

    @property
    def kernel(self):
        return self.data_dict["kernel"].copy()

    @property
    def kernel_fqfn(self):
        return self.data_dict["kernel_fqfn"]
    
    @property
    def nlive(self):
        return self.data_dict["nlive"]
    
    @property
    def rstate(self):
        return self.data_dict["rstate"]
    
    @property
    def sample(self):
        return self.data_dict["sample"]

    @property
    def rho(self):
        return self.data_dict["rho"].copy()

    @property
    def sigma(self):
        return self.data_dict["sigma"]

    @property
    def tag(self):
        return self.data_dict["tag"]
    
    @tag.setter
    def tag(self, tag):
        self.data_dict["tag"] = tag

    @property
    def timesIdeal(self):
        if hasattr(self, "__timesIdeal"):
            return deepcopy(self.__timesIdeal)
        
        self.__timesIdeal = PETUtilities.data2timesInterp(self.data_dict)
        return deepcopy(self.__timesIdeal)
