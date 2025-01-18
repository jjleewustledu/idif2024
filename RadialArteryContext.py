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

from DynestyContext import DynestyContext
from IOImplementations import RadialArteryIO
from RadialArteryData import RadialArteryData
from RadialArterySolver import RadialArterySolver
from InputFuncPlotting import InputFuncPlotting


class RadialArteryContext(DynestyContext):
    def __init__(self, data_dict: dict):
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
