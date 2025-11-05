# Copyright (C) 2024 ETH Zurich
# Institute for Particle Physics and Astrophysics
# Author: Silvan Fischbacher
# created: Wed Aug 07 2024

from .models import ALL_MODELS, CITE_FISCHBACHER24, CITE_GALSBI, CITE_MOSER24, CITE_UFIG


def cite_abc_posterior(name):
    """
    Prints the citation for the model with the given name.

    :param name: model name for which to print the citation
    """
    if name == "Moser+24":
        bib_entry = CITE_MOSER24
    elif name == "Fischbacher+24":
        bib_entry = CITE_FISCHBACHER24
    else:
        raise ValueError(
            f"Model {name} not found, only the following"
            f" models are available: [{ALL_MODELS}]"
        )
    print("(PAPER model)")
    print(bib_entry)


def cite_galsbi_release():
    """
    Prints the citation for the galsbi release.
    """
    print("(PAPERS GalSBI release)")
    print(CITE_FISCHBACHER24)


def cite_code_release(mode):
    """
    Prints the citation for the code release.

    :param mode: mode of the model
    """
    print("(PAPERS code release)")
    print(CITE_GALSBI)
    if not (mode == "intrinsic" or mode == "emu"):
        if (mode == "config_file") or (mode is None):
            print("If you use ufig plugins in your configuration, please also cite:")
        print(CITE_UFIG)
