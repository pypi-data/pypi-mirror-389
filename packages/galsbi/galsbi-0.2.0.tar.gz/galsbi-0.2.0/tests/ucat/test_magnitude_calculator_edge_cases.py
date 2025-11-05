# Copyright (C) 2025 ETH Zurich
# Institute for Particle Physics and Astrophysics
# Author: Silvan Fischbacher
# created: Fri Jul 11 2025

import os
import tempfile
from collections import OrderedDict

import h5py
import numpy as np

from galsbi.ucat.magnitude_calculator import MagCalculatorDirect, MagCalculatorTable


def test_mag_calculator_direct_single_filter():
    """Test MagCalculatorDirect with single filter name (not iterable)."""
    # Create mock filters and templates
    mock_filters = OrderedDict()
    mock_filters["g"] = {
        "lam": np.linspace(400, 700, 100),
        "amp": np.ones(100),
        "integ": 1.0,
    }

    mock_templates = OrderedDict()
    mock_templates["lam"] = np.linspace(400, 700, 100)
    mock_templates["amp"] = np.random.random((2, 100))  # 2 templates
    mock_templates["n_templates"] = 2

    mag_calc = MagCalculatorDirect(mock_filters, mock_templates)

    # Test with single filter name (string, not list) - this should hit line 61
    redshifts = np.array([0.1, 0.5])
    excess_b_v = np.array([0.0, 0.1])
    coeffs = np.array([[0.5, 0.5], [0.3, 0.7]])

    # This should trigger the "if not isinstance(filter_names, Iterable)" branch
    result = mag_calc(redshifts, excess_b_v, coeffs, "g")

    assert "g" in result
    assert len(result["g"]) == 2


def test_mag_calculator_table_single_filter():
    """Test MagCalculatorTable with single filter name."""
    # Create temporary HDF5 file for templates
    with tempfile.NamedTemporaryFile(delete=False, suffix=".h5") as tmp:
        filepath = tmp.name

    try:
        # Create test template integrals file
        with h5py.File(filepath, "w") as f:
            f["z"] = np.array([0.1, 0.5, 1.0])
            f["E(B-V)"] = np.array([0.0, 0.1, 0.2])

            integrals_group = f.create_group("integrals")
            filter_group = integrals_group.create_group("g")

            # Create template data (z_grid x excess_b_v_grid)
            for i in range(2):  # 2 templates
                filter_group[f"template_{i}"] = np.random.random((3, 3))

        mag_calc = MagCalculatorTable(["g"], filepath)

        # Test with single filter name (string) - hits line 157
        redshifts = np.array([0.2, 0.8])
        excess_b_v = np.array([0.05, 0.15])
        coeffs = np.array([[0.6, 0.4], [0.2, 0.8]])

        result = mag_calc(redshifts, excess_b_v, coeffs, "g")

        assert "g" in result
        assert len(result["g"]) == 2

        # Test return_fluxes=True - hits line 176
        fluxes = mag_calc(redshifts, excess_b_v, coeffs, "g", return_fluxes=True)
        assert "g" in fluxes
        assert len(fluxes["g"]) == 2

    finally:
        os.remove(filepath)


def test_mag_calculator_direct_return_fluxes():
    """Test MagCalculatorDirect with return_fluxes=True."""
    mock_filters = OrderedDict()
    mock_filters["g"] = {
        "lam": np.linspace(400, 700, 100),
        "amp": np.ones(100),
        "integ": 1.0,
    }

    mock_templates = OrderedDict()
    mock_templates["lam"] = np.linspace(400, 700, 100)
    mock_templates["amp"] = np.random.random((2, 100))
    mock_templates["n_templates"] = 2

    mag_calc = MagCalculatorDirect(mock_filters, mock_templates)

    redshifts = np.array([0.1])
    excess_b_v = np.array([0.0])
    coeffs = np.array([[0.5, 0.5]])

    # Test return_fluxes=True path
    fluxes = mag_calc(redshifts, excess_b_v, coeffs, ["g"], return_fluxes=True)

    assert "g" in fluxes
    assert isinstance(fluxes["g"], np.ndarray)
    assert len(fluxes["g"]) == 1


def test_mag_calculator_edge_cases():
    """Test various edge cases for magnitude calculators."""
    # Test empty coefficient arrays
    mock_filters = OrderedDict()
    mock_filters["g"] = {
        "lam": np.linspace(400, 700, 10),
        "amp": np.ones(10),
        "integ": 1.0,
    }

    mock_templates = OrderedDict()
    mock_templates["lam"] = np.linspace(400, 700, 10)
    mock_templates["amp"] = np.random.random((1, 10))  # Single template
    mock_templates["n_templates"] = 1

    mag_calc = MagCalculatorDirect(mock_filters, mock_templates)

    # Test with single galaxy
    redshifts = np.array([0.1])
    excess_b_v = np.array([0.0])
    coeffs = np.array([[1.0]])  # Single template, single galaxy

    result = mag_calc(redshifts, excess_b_v, coeffs, ["g"])
    assert "g" in result
    assert len(result["g"]) == 1


def test_mag_calculator_large_redshift():
    """Test magnitude calculator with large redshift values."""
    mock_filters = OrderedDict()
    mock_filters["g"] = {
        "lam": np.linspace(400, 700, 50),
        "amp": np.ones(50),
        "integ": 1.0,
    }

    mock_templates = OrderedDict()
    mock_templates["lam"] = np.linspace(200, 500, 50)  # Rest frame
    mock_templates["amp"] = np.random.random((2, 50))
    mock_templates["n_templates"] = 2

    mag_calc = MagCalculatorDirect(mock_filters, mock_templates)

    # Test with high redshift
    redshifts = np.array([5.0])  # High redshift
    excess_b_v = np.array([0.1])
    coeffs = np.array([[0.7, 0.3]])

    result = mag_calc(redshifts, excess_b_v, coeffs, ["g"])
    assert "g" in result
    assert len(result["g"]) == 1
