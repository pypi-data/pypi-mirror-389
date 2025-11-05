Run in parallel
===============

For larger survey areas, sampling galaxies in one call might become
infeasible due to the additional memory and time that is required.
However, the catalog generation can easily be split into smaller chunks
which reduces the memory consumption significantly. Below we show an
example where we split the mask into many submask that sample only one
healpix pixels each. Speeding up the catalog generation can be achieved
by parallelizing the last for-loop of this script, using
e.g. ``esub-epipe`` to submit each index as a separate job on a cluster
or classic parallelization tools such as Python’s ``multiprocessing``
module or ``concurrent.futures``.

.. code:: python

    def process_healpix_submask(submask, catalog_name):
        model = GalSBI("Fischbacher+24")
        model(healpix_map=submask, file_name=catalog_name)

    nside = 2048
    npix = hp.nside2npix(nside)

    mask = np.zeros(npix)

    # Define a circular patch around the point (theta, phi) = (45 degrees, 45 degrees)
    theta_center = np.radians(45.0)
    phi_center = np.radians(45.0)

    # Set a 0.5 degree radius
    radius = np.radians(0.5)

    # Find all pixel indices within this patch and set mask to 1
    vec_center = hp.ang2vec(theta_center, phi_center)
    patch_pixels = hp.query_disc(nside, vec_center, radius)
    mask[patch_pixels] = 1

    submasks = []
    catalog_names = []
    pixels_per_mask = 10
    n_pixels = len(patch_pixels)
    for i in range(n_pixels // pixels_per_mask + 1):
        submask = np.zeros(npix)
        pixels = patch_pixels[i*pixels_per_mask : (i+1)*pixels_per_mask]
        submask[pixels] = 1
        submasks.append(submask)
        catalog_names.append(f"catalogs_pixelbatch{i}")

    for i in range(len(submasks)):
        process_healpix_submask(submasks[i], catalog_name=catalog_names[i])

We show an example script that generates the catalogs in parallel for the first
healpix pixels below. The script is split into two functions:
``main`` and ``merge``. The ``main`` function is responsible for the main
simulations, which are performed on separate cores. The ``merge`` function can be used
to merge the catalogs into one if necessary.

.. code-block:: python
    :caption: run.py

    # Copyright (C) 2024 ETH Zurich
    # Institute for Particle Physics and Astrophysics
    # Author: Silvan Fischbacher


    import argparse
    import os

    import healpy as hp
    import numpy as np
    from cosmic_toolbox import file_utils
    from cosmic_toolbox.logger import get_logger, set_all_loggers_level
    from galsbi import GalSBI

    LOGGER = get_logger(__file__)


    def setup(args):

        description = "Cool project"
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
            "--output_directory",
            type=str,
            required=True,
            help="Where to write output files to",
        )
        parser.add_argument(
            "--n_healpix_pixels_per_index",
            type=int,
            default=10,
            help="Number of healpix pixels to process per index",
        )
        parser.add_argument("--nside", type=int, default=64, help="Healpix nside")
        args = parser.parse_args(args)

        # set logging level
        set_all_loggers_level(args.verbosity)

        # get absolute paths
        args.output_directory = file_utils.get_abs_path(args.output_directory)

        # make directories
        file_utils.robust_makedirs(args.output_directory)

        return args


    def resources(args):
        # adapt the resources to your needs
        return dict(
            main_memory=10000,
            main_time_per_index=4,
            main_scratch=25000,
            merge_memory=10000,
            merge_time=4,
            merge_scratch=25000,
            merge_n_cores=1,
        )


    def process_healpix_submask(submask, catalog_name):
        model = GalSBI("Moser+24")
        model(healpix_map=submask, file_name=catalog_name)


    def main(indices, args):
        args = setup(args)
        npix = hp.nside2npix(args.nside)

        # each index is a separate job
        for index in indices:
            submask = np.zeros(npix)
            first = index * args.n_healpix_pixels_per_index
            last = (index + 1) * args.n_healpix_pixels_per_index
            submask[first:last] = 1

            catalog_name = os.path.join(args.output_directory, f"cat_pixelbatch{index}")
            process_healpix_submask(submask, catalog_name=catalog_name)
            yield index


    def merge(indices, args):
        args = setup(args)

        for index in indices:
            # TODO: potentially load the catalogs and merge into one
            pass

This script can be submitted to a slurm batch system using the following
command:

.. code:: bash

    esub run.py --n_healpix_pixels_per_index=10 --output_directory=/path/to/output --nside=64 --tasks='0>5' --n_jobs=5 --mode=jobarray --function=all --system=slurm

For more information on how to use ``esub`` please refer to the
`esub documentation <https://cosmo-docs.phys.ethz.ch/esub-epipe/>`_.
