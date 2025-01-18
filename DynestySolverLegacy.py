# The MIT License (MIT)
#
# Copyright (c) 2024 - Present: John J. Lee.
# Copyright (c) 2017 - Present: Josh Speagle and contributors.
# Copyright (c) 2014 - 2017: Kyle Barbary and contributors.
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

# general & system functions
from __future__ import absolute_import
from __future__ import print_function
from abc import ABC
from functools import partial
import sys
from datetime import datetime

# basic numeric setup
import numpy as np

# dynesty
from dynesty import dynesty
from dynesty import utils as dyutils


class DynestySolverLegacy(ABC):

    def __init__(self,
                 model=None,
                 sample="rslice",
                 nlive=1000,
                 rstate=np.random.default_rng(916301),
                 tag=""):
        self.model = model
        self.sample = sample
        self.nlive = nlive
        self.rstate = rstate
        self.tag = tag

        # Set numpy error handling for numerical issues such as underflow/overflow/invalid
        np.seterr(under="ignore")
        np.seterr(over="ignore")
        np.seterr(invalid="ignore")

    def run_nested_for_list(self,
                            prior_tag=None,
                            ndim=None,
                            checkpoint_file=None,
                            print_progress=False,
                            resume=False):
        """ default: checkpoint_file=self.fqfp+"_dynesty-ModelClass-yyyyMMddHHmmss.save") """

        mdl = self.model

        if ndim is None:
            ndim = mdl.ndim

        if resume:
            sampler = dynesty.DynamicNestedSampler.restore(checkpoint_file)
        else:
            prior_transform_with_data = mdl.prior_transform()
            sampler = dynesty.DynamicNestedSampler(mdl.loglike, 
                                                   prior_transform_with_data, 
                                                   ndim,
                                                   sample=self.sample, 
                                                   nlive=self.nlive,
                                                   rstate=self.rstate)
        sampler.run_nested(checkpoint_file=checkpoint_file, print_progress=print_progress, resume=resume)
        # for posterior > evidence, use wt_kwargs={"pfrac": 1.0}
        res = sampler.results
        return res

    def quantile(self, res: dyutils.Results, verbose: bool = False) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        samples = res["samples"].T
        weights = res.importance_weights().T
        ql = np.zeros(len(samples))
        qm = np.zeros(len(samples))
        qh = np.zeros(len(samples))

        # Find max label length for alignment
        max_label_len = max(len(label) for label in self.model.labels)

        # print quantile results in tabular format
        for i, x in enumerate(samples):
            ql[i], qm[i], qh[i] = dyutils.quantile(x, [0.025, 0.5, 0.975], weights=weights)
            if verbose:
                qm_fmt = ".1f" if abs(qm[i]) >= 1000 else ".4f"
                ql_fmt = ".1f" if abs(ql[i]) >= 1000 else ".4f" 
                qh_fmt = ".1f" if abs(qh[i]) >= 1000 else ".4f"
                label_padded = f"{self.model.labels[i]:<{max_label_len}}"
                print(f"Parameter {label_padded}: {qm[i]:{qm_fmt}} [{ql[i]:{ql_fmt}}, {qh[i]:{qh_fmt}}]")
        return qm, ql, qh
