# Copyright (C) 2024 ETH Zurich
# Institute for Particle Physics and Astrophysics
# Author: Silvan Fischbacher
# created: Thu Aug 01 2024


import ivy
import numpy as np
import pytest

from galsbi.ucat import galaxy_sampling_util
from galsbi.ucat.plugins import galaxy_mag_noise, galaxy_z_noise


@pytest.fixture
def ctx():
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )
    ctx.galaxies = galaxy_sampling_util.Catalog()
    ctx.galaxies.abs_magnitude_dict = {"g": np.array([-20, -21, -22])}
    return ctx


def test_galaxy_mag_noise(ctx):
    ctx.parameters.noise_const_abs_mag = 1e-15
    galaxy_mag_noise.Plugin(ctx)()
    for m, m_noisy in zip(
        [-20, -21, -22], ctx.galaxies.abs_magnitude_dict["g"], strict=True
    ):
        assert m != m_noisy


def test_galaxy_z_noise(ctx):
    ctx.galaxies.z = np.ones(1000)
    ctx.parameters.noise_z_sigma = 0.1
    ctx.parameters.noise_z_outlier_fraction = 0.1
    galaxy_z_noise.Plugin(ctx)()
    assert len(ctx.galaxies.z_noisy) == 1000
    z_noisy = ctx.galaxies.z_noisy
    z = ctx.galaxies.z

    # check that most z_noisy are within 2 sigma of z
    assert np.sum(np.abs(z_noisy - z) < 2 * ctx.parameters.noise_z_sigma) > 500

    # check that there are some outliers based on z_outlier_fraction
    assert np.sum(np.abs(z_noisy - z) > 2 * ctx.parameters.noise_z_sigma) > 50
