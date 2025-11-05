# Copyright (C) 2024 ETH Zurich
# Institute for Particle Physics and Astrophysics
# Author: Silvan Fischbacher
# created: Thu Aug 08 2024


import os

import numpy as np
import pytest
from cosmic_toolbox import arraytools as at

import galsbi
from galsbi import GalSBI
from galsbi.citations import CITE_MOSER24


@pytest.fixture
def small_healpix_map():
    healpix_map = np.zeros(12 * 1024**2)
    healpix_map[0] = 1
    return healpix_map


@pytest.fixture
def cwd(tmp_path):
    previous_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        yield tmp_path
    finally:
        os.chdir(previous_cwd)


def test_intrinsic_model(small_healpix_map, cwd):
    model = GalSBI("Moser+24")
    assert model.name == "Moser+24"

    model(healpix_map=small_healpix_map)
    cats = model.load_catalogs()

    # test if all catalogs are written by checking if you can delete them
    for f in ["g", "r", "i", "z", "y"]:
        os.remove(f"GalSBI_sim_0_{f}_ucat.gal.cat")

    model = GalSBI("Moser+24")
    model(model_index=42, healpix_map=small_healpix_map)
    cats2 = model.load_catalogs(model_index=42)

    assert len(cats["ucat galaxies g"]["mag"]) != len(cats2["ucat galaxies g"]["mag"])

    for f in ["g", "r", "i", "z", "y"]:
        os.remove(f"GalSBI_sim_42_{f}_ucat.gal.cat")

    model = GalSBI("Moser+24")
    model(model_index=[0, 42], healpix_map=small_healpix_map, verbosity="warning")

    for f in ["g", "r", "i", "z", "y"]:
        os.remove(f"GalSBI_sim_0_{f}_ucat.gal.cat")
        os.remove(f"GalSBI_sim_42_{f}_ucat.gal.cat")


def test_emu_model(small_healpix_map, cwd):
    model = GalSBI("Moser+24")
    model(file_name="intrinsic", healpix_map=small_healpix_map)

    model = GalSBI("Moser+24")
    model(mode="emulator", file_name="emu", healpix_map=small_healpix_map)

    # test if intrinsic catalogs are the same
    for f in ["g", "r", "i", "z", "y"]:
        cat1 = at.load_hdf(f"intrinsic_0_{f}_ucat.gal.cat")
        cat2 = at.load_hdf(f"emu_0_{f}_ucat.gal.cat")
        shared_params = set(cat1.dtype.names) & set(cat2.dtype.names)
        assert len(shared_params) > 0
        for par in shared_params:
            assert np.all(cat1[par] == cat2[par])

        os.remove(f"intrinsic_0_{f}_ucat.gal.cat")
        os.remove(f"emu_0_{f}_ucat.gal.cat")
        os.remove(f"emu_0_{f}_ucat.star.cat")

    # test if there are output catalogs
    for f in ["g", "r", "i", "z", "y"]:
        cat = at.load_hdf(f"emu_0_{f}_se.cat")
        assert "MAG_AUTO" in cat.dtype.names
        os.remove(f"emu_0_{f}_se.cat")


def test_image(cwd):
    model = GalSBI("Moser+24")
    model(mode="image", size_x=100, size_y=100)

    # creates intrinsic catalogs and images
    for f in ["g", "r", "i", "z", "y"]:
        os.remove(f"GalSBI_sim_0_{f}_ucat.gal.cat")
        os.remove(f"GalSBI_sim_0_{f}_image.fits")


def test_custom_config(small_healpix_map, cwd):
    model = GalSBI("Moser+24")
    model(healpix_map=small_healpix_map)
    cats1 = {}
    for f in ["g", "r", "i", "z", "y"]:
        cats1[f] = at.load_hdf(f"GalSBI_sim_0_{f}_ucat.gal.cat")
        os.remove(f"GalSBI_sim_0_{f}_ucat.gal.cat")

    path2config = os.path.join(
        galsbi.__path__[0], "configs/config_Moser+24_intrinsic.py"
    )
    model = GalSBI("Moser+24")
    model(mode="config_file", config_file=path2config, healpix_map=small_healpix_map)
    cats2 = {}
    for f in ["g", "r", "i", "z", "y"]:
        cats2[f] = at.load_hdf(f"GalSBI_sim_0_{f}_ucat.gal.cat")
        os.remove(f"GalSBI_sim_0_{f}_ucat.gal.cat")

    config_module = "galsbi.configs.config_Moser+24_intrinsic"
    model = GalSBI("Moser+24")
    model(mode="config_file", config_file=config_module, healpix_map=small_healpix_map)
    cats3 = {}
    for f in ["g", "r", "i", "z", "y"]:
        cats3[f] = at.load_hdf(f"GalSBI_sim_0_{f}_ucat.gal.cat")
        os.remove(f"GalSBI_sim_0_{f}_ucat.gal.cat")

    for f in ["g", "r", "i", "z", "y"]:
        assert np.all(cats1[f] == cats2[f])
        assert np.all(cats1[f] == cats3[f])


