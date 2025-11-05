# Copyright (C) 2024 ETH Zurich
# Institute for Particle Physics and Astrophysics
# Author: Silvan Fischbacher
# created: Tue Jul 30 2024


import os

from galsbi.ucat import filters_util


def test_filters_util():
    dirpath_res = os.path.join(os.path.dirname(__file__), "../../resources")
    filters = filters_util.create_filter_collection(dirpath_res)
    assert isinstance(filters, dict)
    filters_util.store_filter_collection("test_filters.h5", filters)
    os.remove("test_filters.h5")


def test_get_default_full_filter_names():
    assert filters_util.get_default_full_filter_names("g") == {"g": "g"}
