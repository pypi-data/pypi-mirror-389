# Copyright (C) 2019 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created on Mar 28, 2019
@author: Joerg Herbel
"""

import copy
import os

import h5py
import healpy as hp
import ivy
import numpy as np
from ufig import coordinate_util

from galsbi.ucat import galaxy_sampling_util, lensing_util
from galsbi.ucat.plugins import apply_shear


def sample_ellipticities(n):
    return np.random.uniform(low=-0.1, high=0.1, size=n)


def write_healpix_map(path, kappa_map, gamma1_map, gamma2_map):
    hp.write_map(
        path,
        m=(kappa_map, gamma1_map, gamma2_map),
        dtype=gamma1_map.dtype,
        fits_IDL=False,
        coord="C",
        overwrite=True,
    )


def write_hdf5_maps(path, z, kappa_maps, gamma1_maps, gamma2_maps):
    with h5py.File(path, mode="w") as fh5:
        fh5.create_dataset(name="z", data=z)
        fh5.create_dataset(name="kappa", data=kappa_maps)
        fh5.create_dataset(name="gamma1", data=gamma1_maps)
        fh5.create_dataset(name="gamma2", data=gamma2_maps)


def test_evaluate_healpix_shear_map():
    """
    Tests the evaluation of a healpix shear map.
    """

    nside = 8
    npix = hp.nside2npix(nside)
    path = "map.fits"

    # create dummy map
    kappa_map = np.random.uniform(low=-0.025, high=0.15, size=npix)
    gamma1_map = sample_ellipticities(npix)
    gamma2_map = sample_ellipticities(npix)
    write_healpix_map(path, kappa_map, gamma1_map, gamma2_map)

    # get coordinates of pixel centers
    theta, phi = hp.pix2ang(nside, np.arange(npix))
    ra, dec = coordinate_util.thetaphi2radec(theta, phi)

    # read out map and test
    kappa, gamma1, gamma2 = apply_shear.evaluate_healpix_shear_map(path, ra, dec)
    assert np.array_equal(kappa_map, kappa)
    assert np.array_equal(gamma1_map, gamma1)
    assert np.array_equal(gamma2_map, gamma2)

    # delete
    os.remove(path)


def test_linear_interpolation():
    """
    Tests the linear interpolation.
    """
    x0 = np.random.uniform(low=-1, high=1, size=10)
    x1 = x0 + np.random.uniform(low=0, high=1, size=x0.size)
    y0 = np.random.uniform(low=-1, high=1, size=x0.size)
    y1 = np.random.uniform(low=-1, high=1, size=x0.size)
    x = x0 + (x1 - x0) * np.random.uniform(low=0, high=1, size=x0.size)
    y = apply_shear.linear_interpolation(x0, y0, x1, y1, x)

    for i in range(y.size):
        assert np.allclose(y[i], np.interp(x[i], [x0[i], x1[i]], [y0[i], y1[i]]))


def test_interpolate_maps():
    """
    Test the interpolation of shear maps.
    """

    # create fake maps
    nside = 8
    npix = hp.nside2npix(nside)
    pix_ind = np.random.choice(npix, replace=True, size=1000)
    z_maps = np.array([0.01, 0.5, 1.0])
    maps = np.empty((z_maps.size, npix))
    maps[0] = 0.1
    maps[1] = -0.05
    maps[2] = 0.3

    # 1) test case where all galaxies are below the lowest map redshift
    z = np.linspace(0, 0.005, num=pix_ind.size)
    ind_intervals = np.full(z_maps.size, z.size)
    intpol_vals = apply_shear.interpolate_maps(z_maps, maps, z, pix_ind, ind_intervals)
    assert np.all(intpol_vals < maps[0, 0])
    assert np.array_equal(intpol_vals, np.sort(intpol_vals))

    # 2) test case where galaxies are distributed across the range, including above and
    # below
    z = np.linspace(0, z_maps[-1] + 0.1, num=pix_ind.size)
    ind_intervals = np.searchsorted(z, z_maps)
    intpol_vals = apply_shear.interpolate_maps(z_maps, maps, z, pix_ind, ind_intervals)
    assert np.all(np.fabs(intpol_vals[: ind_intervals[0]]) < maps[0, 0])
    assert np.all(intpol_vals[ind_intervals[-1] :] == maps[-1, 0])

    for i in range(len(ind_intervals) - 1):
        assert np.all(
            intpol_vals[ind_intervals[i] : ind_intervals[i + 1]]
            <= np.amax(maps[[i, i + 1], 0])
        )
        assert np.all(
            intpol_vals[ind_intervals[i] : ind_intervals[i + 1]]
            >= np.amin(maps[[i, i + 1], 0])
        )

    # 3) test the case where all galaxies are above the highest map redshift
    z = np.arange(z_maps[-1] + 1, z_maps[-1] + 1 + pix_ind.size)
    ind_intervals = np.zeros(z_maps.size, dtype=int)
    intpol_vals = apply_shear.interpolate_maps(z_maps, maps, z, pix_ind, ind_intervals)
    assert np.all(intpol_vals == maps[-1, 0])


def test_evaluate_hdf5_shear_maps():
    """
    Tests the evaluation of multiple shear maps stored in hdf5 format.
    """

    # create and write fake map
    path = "test.h5"
    nside = 8
    npix = hp.nside2npix(nside)
    z_maps = np.array([0.1, 1])
    kappa_maps = np.empty((z_maps.size, npix))
    gamma1_maps = np.empty((z_maps.size, npix))
    gamma2_maps = np.empty((z_maps.size, npix))
    kappa_maps[0] = -0.003
    kappa_maps[1] = 0.05
    gamma1_maps[0] = -0.05
    gamma1_maps[1] = 0.3
    gamma2_maps[0] = 0.7
    gamma2_maps[1] = 0.4
    write_hdf5_maps(path, z_maps, kappa_maps, gamma1_maps, gamma2_maps)

    # define redshift and angular positions
    z = np.array([5, 0.0001, 0.7, 0.2])
    ra = np.zeros_like(z)
    dec = np.zeros_like(z)

    # evaluate
    kappa, gamma1, gamma2 = apply_shear.evaluate_hdf5_shear_maps(path, ra, dec, z)

    # check order
    assert kappa[0] == kappa_maps[-1, 0]
    assert kappa[1] > kappa_maps[0, 0]
    assert kappa[2] < kappa[0]
    assert kappa[3] < kappa[2]
    assert kappa[3] > kappa_maps[0, 0]

    assert gamma1[0] == gamma1_maps[-1, 0]
    assert gamma1[1] > gamma1_maps[0, 0]
    assert gamma1[2] < gamma1[0]
    assert gamma1[3] < gamma1[2]
    assert gamma1[3] > gamma1_maps[0, 0]

    assert gamma2[0] == gamma2_maps[-1, 0]
    assert gamma2[1] < gamma2_maps[0, 0]
    assert gamma2[2] > gamma2[0]
    assert gamma2[3] > gamma2[2]
    assert gamma2[3] < gamma2_maps[0, 0]

    # delete map file
    os.remove(path)


def test_apply_shear_to_ellipticities():
    """
    Tests the transformation of intrinsic ellipticities to sheared ellipticities.
    """

    # check that zero shear does not change ellipticities
    int_e1 = sample_ellipticities(10)
    int_e2 = sample_ellipticities(10)
    kappa = np.zeros_like(int_e1)
    gamma1 = np.zeros_like(int_e1)
    gamma2 = np.zeros_like(int_e2)
    e1, e2 = lensing_util.apply_shear_to_ellipticities(
        int_e1, int_e2, kappa, gamma1, gamma2
    )
    assert np.array_equal(int_e1, e1)
    assert np.array_equal(int_e2, e2)

    # check that zero intrinsic ellipticity results in correct values, namely
    # 2 * g / (1 + |g|^2)
    int_e1 *= 0
    int_e2 *= 0
    kappa = np.random.uniform(low=-0.025, high=0.15, size=10)
    gamma1 = sample_ellipticities(10)
    gamma2 = sample_ellipticities(10)
    g1 = gamma1 / (1 - kappa)
    g2 = gamma2 / (1 - kappa)
    e1, e2 = lensing_util.apply_shear_to_ellipticities(
        int_e1, int_e2, kappa, gamma1, gamma2
    )
    assert np.allclose(e1, 2 * g1 / (1 + g1**2 + g2**2))
    assert np.allclose(e2, 2 * g2 / (1 + g1**2 + g2**2))


def test_apply_shear():
    """
    Tests the execution of the plugin apply_shear.
    """

    ctx = ivy.context.create_ctx(
        numgalaxies=100,
        galaxies=galaxy_sampling_util.Catalog(),
        parameters=ivy.context.create_ctx(
            path_shear_map=None,
            gamma1_sign=1,
            size_x=100,
            size_y=100,
            ra0=0,
            dec0=0,
            pixscale=0.3,
            maps_remote_dir=os.getcwd(),
        ),
    )

    magnitude_dict = dict(
        r=np.random.uniform(low=15, high=25, size=ctx.numgalaxies),
        i=np.random.uniform(low=15, high=25, size=ctx.numgalaxies),
    )

    ctx.galaxies.x = np.zeros(ctx.numgalaxies)
    ctx.galaxies.y = np.zeros(ctx.numgalaxies)
    ctx.galaxies.z = np.random.uniform(low=0, high=1, size=ctx.numgalaxies)
    ctx.galaxies.int_e1 = sample_ellipticities(ctx.numgalaxies)
    ctx.galaxies.int_e2 = sample_ellipticities(ctx.numgalaxies)
    ctx.galaxies.int_r50 = np.ones_like(ctx.galaxies.int_e1)
    ctx.galaxies.int_r50_arcsec = (
        np.ones_like(ctx.galaxies.int_e1) * ctx.parameters.pixscale
    )
    ctx.galaxies.magnitude_dict = copy.deepcopy(magnitude_dict)
    ctx.galaxies.columns = []

    # 1) Test no shear case
    apply_shear.Plugin(ctx)()
    assert np.all(ctx.galaxies.kappa == 0)
    assert np.all(ctx.galaxies.gamma1 == 0)
    assert np.all(ctx.galaxies.gamma2 == 0)
    assert np.all(ctx.galaxies.kappa == 0)
    assert np.array_equal(ctx.galaxies.e1, ctx.galaxies.int_e1)
    assert np.array_equal(ctx.galaxies.e2, ctx.galaxies.int_e2)
    assert np.array_equal(ctx.galaxies.r50, ctx.galaxies.int_r50)
    assert ctx.galaxies.columns == [
        "gamma1",
        "gamma2",
        "kappa",
        "e1",
        "e2",
        "r50",
        "r50_arcsec",
    ]

    # 2) Test if healpix shear map works
    ctx.parameters.path_shear_map = "test.fits"
    nside = 8
    npix = hp.nside2npix(nside)
    kappa_map = np.full(npix, 0.02)
    gamma1_map = np.full(npix, 0.01)
    gamma2_map = np.full(npix, -0.05)
    write_healpix_map(ctx.parameters.path_shear_map, kappa_map, gamma1_map, gamma2_map)
    apply_shear.Plugin(ctx)()
    assert np.all(ctx.galaxies.kappa == 0.02)
    assert np.all(ctx.galaxies.gamma1 == 0.01)
    assert np.all(ctx.galaxies.gamma2 == -0.05)

    # test signflip
    ctx.parameters.gamma1_sign = -1
    apply_shear.Plugin(ctx)()
    assert np.all(ctx.galaxies.gamma1 == -0.01)

    # test magnification
    kappa_map = np.random.uniform(low=-0.025, high=0.15, size=npix)
    gamma1_map = np.random.uniform(low=-0.1, high=0.1, size=npix)
    gamma2_map = np.random.uniform(low=-0.1, high=0.1, size=npix)
    write_healpix_map(ctx.parameters.path_shear_map, kappa_map, gamma1_map, gamma2_map)
    ctx.galaxies.magnitude_dict = copy.deepcopy(magnitude_dict)
    apply_shear.Plugin(ctx)()

    magnification = 1 / (
        (1 - ctx.galaxies.kappa) ** 2 - ctx.galaxies.gamma1**2 - ctx.galaxies.gamma2**2
    )
    select_magnified = magnification > 1
    select_demagnified = ~select_magnified

    for band, unlensed_mag in magnitude_dict.items():
        assert np.all(
            unlensed_mag[select_magnified]
            > ctx.galaxies.magnitude_dict[band][select_magnified]
        )
        assert np.all(
            unlensed_mag[select_demagnified]
            < ctx.galaxies.magnitude_dict[band][select_demagnified]
        )

    # remove written healpix shear map
    os.remove(ctx.parameters.path_shear_map)

    # 3) Test if hdf5 shear maps work
    ctx.parameters.path_shear_map = "test.h5"
    ctx.parameters.gamma1_sign = 1
    z_maps = np.array([0.1, 0.4, 0.6])
    kappa_maps = np.full((z_maps.size, npix), 0.001)
    gamma1_maps = np.full((z_maps.size, npix), 0.03)
    gamma2_maps = np.full((z_maps.size, npix), -0.04)
    write_hdf5_maps(
        ctx.parameters.path_shear_map, z_maps, kappa_maps, gamma1_maps, gamma2_maps
    )
    apply_shear.Plugin(ctx)()
    select_up = ctx.galaxies.z >= z_maps[0]
    assert np.all(ctx.galaxies.kappa[select_up] == 0.001)
    assert np.all(ctx.galaxies.gamma1[select_up] == 0.03)
    assert np.all(ctx.galaxies.gamma2[select_up] == -0.04)
    assert np.all(ctx.galaxies.kappa[~select_up] < 0.001)
    assert np.all(ctx.galaxies.gamma1[~select_up] < 0.03)
    assert np.all(ctx.galaxies.gamma2[~select_up] > -0.04)
    # test signflip
    gamma1_unflipped = ctx.galaxies.gamma1.copy()
    ctx.parameters.gamma1_sign = -1
    apply_shear.Plugin(ctx)()
    assert np.array_equal(ctx.galaxies.gamma1, -gamma1_unflipped)
    os.remove(ctx.parameters.path_shear_map)


def test_distortion_and_shear_transformation():
    e1 = np.random.uniform(low=-0.1, high=0.1, size=100)
    e2 = np.random.uniform(low=-0.1, high=0.1, size=100)

    g1, g2 = lensing_util.distortion_to_shear(e1, e2)
    e1_out, e2_out = lensing_util.shear_to_distortion(g1, g2)

    assert np.allclose(e1, e1_out)
    assert np.allclose(e2, e2_out)


def test_moments_and_distortion_transformation():
    xx = np.random.uniform(low=0.1, high=1, size=100)
    yy = np.random.uniform(low=0.1, high=1, size=100)
    xy = np.random.uniform(low=0.1, high=1, size=100)

    e1, e2, fwhm = lensing_util.moments_to_distortion(xx, yy, xy)
    xx_out, yy_out, xy_out = lensing_util.distortion_to_moments(fwhm, e1, e2)

    assert np.allclose(xx, xx_out)
    assert np.allclose(yy, yy_out)
    assert np.allclose(xy, xy_out)


def test_shear_and_moments_transformation():
    g1 = np.random.uniform(low=-0.1, high=0.1, size=100)
    g2 = np.random.uniform(low=-0.1, high=0.1, size=100)
    fwhm = np.random.uniform(low=0.1, high=1, size=100)

    xx, yy, xy = lensing_util.shear_to_moments(g1, g2, fwhm)
    g1_out, g2_out, fwhm_out = lensing_util.moments_to_shear(xx, yy, xy)
    assert np.allclose(g1, g1_out)
    assert np.allclose(g2, g2_out)
