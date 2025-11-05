# Copyright (C) 2018 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created on Sept 2021
author: Tomasz Kacprzak
using code from: Joerg Herbel
"""

from collections import OrderedDict

import numpy as np
import scipy.integrate
import scipy.optimize
import scipy.special
from cosmic_toolbox import logger

LOGGER = logger.get_logger(__file__)


def find_closest_ind(grid, vals):
    ind = np.searchsorted(grid, vals)
    ind[ind == grid.size] -= 1
    ind[np.fabs(grid[ind] - vals) > np.fabs(grid[ind - 1] - vals)] -= 1
    return ind


def initialize_luminosity_functions(par, pixarea, cosmo, z_m_intp=None):
    kw_lumfun = dict(
        pixarea=pixarea,
        z_res=par.lum_fct_z_res,
        m_res=par.lum_fct_m_res,
        z_max=par.lum_fct_z_max,
        m_max=par.lum_fct_m_max,
        z_m_intp=z_m_intp,
        ngal_multiplier=par.ngal_multiplier,
        cosmo=cosmo,
    )
    if par.ngal_multiplier != 1:
        LOGGER.warning(f"ngal_multiplier is set to {par.ngal_multiplier}")

    lum_funcs = OrderedDict()
    for i, g in enumerate(par.galaxy_types):
        lum_funcs[g] = LuminosityFunction(
            lum_fct_parametrization=par.lum_fct_parametrization,
            m_star_slope=getattr(par, f"lum_fct_m_star_{g}_slope"),
            m_star_intcpt=getattr(par, f"lum_fct_m_star_{g}_intcpt"),
            phi_star_amp=getattr(par, f"lum_fct_phi_star_{g}_amp"),
            phi_star_exp=getattr(par, f"lum_fct_phi_star_{g}_exp"),
            z_const=getattr(par, f"lum_fct_z_const_{g}"),
            alpha=getattr(par, f"lum_fct_alpha_{g}"),
            name=g,
            galaxy_type=i,
            seed_ngal=par.seed_ngal,
            **kw_lumfun,
        )
    return lum_funcs


def maximum_redshift(
    z_m_intp, m_max, z_max, parametrization, z_const, alpha, m_star_par, seed_ngal
):
    """
    Computes the maximum redshift up to which we sample objects from the luminosity
    function. The cutoff is based on the criterion that the CDF for absolute magnitudes
    is larger than 1e-5, i.e. that there is a reasonable probability of actually
    obtaining objects at this redshift and absolute magnitude which still pass the cut
    on par.gals_mag_max.
    """
    if z_m_intp is None:
        return z_max

    def cond_mag_cdf_lim(z):
        m_s = m_star_lum_fct(z, parametrization, z_const, *m_star_par)
        cdf_lim = (
            upper_inc_gamma(alpha + 1, 10 ** (0.4 * (m_s - z_m_intp(z))))
            / upper_inc_gamma(alpha + 1, 10 ** (0.4 * (m_s - m_max)))
            - 1e-5
        )
        return cdf_lim

    try:
        z_max_cutoff = scipy.optimize.brentq(cond_mag_cdf_lim, 0, z_m_intp.x[-1])
    except ValueError:
        z_max_cutoff = z_m_intp.x[-1]

    z_max = min(z_max, z_max_cutoff)
    np.random.seed(seed_ngal)
    z_max += np.random.uniform(0, 0.0001)

    return z_max


def m_star_lum_fct(z, parametrization, z_const, slope, intercept):
    if parametrization == "linexp":
        # Eq. 3.3. from http://arxiv.org/abs/1705.05386
        m_s = np.polyval((slope, intercept), z)
    elif parametrization == "logpower":
        # Eq. 21 + 22 from https://arxiv.org/abs/1106.2039
        m_s = intercept + slope * np.log10(1 + z)
    elif parametrization == "truncated_logexp":
        m_s = intercept + slope * np.log10(1 + np.where(z < z_const, z, z_const))
    return m_s


def phi_star_lum_fct(z, parametrization, amplitude, exp):
    if (parametrization == "linexp") | (parametrization == "truncated_logexp"):
        # Eq. 3.4. from http://arxiv.org/abs/1705.05386
        p_star = amplitude * np.exp(exp * z)
    elif parametrization == "logpower":
        # Eq. 25 from https://arxiv.org/abs/1106.2039
        p_star = amplitude * (1 + z) ** exp
    return p_star


def upper_inc_gamma(a, x):
    if a > 0:
        uig = scipy.special.gamma(a) * scipy.special.gammaincc(a, x)

    elif a == 0:
        uig = -scipy.special.expi(-x)

    else:
        uig = 1 / a * (upper_inc_gamma(a + 1, x) - x**a * np.exp(-x))

    return uig


class NumGalCalculator:
    """
    Computes galaxy number counts by integrating the galaxy luminosity function.
    The integral over absolute magnitudes can be done analytically, while the integral
    over redshifts is computed numerically. See also
    docs/jupyter_notebooks/sample_redshift_magnitude.ipynb.
    """

    def __init__(
        self,
        z_max,
        m_max,
        parametrization,
        z_const,
        alpha,
        m_star_par,
        phi_star_par,
        cosmo,
        pixarea,
        ngal_multiplier=1,
    ):
        z_density_int = scipy.integrate.quad(
            func=self._redshift_density,
            a=0,
            b=z_max,
            args=(
                m_max,
                parametrization,
                z_const,
                alpha,
                m_star_par,
                phi_star_par,
                cosmo,
            ),
        )[0]
        self.n_gal_mean = int(round(z_density_int * pixarea * ngal_multiplier))

    def __call__(self):
        if self.n_gal_mean > 0:
            if self.n_gal_mean < 9e18:
                n_gal = np.random.poisson(self.n_gal_mean)
            else:
                # This is a workaround for the fact that np.random.poisson does not work
                # for large numbers. We use the fact that the Poisson distribution
                # converges to a Gaussian for large means and sample from a Gaussian
                # instead.
                # It will probably be a crazy galaxy population model anyway...
                LOGGER.warning("Using Gaussian instead of a Poisson due to large mean.")
                n = float(self.n_gal_mean)
                n_gal = int(np.random.normal(n, np.sqrt(n)))
        else:
            n_gal = self.n_gal_mean
        return n_gal

    def _redshift_density(
        self, z, m_max, parametrization, z_const, alpha, par_m_star, par_phi_star, cosmo
    ):
        m_star = m_star_lum_fct(z, parametrization, z_const, *par_m_star)
        phi_star = phi_star_lum_fct(z, parametrization, *par_phi_star)
        e = np.sqrt(cosmo.params.omega_m * (1 + z) ** 3 + cosmo.params.omega_l)
        d_h = cosmo.params.c / cosmo.params.H0
        d_m = cosmo.background.dist_trans_a(a=1 / (1 + z))
        density = (
            phi_star
            * d_h
            * d_m**2
            / e
            * upper_inc_gamma(alpha + 1, 10 ** (0.4 * (m_star - m_max)))
        )
        return density


class RedshiftAbsMagSampler:
    """
    Samples redshifts and absolute magnitudes from the galaxy luminosity function.
    The sampling is done by first drawing redshifts from the redshift-pdf obtained by
    integrating out absolute magnitudes. Then, we sample absolute magnitudes from the
    conditional pdfs obtained by conditioning the luminosity function on the sampled
    redshifts (the conditional pdf is different for each redshift). See also
    docs/jupyter_notebooks/sample_redshift_magnitude.ipynb and
    docs/jupyter_notebooks/test_self_consistency.ipynb.
    """

    def __init__(
        self,
        z_res,
        z_max,
        m_res,
        m_max,
        parametrization,
        z_const,
        alpha,
        m_star_par,
        phi_star_par,
        cosmo,
    ):
        self.z_res = z_res
        self.z_max = z_max
        self.m_res = m_res
        self.m_max = m_max
        self.parametrization = parametrization
        self.z_const = z_const
        self.alpha = alpha
        self.m_star_par = m_star_par
        self.phi_star_par = phi_star_par
        self.cosmo = cosmo

        # TODO: Do we need to pass all of these parameters? Should be in the class...
        self._setup_redshift_grid(
            z_max, z_res, m_max, z_const, alpha, m_star_par, phi_star_par, cosmo
        )
        self._setup_mag_grid(
            z_max, m_max, m_res, parametrization, z_const, alpha, m_star_par
        )

    def __call__(self, n_samples):
        z = np.random.choice(self.z_grid, size=n_samples, replace=True, p=self.nz_grid)

        m_s = m_star_lum_fct(z, self.parametrization, self.z_const, *self.m_star_par)
        m_rvs = np.random.uniform(
            low=0,
            high=upper_inc_gamma(self.alpha + 1, 10 ** (0.4 * (m_s - self.m_max))),
            size=n_samples,
        )  # here, we sample M* - M, where M* is redshift-dependent
        uig_ind = find_closest_ind(self.uig_grid, m_rvs)
        m = m_s - self.m_s__m__grid[uig_ind]  # now we transform from M* - M to M
        return z, m

    def _setup_redshift_grid(
        self, z_max, z_res, m_max, z_const, alpha, m_star_par, phi_star_par, cosmo
    ):
        self.z_grid = np.linspace(
            z_res, z_max, num=int(round((z_max - z_res) / z_res)) + 1
        )

        e = np.sqrt(
            cosmo.params.omega_m * (1 + self.z_grid) ** 3 + cosmo.params.omega_l
        )
        d_h = cosmo.params.c / cosmo.params.H0
        d_m = cosmo.background.dist_trans_a(a=1 / (1 + self.z_grid))
        f = d_h * d_m**2 / e
        m_star = m_star_lum_fct(self.z_grid, self.parametrization, z_const, *m_star_par)
        phi_star = phi_star_lum_fct(self.z_grid, self.parametrization, *phi_star_par)

        self.nz_grid = (
            f * phi_star * upper_inc_gamma(alpha + 1, 10 ** (0.4 * (m_star - m_max)))
        )
        self.nz_grid /= np.sum(self.nz_grid)

    def _setup_mag_grid(
        self, z_max, m_max, m_res, parametrization, z_const, alpha, m_star_par
    ):
        m_s_min = scipy.optimize.minimize_scalar(
            lambda z: m_star_lum_fct(z, parametrization, z_const, *m_star_par),
            bounds=(0, z_max),
            method="bounded",
        ).fun
        m_s_max = -scipy.optimize.minimize_scalar(
            lambda z: -m_star_lum_fct(z, parametrization, z_const, *m_star_par),
            bounds=(0, z_max),
            method="bounded",
        ).fun

        m_min = m_max
        while upper_inc_gamma(alpha + 1, 10 ** (0.4 * (m_s_min - m_min))) > 0:
            m_min -= 0.1
        self.m_s__m__grid = np.linspace(
            m_s_max - m_min,
            m_s_min - m_max,
            num=int(round((m_s_max - m_min - m_s_min + m_max) / m_res)) + 1,
        )

        self.uig_grid = upper_inc_gamma(alpha + 1, 10 ** (0.4 * self.m_s__m__grid))


class LuminosityFunction:
    """
    Luminosity function
    """

    def __init__(
        self,
        name,
        lum_fct_parametrization,
        m_star_slope,
        m_star_intcpt,
        phi_star_amp,
        phi_star_exp,
        z_const,
        alpha,
        cosmo,
        pixarea,
        galaxy_type,
        seed_ngal,
        z_res=0.001,
        m_res=0.001,
        z_max=np.inf,
        m_max=2,
        z_m_intp=None,
        ngal_multiplier=1,
    ):
        self.parametrization = lum_fct_parametrization
        self.m_star_slope = m_star_slope
        self.m_star_intcpt = m_star_intcpt
        self.phi_star_amp = phi_star_amp
        self.phi_star_exp = phi_star_exp
        self.m_star_par = m_star_slope, m_star_intcpt
        self.phi_star_par = phi_star_amp, phi_star_exp
        self.z_const = z_const
        self.alpha = alpha
        self.z_m_intp = z_m_intp
        self.m_max = m_max
        self.cosmo = cosmo
        self.pixarea = pixarea
        self.z_res = z_res
        self.name = name
        self.galaxy_type = galaxy_type

        self.z_max = maximum_redshift(
            z_m_intp=z_m_intp,
            m_max=m_max,
            z_max=z_max,
            parametrization=lum_fct_parametrization,
            z_const=z_const,
            alpha=alpha,
            m_star_par=self.m_star_par,
            seed_ngal=seed_ngal,
        )

        self.n_gal_calc = NumGalCalculator(
            z_max=self.z_max,
            m_max=m_max,
            parametrization=lum_fct_parametrization,
            z_const=z_const,
            alpha=alpha,
            m_star_par=self.m_star_par,
            phi_star_par=self.phi_star_par,
            cosmo=cosmo,
            pixarea=pixarea,
            ngal_multiplier=ngal_multiplier,
        )

        self.z_mabs_sampler = RedshiftAbsMagSampler(
            z_res=z_res,
            z_max=self.z_max,
            parametrization=lum_fct_parametrization,
            z_const=z_const,
            m_res=m_res,
            m_max=m_max,
            alpha=alpha,
            m_star_par=self.m_star_par,
            phi_star_par=self.phi_star_par,
            cosmo=cosmo,
        )

    def sample_z_mabs_and_apply_cut(
        self,
        seed_ngal,
        seed_lumfun,
        n_gal_max=np.inf,
        size_chunk=10000,
    ):
        """
        This function gets the abs mag and z using chunking, which uses less memory than
        the original method. It does not give exactly the same result as before due to
        different order of random draws in z_mabs_sampler, but it's the same sample.
        """
        np.random.seed(seed_ngal)
        n_gal = self.n_gal_calc()
        if n_gal == 0:
            return np.array([]), np.array([])
        n_chunks = int(np.ceil(float(n_gal) / float(size_chunk)))
        list_abs_mag = []
        list_z = []
        n_gal_final = 0
        for ic in range(n_chunks):
            n_gal_sample = n_gal % size_chunk if ic + 1 == n_chunks else size_chunk
            z_chunk, abs_mag_chunk = self.z_mabs_sampler(n_gal_sample)
            # Apply cut in z - M - plane
            if self.z_m_intp is not None:
                select = abs_mag_chunk < self.z_m_intp(z_chunk)
                z_chunk = z_chunk[select]
                abs_mag_chunk = abs_mag_chunk[select]

            n_gal_final += len(z_chunk)
            list_z.append(z_chunk)
            list_abs_mag.append(abs_mag_chunk)

            if n_gal_final > n_gal_max:
                break

        z = np.hstack(list_z)
        abs_mag = np.hstack(list_abs_mag)
        return abs_mag, z
