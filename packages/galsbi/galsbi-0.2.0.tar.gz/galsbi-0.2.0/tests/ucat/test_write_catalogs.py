# Copyright (C) 2024 ETH Zurich
# Institute for Particle Physics and Astrophysics
# Author: Silvan Fischbacher
# created: Wed Jul 31 2024


import os

import h5py
import ivy
import numpy as np
from cosmic_toolbox import arraytools as at

from galsbi.ucat import galaxy_sampling_util
from galsbi.ucat.plugins import write_catalog, write_catalog_photo


def test_write_catalogs():
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )
    columns = ["x", "y", "z"]
    ctx.galaxies = galaxy_sampling_util.Catalog()
    ctx.galaxies.columns = columns
    gal = {}
    ctx.stars = galaxy_sampling_util.Catalog()
    ctx.stars.columns = columns
    star = {}

    for c in columns:
        setattr(ctx.galaxies, c, np.zeros(5))
        gal[c] = np.zeros(5)
        setattr(ctx.stars, c, np.ones(5))
        star[c] = np.ones(5)
    gal = at.dict2rec(gal)
    star = at.dict2rec(star)
    write_catalog.Plugin(ctx)()

    par = ctx.parameters
    gal_cat = at.load_hdf(par.galaxy_catalog_name)
    assert np.all(gal_cat == gal)
    star_cat = at.load_hdf(par.star_catalog_name)
    assert np.all(star_cat == star)
    os.remove(par.galaxy_catalog_name)
    os.remove(par.star_catalog_name)


def test_write_catalog_photo():
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )
    ctx.parameters.filepath_tile = "test/"
    ctx.parameters.filters = ["g", "r"]
    columns = ["z", "z_noisy", "galaxy_type", "template_coeffs", "template_coeffs_abs"]
    ctx.galaxies = galaxy_sampling_util.Catalog()
    ctx.galaxies.columns = columns
    gal = {}
    for c in columns:
        setattr(ctx.galaxies, c, np.zeros(5))
        gal[c] = np.zeros(5)
    ctx.galaxies.int_magnitude_dict = {"g": np.zeros(5), "r": np.zeros(5)}
    ctx.galaxies.abs_magnitude_dict = {"g": np.zeros(5), "r": np.zeros(5)}
    ctx.galaxies.magnitude_dict = {"g": np.zeros(5), "r": np.zeros(5)}
    gal = at.dict2rec(gal)
    write_catalog_photo.Plugin(ctx)()

    par = ctx.parameters
    filepath = os.path.join(
        par.filepath_tile,
        write_catalog_photo.get_ucat_catalog_filename(),
    )
    with h5py.File(filepath, "r") as fh5:
        for col in columns:
            assert np.all(fh5[col][:] == gal[col])
        for b in par.filters:
            assert np.all(fh5[f"int_mag_{b}"][:] == np.zeros(5))
            assert np.all(fh5[f"abs_mag_{b}"][:] == np.zeros(5))
            assert np.all(fh5[f"mag_{b}"][:] == np.zeros(5))

    os.remove(filepath)


def test_write_catalog_photo_str_method():
    """Test the __str__ method of the write_catalog_photo plugin."""
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )
    plugin = write_catalog_photo.Plugin(ctx)
    assert str(plugin) == "write ucat photo to file"


def test_write_catalogs_with_seds():
    """Test writing catalogs with SED data when save_SEDs is enabled."""
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )

    # Enable SED saving
    ctx.parameters.save_SEDs = True
    ctx.parameters.galaxy_sed_catalog_name = "test_sed_catalog.h5"

    # Create galaxy catalog with SED data
    columns = ["id", "z", "sed"]
    ctx.galaxies = galaxy_sampling_util.Catalog()
    ctx.galaxies.columns = columns

    n_gal = 3
    n_wavelengths = 50

    # Set up galaxy data
    ctx.galaxies.id = np.arange(n_gal, dtype=np.int32)
    ctx.galaxies.z = np.array([0.1, 0.5, 1.0], dtype=np.float32)
    ctx.galaxies.sed = np.random.uniform(0.1, 1.0, (n_gal, n_wavelengths)).astype(
        np.float32
    )

    # Create wavelength array
    ctx.restframe_wavelength_for_SED = np.linspace(3000, 8000, n_wavelengths)

    write_catalog.Plugin(ctx)()

    # Check that SED catalog was created
    assert os.path.exists(ctx.parameters.galaxy_sed_catalog_name)

    # Verify SED file contents
    with h5py.File(ctx.parameters.galaxy_sed_catalog_name, "r") as f:
        assert "data" in f
        assert "restframe_wavelength_in_A" in f

        data = f["data"][:]
        wavelengths = f["restframe_wavelength_in_A"][:]

        # Check data structure
        assert len(data) == n_gal
        assert "id" in data.dtype.names
        assert "z" in data.dtype.names
        assert "sed" in data.dtype.names

        # Check wavelength array
        np.testing.assert_array_equal(wavelengths, ctx.restframe_wavelength_for_SED)

    # Clean up
    os.remove(ctx.parameters.galaxy_catalog_name)
    os.remove(ctx.parameters.galaxy_sed_catalog_name)


