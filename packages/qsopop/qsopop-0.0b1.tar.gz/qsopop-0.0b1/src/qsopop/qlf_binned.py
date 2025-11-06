
import numpy as np
from astropy import units
from astropy import constants as const
from astropy.cosmology import FlatLambdaCDM

mcgreer2013_str82 = \
      {'lum': np.array([-27.0, -26.45, -25.9, -25.35, -24.8, -24.25]),
       'log_phi': np.array([-8.4, -7.84, -7.9, -7.53, -7.36, -7.14]),
       'sigma_phi': np.array([2.81, 6.97, 5.92, 10.23, 11.51, 19.9])*1e-9,
       'phi_unit': units.Mpc ** -3 * units.mag ** -1,
       'lum_type': 'M1450',
       'lum_unit': units.mag,
       'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.272),
       'redshift': 4.9,
       'redshift_range': [4.7, 5.1]
       }

mcgreer2013_dr7 = \
       {'lum': np.array([-28.05, -27.55, -27.05, -26.55, -26.05]),
        'log_phi': np.array([-9.45, -9.24, -8.51, -8.20, -7.9]),
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([0.21, 0.26, 0.58, 0.91, 1.89])*1e-9,
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.272),
        'redshift': 4.9,
        'redshift_range': [4.7, 5.1]
        }

mcgreer2018_main = \
       {'lum': np.array([-28.55, -28.05, -27.55, -27.05, -26.55, -26.05]),
        'log_phi': np.array([-9.90, -9.70, -8.89, -8.41, -8.10, -8.03]),
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([0.12, 0.14, 0.37, 0.72, 1.08, 1.74])*1e-9,
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.272),
        'redshift': 5,
        'redshift_range': [4.7, 5.3]
        }

mcgreer2018_s82 = \
       {'lum': np.array([-27.00, -26.45, -25.90, -25.35, -24.80, -24.25]),
        'log_phi': np.array([-8.06, -7.75, -8.23, -7.47, -7.24, -7.22]),
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([5.57, 6.97, 3.38, 10.39, 13.12, 21.91])*1e-9,
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.272),
        'redshift': 5,
        'redshift_range': [4.7, 5.3]
        }

mcgreer2018_cfhtls_wide = \
       {'lum': np.array([-26.35, -25.25, -24.35, -23.65, -22.90]),
        'log_phi': np.array([-8.12, -7.56, -7.25, -7.32, -7.32]),
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([4.34, 12.70, 18.05, 23.77, 28.24])*1e-9,
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.272),
        'redshift': 5,
        'redshift_range': [4.7, 5.3]
        }

matsuoka2018 =  \
       {'lum': np.array([-22, -22.75, -23.25, -23.75, -24.25, -24.75, -25.25,
                         -25.75, -26.25, -26.75, -27.5, -29]),
        'phi': np.array([16.2, 23.0, 10.9, 8.3, 6.6, 7.0, 4.6, 1.33, 0.9, 0.58,
                         0.242, 0.0079])*1e-9,
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([16.2, 8.1, 3.6, 2.6, 2.0, 1.7, 1.2,
                                   0.6, 0.32, 0.17, 0.061, 0.0079])*1e-9,
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
        'redshift': 6.1,
        'redshift_range': [5.7, 6.5]
        }


matsuoka2023 = \
    {'lum': np.array([-23.25, -23.75, -24.25, -24.75, -25.25, -25.75, -26.25,
                      -26.75, -27.5]),
     'phi': np.array([2.5, 3.0, 3.5, 3.2, 1.58, 0.75, 0.63, 0.18, 0.082]) * 1e-9,
     'phi_unit': units.Mpc ** -3 * units.mag ** -1,
     'lum_type': 'M1450',
     'lum_unit': units.mag,
     'sigma_phi': np.array([1.8, 1.5, 1.4, 1.3, 0.91, 0.53, 0.26, 0.10,
                            0.047]) * 1e-9,
     'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
     'redshift': 7,
     'redshift_range': [6.55, 7.15]
     }

