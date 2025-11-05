# Copyright (C) 2019 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created on Aug 2021
author: Tomasz Kacprzak
"""

import os

import h5py
from cosmic_toolbox import logger
from ivy.plugin.base_plugin import BasePlugin

LOGGER = logger.get_logger(__file__)
KW_COMPRESS = dict(compression="lzf", shuffle=True)


def get_ucat_catalog_filename():
    return "ucat_photo.h5"


class Plugin(BasePlugin):
    def __call__(self):
        par = self.ctx.parameters

        # columns independent of band
        cols_base = [
            "z",
            "z_noisy",
            "galaxy_type",
            "template_coeffs",
            "template_coeffs_abs",
        ]

        # make output dirs if needed
        if not os.path.isdir(par.filepath_tile):
            os.makedirs(par.filepath_tile)

        # write catalogs
        filepath_out = os.path.join(par.filepath_tile, get_ucat_catalog_filename())
        with h5py.File(filepath_out, "w") as f:
            for col in cols_base:
                if hasattr(self.ctx.galaxies, col):
                    f.create_dataset(
                        name=col, data=getattr(self.ctx.galaxies, col), **KW_COMPRESS
                    )

            for b in par.filters:
                f.create_dataset(
                    name=f"int_mag_{b}",
                    data=self.ctx.galaxies.int_magnitude_dict[b],
                    **KW_COMPRESS,
                )
                f.create_dataset(
                    name=f"abs_mag_{b}",
                    data=self.ctx.galaxies.abs_magnitude_dict[b],
                    **KW_COMPRESS,
                )
                f.create_dataset(
                    name=f"mag_{b}",
                    data=self.ctx.galaxies.magnitude_dict[b],
                    **KW_COMPRESS,
                )

    def __str__(self):
        return "write ucat photo to file"
