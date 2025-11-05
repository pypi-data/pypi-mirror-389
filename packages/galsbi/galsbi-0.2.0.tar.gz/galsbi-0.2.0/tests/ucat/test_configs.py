# Copyright (C) 2024 ETH Zurich
# Institute for Particle Physics and Astrophysics
# Author: Silvan Fischbacher
# created: Thu Aug 01 2024

import ivy


def test_common():
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.common")
    )
    assert ctx.parameters.seed == 102301239
    assert ctx.parameters.gal_num_seed_offset == 100
    assert ctx.parameters.maps_remote_dir == "ufig_res/maps/"


def test_galaxy_catalog():
    ctx = ivy.context.create_ctx(
        parameters=ivy.load_configs("galsbi.ucat.config.galaxy_catalog")
    )
    # assert that new parameters are correclty overwritten
    assert ctx.parameters.plugins == ["ucat.plugins.sample_galaxies"]
    assert ctx.parameters.maps_remote_dir == "ucat/resources/"
    assert ctx.parameters.filters_file_name == "filters_collection.h5"
    assert ctx.parameters.n_templates == 5
    assert ctx.parameters.magnitude_calculation == "table"
    assert (
        ctx.parameters.templates_file_name
        == "ucat/sed_templates/template_spectra_BlantonRoweis07.h5"
    )
    assert (
        ctx.parameters.templates_int_tables_file_name
        == "sed_integrals__template_spectra_BlantonRoweis07.h5"
    )
    assert ctx.parameters.extinction_map_file_name == "lambda_sfd_ebv.fits"

    # assert that common parameters are still present
    assert ctx.parameters.seed == 102301239
    assert ctx.parameters.gal_num_seed_offset == 100
