# Copyright (C) 2018 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created on Mar 5, 2018
author: Joerg Herbel
"""

import os
import warnings

import healpy as hp
import numpy as np
import PyCosmo
from astropy.coordinates import SkyCoord
from cosmic_toolbox import logger
from ivy.plugin.base_plugin import BasePlugin
from ufig import coordinate_util, io_util

from galsbi.ucat import (
    filters_util,
    galaxy_sampling_util,
    sed_templates_util,
    spectrum_util,
    utils,
)
from galsbi.ucat.filters_util import UseShortFilterNames
from galsbi.ucat.galaxy_population_models.galaxy_luminosity_function import (
    initialize_luminosity_functions,
)
from galsbi.ucat.galaxy_population_models.galaxy_position import sample_position_uniform
from galsbi.ucat.galaxy_population_models.galaxy_sed import (
    sample_template_coeff_lumfuncs,
)

LOGGER = logger.get_logger(__file__)
SEED_OFFSET_LUMFUN = 123491
warnings.filterwarnings("once")


class ExtinctionMapEvaluator:
    """
    Class that gives extinction values for positions
    """

    def __init__(self, par):
        if par.extinction_map_file_name is not None:
            extinction_map_file_name = io_util.get_abs_path(
                par.extinction_map_file_name, root_path=par.maps_remote_dir
            )
            self.extinction_map = hp.read_map(
                extinction_map_file_name, nest=True, field=0
            )

        else:
            self.extinction_map = None

    def __call__(self, wcs, x, y):
        if self.extinction_map is not None:
            if wcs is not None:
                ra, dec = coordinate_util.xy2radec(wcs, x, y)
            else:
                ra, dec = x, y
            sky_coord = SkyCoord(ra=ra, dec=dec, frame="icrs", unit="deg")
            gal_lon = sky_coord.galactic.l.deg
            gal_lat = sky_coord.galactic.b.deg
            theta, phi = coordinate_util.radec2thetaphi(gal_lon, gal_lat)
            excess_b_v = hp.get_interp_val(
                self.extinction_map, theta=theta, phi=phi, nest=True
            )

        else:
            excess_b_v = np.zeros_like(x)

        return excess_b_v


def get_magnitude_calculator_direct(filter_names, par):
    """
    Interface to direct magnitude calculation
    """

    filter_names_full = [par.filters_full_names[f] for f in filter_names]
    # TODO: par should be the path to the filters file, either change it here or there
    filepath_sed_integ = os.path.join(par.maps_remote_dir, par.filters_file_name)
    filters = filters_util.load_filters(
        filepath_sed_integ, filter_names=filter_names_full, lam_scale=1e-4
    )

    filepath_sed_templates = os.path.join(par.maps_remote_dir, par.templates_file_name)
    # Load SED templates with following units:
    # Lambda: micrometer
    # SED: erg/s/m2/Å
    sed_templates = sed_templates_util.load_template_spectra(
        filepath_sed_templates, lam_scale=1e-4, amp_scale=1e4
    )

    from galsbi.ucat.magnitude_calculator import MagCalculatorDirect

    return UseShortFilterNames(
        MagCalculatorDirect(filters, sed_templates), par.filters_full_names
    )


def get_magnitude_calculator_table(filter_names, par):
    """
    Interface to magnitude calculation with pre-computed tables
    """

    filepath_sed_integ = os.path.join(
        par.maps_remote_dir, par.templates_int_tables_file_name
    )
    filter_full_names = [par.filters_full_names[f] for f in filter_names]

    from galsbi.ucat.magnitude_calculator import MagCalculatorTable

    return UseShortFilterNames(
        MagCalculatorTable(
            filter_full_names,
            filepath_sed_integ,
            copy_to_cwd=par.copy_template_int_tables_to_cwd,
        ),
        par.filters_full_names,
    )


MAGNITUDES_CALCULATOR = {
    "direct": get_magnitude_calculator_direct,
    "table": get_magnitude_calculator_table,
}


class Plugin(BasePlugin):
    """
    Generate a random catalog of galaxies with magnitudes in multiple bands.
    """

    def check_n_gal_prior(self, par):
        """
        Check if the number of galaxies is inside the prior range,
        even before rendering, to remove extreme values.
        """

        if hasattr(par, "galaxy_count_prior"):
            app_mag = self.ctx.galaxies.int_magnitude_dict[
                par.galaxy_count_prior["band"]
            ]
            n_gal_ = np.count_nonzero(app_mag < par.galaxy_count_prior["mag_max"])
            n_gal_ /= par.ngal_multiplier
            LOGGER.info(
                (
                    "Allowed number galaxies with int_mag<{} per tile [{},{}],"
                    " computed number: {}".format
                )(
                    par.galaxy_count_prior["mag_max"],
                    par.galaxy_count_prior["n_min"],
                    par.galaxy_count_prior["n_max"],
                    n_gal_,
                )
            )
            if (n_gal_ < par.galaxy_count_prior["n_min"]) or (
                n_gal_ > par.galaxy_count_prior["n_max"]
            ):
                raise galaxy_sampling_util.UCatNumGalError(
                    "too many or too few galaxies"
                )

    def check_max_mem_error(self, par):
        """
        Check if the catalog does not exceed allowed memory.
        Prevents job crashes on clusters.
        """

        mem_mb_current = utils.memory_usage_psutil()
        if mem_mb_current > par.max_memlimit_gal_catalog:
            raise galaxy_sampling_util.UCatNumGalError(
                "The sample_galaxies process is taking too much memory:"
                f" mem_mb_current={mem_mb_current},"
                f" max_mem_hard_limit={par.max_memlimit_gal_catalog}"
            )

    def __call__(self):
        par = self.ctx.parameters

        # Cosmology
        cosmo = PyCosmo.build()
        cosmo.set(h=par.h, omega_m=par.omega_m)

        if par.sampling_mode == "wcs":
            LOGGER.info("Sampling galaxies based on RA/DEC and pixel scale")
            # Healpix pixelization
            w = coordinate_util.wcs_from_parameters(par)
            self.ctx.pixels = coordinate_util.get_healpix_pixels(
                par.nside_sampling, w, par.size_x, par.size_y
            )
            if len(self.ctx.pixels) < 15:
                LOGGER.warning(
                    f"Only {len(self.ctx.pixels)} healpy pixels in the footprint,"
                    " consider increasing the nside_sampling"
                )
        elif par.sampling_mode == "healpix":
            LOGGER.info("Sampling galaxies based on healpix pixels")
            self.ctx.pixels = coordinate_util.get_healpix_pixels_from_map(par)
            w = None
        else:
            raise ValueError(
                f"Unknown sampling mode: {par.sampling_mode}, must be wcs or healpix"
            )
        self.ctx.pixarea = hp.nside2pixarea(par.nside_sampling, degrees=False)

        # Magnitude calculator
        all_filters = np.unique(par.filters + [par.lum_fct_filter_band])

        # backward compatibility - check if full filter names are set
        if not hasattr(par, "filters_full_names"):
            par.filters_full_names = filters_util.get_default_full_filter_names(
                all_filters
            )
            warnings.warn(
                "setting filters to default, this will cause problems if you work"
                " with filters from different cameras in the same band",
                stacklevel=1,
            )

        # get magnitude calculators (reload cache to avoid memory leaks and save memory)
        mag_calc = MAGNITUDES_CALCULATOR[par.magnitude_calculation](
            filter_names=all_filters, par=par
        )
        n_templates = mag_calc.n_templates
        # Cut in z - M - plane & boundaries
        z_m_intp = galaxy_sampling_util.intp_z_m_cut(cosmo, mag_calc, par)

        # Initialize galaxy catalog
        self.ctx.galaxies = galaxy_sampling_util.Catalog()
        self.ctx.galaxies.columns = [
            "id",
            "z",
            "template_coeffs",
            "template_coeffs_abs",
            "abs_mag_lumfun",
            "galaxy_type",
            "excess_b_v",
        ]

        # Columns modified inside loop
        loop_cols = [
            "z",
            "template_coeffs",
            "template_coeffs_abs",
            "abs_mag_lumfun",
            "galaxy_type",
            "excess_b_v",
        ]
        if w is not None:
            loop_cols += ["x", "y"]
            self.ctx.galaxies.columns += ["x", "y"]
        else:
            loop_cols += ["ra", "dec"]
            self.ctx.galaxies.columns += ["ra", "dec"]
        for c in loop_cols:
            setattr(self.ctx.galaxies, c, [])

        # set up luminosity functions
        lum_funcs = initialize_luminosity_functions(
            par, cosmo=cosmo, pixarea=self.ctx.pixarea, z_m_intp=z_m_intp
        )

        # Extinction
        extinction_eval = ExtinctionMapEvaluator(par)

        # Helper function to compute templates, extinction
        for g in par.galaxy_types:
            n_gal_type = 0
            n_gal_type_max = getattr(par, f"n_gal_max_{g}")
            max_reached = False

            for i in LOGGER.progressbar(
                range(len(self.ctx.pixels)),
                desc=f"getting {g:<4s} galaxies for healpix pixels",
                at_level="debug",
            ):
                # Sample absolute mag vs redshift from luminosity function
                abs_mag, z = lum_funcs[g].sample_z_mabs_and_apply_cut(
                    seed_ngal=par.seed
                    + self.ctx.pixels[i]
                    + par.gal_num_seed_offset
                    + SEED_OFFSET_LUMFUN * i,
                    seed_lumfun=par.seed
                    + self.ctx.pixels[i]
                    + par.gal_lum_fct_seed_offset
                    + SEED_OFFSET_LUMFUN * i,
                    n_gal_max=n_gal_type_max,
                )

                # Positions
                np.random.seed(par.seed + self.ctx.pixels[i] + par.gal_dist_seed_offset)

                # x and y for wcs, ra and dec for healpix model
                x, y = sample_position_uniform(
                    len(z), w, self.ctx.pixels[i], par.nside_sampling
                )

                # Make the catalog precision already here to avoid inconsistencies in
                # the selection
                x = x.astype(par.catalog_precision)
                y = y.astype(par.catalog_precision)

                (
                    template_coeffs,
                    template_coeffs_abs,
                    excess_b_v,
                    app_mag_ref,
                ) = compute_templates_extinction_appmag_for_galaxies(
                    galaxy_type=g,
                    par=par,
                    n_templates=n_templates,
                    cosmo=cosmo,
                    w=w,
                    redshifts=z,
                    absmags=abs_mag,
                    x_pixel=x,
                    y_pixel=y,
                    mag_calc=mag_calc,
                    extinction_eval=extinction_eval,
                )

                # Reject galaxies outside set magnitude range
                select_mag_range = (app_mag_ref >= par.gals_mag_min) & (
                    app_mag_ref <= par.gals_mag_max
                )
                if w is not None:
                    select_pos_range = in_pos(x, y, par)
                else:
                    select_pos_range = np.ones_like(x, dtype=bool)
                select = select_mag_range & select_pos_range
                n_gal = np.count_nonzero(select)
                n_gal_type += n_gal

                # store
                if w is not None:
                    self.ctx.galaxies.x.append(x[select].astype(par.catalog_precision))
                    self.ctx.galaxies.y.append(y[select].astype(par.catalog_precision))
                else:
                    self.ctx.galaxies.ra.append(x[select].astype(par.catalog_precision))
                    self.ctx.galaxies.dec.append(
                        y[select].astype(par.catalog_precision)
                    )
                self.ctx.galaxies.z.append(z[select].astype(par.catalog_precision))
                self.ctx.galaxies.template_coeffs.append(
                    template_coeffs[select].astype(par.catalog_precision)
                )
                self.ctx.galaxies.template_coeffs_abs.append(
                    template_coeffs_abs[select].astype(par.catalog_precision)
                )
                self.ctx.galaxies.abs_mag_lumfun.append(
                    abs_mag[select].astype(par.catalog_precision)
                )
                self.ctx.galaxies.galaxy_type.append(
                    np.ones(n_gal, dtype=np.ushort) * lum_funcs[g].galaxy_type
                )
                self.ctx.galaxies.excess_b_v.append(
                    excess_b_v[select].astype(par.catalog_precision)
                )

                # see if number of galaxies is OK
                if n_gal_type > n_gal_type_max * par.ngal_multiplier:
                    max_reached = True
                    if par.raise_max_num_gal_error:
                        raise galaxy_sampling_util.UCatNumGalError(
                            "exceeded number of"
                            f" {g} galaxies {n_gal_type}>{n_gal_type_max}"
                        )
                    else:
                        break

            LOGGER.info(
                f"lumfun={g} n_gals={n_gal_type} maximum number of galaxies"
                f" reached={max_reached} ({n_gal_type_max})"
            )

        # check memory footprint
        self.check_max_mem_error(par)

        # Concatenate columns
        for c in loop_cols:
            setattr(self.ctx.galaxies, c, np.concatenate(getattr(self.ctx.galaxies, c)))

        # Calculate requested intrinsic apparent and absolute magnitudes
        self.ctx.galaxies.int_magnitude_dict = mag_calc(
            redshifts=self.ctx.galaxies.z,
            excess_b_v=self.ctx.galaxies.excess_b_v,
            coeffs=self.ctx.galaxies.template_coeffs,
            filter_names=par.filters,
        )

        self.ctx.galaxies.abs_magnitude_dict = mag_calc(
            redshifts=np.zeros_like(self.ctx.galaxies.z),
            excess_b_v=np.zeros_like(self.ctx.galaxies.excess_b_v),
            coeffs=self.ctx.galaxies.template_coeffs_abs,
            filter_names=par.filters,
        )

        # Raise error is the number of galaxies per tile is too high or too low
        self.check_n_gal_prior(par)

        # Set apparent (lensed) magnitudes, for now equal to intrinsic apparent
        # magnitudes
        self.ctx.galaxies.magnitude_dict = dict()
        for band, mag in self.ctx.galaxies.int_magnitude_dict.items():
            self.ctx.galaxies.magnitude_dict[band] = mag.copy()

        # Number of galaxies and id
        self.ctx.numgalaxies = self.ctx.galaxies.z.size
        self.ctx.galaxies.id = np.arange(self.ctx.numgalaxies)

        # Backward compatibility
        self.ctx.galaxies.blue_red = np.ones(len(self.ctx.galaxies.z), dtype=np.ushort)
        self.ctx.galaxies.blue_red[
            self.ctx.galaxies.galaxy_type == lum_funcs["blue"].galaxy_type
        ] = 1
        self.ctx.galaxies.blue_red[
            self.ctx.galaxies.galaxy_type == lum_funcs["red"].galaxy_type
        ] = 0

        LOGGER.info(
            f"galaxy counts n_total={self.ctx.numgalaxies}"
            f" mem_mb_current={utils.memory_usage_psutil():5.1f}"
        )

        if par.save_SEDs:
            # Store SEDs in the catalog
            restframe_wavelength, seds = get_seds(par, self.ctx.galaxies)
            self.ctx.restframe_wavelength_for_SED = restframe_wavelength
            self.ctx.galaxies.sed = seds
        try:
            del mag_calc.func.templates_int_table_dict
            del mag_calc.func.z_grid
            del mag_calc.func.excess_b_v_grid
            del mag_calc.func
        except Exception:
            pass
        # profile.print_stats(output_unit=1)

    def __str__(self):
        return "sample gal photo"


def compute_templates_extinction_appmag_for_galaxies(
    galaxy_type,
    par,
    n_templates,
    cosmo,
    w,
    redshifts,
    absmags,
    x_pixel,
    y_pixel,
    mag_calc,
    extinction_eval,
):
    template_coeffs_abs = sample_template_coeff_lumfuncs(
        par=par, redshift_z={galaxy_type: redshifts}, n_templates=n_templates
    )[galaxy_type]

    # Calculate absolute magnitudes according to coefficients and adjust
    # coefficients according to drawn magnitudes
    mag_z0 = mag_calc(
        redshifts=np.zeros_like(redshifts),
        excess_b_v=np.zeros_like(redshifts),
        coeffs=template_coeffs_abs,
        filter_names=[par.lum_fct_filter_band],
    )

    template_coeffs_abs *= np.expand_dims(
        10 ** (0.4 * (mag_z0[par.lum_fct_filter_band] - absmags)), -1
    )

    # Transform to apparent coefficients
    lum_dist = galaxy_sampling_util.apply_pycosmo_distfun(
        cosmo.background.dist_lum_a, redshifts
    )
    template_coeffs = template_coeffs_abs * np.expand_dims(
        (10e-6 / lum_dist) ** 2 / (1 + redshifts), -1
    )
    excess_b_v = extinction_eval(w, x_pixel, y_pixel)
    # TODO: fix this in the already in the creation that excess_b_v is always
    # array, even when n_gal=1
    if len(redshifts) == 1:
        excess_b_v = np.array([excess_b_v])

    # Calculate apparent reference band magnitude
    app_mag_ref = mag_calc(
        redshifts=redshifts,
        excess_b_v=excess_b_v,
        coeffs=template_coeffs,
        filter_names=[par.reference_band],
    )[par.reference_band]

    return template_coeffs, template_coeffs_abs, excess_b_v, app_mag_ref


def in_pos(x, y, par):
    return (x > 0) & (x < par.size_x) & (y > 0) & (y < par.size_y)


def get_seds(par, galaxies):
    """
    Get SEDs for galaxies in the catalog
    """

    direct_mag_calc = get_magnitude_calculator_direct(filter_names=par.filters, par=par)
    n_obj = galaxies.z.size
    seds = []
    for i in LOGGER.progressbar(
        range(n_obj),
        desc="getting SEDs",
        at_level="debug",
    ):
        lam_obs_in_mu_m = direct_mag_calc.sed_templates["lam"] * (
            1 + galaxies.z[i]
        )  # in micrometer
        spec = spectrum_util.construct_reddened_spectrum(
            lam_obs=lam_obs_in_mu_m,
            templates_amp=direct_mag_calc.sed_templates["amp"],
            coeff=galaxies.template_coeffs[i],
            excess_b_v=galaxies.excess_b_v[i],
            extinction_spline=direct_mag_calc.extinction_spline,
        ).flatten()  # in erg/s/m2/Å
        # save in angstrom and erg/s/cm2/Å
        seds.append(spec / 1e4)
    seds = np.vstack(seds)
    return direct_mag_calc.sed_templates["lam"] * 1e4, seds
