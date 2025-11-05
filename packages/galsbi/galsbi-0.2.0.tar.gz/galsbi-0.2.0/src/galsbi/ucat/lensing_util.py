# Copyright (c) 2017 ETH Zurich, Cosmology Research Group
"""
Created on Jul 2, 2021
@author: Tomasz Kacprzak
"""

import numpy as np


def sigma_to_fwhm(sigma):
    return sigma * 2 * np.sqrt(2.0 * np.log(2.0))


def fwhm_to_sigma(fwhm):
    return fwhm / (2 * np.sqrt(2.0 * np.log(2.0)))


def apply_reduced_shear_to_ellipticities(
    int_e1, int_e2, g1, g2, ellipticity_unit="distortion"
):
    """
    Applies reduced shear to the intrinsic ellipticities,
    if unit=='distortion', then following Bartelmann & Schneider 2001,
    https://arxiv.org/pdf/astro-ph/9912508.pdf. We use the ellipticity defined
    in eq. (4.4), which is sheared according to eq. (4.6), "by interchanging χ and χ(s)
    and replacing g by −g".
    if unit=='shear', then following ...

    :param int_e1: intrinsic ellipticity 1-component
    :param int_e2: intrinsic ellipticity 2-component
    :param kappa: kappa
    :param g1: reduced shear 1-component
    :param g2: reduced shear 2-component
    :return e1: sheared ellipticity 1-component
    :return e2: sheared ellipticity 2-component
    """

    # get complex reduced shear
    g = g1 + 1j * g2

    # compute complex intrinsic ellipticity
    int_e = int_e1 + 1j * int_e2

    if ellipticity_unit == "distortion":
        int_e_conj = np.conjugate(int_e)

        # compute complex sheared ellipticity (eq. (4.6) with χ and χ(s) interchanged
        # and g --> -g))
        e = (int_e + 2 * g + g**2 * int_e_conj) / (
            1 + np.absolute(g) ** 2 + 2 * np.real(g * int_e_conj)
        )

    elif ellipticity_unit == "shear":
        e = (int_e + g) / (1 + np.conjugate(g) * int_e)

    else:
        raise ValueError(f"shape unit {ellipticity_unit} not supported")

    return np.real(e), np.imag(e)


def apply_shear_to_ellipticities(
    int_e1, int_e2, kappa, gamma1, gamma2, ellipticity_unit="distortion"
):
    """
    Applies shear to the intrinsic ellipticities, following Bartelmann & Schneider 2001,
    https://arxiv.org/pdf/astro-ph/9912508.pdf. We use the ellipticity defined in eq.
    (4.4), which is sheared according to eq. (4.6), "by interchanging χ and χ(s) and
    replacing g by −g".

    :param int_e1: intrinsic ellipticity 1-component
    :param int_e2: intrinsic ellipticity 2-component
    :param kappa: kappa
    :param gamma1: shear 1-component
    :param gamma2: shear 2-component
    :return e1: sheared ellipticity 1-component
    :return e2: sheared ellipticity 2-component
    """

    # compute complex reduced shear
    g1, g2 = shear_to_reduced_shear(gamma1, gamma2, kappa)

    # add shear
    e1, e2 = apply_reduced_shear_to_ellipticities(
        int_e1, int_e2, g1, g2, ellipticity_unit=ellipticity_unit
    )

    return e1, e2


def shear_to_reduced_shear(gamma1, gamma2, kappa):
    """
    Calculate reduced shear
    https://arxiv.org/pdf/astro-ph/9407032.pdf1
    Eq 2.14
    """
    g = (gamma1 + 1j * gamma2) / (1 - kappa)

    return g.real, g.imag


def distortion_to_shear(e1, e2):
    """
    Convert shape in distortion units to shear units
    https://arxiv.org/abs/astro-ph/0107431
    eq 2-7, 2-8
    """
    e = e1 + 1j * e2
    g_abs = np.tanh(np.arctanh(np.abs(e)) / 2.0)
    g = g_abs * np.exp(1j * np.angle(e))
    return g.real, g.imag


