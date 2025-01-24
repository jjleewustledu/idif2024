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

from __future__ import absolute_import
from copy import deepcopy
import unittest
import os
from pprint import pprint

import nibabel as nib
from dynesty import dynesty, utils as dyutils
import numpy as np
from testPreliminaries import TestPreliminaries 
from BoxcarContext import BoxcarContext
from IOImplementations import BoxcarIO
from BoxcarData import BoxcarData
from BoxcarSolver import BoxcarSolver
from DynestyPlotting import DynestyPlotting


class TestBoxcar(TestPreliminaries):

    def setUp(self):
        petdir = os.path.join(os.getenv("HOME"), "PycharmProjects", "dynesty", "idif2024", "data", "ses-20210421150523", "pet")
        self.input_func_fqfn = os.path.join(petdir, "sub-108293_ses-20210421150523_trc-oo_proc-MipIdif_idif.nii.gz")
        self.truths = [
            10.2470, 29.5557, 14.4955,
            0.7034, 7.9721, 1.2702, -1.8154, -1.3315, 196.1650,
            0.1356, 0.0074, 0.2352, 
            2.4554,
            0.0100]
        self.data_dict = {
            "input_func_fqfn": self.input_func_fqfn,
            "tag": "custom-tag-from-setUp"
        }

    def test_something(self):
        self.assertEqual(True, True)  # add assertion here

    def test_ctor(self):
        context = BoxcarContext(self.data_dict)
        # print("\n")
        # pprint(context)
        self.assertIsInstance(context.io, BoxcarIO)
        self.assertIsInstance(context.data, BoxcarData)
        self.assertIsInstance(context.solver, BoxcarSolver)
        self.assertIsInstance(context.plotting, DynestyPlotting)

    def test_io(self):
        context = BoxcarContext(self.data_dict)        
        # print("\n")
        # pprint(context.io.fqfp)
        # pprint(context.io.results_fqfp)
        niid = context.io.nii_load(self.data_dict["input_func_fqfn"])
        self.assertIn(niid["fqfp"], self.input_func_fqfn)
        self.assertEqual(niid["halflife"], 122.2416)
        self.assertEqual(niid["img"].shape, (32,))
        self.assertIsInstance(niid["json"], dict)
        self.assertIsInstance(niid["nii"], nib.nifti1.Nifti1Image)
        self.assertEqual(niid["taus"].shape, (32,))
        self.assertEqual(niid["times"].shape, (32,))
        self.assertEqual(niid["timesMid"].shape, (32,))

        # context.data.print_concise(niid, "input_func NIfTI dict")
        """
        ======================= input_func NIfTI dict =======================
        {'fqfp': '/Users/jjlee/PycharmProjects/dynesty/idif2024/data/ses-20210421150523/pet/sub-108293_ses-20210421150523_trc-oo_proc-MipIdif_idif',
        'halflife': 122.2416,
        'img': '<array shape=(32,)>',
        'json': "<dict keys=['Modality', 'ImagingFrequency', 'Manufacturer', "
                "'ManufacturersModelName', 'PatientPosition', 'SoftwareVersions', "
                "'SeriesDescription', 'ProtocolName', 'ImageType', 'SeriesNumber', "
                "'AcquisitionTime', 'AcquisitionNumber', 'ImageComments', "
                "'Radiopharmaceutical', 'RadionuclidePositronFraction', "
                "'RadionuclideTotalDose', 'RadionuclideHalfLife', "
                "'DoseCalibrationFactor', 'ConvolutionKernel', 'Units', "
                "'DecayCorrection', 'ReconstructionMethod', 'SliceThickness', "
                "'ImageOrientationPatientDICOM', 'ConversionSoftware', "
                "'ConversionSoftwareVersion', 'lm_start0_BMC_LM_00_ac_mc', 'starts', "
                "'taus', 'timesMid', 'times']>",
        'nii': '<Nifti1Image>',
        'taus': '<array shape=(32,)>',
        'times': '<array shape=(32,)>',
        'timesMid': '<array shape=(32,)>'}
        ======================================================================
        """

    def test_data(self):
        context = BoxcarContext(self.data_dict)
        self.assertEqual(context.data.data_dict["halflife"], 122.2416)
        self.assertEqual(context.data.data_dict["input_func_fqfn"], self.input_func_fqfn)
        self.assertEqual(context.data.data_dict["rho"].shape, (32,))
        self.assertEqual(context.data.data_dict["tag"], "custom-tag-from-setUp")
        self.assertEqual(context.data.data_dict["taus"].shape, (32,))
        self.assertEqual(context.data.data_dict["times"].shape, (32,))
        self.assertEqual(context.data.data_dict["timesMid"].shape, (32,))
        
        # context.data.print_concise(context.data.data_dict, "context.data_dict")
        # context.data.print_data()
        """
        ========================= context.data_dict =========================
        {'halflife': 122.2416,
        'input_func_fqfn': '/Users/jjlee/PycharmProjects/dynesty/idif2024/data/ses-20210421150523/pet/sub-108293_ses-20210421150523_trc-oo_proc-MipIdif_idif.nii.gz',
        'nlive': 300,
        'rho': '<array shape=(32,)>',
        'rstate': Generator(PCG64) at 0x14882FA00,
        'sample': 'rslice',
        'sigma': 0.1,
        'tag': 'custom-tag-from-setUp',
        'taus': '<array shape=(32,)>',
        'times': '<array shape=(32,)>',
        'timesMid': '<array shape=(32,)>'}
        ======================================================================
        """

        ifm = context.data.input_func_measurement
        self.assertIn(ifm["fqfp"], self.input_func_fqfn)
        self.assertIsInstance(ifm["nii"], nib.nifti1.Nifti1Image)

    def test_solver(self):
        context = BoxcarContext(self.data_dict)
        res = context.solver.run_nested(print_progress=True)
        self.assertIsInstance(res, dyutils.Results)
        self.assertIs(res, context.solver.dynesty_results)
        
        qm, _, _ = context.solver.quantile(verbose=True)
        qm_expected = [ 
            1.02630760e+01,  2.75903261e+01,  1.69716793e+01,  6.65476908e-01,
            8.44111071e+00,  1.38995527e+00, -1.82413010e+00, -1.38948735e+00,
            3.08785180e+02,  1.09157707e-01,  4.54813424e-02,  2.65391466e-01,
            2.18509272e+00,  3.30312016e-02]
        np.testing.assert_allclose(qm, qm_expected, rtol=1e-4)
        
        # context.solver.results_save()
        # context.solver.results_plot()

    def test_solver_2(self):
        petdir2 = os.path.join(os.getenv("HOME"), "PycharmProjects", "dynesty", "idif2024", "data", "ses-20210421154248", "pet")
        input_func_fqfn2 = os.path.join(petdir2, "sub-108293_ses-20210421154248_trc-oo_proc-MipIdif_idif.nii.gz")
        data_dict2 = {
            "input_func_fqfn": input_func_fqfn2,
            "tag": "custom-tag-from-test-solver-2"
        }
        context = BoxcarContext(data_dict2)
        res = context.solver.run_nested(print_progress=True)
        self.assertIsInstance(res, dyutils.Results)
        self.assertIs(res, context.solver.dynesty_results)
        
        qm, _, _ = context.solver.quantile(verbose=True)
        qm_expected = [ 
            4.54640122e+00,  6.46147546e+00,  1.45195640e+01,  3.09892431e+00,
            3.57240214e+00,  2.68976936e+00, -1.23835124e+00, -1.88842400e+00,
            3.23358536e+02,  4.87485335e-01,  5.61298715e-02,  2.83563275e-01,
            2.46602518e+00,  4.98233343e-02]
        np.testing.assert_allclose(qm, qm_expected, rtol=1e-4)

if __name__ == '__main__':
    unittest.main()