def test_citations(capsys, cwd):
    model = GalSBI("Moser+24")
    model.cite()

    captured = capsys.readouterr()
    assert CITE_MOSER24 in captured.out


def test_invalid_model(cwd):
    with pytest.raises(ValueError):
        model = GalSBI("Moser+25")
        model()

    with pytest.raises(ValueError):
        galsbi.load.load_abc_posterior("Moser+25")

    with pytest.raises(ValueError):
        galsbi.citations.cite_abc_posterior("Moser+25")


def test_load_cats_and_images(cwd):
    model = GalSBI("Moser+24")
    model(mode="image", size_x=100, size_y=100)

    cats_rec = model.load_catalogs()
    cats_df = model.load_catalogs(output_format="df")
    cats_fits = model.load_catalogs(output_format="fits")
    assert np.all(
        list(cats_rec["ucat galaxies g"].dtype.names)
        == list(cats_fits["ucat galaxies g"].columns)
    )
    p = "mag"
    assert np.all(cats_rec["ucat galaxies g"][p] == cats_df["ucat galaxies g"][p])
    assert np.all(cats_rec["ucat galaxies g"][p] == cats_fits["ucat galaxies g"][p])

    with pytest.raises(ValueError):
        model.load_catalogs(output_format="invalid")

    images = model.load_images()
    assert (
        list(images.keys()).sort()
        == ["image g", "image r", "image i", "image z", "image y"].sort()
    )

    for f in model.filters:
        os.remove(f"GalSBI_sim_0_{f}_ucat.gal.cat")
        os.remove(f"GalSBI_sim_0_{f}_image.fits")

    images = model.load_images()
    assert images == {}

    cats = model.load_catalogs()
    assert cats == {}


def test_combine_cats(small_healpix_map, cwd):
    model = GalSBI("Moser+24")
    model(mode="emulator", healpix_map=small_healpix_map)

    cats = model.load_catalogs()
    cats_combined = model.load_catalogs(combine=True)

    assert np.all(
        cats["ucat galaxies g"]["mag"] == cats_combined["ucat galaxies"]["mag g"]
    )
    assert np.all(
        cats["sextractor g"]["MAG_AUTO"] == cats_combined["sextractor"]["MAG_AUTO g"]
    )

    for f in ["g", "r", "i", "z", "y"]:
        os.remove(f"GalSBI_sim_0_{f}_ucat.gal.cat")
        os.remove(f"GalSBI_sim_0_{f}_ucat.star.cat")
        os.remove(f"GalSBI_sim_0_{f}_se.cat")


def test_method_call_order(cwd):
    model = GalSBI("Moser+24")
    with pytest.raises(RuntimeError):
        model.load_catalogs()


@pytest.mark.slow
def test_fischbacher_model_with_emulator(cwd):
    model = GalSBI("Fischbacher+24")
    model(mode="emulator")


def test_load_nonexistent_catalogs(cwd):
    model = GalSBI("Moser+24")
    # Run a minimal model to set self.filters
    model(mode="intrinsic", size_x=10, size_y=10)

    # Delete all generated catalogs
    for f in ["g", "r", "i", "z", "y"]:
        os.remove(f"GalSBI_sim_0_{f}_ucat.gal.cat")

    # Try to load catalogs with a non-existent model index
    cats = model.load_catalogs(model_index=42)

    # Should return an empty dictionary
    assert cats == {}

    # Try to combine non-existent catalogs
    combined_cats = model.load_catalogs(model_index=42, combine=True)
    assert combined_cats == {}


