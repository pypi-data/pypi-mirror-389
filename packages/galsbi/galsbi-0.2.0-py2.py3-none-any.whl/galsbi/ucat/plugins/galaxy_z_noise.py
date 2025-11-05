# Copyright (C) 2019 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created on Aug 2021
author: Tomasz Kacprzak
"""

import numpy as np
from cosmic_toolbox import logger
from ivy.plugin.base_plugin import BasePlugin

LOGGER = logger.get_logger(__file__)
SEED_OFFSET_Z_NOISE = 14302


def add_z_noise(z, delta_z, frac_outliers):
    sig = delta_z * (1 + z)
    z_noise = np.random.normal(z, sig, size=len(z))

    n_outliers = int(len(z) * frac_outliers)
    ind_outliers = np.random.choice(len(z), n_outliers)
    z_noise[ind_outliers] = np.random.uniform(low=0, high=z.max(), size=n_outliers)
    return z_noise


class Plugin(BasePlugin):
    def __call__(self):
        par = self.ctx.parameters
        np.random.seed(SEED_OFFSET_Z_NOISE)

        if "galaxies" in self.ctx:
            self.ctx.galaxies.z_noisy = add_z_noise(
                z=self.ctx.galaxies.z,
                delta_z=par.noise_z_sigma,
                frac_outliers=par.noise_z_outlier_fraction,
            )

    def __str__(self):
        return "add noise to redshift"
