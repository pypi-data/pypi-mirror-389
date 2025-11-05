Saving Galaxy Spectra
========================

By default, galaxy spectra are not saved in GalSBI, as doing so can be
storage-intensive. Moreover, in the standard photometry modes, spectra
are not explicitly computed. Instead, either pre-tabulated values are
used to derive magnitudes from template parameters (for the
phenomenological model), or magnitudes are estimated using the magnitude
emulator (in the SPS model).

However, it is possible to save the Spectral Energy Distribution (SED)
for each galaxy if needed. This tutorial demonstrates how to do so.

-----------------------
Phenomenological GalSBI
-----------------------

.. code:: python

    from galsbi import GalSBI
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    import matplotlib.colors as mcolors
    import numpy as np

The SED is saved over a rest-frame wavelength range defined by the
templates when the argument ``save_SEDs=True`` is either passed to the
function or specified in the configuration file.

.. code:: python

    healpix_map = np.zeros(12 * 1024**2)
    healpix_map[0] = 1

    model = GalSBI("Fischbacher+24")
    model(
        save_SEDs=True,
        healpix_map=healpix_map
    )


The SED is saved as an HDF5 file named
``{file_name}_{model_index}_sed.cat``. You can load it using the
standard built-in loading functions. Note that the redshift of the
galaxy is required to convert the SED from rest-frame to observed
wavelength.

If you’re not using the combined loading mode, the SED is stored under a
separate key in the returned dictionary. In combined mode, the SED is
directly attached to the main catalogs — both the ucat and the
SExtractor catalogs, if available.

.. code:: python

    cats = model.load_catalogs()
    wavelength = cats["restframe_wavelength_in_A"]
    sed_catalog = cats["sed"][1]

    lamb = wavelength * (1+sed_catalog["z"])
    sed = sed_catalog["sed"]

    # Alternatively with combined catalogs
    cats = model.load_catalogs(combine=True)
    wavelength = cats["restframe_wavelength_in_A"]
    total_catalog = cats["ucat galaxies"][1]

    lamb = wavelength * (1+total_catalog["z"])
    sed = total_catalog["sed"]

.. code:: python

    path = "../../resources/filters/"
    vista_bands = ["Y", "J", "H", "Ks"]
    vista_template = path + "filters_vista/Paranal_VISTA.{}_filter.dat"
    sdss_bands = ["u", "g", "r", "i", "z"]
    sdss_template = path + "filters_sdss/SLOAN_SDSS.{}.dat"

    # Combine all filters
    all_bands = sdss_bands + vista_bands
    n_filters = len(all_bands)

    # Generate evenly spaced rainbow colors
    cmap = cm.get_cmap('rainbow', n_filters)
    colors = [cmap(i) for i in range(n_filters)]
    band_colors = dict(zip(all_bands, colors))  # map band name to color

    # Start plotting
    plt.figure(figsize=(6, 3))

    # Plot SED
    max_sed = np.max(sed)
    plt.plot(lamb, sed, color="k", lw=0.5)

    # Plot SDSS filters
    for b in sdss_bands:
        lam, t = np.loadtxt(sdss_template.format(b)).T
        t /= (t.max()/max_sed)
        lambda_mean = np.trapz(lam * t, lam) / np.trapz(t, lam)
        color = band_colors[b]
        plt.fill_between(lam, t, color=color, alpha=0.2)
        plt.text(lambda_mean, 0.25*max_sed, b, color="gray", fontsize=10, ha='center', va='bottom')

    # Plot VISTA filters
    for b in vista_bands:
        lam, t = np.loadtxt(vista_template.format(b)).T
        t /= (t.max()/max_sed)
        lambda_mean = np.trapz(lam * t, lam) / np.trapz(t, lam)
        color = band_colors[b]
        plt.fill_between(lam, t, color=color, alpha=0.2)
        plt.text(np.mean(lam), 0.25*max_sed, b, color="gray", fontsize=10, ha='center', va='bottom')

    # Plot formatting
    plt.xlabel("Observed Wavelength (Å)")
    plt.ylabel("Flux Density (erg/s/cm²/Å)")
    plt.title("Spectral Energy Distribution (SED)")
    plt.ylim(bottom=0)
    plt.xlim(2000, 25000)

.. image:: figures/output_7_2.png
