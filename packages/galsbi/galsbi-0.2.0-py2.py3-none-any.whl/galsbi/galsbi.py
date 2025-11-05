# Copyright (C) 2024 ETH Zurich
# Institute for Particle Physics and Astrophysics
# Author: Silvan Fischbacher
# created: Thu Aug 08 2024

import contextlib
import importlib

import h5py
import numpy as np
from astropy.io import fits
from astropy.table import Table
from cosmic_toolbox import arraytools as at
from cosmic_toolbox import logger
from ufig import run_util

from . import citations, load

LOGGER = logger.get_logger(__name__)


class GalSBI:
    """
    This class is the main interface to the model. It provides methods to generate
    mock galaxy catalogs and to cite the model.
    """

    def __init__(self, name, verbosity="info"):
        """
        :param name: name of the model to use
        :param verbosity: verbosity level of the logger, either "debug", "info",
                         "warning", "error" or "critical"
        """
        self.name = name
        self.mode = None
        self.filters = None
        self.verbosity = verbosity

    def generate_catalog(
        self,
        mode="intrinsic",
        config_file=None,
        model_index=0,
        file_name="GalSBI_sim",
        verbosity=None,
        **kwargs,
    ):
        """
        Generates a mock galaxy catalog using the model and configuration specified. The
        parameter model_index is used to select a specific set of model parameters from
        the ABC posterior. If a list of model parameters is provided, catalogs are
        generated for each set of parameters. The saved catalogs and images are named
        according to the file_name and model_index.

        Names of the files
        ------------------
        - Intrinsic ucat galaxy catalog: f"{file_name}_{index}_{band}_ucat.gal.cat"
        - Intrinsic ucat star catalog: f"{file_name}_{index}_{band}_ucat.star.cat"
        - Output catalog: f"{file_name}_{index}_{band}_se.cat"
        - Output image: f"{file_name}_{index}_{band}_image.fits"
        - Segmentation map: f"{file_name}_{index}_{band}_se_seg.h5"
        - Background map: f"{file_name}_{index}_{band}_se_bkg.h5"
        - SED catalog: f"{file_name}_{index}_sed.cat"

        :param mode: mode to use for generating the catalog, either "intrinsic", "emu",
                    "image", "image+SE", "config_file"
        :param config_file: dictionary or path to a configuration file to use for
               generating the catalog (only used if mode="config_file")
        :param model_index: index of the model parameters to use for generating the
               catalog
        :param file_name: filename of the catalog and images to generate
        :param verbosity: verbosity level of the logger, either "debug", "info",
                         "warning", "error" or "critical"
        :param kwargs: additional keyword arguments to pass to the workflow (overwrites
                       the values from the model parameters and config file)
        """
        if verbosity is not None:
            self.verbosity = verbosity
        logger.set_all_loggers_level(self.verbosity)
        self.mode = mode
        model_parameters = load.load_abc_posterior(self.name)
        config = load.load_config(self.name, mode, config_file)

        if isinstance(model_index, int):
            model_index = [model_index]
        for index in model_index:
            LOGGER.info(
                "Generating catalog for model"
                f" {self.name} and mode {mode} with index {index}"
            )
            kwargs["galaxy_catalog_name_format"] = (
                f"{file_name}_{index}_{{}}{{}}_ucat.gal.cat"
            )
            kwargs["star_catalog_name_format"] = (
                f"{file_name}_{index}_{{}}{{}}_ucat.star.cat"
            )
            kwargs["sextractor_forced_photo_catalog_name_format"] = (
                f"{file_name}_{index}_{{}}{{}}_se.cat"
            )
            kwargs["galaxy_sed_catalog_name"] = f"{file_name}_{index}_sed.cat"
            kwargs["image_name_format"] = f"{file_name}_{index}_{{}}{{}}_image.fits"
            kwargs["tile_name"] = ""
            self.file_name = file_name
            self.catalog_name = file_name  # for backward compatibility
            self._run(config, model_parameters[index], **kwargs)

    __call__ = generate_catalog

    def _run(self, config, model_parameters, **kwargs):
        """
        Runs the workflow with the given configuration and model parameters

        :param config: configuration to use for generating the catalog
        :param model_parameters: model parameters to use for generating the catalog
        :param kwargs: additional keyword arguments to pass to the workflow (overwrites
                       the values from the model parameters and config file)
        """
        kargs = {}
        for col in model_parameters.dtype.names:
            kargs[col] = model_parameters[col]
            if ("moffat_beta1" in model_parameters.dtype.names) and (
                "moffat_beta2" in model_parameters.dtype.names
            ):
                kargs["psf_beta"] = [
                    model_parameters["moffat_beta1"][0],
                    model_parameters["moffat_beta2"][0],
                ]
        kargs.update(kwargs)
        if "filters" in kargs:
            self.filters = kargs["filters"]
        else:
            config_module = importlib.import_module(config)
            self.filters = config_module.filters

        self.ctx = run_util.run_ufig_from_config(config, **kargs)

    def cite(self):
        """
        Prints all the papers that should be cited when using the configuration
        specified
        """
        print("\033[1mPlease cite the following papers\033[0m")
        print("=================================")
        print("\033[1mFor using the GalSBI model:\033[0m")
        citations.cite_galsbi_release()
        print("\033[1mFor using the galsbi python package:\033[0m")
        citations.cite_code_release(self.mode)
        print("")

        print(
            "\033[1mFor the galaxy population model and redshift distribution:\033[0m"
        )
        citations.cite_abc_posterior(self.name)
        print("")
        print("Example:")
        print("--------")
        print(
            "We use the GalSBI framework (PAPERS GalSBI release) to generate mock"
            " galaxy catalogs. The galaxy population model corresponds to the"
            " posterior from (PAPER model). (...) "
            "Acknowledgements: We acknowledge the use of the following software:"
            "(numpy), (scipy), (PAPERS code release), (...)"
        )

    def load_catalogs(self, output_format="rec", model_index=0, combine=False):
        """
        Loads the catalogs generated by the model.

        :param output_format: format of the output, either "rec", "df" or "fits"
        :param model_index: index of the model parameters to use for loading the
                            catalogs
        :param combine: if True, combines the catalogs from all bands into a single
                        catalog
        :return: catalogs in the specified format
        """
        if self.filters is None:
            raise RuntimeError("please generate catalogs first")

        if output_format == "rec":
            convert = lambda x: x  # noqa: E731
        elif output_format == "df":
            convert = at.rec2pd
        elif output_format == "fits":
            convert = Table
        else:
            raise ValueError(f"Unknown output format {output_format}")

        output = {}
        for band in self.filters:
            catalog_name = f"{self.file_name}_{model_index}_{band}_ucat.gal.cat"
            with contextlib.suppress(FileNotFoundError):
                output[f"ucat galaxies {band}"] = at.load_hdf(catalog_name)
            catalog_name = f"{self.file_name}_{model_index}_{band}_ucat.star.cat"
            with contextlib.suppress(FileNotFoundError):
                output[f"ucat stars {band}"] = at.load_hdf(catalog_name)
            catalog_name = f"{self.file_name}_{model_index}_{band}_se.cat"
            with contextlib.suppress(FileNotFoundError):
                output[f"sextractor {band}"] = at.load_hdf(catalog_name)
        with contextlib.suppress(FileNotFoundError):
            sed_catalog_name = f"{self.file_name}_{model_index}_sed.cat"
            with h5py.File(sed_catalog_name, "r") as fh5:
                output["sed"] = fh5["data"][:]
                output["restframe_wavelength_in_A"] = fh5["restframe_wavelength_in_A"][
                    :
                ]

        if len(output) == 0:
            LOGGER.warning(
                "No catalogs found. Did you already generate catalogs? Does the "
                "model_index match the one used for generating the catalogs?"
            )
        if not combine:
            catalogs = {
                key: convert(value) if key != "restframe_wavelength_in_A" else value
                for key, value in output.items()
            }
            return catalogs

        combined_catalogs = self._build_combined_catalogs(output)
        return {
            key: value if key == "restframe_wavelength_in_A" else convert(value)
            for key, value in combined_catalogs.items()
        }

    def load_images(self, model_index=0):
        """
        Loads the images generated by the model. This include the actual image,
        the segmentation map and the background map.

        :param model_index: index of the model parameters to use for loading the images
        :return: images as numpy arrays
        """
        output = {}
        for band in self.filters:
            image_name = f"{self.file_name}_{model_index}_{band}_image.fits"
            try:
                hdul = fits.open(image_name)
                image = hdul[0].data
                hdul.close()
                output[f"image {band}"] = image
            except FileNotFoundError:
                pass
            segmap_name = f"{self.file_name}_{model_index}_{band}_se_seg.h5"
            with contextlib.suppress(FileNotFoundError):
                output[f"segmentation {band}"] = at.load_hdf_cols(segmap_name)[
                    "SEGMENTATION"
                ]
            bkgmap_name = f"{self.file_name}_{model_index}_{band}_se_bkg.h5"
            with contextlib.suppress(FileNotFoundError):
                output[f"background {band}"] = at.load_hdf_cols(bkgmap_name)[
                    "BACKGROUND"
                ]
        return output

    def _build_combined_catalogs(self, catalogs):
        band_dep_params = ["int_mag", "mag", "abs_mag", "bkg_noise_amp"]
        combined_catalogs = {}
        filter = self.filters[0]

        if f"ucat galaxies {filter}" in catalogs:
            new_cat = {}
            for f in self.filters:
                cat = catalogs[f"ucat galaxies {f}"]
                for par in cat.dtype.names:
                    if par not in band_dep_params:
                        new_cat[par] = cat[par]
                    else:
                        new_cat[f"{par} {f}"] = cat[par]
            if "sed" in catalogs:
                sed_catalog = catalogs["sed"]
                new_cat["sed"] = sed_catalog["sed"]
            combined_catalogs["ucat galaxies"] = at.dict2rec(new_cat)

        if f"ucat stars {filter}" in catalogs:
            new_cat = {}
            for f in self.filters:
                cat = catalogs[f"ucat stars {f}"]
                for par in cat.dtype.names:
                    if par not in band_dep_params:
                        new_cat[par] = cat[par]
                    else:
                        new_cat[f"{par} {f}"] = cat[par]
            combined_catalogs["ucat stars"] = at.dict2rec(new_cat)

        if f"sextractor {filter}" in catalogs:
            band_ind_params = [
                "dec",
                "ra",
                "z",
                "e1",
                "e2",
                "r50",
                "r50_arcsec",
                "r50_phys",
                "sersic_n",
                "galaxy_type",
                "id",
                "x",
                "y",
                "star_gal",
            ]
            new_cat = {}
            for f in self.filters:
                cat = catalogs[f"sextractor {f}"]
                for par in cat.dtype.names:
                    if par in band_ind_params:
                        new_cat[par] = cat[par]
                    else:
                        new_cat[f"{par} {f}"] = cat[par]
            if "sed" in catalogs:
                sed_catalog = catalogs["sed"]
                ids = new_cat["id"]
                # Match SEDs to IDs and handle non-matched IDs
                matched_gals = new_cat["galaxy_type"] >= 0
                sed_data = np.full(
                    (len(ids), sed_catalog["sed"].shape[1]),
                    np.nan,
                    dtype=sed_catalog["sed"].dtype,
                )
                sed_data[matched_gals] = sed_catalog["sed"][ids[matched_gals]]

                new_cat["sed"] = sed_data
            combined_catalogs["sextractor"] = at.dict2rec(new_cat)
        if "restframe_wavelength_in_A" in catalogs:
            combined_catalogs["restframe_wavelength_in_A"] = catalogs[
                "restframe_wavelength_in_A"
            ]
        return combined_catalogs