def test_save_seds_functionality(small_healpix_map, cwd):
    """Test that save_SEDs functionality works end-to-end."""
    model = GalSBI("Moser+24")

    # Test with save_SEDs enabled
    model(
        mode="intrinsic",
        file_name="test_seds",
        healpix_map=small_healpix_map,
        save_SEDs=True,
        verbosity="warning",
    )

    # Check that SED catalog file was created
    sed_file = "test_seds_0_sed.cat"
    assert os.path.exists(sed_file)

    # Load catalogs and check SED data is included
    cats = model.load_catalogs(model_index=0)

    # Check that sed catalog exists in the output
    assert "sed" in cats
    assert "restframe_wavelength_in_A" in cats

    # Verify SED data structure
    sed_data = cats["sed"]
    wavelengths = cats["restframe_wavelength_in_A"]

    assert len(sed_data) > 0  # Should have some galaxies
    assert "id" in sed_data.dtype.names
    assert "z" in sed_data.dtype.names
    assert "sed" in sed_data.dtype.names
    assert len(wavelengths) > 0  # Should have wavelength grid

    # Test combined catalogs with SEDs
    combined_cats = model.load_catalogs(model_index=0, combine=True)

    # Check that SED data is properly included in combined catalogs
    if "ucat galaxies" in combined_cats:
        ucat_gals = combined_cats["ucat galaxies"]
        assert "sed" in ucat_gals.dtype.names

    if "sextractor" in combined_cats:
        # SEDs should be matched to sextractor catalog
        sext_cat = combined_cats["sextractor"]
        if "sed" in sext_cat.dtype.names:
            # Check that SED matching logic works
            assert sext_cat["sed"].shape[0] == len(sext_cat)

    # Clean up
    for f in ["g", "r", "i", "z", "y"]:
        if os.path.exists(f"test_seds_0_{f}_ucat.gal.cat"):
            os.remove(f"test_seds_0_{f}_ucat.gal.cat")
    if os.path.exists(sed_file):
        os.remove(sed_file)


def test_save_seds_disabled_by_default(small_healpix_map, cwd):
    """Test that SED catalog is not created when save_SEDs is not specified."""
    model = GalSBI("Moser+24")

    # Run without save_SEDs (should default to False)
    model(
        mode="intrinsic",
        file_name="test_no_seds",
        healpix_map=small_healpix_map,
        verbosity="warning",
    )

    # Check that SED catalog file was NOT created
    sed_file = "test_no_seds_0_sed.cat"
    assert not os.path.exists(sed_file)

    # Load catalogs and check SED data is not included
    cats = model.load_catalogs(model_index=0)

    # Check that sed catalog does not exist in the output
    assert "sed" not in cats
    assert "restframe_wavelength_in_A" not in cats

    # Clean up
    for f in ["g", "r", "i", "z", "y"]:
        if os.path.exists(f"test_no_seds_0_{f}_ucat.gal.cat"):
            os.remove(f"test_no_seds_0_{f}_ucat.gal.cat")


def test_save_seds_with_emulator_mode(small_healpix_map, cwd):
    """Test that save_SEDs works correctly with emulator mode."""
    model = GalSBI("Moser+24")

    # Test with emulator mode and save_SEDs enabled
    model(
        mode="emulator",
        file_name="test_emu_seds",
        healpix_map=small_healpix_map,
        save_SEDs=True,
        verbosity="warning",
    )

    # Check that SED catalog file was created
    sed_file = "test_emu_seds_0_sed.cat"
    assert os.path.exists(sed_file)

    # Load and verify SED data
    cats = model.load_catalogs(model_index=0)

    assert "sed" in cats
    assert "restframe_wavelength_in_A" in cats

    cats = model.load_catalogs(model_index=0, combine=True)
    assert "sed" in cats["ucat galaxies"].dtype.names
    assert "restframe_wavelength_in_A" in cats
    assert "sed" in cats["sextractor"].dtype.names

    # Clean up
    for f in ["g", "r", "i", "z", "y"]:
        for suffix in ["_ucat.gal.cat", "_ucat.star.cat", "_se.cat"]:
            file_path = f"test_emu_seds_0_{f}{suffix}"
            if os.path.exists(file_path):
                os.remove(file_path)
    if os.path.exists(sed_file):
        os.remove(sed_file)


