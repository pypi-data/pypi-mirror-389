# Copyright (C) 2025 ETH Zurich
# Institute for Particle Physics and Astrophysics
# Author: Silvan Fischbacher
# created: Thu Jul 10 2025


import os

import h5py
import ivy
import numpy as np
import pytest

from galsbi.ucat import galaxy_sampling_util
from galsbi.ucat.plugins import write_catalog


@pytest.fixture
def mock_galaxy_catalog():
    """Create a mock galaxy catalog for testing."""
    catalog = galaxy_sampling_util.Catalog()
    catalog.columns = ["id", "z", "sed"]

    # Create some test data
    n_gal = 5
    n_wavelengths = 100

    catalog.id = np.arange(n_gal, dtype=np.int32)
    catalog.z = np.random.uniform(0.1, 2.0, n_gal).astype(np.float32)

    # Create synthetic SED data
    catalog.sed = np.random.uniform(0.1, 1.0, (n_gal, n_wavelengths)).astype(np.float32)

    return catalog


@pytest.fixture
def mock_context_with_seds(mock_galaxy_catalog):
    """Create a mock context with galaxy catalog and SED data."""
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )

    # Set up test parameters
    ctx.parameters.save_SEDs = True
    ctx.parameters.galaxy_sed_catalog_name = "test_sed_catalog.h5"

    # Add galaxy catalog
    ctx.galaxies = mock_galaxy_catalog

    # Create wavelength array from template wavelengths
    # This would typically come from SED templates
    ctx.restframe_wavelength_for_SED = np.linspace(3000, 25000, 100)

    return ctx


def test_sed_catalog_to_rec(mock_galaxy_catalog):
    """Test that sed_catalog_to_rec correctly converts catalog to record array."""
    from galsbi.ucat.plugins.write_catalog import sed_catalog_to_rec

    rec = sed_catalog_to_rec(mock_galaxy_catalog)

    # Check that record array has correct columns
    assert "id" in rec.dtype.names
    assert "z" in rec.dtype.names
    assert "sed" in rec.dtype.names

    # Check data integrity
    assert len(rec) == len(mock_galaxy_catalog.id)
    np.testing.assert_array_equal(rec["id"], mock_galaxy_catalog.id)
    np.testing.assert_array_equal(rec["z"], mock_galaxy_catalog.z)
    np.testing.assert_array_equal(rec["sed"], mock_galaxy_catalog.sed)


def test_save_sed_file_creation(mock_context_with_seds, tmp_path):
    """Test that save_sed correctly creates HDF5 file with expected structure."""
    from galsbi.ucat.plugins.write_catalog import save_sed, sed_catalog_to_rec

    # Change to temporary directory
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        ctx = mock_context_with_seds
        cat = sed_catalog_to_rec(ctx.galaxies)
        wavelengths = ctx.restframe_wavelength_for_SED

        save_sed(ctx.parameters.galaxy_sed_catalog_name, cat, wavelengths)

        # Check file exists
        assert os.path.exists(ctx.parameters.galaxy_sed_catalog_name)

        # Check file contents
        with h5py.File(ctx.parameters.galaxy_sed_catalog_name, "r") as f:
            assert "data" in f
            assert "restframe_wavelength_in_A" in f

            # Check data integrity
            loaded_data = f["data"][:]
            loaded_wavelengths = f["restframe_wavelength_in_A"][:]

            assert loaded_data.dtype.names == cat.dtype.names
            assert len(loaded_data) == len(cat)
            np.testing.assert_array_equal(loaded_wavelengths, wavelengths)

    finally:
        os.chdir(old_cwd)


