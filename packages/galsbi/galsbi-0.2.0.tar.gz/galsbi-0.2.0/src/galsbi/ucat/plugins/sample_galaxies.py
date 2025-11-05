# Copyright (C) 2018 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created on Mar 5, 2018
author: Joerg Herbel
"""

from ivy.plugin.base_plugin import BasePlugin


class Plugin(BasePlugin):
    """
    Generate a random catalog of galaxies with magnitudes in multiple bands.
    """

    # @profile
    def __call__(self):
        from galsbi.ucat.plugins.sample_galaxies_morph import \
            Plugin as PluginMorph
        from galsbi.ucat.plugins.sample_galaxies_photo import \
            Plugin as PluginPhoto

        PluginPhoto(self.ctx)()
        PluginMorph(self.ctx)()

    def __str__(self):
        return "sample gal population"
