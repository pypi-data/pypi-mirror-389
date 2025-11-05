Emulate image simulation
============================

The intrinsic catalogs contain all galaxies up to a predefined cut in absolute magnitude.
Not all of these galaxies would actually be detected when building up a catalog from
actual astronomical images. The **detection probability** is to first
order a function of the apparent magnitude. However, there are further
effects such as **blending** or **background noise** that impact the
detection probability (especially at the faint edge). Furthermore, an
intrinsic size or magnitude will not be the size that is measured in
an actual astronomical image by a source extraction software such as
``SExtractor``. Both background noise or the point spread function
(**PSF**) have a strong impact on the measured parameters and introduce
a scatter.

Ideally, these effects are taken into account by performing image
simulations. But as shown in Fischbacher et al. (2024), it
is possible to emulate this effects accurately. We show below how to
generate a galaxy catalog with an emulator trained on HSC deep fields.
Note that the detection classifiers predicts if an object is detected as
a galaxy, most stars are therefore are rejected and only a few stars
contaminate the catalog (based on the accuracy of the star galaxy
separation method).

.. code:: python

    from galsbi import GalSBI
    from trianglechain import TriangleChain
    import matplotlib.pyplot as plt

    model = GalSBI("Fischbacher+24")
    model(mode="emulator")

    cats = model.load_catalogs()

    cat_ucat = cats["ucat galaxies i"]
    cat_sextractor = cats["sextractor i"]

    ranges = {
        "mag": [18, 28],
        "r50": [0, 10],
        "sersic_n": [0, 5],
        "z": [0, 6],
        "MAG_AUTO": [18, 28],
        "FLUX_RADIUS": [0, 10],
        "log10_snr": [0, 5],
    }
    tri = TriangleChain(ranges=ranges, params=list(ranges.keys()), fill=True, histograms_1D_density=False)
    tri.contour_cl(cat_ucat, label="intrinsic");
    tri.contour_cl(cat_sextractor, label="measured", show_legend=True);

.. image:: figures/output_26_2.png
