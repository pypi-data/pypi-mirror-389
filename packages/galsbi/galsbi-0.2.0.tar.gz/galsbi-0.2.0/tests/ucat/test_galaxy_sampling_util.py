"""
Created on July 27, 2018
author: Joerg Herbel
"""

import itertools
import os

import h5py
import healpy as hp
import ivy
import numpy as np
import PyCosmo
import pytest
import scipy.stats
from ivy import context
from ufig import coordinate_util
from ufig.sampling_util import sample_position_uniform as sample_position_uniform_ufig

from galsbi.ucat import galaxy_sampling_util
from galsbi.ucat.galaxy_population_models import galaxy_shape, galaxy_size
from galsbi.ucat.galaxy_population_models.galaxy_light_profile import (
    sample_sersic_for_galaxy_type,
)
from galsbi.ucat.galaxy_population_models.galaxy_luminosity_function import (
    NumGalCalculator,
    RedshiftAbsMagSampler,
    m_star_lum_fct,
    phi_star_lum_fct,
    upper_inc_gamma,
)
from galsbi.ucat.galaxy_population_models.galaxy_position import sample_position_uniform
from galsbi.ucat.galaxy_population_models.galaxy_sed import (
    sample_template_coeff_dirichlet,
    sample_template_coeff_lumfuncs,
)
from galsbi.ucat.galaxy_population_models.galaxy_shape import (
    distortion_to_shear,
    pe_bulge,
    pe_disc,
    sample_ellipticities_beta,
    sample_ellipticities_beta_mode,
    sample_ellipticities_for_galaxy_type,
)
from galsbi.ucat.galaxy_population_models.galaxy_size import (
    apply_pycosmo_distfun,
    r50_phys_to_ang,
    sample_r50_for_galaxy_type,
    sample_r50_phys,
)
from galsbi.ucat.plugins import sample_galaxies_photo


def redshift_mag_density(
    z, m, cosmo, alpha, parametrization, z_const, m_star_par, phi_star_par
):
    """
    Density of galaxies in redshift-absolute magnitude-space.
    :param z: Redshift.
    :param m: Absolute Magnitude.
    :param cosmo: Instance of PyCosmo.Cosmo defining the cosmology.
    :param alpha: alpha parameter of the luminosity function
    :param parametrization: Parametrization of the luminosity function
    :param z_const: Redshift at which the luminosity function is truncated
    :param m_star_par: 2-tuple defining the redshift evolution of m_*
    :param phi_star_par: 2-tuple defining the redshift evolution of phi_*
    :return: dN/(dz dM) evaluated at the input redshift and magnitude.
    """

    z = np.atleast_1d(z)
    z_unique, inv_ind = np.unique(z, return_inverse=True)

    e = np.sqrt(cosmo.params.omega_m * (1 + z) ** 3 + cosmo.params.omega_l)
    d_h = cosmo.params.c / cosmo.params.H0
    d_m = cosmo.background.dist_trans_a(a=1 / (1 + z_unique))[inv_ind]

    m_s = m_star_lum_fct(z, parametrization, z_const, *m_star_par)
    p_star = phi_star_lum_fct(z, parametrization, *phi_star_par)
    pow10 = 10 ** (0.4 * (m_s - m))
    phi = 0.4 * np.log(10) * p_star * pow10 ** (alpha + 1) * np.exp(-pow10)

    density = d_h * d_m**2 / e * phi

    return density


@pytest.fixture
def ctx():
    cosmo = PyCosmo.build()

    ctx = context.create_ctx(
        cosmo=cosmo, parameters=ivy.load_configs("galsbi.ucat.config.common")
    )

    params = {
        "ra0": 59.94140624999999,
        "catalog_precision": np.float32,
        "dec0": 0.0,
        "nside_sampling": 512,
        "pixscale": 0.2,
        "crpix_ra": 5000.5,
        "crpix_dec": 5000.5,
        "lum_fct_parametrization": "linexp",
        "lum_fct_filter_band": "B",
        "lum_fct_alpha_blue": -1.3,
        "lum_fct_alpha_red": -0.5,
        "lum_fct_m_star_blue_slope": -0.9408582,
        "lum_fct_m_star_blue_intcpt": -20.40492365,
        "lum_fct_m_star_red_slope": -0.70798041,
        "lum_fct_m_star_red_intcpt": -20.37196157,
        "lum_fct_phi_star_blue_amp": 0.00370253,
        "lum_fct_phi_star_blue_exp": -0.10268436,
        "lum_fct_phi_star_red_amp": 0.0035097,
        "lum_fct_phi_star_red_exp": -0.70596888,
        "lum_fct_z_res": 0.001,
        "lum_fct_m_max": -15,
        "lum_fct_m_res": 0.001,
        "lum_fct_z_max": 5,
        "gals_mag_max": 20,
        "n_gal_max_blue": np.inf,
        "n_gal_max_red": np.inf,
        "templates_file_name": os.path.join(os.getcwd(), "template_spectra.h5"),
        "templates_int_tables_file_name": os.path.join(
            os.getcwd(), "template_integrals.h5"
        ),
        "filters_file_name": os.path.join(os.getcwd(), "filters.h5"),
        "maps_remote_dir": os.getcwd(),
    }
    for key, value in params.items():
        setattr(ctx.parameters, key, value)
    return ctx


