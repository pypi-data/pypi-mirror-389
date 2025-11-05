# Copyright (C) 2018 ETH Zurich, Institute for Particle Physics and Astrophysics

"""
Created Sept 2021
author: Tomasz Kacprzak

This script manipulates filter information. It can create the filters_collection.h5
file, which contains all listed filters we use.
"""

import os
from collections import OrderedDict

import h5py
import numpy as np
from cosmic_toolbox import logger
from scipy.integrate import simpson as simps

LOGGER = logger.get_logger(__file__)


def create_filter_collection(dirpath_res):
    """
    Create a filter collection file
    Currently supported instruments: DECam, VISTA, GenericBessel
    """

    def add_decam_filters(filters_collect):
        # data downloaded from:
        # https://noirlab.edu/science/programs/ctio/filters/Dark-Energy-Camera
        filepath_filters = os.path.join(
            dirpath_res, "filters/DECam_filters_with_atm.txt"
        )
        # LAMBDA    g      r        i      z        Y     atm
        filter_data = np.loadtxt(filepath_filters).T
        atm = filter_data[-1]
        lam = filter_data[0]
        for i, b in enumerate(["g", "r", "i", "z", "Y"]):
            filters_collect[f"DECam_{b}"] = dict(amp=filter_data[i + 1], lam=lam)
            filters_collect[f"DECamNoAtm_{b}"] = dict(
                amp=filter_data[i + 1] / atm, lam=lam
            )
            LOGGER.info(f"added DECam {b}-band")

        b = "u"
        decam_u_lam, decam_u_amp = np.loadtxt(
            os.path.join(dirpath_res, "filters/DECam_2014_u.res")
        ).T
        filters_collect[f"DECam_{b}"] = dict(amp=decam_u_amp, lam=decam_u_lam)
        LOGGER.info(f"added DECam {b}-band")

    def add_bessel_filters(filters_collect):
        # generic Bessel filters from from
        # http://adsabs.harvard.edu/abs/1990PASP..102.1181B
        # http://svo2.cab.inta-csic.es/svo/theory/fps3/index.php?mode=browse&gname=Generic&asttype=
        bands = ["B", "I", "R", "U", "V"]

        for b in bands:
            lam, amp = np.loadtxt(
                os.path.join(dirpath_res, f"filters/Generic_Bessell.{b}.dat")
            ).T
            filters_collect[f"GenericBessel_{b}"] = dict(amp=amp, lam=lam)
            LOGGER.info(f"added GenericBessel {b}-band")

        bands = ["J", "H", "K", "L", "M"]
        for b in bands:
            lam, amp = np.loadtxt(
                os.path.join(dirpath_res, f"filters/Generic_Bessell_JHKLM.{b}.dat")
            ).T
            filters_collect[f"GenericBessel_{b}"] = dict(amp=amp, lam=lam)
            LOGGER.info(f"added GenericBessel {b}-band")

    def add_johnson_filters(filters_collect):
        # generic Bessel filters from from
        # http://adsabs.harvard.edu/abs/1990PASP..102.1181B
        # http://svo2.cab.inta-csic.es/svo/theory/fps3/index.php?mode=browse&gname=Generic&asttype=
        bands = ["U", "B", "V", "R", "I", "J", "M"]

        for b in bands:
            lam, amp = np.loadtxt(
                os.path.join(dirpath_res, f"filters/Generic_Johnson.{b}.dat")
            ).T
            filters_collect[f"GenericJohnson_{b}"] = dict(amp=amp, lam=lam)
            LOGGER.info(f"added GenericJohnson {b}-band")

    def add_cosmos_filters(filters_collect):
        # https://ftp.iap.fr/pub/from_users/hjmcc/COSMOS2015/COSMOS2015_Laigle+.header
        # https://cosmos.astro.caltech.edu/page/photom
        filters = {}
        filters["Vircam_Ks"] = dict(
            filename="K_uv.res", telescope="VISTA"
        )  # Ks_MAG_AUTO
        filters["Vircam_Y"] = dict(filename="Y_uv.res", telescope="VISTA")  # Y_MAG_AUTO
        filters["Vircam_H"] = dict(filename="H_uv.res", telescope="VISTA")  # H_MAG_AUTO
        filters["Vircam_J"] = dict(filename="J_uv.res", telescope="VISTA")  # J_MAG_AUTO
        filters["SuprimeCam_B"] = dict(
            filename="B_subaru.res", telescope="SUBARU"
        )  # B_MAG_AUTO
        filters["SuprimeCam_V"] = dict(
            filename="V_subaru.res", telescope="SUBARU"
        )  # V_MAG_AUTO
        filters["SuprimeCam_ip"] = dict(
            filename="i_subaru.res", telescope="SUBARU"
        )  # ip_MAG_AUTO
        filters["SuprimeCam_r"] = dict(
            filename="r_subaru.res", telescope="SUBARU"
        )  # r_MAG_AUTO
        filters["SuprimeCam_zp"] = dict(
            filename="z_subaru.res", telescope="SUBARU"
        )  # zp_MAG_AUTO
        filters["SuprimeCam_zpp"] = dict(
            filename="suprime_FDCCD_z.res", telescope="SUBARU"
        )  # zpp_MAG_AUTO
        filters["MegaPrime_u"] = dict(
            filename="u_megaprime_sagem.res", telescope="CFHT"
        )  # u_MAG_AUTO
        filters["SuprimeCam_IA427"] = dict(
            filename="IA427.SuprimeCam.pb", telescope="SUBARU"
        )  # IB427_MAG_AUTO
        filters["SuprimeCam_IB464"] = dict(
            filename="IA464.SuprimeCam.pb", telescope="SUBARU"
        )  # IB464_MAG_AUTO
        filters["SuprimeCam_IA484"] = dict(
            filename="IA484.SuprimeCam.pb", telescope="SUBARU"
        )  # IA484_MAG_AUTO
        filters["SuprimeCam_IA505"] = dict(
            filename="IA505.SuprimeCam.pb", telescope="SUBARU"
        )  # IB505_MAG_AUTO
        filters["SuprimeCam_IA527"] = dict(
            filename="IA527.SuprimeCam.pb", telescope="SUBARU"
        )  # IA527_MAG_AUTO
        filters["SuprimeCam_IA574"] = dict(
            filename="IA574.SuprimeCam.pb", telescope="SUBARU"
        )  # IB574_MAG_AUTO
        filters["SuprimeCam_IA624"] = dict(
            filename="IA624.SuprimeCam.pb", telescope="SUBARU"
        )  # IA624_MAG_AUTO
        filters["SuprimeCam_IA679"] = dict(
            filename="IA679.SuprimeCam.pb", telescope="SUBARU"
        )  # IA679_MAG_AUTO
        filters["SuprimeCam_IA709"] = dict(
            filename="IA709.SuprimeCam.pb", telescope="SUBARU"
        )  # IB709_MAG_AUTO
        filters["SuprimeCam_IA738"] = dict(
            filename="IA738.SuprimeCam.pb", telescope="SUBARU"
        )  # IA738_MAG_AUTO
        filters["SuprimeCam_IA767"] = dict(
            filename="IA767.SuprimeCam.pb", telescope="SUBARU"
        )  # IA767_MAG_AUTO
        filters["SuprimeCam_IA827"] = dict(
            filename="IA827.SuprimeCam.pb", telescope="SUBARU"
        )  # IB827_MAG_AUTO
        filters["SuprimeCam_NB711"] = dict(
            filename="NB711.SuprimeCam.pb", telescope="SUBARU"
        )  # NB711_MAG_AUTO
        filters["SuprimeCam_NB816"] = dict(
            filename="NB816.SuprimeCam.pb", telescope="SUBARU"
        )  # NB816_MAG_AUTO
        filters["wircam_H"] = dict(
            filename="wircam_H.res", telescope="SUBARU"
        )  # Hw_MAG_AUTO
        filters["wircam_Ks"] = dict(
            filename="wircam_Ks.res", telescope="SUBARU"
        )  # Ksw_MAG_AUTO
        filters["irac_ch1"] = dict(
            filename="irac_ch1.res", telescope="SPITZER"
        )  # SPLASH_1_MAG
        filters["irac_ch2"] = dict(
            filename="irac_ch2.res", telescope="SPITZER"
        )  # SPLASH_2_MAG
        filters["irac_ch3"] = dict(
            filename="irac_ch3.res", telescope="SPITZER"
        )  # SPLASH_3_MAG
        filters["irac_ch4"] = dict(
            filename="irac_ch4.res", telescope="SPITZER"
        )  # SPLASH_4_MAG
        filters["mips_24"] = dict(filename="mips24.res", telescope="SPITZER")  # MAG_24
        filters["GALEX_FUV"] = dict(
            filename="galex1500.res", telescope="GALEX"
        )  # MAG_GALEX_FUV
        filters["GALEX_NUV"] = dict(
            filename="galex2500.res", telescope="GALEX"
        )  # MAG_GALEX_NUV

        for f in filters:
            lam, amp = np.loadtxt(
                os.path.join(
                    dirpath_res, "filters/filters_cosmos2015", filters[f]["filename"]
                )
            ).T
            filters_collect[f] = dict(amp=amp, lam=lam)
            LOGGER.info(f"added Cosmos2015 {f}")

    def add_hsc_filters(filters_collect):
        # https://hsc-release.mtk.nao.ac.jp/doc/index.php/survey__pdr3/
        # https://hsc-release.mtk.nao.ac.jp/doc/wp-content/uploads/2021/08/hsc_responses_all_rev4.zip

        bands = ["g", "r", "r2", "i", "i2", "z", "y"]
        for b in bands:
            path = os.path.join(
                dirpath_res, "filters/filters_hsc_v2018", f"hsc_{b}_v2018.dat"
            )
            lam, amp = np.loadtxt(path, comments="#").T
            filters_collect[f"HyperSuprimeCam_{b}"] = dict(amp=amp, lam=lam)
            LOGGER.info(f"added HyperSuprimeCam_{b}")

    def add_sdss_filters(filters_collect):
        # http://svo2.cab.inta-csic.es/svo/theory/fps3/index.php?mode=browse&gname=SLOAN
        bands = ["u", "g", "r", "i", "z"]
        for b in bands:
            path = os.path.join(dirpath_res, f"filters/filters_sdss/SLOAN_SDSS.{b}.dat")
            lam, amp = np.loadtxt(path).T
            filters_collect[f"SDSS_{b}"] = dict(amp=amp, lam=lam)
            LOGGER.info(f"added SDSS_{b}")

    def add_vista_filters(filters_collect):
        # http://svo2.cab.inta-csic.es/svo/theory/fps3/index.php?mode=browse&gname=Paranal&gname2=VISTA
        bands = ["Z", "Y", "J", "H", "Ks"]
        for b in bands:
            path = os.path.join(
                dirpath_res, f"filters/filters_vista/Paranal_VISTA.{b}.dat"
            )
            lam, amp = np.loadtxt(path).T
            filters_collect[f"VISTA_{b}"] = dict(amp=amp, lam=lam)
            LOGGER.info(f"added VISTA_{b}")
        for b in bands:
            path = os.path.join(
                dirpath_res, f"filters/filters_vista/Paranal_VISTA.{b}_filter.dat"
            )
            lam, amp = np.loadtxt(path).T
            filters_collect[f"VISTA_NoAtm{b}"] = dict(amp=amp, lam=lam)
            LOGGER.info(f"added VISTA_NoAtm{b}")

    LOGGER.info("============ creating filter collection")
    filters_collect = {}
    add_decam_filters(filters_collect)
    add_bessel_filters(filters_collect)
    add_johnson_filters(filters_collect)
    add_cosmos_filters(filters_collect)
    add_hsc_filters(filters_collect)
    add_sdss_filters(filters_collect)
    add_vista_filters(filters_collect)

    return filters_collect


