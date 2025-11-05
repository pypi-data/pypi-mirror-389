"""
Created on July 31, 2018
author: Joerg Herbel
adapted and extended by: Silvan Fischbacher
"""

import os

import h5py
import healpy as hp
import ivy
import numpy as np
import pytest
from cosmo_torrent import data_path
from scipy import integrate, interpolate
from ufig import coordinate_util

from galsbi.ucat import galaxy_sampling_util, spectrum_util
from galsbi.ucat.magnitude_calculator import speed_of_light_c_in_micrometer_per_sec
from galsbi.ucat.plugins import sample_galaxies, sample_galaxies_photo


@pytest.fixture
def ctx():
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )
    ctx.parameters.filters = ["g", "r"]
    ctx.parameters.filters_full_names = {
        "B": "SuprimeCam_B",
        "g": "HSC_g",
        "r": "HSC_r2",
    }
    ctx.parameters.maps_remote_dir = os.getcwd()
    ctx.parameters.size_x = 100
    ctx.parameters.size_y = 100
    ctx.parameters.lum_fct_filter_band = "B"
    ctx.parameters.lum_fct_m_max = -15
    ctx.parameters.reference_band = "r"
    ctx.parameters.magnitude_calculation = "direct"
    ctx.parameters.templates_file_name = os.path.join(
        os.getcwd(), "template_spectra.h5"
    )
    ctx.parameters.filters_file_name = os.path.join(os.getcwd(), "filters.h5")
    ctx.parameters.templates_int_tables_file_name = os.path.join(
        os.getcwd(), "template_integrals.h5"
    )
    ctx.parameters.extinction_map_file_name = None
    return ctx


def create_template_spetra_file(filepath):
    template_lam = np.linspace(1000, 20000, num=20000)
    template_amp = np.full((5, template_lam.size), 1e-5)

    with h5py.File(filepath, mode="w") as f:
        f.create_dataset(name="wavelength", data=template_lam)
        f.create_dataset(name="amplitudes", data=template_amp)

    return template_lam, template_amp


def create_filter_bands_file(filepath=None):
    filter_lam = np.linspace(3000, 10000, num=1000)
    filter_b_throughput = np.zeros_like(filter_lam)
    filter_b_throughput[(filter_lam > 4000) & (filter_lam < 4500)] = 1
    filter_g_throughput = np.zeros_like(filter_lam)
    filter_g_throughput[(filter_lam > 4500) & (filter_lam < 5000)] = 1
    filter_r_throughput = np.zeros_like(filter_lam)
    filter_r_throughput[(filter_lam > 7500) & (filter_lam < 8000)] = 1

    filters = {
        "SuprimeCam_B": filter_b_throughput,
        "HSC_g": filter_g_throughput,
        "HSC_r2": filter_r_throughput,
    }
    if filepath is not None:
        with h5py.File(filepath, mode="w") as f:
            for filter_name in filters:
                grp = f.create_group(name=filter_name)
                grp.create_dataset(name="lam", data=filter_lam)
                grp.create_dataset(name="amp", data=filters[filter_name])

    return filter_lam, filter_b_throughput, filter_g_throughput, filter_r_throughput


