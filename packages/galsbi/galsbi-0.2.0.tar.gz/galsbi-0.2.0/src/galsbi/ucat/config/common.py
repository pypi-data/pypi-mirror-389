# Copyright (C) 2018 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created on Mar 5, 2018
author: Joerg Herbel
"""

import numpy as np

# ==================================================================
# G E N E R A L
# ==================================================================

# Filter bands (multi-band only)
filters = ["g", "r", "i", "z", "y"]
# Filters full names
filters_full_names = {
    "B": "SuprimeCam_B",
    "g": "HSC_g",
    "r": "HSC_r2",
    "i": "HSC_i2",
    "z": "HSC_z",
    "y": "HSC_y",
}
reference_band = "i"

# Seeds
# ---------------------
# General seed set when initializing UFig
seed = 102301239
# Seed offset set before sampling the number of galaxies
gal_num_seed_offset = 100
# Seed offset set before drawing from luminosity function
gal_lum_fct_seed_offset = 1200
# Seed offset set before sampling galaxy positions
gal_dist_seed_offset = 200
# Seed offset set before sampling the galaxies' Sersic indices distribution
gal_sersic_seed_offset = 300
# Seed offset set before sampling the galaxies' ellipticity distribution
gal_ellipticities_seed_offset = 400
# Seed to make redshift addition deterministic
seed_ngal = 500

# Sampling and other general parameters
# -------------------------------------
# Sampling mode for galaxy catalog, either "wcs" (for image simulations) or "healpix"
sampling_mode = "wcs"
# healpy map for healpix sampling
healpix_map = None
# Healpix pixelization for sampling
nside_sampling = 512
# Remote directory containing maps
maps_remote_dir = "ufig_res/maps/"
# galaxy_catalog_name
galaxy_catalog_name = "ucat_galaxies.h5"
# galaxy_sed_catalog_name
galaxy_sed_catalog_name = "ucat_galaxies_sed.h5"
# star_catalog_name
star_catalog_name = "ucat_stars.h5"
# by how much the number of galaxies should be multiplied (used to test high or low
# blending regimes)
ngal_multiplier = 1
# if to enrich the catalog by parameters such as bkg, absolute ellipticity, etc.
enrich_catalog = False

# ==================================================================
# I M A G E   P R O P E R T I E S
# ==================================================================

# Number of pixels on image x-axis
size_x = 10000
# Number of pixels on image y-axis
size_y = 10000
# Center of field (RA)
ra0 = 70.459787
# Center of field (Dec)
dec0 = -44.244444
# Pixel scale (arcsec/pixel)
pixscale = 0.263


# ==================================================================
# C O S M O L O G Y
# ==================================================================

# Reduced Hubble parameter
h = 0.7
# Matter density
omega_m = 0.3
# Dark energy density
omega_l_in = "flat"

# ==================================================================
# G A L A X Y   C A T A L O G
# ==================================================================

# -------------------
# Luminosity function
# -------------------

# Galaxy type, each will have its own luminosity functions (see luminosity_functions.py:
# GALAXY_TYPES_ALL, initialize_luminosity_functions)
galaxy_types = ["red", "blue"]
# Functional forms of M* and phi*, can be linexp (linear and exponential) or
# logpower (for logarithmic and power law)
lum_fct_parametrization = "linexp"
# Filter band in which the luminosity function is valid
lum_fct_filter_band = "B"
# Schechter parameter alpha for blue galaxies
lum_fct_alpha_blue = -1.3
# Schechter parameter alpha for red galaxies
lum_fct_alpha_red = -0.5
# Parameter a in M*(z) = a*z + b for blue galaxies  (if linexp),
# M*(z) = a*log(1+z) + b (if logpower), M*: Schechter parameter
lum_fct_m_star_blue_slope = -0.9408582
# Parameter b in M*(z) = a*z + b for blue galaxies  (if linexp),
# M*(z) = a*log(1+z) + b (if logpower), M*: Schechter parameter
lum_fct_m_star_blue_intcpt = -20.40492365
# Parameter a in M*(z) = a*z + b for red galaxies  (if linexp),
# M*(z) = a*log(1+z) + b (if logpower), M*: Schechter parameter
lum_fct_m_star_red_slope = -0.70798041
# Parameter b in M*(z) = a*z + b for red galaxies  (if linexp),
# M*(z) = a*log(1+z) + b (if logpower), M*: Schechter parameter
lum_fct_m_star_red_intcpt = -20.37196157
# Parameter a in phi*(z) = a * exp(bz) for blue galaxies (if linexp),
# phi*(z) = a*(1+z)**b (if logpower), phi*: Schechter parameter
lum_fct_phi_star_blue_amp = 0.00370253
# Parameter b in phi*(z) = a * exp(bz) for blue galaxies (if linexp),
# phi*(z) = a*(1+z)**b (if logpower), phi*: Schechter parameter
lum_fct_phi_star_blue_exp = -0.10268436
# Parameter a in phi*(z) = a * exp(bz) for red galaxies(if linexp),
# phi*(z) = a*(1+z)**b (if logpower), phi*: Schechter parameter
lum_fct_phi_star_red_amp = 0.0035097
# Parameter b in phi*(z) = a * exp(bz) for red galaxies (if linexp),
# phi*(z) = a*(1+z)**b (if logpower), phi*: Schechter parameter
lum_fct_phi_star_red_exp = -0.70596888
# Parameter controlling the redshift after which M* for blue galaxies is constant
# if the lum_fct_parametrization = truncated_logexp
lum_fct_z_const_blue = 4
# Parameter controlling the redshift after which M* for red galaxies is constant
# if the lum_fct_parametrization = truncated_logexp
lum_fct_z_const_red = 4
# Resolution for sampling redshift
lum_fct_z_res = 0.001
# Maximum redshift of galaxies to sample
lum_fct_z_max = 3
# Maximum absolute magnitude to be sampled
lum_fct_m_max = -5
# Resolution for sampling absolute magnitudes
lum_fct_m_res = 0.001
# Maximum number of blue galaxies in one healpix pixel. This parameter has the function
# to limit runtime for ABC runs. A reasonable value critically depends on the healpix
# pixelization and the maximum absolute and apparent magnitudes.
n_gal_max_blue = np.inf
# Same as parameter above for red galaxies.
n_gal_max_red = np.inf
# If to raise an exception if the above limits are reached, or just to finish the
# calculation and continue
raise_max_num_gal_error = True
# Raise an error if there are some galaxies that are fainter than specified
raise_z_m_interp_error = False
# Memory limit for the size of the catalog in Mb (assuming 10 float64 columns per
# catalog), if reached, the UCatNumGalError is thrown, prevents jobs from crashing
max_memlimit_gal_catalog = np.inf
# Precision of the catalog.
catalog_precision = np.float64


# ----------
# Clustering
# ----------
apply_clustering_for_galaxy_positions = False


# ---------------------
# Template coefficients
# ---------------------
# Template coefficients are drawn from Dirichlet distributions of order 5 separately for
# blue and red galaxies.
# The parameters alpha of these distributions evolve with redshift. The evolution is
# parameterized 10 parameters, separately for blue and red galaxies: 5 parameters at
# redshift 0 and 5 parameters at redshift z1 > 0. Dirichlet
# parameters are calculated separately for each galaxy according to
# alpha(z) = (alpha0)^(1-z/z1) * (alpha1)^(z/z1),
# where alpha is five-dimensional. Thus, alpha(z=0) = alpha0 and alpha(z=z1) = alpha1
# with a smooth transition in between. Finally, after drawing the coefficients, they are
# weighted separately along each dimension.

# which sampling model to use.
# 'dirichlet': from Herbel et al. 2018,
# 'dirichlet_alpha_sum': enforce sum of alpha
# 'dirichlet_alpha_std': enforce standard deviation of alpha
# 'dirichlet_alpha_mode': use parameterisation with mode and standard deviation
template_coeff_sampler = "dirichlet"
# Redshift z1>0 for blue galaxies
template_coeff_z1_blue = 1
# Redshift z1>0 for red galaxies
template_coeff_z1_red = 1
# Dirichlet parameter for blue galaxies at z=0
template_coeff_alpha0_blue_0 = 1.9946549
# Dirichlet parameter for blue galaxies at z=0
template_coeff_alpha0_blue_1 = 1.99469164
# Dirichlet parameter for blue galaxies at z=0
template_coeff_alpha0_blue_2 = 1.99461187
# Dirichlet parameter for blue galaxies at z=0
template_coeff_alpha0_blue_3 = 1.9946589
# Dirichlet parameter for blue galaxies at z=0
template_coeff_alpha0_blue_4 = 1.99463069
# Dirichlet parameter for blue galaxies at z=z1
template_coeff_alpha1_blue_0 = template_coeff_alpha0_blue_0
# Dirichlet parameter for blue galaxies at z=z1
template_coeff_alpha1_blue_1 = template_coeff_alpha0_blue_1
# Dirichlet parameter for blue galaxies at z=z1
template_coeff_alpha1_blue_2 = template_coeff_alpha0_blue_2
# Dirichlet parameter for blue galaxies at z=z1
template_coeff_alpha1_blue_3 = template_coeff_alpha0_blue_3
# Dirichlet parameter for blue galaxies at z=z1
template_coeff_alpha1_blue_4 = template_coeff_alpha0_blue_4
# Dirichlet parameter for red galaxies at z=0
template_coeff_alpha0_red_0 = 1.62158197
# Dirichlet parameter for red galaxies at z=0
template_coeff_alpha0_red_1 = 1.62137391
# Dirichlet parameter for red galaxies at z=0
template_coeff_alpha0_red_2 = 1.62175061
# Dirichlet parameter for red galaxies at z=0
template_coeff_alpha0_red_3 = 1.62159144
# Dirichlet parameter for red galaxies at z=0
template_coeff_alpha0_red_4 = 1.62165971
# Dirichlet parameter for red galaxies at z=z1
template_coeff_alpha1_red_0 = template_coeff_alpha0_red_0
# Dirichlet parameter for red galaxies at z=z1
template_coeff_alpha1_red_1 = template_coeff_alpha0_red_1
# Dirichlet parameter for red galaxies at z=z1
template_coeff_alpha1_red_2 = template_coeff_alpha0_red_2
# Dirichlet parameter for red galaxies at z=z1
template_coeff_alpha1_red_3 = template_coeff_alpha0_red_3
# Dirichlet parameter for red galaxies at z=z1
template_coeff_alpha1_red_4 = template_coeff_alpha0_red_4
# std of the Dirichlet distribution for blue galaxies at z=0
template_coeff_alpha0_blue_std = 0.1
# std of the Dirichlet distribution for blue galaxies at z=z1
template_coeff_alpha1_blue_std = 0.1
# std of the Dirichlet distribution for red galaxies at z=0
template_coeff_alpha0_red_std = 0.1
# std of the Dirichlet distribution for red galaxies at z=z1
template_coeff_alpha1_red_std = 0.1
# Weights for blue and red galaxies applied after drawing the coefficients
template_coeff_weight_blue = np.array(
    [3.47116583e09, 3.31262983e06, 2.13298069e09, 1.63722853e10, 1.01368664e09]
)
template_coeff_weight_red = np.array(
    [3.84729278e09, 1.56768931e06, 3.91242928e08, 4.66363319e10, 3.03275998e07]
)
# If to store the SED in the catalog
save_SEDs = False

# ------------------------------
# Apparent magnitude calculation
# ------------------------------

# The way magnitudes are calculated
magnitude_calculation = "table"
# File containing filter throughputs
filters_file_name = "filters.h5"
# File containing template spectra
templates_file_name = "template_spectra.h5"
# File containing integration tables of template spectra for different filters
templates_int_tables_file_name = "template_integrals.h5"
# If True, copy the template integration table files to the current working directory
# (local scratch)
copy_template_int_tables_to_cwd = False
# Extinction map (expected to be in galactic coordinates)
extinction_map_file_name = "extinction.fits"
# Minimum galaxy magnitude cutoff
gals_mag_min = 16
# Maximum galaxy magnitude cutoff
gals_mag_max = 27
# Noise level corresponding to background flux, constant across bands (for abs mag
# calculation, see ABC for deepfields)
noise_const_abs_mag = None
# Redshift noise, z=sig*(1+z) Leigle et al 2015, doi:10.3847/0067-0049/224/2/24
noise_z_sigma = 0.007
# Redshift outlier fraction, from 0 to max_z present in catalog  Leigle et al 2015,
# doi:10.3847/0067-0049/224/2/24
noise_z_outlier_fraction = 0.005

# -------------------
# Sersic distribution
# -------------------

# Mean sersic n for mag<20 galaxies
sersic_n_mean_low = 0.2
# RMS sersic n for mag<20 galaxies
sersic_n_sigma_low = 1
# 1st mean sersic n for mag>20 galaxies
sersic_n_mean_1_hi = 0.3
# 1st RMS sersic n for mag>20 galaxies
sersic_n_sigma_1_hi = 0.5
# 2nd mean sersic n for mag>20 galaxies
sersic_n_mean_2_hi = 1.6
# 2nd RMS sersic n for mag>20 galaxies
sersic_n_sigma_2_hi = 0.4
# Minimum sersic n cutoff
sersic_n_offset = 0.2
# Switch sampling methods for sersic index
# default = use default from Berge et al 2012 (sersic_n_mean_low, sersic_n_sigma_low,
#    sersic_n_mean_1_hi, sersic_n_sigma_1_hi, sersic_n_mean_2_hi, sersic_n_sigma_2_hi,
#    sersic_n_offset)
# blue_red_fixed = use sersic_index_blue for blue and sersic_index_red for red
# single = use sersic_single_value for all galaxies
# blue_red_betaprime = use the betaprime distribution with mode and size, limited by
# (0.2, 10)
sersic_sampling_method = "blue_red_betaprime"
# Fixed sersic index all galaxies in case sersic_sampling_method = single
sersic_single_value = 1.0
# Fixed sersic index for blue galaxies in case sersic_sampling_method = blue_red_fixed
sersic_index_blue = 1.0
# Fixed sersic index for red galaxies in case sersic_sampling_method = blue_red_fixed
sersic_index_red = 4.0
# Sersic_betaprime model, peak for blue galaxies
sersic_betaprime_blue_mode = 0.8
# Sersic_betaprime model, spread for blue galaxies
sersic_betaprime_blue_size = 5
# Sersic_betaprime model, slope of the redshift dependence
sersic_betaprime_blue_mode_alpha = 0
# Sersic_betaprime model, peak for red galaxies
sersic_betaprime_red_mode = 1.5
# Sersic_betaprime model, spread for red galaxies
sersic_betaprime_red_size = 50
# Sersic_betaprime model, slope of the redshift dependence
sersic_betaprime_red_mode_alpha = 0
# Sersic_betaprime model, minimum sersic index
sersic_n_min = 0.2
# Sersic_betaprime model, maximum sersic index
sersic_n_max = 10

# ----------
# Size model
# ----------
# Physical sizes are sampled from a log-normal distribution and then transformed into
# apparent sizes using redshift and the input cosmology. The mean of the log of physical
# sizes depends linearly on the absolute magnitude of a galaxy:
# log(Mean physical sizes) = a * (Abs. mag.) + b
# The standard deviation of the distribution of the log of physical sizes is constant.

# Method to sample sizes:
# "single" - for the same distribution for red and blue, or
# "red_blue" for separate parameters
# "sdss_fit" - for the SDSS fit from Shen et al. 2003 (in that case use the sdss_fit
# parameters)
logr50_sampling_method = "single"
# shift to the absolute magnitude for the mean physical size of galaxies
logr50_phys_M0 = -20
# Slope of the evolution of the log of the mean physical size of galaxies (a in eq.
# above)
logr50_phys_mean_slope = -0.24293465
# Intercept of the evolution of the log of the mean physical size of galaxies (b in eq.
# above)
logr50_phys_mean_intcpt = 1.2268735
# Standard deviation of the log of physical sizes
logr50_phys_std = 0.56800081
# logr50_phys_mean_slope for red galaxies
logr50_phys_mean_slope_red = -0.24293465
# logr50_phys_mean_intcpt for red galaxies
logr50_phys_mean_intcpt_red = 1.2268735
# logr50_phys_std for red galaxies
logr50_phys_std_red = 0.56800081
# logr50_phys_mean_slope for blue galaxies
logr50_phys_mean_slope_blue = -0.24293465
# logr50_phys_mean_intcpt for blue galaxies
logr50_phys_mean_intcpt_blue = 1.2268735
# logr50_phys_std for blue galaxies
logr50_phys_std_blue = 0.56800081
# redshift dependence scaling factor parametrized with (1+z)**alpha, also for sdss_fit
logr50_alpha = 0
logr50_alpha_red = 0
logr50_alpha_blue = 0
# SDSS fit parameters (defaults to measurements for Fig. 4 of Shen et al. 2003)
logr50_sdss_fit_sigma1_red = 0.48
logr50_sdss_fit_sigma2_red = 0.25
logr50_sdss_fit_M0_red = -20.52
logr50_sdss_fit_a_red = 0.6
logr50_sdss_fit_b_red = -4.63
logr50_sdss_fit_sigma1_blue = 0.48
logr50_sdss_fit_sigma2_blue = 0.25
logr50_sdss_fit_M0_blue = -20.52
logr50_sdss_fit_alpha_blue = 0.21
logr50_sdss_fit_beta_blue = 0.53
logr50_sdss_fit_gamma_blue = -1.31


# ------------------------
# Ellipticity distribution
# ------------------------

# Mean galaxy e1 before PSF
e1_mean = 0
# RMS galaxy e1 before PSF
e1_sigma = 0.39
# Mean galaxy e2 before PSF
e2_mean = 0
# RMS galaxy e1 before PSF
e2_sigma = 0.39
# mean galaxy e1 for blue galaxies
e1_mean_blue = 0
# mean galaxy e2 for blue galaxies
e2_mean_blue = 0
# Sigma of a Gaussian for blue galaxies
ell_sigma_blue = 0.4600
# Sigma of a Gaussian for red galaxies
ell_sigma_red = 0.2
# Parameters for the ellipticity distribution for the
# ellipticity_sampling_method=blue_red_miller2013
ell_disc_log_a = -1.3708147902715042
ell_disc_emax = 0.8
ell_disc_min_e = 0.02
ell_disc_pow_alpha = 1

ell_bulge_b = 2.368
ell_bulge_c = 6.691

# Ratio of a and b parameters
ell_beta_ab_ratio = 0.57
# Mode of the ellipticity distribution
ell_beta_mode = 0.2
# Sum of a and b parameters of the beta distribution
ell_beta_ab_sum = 2.9
# Maximum ellipticity
ell_beta_emax = 0.98
# p(e) with beta_function and beta_function_mod for red galaxies: maximum ellipticity
ell_beta_mode_red = 0.2
# p(e) with beta_function and beta_function_mod for red galaxies: sum of a and b
# parameters of the beta distribution
ell_beta_ab_sum_red = 2.9
# p(e) with beta_function and beta_function_mode for blue galaxies: maximum ellipticity
ell_beta_mode_blue = 0.2
# p(e) with beta_function and beta_function_mode for blue galaxies: sum of a and b
# parameters of the beta distribution
ell_beta_ab_sum_blue = 2.9

# Switch sampling methods for ellipticity:
# default = use single Gaussian (e*_mean, e*_sigma),
# blue_red = use separate Gaussians for blue and red (ell_sigma_blue, ell_sigma_red)
# blue_red_miller2013 = use functions from Miller et al 2013 (ell_disc_log_a,
#       ell_disc_min_e, ell_bulge_b, ell_disc_pow_alpha)
# beta_ratio = use modified beta function (ell_beta_ab_ratio, ell_beta_ab_sum,
#       ell_beta_emax)
# beta_mode = use modified beta function (ell_beta_mode, ell_beta_ab_sum,
# ell_beta_emax)
# beta_mode_red_blue = same as beta_function_mode, but for different parameters
#       for red and blue
ellipticity_sampling_method = "beta_mode_red_blue"

# -----
# Shear
# -----

path_shear_map = None

gamma1_sign = -1
