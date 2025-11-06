
import numpy as np
from astropy import units
from astropy import constants as const
from astropy.cosmology import FlatLambdaCDM


# https://ui.adsabs.harvard.edu/abs/2022ApJS..259...20H/abstract
# UV luminosity function (total: galaxy+ AGN)
# z=6
harikane2022 = \
{'lum': np.array([-25.02, -24.52, -24.02, -23.52, -23.12, -22.82,
                  -22.52, -22.22, -21.92, -21.62, -21.32, -21.02]),
 'phi': np.array([1.05e-8, 2.13e-8, 2.77e-8, 8.51e-8, 3.34e-7, 1.24e-6,
                  2.67e-6, 4.48e-6, 1.10e-5, 3.69e-5, 7.35e-5, 1.77e-4]),

 'phi_unit': units.Mpc ** -3 * units.mag ** -1,
 'lum_type': 'M1450', # should be MUV
 'lum_unit': units.mag,
 'sigma_phi': np.array([[1.05e-8, 2.13e-8, 2.23e-8, 2.25e-8, 0.72e-7, 0.14e-6,
                         0.39e-6, 0.53e-6, 0.09e-5, 0.48e-5, 0.85e-5, 0.21e-4],
                        [4.11e-8, 4.21e-8, 4.19e-8, 5.38e-8, 0.72e-7, 0.15e-6,
                         0.39e-6, 0.53e-6, 0.09e-5, 0.48e-5, 0.85e-5,
                         0.21e-4]]),
 'ref_cosmology': FlatLambdaCDM(H0=67.774, Om0=0.3089, Ob0=0.049),
 'redshift': 6,}


# z=7
harikane2022z7 = \
{'lum': np.array([-25.42, -24.92, -24.42, -23.92, -23.42, -22.92,
                  -22.42, -21.92]),
 'phi': np.array([5.64E-9, 8.89E-9, 2.41E-8, 9.02E-8, 1.62E-7, 4.63E-7,
                  1.95E-6, 3.47E-6]),

 'phi_unit': units.Mpc ** -3 * units.mag ** -1,
 'lum_type': 'M1450', # should be MUV
 'lum_unit': units.mag,
 'sigma_phi': np.array([[5.64E-9, 7.41E-9, 0.98E-8, 1.66E-8, 0.23E-7,
                         2.71E-7, 0.67E-6, 1.03E-6],
                        [14.65E-9, 15.29E-9, 1.75E-8, 2.13E-8, 0.3E-7,
                         7.53E-7, 1.13E-6, 1.7E-6]]),
 'ref_cosmology': FlatLambdaCDM(H0=67.774, Om0=0.3089, Ob0=0.049),
 'redshift': 7}


# https://ui.adsabs.harvard.edu/abs/2021AJ....162...47B/abstract
# z=7
bouwens2021z7 = \
{'lum': np.array([-22.19, -21.69, -21.19, -20.69, -20.19, -19.69,
                  -19.19, -18.69, -17.94, -16.94]),
 'phi': np.array([1e-6, 41e-6, 47e-6, 198e-6, 283e-6, 589e-6,
                  1172e-6, 1433e-6, 5760e-6, 8320e-6]),

 'phi_unit': units.Mpc ** -3 * units.mag ** -1,
 'lum_type': 'M1450', # should be MUV
 'lum_unit': units.mag,
 'sigma_phi': np.array([[2e-6, 11e-6, 15e-6, 36e-6, 66e-6, 126e-6, 336e-6,
                         419e-6, 1440e-6, 2900e-6],
                        [2e-6, 11e-6, 15e-6, 36e-6, 66e-6, 126e-6, 336e-6,
                         419e-6, 1440e-6, 2900e-6]]),
 'ref_cosmology': FlatLambdaCDM(H0=70, Om0=0.30),
 'redshift': 7}
