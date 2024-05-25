# This is a sample Python script.
import logging
# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import os
import sys
from pprint import pprint
from multiprocessing import Pool
import logging

import numpy as np

from Raichle1983Model import Raichle1983Model
from Mintun1984Model import Mintun1984Model
from TZ3108 import TZ3108


def the_tag(nlive: float, tag_model: str):
    """    """

    # __file__ gives the relative path of the script
    file_path = __file__
    file_name = os.path.basename(file_path)
    tag, _ = os.path.splitext(file_name)
    return f"{tag}-{nlive}-{tag_model}"


def work(tidx, data: dict):
    """    """

    pprint(data)
    _nlive = data["nlive"]
    _model = data["model"]
    _tag = the_tag(_nlive, _model)

    if "trc-tz3108" in data["pet_measurement"]:
        _tcm = TZ3108(
            data["input_function"],
            data["pet_measurement"],
            truths=[0.476, 0.094, 0.005, 0.0, 9.066, -43.959, 0.021],
            nlive=_nlive,
            tag=_tag,
            model=_model)
    else:
        return {}
        # raise RuntimeError(__name__ + ".work: data['pet_measurement'] -> " + data["pet_measurement"])

    _package = _tcm.run_nested_for_indexed_tac(tidx)
    _package["tcm"] = _tcm
    return _package


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # the_data objects for work

    input_func_kind = sys.argv[1]
    pet = sys.argv[2]
    try:
        Nparcels = int(sys.argv[3])
    except ValueError:
        sys.exit(1)
    try:
        Nlive = int(sys.argv[4])
    except ValueError:
        Nlive = 300
    try:
        model = sys.argv[5]
    except ValueError:
        model = "Ichise2002Model"

    fqfp, _ = os.path.splitext(pet)
    fqfp, _ = os.path.splitext(fqfp)
    logging.basicConfig(
        filename=fqfp + ".log",
        filemode="w",
        format="%(name)s - %(levelname)s - %(message)s")

    trunc_idx = pet.find("proc-")
    prefix = pet[:trunc_idx]
    if "idif".lower() in input_func_kind.lower():
        input_func = (prefix + "proc-MipIdif_idif_dynesty-Boxcar-ideal-plasma.nii.gz")
    elif ("twil".lower() in input_func_kind.lower() or
          "aif".lower() in input_func_kind.lower()):
        input_func = (prefix + "proc-plasma.nii.gz")
    else:
        raise RuntimeError(__name__ + ": input_func_kind -> " + input_func_kind)

    the_data = {
        "input_function": input_func,
        "pet_measurement": pet,
        "nlive": Nlive,
        "model": model}
    tindices = list(range(Nparcels))  # parcs & segs in Nick Metcalf's Schaeffer parcellations

    # do multi-processing

    with Pool() as p:
        packages = p.starmap(work, [(tidx, the_data) for tidx in tindices])

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
        try:
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
        except Exception as e:
            # catch any error to enable graceful exit with writing whatever results were incompletely obtained
            logging.exception(__name__ + ": error in tcm -> " + str(e), exc_info=True)

    package1 = {
        "res": ress,
        "logz": np.array(logzs),
        "information": np.array(informations),
        "qm": np.vstack(qms),
        "ql": np.vstack(qls),
        "qh": np.vstack(qhs),
        "rho_pred": np.vstack(rhos_pred),
        "resid": np.array(resids)}

    packages[0]["tcm"].save_results(package1, tag=the_tag(Nlive))

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
