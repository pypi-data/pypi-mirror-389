=================
Filters in GalSBI
=================

Computing an apparent magnitude in a specific filter band in ``galsbi`` can be done in two ways.
If you define ``magnitude_calculation="direct"`` in the configuration file, the apparent
magnitude is calculated on the fly. For this you need to provide the template files
and the filter file. The config file could contain the following lines:

.. code-block:: python

    import os
    from cosmo_torrent import data_path

    magnitude_calculation = "table"
    filters_file_name = os.path.join(data_path("all_filters_v2"), "filters_collection.h5")
    templates_file_name = os.path.join(
        data_path("template_BlantonRoweis07"), "template_spectra_BlantonRoweis07.h5"
    )

If you define ``magnitude_calculation="table"``, the apparent magnitude is calculated
using the precomputed tables. The config file could contain the following lines:

.. code-block:: python

    import os
    from cosmo_torrent import data_path

    magnitude_calculation = "table"
    templates_int_tables_file_name = os.path.join(
        data_path("all_filters_v2"), "sed_integrals__template_spectra_BlantonRoweis07.h5"
    )

These files contain all the necessary information needed for the supported filters.
Currently, ``galsbi`` supports the following filters:

- DECamNoAtm_g, DECamNoAtm_r, DECamNoAtm_i, DECamNoAtm_z, DECamNoAtm_Y
- DECam_u, DECam_g, DECam_r, DECam_i, DECam_z, DECam_Y
- GALEX_FUV, GALEX_NUV
- GenericBessel_U, GenericBessel_B, GenericBessel_V, GenericBessel_R, GenericBessel_I, GenericBessel_J, GenericBessel_K, GenericBessel_L, GenericBessel_M
- GenericJohnson_U, GenericJohnson_B, GenericJohnson_V, GenericJohnson_R, GenericJohnson_I, GenericJohnson_J, GenericJohnson_M
- HyperSuprimeCam_g, HyperSuprimeCam_r, HyperSuprimeCam_r2, HyperSuprimeCam_i, HyperSuprimeCam_i2, HyperSuprimeCam_z, HyperSuprimeCam_y
- MegaPrime_u
- SuprimeCam_B, SuprimeCam_V, SuprimeCam_r, SuprimeCam_ip, SuprimeCam_zp, SuprimeCam_zpp, SuprimeCam_IA484, SuprimeCam_IA527, SuprimeCam_IA624, SuprimeCam_IA679, SuprimeCam_IA738, SuprimeCam_IA767, SuprimeCam_IB427, SuprimeCam_IB464, SuprimeCam_IB505, SuprimeCam_IB574, SuprimeCam_IB709, SuprimeCam_IB827, SuprimeCam_NB711, SuprimeCam_NB816
- SDSS_u, SDSS_g, SDSS_r, SDDS_i, SDSS_z
- Vircam_Y, Vircam_J, Vircam_H, Vircam_Ks
- VISTA_Z, VISTA_Y, VISTA_J, VISTA_H, VISTA_Ks
- VISTA_NoAtmZ, VISTA_NoAtmY, VISTA_NoAtmJ, VISTA_NoAtmH, VISTA_NoAtmKs
- irac_ch1, irac_ch2, irac_ch3, irac_ch4
- mips_24
- wircam_H, wircam_Ks

Some of them are shown in the following figure:

.. image:: notebooks/filters.svg

The raw filter files are stored at ``resources/filters`` in the ``galsbi`` package.
Using a specific filter is as simple as defining the filter name in the configuration file.
For example, if you want to use the DECam filters, you can define the following lines in the config file:

.. code-block:: python

    filters = ["u", "g", "r", "i", "z", "Y"]
    filters_full_names = {
        "u": "DECam_u",
        "g": "DECam_g",
        "r": "DECam_r",
        "i": "DECam_i",
        "z": "DECam_z",
        "Y": "DECam_Y",
    }

Adding a new filter
===================

To add a new filter or to create a new filter file (e.g. with less filters to have a smaller file),
you can use the ``run_template_filter_integrals`` app. This app was also used to create the
``sed_integrals__template_spectra_BlantonRoweis07.h5`` and ``filters_collection.h5`` files.
We assume in the following that you have cloned the ``galsbi`` repository, installed the package
from the source, and are in the ``galsbi`` root directory.
You have to follow these steps:

1. Save the raw filter files in a folder, e.g. ``new_resources/filters``, and the template file
   at ``new_resources/template/template_spectra_BlantonRoweis07.h5``. You can use any templates
   but we recommend to use the Blanton & Roweis 2007 templates since the ``galsbi`` package
   was tested with these templates. Otherwise, the template coefficients would have to be
   constrained independently.
2. Edit the filter interface in ``galsbi/src/galsbi/ucat/filters_utils.py``. If you add a
   new filter, make an additional nested function in ``create_filter_collection`` following
   the same structure as the other filters. If you want to create a new filter file,
   you will have to remove the code that processes the filters that are not in the new filter file.
   Add the new filter to the ``filter_collect`` dictionary with the following convention:
   ``filters_collect["InstrumentName_band"] = dict(amp=amplitude, lam=lambda)``.
3. Run the app with the following command:

   .. code-block:: bash

       esub src/galsbi/ucat/apps/run_template_filter_integrals.py --dirpath_res=new_resources/ --filename_sed_templates=template/template_spectra_BlantonRoweis07.h5 --function=preprocess --mode=run

   This will create the new ``filters_collection.h5`` files. If you want to use the direct
   calculation, you can stop here. If you want to use the table calculation, you have to
   continue with the next steps.
4. Run the app with the following command:

    .. code-block:: bash

        esub src/galsbi/ucat/apps/run_template_filter_integrals.py --dirpath_res=new_resources/ --filename_sed_templates=template/template_spectra_BlantonRoweis07.h5 --function=all --mode=jobarray --system=slurm

   This will submit jobs for each filter and each template on a slurm cluster. If your
   cluster uses IBM's LSF, you can remove the ``--system=slurm`` option. If you don't want
   to use a cluster, you can change the ``--mode`` option to ``run``. Then, the jobs will be
   run sequentially.
   This will create the new ``sed_integrals__template_spectra_BlantonRoweis07.h5`` files.
5. You can now use the new files in the configuration file. You have to define the new
   filter in the config file together with the updated paths to the new files.

   .. code-block:: python

        filter_file_name = "new_resources/filters/filters_collection.h5"
        templates_file_name = "new_resources/template/template_spectra_BlantonRoweis07.h5"
        templates_int_tables_file_name = "new_resources/sed_integrals__template_spectra_BlantonRoweis07.h5"
        filters = ["g", "r", "i", "z", "y"]
        filters_full_names = {
            "g": "NewFilter_g",
            "r": "NewFilter_r",
            "i": "NewFilter_i",
            "z": "NewFilter_z",
            "y": "NewFilter_y",
        }

6. If you add a new filter, consider to submit a merge request to the ``galsbi`` repository
   such that the new filter can be used by other users as well.