def test_write_catalogs_seds_disabled():
    """Test that SED catalog is not created when save_SEDs is False."""
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )

    # Ensure SED saving is disabled
    ctx.parameters.save_SEDs = False
    ctx.parameters.galaxy_sed_catalog_name = "test_sed_catalog_disabled.h5"

    # Create galaxy catalog with SED data
    columns = ["id", "z", "sed"]
    ctx.galaxies = galaxy_sampling_util.Catalog()
    ctx.galaxies.columns = columns

    ctx.galaxies.id = np.array([1, 2], dtype=np.int32)
    ctx.galaxies.z = np.array([0.1, 0.5], dtype=np.float32)
    ctx.galaxies.sed = np.random.uniform(0.1, 1.0, (2, 10)).astype(np.float32)

    # Create wavelength array
    ctx.restframe_wavelength_for_SED = np.linspace(3000, 8000, 10)

    write_catalog.Plugin(ctx)()

    # Check that SED catalog was NOT created
    assert not os.path.exists(ctx.parameters.galaxy_sed_catalog_name)

    # Clean up
    os.remove(ctx.parameters.galaxy_catalog_name)


def test_write_catalogs_reference_band_logic():
    """Test that SEDs are only saved when current_filter matches reference_band."""
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )

    # Enable SED saving and set reference band
    ctx.parameters.save_SEDs = True
    ctx.parameters.reference_band = "i"
    ctx.parameters.galaxy_sed_catalog_name = "test_sed_ref_band.h5"

    # Create minimal galaxy catalog
    columns = ["id", "z", "sed"]
    ctx.galaxies = galaxy_sampling_util.Catalog()
    ctx.galaxies.columns = columns

    ctx.galaxies.id = np.array([1], dtype=np.int32)
    ctx.galaxies.z = np.array([0.5], dtype=np.float32)
    ctx.galaxies.sed = np.random.uniform(0.1, 1.0, (1, 10)).astype(np.float32)

    ctx.restframe_wavelength_for_SED = np.linspace(3000, 8000, 10)

    # Test 1: current_filter matches reference_band - should save SEDs
    ctx.current_filter = "i"
    write_catalog.Plugin(ctx)()
    assert os.path.exists(ctx.parameters.galaxy_sed_catalog_name)
    os.remove(ctx.parameters.galaxy_sed_catalog_name)
    os.remove(ctx.parameters.galaxy_catalog_name)

    # Test 2: current_filter doesn't match reference_band - should not save SEDs
    ctx.current_filter = "g"
    write_catalog.Plugin(ctx)()
    assert not os.path.exists(ctx.parameters.galaxy_sed_catalog_name)
    os.remove(ctx.parameters.galaxy_catalog_name)


def test_write_catalog_str_method():
    """Test the __str__ method of the write_catalog plugin."""
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )
    plugin = write_catalog.Plugin(ctx)
    assert str(plugin) == "write ucat catalog to file"


def test_catalog_to_rec_with_1d_column_arrays():
    """Test catalog_to_rec with 1D column arrays (shape[1] == 1)."""
    from galsbi.ucat.plugins.write_catalog import catalog_to_rec

    catalog = galaxy_sampling_util.Catalog()
    catalog.columns = ["id", "single_val"]

    # Regular 1D array
    catalog.id = np.array([1, 2, 3], dtype=np.int32)

    # 2D array with shape (3, 1) - should trigger the elif branch at line 41
    catalog.single_val = np.array([[1.5], [2.5], [3.5]], dtype=np.float32)

    rec = catalog_to_rec(catalog)

    # Check that 2D array with shape[1]==1 gets raveled
    assert rec["single_val"].shape == (3,)  # Should be flattened
    np.testing.assert_array_equal(rec["single_val"], [1.5, 2.5, 3.5])
    np.testing.assert_array_equal(rec["id"], [1, 2, 3])


def test_get_ucat_catalog_filename():
    """Test the get_ucat_catalog_filename utility function from write_catalog_photo."""
    from galsbi.ucat.plugins.write_catalog_photo import get_ucat_catalog_filename

    # Test basic function call - this should hit line 18 in write_catalog_photo.py
    result = get_ucat_catalog_filename()
    assert result == "ucat_photo.h5"