# M0 M1 Z0 Z1 M1450_Mean M1450_err z_Mean N N_corr Phi Phi_err
# -27.6 -26.9 6.45 7.05 -27.1849570034 0.198454192575 6.68253 4 6.57997180974 1.49806504375e-10 4.76706351322e-11
# -26.9 -26.2 6.45 7.05 -26.4394997883 0.141104303161 6.70167 9 15.7066648272 3.5759432125e-10 7.57916215887e-11
# -26.2 -25.5 6.45 7.05 -25.8306028526 0.265699553273 6.65747 4 36.3303873458 8.27135508817e-10 3.19637408061e-10

wangfeige2019 =  \
       {'lum': np.array([-27.1849570034, -26.4394997883, -25.8306028526]),
        'sigma_lum': np.array([0.198454192575, 0.141104303161, 0.265699553273]),

        'lum_bins': np.array([[-27.6, -26.9], [-26.9, -26.2], [-26.2, -25.5]]),
        'phi': np.array([1.49806504375e-10, 3.5759432125e-10,
                         8.27135508817e-10]),
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([4.76706351322e-11, 7.57916215887e-11,
                               3.19637408061e-10]),
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
        'redshift_mean': np.array([6.68253, 6.70167, 6.65747]),
        'redshift': 6.7,
        'redshift_range': [6.45, 7.05]
        }

jianglinhua2016 =  \
       {'lum': np.array([-26.599, -27.199, -27.799, -28.699, -24.829,
                         -25.929, -26.449]),
        'phi': np.array([5.27E-10, 3.43E-10, 1.36E-10, 1.51E-11, 7.09E-09,
                         3.16E-09, 1.06E-09]),
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([1.7387E-01, 1.2838E-01, 5.0821E-02, 1.4950E-02,
                               2.6535E+00, 1.2782E+00, 3.3034E-01]) * 1E-9,
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
        'lum_median': [-26.78, -27.11, -27.61, -29.1, -24.73, -25.74, -26.27],
        'survey': ['main_survey', 'main_survey', 'main_survey', 'main_survey',
                   'stripe82', 'stripe82', 'overlap_region'],
        'redshift': 6.05,
        'redshift_range': [5.7, 6.4]
        }

# Add Willott 2010
# z=6 optical quasar luminosity function data from Willott et al. 2010, AJ, 139, 906.
# Bins for CFHQS, SDSS main and SDSS deep samples. See Sec. 5.1 of the paper.
# Note that the SDSS data have been rebinned by me, so are not the same binned numbers as found in Fan et al. and Jiang et al. papers.
#
# Sample  M_1450(avg) M_1450(low) M_1450(high)  rho (Mpc^-3 mag^-1)  rho_err
#==================================================================================
# SDSS main   -27.74      -28.00      -27.50        2.2908E-10        1.1454E-10
# SDSS main   -27.23      -27.50      -27.00        3.7653E-10        1.6839E-10
# SDSS main   -26.78      -27.00      -26.68        1.0794E-09        4.8271E-10
# SDSS deep   -25.97      -27.00      -25.50        2.1946E-09        9.8146E-10
# SDSS deep   -25.18      -25.50      -24.00        6.6670E-09        2.9816E-09
# CFHQS       -26.15      -27.00      -25.50        1.0070E-09        5.0249E-10
# CFHQS       -24.66      -25.50      -24.00        6.9481E-09        2.0047E-09
# CFHQS       -22.21      -23.50      -22.00        5.1438E-08        5.1437E-08

willott2010 = {'lum': np.array([-27.74,  -27.23, -26.78, -25.97, -25.18,
                                -26.15, -24.66, -22.21]),
               'lum_bins': np.array(
                   [[-28, -27.5], [-27.5, -27], [-27.0, -26.68],
                    [-27.0, -25.5], [-25.5, -24], [-27.0, -25.5],
                    [-25.5, -24.0], [-23.5, -22.0]]),
        'phi': np.array([2.2908E-10, 3.7653E-10, 1.0794E-09,
                         2.1946E-09, 6.6670E-09, 1.0070E-09,
                         6.9481E-09, 5.1438E-08]),
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([1.1454E-10, 1.6839E-10, 4.8271E-10,
                               9.8146E-10, 2.9816E-09, 5.0249E-10,
                               2.0047E-09, 5.1437E-08]),
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.28),
        'redshift': 6,
        'redshift_range': [5.8, 6.4]
        }