def test_save_sed_not_in_ucat_cat(small_healpix_map, cwd):
    """Test that SEDs are not saved in ucat catalogs by default."""
    model = GalSBI("Moser+24")

    # Run with save_SEDs enabled
    model(
        mode="intrinsic",
        file_name="test_seds_not_in_ucat",
        healpix_map=small_healpix_map,
        save_SEDs=True,
        verbosity="warning",
    )

    # Check that SED catalog file was created
    sed_file = "test_seds_not_in_ucat_0_sed.cat"
    assert os.path.exists(sed_file)

    # Load ucat catalogs and check SEDs are not included
    cats = model.load_catalogs(model_index=0)

    for f in ["g", "r", "i", "z", "y"]:
        ucat_file = f"test_seds_not_in_ucat_0_{f}_ucat.gal.cat"
        assert os.path.exists(ucat_file)
        ucat_cat = at.load_hdf(ucat_file)
        assert "sed" not in ucat_cat.dtype.names

    assert "sed" in cats
    assert "restframe_wavelength_in_A" in cats

    cats = model.load_catalogs(model_index=0, combine=True)
    assert "sed" in cats["ucat galaxies"].dtype.names
    assert "restframe_wavelength_in_A" in cats

    # Clean up
    for f in ["g", "r", "i", "z", "y"]:
        if os.path.exists(f"test_seds_not_in_ucat_0_{f}_ucat.gal.cat"):
            os.remove(f"test_seds_not_in_ucat_0_{f}_ucat.gal.cat")
    if os.path.exists(sed_file):
        os.remove(sed_file)


def test_save_seds_with_df(small_healpix_map, cwd):
    """Test that SEDs are saved correctly when using DataFrame output."""
    model = GalSBI("Moser+24")

    # Run with save_SEDs enabled
    model(
        mode="intrinsic",
        file_name="test_seds_df",
        healpix_map=small_healpix_map,
        save_SEDs=True,
        verbosity="warning",
    )

    # Load catalogs as DataFrame
    cats_df = model.load_catalogs(model_index=0, output_format="df")

    # Check SED data in DataFrame
    assert "sed" in cats_df
    assert "restframe_wavelength_in_A" in cats_df
    assert type(cats_df["restframe_wavelength_in_A"]) is np.ndarray
    assert "sed_0" in cats_df["sed"].columns

    cats = model.load_catalogs(model_index=0, combine=True, output_format="df")
    assert "sed" not in cats["ucat galaxies"]
    assert "sed_0" in cats["ucat galaxies"]
    assert "restframe_wavelength_in_A" in cats

    # Clean up
    for f in ["g", "r", "i", "z", "y"]:
        if os.path.exists(f"test_seds_df_0_{f}_ucat.gal.cat"):
            os.remove(f"test_seds_df_0_{f}_ucat.gal.cat")
    if os.path.exists("test_seds_df_0_sed.cat"):
        os.remove("test_seds_df_0_sed.cat")


def test_save_seds_with_fits(small_healpix_map, cwd):
    """Test that SEDs are saved correctly when using FITS output."""
    model = GalSBI("Moser+24")

    # Run with save_SEDs enabled
    model(
        mode="intrinsic",
        file_name="test_seds_fits",
        healpix_map=small_healpix_map,
        save_SEDs=True,
        verbosity="warning",
    )

    # Load catalogs as FITS
    cats_fits = model.load_catalogs(model_index=0, output_format="fits")
    n_gals = len(cats_fits["ucat galaxies g"]["mag"])

    # Check SED data in FITS
    assert "sed" in cats_fits
    assert "restframe_wavelength_in_A" in cats_fits
    n_lambda = len(cats_fits["restframe_wavelength_in_A"])
    assert type(cats_fits["restframe_wavelength_in_A"]) is np.ndarray
    assert cats_fits["sed"]["sed"].shape == (n_gals, n_lambda)

    cats_fits_combined = model.load_catalogs(
        model_index=0, combine=True, output_format="fits"
    )
    assert "sed" in cats_fits_combined["ucat galaxies"].columns
    assert "restframe_wavelength_in_A" in cats_fits_combined
    assert type(cats_fits_combined["restframe_wavelength_in_A"]) is np.ndarray

    # Clean up
    for f in ["g", "r", "i", "z", "y"]:
        if os.path.exists(f"test_seds_fits_0_{f}_ucat.gal.cat"):
            os.remove(f"test_seds_fits_0_{f}_ucat.gal.cat")
    if os.path.exists("test_seds_fits_0_sed.cat"):
        os.remove("test_seds_fits_0_sed.cat")
