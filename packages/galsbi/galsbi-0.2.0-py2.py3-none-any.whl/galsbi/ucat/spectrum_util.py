# Copyright (C) 2018 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created on Mar 6, 2018
author: Joerg Herbel
"""

import numpy as np
import scipy.interpolate


def spline_ext_coeff():
    """
    Perform the cubic spline interpolation described by
    Fitzpatrick (1999, DOI: 10.1086/316293) to obtain the extinction law in the optical
    and IR region (for wavelengths > 2700 Angstrom)

    :return: spline object than can be evaluated at arbitrary inverse wavelengths
    """
    spline_x = (0.0, 0.377, 0.820, 1.667, 1.828, 2.141, 2.433, 3.704, 3.846)
    spline_y = (0.0, 0.265, 0.829, 2.688, 3.055, 3.806, 4.315, 6.265, 6.591)
    spline = scipy.interpolate.InterpolatedUnivariateSpline(spline_x, spline_y, k=3)
    return spline


def extinction_coefficient(lam, excess_b_v, spline):
    """
    Calculate the extinction coefficient as described in
    Schlafly et. al. (2011, DOI: 10.1088/0004-637X/737/2/103). The extinction law is the
    one given by Fitzpatrick (1999, DOI: 10.1086/316293), the extinction map is the one
    presented in Schlegel et. al. (1998, DOI: 10.1086/305772).

    :param lam: Wavelength in micrometre
    :param excess_b_v: Excess E(B-V) in B-V color from the map provided by Schlegel et.
                       al. (1998, DOI: 10.1086/305772)
    :param spline: Cubic spline for the optical and IR-region according to Fitzpatrick
                   (1999, DOI: 10.1086/316293)
    :return: Extinction coefficient A_lambda evaluated at the input wavelengths.
    """

    def uv_extinction(x):
        """
        Extinction law for the UV-region (wavelengths < 2700 Angstrom) according to
        Fitzpatrick (1999, DOI: 10.1086/316293)

        :param x: Inverse wavelength in micrometre^-1
        :return: A_lambda/E(B-V) evaluated at input inverse wavelengthss
        """

        def uv_curvature(x):
            f = np.zeros_like(x)
            mask = x >= 5.9
            y = x[mask] - 5.9
            f[mask] = 0.5392 * y**2 + 0.05644 * y**3
            return f

        r_v = 3.1
        c_1 = 4.50777 - 14.184 / r_v
        c_2 = -0.824 + 4.717 / r_v
        c_3 = 3.23
        c_4 = 0.41
        gam = 0.99
        x_0 = 4.596

        x_sq = x**2

        k = (
            c_1
            + c_2 * x
            + c_3 * x_sq / ((x_sq - x_0**2) ** 2 + x_sq * gam**2)
            + c_4 * uv_curvature(x)
        )

        return k + r_v

    lam_inv = 1 / lam
    uv_mask = (
        lam_inv >= 1 / 0.27
    )  # UV region is defined as all wavelengths <= 2700 Angstrom

    ext_coeff = np.append(uv_extinction(lam_inv[uv_mask]), spline(lam_inv[~uv_mask]))[
        np.newaxis, ...
    ]
    ext_coeff = (
        ext_coeff * 0.78 * 1.32 * excess_b_v[..., np.newaxis] / spline(1)
    )  # See Schlafly et. al. (2011, DOI: 10.1088/0004-637X/737/2/103), eq. (A1)

    return ext_coeff


def construct_intrinsic_spectrum(coeff, templates_amp):
    """
    :param templates_amp: (n_templates, n_lambda)
    :param coeff: (n_gal, n_templates)
    :return: (n_gal, n_lambda)
    """
    specrum = np.sum(coeff[..., np.newaxis] * templates_amp[np.newaxis, ...], axis=1)
    return specrum


def apply_extinction(spectrum, lam_obs, excess_b_v, extinction_spline):
    """
    :param spectrum: (n_gal, n_lambda)
    :param lam_obs: (n_lambda,)
    :param excess_b_v: (n_gal,)
    :param extinction_spline:
    """
    spectrum *= 10 ** (
        -2 / 5 * extinction_coefficient(lam_obs, excess_b_v, extinction_spline)
    )


def construct_reddened_spectrum(
    lam_obs, templates_amp, coeff, excess_b_v, extinction_spline
):
    """
    :param lam_obs: (n_lambda, )
    :param templates_amp: (n_templates, n_lambda)
    :param coeff: (n_gal, n_templates)
    :param excess_b_v: (n_gal,)
    :param extinction_spline:
    :return: (n_gal, n_lambda)
    """
    spectrum = construct_intrinsic_spectrum(coeff, templates_amp)
    apply_extinction(spectrum, lam_obs, excess_b_v, extinction_spline)
    return spectrum