willott2010_cfhqs = {'lum': np.array([-26.15, -24.66, -22.21]),
               'lum_bins': np.array(
                   [[-27.0, -25.5],
                    [-25.5, -24.0], [-23.5, -22.0]]),
        'phi': np.array([1.0070E-09,
                         6.9481E-09, 5.1438E-08]),
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([5.0249E-10,
                               2.0047E-09, 5.1437E-08]),
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.28),
        'redshift': 6,
        'redshift_range': [5.8, 6.4]
        }


# Add Jinyi Yang 2016
yangjinyi2016 =  \
       {'lum': np.array([-28.99, -28.55, -28.05, -27.55, -27.05]),
        'log_phi': np.array([-9.48, -9.86, -9.36, -9.09, -8.7]),
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([0.33, 0.08, 0.15, 0.19, 0.32]) * 1E-9,
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.272),
        'redshift': 5,
        'redshift_range': [4.7, 5.4]
        }


# Schindler+2019 ELQS QLF
# lum bin edges −29.1, −28.7, −28.3, −28, −27.7, −27.5
#M1450 N Ncorr log10Φ σΦ Bin
#(mag) (Mpc−3 mag−1) (Gpc−3 mag−1) Filled
# 2.8 - 3.0
# −28.9 2 3.9 −9.46 0.25 True
# −28.5 4 10.1 −9.05 0.50 True
# −28.15 11 28.6 −8.47 1.08 True
# −27.85 7 21.2 −8.60 1.00 True
# −27.6 9 41.3 −8.13 2.59 True

schindler2019_2p9 = \
       {'lum': np.array([-28.9, -28.5, -28.15, -27.85, -27.6]),
        'lum_bins': np.array([[-29.1, -28.7], [-28.7, -28.3],
                              [-28.3, -28.0], [-28.0, -27.7],
                              [-27.7, -27.5]]),
        'log_phi': np.array([-9.46, -9.05, -8.47, -8.6, -8.13]),
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([0.25, 0.50, 1.08, 1.00, 2.59]) * 1E-9,
        'bin_filled': np.array([True, True, True, True, True]),
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
        'redshift': 2.9,
        'redshift_range': [2.8, 3.0]
        }

# 3.0 - 3.5
# −28.9 3 3.9 −9.85 0.08 True
# −28.5 10 12.9 −9.33 0.15 True
# −28.15 28 42.0 −8.69 0.39 True
# −27.85 31 67.6 −8.48 0.60 True
# −27.6 17 69.9 −8.29 1.28 False

schindler2019_3p25 = \
       {'lum': np.array([-28.9, -28.5, -28.15, -27.85, -27.6]),
        'lum_bins': np.array([[-29.1, -28.7], [-28.7, -28.3],
                              [-28.3, -28.0], [-28.0, -27.7],
                              [-27.7, -27.5]]),
        'log_phi': np.array([-9.85, -9.33, -8.69, -8.48, -8.29]),
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([0.08, 0.15, 0.39, 0.6, 1.28]) * 1E-9,
        'bin_filled': np.array([True, True, True, True, False]),
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
        'redshift': 3.25,
        'redshift_range': [3.0, 3.5]
        }

# 3.5 - 4.0
# −28.9 2 2.1 −10.09 0.06 True
# −28.5 6 7.2 −9.56 0.11 True
# −28.15 12 18.8 −9.02 0.28 True
# −27.85 6 15.4 −9.08 0.34 False
# −27.6 2 9.3 −8.68 1.49 False

