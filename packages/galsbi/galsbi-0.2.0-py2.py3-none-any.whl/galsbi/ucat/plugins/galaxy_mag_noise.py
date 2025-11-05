# Copyright (C) 2019 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created on Aug 2021
author: Tomasz Kacprzak
"""

import numpy as np
from cosmic_toolbox import logger
from ivy.plugin.base_plugin import BasePlugin

LOGGER = logger.get_logger(__file__)
SEED_OFFSET_MAG_NOISE = 14301


def mag_to_flux(mag):
    return 10 ** ((mag + 48.6) / (-2.5))


def flux_to_mag(flux):
    return -2.5 * np.log10(flux) - 48.6


class Plugin(BasePlugin):
    def __call__(self):
        par = self.ctx.parameters

        np.random.seed(SEED_OFFSET_MAG_NOISE + par.seed)

        if "galaxies" in self.ctx and par.noise_const_abs_mag is not None:
            for band, mag in self.ctx.galaxies.abs_magnitude_dict.items():
                flux_noisy = np.random.normal(
                    loc=mag_to_flux(mag),
                    scale=par.noise_const_abs_mag,
                    size=len(mag),
                )
                mag_noisy = flux_to_mag(flux_noisy)
                mag_noisy[np.isnan(mag_noisy)] = np.inf
                self.ctx.galaxies.abs_magnitude_dict[band] = mag_noisy

    def __str__(self):
        return "add noise to app_mags"
