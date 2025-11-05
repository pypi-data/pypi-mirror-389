# Copyright (C) 2018 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created 2021
author: Tomasz Kacprzak
"""

from warnings import warn

import numpy as np


def apply_pycosmo_distfun(dist_fun, z):
    z_unique, inv_ind = np.unique(z, return_inverse=True)
    dist = dist_fun(a=1 / (1 + z_unique))[inv_ind]  # Unit: Mpc
    return dist


def r50_phys_to_ang(r50_phys, cosmo, z):
    """
    Convert physical size to angular size

    :param r50_phys: physical size of the galaxy in kpc
    :param cosmo: cosmological model
    :param z: redshift of the galaxy
    :return: angular size of the galaxy in arcsec
    """
    d_a = apply_pycosmo_distfun(cosmo.background.dist_ang_a, z)  # unit: Mpc
    r50_ang = r50_phys / (1e3 * d_a)  # unit: rad
    r50_ang = np.rad2deg(r50_ang) * 60**2  # unit: arcsec
    return r50_ang


##########################################################
#
#        Sampling galaxy size
#
##########################################################


def sample_r50_for_galaxy_type(z, abs_mag, cosmo, par, galaxy_type):
    """
    Sample the physical size of a galaxy given its absolute magnitude
    and redshift. The physical size is sampled from a log-normal
    distribution with a mean that depends on the absolute magnitude
    and redshift. The physical size is then converted to an angular
    size using the cosmological distance.

    :param z: redshift of the galaxy
    :param abs_mag: absolute magnitude of the galaxy
    :param cosmo: cosmological model
    :param par: ucat parameters
    :param galaxy_type: type of the galaxy (e.g. "red", "blue")
    :return: angular size of the galaxy in pixels, in arcsec and physical size in kpc
    """
    backwards_compatibility(par)

    # set defaults
    if not hasattr(par, "logr50_sampling_method"):
        par.logr50_sampling_method = "single"

    if par.logr50_sampling_method == "single":
        r50_phys = sample_r50_phys(
            abs_mag_shift=abs_mag - par.logr50_phys_M0,
            logr50_phys_std=par.logr50_phys_std,
            logr50_phys_mean_slope=par.logr50_phys_mean_slope,
            logr50_phys_mean_intcpt=par.logr50_phys_mean_intcpt,
            logr50_alpha=par.logr50_alpha,
            z=z,
        )

    elif par.logr50_sampling_method == "red_blue":
        r50_phys = sample_r50_phys(
            abs_mag_shift=abs_mag - par.logr50_phys_M0,
            logr50_phys_std=getattr(par, f"logr50_phys_std_{galaxy_type}"),
            logr50_phys_mean_slope=getattr(
                par, f"logr50_phys_mean_slope_{galaxy_type}"
            ),
            logr50_phys_mean_intcpt=getattr(
                par, f"logr50_phys_mean_intcpt_{galaxy_type}"
            ),
            logr50_alpha=getattr(par, f"logr50_alpha_{galaxy_type}"),
            z=z,
        )

    elif par.logr50_sampling_method == "sdss_fit":
        # this sampling is based on https://arxiv.org/abs/astro-ph/0301527
        sigma1 = getattr(par, f"logr50_sdss_fit_sigma1_{galaxy_type}")
        sigma2 = getattr(par, f"logr50_sdss_fit_sigma2_{galaxy_type}")
        M0 = getattr(par, f"logr50_sdss_fit_M0_{galaxy_type}")

        # Equation (16)
        std = sigma2 + ((sigma1 - sigma2) / (1 + 10 ** (-0.8 * (abs_mag - M0))))

        if galaxy_type == "red":
            # Equation (14)
            slope = -0.4 * par.logr50_sdss_fit_a_red
            intcp = par.logr50_sdss_fit_b_red
        elif galaxy_type == "blue":
            alpha = par.logr50_sdss_fit_alpha_blue
            beta = par.logr50_sdss_fit_beta_blue
            gamma = par.logr50_sdss_fit_gamma_blue
            # Equation (15)
            # (intcp is not a classic intercept, but we can reuse sample_r50_phys)
            slope = -0.4 * alpha
            intcp = (beta - alpha) * np.log10(1 + 10 ** (-0.4 * (abs_mag - M0))) + gamma
        else:
            raise ValueError(
                f"unsupported galaxy_type={galaxy_type} for"
                " logr50_sampling_method=sdss_fit"
            )

        r50_phys = sample_r50_phys(
            abs_mag_shift=abs_mag,
            logr50_phys_std=std,
            logr50_phys_mean_slope=slope,
            logr50_phys_mean_intcpt=intcp,
            logr50_alpha=getattr(par, f"logr50_alpha_{galaxy_type}"),
            z=z,
        )

    else:
        raise Exception(
            f"unsupported logr50_sampling_method={par.logr50_sampling_method}"
        )

    # convert physical size to observerd angular size
    r50_ang = r50_phys_to_ang(r50_phys, cosmo, z)

    r50_ang_pix = r50_ang.astype(par.catalog_precision) / par.pixscale
    r50_ang_arcsec = r50_ang.astype(par.catalog_precision)
    r50_phys = r50_phys.astype(par.catalog_precision)

    return r50_ang_pix, r50_ang_arcsec, r50_phys


def sample_r50_phys(
    abs_mag_shift,
    logr50_phys_std,
    logr50_phys_mean_slope,
    logr50_phys_mean_intcpt,
    logr50_alpha=0.0,
    z=0.0,
):
    r50_phys = np.random.normal(loc=0, scale=logr50_phys_std, size=len(abs_mag_shift))
    r50_phys += abs_mag_shift * logr50_phys_mean_slope + logr50_phys_mean_intcpt
    r50_phys = np.exp(r50_phys)  # unit: kpc
    r50_phys *= (1 + z) ** logr50_alpha

    return r50_phys


def backwards_compatibility(par):
    if hasattr(par, "sample_r50_model"):
        warn(
            DeprecationWarning(
                "sample_r50_model is deprecated, "
                "define logr50_phys_M0 or logr50_sdss_fit_M0 instead"
            ),
            stacklevel=1,
        )
        if par.sample_r50_model == "base":
            par.logr50_phys_M0 = 0.0
        elif par.sample_r50_model == "shift20":
            par.logr50_phys_M0 = -20.0