def test_apply_pycosmo_distfun(ctx):
    """
    Test the function which evaluates PyCosmo distance measures.
    """

    cosmo = ctx.cosmo

    # Distance functions that will be tested
    distances_test = [
        cosmo.background.dist_ang_a,
        cosmo.background.dist_lum_a,
        cosmo.background.dist_rad_a,
        cosmo.background.dist_trans_a,
    ]

    # Redshifts to test, each redshift is repeated thrice, since the function we test
    # specifically implements the distance computation for repeated redshifts
    z_test = np.linspace(0, 10, num=10)
    z_test = np.repeat(z_test, 3)
    a_test = 1 / (1 + z_test)

    for dist in distances_test:
        dist_direct = dist(a=a_test)
        dist_apply_pc_df = apply_pycosmo_distfun(dist, z_test)
        assert np.array_equal(dist_direct, dist_apply_pc_df)


@pytest.mark.parametrize("a", [1.5, 1.0, 0.1, -0.1, -1.5])
def test_upper_inc_gamma(a, snapshot):
    """
    Test implementation of upper incomplete gamma function using values from
    WolframAlpha.
    """
    # Values of the upper incomplete gamma function from WolframAlpha
    x = np.array([0.5, 1, 2])
    snapshot.check(upper_inc_gamma(a, x), rtol=1e-8, atol=0)


def test_sample_redshift_mag(ctx):
    """
    Test the sampling of redshifts and absolute magnitudes. The test samples redshifts
    and magnitudes using the sampler implemented in galsbi.ucat.galaxy_sampling_util.
    It also samples directly from the 2-d PDF by evaluating it on a grid. The two
    samples are then compared separately in each dimension using the K-S test (also in
    slices of redshift and absolute magnitude). The requirement is that the average
    p-value does not fall below 5%, such that we cannot reject the null hypothesis that
    we are sampling redshifts and magnitudes from the correct distribution.
    """

    par = ctx.parameters
    z_max = 3
    m_min = -25

    m_star_par_blue = (par.lum_fct_m_star_blue_slope, par.lum_fct_m_star_blue_intcpt)
    m_star_par_red = (par.lum_fct_m_star_red_slope, par.lum_fct_m_star_red_intcpt)
    phi_star_par_blue = (par.lum_fct_phi_star_blue_amp, par.lum_fct_phi_star_blue_exp)
    phi_star_par_red = (par.lum_fct_phi_star_red_amp, par.lum_fct_phi_star_red_exp)
    parametrization = par.lum_fct_parametrization

    ks_tests_redshift_mag(
        par.lum_fct_z_res,
        z_max,
        0.002,  # reduced resolution to avoid memory usage issues on ci
        m_min,
        par.lum_fct_m_max,
        parametrization,
        par.lum_fct_alpha_blue,
        m_star_par_blue,
        phi_star_par_blue,
        ctx.cosmo,
    )

    ks_tests_redshift_mag(
        par.lum_fct_z_res,
        z_max,
        0.002,  # reduced resolution to avoid memory usage issues on ci
        m_min,
        par.lum_fct_m_max,
        parametrization,
        par.lum_fct_alpha_red,
        m_star_par_red,
        phi_star_par_red,
        ctx.cosmo,
    )


def ks_tests_redshift_mag(
    z_res,
    z_max,
    m_res,
    m_min,
    m_max,
    parametrization,
    alpha,
    m_star_par,
    phi_star_par,
    cosmo,
    n_samples=int(1e6),
    n_bins_check=3,
):
    # Sample using sampler
    z_m_sampler = RedshiftAbsMagSampler(
        z_res=z_res,
        z_max=z_max,
        m_res=m_res,
        m_max=m_max,
        parametrization=parametrization,
        z_const=5,
        alpha=alpha,
        m_star_par=m_star_par,
        phi_star_par=phi_star_par,
        cosmo=cosmo,
    )

    z_sampler, m_sampler = z_m_sampler(n_samples)

    # Sample from 2-dim. pdf
    z_grid = np.arange(z_res, z_max + z_res, z_res)
    m_grid = np.arange(m_min, m_max + m_res, m_res)
    z_grid, m_grid = np.meshgrid(z_grid, m_grid)
    z_grid = np.ravel(z_grid)
    m_grid = np.ravel(m_grid)
    prob_pdf = redshift_mag_density(
        z_grid, m_grid, cosmo, alpha, parametrization, 5, m_star_par, phi_star_par
    )
    prob_pdf /= np.sum(prob_pdf)
    ind_pdf = np.random.choice(
        len(z_grid), size=len(z_sampler), replace=True, p=prob_pdf
    )
    z_pdf = z_grid[ind_pdf]
    m_pdf = m_grid[ind_pdf]

    # k-s tests for complete sample
    p_val = 0
    n_tests = 0
    p_val += scipy.stats.ks_2samp(z_pdf, z_sampler)[1]
    p_val += scipy.stats.ks_2samp(m_pdf, m_sampler)[1]
    n_tests += 2

    # k-s tests for sample split by redshift
    bins_z = np.linspace(0, z_max, num=n_bins_check + 1)

    for i_bin in range(n_bins_check):
        select_sampler = (z_sampler > bins_z[i_bin]) & (z_sampler <= bins_z[i_bin + 1])
        select_pdf = (z_pdf > bins_z[i_bin]) & (z_pdf <= bins_z[i_bin + 1])
        m_sampler_bin = m_sampler[select_sampler]
        m_pdf_bin = m_pdf[select_pdf]

        p_val += scipy.stats.ks_2samp(m_pdf_bin, m_sampler_bin)[1]
        n_tests += 1

    # k-s tests for sample split by magnitude
    bins_m = np.linspace(m_min, m_max, num=n_bins_check + 1)

    for i_bin in range(n_bins_check):
        select_sampler = (m_sampler > bins_m[i_bin]) & (m_sampler <= bins_m[i_bin + 1])
        select_pdf = (m_pdf > bins_m[i_bin]) & (m_pdf <= bins_m[i_bin + 1])
        z_sampler_bin = z_sampler[select_sampler]
        z_pdf_bin = z_pdf[select_pdf]

        p_val += scipy.stats.ks_2samp(z_sampler_bin, z_pdf_bin)[1]
        n_tests += 1

    p_val_average = p_val / n_tests
    assert p_val_average > 0.05