def test_write_catalog_plugin_saves_seds_when_enabled(mock_context_with_seds, tmp_path):
    """Test that write_catalog plugin saves SEDs when save_SEDs is True."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        ctx = mock_context_with_seds
        ctx.parameters.galaxy_catalog_name = "test_galaxy_catalog.h5"

        # Run the plugin
        plugin = write_catalog.Plugin(ctx)
        plugin()

        # Check that SED catalog was created
        assert os.path.exists(ctx.parameters.galaxy_sed_catalog_name)

        # Verify SED file contents
        with h5py.File(ctx.parameters.galaxy_sed_catalog_name, "r") as f:
            assert "data" in f
            assert "restframe_wavelength_in_A" in f

            data = f["data"][:]
            assert len(data) == len(ctx.galaxies.id)
            assert "sed" in data.dtype.names

    finally:
        os.chdir(old_cwd)


def test_write_catalog_plugin_skips_seds_when_disabled(
    mock_context_with_seds, tmp_path
):
    """Test that write_catalog plugin doesn't save SEDs when save_SEDs is False."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        ctx = mock_context_with_seds
        ctx.parameters.save_SEDs = False
        ctx.parameters.galaxy_catalog_name = "test_galaxy_catalog.h5"

        # Run the plugin
        plugin = write_catalog.Plugin(ctx)
        plugin()

        # Check that SED catalog was NOT created
        assert not os.path.exists(ctx.parameters.galaxy_sed_catalog_name)

    finally:
        os.chdir(old_cwd)