def create_table_file(
    par,
    template_lam,
    template_amp,
    filter_lam,
    filter_b_throughput,
    filter_g_throughput,
    filter_r_throughput,
):
    filter_b_intp = interpolate.interp1d(
        filter_lam * 1e-4,
        filter_b_throughput,
        kind="cubic",
        bounds_error=False,
        fill_value=0,
    )
    filter_g_intp = interpolate.interp1d(
        filter_lam * 1e-4,
        filter_g_throughput,
        kind="cubic",
        bounds_error=False,
        fill_value=0,
    )
    filter_r_intp = interpolate.interp1d(
        filter_lam * 1e-4,
        filter_r_throughput,
        kind="cubic",
        bounds_error=False,
        fill_value=0,
    )
    z_grid = np.array([0, 1, 2])
    excess_b_v_grid = np.array([0.0])

    int_tables_filter_b = [
        np.empty((z_grid.size, excess_b_v_grid.size), dtype=np.float32)
        for _ in range(template_amp.shape[0])
    ]
    int_tables_filter_g = [
        np.empty((z_grid.size, excess_b_v_grid.size), dtype=np.float32)
        for _ in range(template_amp.shape[0])
    ]

    int_tables_filter_r = [
        np.empty((z_grid.size, excess_b_v_grid.size), dtype=np.float32)
        for _ in range(template_amp.shape[0])
    ]

    extinction_spline = spectrum_util.spline_ext_coeff()

    for z_ind in range(z_grid.size):
        lam = template_lam * (1 + z_grid[z_ind]) * 1e-4
        filter_b_throughput_intp = filter_b_intp(lam)
        filter_g_throughput_intp = filter_g_intp(lam)
        filter_r_throughput_intp = filter_r_intp(lam)

        for ebv_ind in range(excess_b_v_grid.size):
            for template_ind in range(template_amp.shape[0]):
                spec = template_amp[template_ind] * 1e4 * lam
                spec = spec.reshape(-1, spec.size)
                spectrum_util.apply_extinction(
                    spec, lam, excess_b_v_grid[ebv_ind], extinction_spline
                )
                spec = spec[0]
                # TODO: Check if the normalization is correct
                b = integrate.simpson(spec * filter_b_throughput_intp, x=lam)
                b /= (
                    integrate.simpson(filter_b_throughput_intp / lam, x=lam)
                    * speed_of_light_c_in_micrometer_per_sec
                )
                g = integrate.simpson(spec * filter_g_throughput_intp, x=lam)
                g /= (
                    integrate.simpson(filter_g_throughput_intp / lam, x=lam)
                    * speed_of_light_c_in_micrometer_per_sec
                )
                int_tables_filter_g[template_ind][z_ind, ebv_ind] = g
                r = integrate.simpson(spec * filter_r_throughput_intp, x=lam)
                r /= (
                    integrate.simpson(filter_r_throughput_intp / lam, x=lam)
                    * speed_of_light_c_in_micrometer_per_sec
                )
                int_tables_filter_r[template_ind][z_ind, ebv_ind] = r
    with h5py.File(par.templates_int_tables_file_name, mode="w") as f:
        f.create_dataset(name="z", data=z_grid)
        f.create_dataset(name="E(B-V)", data=excess_b_v_grid)

        for i in range(template_amp.shape[0]):
            f.create_dataset(
                name=f"integrals/SuprimeCam_B/template_{i}",
                data=int_tables_filter_b[i],
            )
            f.create_dataset(
                name=f"integrals/HSC_g/template_{i}",
                data=int_tables_filter_g[i],
            )
            f.create_dataset(
                name=f"integrals/HSC_r2/template_{i}",
                data=int_tables_filter_r[i],
            )
    return z_grid, excess_b_v_grid


