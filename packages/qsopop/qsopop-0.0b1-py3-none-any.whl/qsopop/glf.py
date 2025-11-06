
import numpy as np
from astropy.cosmology import FlatLambdaCDM

from qsopop.lumfun import SchechterLF, SchechterLFLum, Parameter


class Meyer2024O3LF_z7(SchechterLFLum):
    """Implementation of the [OIII] 5007 luminosity function of
        Meyer+2024 at z~7.

        ADS reference: https://ui.adsabs.harvard.edu/abs/2024arXiv240505111M/abstract

        The luminosity function is parameterized as a schechter function.

        This implementation adopts the results presented in Section 4.2 (main
         text)
        """
    def __init__(self, cosmology=None):

        phi_star = Parameter(10**(-4.06), 'phi_star')
        alpha = Parameter(-2.06, 'alpha')
        log_lum_star = Parameter(10**42.98, 'lum_star')

        parameters = {'phi_star': phi_star,
                      'alpha': alpha,
                      'lum_star': log_lum_star}

        param_functions = {}

        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 7.1


        super(Meyer2024O3LF_z7, self).__init__(parameters, param_functions,
                                                lum_type=lum_type,
                                                ref_cosmology=ref_cosmology,
                                                ref_redsh=ref_redsh,
                                                cosmology=cosmology)


class Bouwens2022LF(SchechterLF):

    def __init__(self, verbose=0):

        parameters = {}

        param_functions = {'alpha': self.alpha,
                           'mag_star': self.mag_star,
                           'phi_star': self.phi_star
                           }

        lum_type = 'UV'

        super(Bouwens2022LF, self).__init__(parameters, param_functions,
                                                 lum_type=lum_type,
                                            verbose=verbose)


    @staticmethod
    def mag_star(redsh):

        zt = 2.42
        if type(redsh) == np.ndarray:
            redsh_row = redsh[0, :]
            mag_star_row = np.zeros_like(redsh_row)
            for i, i_redsh in enumerate(redsh_row):
                if i_redsh < zt:
                    mag_star_row[i] = -20.87 + -1.10*(i_redsh-zt)
                else:
                    mag_star_row[i] = -21.04 + -0.05*(i_redsh-6)

            return np.tile(mag_star_row, (redsh.shape[0], 1))

        elif type(redsh) == float or type(redsh) == np.float64:
            if redsh < zt:
                return -20.87 + -1.10*(redsh-zt)
            else:
                return -21.04 + -0.05*(redsh-6)

    @staticmethod
    def phi_star(redsh):

        log_phi_star = np.log10(
            0.38 * 1e-3 * 10 ** (-0.35 * (redsh - 6.) - 0.027 * (redsh - 6.) **
                                 2))

        return 10**log_phi_star


    @staticmethod
    def alpha(redsh):

            return -1.95 - 0.11*(redsh-6.)