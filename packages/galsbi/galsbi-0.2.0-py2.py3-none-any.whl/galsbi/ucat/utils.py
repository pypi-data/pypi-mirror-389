# Copyright (C) 2017 ETH Zurich, Cosmology Research Group

"""
Created on Jan 03, 2020
author: Joerg Herbel
"""

import os

import psutil


def memory_usage_psutil():
    # return the memory usage in MB

    return psutil.Process(os.getpid()).memory_info().rss / 1024**2
