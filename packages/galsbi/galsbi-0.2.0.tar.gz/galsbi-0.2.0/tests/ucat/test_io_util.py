"""
Created on Aug 2, 2018
author: Joerg Herbel
"""

import os
import random
import string
from unittest.mock import patch

import h5py
import numpy as np
import pytest
from darkskysync.DarkSkySync import DarkSkySync
from darkskysync.DataSourceFactory import DataSourceFactory
from pkg_resources import resource_filename
from ufig import io_util

from galsbi import ucat

# Get non-existing filename for remote test
FILENAME_TEST_REMOTE = random.choice(string.ascii_letters + string.digits)
while os.path.exists(
    os.path.join(resource_filename(ucat.__name__, ""), FILENAME_TEST_REMOTE)
):
    FILENAME_TEST_REMOTE += random.choice(string.ascii_letters + string.digits)


def test_get_abs_path_local():
    """
    Test galsbi.ucat.io_util.get_abs_path for local paths.
    """

    # Absolute file name input for existing file
    filename = os.path.abspath(__file__)
    abspath = os.path.abspath(filename)
    path = io_util.get_abs_path(abspath)
    assert path == abspath

    # Relative file name input for existing file
    path = io_util.get_abs_path(filename, root_path="tests/")
    assert path == abspath

    # Absolute file name input for non-existing file
    abspath = "/" + random.choice(string.ascii_letters + string.digits)
    while os.path.exists(abspath):
        abspath += random.choice(string.ascii_letters + string.digits)

    with pytest.raises(OSError):
        io_util.get_abs_path(abspath)


@patch.object(DataSourceFactory, "fromConfig", autospec=False)
@patch.object(DarkSkySync, "load", autospec=True, side_effect=[[FILENAME_TEST_REMOTE]])
def test_get_abs_path_remote(dss_object, load_object):
    """
    Test galsbi.ucat.io_util.get_abs_path for a remote path (i.e. a local, non-
    """
    path = io_util.get_abs_path(FILENAME_TEST_REMOTE, root_path="")
    assert path == FILENAME_TEST_REMOTE


def test_load_from_hdf5():
    """
    Test the loading of numpy-arrays from a HDF5-file.
    """

    data = np.random.uniform(size=10)
    path = os.path.join(os.getcwd(), "testfile.h5")

    with h5py.File(path, mode="w") as f:
        f.create_dataset("data", data=data)
        f.create_group("data2")
        f["data2"].create_dataset("data", data=data)

    x = io_util.load_from_hdf5(path, "data")

    assert np.array_equal(x, data)

    x = io_util.load_from_hdf5(path, "data", hdf5_path="data2/")

    assert np.array_equal(x, data)

    x = io_util.load_from_hdf5(path, ["data"])

    assert np.array_equal(x[0], data)

    x, y = io_util.load_from_hdf5(path, ("data", "data2/data"))

    assert np.array_equal(x, data)
    assert np.array_equal(y, data)

    os.remove(path)


def test_get_local_abs_path_with_remote_path():
    # Test a path with "@" and ":/" in it
    path = "user@server:/path/to/file"
    assert io_util.get_local_abs_path(path) == path


def test_get_local_abs_path_with_absolute_path():
    # Test an absolute path
    path = "/absolute/path/to/file"
    assert io_util.get_local_abs_path(path) == path


def test_get_local_abs_path_with_relative_path_and_submit_dir():
    # Test a relative path with SUBMIT_DIR set in the environment
    relative_path = "relative/path/to/file"
    submit_dir = "/submit/dir"

    with patch.dict(os.environ, {"SUBMIT_DIR": submit_dir}):
        expected_path = os.path.join(submit_dir, relative_path)
        assert io_util.get_local_abs_path(relative_path) == expected_path


def test_get_local_abs_path_with_relative_path_and_no_submit_dir():
    # Test a relative path without SUBMIT_DIR, should use os.getcwd()
    relative_path = "relative/path/to/file"
    current_dir = "/current/working/dir"

    with patch("os.getcwd", return_value=current_dir):
        expected_path = os.path.join(current_dir, relative_path)
        assert io_util.get_local_abs_path(relative_path) == expected_path
