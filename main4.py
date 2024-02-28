# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import os
import sys
from pprint import pprint
from multiprocessing import Pool
import numpy as np

from Raichle1983ModelAndArtery import Raichle1983ModelAndArtery
from Mintun1984ModelAndArtery import Mintun1984ModelAndArtery
from Huang1980ModelAndArtery import Huang1980ModelAndArtery


def work(tidx, data: dict):
    """"""

    pprint(data)

    if "trc-ho" in data["pet_measurement"]:
        _tcm = Raichle1983ModelAndArtery(
            data["input_function"],
            data["pet_measurement"],
            truths=[
                13.8, 12.3, 53.9,
                0.668, 7.66, 1.96, -1.38, -0.023, 60.0,
                0.074, 0.027, 0.014,
                2.427,
                0.008,
                0.014, 0.866, 0.013, 17.6, -8.6, 0.049],
            nlive=100)
    elif "trc-oo" in data["pet_measurement"]:
        _tcm = Mintun1984ModelAndArtery(
            data["input_function"],
            data["pet_measurement"],
            nlive=100)
    elif "trc-fdg" in data["pet_measurement"]:
        _tcm = Huang1980ModelAndArtery(
            data["input_function"],
            data["pet_measurement"],
            nlive=100)
    else:
        raise RuntimeError(__name__ + ".work: data['pet_measurement'] -> " + data["pet_measurement"])

    _package = _tcm.run_nested_for_indexed_tac(tidx)
    _package["tcm"] = _tcm
    return _package


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # data objects for work

    # petdir = os.path.join(
    #     os.getenv("HOME"),
    #     "PycharmProjects", "dynesty", "idif2024", "data", "ses-20210421152358", "pet")
    # idif = os.path.join(petdir, "sub-108293_ses-20210421152358_trc-ho_proc-MipIdif_idif.nii.gz")
    # pet = os.path.join(
    #     petdir,
    #     "sub-108293_ses-20210421152358_trc-ho_proc-delay0-BrainMoCo2-createNiftiMovingAvgFrames"
    #     "-ParcSchaeffer-reshape-to-schaeffer-schaeffer.nii.gz")

    idif = sys.argv[1]
    pet = sys.argv[2]
    data = {
        "input_function": idif,
        "pet_measurement": pet}
    tindices = list(range(4))  # parcs & segs in Nick Metcalf's Schaeffer parcellations

    # do multi-processing

    with Pool() as p:
        packages = p.starmap(work, [(tidx, data) for tidx in tindices])

    # re-order and save packages

    ress = []
    logzs = []
    informations = []
    qms = []
    qls = []
    qhs = []
    rhos_pred = []
    resids = []

    for package in packages:
        tcm = package["tcm"]
        ress.append(package["res"])
        rd = package["res"].asdict()
        logzs.append(rd["logz"][-1])
        informations.append(rd["information"][-1])
        _qm, _ql, _qh = tcm.solver.quantile(package["res"])
        qms.append(_qm)
        qls.append(_ql)
        qhs.append(_qh)
        _rho_pred, _, _, _ = tcm.signalmodel(tcm.data(_qm))
        rhos_pred.append(_rho_pred)
        resids.append(np.sum(_rho_pred - tcm.RHO) / np.sum(tcm.RHO))

    package1 = {
        "res": ress,
        "logz": np.array(logzs),
        "information": np.array(informations),
        "qm": np.vstack(qms),
        "ql": np.vstack(qls),
        "qh": np.vstack(qhs),
        "rho_pred": np.vstack(rhos_pred),
        "resid": np.array(resids)}

    packages[0]["tcm"].save_results(package1, tag="main4")

# See PyCharm help at https://www.jetbrains.com/help/pycharm/