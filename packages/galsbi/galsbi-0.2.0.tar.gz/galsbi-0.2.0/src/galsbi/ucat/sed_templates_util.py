# Copyright (C) 2018 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created Aug 2021
author: Tomasz Kacprzak
code from:
Joerg Herbel
# ucat/docs/jupyter_notebooks/tabulate_template_integrals.ipynb
"""

import itertools
import os
from collections import OrderedDict

import h5py

# See Fast calculation of magnitudes from spectra
# ucat/docs/jupyter_notebooks/tabulate_template_integrals.ipynb
import numpy as np
from cosmic_toolbox import file_utils, logger

LOGGER = logger.get_logger(__file__)


def get_redshift_extinction_grid(
    z_max, z_stepsize, excess_b_v_max, excess_b_v_stepsize
):
    # Redshift grid
    z_grid = np.arange(0, z_max + z_stepsize, step=z_stepsize)

    # E(B-V) grid
    excess_b_v_grid = np.arange(
        0, excess_b_v_max + excess_b_v_stepsize, excess_b_v_stepsize
    )

    ze_cross = np.array(list(itertools.product(z_grid, excess_b_v_grid)))

    z_cross = ze_cross[:, 0]
    excess_b_v_cross = ze_cross[:, 1]

    return z_grid, excess_b_v_grid, z_cross, excess_b_v_cross


def get_template_integrals(
    sed_templates, filters, filter_names=None, ids_templates=None, test=False
):
    if test:
        (
            z_grid,
            excess_b_v_grid,
            z_cross,
            excess_b_v_cross,
        ) = get_redshift_extinction_grid(
            z_stepsize=0.05, excess_b_v_max=0.4, excess_b_v_stepsize=0.05, z_max=7.462
        )
    else:  # pragma: no cover
        (
            z_grid,
            excess_b_v_grid,
            z_cross,
            excess_b_v_cross,
        ) = get_redshift_extinction_grid(
            z_stepsize=0.001, excess_b_v_max=0.4, excess_b_v_stepsize=0.001, z_max=7.462
        )

    coeffs = np.ones(len(z_cross))
    filter_names = filters.keys() if filter_names is None else filter_names
    ids_templates = (
        range(sed_templates["n_templates"]) if ids_templates is None else ids_templates
    )

    from galsbi.ucat.magnitude_calculator import MagCalculatorDirect

    sed_template_integrals = OrderedDict({f: {} for f in filter_names})

    for i, id_templ in enumerate(ids_templates):
        LOGGER.info(f"SED template id_templ={id_templ} {i + 1}/{len(ids_templates)}")
        sed_templates_current = OrderedDict(
            lam=sed_templates["lam"],
            amp=sed_templates["amp"][[id_templ]],
            n_templates=1,
        )
        mag_calc = MagCalculatorDirect(filters, sed_templates_current)
        fluxes = mag_calc(
            redshifts=z_cross,
            excess_b_v=excess_b_v_cross,
            filter_names=filter_names,
            coeffs=coeffs,
            return_fluxes=True,
        )

        for f in fluxes:
            flux_reshape = fluxes[f].reshape([len(z_grid), len(excess_b_v_grid)])
            sed_template_integrals[f][id_templ] = flux_reshape

    return sed_template_integrals, excess_b_v_grid, z_grid


def store_sed_integrals(filename, integrals, excess_b_v_grid, z_grid):
    # get absolute path
    filename = os.path.abspath(filename)
    d = os.path.dirname(filename)
    if not os.path.isdir(d):
        os.makedirs(d)
        LOGGER.info(f"made dir {d}")

    with h5py.File(filename, "w") as f:
        f["E(B-V)"] = excess_b_v_grid
        f["z"] = z_grid
        for b, templates in integrals.items():
            for t in templates:
                f[f"integrals/{b}/template_{t}"] = integrals[b][t]
    LOGGER.info(f"wrote {filename}")


def load_sed_integrals(
    filepath_sed_integ,
    filter_names=None,
    crop_negative=False,
    sed_templates=None,
    copy_to_cwd=False,
):
    """
    Loads SED integrals, uses cache.
    :param filepath_sed_integ: name of the file containing SED template integrals
    :param filter_names: list of filter name, should be in format Camera_band, but just
    band is also accepted to ensure backwards compatibility

    :param crop_negative: if to set all negative elements in the filter to zero
    :param sed_templates: OrderedDict containing a buffer for templates
    :param copy_to_cwd: copy the file to the current working directory
    """

    def filter_name_back_compatibility(filter_name, integrals):
        # backwards compatibility check
        if filter_name not in integrals:
            return filter_name.split("_")[-1]
        else:
            return filter_name

    if sed_templates is None:
        sed_templates = OrderedDict()

    filepath_sed_integ_local = os.path.join(
        os.getcwd(), os.path.basename(filepath_sed_integ)
    )

    # copy to local directory (local scratch) if not already there
    if copy_to_cwd and (not os.path.exists(filepath_sed_integ_local)):
        src = filepath_sed_integ
        file_utils.robust_copy(src, filepath_sed_integ_local)
        load_filename = filepath_sed_integ_local
    elif copy_to_cwd:
        load_filename = filepath_sed_integ_local
    else:
        load_filename = filepath_sed_integ

    with h5py.File(load_filename, mode="r") as f:
        for filter_name in filter_names:
            # only load if not already in buffer
            if filter_name not in sed_templates:
                # backwards compatibility check
                filter_name_use = filter_name_back_compatibility(
                    filter_name, f["integrals"]
                )
                sed_templates[filter_name_use] = []

                n_templ = len(f["integrals"][filter_name_use].keys())

                for i in range(n_templ):
                    int_templ = np.array(
                        f["integrals"][filter_name_use][f"template_{i}"]
                    )
                    if crop_negative:
                        np.clip(int_templ, a_min=0, a_max=None, out=int_templ)
                    sed_templates[filter_name_use] += [int_templ]
            else:
                LOGGER.debug(f"read {filter_name} from sed_templates cache")
        if not hasattr(sed_templates, "n_templates"):
            sed_templates.n_templates = len(f["integrals"][filter_name_use].keys())

        if not hasattr(sed_templates, "z_grid"):
            sed_templates.z_grid = np.array(f["z"])

        if not hasattr(sed_templates, "excess_b_v_grid"):
            sed_templates.excess_b_v_grid = np.array(f["E(B-V)"])
    return sed_templates


def load_template_spectra(filepath_sed_templates, lam_scale=1, amp_scale=1):
    with h5py.File(filepath_sed_templates, "r") as f:
        sed_templates_lam = np.array(f["wavelength"])
        sed_templates_amp = np.array(f["amplitudes"])
        LOGGER.info(f"using template set: {filepath_sed_templates}")
        for a in f["amplitudes"].attrs:
            LOGGER.info("templates {}:\n{}".format(a, f["amplitudes"].attrs[a]))

    sed_templates_lam *= lam_scale  # scale by the desired factor
    sed_templates_amp *= amp_scale  # scale by the desired factor
    sed_templates = OrderedDict(amp=sed_templates_amp, lam=sed_templates_lam)
    sed_templates.n_templates = sed_templates_amp.shape[0]
    return sed_templates
