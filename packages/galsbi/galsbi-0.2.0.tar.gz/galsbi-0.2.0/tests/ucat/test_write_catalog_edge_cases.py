# Copyright (C) 2025 ETH Zurich
# Institute for Particle Physics and Astrophysics
# Author: Silvan Fischbacher
# created: Thu Jul 10 2025


import os

import ivy
import numpy as np
import pytest

from galsbi.ucat import galaxy_sampling_util
from galsbi.ucat.plugins import write_catalog


@pytest.fixture
def mock_context_minimal():
    """Create a minimal mock context for testing edge cases."""
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )

    # Set up minimal parameters
    ctx.parameters.galaxy_catalog_name = "test_galaxy_catalog.h5"
    ctx.parameters.enrich_catalog = True

    return ctx


@pytest.fixture
def mock_context_enrichment_disabled():
    """Create a mock context with catalog enrichment disabled."""
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )

    # Set up parameters with enrichment disabled
    ctx.parameters.galaxy_catalog_name = "test_galaxy_catalog.h5"
    ctx.parameters.enrich_catalog = False

    return ctx


def test_enrich_catalog_disabled(mock_context_enrichment_disabled, tmp_path):
    """Test that enrich_catalog returns catalog unchanged when disabled."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        ctx = mock_context_enrichment_disabled

        # Create minimal galaxy catalog
        ctx.galaxies = galaxy_sampling_util.Catalog()
        ctx.galaxies.columns = ["id", "z"]
        ctx.galaxies.id = np.array([1, 2], dtype=np.int32)
        ctx.galaxies.z = np.array([0.1, 0.5], dtype=np.float32)

        # Create plugin and test enrich_catalog method
        plugin = write_catalog.Plugin(ctx)

        # Convert to catalog format
        cat = write_catalog.catalog_to_rec(ctx.galaxies)
        original_columns = set(cat.dtype.names)

        # Test enrichment (should do nothing when disabled)
        enriched_cat = plugin.enrich_catalog(cat)
        new_columns = set(enriched_cat.dtype.names)

        # Should be identical when enrichment is disabled
        assert original_columns == new_columns
        assert np.array_equal(cat, enriched_cat)

    finally:
        os.chdir(old_cwd)


def test_enrich_catalog_missing_ellipticity_data(mock_context_minimal, tmp_path):
    """Test enrich_catalog behavior when ellipticity data is missing."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        ctx = mock_context_minimal

        # Create galaxy catalog WITHOUT ellipticity data (e1, e2)
        ctx.galaxies = galaxy_sampling_util.Catalog()
        ctx.galaxies.columns = ["id", "z"]
        ctx.galaxies.id = np.array([1, 2], dtype=np.int32)
        ctx.galaxies.z = np.array([0.1, 0.5], dtype=np.float32)

        # Create plugin and test enrich_catalog method
        plugin = write_catalog.Plugin(ctx)

        # Convert to catalog format
        cat = write_catalog.catalog_to_rec(ctx.galaxies)

        # Test enrichment (should handle missing e1, e2 gracefully)
        enriched_cat = plugin.enrich_catalog(cat)

        # Should not have e_abs column since e1, e2 are missing
        assert "e_abs" not in enriched_cat.dtype.names

    finally:
        os.chdir(old_cwd)


def test_enrich_catalog_with_ellipticity_data(mock_context_minimal, tmp_path):
    """Test enrich_catalog behavior when ellipticity data is present."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        ctx = mock_context_minimal

        # Create galaxy catalog WITH ellipticity data
        ctx.galaxies = galaxy_sampling_util.Catalog()
        ctx.galaxies.columns = ["id", "z", "e1", "e2"]
        ctx.galaxies.id = np.array([1, 2], dtype=np.int32)
        ctx.galaxies.z = np.array([0.1, 0.5], dtype=np.float32)
        ctx.galaxies.e1 = np.array([0.1, -0.2], dtype=np.float32)
        ctx.galaxies.e2 = np.array([0.3, 0.1], dtype=np.float32)

        # Create plugin and test enrich_catalog method
        plugin = write_catalog.Plugin(ctx)

        # Convert to catalog format
        cat = write_catalog.catalog_to_rec(ctx.galaxies)

        # Test enrichment
        enriched_cat = plugin.enrich_catalog(cat)

        # Should have e_abs column
        assert "e_abs" in enriched_cat.dtype.names

        # Check that e_abs is calculated correctly
        expected_e_abs = np.sqrt(cat["e1"] ** 2 + cat["e2"] ** 2)
        np.testing.assert_array_almost_equal(enriched_cat["e_abs"], expected_e_abs)

    finally:
        os.chdir(old_cwd)


def test_enrich_catalog_with_bkg_noise_amp(mock_context_minimal, tmp_path):
    """Test enrich_catalog behavior with background noise amplitude parameter."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        ctx = mock_context_minimal
        ctx.parameters.bkg_noise_amp = 1.5  # Set a background noise amplitude

        # Create minimal galaxy catalog
        ctx.galaxies = galaxy_sampling_util.Catalog()
        ctx.galaxies.columns = ["id", "z"]
        ctx.galaxies.id = np.array([1, 2], dtype=np.int32)
        ctx.galaxies.z = np.array([0.1, 0.5], dtype=np.float32)

        # Create plugin and test enrich_catalog method
        plugin = write_catalog.Plugin(ctx)

        # Convert to catalog format
        cat = write_catalog.catalog_to_rec(ctx.galaxies)

        # Test enrichment
        enriched_cat = plugin.enrich_catalog(cat)

        # Should have bkg_noise_amp column
        assert "bkg_noise_amp" in enriched_cat.dtype.names

        # Check that all values are set to the parameter value
        assert np.all(enriched_cat["bkg_noise_amp"] == 1.5)

    finally:
        os.chdir(old_cwd)