def test_z_m_cut(ctx):
    """
    Test the interpolation of the cut in the redshift-absolute mag-plane. The test
    creates an artifical tempalte and two filter bands. It then computes the
    interpolation. To check if the interpolation is sensible, it checks at various
    randomly selected redshifts whether the apparent magnitude computed at that redshift
    according to the interpolated value of the absolute magnitude is close to the set
    limiting apparent magnitude.
    """

    par = ctx.parameters

    # Create template spectra file
    # we use a template where the flux increases linearly with the wavelength for
    # testing purposes
    template_lam = np.linspace(1000, 15000, num=15000)
    l1 = template_lam[0]
    l2 = template_lam[-1]
    f1 = 1e-5
    f2 = 0.5e-2
    m = (f1 - f2) / (l1 - l2)
    c = f2 - m * l2
    template_amp = m * template_lam[np.newaxis, :] + c

    with h5py.File(par.templates_file_name, mode="w") as f:
        f.create_dataset(name="wavelength", data=template_lam)
        f.create_dataset(name="amplitudes", data=template_amp)

    # Create filter bands
    filter_lam = np.linspace(3000, 10000, num=1000)
    filter_b_throughput = np.zeros_like(filter_lam)
    filter_b_throughput[(filter_lam > 4500) & (filter_lam < 5000)] = 1
    filter_r_throughput = np.zeros_like(filter_lam)
    filter_r_throughput[(filter_lam > 7500) & (filter_lam < 8000)] = 1
    filters = {"SuprimeCam_B": filter_b_throughput, "HSC_r2": filter_r_throughput}
    with h5py.File(par.filters_file_name, mode="w") as f:
        for filter_name in filters:
            grp = f.create_group(name=filter_name)
            grp.create_dataset(name="lam", data=filter_lam)
            grp.create_dataset(name="amp", data=filters[filter_name])

    # Magnitude calculator
    filters = ["B", "r"]
    par.filters = filters
    par.reference_band = "r"
    par.filters_full_names = {"B": "SuprimeCam_B", "r": "HSC_r2"}
    mag_calc = sample_galaxies_photo.get_magnitude_calculator_direct(filters, par)

    # Interpolate cut in redshift-absolute magnitude plane
    z_m_cut_intp = galaxy_sampling_util.intp_z_m_cut(ctx.cosmo, mag_calc, par)

    # Test interpolation at various redshifts
    z_test = np.random.uniform(low=z_m_cut_intp.x[1], high=z_m_cut_intp.x[-1], size=100)
    m_abs_test = z_m_cut_intp(z_test)
    avg_delta_mag = 0.0

    for z, m_abs in zip(z_test, m_abs_test, strict=True):
        # 1) Check that adjusting the template coefficients according to the absolute
        # magnitude works
        coeff = np.ones((1, 1))
        coeff[:] = 10 ** (
            0.4
            * (
                mag_calc(
                    redshifts=np.zeros(1),
                    excess_b_v=np.zeros(1),
                    coeffs=coeff,
                    filter_names=[par.lum_fct_filter_band],
                )[par.lum_fct_filter_band]
                - m_abs
            )
        )

        m_abs_calc = mag_calc(
            redshifts=np.zeros(1),
            excess_b_v=np.zeros(1),
            coeffs=coeff,
            filter_names=[par.lum_fct_filter_band],
        )[par.lum_fct_filter_band][0]
        assert np.allclose(m_abs, m_abs_calc)

        # 2) Compute corresponding apparent magnitude and check that it is close to the
        # set limit
        coeff *= (1e-5 / ctx.cosmo.background.dist_lum_a(a=1 / (1 + z))) ** 2 / (1 + z)
        m_app_calc = mag_calc(
            redshifts=np.atleast_1d(z),
            excess_b_v=np.zeros(1),
            coeffs=coeff,
            filter_names=["r"],
        )["r"][0]
        delta_mag = abs(m_app_calc - par.gals_mag_max)
        avg_delta_mag += delta_mag
        assert delta_mag < 0.5

    # 3) Check if average delta magnitude is small
    avg_delta_mag /= len(z_test)
    assert avg_delta_mag < 0.05

    # Clean up
    os.remove(par.templates_file_name)
    os.remove(par.filters_file_name)


