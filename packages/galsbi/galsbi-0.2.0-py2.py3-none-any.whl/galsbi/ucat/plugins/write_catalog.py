# Copyright (C) 2019 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created on Aug 2021
author: Tomasz Kacprzak
"""

import h5py
import numpy as np
from cosmic_toolbox import arraytools as at
from cosmic_toolbox import logger
from ivy.plugin.base_plugin import BasePlugin

LOGGER = logger.get_logger(__file__)


def catalog_to_rec(catalog):
    # get dtype first
    dtype_list = []
    for col_name in catalog.columns:
        col = getattr(catalog, col_name)
        n_obj = len(col)
        if len(col.shape) == 1 or col.shape[1] == 1:
            dtype_list += [(col_name, col.dtype)]
        else:
            dtype_list += [(col_name, col.dtype, col.shape[1:])]

    # create empty array
    rec = np.empty(n_obj, dtype=np.dtype(dtype_list))

    # copy columns to array
    for col_name in catalog.columns:
        col = getattr(catalog, col_name)
        if len(col.shape) == 1:
            rec[col_name] = col
        elif col.shape[1] == 1:
            rec[col_name] = col.ravel()
        else:
            rec[col_name] = col

    return rec


def sed_catalog_to_rec(catalog):
    """
    To save the SEDs, we don't need the full catalog, but only the ID, SED and redshift.
    The ID is necessary to link the SEDs to the galaxies in the photometric catalog.
    The redshift is necessary to adapt the wavelengths of the SEDs to the observed frame
    """
    columns = ["id", "sed", "z"]
    dtype_list = []
    for col in columns:
        arr = getattr(catalog, col)
        if len(arr.shape) == 1 or arr.shape[1] == 1:
            dtype_list.append((col, arr.dtype))
        else:
            dtype_list.append((col, arr.dtype, arr.shape[1:]))

    n_obj = len(getattr(catalog, columns[0]))
    rec = np.empty(n_obj, dtype=np.dtype(dtype_list))
    for col in columns:
        arr = getattr(catalog, col)
        if len(arr.shape) == 1:
            rec[col] = arr
        elif arr.shape[1] == 1:
            rec[col] = arr.ravel()
        else:
            rec[col] = arr
    return rec


def save_sed(filepath_out, cat, restframe_wavelength_in_A):
    """
    Save the SEDs to a file.
    The SEDs are saved in the rest frame, so we need to adapt the wavelenghts to the
    observed frame.
    """
    with h5py.File(filepath_out, "w") as f:
        f.create_dataset("data", data=cat)
        f.create_dataset("restframe_wavelength_in_A", data=restframe_wavelength_in_A)


class Plugin(BasePlugin):
    def __call__(self):
        par = self.ctx.parameters

        if hasattr(self.ctx, "current_filter"):
            # if the current filter is set, use it
            # this is the case for the image generation
            f = self.ctx.current_filter
            save_seds_if_requested = f == par.reference_band
        else:
            save_seds_if_requested = True

        # write catalogs
        if "galaxies" in self.ctx:
            filepath_out = par.galaxy_catalog_name
            cat = catalog_to_rec(self.ctx.galaxies)

            cat = self.enrich_catalog(cat)
            at.write_to_hdf(filepath_out, cat)

        if "stars" in self.ctx:
            filepath_out = par.star_catalog_name
            cat = catalog_to_rec(self.ctx.stars)
            at.write_to_hdf(filepath_out, cat)

        if par.save_SEDs and save_seds_if_requested:
            filepath_out = par.galaxy_sed_catalog_name
            cat = sed_catalog_to_rec(self.ctx.galaxies)
            restframe_wavelength_in_A = self.ctx.restframe_wavelength_for_SED
            save_sed(filepath_out, cat, restframe_wavelength_in_A)

    def enrich_catalog(self, cat):
        par = self.ctx.parameters
        if par.enrich_catalog is False:
            LOGGER.debug("Enriching catalog is disabled.")
            return cat
        try:
            cat = at.add_cols(
                cat, ["e_abs"], data=np.sqrt(cat["e1"] ** 2 + cat["e2"] ** 2)
            )
        except (ValueError, KeyError) as e:
            LOGGER.debug(f"e_abs could not be calculated: {e}")
        # add noise levels
        try:
            cat = at.add_cols(
                cat, ["bkg_noise_amp"], data=np.ones(len(cat)) * par.bkg_noise_amp
            )
        except AttributeError as e:
            LOGGER.debug(f"bkg_noise_amp could not be calculated: {e}")

        try:
            if "ra" not in cat.dtype.names and "dec" not in cat.dtype.names:
                y = np.array(cat["y"], dtype=int)
                x = np.array(cat["x"], dtype=int)
                if hasattr(par.bkg_noise_std, "shape"):
                    cat = at.add_cols(
                        cat, ["bkg_noise_std"], data=par.bkg_noise_std[y, x]
                    )
                else:
                    cat = at.add_cols(cat, ["bkg_noise_std"], data=par.bkg_noise_std)
        except (ValueError, KeyError, AttributeError) as e:
            LOGGER.debug(f"bkg_noise_std could not be calculated: {e}")
        return cat

    def __str__(self):
        return "write ucat catalog to file"