def test_enrich_catalog_with_position_and_bkg_noise_std_scalar(
    mock_context_minimal, tmp_path
):
    """Test enrich_catalog with position data and scalar background noise std."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        ctx = mock_context_minimal
        ctx.parameters.bkg_noise_std = 2.0  # Scalar value

        # Create galaxy catalog with position data (x, y)
        ctx.galaxies = galaxy_sampling_util.Catalog()
        ctx.galaxies.columns = ["id", "z", "x", "y"]
        ctx.galaxies.id = np.array([1, 2], dtype=np.int32)
        ctx.galaxies.z = np.array([0.1, 0.5], dtype=np.float32)
        ctx.galaxies.x = np.array([10, 20], dtype=np.float32)
        ctx.galaxies.y = np.array([15, 25], dtype=np.float32)

        # Create plugin and test enrich_catalog method
        plugin = write_catalog.Plugin(ctx)

        # Convert to catalog format
        cat = write_catalog.catalog_to_rec(ctx.galaxies)

        # Test enrichment
        enriched_cat = plugin.enrich_catalog(cat)

        # Should have bkg_noise_std column
        assert "bkg_noise_std" in enriched_cat.dtype.names

        # Check that all values are set to the scalar value
        assert np.all(enriched_cat["bkg_noise_std"] == 2.0)

    finally:
        os.chdir(old_cwd)


def test_enrich_catalog_with_position_and_bkg_noise_std_array(
    mock_context_minimal, tmp_path
):
    """Test enrich_catalog with position data and array background noise std."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        ctx = mock_context_minimal
        # Create a small 2D array for background noise std
        ctx.parameters.bkg_noise_std = np.array(
            [[1.0, 1.5], [2.0, 2.5]], dtype=np.float32
        )

        # Create galaxy catalog with position data (x, y) that fit within the
        # array bounds
        ctx.galaxies = galaxy_sampling_util.Catalog()
        ctx.galaxies.columns = ["id", "z", "x", "y"]
        ctx.galaxies.id = np.array([1, 2], dtype=np.int32)
        ctx.galaxies.z = np.array([0.1, 0.5], dtype=np.float32)
        ctx.galaxies.x = np.array([0, 1], dtype=np.float32)  # Valid indices
        ctx.galaxies.y = np.array([0, 1], dtype=np.float32)  # Valid indices

        # Create plugin and test enrich_catalog method
        plugin = write_catalog.Plugin(ctx)

        # Convert to catalog format
        cat = write_catalog.catalog_to_rec(ctx.galaxies)

        # Test enrichment
        enriched_cat = plugin.enrich_catalog(cat)

        # Should have bkg_noise_std column
        assert "bkg_noise_std" in enriched_cat.dtype.names

        # Check that values are taken from the array at the correct positions
        expected_values = [
            ctx.parameters.bkg_noise_std[0, 0],  # y=0, x=0
            ctx.parameters.bkg_noise_std[1, 1],  # y=1, x=1
        ]
        np.testing.assert_array_almost_equal(
            enriched_cat["bkg_noise_std"], expected_values
        )

    finally:
        os.chdir(old_cwd)


def test_enrich_catalog_with_ra_dec_coordinates(mock_context_minimal, tmp_path):
    """Test enrich_catalog behavior when using ra/dec coordinates instead of x/y."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        ctx = mock_context_minimal
        ctx.parameters.bkg_noise_std = 1.0  # Scalar value

        # Create galaxy catalog with ra/dec coordinates (not x/y)
        ctx.galaxies = galaxy_sampling_util.Catalog()
        ctx.galaxies.columns = ["id", "z", "ra", "dec"]
        ctx.galaxies.id = np.array([1, 2], dtype=np.int32)
        ctx.galaxies.z = np.array([0.1, 0.5], dtype=np.float32)
        ctx.galaxies.ra = np.array([180.0, 185.0], dtype=np.float32)
        ctx.galaxies.dec = np.array([-30.0, -25.0], dtype=np.float32)

        # Create plugin and test enrich_catalog method
        plugin = write_catalog.Plugin(ctx)

        # Convert to catalog format
        cat = write_catalog.catalog_to_rec(ctx.galaxies)

        # Test enrichment
        enriched_cat = plugin.enrich_catalog(cat)

        # Should NOT have bkg_noise_std column since we have ra/dec instead of x/y
        assert "bkg_noise_std" not in enriched_cat.dtype.names

    finally:
        os.chdir(old_cwd)
