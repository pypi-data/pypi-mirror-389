# Copyright (C) 2024 ETH Zurich
# Institute for Particle Physics and Astrophysics
# Author: Silvan Fischbacher
# created: Thu Aug 01 2024


import os

import h5py
import numpy as np
from cosmic_toolbox import file_utils

from galsbi.ucat import sed_templates_util


def test_get_template_integrals():
    filter = "DECam_i"

    filters = {}
    with h5py.File(
        os.path.join(
            os.path.dirname(__file__), "./../../resources/filters_collection.h5"
        ),
        "r",
    ) as f:
        filters[filter] = {}
        filters[filter]["lam"] = np.array(f[filter]["lam"])
        filters[filter]["amp"] = np.array(f[filter]["amp"])

    filters[filter]["integ"] = np.trapz(filters[filter]["amp"], filters[filter]["lam"])

    sed_templates = {}
    sed_templates["n_templates"] = 3
    sed_templates["lam"] = filters[filter]["lam"]
    sed_templates["amp"] = np.random.rand(
        sed_templates["n_templates"], len(sed_templates["lam"])
    )
    integrals, excess_grid, z_grid = sed_templates_util.get_template_integrals(
        sed_templates, filters, filter_names=[filter], test=True
    )
    assert integrals[filter][0].shape[1] == len(excess_grid)
    assert integrals[filter][0].shape[0] == len(z_grid)

    sed_templates_util.store_sed_integrals("test.h5", integrals, excess_grid, z_grid)
    sed_templates_util.store_sed_integrals(
        "test_dir/test.h5", integrals, excess_grid, z_grid
    )
    os.remove("test.h5")
    file_utils.robust_remove("test_dir/")


def test_sed_templates_edge_cases():
    """Test edge cases for sed_templates_util functions."""
    # Test filter_name_back_compatibility with missing filter
    import tempfile

    from galsbi.ucat import sed_templates_util

    with tempfile.NamedTemporaryFile(delete=False, suffix=".h5") as tmp:
        filepath = tmp.name

    # Create test HDF5 file with specific structure
    with h5py.File(filepath, "w") as f:
        # Create test data structure
        f["z"] = np.array([0.1, 0.5, 1.0])
        f["E(B-V)"] = np.array([0.0, 0.1, 0.2])

        # Create integrals group
        integrals_group = f.create_group("integrals")
        # Add a filter without the full name
        filter_group = integrals_group.create_group("g")
        filter_group["template_0"] = np.random.random((3, 3))
        filter_group["template_1"] = np.random.random((3, 3))

    try:
        # Test backwards compatibility handling
        sed_templates = sed_templates_util.load_sed_integrals(
            filepath, filter_names=["euclid_g"], copy_to_cwd=False
        )

        # Should handle missing filter by falling back to shortened name
        assert "g" in sed_templates

        # Test copy_to_cwd functionality
        cwd_templates = sed_templates_util.load_sed_integrals(
            filepath, filter_names=["g"], copy_to_cwd=True
        )

        # Should create local copy and work
        assert "g" in cwd_templates

        # Test crop_negative functionality
        with h5py.File(filepath, "w") as f:
            f["z"] = np.array([0.1, 0.5])
            f["E(B-V)"] = np.array([0.0, 0.1])
            integrals_group = f.create_group("integrals")
            filter_group = integrals_group.create_group("g")
            # Add template with negative values
            filter_group["template_0"] = np.array([[-1.0, 2.0], [3.0, -0.5]])

        cropped_templates = sed_templates_util.load_sed_integrals(
            filepath, filter_names=["g"], crop_negative=True
        )

        # Negative values should be clipped to 0
        template_data = cropped_templates["g"][0]
        assert np.all(template_data >= 0)

    finally:
        # Clean up
        os.remove(filepath)
        local_copy = os.path.join(os.getcwd(), os.path.basename(filepath))
        if os.path.exists(local_copy):
            os.remove(local_copy)


def test_load_template_spectra():
    """Test load_template_spectra function."""
    import tempfile

    from galsbi.ucat import sed_templates_util

    with tempfile.NamedTemporaryFile(delete=False, suffix=".h5") as tmp:
        filepath = tmp.name

    # Create test template spectra file
    wavelengths = np.linspace(3000, 8000, 100)
    amplitudes = np.random.random((5, 100))  # 5 templates

    with h5py.File(filepath, "w") as f:
        f["wavelength"] = wavelengths
        f["amplitudes"] = amplitudes
        f["amplitudes"].attrs["description"] = "Test template set"
        f["amplitudes"].attrs["n_templates"] = 5

    try:
        # Test basic loading
        templates = sed_templates_util.load_template_spectra(filepath)

        assert "lam" in templates
        assert "amp" in templates
        assert templates.n_templates == 5
        np.testing.assert_array_equal(templates["lam"], wavelengths)
        np.testing.assert_array_equal(templates["amp"], amplitudes)

        # Test with scaling factors
        templates_scaled = sed_templates_util.load_template_spectra(
            filepath, lam_scale=2.0, amp_scale=0.5
        )

        np.testing.assert_array_equal(templates_scaled["lam"], wavelengths * 2.0)
        np.testing.assert_array_equal(templates_scaled["amp"], amplitudes * 0.5)

    finally:
        os.remove(filepath)
