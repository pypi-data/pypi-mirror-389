# Copyright (C) 2024 ETH Zurich
# Institute for Particle Physics and Astrophysics
# Author: Silvan Fischbacher
# created: Thu Aug 08 2024

import os

import numpy as np
import ufig.config.common
from cosmo_torrent import data_path
from ivy.loop import Loop
from ufig.workflow_util import FiltersStopCriteria

import galsbi.ucat.config.common


# Import all common settings from ucat and ufig as default
def _update_globals(module, globals_):
    globals_.update(
        {k: v for k, v in module.__dict__.items() if not k.startswith("__")}
    )


_update_globals(galsbi.ucat.config.common, globals())
_update_globals(ufig.config.common, globals())


# Default size of the image
sampling_mode = "wcs"
ra0 = 0
dec0 = 0
pixscale = 0.168
size_x = 1000
size_y = 1000


# Define the filters
filters = ["g", "r", "i", "z", "y"]
filters_full_names = {
    "B": "SuprimeCam_B",
    "g": "HSC_g",
    "r": "HSC_r2",
    "i": "HSC_i2",
    "z": "HSC_z",
    "y": "HSC_y",
}
reference_band = "i"
magzero_dict = {"g": 27.0, "r": 27.0, "i": 27.0, "z": 27.0, "y": 27.0}

# Define the plugins that should be used
plugins = [
    "ufig.plugins.multi_band_setup",
    "galsbi.ucat.plugins.sample_galaxies",
    # "ufig.plugins.draw_stars_besancon_map",
    Loop(
        [
            "ufig.plugins.single_band_setup",
            "ufig.plugins.background_noise",
            "ufig.plugins.resample",
            "ufig.plugins.add_psf",
            "ufig.plugins.gamma_interpolation_table",
            "ufig.plugins.render_galaxies_flexion",
            "ufig.plugins.convert_photons_to_adu",
            # because from the image we see single spike in the x direction:
            "ufig.plugins.saturate_pixels_x",
            "galsbi.ucat.plugins.write_catalog",
            "ufig.plugins.write_image",
        ],
        stop=FiltersStopCriteria(),
    ),
    Loop(
        [
            "ufig.plugins.single_band_setup",
            "ufig.plugins.run_sextractor_forced_photometry",
        ],
        stop=FiltersStopCriteria(),
    ),
    "ufig.plugins.match_sextractor_seg_catalog_multiband_read",
    "ufig.plugins.cleanup_catalogs",
    "ivy.plugin.show_stats",
]

# Background noise  (corresponding roughly to a HSC deep field image)
background_type = "gaussian"
background_sigma_dict = {"g": 1.2, "r": 1.5, "i": 2.6, "z": 6.4, "y": 8.6}
bkg_noise_amp_dict = {"g": 0.005, "r": 0.005, "i": 0.01, "z": 0.01, "y": 0.02}
bkg_noise_multiply_gain = False
gain_dict = {
    "g": 70,
    "r": 60,
    "i": 80,
    "z": 105,
    "y": 70,
}
n_exp_dict = {
    "g": 20,
    "r": 16,
    "i": 22,
    "z": 30,
    "y": 20,
}

# PSF  (corresponding roughly to a HSC deep field image)
psf_type = "constant_moffat"  # constant PSF defined by Moffat profile
psf_e1 = 0.0  # PSF e1
psf_e2 = 0.0  # PSF e2
psf_beta = [2.0, 5.0]  # Moffat beta parameter
seeing = 0.6  # mean seeing in arcsec

# SExtractor
sextractor_use_forced_photo = True
sextractor_params = "newdefault.param"
sextractor_config = "hsc_deblend_aper.config"
sextractor_checkimages = ["SEGMENTATION", "BACKGROUND"]
sextractor_checkimages_suffixes = ["_seg.fits", "_bkg.fits"]
sextractor_forced_photo_detection_bands = ["i"]
sextractor_catalog_off_mask_radius = 1
flag_gain_times_nexp = False

# Luminosity function
lum_fct_z_res = 0.001
lum_fct_m_max = -4
lum_fct_z_max = 6

# Sampling methods ucat
nside_sampling = 1024

# Magnitude limits
stars_mag_max = 26
gals_mag_max = 28
stars_mag_min = 12
gals_mag_min = 14

# Filter throughputs
filters_file_name = os.path.join(
    data_path("HSC_tables"), "HSC_filters_collection_yfix.h5"
)

# Template spectra & integration tables
n_templates = 5
templates_file_name = os.path.join(
    data_path("template_BlantonRoweis07"), "template_spectra_BlantonRoweis07.h5"
)

# Extinction
extinction_map_file_name = os.path.join(
    data_path("lambda_sfd_ebv"), "lambda_sfd_ebv.fits"
)

# magnitude table
magnitude_calculation = "table"
templates_int_tables_file_name = os.path.join(
    data_path("HSC_tables"), "HSC_template_integrals_yfix.h5"
)

# Catalog precision
catalog_precision = np.float32

# Seed
seed = 1996


# Parameters that are specific to the Moser+24 model
# Mainly the different parametrizations of the galaxy population model.
# DO NOT CHANGE THESE VALUES IF YOU WANT TO USE THE GALAXY POPULATION MODEL OF MOSER+24
# CHANGING THESE VALUES WILL LEAD TO A DIFFERENT MEANING OF SOME OF THE PARAMETERS
lum_fct_parametrization = "logpower"
ellipticity_sampling_method = "beta_mode_red_blue"
sersic_sampling_method = "blue_red_betaprime"
logr50_sampling_method = "red_blue"
template_coeff_sampler = "dirichlet_alpha_mode"
template_coeff_weight_blue = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
template_coeff_weight_red = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
template_coeff_z1_blue = 3
template_coeff_z1_red = 3