def test_sample_template_coefficients_dirichlet():
    """
    Test the sampling of the template spectra coefficients. The test samples a set of
    coefficients, whereby the corresponding parameter values are set such that all
    samples should come from the same Dirichlet distribution (no evolution with
    redshift). The test then computes the sum, the mean and the variance of the samples
    and checks against the expected values. The criterion is that the sum is always very
    close to 1. The test compares the means and variances using the standard errors of
    these quantities. The criterion is that the discrepancy between the expected and the
    computed values is on average smaller than two times the standard error (whereby the
    average runs over the dimensions of the samples. In a second step, the test draws
    samples from the corresponding Dirichlet distribution and compares them to the drawn
    coefficients using the KS-test. The criterion is that the average p-value is larger
    than 0.05, such that we cannot reject the null hypothesis that the coefficients are
    sampled correctly.
    """

    # Draw samples
    n_samples = int(1e6)
    alpha = np.arange(1, 6)
    z1 = 1
    weight = 1
    z = np.linspace(0, 10, num=n_samples)
    coeff = sample_template_coeff_dirichlet(z, alpha, alpha, z1, weight)

    # 1) Test mean, variance and sum
    sum = np.sum(coeff, axis=1)
    mean = np.mean(coeff, axis=0)
    var = np.var(coeff, axis=0, ddof=1)

    stderr_mean = np.sqrt(var / n_samples)
    mu_4 = np.mean((coeff - mean) ** 4, axis=0)
    stderr_var = np.sqrt(
        (mu_4 - (n_samples - 3) / (n_samples - 1) * var**2) / n_samples
    )

    sum_alpha = np.sum(alpha)
    mean_exp = alpha / sum_alpha
    var_exp = alpha * (sum_alpha - alpha) / (sum_alpha**2 * (sum_alpha + 1))

    assert np.allclose(sum, 1)
    assert np.mean(np.fabs(mean - mean_exp) / stderr_mean) < 2
    assert np.mean(np.fabs(var - var_exp) / stderr_var) < 2

    # 2) KS-tests against Dirichlet samples
    samples_dir = np.random.dirichlet(alpha, size=n_samples)

    n_tests = 1
    p_val_avg = scipy.stats.ks_2samp(coeff.flatten(), samples_dir.flatten())[1]

    for i in range(alpha.size):
        p_val_avg += scipy.stats.ks_2samp(coeff[:, i], samples_dir[:, i])[1]
        n_tests += 1

    p_val_avg /= n_tests

    assert p_val_avg > 0.05


def test_sample_template_coefficients_dirichlet_lumfuncs(ctx):
    par = ctx.parameters

    redshifts = dict(
        red=np.linspace(0, 10, num=int(1e6)), blue=np.linspace(0, 5, num=int(1e6))
    )
    n_templates = 5
    coeff_samplers = [
        "dirichlet",
        "dirichlet_alpha_mode",
    ]

    par.template_coeff_weight_blue = 1
    par.template_coeff_weight_red = 1
    for c in coeff_samplers:
        par.template_coeff_sampler = c
        if c == "dirichlet_alpha_mode":
            for key in redshifts:
                for i in range(n_templates):
                    setattr(par, f"template_coeff_alpha0_{key}_{i}", 0.2)
                    setattr(par, f"template_coeff_alpha1_{key}_{i}", 0.2)
        coeffs = sample_template_coeff_lumfuncs(par, redshifts, n_templates)
        for key in redshifts:
            assert coeffs[key].shape == (redshifts[key].size, n_templates)
            assert np.allclose(np.sum(coeffs[key], axis=1), 1)


def test_sample_position_uniform(ctx):
    """
    Test the sampling of the galaxy positions within a Healpix pixel.
    """

    par = ctx.parameters
    n_obj = int(1e6)

    w = coordinate_util.tile_in_skycoords(
        pixscale=par.pixscale,
        ra0=par.ra0,
        dec0=par.dec0,
        crpix_ra=par.crpix_ra,
        crpix_dec=par.crpix_dec,
    )

    theta, phi = coordinate_util.radec2thetaphi(par.ra0, par.dec0)
    pixel_index = hp.ang2pix(par.nside_sampling, theta, phi)

    pixel_center_theta, pixel_center_phi = hp.pix2ang(par.nside_sampling, pixel_index)

    corners = hp.boundaries(par.nside_sampling, pixel_index, 1)
    corners_theta, corners_phi = hp.vec2ang(np.transpose(corners))

    x, y = sample_position_uniform(n_obj, w, pixel_index, par.nside_sampling)
    theta, phi = coordinate_util.xy2thetaphi(w, x, y)

    # All positions within pixel bounds
    assert np.min(theta) >= np.min(corners_theta)
    assert np.max(theta) <= np.max(corners_theta)
    assert np.min(phi) >= np.min(corners_phi)
    assert np.max(phi) <= np.max(corners_phi)

    # Mean of positions is close to pixel center
    assert abs(np.mean(theta) - pixel_center_theta) < np.pi / 180 / 3600  # 1 arcsec
    assert abs(np.mean(phi) - pixel_center_phi) < np.pi / 180 / 3600  # 1 arcsec