schindler2019_3p75 = \
       {'lum': np.array([-28.9, -28.5, -28.15, -27.85, -27.6]),
        'lum_bins': np.array([[-29.1, -28.7], [-28.7, -28.3],
                              [-28.3, -28.0], [-28.0, -27.7],
                              [-27.7, -27.5]]),
        'log_phi': np.array([-10.09, -9.56, -9.02, -9.08, -8.68]),
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([0.06, 0.11, 0.28, 0.34, 1.49]) * 1E-9,
        'bin_filled': np.array([True, True, True, False, False]),
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
        'redshift': 3.75,
        'redshift_range': [3.5, 4.0]
        }


# 4.0 - 4.5
# −28.9 2 2.3 −10.04 0.06 True
# −28.5 5 7.8 −9.50 0.14 True

schindler2019_4p25 = \
       {'lum': np.array([-28.9, -28.5]),
        'lum_bins': np.array([[-29.1, -28.7], [-28.7, -28.3]]),
        'log_phi': np.array([-10.04, -9.5]),
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([0.06, 0.14]) * 1E-9,
        'bin_filled': np.array([True, True]),
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
        'redshift': 4.25,
        'redshift_range': [4.0, 4.25]
        }

# Glikman+2011
# M1450 Bin Center 〈M1450 〉a ΦNQSO
# (mag) (mag) (10−8 Mpc−3 mag−1)
# SDSS
# −28.5 −28.45 0.008+0.011−0.005 2
# −27.5 −27.33 0.20+0.04−0.03 41
# −26.5 −26.46 0.93 ± 0.07 169
# −25.5 −25.70 4.3 ± 0.5 102
# −24.5 −24.72 0.4+0.3−0.2 4
# NDWFS+DLS
# −25.5 −25.37 24+13−9 7
# −24.5 −24.71 8.8+8.5−4.8 3
# −23.5 −23.47 143+77−53 7
# −22.5 −22.61 307+208−133 5
# −21.5 −21.61 434+572−280 2

glikman2011_ndwfs_dls = \
       {'lum': np.array([-25.5, -24.5, -23.5, -22.5, -21.5]),
        'lum_mean': np.array([-25.37, -24.71, -23.47, -22.61, -21.61]),
        'phi': np.array([24, 8.8, 143, 307, 434])*1E-8,
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([[9, 4.8, 53, 133, 280],[13, 8.5, 77, 208,
                                                       572]]) * 1E-8,
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
        'redshift': 4.0,
        'redshift_range': [3.74, 5.06]
        }

# Giallongo2019
# Δz M 1450 fobs fcorr Nobj fMC
# 4–5
# −19 6.81 -+14.54 5.81 8.72 6 18.05±4.27
# −20 4.74 -+11.47 4.59 6.88 6 8.03±3.34
# −21 3.29 -+5.08 2.21 3.45 5 4.52±1.15
# −22 1.24 -+1.31 0.87 1.74 2 1.33±0.11
# 5–6.1
# −19 3.62 -+7.27 4.02 7.12 3 6.27±3.42
# −20 3.12 -+4.77 2.31 3.79 4 2.91±1.84
# −21 0.65 -+0.69 0.60 1.61 1 1.13±0.70
# −22 0.61 -+0.62 0.54 1.44 1 0.80±0.33


giallongo2019_z4p5 = \
       {'lum': np.array([-19, -20, -21, -22]),
        'phi': np.array([14.54, 11.47, 5.08, 1.31])*1E-6,
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([[5.81, 4.59, 2.21, 0.87],
                               [8.72, 6.88, 3.45, 1.74]]) * 1E-6,
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
        'redshift': 4.5,
        'redshift_range': [4, 5]
        }

giallongo2019_z5p05 = \
       {'lum': np.array([-19, -20, -21, -22]),
        'phi': np.array([7.27, 4.77, 0.69, 0.62])*1E-6,
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([[4.02, 2.31, 0.6, 0.54],
                               [7.12, 3.79, 1.61, 1.44]]) * 1E-6,
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
        'redshift': 5.6,
        'redshift_range': [5, 6.1]
        }

# Boutsia2018 COSMOS
# M1450 ΦupsF lowsF NAGN corrF
# Mpc Mag3 1 - -
# −24.5 3.509e-07 2.789e-07 1.699e-07 4 7.018e-07
# −23.5 7.895e-07 3.616e-07 2.595e-07 9 1.579e-06

