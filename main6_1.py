# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import os
import sys
from pprint import pprint
from multiprocessing import Pool
import numpy as np

from Raichle1983Model import Raichle1983Model
from Mintun1984Model import Mintun1984Model
from Huang1980Model import Huang1980Model


def the_tag():
    # __file__ gives the relative path of the script
    file_path = __file__
    file_name = os.path.basename(file_path)
    tag, _ = os.path.splitext(file_name)
    return tag


def work(tidx, data: dict):
    """"""

    pprint(data)

    if "trc-ho" in data["pet_measurement"]:
        _tcm = Raichle1983Model(
            data["input_function"],
            data["pet_measurement"],
            truths=[0.014, 0.866, 0.013, 17.6, -8.6, 0.049],
            nlive=300,
            tag=the_tag())
    elif "trc-oo" in data["pet_measurement"]:
        _tcm = Mintun1984Model(
            data["input_function"],
            data["pet_measurement"],
            truths=[0.511, 0.245, 0.775, 5, -5, 0.029],
            nlive=300,
            tag=the_tag())
    elif "trc-fdg" in data["pet_measurement"]:
        _tcm = Huang1980Model(
            data["input_function"],
            data["pet_measurement"],
            truths=[0.069, 0.003, 0.002, 0.000, 12.468, -9.492, 0.020],
            nlive=300,
            tag=the_tag())
    else:
        raise RuntimeError(__name__ + ".work: data['pet_measurement'] -> " + data["pet_measurement"])

    _package = _tcm.run_nested_for_indexed_tac(tidx)
    _package["tcm"] = _tcm
    return _package


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # data objects for work

    input_func_kind = "twil"
    petdir = os.path.join(
        os.getenv("SINGULARITY_HOME"),
        "CCIR_01211", "derivatives", "sub-108293", "ses-20210421150523", "pet")
    pet = os.path.join(
        petdir,
        "sub-108293_ses-20210421150523_trc-oo_proc-delay0-BrainMoCo2-createNiftiMovingAvgFrames_timeAppend-4-"
        "ParcSchaeffer-reshape-to-schaeffer-schaeffer.nii.gz")

    trunc_idx = pet.find("proc-")
    prefix = pet[:trunc_idx]
    if "idif".lower() in input_func_kind.lower():
        input_func = (prefix +
                      "proc-MipIdif_idif_dynesty-Boxcar-ideal.nii.gz")
    elif ("twil".lower() in input_func_kind.lower() or
          "aif".lower() in input_func_kind.lower()):
        input_func = (prefix +
                      "proc-TwiliteKit-do-make-input-func-nomodel_inputfunc_dynesty-RadialArtery-ideal.nii.gz")
    else:
        raise RuntimeError(__name__ + ": input_func_kind -> " + input_func_kind)

    data = {
        "input_function": input_func,
        "pet_measurement": pet}
    tindices = list(range(30))  # parcs & segs in Nick Metcalf's Schaeffer parcellations

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

    packages[0]["tcm"].save_results(package1, tag=the_tag())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