def test_sample_position_uniform_ufig(ctx):
    """
    Check that the ufig implementation for the stars is consistent with the galsbi
    implementation for galaxies.
    """
    par = ctx.parameters
    n_obj = int(1e6)

    w = coordinate_util.tile_in_skycoords(
        pixscale=par.pixscale,
        ra0=par.ra0,
        dec0=par.dec0,
        crpix_ra=par.crpix_ra,
        crpix_dec=par.crpix_dec,
    )

    theta, phi = coordinate_util.radec2thetaphi(par.ra0, par.dec0)
    pixel_index = hp.ang2pix(par.nside_sampling, theta, phi)

    np.random.seed(0)
    x, y = sample_position_uniform(n_obj, w, pixel_index, par.nside_sampling)
    np.random.seed(0)
    x_ufig, y_ufig = sample_position_uniform_ufig(
        n_obj, w, pixel_index, par.nside_sampling
    )

    # check that the implementation has not changed by comparing to one in ufig
    assert np.allclose(
        x, x_ufig
    ), "configuration changed, adapt also ufig implementation"
    assert np.allclose(
        y, y_ufig
    ), "configuration changed, adapt also ufig implementation"


def test_sample_sersic():
    """
    Test the sampling of Sersic indices.
    """

    par = context.create_ctx(
        sersic_n_mean_low=0.2,
        sersic_n_sigma_low=1,
        sersic_n_mean_1_hi=0.3,
        sersic_n_sigma_1_hi=0.5,
        sersic_n_mean_2_hi=1.6,
        sersic_n_sigma_2_hi=0.4,
        sersic_n_offset=0.2,
        sersic_single_value=2,
        sersic_index_blue=1,
        sersic_index_red=4,
        sersic_betaprime_blue_mode=0.8,
        sersic_betaprime_blue_size=5,
        sersic_betaprime_blue_mode_alpha=0.0,
        sersic_betaprime_red_mode=1.5,
        sersic_betaprime_red_size=50,
        sersic_betaprime_red_mode_alpha=0.0,
        sersic_n_min=0,
        sersic_n_max=3,
        catalog_precision=np.float32,
    )

    n_gal = int(1e4)
    app_mag_r = np.random.uniform(low=15, high=30, size=n_gal)
    z = np.random.uniform(low=0.0, high=1, size=n_gal)

    sampling_methods = ["default", "single", "blue_red_fixed", "blue_red_betaprime"]

    for sampling_method in sampling_methods:
        par.sersic_sampling_method = sampling_method
        sersic_n = sample_sersic_for_galaxy_type(n_gal, "blue", app_mag_r, par, z=z)
        assert sersic_n.size == n_gal
        assert np.all(sersic_n > 0)

    par.sersic_sampling_method = "unknown"
    with pytest.raises(ValueError):
        sample_sersic_for_galaxy_type(n_gal, "blue", app_mag_r, par)


def test_sample_r50(ctx):
    """
    Test the sampling of intrinsic galaxy sizes.
    """

    # Setup
    par = ctx.parameters
    n_gal = int(1e5)
    z = np.random.uniform(low=0.0, high=10.0, size=n_gal)
    abs_mag = np.random.uniform(low=-30.0, high=0.0, size=n_gal)

    # Split by maximum angular luminosity distance
    dist_ang_a = ctx.cosmo.background.dist_ang_a(a=1 / (1 + z))
    z_max_dist_ang_a = z[np.argmax(dist_ang_a)]
    select_growing_dist_ang_a = z <= z_max_dist_ang_a
    select_declining_dist_ang_a = ~select_growing_dist_ang_a
    z_growing = z[select_growing_dist_ang_a]
    z_declining = z[select_declining_dist_ang_a]

    sampling_methods = ["single", "red_blue", "sdss_fit"]
    galaxy_types = ["blue", "red"]
    for sampling_method, g_type in itertools.product(sampling_methods, galaxy_types):
        par.logr50_sampling_method = sampling_method
        if sampling_method == "sdss_fit":
            par.sample_r50_model = "base"
        else:
            par.sample_r50_model = "shift20"
        r50, r50_arcsec, _ = sample_r50_for_galaxy_type(
            z, abs_mag, ctx.cosmo, par, galaxy_type=g_type
        )
        assert np.all(r50 > 0)
        assert np.allclose(r50, r50_arcsec / par.pixscale)

        # For galaxies with redshifts smaller than the redshift where the angular
        # luminosity distance peaks, the intrinsic size should decrease on average; for
        # galaxies with larger redshifts, it should increase (on average)
        slope_growing = np.polyfit(z_growing, r50[select_growing_dist_ang_a], 1)[0]
        slope_declining = np.polyfit(z_declining, r50[select_declining_dist_ang_a], 1)[
            0
        ]
        assert slope_growing < 0
        assert slope_declining > 0


