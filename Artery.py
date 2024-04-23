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

from abc import ABC
from PETModel import PETModel
from dynesty import utils as dyutils

# general & system functions
import re
import os
from copy import deepcopy
import pickle

# basic numeric setup
import numpy as np
import pandas as pd

# plotting
from matplotlib import pyplot as plt
from matplotlib import cm

# re-defining plotting defaults
from matplotlib import rcParams

rcParams.update({"xtick.major.pad": "7.0"})
rcParams.update({"xtick.major.size": "7.5"})
rcParams.update({"xtick.major.width": "1.5"})
rcParams.update({"xtick.minor.pad": "7.0"})
rcParams.update({"xtick.minor.size": "3.5"})
rcParams.update({"xtick.minor.width": "1.0"})
rcParams.update({"ytick.major.pad": "7.0"})
rcParams.update({"ytick.major.size": "7.5"})
rcParams.update({"ytick.major.width": "1.5"})
rcParams.update({"ytick.minor.pad": "7.0"})
rcParams.update({"ytick.minor.size": "3.5"})
rcParams.update({"ytick.minor.width": "1.0"})
rcParams.update({"font.size": 30})


class Artery(PETModel, ABC):
    """
    Artery class for modeling arterial data in PET imaging.

    Args:
        input_func_measurement (str or dict): Path to input function measurement file or dictionary representing the input function measurement.
        tracer (str, optional): Tracer information. If not provided, it will be extracted from the input_func_measurement file name.
        truths (dict, optional): Dictionary representing the ground truth parameter values. If not provided, the internally stored truths will be used.
        home (str, optional): Home directory. Defaults to the current working directory.
        sample (str, optional): Sample type. Defaults to "rslice".
        nlive (int, optional): Number of live points for the nested sampling algorithm. Defaults to 1000.
        rstate (numpy.random.Generator, optional): Random state for reproducibility. Defaults to np.random.default_rng(916301).
        tag (str, optional): Tag for saving results. Defaults to "".

    Attributes:
        KERNEL (Any): Kernel attribute.
        __input_func_measurement (str or dict): Path to input function measurement file or dictionary representing the input function measurement.
        HALFLIFE (float): Halflife attribute.
        RHO (ndarray): Rho attribute.
        SIGMA (float): Sigma attribute.
        TAUS (ndarray): Taus attribute.
        TIMES_MID (ndarray): TimesMid attribute.
        tracer (str): Tracer attribute.
        _truths_internal (dict): Internal truths attribute.

    """
    def __init__(self,
                 input_func_measurement,
                 tracer=None,
                 truths=None,
                 home=os.getcwd(),
                 sample="rslice",
                 nlive=1000,
                 rstate=np.random.default_rng(916301),
                 times_last=None,
                 tag=""):
        super().__init__(home=home,
                         sample=sample,
                         nlive=nlive,
                         rstate=rstate,
                         time_last=times_last,
                         tag=tag)

        self._truths_internal = truths

        self.KERNEL = None
        self.__input_func_measurement = input_func_measurement  # set with fqfn
        ifm = self.input_func_measurement  # get dict conforming to nibabel
        self.HALFLIFE = ifm["halflife"]
        self.RHO = ifm["img"] / np.max(ifm["img"])
        self.SIGMA = 0.1
        self.TAUS = ifm["taus"]
        self.TIMES_MID = ifm["timesMid"]

        self.tracer = tracer
        if not self.tracer:
            regex = r"_trc-(.*?)_"
            matches = re.findall(regex, input_func_measurement)
            assert matches, "no tracer information in input_func_measurement"
            self.tracer = matches[0]
            print(f"{self.__class__.__name__}: found data for tracer {self.tracer}")

    @property
    def fqfp(self):
        return self.input_func_measurement["fqfp"]

    @property
    def fqfp_results(self):
        return self.fqfp + "-" + self.__class__.__name__

    @property
    def input_func_measurement(self):
        if isinstance(self.__input_func_measurement, dict):
            return deepcopy(self.__input_func_measurement)

        assert os.path.isfile(self.__input_func_measurement), f"{self.__input_func_measurement} was not found."
        fqfn = self.__input_func_measurement
        self.__input_func_measurement = self.load_nii(fqfn)
        return deepcopy(self.__input_func_measurement)

    @property
    def labels(self):
        return [
            r"$t_0$", r"$\tau_2$", r"$\tau_3$",
            r"$\alpha - 1$", r"$1/\beta$", r"$p$", r"$\delta p_2$", r"$\delta p_3$", r"$1/\gamma$",
            r"$f_2$", r"$f_3$", r"$f_{ss}$",
            r"$A$", r"$\sigma$"]

    @property
    def ndim(self):
        return len(self.labels)

    @property
    def truths(self):
        return self._truths_internal.copy()

    def data(self, v):
        return deepcopy({
            "halflife": self.HALFLIFE,
            "rho": self.RHO, "timesMid": self.TIMES_MID, "taus": self.TAUS, "times": (self.TIMES_MID - self.TAUS / 2),
            "kernel": self.KERNEL,
            "v": v})

    def loglike(self, v):
        data = self.data(v)
        rho_pred, _, _ = self.signalmodel(data)
        sigma = v[-1]
        residsq = (rho_pred - data["rho"]) ** 2 / sigma ** 2
        loglike = -0.5 * np.sum(residsq + np.log(2 * np.pi * sigma ** 2))

        if not np.isfinite(loglike):
            loglike = -1e300

        return loglike

    def plot_truths(self, truths=None, parc_index=None):
        if truths is None:
            truths = self.truths
        data = self.data(truths)
        rho_pred, rho_ideal, t_ideal = self.signalmodel(data)

        ifm = self.input_func_measurement
        tM = ifm["timesMid"]
        rho = ifm["img"]
        M0 = np.max(rho)

        plt.figure(figsize=(12, 8))
        plt.plot(tM, rho, color="black", marker="+",
                 ls="none", alpha=0.9, markersize=16)
        plt.plot(tM, M0 * rho_pred, marker="o", color="red", ls="none", alpha=0.8)
        plt.plot(t_ideal, M0 * rho_ideal, color="dodgerblue", linewidth=2, alpha=0.7)
        plt.xlim([-0.1, 1.1 * np.max(tM)])
        plt.xlabel("time of mid-frame (s)")
        plt.ylabel("activity (Bq/mL)")
        plt.tight_layout()

    def plot_variations(self, tindex=0, tmin=None, tmax=None, truths=None):
        if truths is None:
            truths = self.truths
        _truths = truths.copy()

        plt.figure(figsize=(12, 7.4))

        ncolors: int = 75
        viridis = cm.get_cmap("viridis", ncolors)
        dt = (tmax - tmin) / ncolors
        trange = np.arange(tmin, tmax, dt)
        for tidx, t in enumerate(trange):
            _truths[tindex] = t
            data = self.data(_truths)
            _, rho_ideal, t_ideal = self.signalmodel(data)
            plt.plot(t_ideal, rho_ideal, color=viridis(tidx))

        # plt.xlim([-0.1,])
        plt.xlabel("time of mid-frame (s)")
        plt.ylabel("activity (arbitrary)")

        # Add a colorbar to understand colors
        # First create a mappable object with the same colormap
        sm = plt.cm.ScalarMappable(cmap=viridis)
        sm.set_array(trange)
        plt.colorbar(sm, label="Varying " + self.labels[tindex])

        plt.tight_layout()

    def prior_transform(self):
        return {
            "co": Artery.prior_transform_co,
            "oc": Artery.prior_transform_co,
            "oo": Artery.prior_transform_oo
        }.get(self.tracer, Artery.prior_transform_default)

    def run_nested(self, checkpoint_file=None, print_progress=False, resume=False):
        """ conforms with behaviors and interfaces of TCModel.py """

        res = []
        logz = []
        information = []
        qm = []
        ql = []
        qh = []
        rho_pred = []
        resid = []
        tac = self.RHO

        _res = self.solver.run_nested_for_list(prior_tag=self.__class__.__name__,
                                               ndim=self.ndim,
                                               checkpoint_file=checkpoint_file,
                                               print_progress=print_progress,
                                               resume=resume)
        if print_progress:
            self.plot_results(_res)
        res.append(_res)
        rd = _res.asdict()
        logz.append(rd["logz"][-1])
        information.append(rd["information"][-1])
        _qm, _ql, _qh = self.solver.quantile(_res)
        qm.append(_qm)
        ql.append(_ql)
        qh.append(_qh)
        _rho_pred, _, _ = self.signalmodel(self.data(_qm))
        rho_pred.append(_rho_pred)
        resid.append(np.sum(_rho_pred - tac) / np.sum(tac))

        package = {"res": res,
                   "logz": np.array(logz),
                   "information": np.array(information),
                   "qm": np.squeeze(np.array(qm)),
                   "ql": np.squeeze(np.array(ql)),
                   "qh": np.squeeze(np.array(qh)),
                   "rho_pred": np.squeeze(np.array(rho_pred)),
                   "resid": np.array(resid)}

        self.save_results(package, tag=self.TAG)
        return package

    def save_results(self, res_dict: dict, tag=""):
        """ conforms with behaviors and interfaces of TCModel.py """

        if not tag:
            tag = self.TAG
        if tag:
            tag = "-" + tag
        fqfp1 = self.fqfp_results + tag

        ifm = self.input_func_measurement
        M0 = np.max(ifm["img"])

        product = deepcopy(ifm)
        product["img"] = res_dict["logz"]
        self.save_nii(product, fqfp1 + "-logz.nii.gz")

        product = deepcopy(ifm)
        product["img"] = res_dict["information"]
        self.save_nii(product, fqfp1 + "-information.nii.gz")

        product = deepcopy(ifm)
        product["img"] = res_dict["qm"]
        self.save_nii(product, fqfp1 + "-qm.nii.gz")

        product = deepcopy(ifm)
        product["img"] = res_dict["ql"]
        self.save_nii(product, fqfp1 + "-ql.nii.gz")

        product = deepcopy(ifm)
        product["img"] = res_dict["qh"]
        self.save_nii(product, fqfp1 + "-qh.nii.gz")

        product = deepcopy(ifm)
        product["img"] = M0 * res_dict["rho_pred"]
        self.save_nii(product, fqfp1 + "-rho-pred.nii.gz")

        product = deepcopy(ifm)
        product["img"] = res_dict["resid"]
        self.save_nii(product, fqfp1 + "-resid.nii.gz")

        with open(fqfp1 + "-res.pickle", 'wb') as f:
            pickle.dump(res_dict["res"], f, pickle.HIGHEST_PROTOCOL)

        # from save_results_legacy()

        fqfp = ifm["fqfp"]
        nii = ifm["nii"]
        timesMid = ifm["timesMid"]
        taus = ifm["taus"]
        data = self.data(res_dict["qm"])
        rho_signal, rho_ideal, timesUnif = self.signalmodel(data)

        self.save_nii(
            {"timesMid": timesMid, "taus": taus, "img": M0 * rho_signal, "nii": nii, "fqfp": fqfp},
            fqfp1 + "-signal.nii.gz")

        self.save_nii(
            {"times": timesUnif, "taus": np.ones(timesUnif.shape), "img": M0 * rho_ideal, "nii": nii, "fqfp": fqfp},
            fqfp1 + "-ideal.nii.gz")

        d_quantiles = {
            "label": self.labels,
            "qm": res_dict["qm"],
            "ql": res_dict["ql"],
            "qh": res_dict["qh"]}
        df = pd.DataFrame(d_quantiles)
        df.to_csv(fqfp1 + "-quantiles.csv")

    @staticmethod
    def prior_transform_co(u):
        v = u
        v[0] = u[0] * 60  # t_0
        v[1] = u[1] * 60  # \tau_2 ~ t_2 - t_0
        v[2] = u[2] * 60  # \tau_3 ~ t_3 - t_2
        v[3] = u[3] * 20  # \alpha - 1
        v[4] = u[4] * 30 + 1  # 1/\beta
        v[5] = u[5] * 9.75 + 0.25  # p
        v[6] = u[6] * 10 - 10  # \delta p_2 ~ p_2 - p
        v[7] = u[7] * 10 - 10  # \delta p_3 ~ p_3 - p_2
        v[8] = u[8] * 300 + 0.01  # 1/\gamma for s.s.
        v[9] = u[9] * 0.75 + 0.25  # f_2
        v[10] = u[10] * 0.75  # f_3
        v[11] = u[11] * 0.75  # f_{ss}
        v[12] = u[12] * 4 + 0.5  # A is amplitude adjustment
        v[13] = u[13] * Artery.sigma()  # sigma ~ fraction of M0
        return v

    @staticmethod
    def prior_transform_oo(u):
        v = u
        v[0] = u[0] * 60  # t_0
        v[1] = u[1] * 60  # \tau_2 ~ t_2 - t_0
        v[2] = u[2] * 60  # \tau_3 ~ t_3 - t_2
        v[3] = u[3] * 20  # \alpha - 1
        v[4] = u[4] * 30 + 1  # 1/\beta
        v[5] = u[5] * 9.75 + 0.25  # p
        v[6] = u[6] * 10 - 10  # \delta p_2 ~ p_2 - p
        v[7] = u[7] * 10 - 10  # \delta p_3 ~ p_3 - p_2
        v[8] = u[8] * 300 + 0.01  # 1/\gamma for s.s.
        v[9] = u[9] * 0.75 + 0.25  # f_2
        v[10] = u[10] * 0.5  # f_3
        v[11] = u[11] * 0.25  # f_{ss}
        v[12] = u[12] * 4 + 0.5  # A is amplitude adjustment
        v[13] = u[13] * Artery.sigma()  # sigma ~ fraction of M0
        return v

    @staticmethod
    def prior_transform_default(u):
        v = u
        v[0] = u[0] * 60  # t_0
        v[1] = u[1] * 60  # \tau_2 ~ t_2 - t_0
        v[2] = u[2] * 60  # \tau_3 ~ t_3 - t_2
        v[3] = u[3] * 20  # \alpha - 1
        v[4] = u[4] * 30 + 1  # 1/\beta
        v[5] = u[5] * 9.75 + 0.25  # p
        v[6] = u[6] * 10 - 10  # \delta p_2 ~ p_2 - p
        v[7] = u[7] * 10 - 10  # \delta p_3 ~ p_3 - p_2
        v[8] = u[8] * 300 + 0.01  # 1/\gamma for s.s.
        v[9] = u[9] * 0.5  # f_2
        v[10] = u[10] * 0.25  # f_3
        v[11] = u[11] * 0.25  # f_{ss}
        v[12] = u[12] * 4 + 0.5  # A is amplitude adjustment
        v[13] = u[13] * Artery.sigma()  # sigma ~ fraction of M0
        return v

    @staticmethod
    def sigma():
        return 0.1

    @staticmethod
    def solution_1bolus(t, t_0, a, b, p):
        """ generalized gamma distribution """

        t_ = np.array(t - t_0, dtype=complex)
        t_ = t_.clip(min=0)
        rho = np.power(t_, a) * np.exp(-np.power((b * t_), p))
        rho = np.real(rho)
        rho = rho.clip(min=0)
        rho = rho / np.max(rho)
        return rho

    @staticmethod
    def solution_2bolus(t, t_0, a, b, p, g, f_ss):
        """ generalized gamma distributions + rising exponential """
        f_1 = 1 - f_ss
        rho = (f_1 * Artery.solution_1bolus(t, t_0, a, b, p) +
               f_ss * Artery.solution_ss(t, t_0, g))
        return rho

    @staticmethod
    def solution_3bolus(t, t_0, tau_2, a, b, p, dp_2, g, f_2, f_ss):
        """ two sequential generalized gamma distributions + rising exponential """

        f_ss_ = f_ss * (1 - f_2)
        f_1_ = (1 - f_ss) * (1 - f_2)
        f_2_ = f_2
        rho = (f_1_ * Artery.solution_1bolus(t, t_0, a, b, p) +
               f_2_ * Artery.solution_1bolus(t, t_0 + tau_2, a, b, max(0.25, p + dp_2)) +
               f_ss_ * Artery.solution_ss(t, t_0, g))
        return rho

    @staticmethod
    def solution_4bolus(t, t_0, tau_2, tau_3, a, b, p, dp_2, dp_3, g, f_2, f_3, f_ss):
        """ three sequential generalized gamma distributions + rising exponential """

        f_ss_ = f_ss * (1 - f_2) * (1 - f_3)
        f_1_ = (1 - f_ss) * (1 - f_2) * (1 - f_3)
        f_2_ = f_2 * (1 - f_3)
        f_3_ = f_3
        rho = (f_1_ * Artery.solution_1bolus(t, t_0, a, b, p) +
               f_2_ * Artery.solution_1bolus(t, t_0 + tau_2, a, b, max(0.25, p + dp_2)) +
               f_3_ * Artery.solution_1bolus(t, t_0 + tau_2 + tau_3, a, b, max(0.25, p + dp_2 + dp_3)) +
               f_ss_ * Artery.solution_ss(t, t_0, g))
        return rho

    @staticmethod
    def solution_ss(t, t0, g):
        """ rising exponential coincident with first-appearing bolus """

        t_ = np.array(t - t0)
        rho = 1 - np.exp(-g * t_)
        rho = rho.clip(min=0)
        rho = rho / np.max(rho)
        return rho
