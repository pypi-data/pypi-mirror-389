# Copyright (C) 2019 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created on Aug, 2021
author: Tomasz Kacprzak

Based on:

ucat/docs/jupyter_notebooks/tabulate_template_integrals.ipynb

"""

import argparse
import os

import h5py
import numpy as np
from cosmic_toolbox import file_utils, logger

from galsbi.ucat import filters_util, sed_templates_util

LOGGER = logger.get_logger(__file__)


def setup(args):
    description = "create filter file and template integrals"
    parser = argparse.ArgumentParser(description=description, add_help=True)
    parser.add_argument(
        "-v",
        "--verbosity",
        type=str,
        default="info",
        choices=("critical", "error", "warning", "info", "debug"),
        help="logging level",
    )
    parser.add_argument(
        "--dirpath_res",
        type=str,
        required=True,
        help="path to directory containing filter sets (maps remote dir)",
    )
    parser.add_argument(
        "--filename_sed_templates",
        type=str,
        required=True,
        help="file name of the template set",
    )
    parser.add_argument(
        "--test", action="store_true", help="test run on all filters with low res"
    )
    # This is just needed for the preprocess function and get_tasks
    parser.add_argument("--function", type=str, default="main", help="function to run")

    args = parser.parse_args(args)

    args.dirpath_res = file_utils.get_abs_path(args.dirpath_res)

    logger.set_all_loggers_level(args.verbosity)

    return args


def get_tasks(args):
    args = setup(args)

    if args.function == "preprocess":
        # indices are not used in preprocess
        return [0]

    filepath_collection = os.path.join(
        args.dirpath_res, get_filename_filters_collection()
    )
    filters = filters_util.load_filters(filepath_collection, lam_scale=1e-4)
    filter_names_all = list(filters.keys())
    filepath_sed_templates = os.path.join(args.dirpath_res, args.filename_sed_templates)
    sed_templates = sed_templates_util.load_template_spectra(
        filepath_sed_templates, lam_scale=1e-4, amp_scale=1e4
    )

    n_filters = len(filter_names_all)
    n_templates = sed_templates.n_templates
    return np.arange(n_filters * n_templates).tolist()


def resources(args):
    return dict(
        main_memory=1000,
        main_time=4,
        merge_memory=4000,
        merge_time=4,
    )


def main(indices, args):
    args = setup(args)

    # first create filters collection file
    filepath_collection = os.path.join(
        args.dirpath_res, get_filename_filters_collection()
    )
    filters = filters_util.load_filters(filepath_collection, lam_scale=1e-4)
    filter_names_all = list(filters.keys())

    # load templates
    filepath_sed_templates = os.path.join(args.dirpath_res, args.filename_sed_templates)
    sed_templates = sed_templates_util.load_template_spectra(
        filepath_sed_templates, lam_scale=1e-4, amp_scale=1e4
    )

    ids_temp_filt = [
        get_filter_and_templ_ids(
            i, n_filters=len(filter_names_all), n_templates=sed_templates.n_templates
        )
        for i in range(len(filter_names_all) * sed_templates.n_templates)
    ]
    for i, (id_filter, id_template) in enumerate(ids_temp_filt):
        LOGGER.debug(
            f"index={i} filter={filter_names_all[id_filter]} templ={id_template}"
        )

    # calculate all integrals
    for index in indices:
        id_filter, id_template = get_filter_and_templ_ids(
            index,
            n_filters=len(filter_names_all),
            n_templates=sed_templates.n_templates,
        )

        filter_name = filter_names_all[id_filter]
        LOGGER.info(
            f"running on index={index} filter={filter_name} templ={id_template}"
        )
        (
            sed_templates_integrals,
            excess_b_v_grid,
            z_grid,
        ) = sed_templates_util.get_template_integrals(
            sed_templates=sed_templates,
            filters=filters,
            filter_names=[filter_name],
            ids_templates=[id_template],
            test=args.test,
        )

        filepath_sed_integ = os.path.join(
            args.dirpath_res, get_filename_sed_templ_integ_index(args, index)
        )
        sed_templates_util.store_sed_integrals(
            filepath_sed_integ, sed_templates_integrals, excess_b_v_grid, z_grid
        )

    yield 0


def merge(indices, args):
    args = setup(args)

    # load filters
    filepath_collection = os.path.join(
        args.dirpath_res, get_filename_filters_collection()
    )
    filters = filters_util.load_filters(filepath_collection, lam_scale=1e-4)
    filter_names_all = list(filters.keys())

    # load templates
    filepath_sed_templates = os.path.join(args.dirpath_res, args.filename_sed_templates)
    sed_templates = sed_templates_util.load_template_spectra(
        filepath_sed_templates, lam_scale=1e-4, amp_scale=1e4
    )

    # write merged template integrals file
    filepath_out_merged = os.path.join(
        args.dirpath_res, get_filepath_sed_templ_integ_merged(args)
    )

    def merge_in(filepath_out_merged, val, key):
        with h5py.File(filepath_out_merged, "a") as f:
            if key in f:
                del f[key]
            f.create_dataset(name=key, data=val, compression="lzf", shuffle=True)

    for index in indices:
        get_filter_and_templ_ids(
            index,
            n_filters=len(filter_names_all),
            n_templates=sed_templates.n_templates,
        )

        filepath_sed_integ = os.path.join(
            args.dirpath_res, get_filename_sed_templ_integ_index(args, index)
        )
        if not os.path.isfile(filepath_sed_integ):
            LOGGER.error(f"file {filepath_sed_integ} not found")
        else:
            with h5py.File(filepath_sed_integ, "r") as f:
                filter_name = list(f["integrals"].keys())[0]
                merge_in(filepath_out_merged, val=np.array(f["E(B-V)"]), key="E(B-V)")
                merge_in(filepath_out_merged, val=np.array(f["z"]), key="z")
                for t in f[f"integrals/{filter_name}"]:
                    merge_in(
                        filepath_out_merged,
                        val=np.array(f[f"integrals/{filter_name}/{t}"]),
                        key=f"integrals/{filter_name}/{t}",
                    )
                    LOGGER.info(f"merged {filter_name} {t}")
    LOGGER.info(f"wrote {filepath_out_merged}")


def preprocess(indices, args):
    args = setup(args)

    # first create filters collection file
    filters_collect = filters_util.create_filter_collection(args.dirpath_res)
    filepath_collection = os.path.join(
        args.dirpath_res, get_filename_filters_collection()
    )
    filters_util.store_filter_collection(filepath_collection, filters_collect)


def get_filter_and_templ_ids(index, n_filters, n_templates):
    id_filter, id_template = np.unravel_index(index, shape=(n_filters, n_templates))
    return id_filter, id_template


def get_filename_sed_templ_integ_index(args, index):
    suffix = os.path.splitext(os.path.basename(args.filename_sed_templates))[0]
    filename_sed_integ = f"sed_integrals__{suffix}/index{index:03d}.h5"
    return filename_sed_integ


def get_filepath_sed_templ_integ_merged(args):
    suffix = os.path.splitext(os.path.basename(args.filename_sed_templates))[0]
    filename_sed_integ = f"sed_integrals__{suffix}.h5"
    return filename_sed_integ


def get_filename_filters_collection():
    return "filters_collection.h5"