def test_sample_ellipticities():
    """
    Test the sampling of intrinsic galaxy ellipticities.
    """
    par = context.create_ctx(
        e1_mean=0.0,
        e2_mean=-0.05,
        e1_sigma=0.39,
        e2_sigma=0.39,
        e1_mean_blue=0.0,
        e2_mean_blue=0.0,
        e1_mean_red=0.0,
        e2_mean_red=0.0,
        ell_sigma_blue=0.46,
        ell_sigma_red=0.2,
        ell_disc_log_a=-1.3708147902715042,
        ell_disc_min_e=0.02,
        ell_disc_pow_alpha=1,
        ell_bulge_b=2.368,
        ell_beta_ab_ratio=0.57,
        ell_beta_ab_sum=2.9,
        ell_beta_emax=0.98,
        ell_beta_mode=0.2,
        ell_beta_mode_blue=0.2,
        ell_beta_mode_red=0.2,
        ell_beta_ab_sum_blue=2.9,
        ell_beta_ab_sum_red=2.9,
    )

    n_gal = int(1e4)

    sampling_methods = [
        "gaussian",
        "gaussian_blue_red",
        "blue_red_miller2013",
        "beta_ratio",
        "beta_mode",
        "beta_mode_red_blue",
    ]

    for sampling_method in sampling_methods:
        par.ellipticity_sampling_method = sampling_method
        e1, e2 = sample_ellipticities_for_galaxy_type(n_gal, "blue", par)
        e_sq = e1**2 + e2**2
        assert e_sq.size == n_gal
        assert np.all(e_sq < 1)
        e1, e2 = sample_ellipticities_for_galaxy_type(n_gal, "red", par)
        e_sq = e1**2 + e2**2
        assert e_sq.size == n_gal
        assert np.all(e_sq < 1)


def test_crazy_large_galaxy_numbers():
    cosmo = PyCosmo.build()
    NumGalCalculator(
        z_max=5,
        m_max=-15,
        parametrization="linexp",
        z_const=5,
        alpha=-1,
        m_star_par=(-20, 0),
        phi_star_par=(1e7, 0),  # crazy high value
        cosmo=cosmo,
        pixarea=1,
    )


@pytest.mark.parametrize(
    "input_method,expected_method,warning_msg",
    [
        ("default", "gaussian", "ellipticity_sampling_method=default is deprecated"),
        (
            "blue_red",
            "gaussian_blue_red",
            "ellipticity_sampling_method=blue_red is deprecated",
        ),
        (
            "beta_function",
            "beta_ratio",
            "ellipticity_sampling_method=beta_function is deprecated",
        ),
        (
            "beta_function_mode",
            "beta_mode",
            "ellipticity_sampling_method=beta_function_mode is deprecated",
        ),
        (
            "beta_function_mode_red_blue",
            "beta_mode_red_blue",
            "ellipticity_sampling_method=beta_function_mode_red_blue is deprecated",
        ),
    ],
)
def test_ellipticity_backwards_compatibility(
    input_method, expected_method, warning_msg
):
    par = context.create_ctx(ellipticity_sampling_method=input_method)
    with pytest.warns(DeprecationWarning, match=warning_msg):
        galaxy_shape.backwards_compatibility(par)
    assert par.ellipticity_sampling_method == expected_method


def test_ellipticity_error_handling():
    """Test error handling for invalid ellipticity sampling methods and galaxy types."""
    par = context.create_ctx(
        ellipticity_sampling_method="unknown_method",
        e1_mean=0.0,
        e2_mean=0.0,
        e1_sigma=0.2,
        e2_sigma=0.2,
    )

    n_gal = 100

    # Test unknown sampling method
    with pytest.raises(ValueError, match="unknown ellipticity_sampling_method"):
        sample_ellipticities_for_galaxy_type(n_gal, "blue", par)

    # Test unsupported galaxy type for Miller2013 method
    par.ellipticity_sampling_method = "blue_red_miller2013"
    par.ell_disc_log_a = -1.367
    par.ell_disc_min_e = 0.025
    par.ell_disc_pow_alpha = 1.0

    with pytest.raises(ValueError, match="galaxy type.*not supported"):
        sample_ellipticities_for_galaxy_type(n_gal, "green", par)


def test_galaxy_size_backwards_compatibility():
    """Test backwards compatibility warnings for deprecated galaxy size sampling
    methods."""

    # Test deprecated 'sample_r50_model' parameter
    par = context.create_ctx(sample_r50_model="base")
    with pytest.warns(DeprecationWarning, match="sample_r50_model is deprecated"):
        galaxy_size.backwards_compatibility(par)
    assert par.logr50_phys_M0 == 0.0


def test_galaxy_size_error_handling(ctx):
    """Test error handling for invalid galaxy size sampling methods and galaxy types."""
    cosmo = ctx.cosmo
    par = ctx.parameters
    n_gal = 10
    abs_mag = np.random.uniform(-22, -18, n_gal)
    z = np.random.uniform(0.1, 1.0, n_gal)

    # Test unknown sampling method
    par.logr50_sampling_method = "unknown_method"
    par.catalog_precision = np.float32
    par.pixscale = 0.2

    with pytest.raises(Exception, match="unsupported logr50_sampling_method"):
        sample_r50_for_galaxy_type(abs_mag, z, cosmo, par, "blue")

    # Test unsupported galaxy type for SDSS fit method
    par.logr50_sampling_method = "sdss_fit"
    # Set some required SDSS parameters to avoid AttributeError
    par.logr50_sdss_fit_sigma1_green = 0.4  # This will trigger the ValueError later
    par.logr50_sdss_fit_sigma2_green = 0.2
    par.logr50_sdss_fit_M0_green = -20.0

    with pytest.raises(ValueError, match="unsupported galaxy_type=green"):
        sample_r50_for_galaxy_type(abs_mag, z, cosmo, par, "green")


