# Copyright (C) 2018 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created on Sept 2021
author: Tomasz Kacprzak
Code author: Joerg Herbel
"""

from collections import OrderedDict

import numpy as np
from cosmic_toolbox import logger

from galsbi.ucat import sed_templates_util, spectrum_util
from galsbi.ucat.galaxy_population_models.galaxy_luminosity_function import (
    find_closest_ind,
)

LOGGER = logger.get_logger(__file__)

speed_of_light_c_in_micrometer_per_sec = 3 * 1e8 * 1e6

TEMPL_INTEGRALS_CACHE = OrderedDict()


def flux_to_AB_mag(flux):
    mag = -2.5 * np.log10(flux) - 48.6
    mag[np.isnan(mag)] = np.inf
    return mag


def AB_mag_to_flux(mag):
    return 10 ** ((mag + 48.6) / (-2.5))


class MagCalculatorDirect:
    """
    Computes galaxy magnitudes by integrating redshifted and reddened galaxy spectra
    which are given by a sum of five template spectra. See also
    docs/jupyter_notebooks/spectra_to_magnitudes.ipynb and
    docs/jupyter_notebooks/extinction.ipynb.

    We use the following units:

    - Wavelength: micrometer
    - SED: erg/s/m2/Å
    """

    def __init__(self, filters, sed_templates):
        self.filters = filters
        self.sed_templates = sed_templates
        self.extinction_spline = spectrum_util.spline_ext_coeff()
        self.n_templates = sed_templates["amp"].shape[0]

    def __call__(
        self, redshifts, excess_b_v, coeffs, filter_names, return_fluxes=False
    ):
        # check if iterable
        from collections.abc import Iterable

        if not isinstance(filter_names, Iterable):
            filter_names = [filter_names]

        n_obj = redshifts.size
        fluxes = {f: np.empty(n_obj) for f in filter_names}

        for i in LOGGER.progressbar(
            range(n_obj), desc="getting magnitudes", at_level="debug"
        ):
            lam_obs_in_micrometer = self.sed_templates["lam"] * (1 + redshifts[i])

            spec = spectrum_util.construct_reddened_spectrum(
                lam_obs=lam_obs_in_micrometer,
                templates_amp=self.sed_templates["amp"],  # in erg/s/m2/Å
                coeff=coeffs[i],
                excess_b_v=excess_b_v[i],
                extinction_spline=self.extinction_spline,
            )

            for f in filter_names:
                filt_amp = np.interp(
                    lam_obs_in_micrometer,
                    self.filters[f]["lam"],
                    self.filters[f]["amp"],
                )
                fluxes[f][i] = np.trapz(
                    lam_obs_in_micrometer * spec * filt_amp, x=lam_obs_in_micrometer
                ).item() / (
                    speed_of_light_c_in_micrometer_per_sec * self.filters[f]["integ"]
                )

        if return_fluxes:
            return fluxes

        else:
            mags = {}
            for f in filter_names:
                mags[f] = flux_to_AB_mag(fluxes[f])
                mags[f][np.isnan(mags[f])] = np.inf
                del fluxes[f]

            return mags


class MagCalculatorTable:
    """
    Computes galaxy magnitudes by looking up pre-computed values of the integrals of our
    template spectra as a function of redshift and extinction E(B-V). The integrals need
    to be pre-computed for every filter band separately, such that for every filter
    band, we have five (number of template spectra) 2-dim. tables of integrals with
    redshift on the one and E(B-V) on the other axis. See also
    docs/jupyter_notebooks/tabulate_template_integrals.ipynb and
    docs/jupyter_notebooks/extinction.ipynb.
    """

    def __init__(
        self,
        filter_names,
        filepath_sed_integrals,
        reload_cache=False,
        copy_to_cwd=False,
    ):
        # TODO: check if this cache helped at all and if it did, fix the memory leak
        """
        if reload_cache:
            for key in TEMPL_INTEGRALS_CACHE:
                del TEMPL_INTEGRALS_CACHE[key]
        sed_templates_util.load_sed_integrals(
            filepath_sed_integrals,
            filter_names,
            crop_negative=True,
            sed_templates=TEMPL_INTEGRALS_CACHE,
        )
        self.templates_int_table_dict = TEMPL_INTEGRALS_CACHE
        self.z_grid = TEMPL_INTEGRALS_CACHE.z_grid
        self.excess_b_v_grid = TEMPL_INTEGRALS_CACHE.excess_b_v_grid

        """
        self.templates_int_table_dict = sed_templates_util.load_sed_integrals(
            filepath_sed_integrals,
            filter_names,
            crop_negative=True,
            sed_templates=None,
            copy_to_cwd=copy_to_cwd,
        )
        self.z_grid = self.templates_int_table_dict.z_grid
        self.excess_b_v_grid = self.templates_int_table_dict.excess_b_v_grid

        self.n_templates = self.templates_int_table_dict.n_templates

    def __call__(
        self, redshifts, excess_b_v, coeffs, filter_names, return_fluxes=False
    ):
        # check if iterable
        from collections.abc import Iterable

        if not isinstance(filter_names, Iterable):
            filter_names = [filter_names]

        # find the values of redshift and extinction in the grid for all objects
        z_ind = find_closest_ind(self.z_grid, redshifts)
        excess_b_v_ind = find_closest_ind(self.excess_b_v_grid, excess_b_v)

        fluxes = {}

        for f in filter_names:
            templates_int_tables = self.templates_int_table_dict[f]
            fluxes[f] = np.zeros(redshifts.size, dtype=np.float64)

            # create fluxes from templates
            for i in range(coeffs.shape[1]):
                fluxes[f] += (
                    coeffs[:, i] * templates_int_tables[i][z_ind, excess_b_v_ind]
                )

        if return_fluxes:
            return fluxes
        else:
            # convert flux to AB mag
            magnitudes = {}
            for f in filter_names:
                magnitudes[f] = flux_to_AB_mag(fluxes[f])
                del fluxes[f]
        return magnitudes
