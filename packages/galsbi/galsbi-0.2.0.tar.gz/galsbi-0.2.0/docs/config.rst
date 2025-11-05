Customize configuration
=======================

``galsbi`` is highly customizable. An overview of parameters that can be
passed to ``ucat`` or ``ufig`` can be found in the corresponding common
files. Each of these parameters can either be passed as an argument to
the call of the model or a completely new config file can be passed. We
advice to use the existing config files of the corresponding galaxy
population models as a template. In this config files it is clearly
stated which parameters should not be changed when using this galaxy
population model (e.g. the parametrization of the luminosity function
because this changes the meaning of the parameters of the galaxy
population model).

The config file can be passed as a path or a module. Below we show an
example where we load the basic intrinsic config file using both
versions.

.. code:: python

    import galsbi
    import os


    path2config = os.path.join(galsbi.__path__[0], "configs/config_Fischbacher+24_intrinsic.py")
    model = GalSBI("Fischbacher+24")
    model(mode="config_file", config_file=path2config)

    config_module = "galsbi.configs.config_Fischbacher+24_intrinsic"
    model = GalSBI("Fischbacher+24")
    model(mode="config_file", config_file=config_module)