def test_luminosity_function_edge_cases():
    """Test edge cases for luminosity function calculations."""
    cosmo = PyCosmo.build()

    # Test with very large galaxy numbers (should trigger Gaussian approximation)
    calc = NumGalCalculator(
        z_max=5,
        m_max=-15,
        parametrization="linexp",
        z_const=5,
        alpha=-1,
        m_star_par=(-20, 0),
        phi_star_par=(1e20, 0),  # Extremely high value to trigger large mean
        cosmo=cosmo,
        pixarea=1,
        ngal_multiplier=1e10,  # Large multiplier
    )

    # This should trigger the Gaussian approximation warning (it's a logger warning,
    # not pytest warning)
    # Let's just check that it doesn't crash and returns a reasonable value
    n_gal = calc()
    assert n_gal > 0

    # Test with zero mean (should return exactly the mean)
    calc_zero = NumGalCalculator(
        z_max=5,
        m_max=-15,
        parametrization="linexp",
        z_const=5,
        alpha=-1,
        m_star_par=(-20, 0),
        phi_star_par=(0, 0),  # Zero amplitude
        cosmo=cosmo,
        pixarea=1,
    )

    n_gal_zero = calc_zero()
    assert n_gal_zero == 0


def test_zero_galaxy_edge_cases():
    """Test edge cases with zero galaxies."""
    # Test ellipticity sampling with zero galaxies
    par = context.create_ctx(
        ellipticity_sampling_method="gaussian",
        e1_mean=0.0,
        e2_mean=0.0,
        e1_sigma=0.2,
        e2_sigma=0.2,
    )

    e1, e2 = sample_ellipticities_for_galaxy_type(0, "blue", par)
    assert len(e1) == 0
    assert len(e2) == 0

    # Test size sampling with zero galaxies
    cosmo = PyCosmo.build()
    par_size = context.create_ctx(
        logr50_sampling_method="single",
        logr50_phys_M0=-20.0,
        logr50_phys_std=0.3,
        logr50_phys_mean_slope=-0.2,
        logr50_phys_mean_intcpt=1.0,
        logr50_alpha=-0.5,
        catalog_precision=np.float32,
        pixscale=0.2,
    )

    abs_mag = np.array([])
    z = np.array([])

    r50_pix, r50_arcsec, r50_phys = sample_r50_for_galaxy_type(
        abs_mag, z, cosmo, par_size, "blue"
    )

    assert len(r50_pix) == 0
    assert len(r50_arcsec) == 0
    assert len(r50_phys) == 0


def test_single_galaxy_edge_cases(ctx):
    """Test edge cases with single galaxy."""
    # Test ellipticity sampling with single galaxy
    par = context.create_ctx(
        ellipticity_sampling_method="gaussian",
        e1_mean=0.1,
        e2_mean=-0.05,
        e1_sigma=0.0,  # Zero scatter for deterministic result
        e2_sigma=0.0,
    )

    e1, e2 = sample_ellipticities_for_galaxy_type(1, "blue", par)
    assert len(e1) == 1
    assert len(e2) == 1
    assert np.isclose(e1[0], 0.1)
    assert np.isclose(e2[0], -0.05)


def test_extreme_parameter_values(ctx):
    """Test handling of extreme parameter values - just test ellipticities."""
    # Test ellipticity sampling with extreme sigma values
    par = context.create_ctx(
        ellipticity_sampling_method="gaussian",
        e1_mean=0.0,
        e2_mean=0.0,
        e1_sigma=0.8,  # Large sigma
        e2_sigma=0.8,
    )

    e1, e2 = sample_ellipticities_for_galaxy_type(100, "blue", par)

    # Should still satisfy constraint despite large sigma
    assert np.all(e1**2 + e2**2 < 1.0)
    assert len(e1) == 100
    assert len(e2) == 100


def test_ellipticity_gaussian_rejection_sampling():
    """Test Gaussian ellipticity sampling with large scatter to trigger rejection
    sampling."""
    par = context.create_ctx(
        ellipticity_sampling_method="gaussian",
        e1_mean=0.0,
        e2_mean=0.0,
        e1_sigma=1.0,  # Large sigma will generate many rejections
        e2_sigma=1.0,
    )

    n_gal = 100
    e1, e2 = sample_ellipticities_for_galaxy_type(n_gal, "blue", par)

    # Check constraint is satisfied despite large scatter
    assert np.all(e1**2 + e2**2 < 1.0)
    assert len(e1) == n_gal
    assert len(e2) == n_gal


