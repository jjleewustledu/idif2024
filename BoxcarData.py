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


from InputFuncData import InputFuncData


class BoxcarData(InputFuncData):
    """Class for handling boxcar input function data from PET imaging.

    This class extends InputFuncData to provide specialized handling of boxcar input functions,
    which are derived from image-derived input functions (IDIFs). It requires all incoming PET 
    data to be decay corrected.

    Args:
        context: The context object containing solver, data, and IO information.
        data_dict (dict, optional): Dictionary containing configuration and data. Defaults to {}.

    Attributes:
        Inherits all attributes from InputFuncData parent class.
    """
    
    """ input function data assumed to be decay-corrected, consistent with tomography """
    
    def __init__(self, context, data_dict: dict = {}):
        super().__init__(context, data_dict)