def shear_to_distortion(g1, g2):
    """
    Convert shape in shear units to distortion units
    # https://arxiv.org/abs/astro-ph/0107431
    # eq 2-7, 2-8
    """
    g = g1 + 1j * g2
    e_abs = np.tanh(2 * np.arctanh(np.abs(g)))
    e = e_abs * np.exp(1j * np.angle(g))
    return e.real, e.imag


def distortion_to_moments(fwhm, e1, e2, xx_out=None, yy_out=None, xy_out=None):
    if xx_out is None:
        xx_out = np.zeros(len(fwhm), dtype=fwhm.dtype)
    if yy_out is None:
        yy_out = np.zeros(len(fwhm), dtype=fwhm.dtype)
    if xy_out is None:
        xy_out = np.zeros(len(fwhm), dtype=fwhm.dtype)

    r_sq = fwhm_to_sigma(fwhm) ** 2
    xx_out[:] = r_sq * (1 + e1)
    yy_out[:] = r_sq * (1 - e1)
    xy_out[:] = r_sq * e2

    return xx_out, yy_out, xy_out


def moments_to_distortion(xx, yy, xy, e1_out=None, e2_out=None, fwhm_out=None):
    if e1_out is None:
        e1_out = np.zeros(len(xx), dtype=xx.dtype)
    if e2_out is None:
        e2_out = np.zeros(len(xx), dtype=xx.dtype)
    if fwhm_out is None:
        fwhm_out = np.zeros(len(xx), dtype=xx.dtype)

    xx_yy_sum = xx + yy
    e1_out[:] = (xx - yy) / xx_yy_sum
    e2_out[:] = 2 * xy / xx_yy_sum
    fwhm_out[:] = sigma_to_fwhm(np.sqrt(xx_yy_sum / 2.0))
    return e1_out, e2_out, fwhm_out


def moments_to_shear(xx, yy, xy, e1_out=None, e2_out=None, fwhm_out=None):
    if e1_out is None:
        e1_out = np.zeros(len(xx), dtype=xx.dtype)
    if e2_out is None:
        e2_out = np.zeros(len(xx), dtype=xx.dtype)
    if fwhm_out is None:
        fwhm_out = np.zeros(len(xx), dtype=xx.dtype)

    zz = xx + yy + 2 * np.sqrt(xx * yy - xy**2)
    e1_out[:] = (xx - yy) / zz
    e2_out[:] = 2 * xy / zz
    fwhm_out[:] = sigma_to_fwhm(np.sqrt((xx + yy) / 2.0))

    return e1_out, e2_out, fwhm_out


def shear_to_moments(g1, g2, fwhm, xx_out=None, yy_out=None, xy_out=None):
    """
    Convert shape in shear unit to moments
    PhD Thesis Tomasz Kacprzak Eqn 2.13
    """

    if xx_out is None:
        xx_out = np.zeros(len(fwhm), dtype=fwhm.dtype)
    if xy_out is None:
        xy_out = np.zeros(len(fwhm), dtype=fwhm.dtype)
    if yy_out is None:
        yy_out = np.zeros(len(fwhm), dtype=fwhm.dtype)

    zz = 1 + g1**2 + g2**2
    # TODO: check if r2 should be a parameter
    r2 = 1
    xx_out[:] = r2 * (1 + g1**2 + g2**2 + 2 * g1) / zz
    yy_out[:] = r2 * (1 + g1**2 + g2**2 - 2 * g1) / zz
    xy_out[:] = r2 * (2 * g2) / zz
    return xx_out, yy_out, xy_out


def calculate_flux_magnification(kappa, gamma1, gamma2):
    # magnification in terms of flux, see Bartelmann & Schneider 2001,
    # https://arxiv.org/pdf/astro-ph/9912508.pdf, eq. (3.14)
    magnification_flux = 1 / ((1 - kappa) ** 2 - gamma1**2 - gamma2**2)
    return magnification_flux


def calculate_size_magnification(r, kappa):
    magnified_r = r / (1 - kappa)
    return magnified_r