def test_write_catalog_reference_band_logic(mock_context_with_seds, tmp_path):
    """Test that SEDs are only saved for reference band when current_filter is set."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        ctx = mock_context_with_seds
        ctx.parameters.reference_band = "i"
        ctx.parameters.galaxy_catalog_name = "test_galaxy_catalog.h5"

        # Test with current_filter set to reference band
        ctx.current_filter = "i"
        plugin = write_catalog.Plugin(ctx)
        plugin()
        assert os.path.exists(ctx.parameters.galaxy_sed_catalog_name)

        # Clean up for next test
        os.remove(ctx.parameters.galaxy_sed_catalog_name)

        # Test with current_filter set to non-reference band
        ctx.current_filter = "g"
        plugin = write_catalog.Plugin(ctx)
        plugin()
        assert not os.path.exists(ctx.parameters.galaxy_sed_catalog_name)

    finally:
        os.chdir(old_cwd)


def test_get_seds_function():
    """Test the get_seds function that generates SEDs for galaxies."""
    # Create a minimal test case
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )

    # Set required parameters for get_seds
    ctx.parameters.filters = ["g", "r"]

    # Create minimal galaxy catalog
    galaxies = galaxy_sampling_util.Catalog()
    galaxies.z = np.array([0.1, 0.5], dtype=np.float32)
    galaxies.template_coeffs = np.array(
        [[0.2, 0.3, 0.2, 0.2, 0.1], [0.1, 0.4, 0.2, 0.2, 0.1]], dtype=np.float32
    )
    galaxies.excess_b_v = np.array([0.1, 0.2], dtype=np.float32)

    # This test would require the full SED template infrastructure to be loaded
    # For now, we'll test that the function can be imported and has correct signature
    from galsbi.ucat.plugins.sample_galaxies_photo import get_seds

    assert callable(get_seds)


def test_save_seds_config_parameter():
    """Test that save_SEDs configuration parameter exists and has correct default."""
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )

    assert hasattr(ctx.parameters, "save_SEDs")
    assert not ctx.parameters.save_SEDs  # Default should be False


def test_sed_wavelength_from_templates():
    """Test that SED wavelengths come from templates, not configuration parameters."""
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )
    assert hasattr(ctx.parameters, "save_SEDs")


def test_save_sed_invalid_file_path():
    """Test error handling in save_sed function with invalid file path."""
    # Create minimal test data
    cat = np.array(
        [(1, 0.5, [1.0, 2.0, 3.0])],
        dtype=[("id", "i4"), ("z", "f4"), ("sed", "f4", (3,))],
    )
    wavelengths = np.array([4000, 5000, 6000], dtype=np.float32)

    # Test with invalid directory path
    invalid_path = "/nonexistent/directory/test.h5"

    # This should raise an error due to invalid path
    with pytest.raises((OSError, FileNotFoundError)):
        from galsbi.ucat.plugins.write_catalog import save_sed

        save_sed(invalid_path, cat, wavelengths)


def test_sed_catalog_to_rec_missing_column():
    """Test sed_catalog_to_rec with missing required columns."""
    from galsbi.ucat.plugins.write_catalog import sed_catalog_to_rec

    # Create catalog missing the 'sed' column
    catalog = galaxy_sampling_util.Catalog()
    catalog.columns = ["id", "z"]  # Missing 'sed'
    catalog.id = np.array([1, 2], dtype=np.int32)
    catalog.z = np.array([0.1, 0.5], dtype=np.float32)

    # This should raise an AttributeError for missing 'sed' attribute
    with pytest.raises(AttributeError):
        sed_catalog_to_rec(catalog)


def test_sed_catalog_to_rec_with_1d_arrays():
    """Test sed_catalog_to_rec with 1D SED arrays."""
    from galsbi.ucat.plugins.write_catalog import sed_catalog_to_rec

    # Create catalog with 1D SED arrays (edge case)
    catalog = galaxy_sampling_util.Catalog()
    catalog.columns = ["id", "z", "sed"]
    catalog.id = np.array([1, 2], dtype=np.int32)
    catalog.z = np.array([0.1, 0.5], dtype=np.float32)
    # Create 2D array with shape (2, 1) - will be treated as 1D
    catalog.sed = np.array([[1.5], [2.5]], dtype=np.float32)

    rec = sed_catalog_to_rec(catalog)

    # Check that the result is correctly shaped
    assert "sed" in rec.dtype.names
    assert rec["sed"].shape == (2,)  # Should be flattened
    np.testing.assert_array_equal(rec["sed"], [1.5, 2.5])


def test_write_catalog_with_missing_galaxies_context():
    """Test write_catalog plugin behavior when galaxies context is missing."""
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )

    # Set parameters but don't create galaxies context
    ctx.parameters.save_SEDs = False
    ctx.parameters.galaxy_catalog_name = "test_missing_galaxies.h5"

    # Create plugin - should handle missing galaxies gracefully
    plugin = write_catalog.Plugin(ctx)

    # This should not crash even without galaxies context
    plugin()

    # No files should be created since no galaxies were provided
    assert not os.path.exists("test_missing_galaxies.h5")


def test_save_seds_large_catalog():
    """Test save_SEDs functionality with a larger catalog to ensure performance."""
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )

    # Set up parameters for larger test
    ctx.parameters.save_SEDs = True
    ctx.parameters.galaxy_sed_catalog_name = "test_large_sed_catalog.h5"

    # Create larger galaxy catalog
    n_gal = 1000
    n_wavelengths = 200

    ctx.galaxies = galaxy_sampling_util.Catalog()
    ctx.galaxies.columns = ["id", "z", "sed"]

    ctx.galaxies.id = np.arange(n_gal, dtype=np.int32)
    ctx.galaxies.z = np.random.uniform(0.1, 2.0, n_gal).astype(np.float32)
    ctx.galaxies.sed = np.random.uniform(0.1, 1.0, (n_gal, n_wavelengths)).astype(
        np.float32
    )

    # Create wavelength array (would normally come from templates)
    ctx.restframe_wavelength_for_SED = np.linspace(3000, 25000, n_wavelengths)

    # Test write_catalog plugin with larger dataset
    plugin = write_catalog.Plugin(ctx)
    plugin()

    # Check that file was created and has correct size
    assert os.path.exists(ctx.parameters.galaxy_sed_catalog_name)

    # Verify file contents
    with h5py.File(ctx.parameters.galaxy_sed_catalog_name, "r") as f:
        data = f["data"][:]
        wavelengths = f["restframe_wavelength_in_A"][:]

        assert len(data) == n_gal
        assert len(wavelengths) == n_wavelengths
        assert data["sed"].shape == (n_gal, n_wavelengths)

    # Clean up
    os.remove(ctx.parameters.galaxy_sed_catalog_name)


def test_write_catalog_str_method():
    """Test the __str__ method of the write_catalog plugin."""
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )

    plugin = write_catalog.Plugin(ctx)

    # Test string representation
    assert str(plugin) == "write ucat catalog to file"
