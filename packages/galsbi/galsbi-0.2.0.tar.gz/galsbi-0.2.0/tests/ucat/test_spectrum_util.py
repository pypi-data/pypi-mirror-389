"""
Created on Aug 02, 2018
author: Joerg Herbel
"""

import numpy as np

from galsbi.ucat import spectrum_util


def test_extinction_coefficient():
    """
    Test the calculation of extinction coefficients.
    """

    # Wavelength in micrometre
    lam = np.linspace(1000, 10000, num=500) * 1e-4

    # Spline interpolation
    spline = spectrum_util.spline_ext_coeff()

    # Test using some random color excess
    for excess_b_v in np.random.uniform(low=0, high=0.5, size=10):
        extinction_coeff = spectrum_util.extinction_coefficient(
            lam, excess_b_v, spline
        )[0]

        # Check if all extinction coefficients are positive
        assert np.all(extinction_coeff >= 0)

        # Check if on average, the extinction coefficients decrease when the wavelength
        # increases (since bluer wavelengths suffer on average more from extinction -->
        # reddening).
        slope = np.polyfit(lam, extinction_coeff, 1)[0]
        assert slope < 0