def test_magnitude_calculation(ctx):
    """
    Test the computation of magnitudes from redshifts, E(B-V) values and template
    coefficients. The test defines some arbitrary templates and filter bands. It then
    computes magnitudes in two ways: by direct integration and by setting up template
    integration tables. The results are required to agree to the 0.5% level for the test
    to pass.
    """

    par = ctx.parameters

    # Create template spectra file
    template_lam, template_amp = create_template_spetra_file(par.templates_file_name)

    # Create filter bands
    (
        filter_lam,
        filter_b_throughput,
        filter_g_throughput,
        filter_r_throughput,
    ) = create_filter_bands_file(par.filters_file_name)

    # Create table
    z_grid, excess_b_v_grid = create_table_file(
        par,
        template_lam,
        template_amp,
        filter_lam,
        filter_b_throughput,
        filter_g_throughput,
        filter_r_throughput,
    )

    # Define some template coefficients
    template_coeffs = np.random.uniform(
        low=0.0,
        high=1.0,
        size=(z_grid.size * excess_b_v_grid.size, template_amp.shape[0]),
    )
    # Setup magnitude calculators
    filters = ["g", "r"]
    par.filters_full_names = {"g": "HSC_g", "r": "HSC_r2"}

    mag_calc_direct = sample_galaxies_photo.get_magnitude_calculator_direct(
        filters, par
    )
    mag_calc_table = sample_galaxies_photo.get_magnitude_calculator_table(filters, par)

    # Compute magnitudes
    z_meshgrid, excess_b_v_meshgrid = np.meshgrid(z_grid, excess_b_v_grid)
    z_meshgrid = np.ravel(z_meshgrid)
    excess_b_v_meshgrid = np.ravel(excess_b_v_meshgrid)
    mag_direct = mag_calc_direct(
        redshifts=z_meshgrid,
        excess_b_v=excess_b_v_meshgrid,
        coeffs=template_coeffs,
        filter_names=filters,
    )
    mag_table = mag_calc_table(
        redshifts=z_meshgrid,
        excess_b_v=excess_b_v_meshgrid,
        coeffs=template_coeffs,
        filter_names=filters,
    )
    for band in mag_direct:
        assert np.allclose(mag_direct[band], mag_table[band], rtol=0.005)

    # Clean up
    os.remove(par.templates_file_name)
    os.remove(par.templates_int_tables_file_name)


def test_sample_galaxies(ctx):
    """
    Test the plugin plugins.sample_galaxies. The code runs the plugin and performs a
    few simple checks on the output.
    """

    par = ctx.parameters
    par.galaxy_count_prior = {"band": "g", "mag_max": 24, "n_min": 0, "n_max": 20000}

    # Create template spectra file
    create_template_spetra_file(par.templates_file_name)

    # Create filter bands file
    create_filter_bands_file(filepath=par.filters_file_name)

    # Run plugin
    sample_galaxies.Plugin(ctx)()

    # Tests
    for col_name in ctx.galaxies.columns:
        col = getattr(ctx.galaxies, col_name)
        assert len(col) == ctx.numgalaxies

    assert np.all(ctx.galaxies.excess_b_v == 0)

    assert sorted(ctx.galaxies.magnitude_dict.keys()) == sorted(par.filters)

    for band in par.filters:
        assert len(ctx.galaxies.int_magnitude_dict[band]) == ctx.numgalaxies
        assert np.array_equal(
            ctx.galaxies.int_magnitude_dict[band], ctx.galaxies.magnitude_dict[band]
        )

    # Clean up
    os.remove(par.templates_file_name)
    os.remove(par.filters_file_name)


def test_sampling_table(ctx):
    par = ctx.parameters

    par.templates_int_tables_file_name = os.path.join(
        data_path("HSC_tables"), "HSC_template_integrals_yfix.h5"
    )

    par.magnitude_calculation = "table"
    sample_galaxies_photo.Plugin(ctx)()

    for col_name in ctx.galaxies.columns:
        col = getattr(ctx.galaxies, col_name)
        assert len(col) == ctx.numgalaxies

    assert np.all(ctx.galaxies.excess_b_v == 0)

    assert sorted(ctx.galaxies.magnitude_dict.keys()) == sorted(par.filters)

    for band in par.filters:
        assert len(ctx.galaxies.int_magnitude_dict[band]) == ctx.numgalaxies
        assert np.array_equal(
            ctx.galaxies.int_magnitude_dict[band], ctx.galaxies.magnitude_dict[band]
        )


def test_ngal_multiplier(ctx):
    """
    Test the plugin plugins.sample_galaxies with the ngal_multiplier parameter set to 2.
    The code runs the plugin and performs a few simple checks on the output.
    """

    par = ctx.parameters
    par.ngal_multiplier = 1

    # Create template spectra file
    create_template_spetra_file(par.templates_file_name)

    # Create filter bands file
    create_filter_bands_file(filepath=par.filters_file_name)

    # Run plugin
    sample_galaxies.Plugin(ctx)()
    n_gal1 = len(ctx.galaxies.int_magnitude_dict[par.filters[0]])

    par.ngal_multiplier = 2
    # Run plugin
    sample_galaxies.Plugin(ctx)()
    n_gal2 = len(ctx.galaxies.int_magnitude_dict[par.filters[0]])

    par.ngal_multiplier = 0.1
    # Run plugin
    sample_galaxies.Plugin(ctx)()
    n_gal3 = len(ctx.galaxies.int_magnitude_dict[par.filters[0]])

    assert n_gal1 < n_gal2
    assert n_gal1 > n_gal3

    # Clean up
    os.remove(par.templates_file_name)
    os.remove(par.filters_file_name)