boutsia2018 = \
       {'lum': np.array([-24.5, -23.5]),
        'phi': np.array([7.018e-07, 1.579e-06]),
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([[1.699e-07, 2.595e-07],
                               [2.789e-07, 3.616e-07]]),
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
        'redshift': 3.9,
        'redshift_range': [3.6, 4.2]
        }


#Boutsia2021 QUBRICS
# Interval <M1450 >NQSO ΦσΦ(up)σΦ(low)
# cMpc−3 cMpc−3 cMpc−3
# −28.5 M1450 −28.0 −28.25 36 1.089E-09 2.136E-10 1.809E-10
# −29.0 M1450 −28.5 −28.75 9 2.611E-10 1.196E-10 8.581E-11
# −29.5 M1450 −29.0 −29.25 2 5.802E-11 7.712E-11 3.838E-11

boutsia2021  = \
       {'lum': np.array([-28.25, -28.75, -29.25]),
        'lum_bins': np.array([[-28.5, -28.0], [-29.0, -28.5], [-29.5, -29.0]]),
        'phi': np.array([1.089E-09, 2.611E-10, 5.802E-11]),
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([[1.809E-10, 8.581E-11, 3.838E-11],
                               [2.136E-10, 1.196E-10, 7.712E-11]]),
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
        'redshift': 3.9,
        'redshift_range': [3.6, 4.2]
        }


# Kim, Yongjung 2021 IMS
# −27.25 1 4.7±4.7 0 L45 1.52±0.23
# −26.75 1 4.7±4.7 1 7.1±7.1 0 L
# −26.25 3 15.1±8.7 3 19.6±11.3 0 L
# −25.75 3 16.5±9.5 3 19.2±11.1 0 L
# −25.25 5 30.8±13.8 4 28.8±14.4 0 L
# −24.75 7 48.1±18.2 6 51.3±20.9 0 L
# −24.25 10 70.7±22.4 6 55.0±22.5 0 L
# −23.75 7 59.0±22.3 6 69.5±28.4 0 L
# −23.25 6 104.1±42.5 3 68.1±39.3 0 L

kim2021  = \
       {'lum': np.array([-27.25, -26.75, -26.25, -25.75, -25.25, -24.75,
                         -24.25,-23.75, -23.25]),
        'phi': np.array([4.7, 4.7, 15.1, 16.5, 30.8, 48.1, 70.7, 59.0,
                         104.1])*1E-9,
        'phi_unit': units.Mpc**-3 * units.mag**-1,
        'lum_type': 'M1450',
        'lum_unit': units.mag,
        'sigma_phi': np.array([[4.7, 4.7, 8.7, 9.5, 13.8, 18.2, 22.4, 22.3,
                                42.5],
                               [4.7, 4.7, 8.7, 9.5, 13.8, 18.2, 22.4, 22.3,
                                42.5]])*1E-9,
        'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
        'redshift': 5,
        'redshift_range': [4.7, 5.4]
        }


schindler2023 = \
    {'lum': np.array([-27.5, -27.0, -26.5, -26.0, -25.375]),
    'lum_bins': np.array([[-27.75, -27.25], [-27.25, -26.75], [-26.75, -26.25],
                          [-26.25, -25.75], [-25.75, -25.0]]),
     'phi': np.array([1.4925734119219086e-10, 3.8109585059543343e-10,
                      8.433440329101938e-10, 1.7002671246840014e-09,
                      3.433265511360749e-09]),
     'phi_unit': units.Mpc ** -3 * units.mag ** -1,
     'lum_type': 'M1450',
     'lum_unit': units.mag,
     'sigma_phi': np.array([[5.920464696955311e-11, 9.729247866390617e-11,
                             1.506503895812834e-10, 2.7825835990688776e-10,
                             6.037443823093605e-10],
                            [8.914923235074313e-11, 1.2598620075912893e-10,
                             1.8030527016639774e-10, 3.2800004737690426e-10,
                             7.205450300694091e-10]]),
     'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
     'redshift': 6,
     'redshift_range': [5.95, 6.25]
     }


