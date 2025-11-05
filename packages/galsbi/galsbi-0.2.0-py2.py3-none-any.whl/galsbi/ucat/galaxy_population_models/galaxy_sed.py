# Copyright (C) 2018 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created 2021
author: Tomasz Kacprzak
"""

from collections import OrderedDict

import numpy as np

##########################################################
#
#        Sampling templates
#
##########################################################


def dirichlet_alpha_ev(z, alpha0, alpha1, z1):
    f = np.expand_dims(z, axis=-1) / z1
    alpha = alpha0 ** (1 - f) * alpha1**f
    return alpha


def draw_dirichlet_add_weight(alpha, weight):
    samples = alpha  # Modifies alpha in-place

    for i in range(alpha.shape[1]):
        samples[:, i] = np.random.gamma(alpha[:, i], scale=1)

    samples /= np.sum(samples, axis=1, keepdims=True)

    samples *= weight

    return samples


def sample_template_coeff_dirichlet__alpha_mode(
    z, amode0, amode1, z1, weight, alpha0_std, alpha1_std
):
    """
    Samples template coefficients from redshift-dependent Dirichlet distributions.
    See also docs/jupyter_notebooks/coeff_distribution_dirichlet.ipynb.
    Then the alpha0 and alpha1 will be scaled such that std(alpha)=alpha_std,
    for a equal alphas. alpha_std is also interpolated between redshifts.
    """

    def dir_mode_to_alpha(amode, sigma):
        assert np.allclose(np.sum(amode, axis=1), 1), "dirichlet amode must sum to 1"
        K = amode.shape[1]
        ms = 1 / sigma**2 * (1 / K - 1 / K**2) - K - 1
        alpha = 1 + amode * ms
        return alpha

    def dir_mode(alpha):
        return (alpha - 1) / (np.sum(alpha) - len(alpha))

    def get_max_sigma(k):
        return np.sqrt((1 / k - 1 / k**2) / (k + 1))

    # check alpha mode and interpolate in redshift
    for amode_ in (amode0, amode1):
        assert np.allclose(
            np.sum(amode_), 1
        ), "dirichlet amode coefficients must sum to 1"
    amode = dirichlet_alpha_ev(z, amode0, amode1, z1)
    amode /= np.sum(amode, axis=1, keepdims=True)

    # get maximum allowed sigma for given number of dimensions
    K = amode.shape[1]
    max_sig = get_max_sigma(K)

    # check standard deviation of alpha and interpolate
    for alpha_std_ in (alpha0_std, alpha1_std):
        assert alpha_std_ > 0, "dirichlet alpha_std must be >0"
        assert (
            alpha_std_ < max_sig
        ), f"dirichlet alpha0_std must be < max_sig for K={K} {max_sig:2.3e}"
    alpha_std = dirichlet_alpha_ev(z, alpha0_std, alpha1_std, z1)
    alpha_std = np.clip(alpha_std, a_min=1e-4, a_max=max_sig - 1e-4)

    # convert to Dirichlet alpha
    alpha = dir_mode_to_alpha(amode, alpha_std)

    # finally, draw the samples
    samples = draw_dirichlet_add_weight(alpha, weight)

    return samples


def sample_template_coeff_dirichlet(z, alpha0, alpha1, z1, weight):
    """
    Samples template coefficients from redshift-dependent Dirichlet distributions.
    See also docs/jupyter_notebooks/coeff_distribution_dirichlet.ipynb.
    """

    alpha = dirichlet_alpha_ev(z, alpha0, alpha1, z1)

    samples = draw_dirichlet_add_weight(alpha, weight)

    return samples


def sample_template_coeff_lumfuncs(par, redshift_z, n_templates):
    template_coeffs = OrderedDict()
    for g in redshift_z:
        z = redshift_z[g]
        alpha0 = np.array(
            [getattr(par, f"template_coeff_alpha0_{g}_{i}") for i in range(n_templates)]
        )
        alpha1 = np.array(
            [getattr(par, f"template_coeff_alpha1_{g}_{i}") for i in range(n_templates)]
        )
        z1 = getattr(par, f"template_coeff_z1_{g}")
        weight = getattr(par, f"template_coeff_weight_{g}")

        if par.template_coeff_sampler == "dirichlet":
            template_coeffs[g] = sample_template_coeff_dirichlet(
                z, alpha0, alpha1, z1, weight
            )

        elif par.template_coeff_sampler == "dirichlet_alpha_mode":
            template_coeffs[g] = sample_template_coeff_dirichlet__alpha_mode(
                z,
                alpha0,
                alpha1,
                z1,
                weight,
                alpha0_std=getattr(par, f"template_coeff_alpha0_{g}_std"),
                alpha1_std=getattr(par, f"template_coeff_alpha1_{g}_std"),
            )

    return template_coeffs