def test_lumfunc_parametrizations(ctx):
    """
    Test the plugin plugins.sample_galaxies with different luminosity function
    parametrizations. The code runs the plugin and performs a few simple checks on the
    output.
    """

    par = ctx.parameters

    # Create template spectra file
    create_template_spetra_file(par.templates_file_name)

    # Create filter bands file
    create_filter_bands_file(filepath=par.filters_file_name)

    # Run plugin with logpower
    par.lum_fct_parametrization = "logpower"
    sample_galaxies.Plugin(ctx)()

    # Tests
    for col_name in ctx.galaxies.columns:
        col = getattr(ctx.galaxies, col_name)
        assert len(col) == ctx.numgalaxies

    assert np.all(ctx.galaxies.excess_b_v == 0)

    assert sorted(ctx.galaxies.magnitude_dict.keys()) == sorted(par.filters)

    for band in par.filters:
        assert len(ctx.galaxies.int_magnitude_dict[band]) == ctx.numgalaxies
        assert np.array_equal(
            ctx.galaxies.int_magnitude_dict[band], ctx.galaxies.magnitude_dict[band]
        )

    # Run plugin with truncated_logexp
    par.lum_fct_parametrization = "truncated_logexp"
    sample_galaxies.Plugin(ctx)()

    # Tests
    for col_name in ctx.galaxies.columns:
        col = getattr(ctx.galaxies, col_name)
        assert len(col) == ctx.numgalaxies

    assert np.all(ctx.galaxies.excess_b_v == 0)

    assert sorted(ctx.galaxies.magnitude_dict.keys()) == sorted(par.filters)

    for band in par.filters:
        assert len(ctx.galaxies.int_magnitude_dict[band]) == ctx.numgalaxies
        assert np.array_equal(
            ctx.galaxies.int_magnitude_dict[band], ctx.galaxies.magnitude_dict[band]
        )

    # Clean up
    os.remove(par.templates_file_name)
    os.remove(par.filters_file_name)


def test_extinction_map_evaluater(ctx):
    par = ctx.parameters
    Extinction = sample_galaxies_photo.ExtinctionMapEvaluator(par)
    wcs = coordinate_util.wcs_from_parameters(par)
    x = 0
    y = 0
    ebv = Extinction(wcs, x, y)
    assert ebv == 0

    ctx.parameters.extinction_map_file_name = os.path.join(
        os.path.dirname(__file__), "../../resources/lambda_sfd_ebv.fits"
    )
    par = ctx.parameters
    Extinction = sample_galaxies_photo.ExtinctionMapEvaluator(par)
    ebv = Extinction(wcs, x, y)
    assert ebv != 0


def test_extinction_map_evaluater_healpix_sampling(ctx):
    par = ctx.parameters
    par.sampling_mode = "healpix"
    par.healpix_map = np.zeros(hp.nside2npix(2048))
    par.healpix_map[0] = 1
    Extinction = sample_galaxies_photo.ExtinctionMapEvaluator(par)
    wcs = None
    ra = 0
    dec = 0
    ebv = Extinction(wcs, ra, dec)
    assert ebv == 0

    ctx.parameters.extinction_map_file_name = os.path.join(
        os.path.dirname(__file__), "../../resources/lambda_sfd_ebv.fits"
    )
    par = ctx.parameters
    Extinction = sample_galaxies_photo.ExtinctionMapEvaluator(par)
    ebv = Extinction(wcs, ra, dec)
    assert ebv != 0


