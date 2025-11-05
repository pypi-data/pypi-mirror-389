============
Installation
============

You can install galsbi using pip:

.. code-block:: bash

    pip install galsbi

Or with uv:

.. code-block:: bash

    uv pip install galsbi

To install the latest development version directly from the GitLab repository:

.. code-block:: bash

    # Using SSH (requires SSH key setup)
    pip install git+ssh://git@gitlab.com/cosmology-ethz/galsbi.git
    # Or using HTTPS
    pip install git+https://gitlab.com/cosmology-ethz/galsbi.git

Or with uv:

.. code-block:: bash

    # Using SSH (requires SSH key setup)
    uv pip install git+ssh://git@gitlab.com/cosmology-ethz/galsbi.git
    # Or using HTTPS
    uv pip install git+https://gitlab.com/cosmology-ethz/galsbi.git

If you want to install the development version and have the source code available for
modifications or contributions, clone the repository and install it in editable mode:

.. code-block:: bash

    # Using SSH (requires SSH key setup)
    git clone git@gitlab.com:cosmology-ethz/galsbi.git
    # Or using HTTPS
    git clone https://gitlab.com/cosmology-ethz/galsbi.git

    cd galsbi
    pip install -e .

Or with uv:

.. code-block:: bash

    # Using SSH (requires SSH key setup)
    git clone git@gitlab.com:cosmology-ethz/galsbi.git
    # Or using HTTPS
    git clone https://gitlab.com/cosmology-ethz/galsbi.git

    cd galsbi
    uv pip install -e .

After installation, some additional data files may be downloaded automatically the
first time you run galsbi. This is normal and will only occur once to cache the
necessary files locally. The first time you sample galaxies may also take longer due
to PyCosmo initialization. For more information,
see the `FAQ <https://cosmo-docs.phys.ethz.ch/galsbi/faq.html#i-get-an-error-when-i-run-the-code-for-the-first-time-during-the-compilation-of-pycosmo-what-should-i-do>`_
if you encounter any issues.
