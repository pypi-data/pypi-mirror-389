# Copyright (C) 2024 ETH Zurich
# Institute for Particle Physics and Astrophysics
# Author: Silvan Fischbacher
# created: Wed Aug 07 2024


import os
import sys

from cosmic_toolbox import arraytools as at
from cosmo_torrent import data_path

from .models import ALL_MODELS


def load_abc_posterior(name):
    """
    Loads the ABC posterior for the given model.

    :param name: name of the model
    :return: ABC posterior as a structured numpy array
    """
    if name == "Moser+24":
        path = data_path("Moser+24_abc_posterior")
        path = os.path.join(path, "abc_posterior.h5")
    elif name == "Fischbacher+24":
        path = data_path("Fischbacher+24_abc_posterior")
        path = os.path.join(path, "abc_posterior.h5")
    else:
        raise ValueError(
            f"Model {name} not found, only the following"
            f" models are available: [{ALL_MODELS}]"
        )

    return at.load_hdf_cols(path)


def load_config(name, mode, config_file=None):
    """
    Loads the correct configuration for the given model and mode.
    If mode is "config_file", the configuration is loaded from the given file.
    Otherwise, the configuration is loaded based on the model name and mode.

    :param name: name of the model
    :param mode: mode for which to load the configuration (either "intrinsic", "emu",
                "image", "config_file")
    :param config_file: path to a configuration file to use
    :return: module name of the configuration to use
    """
    if mode == "config_file":
        return _check_custom_config_file(config_file)

    module_name = f"config_{name}_{mode}"
    return f"galsbi.configs.{module_name}"


def _check_custom_config_file(config_file):
    """
    Checks if the given configuration file is a path or a module name.
    If it is a path, the module name is generated based on the path.
    If it is a module name, the module name is returned.
    """
    if os.path.isfile(config_file):
        file_dir = os.path.abspath(os.path.dirname(config_file))
        sys.path.append(file_dir)
        module_name = os.path.splitext(os.path.basename(config_file))[0]
        return module_name
    return config_file
