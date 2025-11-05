# Copyright (C) 2019 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created on Mar 27, 2019
author: Joerg Herbel
"""

import h5py
import healpy as hp
import numpy as np
from cosmic_toolbox import logger
from ivy.plugin.base_plugin import BasePlugin
from ufig import coordinate_util, io_util

from galsbi.ucat import lensing_util

LOGGER = logger.get_logger(__file__)


def evaluate_healpix_shear_map(path, ra, dec):
    """
    Reads in a healpix map and evaluates it at given positions.

    :param path: path where map is stored, assumes that file contains three maps (kappa,
        gamma1, gamma2)
    :param ra: right ascension where map is evaluated
    :param dec: declinations where map is evaluated
    :return: kappa, gamma1 and gamma2 evaluated at input positions
    """

    # read map
    map_kappa, map_gamma_1, map_gamma_2 = hp.read_map(path, field=(0, 1, 2))

    # get pixel indices
    pixel_ind = coordinate_util.radec2pix(ra, dec, hp.npix2nside(map_kappa.size))

    # read out pixels
    kappa = map_kappa[pixel_ind]
    gamma_1 = map_gamma_1[pixel_ind]
    gamma_2 = map_gamma_2[pixel_ind]

    return kappa, gamma_1, gamma_2


def linear_interpolation(x0, y0, x1, y1, x):
    """
    Vectorized linear interpolation between two data points.

    :param x0: x-coordinates of first data points
    :param y0: y-coordinates of first data points
    :param x1: x-coordinates of second data points
    :param y1: y-coordinates of second data points
    :param x: positions where interpolation is evaluated
    :return: interpolated values
    """
    y = y0 + (x - x0) * (y1 - y0) / (x1 - x0)
    return y


def interpolate_maps_fast(z_maps, maps, z, pixel_ind, ind_intervals):
    """
    Linearly interpolate to input redshifts between healpix maps at given redshifts.

    :param z_maps: redshifts of input maps, assumed to be ordered
    :param maps: input maps corresponding to z_maps, type: hdf5-dataset or numpy-array
    :param z: redshifts to which maps will be interpolated, assumed to be sorted
    :param pixel_ind: indices indicating pixels of input maps to interpolate, same size
                      as z
    :param ind_intervals: indices splitting up z into chunks that lie between the maps
    :return: interpolated values
    """

    pixel_unique, indices_inv = np.unique(pixel_ind, return_inverse=True)
    pixel_min, pixel_max = pixel_unique.min(), pixel_unique.max()
    maps_slab = maps[:, pixel_min : pixel_max + 1]  # hdf read-in with hyperslabs
    maps_unique = maps_slab[:, pixel_unique - pixel_unique[0]]
    maps_ind = maps_unique[:, indices_inv]

    intpol_values = np.empty_like(z)

    # galaxies at redshifts lower than the first map --> interpolate between zero shear
    # at z=0 and first map
    intpol_values[: ind_intervals[0]] = linear_interpolation(
        0,
        np.zeros(ind_intervals[0]),
        z_maps[0],
        maps_ind[0, : ind_intervals[0]],
        z[: ind_intervals[0]],
    )

    # galaxies in between two maps
    for i_map in range(len(ind_intervals) - 1):
        ind_low = ind_intervals[i_map]
        ind_up = ind_intervals[i_map + 1]
        intpol_values[ind_low:ind_up] = linear_interpolation(
            z_maps[i_map],
            maps_ind[i_map, ind_low:ind_up],
            z_maps[i_map + 1],
            maps_ind[i_map + 1, ind_low:ind_up],
            z[ind_low:ind_up],
        )

    # galaxies at redshifts higher than the last map --> use last map to set shear
    # values
    intpol_values[ind_intervals[-1] :] = maps_ind[-1, ind_intervals[-1] :]

    return intpol_values


def interpolate_maps(z_maps, maps, z, pixel_ind, ind_intervals):
    """
    Linearly interpolate to input redshifts between healpix maps at given redshifts.

    :param z_maps: redshifts of input maps, assumed to be ordered
    :param maps: input maps corresponding to z_maps, type: hdf5-dataset or numpy-array
    :param z: redshifts to which maps will be interpolated, assumed to be sorted
    :param pixel_ind: indices indicating pixels of input maps to interpolate, same size
                      as z
    :param ind_intervals: indices splitting up z into chunks that lie between the maps
    :return: interpolated values
    """

    intpol_values = np.empty_like(z)
    map_low = np.empty(maps.shape[1], dtype=maps.dtype)
    map_up = maps[0][...]

    # galaxies at redshifts lower than the first map --> interpolate between zero shear
    # at z=0 and first map
    intpol_values[: ind_intervals[0]] = linear_interpolation(
        0,
        np.zeros(ind_intervals[0]),
        z_maps[0],
        map_up[pixel_ind[: ind_intervals[0]]],
        z[: ind_intervals[0]],
    )

    # galaxies in between two maps
    for i_map in range(len(ind_intervals) - 1):
        ind_low = ind_intervals[i_map]
        ind_up = ind_intervals[i_map + 1]
        map_low[:] = map_up
        map_up[:] = maps[i_map + 1][...]

        intpol_values[ind_low:ind_up] = linear_interpolation(
            z_maps[i_map],
            map_low[pixel_ind[ind_low:ind_up]],
            z_maps[i_map + 1],
            map_up[pixel_ind[ind_low:ind_up]],
            z[ind_low:ind_up],
        )

    # galaxies at redshifts higher than the last map --> use last map to set shear
    # values
    intpol_values[ind_intervals[-1] :] = map_up[pixel_ind[ind_intervals[-1] :]]

    return intpol_values


def evaluate_hdf5_shear_maps(path, ra, dec, z):
    """
    Evaluate hdf5 shear maps given at multiple redshifts for given redshifts and angular
    positions.

    :param path: path to hdf5 file containing shear maps; assumes that this file
                 contains four datasets:
                 - z: redshifts of maps
                 - kappa: kappa-maps
                 - gamma1: gamma1-maps
                 - gamma2: gamma2-maps
    :param ra: right ascensions where maps will be evaluated
    :param dec: declinations where maps will be evaluated
    :param z: redshifts to which maps will be interpolated
    :return: kappa, gamma1 and gamma2
    """

    # sort by redshift
    ind_sort = np.argsort(z)
    ra = ra[ind_sort]
    dec = dec[ind_sort]
    z = z[ind_sort]

    with h5py.File(path, mode="r") as fh5:
        # get redshifts of maps, assumed to be sorted
        # print('{} reading shear map file {}'.format(str(datetime.now()), path))
        LOGGER.info(f"reading shear map file {path}")
        z_maps = fh5["z"][...]

        # compute pixel indices
        pixel_ind = coordinate_util.radec2pix(
            ra, dec, hp.npix2nside(fh5["kappa"].shape[1])
        )

        # sort galaxies into redshift intervals between the maps
        ind_intervals = np.searchsorted(z, z_maps)

        # read out maps and interpolate
        LOGGER.info(f"reading maps and interpolating for {len(z)} objects")
        kappa = interpolate_maps_fast(z_maps, fh5["kappa"], z, pixel_ind, ind_intervals)
        gamma1 = interpolate_maps_fast(
            z_maps, fh5["gamma1"], z, pixel_ind, ind_intervals
        )
        gamma2 = interpolate_maps_fast(
            z_maps, fh5["gamma2"], z, pixel_ind, ind_intervals
        )

    # undo sorting by redshift
    ind_unsort = np.argsort(ind_sort)
    kappa[:] = kappa[ind_unsort]
    gamma1[:] = gamma1[ind_unsort]
    gamma2[:] = gamma2[ind_unsort]

    return kappa, gamma1, gamma2


class Plugin(BasePlugin):
    """
    Apply a potentially redshift-dependent shear from input shear maps specified by
    ctx.parameters.path_shear_map. Only first-order effects due to gamma are applied,
    kappa is completely ignored.
    There are three options:

    1. The path is None, which will result in zero shear.
    2. The path is a file readable by healpy. The file is then assumed to contain 3
        healpix maps (kappa, gamma1, gamma2).
    3. The path is and hdf5-file containing multiple, kappa-, gamma1- and gamma2-maps at
        given redshifts. The shear values are computed by interpolating linearly between
        the maps.
    """

    def __call__(self):
        par = self.ctx.parameters

        # first check if path of shear map is set to None --> zero shear
        if par.path_shear_map is None:
            self.ctx.galaxies.kappa = np.zeros(self.ctx.numgalaxies, dtype=float)
            self.ctx.galaxies.gamma1 = np.zeros_like(self.ctx.galaxies.kappa)
            self.ctx.galaxies.gamma2 = np.zeros_like(self.ctx.galaxies.kappa)

        else:
            ra, dec = coordinate_util.xy2radec(
                coordinate_util.wcs_from_parameters(par),
                self.ctx.galaxies.x,
                self.ctx.galaxies.y,
            )

            path_shear_map = io_util.get_abs_path(
                par.path_shear_map, root_path=par.maps_remote_dir
            )

            if h5py.is_hdf5(path_shear_map):
                LOGGER.info(
                    "Shear map file is in hdf5-format, assuming multiple"
                    " shear maps at different redshifts"
                )
                (
                    self.ctx.galaxies.kappa,
                    self.ctx.galaxies.gamma1,
                    self.ctx.galaxies.gamma2,
                ) = evaluate_hdf5_shear_maps(
                    path=path_shear_map, ra=ra, dec=dec, z=self.ctx.galaxies.z
                )
            else:
                LOGGER.info(
                    "Shear map file is not in hdf5-format, assuming a single"
                    " shear map stored in fits-format"
                )
                (
                    self.ctx.galaxies.kappa,
                    self.ctx.galaxies.gamma1,
                    self.ctx.galaxies.gamma2,
                ) = evaluate_healpix_shear_map(path=path_shear_map, ra=ra, dec=dec)

        # apply sign to gamma1
        self.ctx.galaxies.gamma1 *= par.gamma1_sign

        # scale size
        self.ctx.galaxies.r50 = lensing_util.calculate_size_magnification(
            r=self.ctx.galaxies.int_r50, kappa=self.ctx.galaxies.kappa
        )
        # convert to arcsec
        self.ctx.galaxies.r50_arcsec = self.ctx.galaxies.r50 * par.pixscale

        # shear ellipticities
        LOGGER.info("applying shear and magnification")
        (
            self.ctx.galaxies.e1,
            self.ctx.galaxies.e2,
        ) = lensing_util.apply_shear_to_ellipticities(
            self.ctx.galaxies.int_e1,
            self.ctx.galaxies.int_e2,
            self.ctx.galaxies.kappa,
            self.ctx.galaxies.gamma1,
            self.ctx.galaxies.gamma2,
        )

        # magnify flux

        # magnification in terms of flux, see Bartelmann & Schneider 2001,
        # https://arxiv.org/pdf/astro-ph/9912508.pdf, eq. (3.14)
        magnification = lensing_util.calculate_flux_magnification(
            self.ctx.galaxies.kappa, self.ctx.galaxies.gamma1, self.ctx.galaxies.gamma2
        )

        # in terms of magnitudes
        magnification[:] = 2.5 * np.log10(magnification)

        for mag in self.ctx.galaxies.magnitude_dict.values():
            mag -= magnification

        # add new columns to list
        self.ctx.galaxies.columns.extend(
            ["gamma1", "gamma2", "kappa", "e1", "e2", "r50", "r50_arcsec"]
        )

    def __str__(self):
        return "apply shear"
