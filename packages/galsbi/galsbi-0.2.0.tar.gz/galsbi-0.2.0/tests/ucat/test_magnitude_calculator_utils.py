# Copyright (C) 2024 ETH Zurich
# Institute for Particle Physics and Astrophysics
# Author: Silvan Fischbacher
# created: Wed Sep 04 2024


import numpy as np

from galsbi.ucat.magnitude_calculator import AB_mag_to_flux, flux_to_AB_mag


def test_conversion():
    flux = np.array([1, 2, 3])
    mag = flux_to_AB_mag(flux)
    flux2 = AB_mag_to_flux(mag)
    assert np.allclose(flux, flux2)
