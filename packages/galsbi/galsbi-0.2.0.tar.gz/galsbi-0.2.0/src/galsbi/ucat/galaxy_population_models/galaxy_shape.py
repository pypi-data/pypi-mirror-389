# Copyright (C) 2018 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created 2021
author: Tomasz Kacprzak
"""

from warnings import warn

import numpy as np
from scipy.stats import beta

LOG_0_2539 = np.log(0.2539)


def distortion_to_shear(distortion_x):
    q_sq = (1 - distortion_x) / (1 + distortion_x)
    q = np.sqrt(q_sq)
    shear_x = (1 - q) / (1 + q)
    return shear_x


##########################################################
#
#        Sample galaxy ellipticities
#
##########################################################


def sample_ellipticities_gaussian(numgalaxies, e1_mean, e2_mean, e1_sigma, e2_sigma):
    """
    Sample Gaussian distributions for the intrinsic e1 and e2 while enforcing that
    e1**2 + e2**2 <= 1

    :param numgalaxies: number of galaxies, i.e. number of samples
    :param par: ctx.parameters; part of ctx containing parameters
    :return: e1 values
    :return: e2 values
    """

    gal_e1 = np.ones(numgalaxies)
    gal_e2 = np.ones(numgalaxies)

    while np.any(gal_e1**2 + gal_e2**2 >= 1.0):
        index = gal_e1**2 + gal_e2**2 >= 1.0

        if np.any(index):
            gal_e1[index] = np.random.normal(e1_mean, e1_sigma, size=np.sum(index))
            gal_e2[index] = np.random.normal(e2_mean, e2_sigma, size=np.sum(index))

    return gal_e1, gal_e2


def pe_disc(ngal, log_a=LOG_0_2539, emax=0.8, emin=0.0256, pow_alpha=1):
    """
    From miller2013.
    """

    e_distortion = np.linspace(0, 1, 100000)
    e_shear = distortion_to_shear(e_distortion)
    pe = (
        (e_shear**pow_alpha)
        * (1 - np.exp((e_shear - emax) / np.exp(log_a)))
        / (1.0 + e_shear)
        / np.sqrt(e_shear**2 + emin**2)
    )
    pe[e_shear > 1] = 0
    pe[pe < 0] = 0
    pe = pe / np.sum(pe)
    pep = np.random.choice(a=e_distortion, size=ngal, p=pe)
    ea = pep * np.exp(1j * np.random.uniform(0.0, 2 * np.pi, len(pep)))
    e1, e2 = ea.real, ea.imag
    return e1, e2


def pe_bulge(ngal, b=2.368, c=6.691):
    """
    From miller2013.
    """

    e_distortion = np.linspace(0, 1, 100000)
    e_shear = distortion_to_shear(e_distortion)
    pe = e_shear * np.exp(-b * e_shear - c * e_shear**2)
    pe[e_shear > 1] = 0
    pe[pe < 0] = 0
    pe = pe / np.sum(pe)
    pep = np.random.choice(a=e_distortion, size=ngal, p=pe)
    ea = pep * np.exp(1j * np.random.uniform(0.0, 2 * np.pi, len(pep)))
    e1, e2 = ea.real, ea.imag
    return e1, e2


def sample_ellipticities_beta(n_gal, par):
    grid_e = np.linspace(0, 1, 100000)
    beta_a = par.ell_beta_ab_sum * (par.ell_beta_ab_ratio)
    beta_b = par.ell_beta_ab_sum * (1 - par.ell_beta_ab_ratio)
    rv = beta(beta_a, beta_b)
    pe = (grid_e / par.ell_beta_emax) ** 0.2 * rv.pdf(grid_e / par.ell_beta_emax)
    pe[~np.isfinite(pe)] = 0
    pe = pe / np.sum(pe)
    pep = np.random.choice(a=grid_e, size=n_gal, p=pe)
    ea = pep * np.exp(1j * np.random.uniform(0.0, 2 * np.pi, len(pep)))
    e1, e2 = ea.real, ea.imag
    return e1, e2


def sample_ellipticities_beta_mode(
    n_gal, ell_beta_ab_sum, ell_beta_mode, ell_beta_emax
):
    beta_a = ell_beta_ab_sum * ell_beta_mode - 2 * ell_beta_mode + 1
    beta_b = ell_beta_ab_sum - beta_a
    pep = beta.rvs(beta_a, beta_b, scale=ell_beta_emax, size=n_gal)
    ea = pep * np.exp(1j * np.random.uniform(0.0, 2 * np.pi, len(pep)))
    e1, e2 = ea.real, ea.imag
    return e1, e2


def sample_ellipticities_for_galaxy_type(n_gal, galaxy_type, par):
    backwards_compatibility(par)

    if par.ellipticity_sampling_method == "gaussian":
        int_e1, int_e2 = sample_ellipticities_gaussian(
            numgalaxies=n_gal,
            e1_mean=par.e1_mean,
            e2_mean=par.e2_mean,
            e1_sigma=par.e1_sigma,
            e2_sigma=par.e2_sigma,
        )

    elif par.ellipticity_sampling_method == "gaussian_blue_red":
        int_e1, int_e2 = sample_ellipticities_gaussian(
            numgalaxies=n_gal,
            e1_mean=getattr(par, f"e1_mean_{galaxy_type}"),
            e2_mean=getattr(par, f"e2_mean_{galaxy_type}"),
            e1_sigma=getattr(par, f"ell_sigma_{galaxy_type}"),
            e2_sigma=getattr(par, f"ell_sigma_{galaxy_type}"),
        )

    elif par.ellipticity_sampling_method == "blue_red_miller2013":
        if galaxy_type == "blue":
            int_e1, int_e2 = pe_disc(
                ngal=n_gal,
                log_a=par.ell_disc_log_a,
                emin=par.ell_disc_min_e,
                pow_alpha=par.ell_disc_pow_alpha,
            )

        elif galaxy_type == "red":
            int_e1, int_e2 = pe_bulge(ngal=n_gal, b=par.ell_bulge_b)

        else:
            raise ValueError(
                f"galaxy type {galaxy_type} not supported for"
                " par.ellipticity_sampling_method=blue_red_miller2013"
            )

    elif par.ellipticity_sampling_method == "beta_ratio":
        int_e1, int_e2 = sample_ellipticities_beta(n_gal=n_gal, par=par)

    elif par.ellipticity_sampling_method == "beta_mode":
        int_e1, int_e2 = sample_ellipticities_beta_mode(
            n_gal=n_gal,
            ell_beta_ab_sum=par.ell_beta_ab_sum,
            ell_beta_mode=par.ell_beta_mode,
            ell_beta_emax=par.ell_beta_emax,
        )

    elif par.ellipticity_sampling_method == "beta_mode_red_blue":
        int_e1, int_e2 = sample_ellipticities_beta_mode(
            n_gal=n_gal,
            ell_beta_ab_sum=getattr(par, f"ell_beta_ab_sum_{galaxy_type}"),
            ell_beta_mode=getattr(par, f"ell_beta_mode_{galaxy_type}"),
            ell_beta_emax=par.ell_beta_emax,
        )

    else:
        raise ValueError(
            f"unknown ellipticity_sampling_method {par.ellipticity_sampling_method}"
        )

    return int_e1, int_e2


def backwards_compatibility(par):
    if par.ellipticity_sampling_method == "default":
        warn(
            DeprecationWarning(
                "ellipticity_sampling_method=default is deprecated, "
                "using gaussian instead"
            ),
            stacklevel=1,
        )
        par.ellipticity_sampling_method = "gaussian"

    if par.ellipticity_sampling_method == "blue_red":
        warn(
            DeprecationWarning(
                "ellipticity_sampling_method=blue_red is deprecated, "
                "using gaussian_blue_red instead"
            ),
            stacklevel=1,
        )
        par.ellipticity_sampling_method = "gaussian_blue_red"

    if par.ellipticity_sampling_method == "beta_function":
        warn(
            DeprecationWarning(
                "ellipticity_sampling_method=beta_function is deprecated, "
                "using beta_ratio instead"
            ),
            stacklevel=1,
        )
        par.ellipticity_sampling_method = "beta_ratio"

    if par.ellipticity_sampling_method == "beta_function_mode":
        warn(
            DeprecationWarning(
                "ellipticity_sampling_method=beta_function_mode is deprecated, "
                "using beta_mode instead"
            ),
            stacklevel=1,
        )
        par.ellipticity_sampling_method = "beta_mode"

    if par.ellipticity_sampling_method == "beta_function_mode_red_blue":
        warn(
            DeprecationWarning(
                "ellipticity_sampling_method=beta_function_mode_red_blue is "
                "deprecated, using beta_mode_red_blue instead"
            ),
            stacklevel=1,
        )
        par.ellipticity_sampling_method = "beta_mode_red_blue"