def test_healpix_sampling(ctx):
    par = ctx.parameters
    par.sampling_mode = "healpix"

    # Create template spectra file
    create_template_spetra_file(par.templates_file_name)

    # Create filter bands file
    create_filter_bands_file(filepath=par.filters_file_name)

    # Run plugin
    with pytest.raises(ValueError):
        sample_galaxies.Plugin(ctx)()

    nside = 2048
    par.healpix_map = np.zeros(hp.nside2npix(nside))

    w = coordinate_util.wcs_from_parameters(par)
    pixels = coordinate_util.get_healpix_pixels(nside, w, par.size_x, par.size_y)
    par.healpix_map[pixels] = 1

    sample_galaxies.Plugin(ctx)()

    assert hasattr(ctx.galaxies, "ra")
    assert hasattr(ctx.galaxies, "dec")
    z1 = ctx.galaxies.z

    par = ctx.parameters
    par.sampling_mode = "wcs"
    par.nside_sampling = nside
    sample_galaxies.Plugin(ctx)()
    z2 = ctx.galaxies.z

    # no cutting of galaxies due to image size
    assert len(z1) > len(z2)
    # galaxy population is the same
    mean1 = np.mean(z1)
    mean2 = np.mean(z2)
    std1 = np.std(z1)
    std2 = np.std(z2)
    n1 = len(z1)
    n2 = len(z2)

    exp_diff = np.sqrt((std1**2 / n1) + (std2**2 / n2))
    assert np.abs(mean1 - mean2) < 3 * exp_diff

    # Clean up
    os.remove(par.templates_file_name)
    os.remove(par.filters_file_name)


def test_wrong_sampling_mode(ctx):
    par = ctx.parameters
    par.sampling_mode = "unknown"
    with pytest.raises(ValueError):
        sample_galaxies.Plugin(ctx)()


def test_n_gal_error(ctx):
    par = ctx.parameters
    par.galaxy_count_prior = {"band": "g", "mag_max": 24, "n_min": 0, "n_max": 0}
    par.raise_max_num_gal_error = True

    # Create template spectra file
    create_template_spetra_file(par.templates_file_name)

    # Create filter bands file
    create_filter_bands_file(filepath=par.filters_file_name)

    with pytest.raises(galaxy_sampling_util.UCatNumGalError):
        sample_galaxies.Plugin(ctx)()

    par.galaxy_count_prior = {"band": "g", "mag_max": 24, "n_min": 0, "n_max": np.inf}
    par.n_gal_max_blue = 0
    par.raise_max_num_gal_error = False
    sample_galaxies.Plugin(ctx)()

    par.raise_max_num_gal_error = True
    with pytest.raises(galaxy_sampling_util.UCatNumGalError):
        sample_galaxies.Plugin(ctx)()

    # Clean up
    os.remove(par.templates_file_name)
    os.remove(par.filters_file_name)


def test_mem_error(ctx):
    par = ctx.parameters
    par.max_memlimit_gal_catalog = -1
    with pytest.raises(galaxy_sampling_util.UCatNumGalError):
        plugin = sample_galaxies_photo.Plugin(ctx)
        plugin.check_max_mem_error(par)


def test_in_pos():
    """Test the in_pos function from sample_galaxies_photo."""
    from galsbi.ucat.plugins.sample_galaxies_photo import in_pos

    # Create mock parameters
    class MockParams:
        size_x = 100
        size_y = 100

    par = MockParams()

    # Test positions inside bounds
    assert in_pos(50, 50, par)
    assert in_pos(1, 1, par)  # Changed from (0,0) - boundary condition
    assert in_pos(99, 99, par)

    # Test positions outside bounds
    assert not in_pos(0, 50, par)  # On boundary - should be False
    assert not in_pos(-1, 50, par)
    assert not in_pos(50, -1, par)
    assert not in_pos(100, 50, par)
    assert not in_pos(50, 100, par)


def test_sample_galaxies_photo_str_method():
    """Test the __str__ method of sample_galaxies_photo Plugin."""
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )
    plugin = sample_galaxies_photo.Plugin(ctx)
    assert str(plugin) == "sample gal photo"
