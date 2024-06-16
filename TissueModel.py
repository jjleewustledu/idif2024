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

from PETModel import PETModel
from Boxcar import Boxcar
from RadialArtery import RadialArtery
from RadialArtery import kernel_fqfn
from TrivialArtery import TrivialArtery

# general & system functions
import os
import pickle
import sys
from abc import ABC
from copy import deepcopy

# basic numeric setup
import numpy as np

# plotting
from matplotlib import cm, pyplot as plt
from matplotlib import rcParams

# re-defining plotting defaults
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


class TissueModel(PETModel, ABC):
    """
    """

    def __init__(self,
                 input_function,
                 pet_measurement,
                 truths=None,
                 home=os.getcwd(),
                 sample="rslice",
                 nlive=1000,
                 recovery_coefficient=1.8509,
                 rstate=np.random.default_rng(916301),
                 time_last=None,
                 tag="",
                 delta_time=1):
        super().__init__(home=home,
                         sample=sample,
                         nlive=nlive,
                         rstate=rstate,
                         time_last=time_last,
                         tag=tag)
        self._input_function = input_function  # fqfn to be converted to dict by property
        self._pet_measurement = pet_measurement  # fqfn to be converted to dict by property
        self._truths_internal = truths

        # use adjusted_pet_measurement()
        apetm = self.adjusted_pet_measurement
        self.RHOS = apetm["img"] / np.max(apetm["img"])
        self.RHO = self.slice_parc(self.RHOS, 0)
        self.TAUS = apetm["taus"]
        self.TIMES_MID = apetm["timesMid"]

        # use adjusted_input_function()
        self.DELTA_TIME = np.round(delta_time)  # required by adjusted_input_function()
        inputf_timesMid = self.adjusted_input_function()["timesMid"]
        inputf_timesMidInterp = np.arange(0, apetm["timesMid"][-1], self.DELTA_TIME)
        self.INPUTF_INTERP = self.adjusted_input_function()["img"] / np.max(apetm["img"])
        self.INPUTF_INTERP = np.interp(inputf_timesMidInterp, inputf_timesMid, self.INPUTF_INTERP)

        self.ARTERY = None
        self.HALFLIFE = self.adjusted_input_function()["halflife"]
        self.RECOVERY_COEFFICIENT = recovery_coefficient

    @property
    def fqfp(self):
        return self.adjusted_pet_measurement["fqfp"]

    @property
    def fqfp_results(self):
        fqfp1 = self.fqfp + "-" + self.__class__.__name__ + self.ARTERY.__class__.__name__
        fqfp1 = fqfp1.replace("ParcSchaeffer-reshape-to-schaeffer-", "")
        fqfp1 = fqfp1.replace("ModelAndArtery", "")
        fqfp1 = fqfp1.replace("Model", "")
        fqfp1 = fqfp1.replace("Radial", "")
        return fqfp1

    @property
    def ndim(self):
        return len(self.labels)

    @property
    def adjusted_pet_measurement(self):
        if isinstance(self._pet_measurement, dict):
            return deepcopy(self._pet_measurement)

        assert os.path.isfile(self._pet_measurement), f"{self._pet_measurement} was not found."
        fqfn = self._pet_measurement
        if self.parse_isotope(fqfn) == "15O":
            self._pet_measurement = self.decay_uncorrect(self.load_nii(fqfn))
        else:
            self._pet_measurement = self.load_nii(fqfn)
        return deepcopy(self._pet_measurement)

    @property
    def truths(self):
        return self._truths_internal.copy()

    def adjusted_input_function(self):
        """input function read from filesystem, never updated during dynesty operations"""

        if isinstance(self._input_function, dict):
            return deepcopy(self._input_function)

        assert os.path.isfile(self._input_function), f"{self._input_function} was not found."
        fqfn = self._input_function

        if "MipIdif_idif" in fqfn:
            self.ARTERY = Boxcar(
                fqfn,
                truths=self.truths[:14],
                nlive=self.NLIVE,
                times_last=self.TIME_LAST)
        elif "TwiliteKit-do-make-input-func-nomodel" in fqfn:
            self.ARTERY = RadialArtery(
                fqfn,
                kernel_fqfn(fqfn),
                truths=self.truths[:14],
                nlive=self.NLIVE,
                times_last=self.TIME_LAST)
        elif "_proc-" in fqfn and "-aif" in fqfn:
            self.ARTERY = TrivialArtery(
                fqfn,
                times_last=self.TIME_LAST)
        else:
            raise RuntimeError(self.__class__.__name__ + ": does not yet support " + fqfn)

        niid = self.ARTERY.input_func_measurement
        if self.parse_isotope(fqfn) == "15O":
            niid = self.decay_uncorrect(niid)
        if isinstance(self.ARTERY, Boxcar):
            niid["img"] = self.RECOVERY_COEFFICIENT * niid["img"]

        # interpolate to timing domain of pet_measurements
        petm = self.adjusted_pet_measurement
        tMI = np.arange(0, round(petm["timesMid"][-1]), self.DELTA_TIME)
        niid["img"] = np.interp(tMI, niid["timesMid"], niid["img"])
        niid["timesMid"] = tMI
        self._input_function = niid
        return deepcopy(self._input_function)

    def data(self, v):
        rhoUsesBoxcar = self.TAUS[2] > self.TIMES_MID[2] - self.TIMES_MID[1]
        return deepcopy({
            "halflife": self.HALFLIFE,
            "rho": self.RHO, "rhos": self.RHOS, "timesMid": self.TIMES_MID, "taus": self.TAUS,
            "times": (self.TIMES_MID - self.TAUS / 2), "inputFuncInterp": self.INPUTF_INTERP,
            "v": v,
            "rhoUsesBoxcar": rhoUsesBoxcar,
            "delta_time": self.DELTA_TIME})

    @staticmethod
    def is_sequence(obj):
        """ a sequence cannot be multiplied by floating point """
        return isinstance(obj, (list, tuple, type(None)))

    def loglike(self, v):
        data = self.data(v)
        rho_pred, _, _, _ = self.signalmodel(data)  # has 4 returned objects compared to Artery.loglike()
        sigma = v[-1]
        residsq = (rho_pred - data["rho"]) ** 2 / sigma ** 2
        loglike = -0.5 * np.sum(residsq + np.log(2 * np.pi * sigma ** 2))

        if not np.isfinite(loglike):
            loglike = -1e300

        return loglike

    def pickle_results(self, res_dict: dict, tag=""):

        if tag:
            tag = "-" + tag
        fqfp1 = self.fqfp_results + tag

        with open(fqfp1 + "-res.pickle", 'wb') as f:
            pickle.dump(res_dict["res"], f, pickle.HIGHEST_PROTOCOL)

    def plot_truths(self, truths=None, parc_index=None, activity_units="Bq/cm^3"):
        if truths is None:
            truths = self.truths
        data = self.data(truths)
        rho_pred, t_pred, _, _ = self.signalmodel(data)

        petm = self.adjusted_pet_measurement
        t_petm = petm["timesMid"]
        if parc_index:
            petm_hat = petm["img"][parc_index]
        else:
            # evaluates mean of petm["img"] for spatial dimensions only
            selected_axes = tuple(np.arange(petm["img"].ndim - 1))
            petm_hat = np.median(petm["img"], axis=selected_axes)
        M0 = np.max(petm["img"])

        inputf = self.adjusted_input_function()
        t_inputf = inputf["timesMid"]
        inputf_hat = inputf["img"]
        I0 = M0 / np.max(inputf_hat)

        plt.figure(figsize=(12, 8))
        p1, = plt.plot(t_inputf, I0 * inputf_hat, color="black", linewidth=2, alpha=0.7,
                       label=f"input function x {I0:.3}")
        p2, = plt.plot(t_petm, petm_hat, color="black", marker="+", ls="none", alpha=0.9, markersize=16,
                       label=f"measured TAC, parcel {parc_index}")
        p3, = plt.plot(t_pred, M0 * rho_pred, marker="o", color="red", ls="none", alpha=0.8,
                       label=f"predicted TAC, parcel {parc_index}")
        width = np.max((np.max(t_petm), np.max(t_inputf)))
        plt.xlim((-0.1 * width, 1.1 * width))
        plt.xlabel("time of mid-frame (s)")
        plt.ylabel("activity (" + activity_units + ")")
        plt.legend(handles=[p1, p2, p3], loc="right", fontsize=12)
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
            rho, timesMid, _, _ = self.signalmodel(data)  # distinct from Artery.plot_variations()
            plt.plot(timesMid, rho, color=viridis(tidx))  # distinct from Artery.plot_variations()

        # plt.xlim([-0.1,])
        plt.xlabel("time of mid-frame (s)")
        plt.ylabel("activity (arbitrary)")

        # Add a colorbar to understand colors
        # First create a mappable object with the same colormap
        sm = plt.cm.ScalarMappable(cmap=viridis)
        sm.set_array(trange)
        plt.colorbar(sm, label="Varying " + self.labels[tindex])

        plt.tight_layout()

    def run_nested(self, checkpoint_file=None, print_progress=False, resume=False):
        """ default: checkpoint_file=self.fqfp+"_dynesty-ModelClass-yyyyMMddHHmmss.save") """

        res = []
        logz = []
        information = []
        qm = []
        ql = []
        qh = []
        rho_pred = []
        resid = []

        if self.RHOS.ndim == 1:
            self.RHO = self.RHOS
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
            _rho_pred, _, _, _ = self.signalmodel(self.data(_qm))
            rho_pred.append(_rho_pred)
            resid.append(np.sum(_rho_pred - tac) / np.sum(tac))
            package = {
                "res": res,
                "logz": np.array(logz),
                "information": np.array(information),
                "qm": np.array(qm),
                "ql": np.array(ql),
                "qh": np.array(qh),
                "rho_pred": np.array(rho_pred),
                "resid": np.array(resid)}

        elif self.RHOS.ndim == 2:
            for tidx, tac in enumerate(self.RHOS):
                self.RHO = tac
                _res = self.solver.run_nested_for_list(prior_tag=self.__class__.__name__,
                                                       ndim=self.ndim,
                                                       checkpoint_file=checkpoint_file,
                                                       print_progress=print_progress,
                                                       resume=resume)

                # if print_progress:
                self.plot_results(_res, tag=f"parc{tidx}", parc_index=tidx)

                res.append(_res)
                rd = _res.asdict()
                logz.append(rd["logz"][-1])
                information.append(rd["information"][-1])
                _qm, _ql, _qh = self.solver.quantile(_res)
                qm.append(_qm)
                ql.append(_ql)
                qh.append(_qh)
                _rho_pred, _, _, _ = self.signalmodel(self.data(_qm))
                rho_pred.append(_rho_pred)
                resid.append(np.sum(_rho_pred - tac) / np.sum(tac))
            package = {
                "res": res,
                "logz": np.array(logz),
                "information": np.array(information),
                "qm": np.vstack(qm),
                "ql": np.vstack(ql),
                "qh": np.vstack(qh),
                "rho_pred": np.vstack(rho_pred),
                "resid": np.array(resid)}

        else:
            raise RuntimeError(self.__class__.__name__ + ": self.RHOS.ndim -> " + self.RHOS.ndim)

        self.save_results(package, tag=self.TAG)
        return package

    # noinspection DuplicatedCode
    def run_nested_for_indexed_tac(self, tidx: int, checkpoint_file=None, print_progress=False, resume=False):
        self.RHO = self.RHOS[tidx]
        _res = self.solver.run_nested_for_list(
            prior_tag=self.__class__.__name__,
            ndim=self.ndim,
            checkpoint_file=checkpoint_file,
            print_progress=print_progress,
            resume=resume)

        # if print_progress:
        self.plot_results(_res, tag=f"parc{tidx}", parc_index=tidx)

        _rd = _res.asdict()
        _qm, _ql, _qh = self.solver.quantile(_res)
        _rho_pred, _, _, _ = self.signalmodel(self.data(_qm))
        _resid = np.sum(_rho_pred - self.RHO) / np.sum(self.RHO)
        package = {
            "res": _res,
            "logz": np.array(_rd["logz"][-1]),
            "information": np.array(_rd["information"][-1]),
            "qm": np.array(_qm),
            "ql": np.array(_ql),
            "qh": np.array(_qh),
            "rho_pred": np.array(_rho_pred),
            "resid": np.array(_resid)}
        return package

    # noinspection DuplicatedCode
    def save_results(self, res_dict: dict, tag=""):
        """  """

        if tag:
            tag = "-" + tag
        fqfp1 = self.fqfp_results + tag

        with open(fqfp1 + "-res.pickle", 'wb') as f:
            pickle.dump(res_dict["res"], f, pickle.HIGHEST_PROTOCOL)

        apetm = self.adjusted_pet_measurement
        M0 = np.max(apetm["img"])

        product = deepcopy(apetm)
        product["img"] = res_dict["logz"]
        self.save_nii(product, fqfp1 + "-logz.nii.gz")

        product = deepcopy(apetm)
        product["img"] = res_dict["information"]
        self.save_nii(product, fqfp1 + "-information.nii.gz")

        product = deepcopy(apetm)
        product["img"] = res_dict["qm"]
        self.save_nii(product, fqfp1 + "-qm.nii.gz")

        product = deepcopy(apetm)
        product["img"] = res_dict["ql"]
        self.save_nii(product, fqfp1 + "-ql.nii.gz")

        product = deepcopy(apetm)
        product["img"] = res_dict["qh"]
        self.save_nii(product, fqfp1 + "-qh.nii.gz")

        try:
            # historically prone to fail

            if not TissueModel.is_sequence(res_dict["rho_pred"]):
                product = deepcopy(apetm)
                product["img"] = M0 * res_dict["rho_pred"]
                self.save_nii(product, fqfp1 + "-rho-pred.nii.gz")

            if not TissueModel.is_sequence(res_dict["resid"]):
                product = deepcopy(apetm)
                product["img"] = res_dict["resid"]
                self.save_nii(product, fqfp1 + "-resid.nii.gz")

            if not TissueModel.is_sequence(res_dict["martinv1"]):
                product = deepcopy(apetm)
                product["img"] = res_dict["martinv1"]
                self.save_nii(product, fqfp1 + "-martinv1.nii.gz")
        except Exception as e:
            # catch any error to enable graceful exit while sequentially writing NIfTI files
            print(f"{TissueModel.save_results.__name__}: caught Exception {e}, but proceeding", file=sys.stderr)
