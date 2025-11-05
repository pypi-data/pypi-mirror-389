# Copyright (C) 2018 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Updated 11, 2021
by: Tomasz Kacprzak

Created on Mar 5, 2018
author: Joerg Herbel
"""

from galsbi.ucat.config import common

for name in [name for name in dir(common) if not name.startswith("__")]:
    globals()[name] = getattr(common, name)


plugins = ["ucat.plugins.sample_galaxies"]


maps_remote_dir = "ucat/resources/"

# Filter throughputs
filters_file_name = "filters_collection.h5"

# Template spectra & integration tables
n_templates = 5
magnitude_calculation = "table"
templates_file_name = "ucat/sed_templates/template_spectra_BlantonRoweis07.h5"
templates_int_tables_file_name = "sed_integrals__template_spectra_BlantonRoweis07.h5"


# Extinction
extinction_map_file_name = "lambda_sfd_ebv.fits"