def store_filter_collection(filepath_collection, filters_collect):
    # store collection
    n_filters = len(filters_collect)
    with h5py.File(filepath_collection, "w") as f:
        for b in filters_collect:
            for k in filters_collect[b]:
                f[f"{b}/{k}"] = filters_collect[b][k]

    LOGGER.info(f"wrote {filepath_collection} with {n_filters} filters")
    LOGGER.info(filters_collect.keys())


def load_filters(filepath_filters, filter_names=None, lam_scale=1):
    filters = OrderedDict()
    with h5py.File(filepath_filters, "r") as f:
        filter_names = list(f.keys()) if filter_names is None else filter_names
        for b in filter_names:
            amp = np.array(f[b]["amp"])
            lam = np.array(f[b]["lam"]) * lam_scale
            integ = simps(x=lam, y=amp / lam)
            LOGGER.debug(f"filter {b} integral={integ:2.5e}")
            filters[b] = dict(amp=amp, lam=lam, integ=integ)
    return filters


class UseShortFilterNames:
    """
    Interface between short and long filter names
    """

    def __init__(self, func, filters_full_names):
        self.func = func
        self.filters_full_names = filters_full_names
        self.filters_full_names_rev = {ff: fs for fs, ff in filters_full_names.items()}

    def __call__(self, **kw):
        if "filter_names" in kw:
            kw["filter_names"] = [
                self.filters_full_names[f] for f in kw["filter_names"]
            ]

        out = self.func(**kw)

        if not isinstance(out, dict):
            return out
        else:
            out_ = {}
            for k in out:
                if k in self.filters_full_names_rev:
                    out_[self.filters_full_names_rev[k]] = out[k]
        return out_

    def __getattr__(self, name):
        return getattr(self.func, name)


