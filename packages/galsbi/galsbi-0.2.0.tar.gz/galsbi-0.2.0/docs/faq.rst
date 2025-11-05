===================================
FAQs
===================================

.. _faq:

Here are some frequently asked questions (FAQs) regarding the project. Click on the links below to jump to the corresponding answer.

.. contents:: Table of Contents
   :local:
   :depth: 1

.. _citation:

Which papers should I cite when using `galsbi`?
-----------------------------------------------

You can find out which papers to cite by using the following command in Python:

.. code-block:: python

    from galsbi import GalSBI
    model = GalSBI("model_name")
    model.cite()

This will print the bibtex entries of the papers that should be cited when using your
configuration.

.. _emu_version:

Can I use the emulator with any version of libraries (e.g. `tensorflow`, `jax`)?
------------------------------------------------------------------------------------------------------------

The emulators are trained with the following versions of the libraries:

- `tensorflow` / `keras` version 2.12
- `sklearn` version 1.5.2
- `jax` version 0.4.31
- `pzflow` version 3.1.3

We tested that the emulator is working correctly for the following versions of the libraries:

- `tensorflow` version 2.12 to 2.18
- `keras` version 2.12 to 3.5
- `sklearn` version 1.2 to 1.5
- `jax` version 0.4.6 to 0.4.35
- `pzflow` version 3.1.0 to 3.1.3

Newer versions or older versions of the libraries might work as well, but we cannot guarantee that.
Note that depending on your installed software, different emulators are loaded in the
default config.
If you adapt configs, make sure that you are using the correct emulator.
If you encounter any problems or you need a specific library version with which the emulator
is not working, please contact the developers.
Retraining the emulator with your library version is potentially possible if no other solution can be found.


.. _pycosmo-first-run:

I run the code for the first time and it is taking a long time and printing a lot of messages. Is this normal?
--------------------------------------------------------------------------------------------------------------

Yes, this is normal. The first time you run the code, it will compile the necessary C code
for PyCosmo and cache it. This process can take a few minutes, depending on your system.
After the first run, the code will run much faster.

.. _pycosmo-error:

I get an error when I run the code for the first time during the compilation of `PyCosmo`. What should I do?
------------------------------------------------------------------------------------------------------------

If you get an error when you run the code for the first time during the compilation of `PyCosmo`,
(e.g. `ModuleNotFoundError: No module named '_wrapper_1db8b055_fc3ec'`), something went
wrong during the compilation of the code. This can normally be resolved by deleting the
cache and recompiling the code. To do this, run the following commands on Linux:

.. code-block:: bash

    cd ~/_cache
    rm -rf PyCosmo
    rm -rf gsl
    rm -rf libf2c
    rm -rf sympy2c

On macOS, run:

.. code-block:: bash

    cd ~/Library/Cache
    rm -rf PyCosmo
    rm -rf gsl
    rm -rf libf2c
    rm -rf sympy2c

After deleting the cache, recompile the code by running the following python code:

.. code-block:: python

    import PyCosmo
    PyCosmo.build()

This should resolve the issue. If you still encounter problems, please contact the developers.
