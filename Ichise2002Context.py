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


import sys
import logging
import matplotlib

from TissueData import TissueData
from Ichise2002Solver import Ichise2002Solver
from TissueContext import TissueContext


class Ichise2002Context(TissueContext):
    """Context class for the implementation of Ichise's 2002 report.

    This class provides the context for analyzing PET data using Ichise's 2002 model.
    It coordinates the data handling, solver, and I/O operations specific to this model.

    Args:
        data_dict (dict): Dictionary containing input data including:
            - input_func_fqfn (str): Fully qualified filename for input function data
            - tissue_fqfn (str): Fully qualified filename for tissue data

    Attributes:
        data (TissueData): Data handler for the 2-tissue compartment model
        solver (Ichise2002Solver): Solver implementing the 2-tissue compartment model
        tag (str): Identifier tag for the analysis
        input_func_type (str): Type of input function used

    Example:
        >>> data = {"input_func_fqfn": "input.csv", "tissue_fqfn": "tissue.csv"}
        >>> context = Ichise2002Context(data)
        >>> context()  # Run the analysis
        >>> results = context.solver.results_load()

    Notes:
        Ichise M, Toyama H, Innis RB, Carson RE. 
        "Strategies to Improve Neuroreceptor Parameter Estimation by Linear Regression Analysis."
        Journal of Cerebral Blood Flow & Metabolism. 2002;22(10):1271-1281. doi:10.1097/01.WCB.0000038000.34930.4E

        Requires all incoming PET and input function data to be decay corrected."""

    def __call__(self) -> None:
        logging.basicConfig(
            filename=self.data.results_fqfp + ".log",
            filemode="w",
            format="%(name)s - %(levelname)s - %(message)s")
        self.solver.run_nested(print_progress=False)
        self.solver.results_save()

    def __init__(self, data_dict: dict):
        super().__init__(data_dict)
        self._data = TissueData(self, data_dict)
        self._solver = Ichise2002Solver(self)
        if "Ichise2002" not in self.tag:
            if self.tag:
                self.tag += "-Ichise2002"
            else:
                self.tag = "Ichise2002"

    @property
    def data(self):
        return self._data

    @property
    def input_func_type(self):
        return self.data.input_func_type

    @property
    def solver(self):
        return self._solver

    @property
    def tag(self):
        return self.data.tag

    @tag.setter
    def tag(self, tag):
        self._data.tag = tag


if __name__ == "__main__":
    matplotlib.use('Agg')  # disable interactive plotting

    data_dict = {
        "input_func_fqfn": sys.argv[1],
        "tissue_fqfn": sys.argv[2],
        "nlive": int(sys.argv[3])
    }
    ich = Ichise2002Context(data_dict)
    ich()