# https://ui.adsabs.harvard.edu/abs/2020ApJ...897...94G/abstract
grazian2020 = \
{'lum': np.array([-22.33]),
 'phi': np.array([1.291e-6]),

 'phi_unit': units.Mpc ** -3 * units.mag ** -1,
 'lum_type': 'M1450',
 'lum_unit': units.mag,
 'sigma_phi': np.array([[0.854e-6],
                        [1.717e-6]]),
 'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
 'redshift': 5.5,
 'redshift_range:': [5.0, 6.1]}


#-------------------------
# LRD luminosity functions
#-------------------------

harikane2023z7_arxiv = \
{'lum': np.array([-21.5]),
 'phi': np.array([1.6e-6]),
 'phi_unit': units.Mpc ** -3 * units.mag ** -1,
 'sigma_phi': np.array([[1.4e-6],
                        [3.7e-6]]),
 'lum_type': 'M1450',  # should be MUV
 'lum_unit': units.mag,
 'ref_cosmology': FlatLambdaCDM(H0=67.66, Om0=0.3111),
 'redshift': 7}

# https://ui.adsabs.harvard.edu/abs/2024ApJ...964...39G

greene2024z7 = \
{'lum': np.array([-19.0, -18.0, -17.0]),
 'phi': np.array([1.3, 2.6, 4.0]) * 1e-5,
 'phi_unit': units.Mpc ** -3 * units.mag ** -1,
'sigma_phi': np.array([[0.5, 0.7, 1.0],
                       [0.5, 0.7, 1.0]]) * 1e-5,
 'lum_type': 'M1450',
 'lum_unit': units.mag,
 'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
 'redshift': 7.5}

greene2024z7_bol = \
{'lum': np.array([1e+45, 1e+46]),
 'phi': np.array([2.6, 1.3]) * 1e-5,
 'phi_unit': units.Mpc ** -3 * units.mag ** -1,
'sigma_phi': np.array([[0.5, 0.5],
                       [0.5, 0.5]]) * 1e-5,
 'lum_type': 'M1450',  # should be Lbol
 'lum_unit': units.mag,
 'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
 'redshift': 7.5}


kokorev2024z7_arxiv = \
{'lum': np.array([-21.0, -20.0, -19.0, -18.0, -17.0]),
 'log_phi': np.array([-6.12, -5.58, -5.02, -4.95, -4.58]),
 # 'phi': np.array([1.3, 2.6, 4.0]) ,
 'phi_unit': units.Mpc ** -3 * units.mag ** -1,
 'sigma_log_phi': np.array([0.92, 0.55, 0.30, 0.28, 0.75]),
 'lum_type': 'M1450',  # should be MUV
 'lum_unit': units.mag,
 'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
 'redshift': 7.5}

kokorev2024z7_bol_arxiv = \
{'lum': np.array([1e+44, 1e+45, 1e+46, 1e+47]),
 'log_phi': np.array([-5.48, -4.51, -4.76, -5.47]),
 'phi_unit': units.Mpc ** -3 * units.mag ** -1,
'sigma_log_phi': np.array([1, 0.23, 0.15, 0.29]),
 'lum_type': 'M1450',  # should be Lbol
 'lum_unit': units.mag,
 'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.3),
 'redshift': 7.5}


kocevskiz2024_7p5_arxiv = \
{'lum': np.array([-17.0, -18.0, -19.0, -20.0, -21.0, -22.0]),
 'log_phi': np.array([-4.53, -4.61, -4.87, -5.23, -5.87, -6.35]),
 'phi_unit': units.Mpc ** -3 * units.mag ** -1,
 'sigma_log_phi': np.array([[0.13, 0.08, 0.08, 0.14, 0.34, 0.76],
                        [0.13, 0.08, 0.09, 0.13, 0.29, 0.52]]),
 'lum_type': 'M1450',  # should be MUV
 'lum_unit': units.mag,
 'ref_cosmology': FlatLambdaCDM(H0=67.66, Om0=0.3111),
 'redshift': 7}
