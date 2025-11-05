# Copyright (C) 2018 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created on Mar 6, 2018
author: Joerg Herbel
"""

import warnings

import numpy as np
import scipy.interpolate
import scipy.optimize
import scipy.special
import scipy.stats

warnings.filterwarnings("once")


class UCatNumGalError(ValueError):
    """
    Raised when more galaxies than allowed by the input parameters are sampled
    """


class UCatMZInterpError(ValueError):
    """
    Raised when lum_fct_m_max is too low for the given redshift range
    """


class Catalog:
    pass


def apply_pycosmo_distfun(dist_fun, z):
    z_unique, inv_ind = np.unique(z, return_inverse=True)
    dist = dist_fun(a=1 / (1 + z_unique))[inv_ind]  # Unit: Mpc
    return dist


def intp_z_m_cut(cosmo, mag_calc, par):
    """
    This function returns an interpolator which predicts the maximum absolute magnitude
    for a given redshift such that a galaxy will still fall below the limiting apparent
    magnitude in the reference band (par.gals_mag_max). To do this, we do a check for a
    number of grid points in redshift. The check consists of finding the template with
    the smallest ratio of flux in the ref-band at that redshift (apparent flux) and flux
    in the luminosity function band at redshift zero (absolute flux). We then compute
    the absolute magnitude a galaxy would need to have to still pass the cut assuming
    that its spectrum is given by only that one template which we found. This works
    because the mixing-in of other templates will only make the object brighter in the
    r-band at this redshift. See also docs/jupyter_notebooks/z_m_cut.ipynb.
    """

    def find_max_template_ind(z, n_templates):
        coeffs = np.eye(n_templates)

        m_lf = mag_calc(
            redshifts=np.zeros(n_templates),
            excess_b_v=np.zeros(n_templates),
            coeffs=coeffs,
            filter_names=[par.lum_fct_filter_band],
        )[par.lum_fct_filter_band]

        m_ref = mag_calc(
            redshifts=np.full(n_templates, z),
            excess_b_v=np.zeros(n_templates),
            coeffs=coeffs,
            filter_names=[par.reference_band],
        )[par.reference_band]

        ind = np.argmin(m_ref - m_lf)

        return ind

    def app_mag_ref(z, temp_i, m_abs, n_templates):
        coeff = np.zeros((1, n_templates))
        coeff[0, temp_i] = 1
        coeff[0, temp_i] = 10 ** (
            0.4
            * (
                mag_calc(
                    redshifts=np.zeros(1),
                    excess_b_v=np.zeros(1),
                    coeffs=coeff,
                    filter_names=[par.lum_fct_filter_band],
                )[par.lum_fct_filter_band][0]
                - m_abs
            )
        )
        coeff[0, temp_i] *= (1e-5 / cosmo.background.dist_lum_a(a=1 / (1 + z))) ** 2 / (
            1 + z
        )
        m = mag_calc(
            redshifts=np.atleast_1d(z),
            excess_b_v=np.zeros(1),
            coeffs=coeff,
            filter_names=[par.reference_band],
        )[par.reference_band]

        return m[0]

    n_templates = mag_calc.n_templates
    z_intp = [par.lum_fct_z_res]
    temp_ind = find_max_template_ind(z_intp[0], n_templates)
    abs_mag = [
        scipy.optimize.brentq(
            f=lambda m: app_mag_ref(z_intp[0], temp_ind, m, n_templates)
            - par.gals_mag_max,
            a=-100,
            b=par.gals_mag_max,
        )
    ]

    i_loop = 0
    while True:
        i_loop += 1
        try:
            z_ = z_intp[-1] + 0.02

            if z_ > par.lum_fct_z_max:
                break

            temp_ind = find_max_template_ind(z_, n_templates)
            abs_mag_ = scipy.optimize.brentq(
                f=lambda m,
                temp_ind=temp_ind,
                z_=z_,
                n_templates=n_templates: app_mag_ref(z_, temp_ind, m, n_templates)
                - par.gals_mag_max,
                a=-100,
                b=abs_mag[-1],
            )
            z_intp.append(z_)
            abs_mag.append(abs_mag_)
        except ValueError:
            break

    intp = scipy.interpolate.interp1d(
        x=z_intp,
        y=abs_mag,
        kind="cubic",
        bounds_error=False,
        fill_value=(abs_mag[0], abs_mag[-1]),
    )

    if np.any(intp(intp.x) > par.lum_fct_m_max):
        msg = (
            "par.lum_fct_m_max is too low according to z-m-interpolation,"
            " some galaxies may be missing\n"
            f"gals_mag_max={par.gals_mag_max:2.2f}"
            f" lum_fct_z_max={par.lum_fct_z_max:2.2f}"
            f" m_max_sample={np.max(intp(intp.x)):2.2f}"
            f" lum_fct_m_max={par.lum_fct_m_max:2.2f}"
        )
        if par.raise_z_m_interp_error:
            raise UCatMZInterpError(msg)
        else:
            warnings.warn(msg, stacklevel=1)

    return intp
