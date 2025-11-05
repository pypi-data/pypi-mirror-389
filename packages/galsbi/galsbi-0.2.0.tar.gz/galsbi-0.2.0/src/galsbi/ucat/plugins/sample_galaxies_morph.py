# Copyright (C) 2018 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created 2021
author: Tomasz Kacprzak
"""

import numpy as np
import PyCosmo
from cosmic_toolbox import logger
from ivy.plugin.base_plugin import BasePlugin

from galsbi.ucat.galaxy_population_models.galaxy_light_profile import (
    sample_sersic_for_galaxy_type,
)
from galsbi.ucat.galaxy_population_models.galaxy_shape import (
    sample_ellipticities_for_galaxy_type,
)
from galsbi.ucat.galaxy_population_models.galaxy_size import sample_r50_for_galaxy_type

LOGGER = logger.get_logger(__file__)
SEED_OFFSET_LUMFUN = 123491


class Plugin(BasePlugin):
    """
    Generate a random catalog of galaxies with magnitudes in multiple bands.
    """

    def __call__(self):
        par = self.ctx.parameters

        # cosmology
        cosmo = PyCosmo.build()
        cosmo.set(h=par.h, omega_m=par.omega_m)

        # Initialize galaxy catalog
        assert hasattr(
            self.ctx, "galaxies"
        ), "galaxy catalog not initialized, perhaps run sample_galaxies_photo first"
        assert hasattr(
            self.ctx, "pixels"
        ), "pixels not initialized, perhaps run sample_galaxies_photo first"

        # add new columns
        morph_columns = [
            "sersic_n",
            "int_r50",
            "int_r50_arcsec",
            "int_r50_phys",
            "int_e1",
            "int_e2",
        ]
        self.ctx.galaxies.columns += morph_columns
        n_gal_total = len(self.ctx.galaxies.z)
        for c in morph_columns:
            setattr(
                self.ctx.galaxies, c, np.zeros(n_gal_total, dtype=par.catalog_precision)
            )

        # loop over luminosity functions
        for j, g in enumerate(par.galaxy_types):
            for i in range(len(self.ctx.pixels)):
                # get info about the sample
                select_type = self.ctx.galaxies.galaxy_type == j
                n_gal_ = np.count_nonzero(select_type)

                if n_gal_ == 0:
                    continue

                # sersic index
                np.random.seed(
                    par.seed + self.ctx.pixels[i] + par.gal_sersic_seed_offset
                )
                sersic_n = sample_sersic_for_galaxy_type(
                    n_gal=n_gal_,
                    galaxy_type=g,
                    app_mag=self.ctx.galaxies.int_magnitude_dict[par.reference_band][
                        select_type
                    ],
                    par=par,
                    z=self.ctx.galaxies.z[select_type],
                )

                # intrinsic size
                int_r50, int_r50_arcsec, int_r50_phys = sample_r50_for_galaxy_type(
                    z=self.ctx.galaxies.z[select_type],
                    abs_mag=self.ctx.galaxies.abs_magnitude_dict[par.reference_band][
                        select_type
                    ],
                    cosmo=cosmo,
                    par=par,
                    galaxy_type=g,
                )

                # intrinsic ellipticity
                np.random.seed(
                    par.seed + self.ctx.pixels[i] + par.gal_ellipticities_seed_offset
                )
                (
                    int_e1,
                    int_e2,
                ) = sample_ellipticities_for_galaxy_type(
                    n_gal=n_gal_, galaxy_type=g, par=par
                )

                # append lists
                self.ctx.galaxies.int_r50[select_type] = int_r50
                self.ctx.galaxies.int_r50_arcsec[select_type] = int_r50_arcsec
                self.ctx.galaxies.int_r50_phys[select_type] = int_r50_phys
                self.ctx.galaxies.sersic_n[select_type] = sersic_n
                self.ctx.galaxies.int_e1[select_type] = int_e1
                self.ctx.galaxies.int_e2[select_type] = int_e2

    def __str__(self):
        return "sample gal morph "