def test_distortion_to_shear():
    """Test the distortion_to_shear function."""

    # Test basic functionality
    distortion = np.array([0.0, 0.5, 0.8])
    shear = distortion_to_shear(distortion)

    # Check that shear is positive and bounded
    assert np.all(shear >= 0)
    assert np.all(shear < 1)

    # Check that distortion=0 gives shear=0
    assert np.isclose(shear[0], 0.0)

    # Test edge cases
    small_distortion = 1e-6
    shear_small = distortion_to_shear(small_distortion)
    assert shear_small > 0

    large_distortion = 0.99
    shear_large = distortion_to_shear(large_distortion)
    assert shear_large < 1.0


def test_pe_disc_and_pe_bulge():
    """Test pe_disc and pe_bulge functions for specific ellipticity distributions."""

    n_gal = 1000

    # Test pe_disc
    e1_disc, e2_disc = pe_disc(n_gal)
    assert len(e1_disc) == n_gal
    assert len(e2_disc) == n_gal
    e_mag_disc = np.sqrt(e1_disc**2 + e2_disc**2)
    assert np.all(e_mag_disc >= 0)
    assert np.all(e_mag_disc <= 1.0)

    # Test pe_disc with custom parameters
    e1_disc_custom, e2_disc_custom = pe_disc(
        n_gal, log_a=-1.0, emax=0.6, emin=0.01, pow_alpha=2
    )
    assert len(e1_disc_custom) == n_gal
    assert len(e2_disc_custom) == n_gal

    # Test pe_bulge
    e1_bulge, e2_bulge = pe_bulge(n_gal)
    assert len(e1_bulge) == n_gal
    assert len(e2_bulge) == n_gal
    e_mag_bulge = np.sqrt(e1_bulge**2 + e2_bulge**2)
    assert np.all(e_mag_bulge >= 0)
    assert np.all(e_mag_bulge <= 1.0)

    # Test pe_bulge with custom parameters
    e1_bulge_custom, e2_bulge_custom = pe_bulge(n_gal, b=3.0, c=8.0)
    assert len(e1_bulge_custom) == n_gal
    assert len(e2_bulge_custom) == n_gal


def test_beta_ellipticity_sampling():
    """Test beta distribution ellipticity sampling methods."""

    n_gal = 1000

    # Test sample_ellipticities_beta
    par = context.create_ctx(
        ell_beta_ab_sum=4.0,
        ell_beta_ab_ratio=0.3,
        ell_beta_emax=0.8,
    )

    e1_beta, e2_beta = sample_ellipticities_beta(n_gal, par)
    assert len(e1_beta) == n_gal
    assert len(e2_beta) == n_gal
    e_mag_beta = np.sqrt(e1_beta**2 + e2_beta**2)
    assert np.all(e_mag_beta >= 0)
    assert np.all(e_mag_beta <= 1.0)

    # Test sample_ellipticities_beta_mode
    e1_beta_mode, e2_beta_mode = sample_ellipticities_beta_mode(
        n_gal=n_gal, ell_beta_ab_sum=4.0, ell_beta_mode=0.3, ell_beta_emax=0.8
    )
    assert len(e1_beta_mode) == n_gal
    assert len(e2_beta_mode) == n_gal
    e_mag_beta_mode = np.sqrt(e1_beta_mode**2 + e2_beta_mode**2)
    assert np.all(e_mag_beta_mode >= 0)
    assert np.all(e_mag_beta_mode <= 1.0)


def test_r50_phys_to_ang():
    """Test physical to angular size conversion."""

    cosmo = PyCosmo.build()
    r50_phys = np.array([1.0, 5.0, 10.0])  # kpc
    z = np.array([0.1, 0.5, 1.0])

    r50_ang = r50_phys_to_ang(r50_phys, cosmo, z)

    assert len(r50_ang) == len(r50_phys)
    assert np.all(r50_ang > 0)  # Angular sizes should be positive
    assert np.all(np.isfinite(r50_ang))

    # Test with single values
    r50_ang_single = r50_phys_to_ang(2.0, cosmo, 0.3)
    assert np.isscalar(r50_ang_single) or len(r50_ang_single) == 1
    assert r50_ang_single > 0


def test_sample_r50_phys():
    """Test physical size sampling function."""

    n_gal = 100
    abs_mag_shift = np.random.uniform(-2, 2, n_gal)

    r50_phys = sample_r50_phys(
        abs_mag_shift=abs_mag_shift,
        logr50_phys_std=0.3,
        logr50_phys_mean_slope=-0.2,
        logr50_phys_mean_intcpt=1.0,
        logr50_alpha=0.0,
        z=np.full(n_gal, 0.5),
    )

    assert len(r50_phys) == n_gal
    assert np.all(r50_phys > 0)  # Physical sizes must be positive
    assert np.all(np.isfinite(r50_phys))

    # Test with zero scatter (deterministic result)
    abs_mag_shift_det = np.array([0, 1, -1])
    r50_phys_det = sample_r50_phys(
        abs_mag_shift=abs_mag_shift_det,
        logr50_phys_std=0.0,  # No scatter
        logr50_phys_mean_slope=-0.3,
        logr50_phys_mean_intcpt=1.0,
        logr50_alpha=0.0,
        z=np.zeros(len(abs_mag_shift_det)),
    )

    # With no scatter, should follow the exact relation
    expected = np.exp(abs_mag_shift_det * -0.3 + 1.0)
    np.testing.assert_allclose(r50_phys_det, expected, rtol=1e-10)
