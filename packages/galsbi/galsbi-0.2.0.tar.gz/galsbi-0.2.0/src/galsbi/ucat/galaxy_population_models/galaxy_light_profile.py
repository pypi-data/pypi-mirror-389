# Copyright (C) 2018 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created 2021
author: Tomasz Kacprzak
"""

from warnings import warn

import numpy as np
from scipy.stats import betaprime

##########################################################
#
#       Sampling sersic
#
##########################################################


def sample_sersic_berge(numgalaxies, int_mag, par):
    """
    Sample the Sersic index-distribution parametrized as described in (Berge et al.
    2013)

    :param numgalaxies: number of galaxies, i.e. number of samples
    :param int_mag: intrinsic, unmagnified magnitude of all galaxies
    :param par: ctx.parameters; part of ctx containing parameters
    :return: Sersic index
    """

    sersic_n = np.zeros(numgalaxies, dtype=par.catalog_precision)

    while np.any(sersic_n <= 0) or np.any(sersic_n > 10):
        index = np.where((int_mag < 20) & ((sersic_n <= 0) | (sersic_n > 10)))[0]

        if index.size > 0:
            sersic_n_temp = np.zeros_like(sersic_n[index])
            midpoint = index.size // 2
            rest = index.size % 2
            sersic_n_temp[:midpoint] = (
                np.exp(
                    np.random.normal(
                        par.sersic_n_mean_1_hi, par.sersic_n_sigma_1_hi, size=midpoint
                    )
                )
                + np.ones_like(midpoint) * par.sersic_n_offset
            )

            sersic_n_temp[midpoint:] = (
                np.exp(
                    np.random.normal(
                        par.sersic_n_mean_2_hi,
                        par.sersic_n_sigma_2_hi,
                        size=midpoint + rest,
                    )
                )
                + np.ones_like(midpoint + rest) * par.sersic_n_offset
            )

            sersic_n[index] = np.random.permutation(sersic_n_temp).copy()

        index = (int_mag >= 20) & ((sersic_n <= 0) | (sersic_n > 10))

        if np.any(index):
            sersic_n[index] = (
                np.exp(
                    np.random.normal(
                        par.sersic_n_mean_low,
                        par.sersic_n_sigma_low,
                        size=np.sum(index),
                    )
                )
                + np.ones_like(np.sum(index)) * par.sersic_n_offset
            )

    return sersic_n


def sample_sersic_betaprime(n_gal, mode, size, alpha=0, z=0.0, min_n=0.2, max_n=5.0):
    """
    Sample the Sersic index-distribution parametrized as described in (Moser et al.
    2024). The parameter mode corresponds to the mode of the distribution, the size
    parameter is responsible for the scatter (with larger size the distribution becomes
    tighter). The alpha parameter is responsible for the redshift dependence of the
    mode. This was first introduced in Fischbacher et al. 2024.

    :param n_gal: number of galaxies, i.e. number of samples
    :param mode: mode of the distribution
    :param size: size of the distribution (with larger size the distribution becomes
                tighter)
    :param alpha: redshift dependence of the mode
    :param z: redshift
    :param min_n: minimum Sersic index, raise exception if the sampled value is below
                  this value
    :param max_n: maximum Sersic index, raise exception if the sampled value is above
                  this value
    :return: Sersic index
    """
    sersic_n = np.zeros(n_gal)
    mode_z = mode * (1 + z) ** alpha
    betaprime_a = mode_z * (size + 1) + 1
    betaprime_b = size
    sersic_n[:] = betaprime.rvs(a=betaprime_a, b=betaprime_b, size=n_gal)
    n_iter_max = 10 * n_gal
    for _ in range(n_iter_max):
        mask = (sersic_n > max_n) | (sersic_n < min_n)
        if np.any(mask):
            if isinstance(betaprime_a, np.ndarray):
                a = betaprime_a[mask]
            else:
                a = betaprime_a
            sersic_n[mask] = betaprime.rvs(
                a=a, b=betaprime_b, size=np.count_nonzero(mask)
            )
        else:
            return sersic_n

    raise RuntimeError(
        "Failed to get valid sersic indices after"
        f" {n_iter_max} iterations for mode {mode} and alpha {alpha}"
    )


def sample_sersic_for_galaxy_type(n_gal, galaxy_type, app_mag, par, z=0.0):
    # Backward compability
    if par.sersic_sampling_method == "default":
        warn(
            DeprecationWarning(
                "sersic_sampling_method=default is deprecated, using berge instead"
            ),
            stacklevel=1,
        )
        par.sersic_sampling_method = "berge"

    if par.sersic_sampling_method == "berge":
        sersic_n = sample_sersic_berge(n_gal, app_mag, par).astype(
            par.catalog_precision
        )

    elif par.sersic_sampling_method == "blue_red_fixed":
        assert galaxy_type in [
            "blue",
            "red",
        ], f"sersic index for galaxy_type {galaxy_type} not implemented"

        sersic_n = np.full(
            n_gal,
            fill_value=getattr(par, f"sersic_index_{galaxy_type}"),
            dtype=par.catalog_precision,
        )

    elif par.sersic_sampling_method == "single":
        sersic_n = np.full(
            n_gal, fill_value=par.sersic_single_value, dtype=par.catalog_precision
        )

    elif par.sersic_sampling_method == "blue_red_betaprime":
        assert galaxy_type in [
            "blue",
            "red",
        ], f"sersic index for galaxy_type {galaxy_type} not implemented"

        sersic_n = sample_sersic_betaprime(
            n_gal=n_gal,
            mode=getattr(par, f"sersic_betaprime_{galaxy_type}_mode"),
            size=getattr(par, f"sersic_betaprime_{galaxy_type}_size"),
            alpha=getattr(par, f"sersic_betaprime_{galaxy_type}_mode_alpha"),
            z=z,
            min_n=par.sersic_n_min,
            max_n=par.sersic_n_max,
        )

    else:
        raise ValueError("unknown sersic_sampling_method {par.sersic_sampling_method}")

    return sersic_n.astype(par.catalog_precision)
