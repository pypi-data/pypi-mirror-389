Getting Started
===============

Generating a galaxy catalog with intrinsic properties can be done with just a few lines of code.
Initialize the GalSBI class with the desired model and call it.
If you run a model for the first time, it might take a bit longer since some files have to be loaded to cache.
A default configuration will be used to generate an intrinsic catalog.
It can be loaded directly and plotted.
By default, the catalog will be saved in the current directory.

.. code:: python

    from galsbi import GalSBI
    from trianglechain import TriangleChain
    import matplotlib.pyplot as plt

    model = GalSBI("Fischbacher+24")
    model()
    cats = model.load_catalogs()
    cat = cats["ucat galaxies i"]

    ranges = {
        "mag": [18, 27],
        "r50": [0, 4],
        "sersic_n": [0, 5],
        "z": [0, 6]
    }
    tri = TriangleChain(ranges=ranges, params=list(ranges.keys()), fill=True)
    tri.contour_cl(cat);


.. image:: figures/output_7_1.png

This is a simple example of how to generate a catalog from one sample of the posterior distribution.
To obtain catalogs from different posterior samples, one can change the ``model_index`` (which is by default 0).
The positions of the galaxies are by default in the first pixel of a healpix map with nside 64.
This can easily be changed by passing a boolean healpix mask to the GalSBI class.

.. code:: python

    import healpy as hp
    import numpy as np
    import matplotlib.pyplot as plt

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

    model = GalSBI("Fischbacher+24")
    model(healpix_map=mask, model_index=42)

The catalogs are saved as ``{file_name}_{model_index}_{band}_ucat.gal.cat`` and
``{file_name}_{model_index}_{band}_ucat.star.cat``.
To change the path where the catalogs are saved, pass a different ``file_name`` argument to the call.
The catalogs are saved as structured numpy arrays but they can be loaded as pandas dataframes (``output_format="df"``)
or fits tables (``output_format="fits"``). To obtain the catalog from the correct model index, pass the ``model_index`` argument.

.. code:: python

    cats_as_pd_df = model.load_catalogs(output_format="df", model_index=42)
    cats_as_fits = model.load_catalogs(output_format="fits", model_index=42)

By default, the catalogs are returned separately for each band.
To get a single catalog with all bands, pass ``combine=True``.

.. code:: python

    cats_combined = model.load_catalogs(combine=True, model_index=42)

Finally, to see which papers should be cited given the specific setup used, call the ``cite`` method.

.. code:: python

    model.cite()