def get_default_full_filter_names(filters):
    filters_full_names = {f: f for f in filters}

    return filters_full_names


#  'Ks_MAG_AUTO'           Ks_uv.res
#  'Y_MAG_AUTO'            Y_uv.res
#  'H_MAG_AUTO'            H_uv.res
#  'J_MAG_AUTO'            J_uv.res
#  'B_MAG_AUTO'            B_subaru.res
#  'V_MAG_AUTO'            V_subaru.res
#  'ip_MAG_AUTO'           i_Subaru.res
#  'r_MAG_AUTO'            r_subaru.res
#  'zp_MAG_AUTO'           z_subaru.res
#  'zpp_MAG_AUTO'          suprime_FDCCD_z.res
#  'u_MAG_AUTO'            u_megaprime_sagem.res
#  'IB427_MAG_AUTO'        IB427.SuprimeCam.pb
#  'IB464_MAG_AUTO'        IB464.SuprimeCam.pb
#  'IA484_MAG_AUTO'        IA484.SuprimeCam.pb
#  'IB505_MAG_AUTO'        IB505.SuprimeCam.pb
#  'IA527_MAG_AUTO'        IA527.SuprimeCam.pb
#  'IB574_MAG_AUTO'        IB574.SuprimeCam.pb
#  'IA624_MAG_AUTO'        IA624.SuprimeCam.pb
#  'IA679_MAG_AUTO'        IA679.SuprimeCam.pb
#  'IB709_MAG_AUTO'        IB709.SuprimeCam.pb
#  'IA738_MAG_AUTO'        IA738.SuprimeCam.pb
#  'IA767_MAG_AUTO'        IA767.SuprimeCam.pb
#  'IB827_MAG_AUTO'        IB827.SuprimeCam.pb
#  'NB711_MAG_AUTO'        NB711.SuprimeCam.pb
#  'NB816_MAG_AUTO'        NB816.SuprimeCam.pb
#  'Hw_MAG_AUTO'           wircam_H.res
#  'Ksw_MAG_AUTO'          wircam_Ks.res
#  'yHSC_MAG_AUTO'         y_HSC.txt
#  'SPLASH_1_MAG',         irac_ch1.res
#  'SPLASH_2_MAG',         irac_ch2.res
#  'SPLASH_3_MAG',         irac_ch3.res
#  'SPLASH_4_MAG',         irac_ch4.res
#  'MAG_24',               mips24.res
#  'MAG_GALEX_FUV'         galex1500.res
#  'MAG_GALEX_NUV'         galex2500.res
