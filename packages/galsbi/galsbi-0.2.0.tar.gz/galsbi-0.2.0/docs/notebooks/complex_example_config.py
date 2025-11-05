import os

from cosmo_torrent import data_path

import galsbi.ucat.config.common

# Import all common settings from ucat and ufig
for name in [
    name for name in dir(galsbi.ucat.config.common) if not name.startswith("__")
]:
    globals()[name] = getattr(galsbi.ucat.config.common, name)

plugins = [
    "galsbi.ucat.plugins.sample_galaxies",
    "galsbi.ucat.plugins.apply_shear",
    "galsbi.ucat.plugins.write_catalog_photo",
    "galsbi.ucat.plugins.write_catalog",
    "ivy.plugin.show_stats",
]

filters_file_name = os.path.join(
    data_path("HSC_tables"), "HSC_filters_collection_yfix.h5"
)
templates_file_name = os.path.join(
    data_path("template_BlantonRoweis07"), "template_spectra_BlantonRoweis07.h5"
)
extinction_map_file_name = os.path.join(
    data_path("lambda_sfd_ebv"), "lambda_sfd_ebv.fits"
)
templates_int_tables_file_name = os.path.join(
    data_path("HSC_tables"), "HSC_template_integrals_yfix.h5"
)

filepath_tile = os.getcwd()
