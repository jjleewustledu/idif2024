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


import os
import sys
import logging
import matplotlib

from DynestyContext import DynestyContext
from IOImplementations import RadialArteryIO
from RadialArteryData import RadialArteryData
from RadialArterySolver import RadialArterySolver
from InputFuncPlotting import InputFuncPlotting


class RadialArteryContext(DynestyContext):
    """Context class for analyzing radial artery input functions.

    This class provides the context for analyzing PET input functions from radial artery samples.
    It coordinates the data handling, solver, and I/O operations specific to radial artery analysis.

    Args:
        data_dict (dict): Dictionary containing input data including:
            - input_func_fqfn (str): Fully qualified filename for input function data
            - nlive (int): Number of live points for nested sampling

    Attributes:
        data (RadialArteryData): Data handler for radial artery analysis
        solver (RadialArterySolver): Solver implementing radial artery analysis
        io (RadialArteryIO): I/O handler for radial artery data
        plotting (InputFuncPlotting): Plotting utilities for input functions
        tag (str): Identifier tag for the analysis

    Example:
        >>> data = {"input_func_fqfn": "input.csv", "nlive": 1000}
        >>> context = RadialArteryContext(data)
        >>> context()  # Run the analysis
        >>> results = context.solver.results_load()

    Notes:
        Requires all incoming PET and input function data to be decay corrected.
    """
    def __call__(self) -> None:
        logging.basicConfig(
            filename=self.data.results_fqfp + ".log",
            filemode="w",
            format="%(name)s - %(levelname)s - %(message)s")        
        self.solver.run_nested(print_progress=False)
        self.solver.results_save()
        self.plotting.results_plot(do_save=True)

    def __init__(self, data_dict: dict) -> None:
        super().__init__()
        self._io = RadialArteryIO(self)
        self._data = RadialArteryData(self, data_dict)
        self._solver = RadialArterySolver(self)
        self._plotting = InputFuncPlotting(self)
               
    @property
    def data(self):
        return self._data
    
    @property
    def io(self):
        return self._io
        
    @property
    def solver(self):
        return self._solver
    
    @property
    def plotting(self):
        return self._plotting

    @property
    def tag(self):
        return self.data.tag
    
    @tag.setter
    def tag(self, tag):
        self._data.tag = tag


def fqfn2kernel(artery_fqfn: str):
    """
    :param artery_fqfn: The fully qualified file name for an artery.
    :return: The fully qualified file name for the corresponding kernel file.

    This method takes a fully qualified file name for an artery and returns the fully qualified file name for the corresponding kernel file. It uses the artery_fqfn parameter to determine
    * which kernel file to return based on the substring contained in the artery_fqfn.

    Example usage:
        artery_file = "/path/to/sub-108293_artery.nii.gz"
        kernel_file = fqfn2kernel(artery_file)
        print(kernel_file)  # /path/to/CCIR_01211/sourcedata/kernel_hct=46.8.nii.gz
    """
    sourcedata = os.path.join(os.getenv("HOME"), "PycharmProjects", "dynesty", "idif2025", "data", "kernels")
    if "sub-108293" in artery_fqfn:
        return os.path.join(sourcedata, "kernel_hct=46.8.nii.gz")
    if "sub-108237" in artery_fqfn:
        return os.path.join(sourcedata, "kernel_hct=43.9.nii.gz")
    if "sub-108254" in artery_fqfn:
        return os.path.join(sourcedata, "kernel_hct=37.9.nii.gz")
    if "sub-108250" in artery_fqfn:
        return os.path.join(sourcedata, "kernel_hct=42.8.nii.gz")
    if "sub-108284" in artery_fqfn:
        return os.path.join(sourcedata, "kernel_hct=39.7.nii.gz")
    if "sub-108306" in artery_fqfn:
        return os.path.join(sourcedata, "kernel_hct=41.1.nii.gz")

    # mean hct for females and males
    return os.path.join(sourcedata, "kernel_hct=44.5.nii.gz")        


if __name__ == "__main__":
    matplotlib.use('Agg')  # disable interactive plotting

    data_dict = {
        "input_func_fqfn": sys.argv[1],
        "kernel_fqfn": fqfn2kernel(sys.argv[1]),
        "nlive": int(sys.argv[2])
    }
    ra = RadialArteryContext(data_dict)
    ra()
