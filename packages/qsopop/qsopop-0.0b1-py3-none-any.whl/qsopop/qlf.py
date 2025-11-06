
import numpy as np
from astropy import units
from astropy import constants as const
from astropy.cosmology import FlatLambdaCDM

from qsopop.lumfun import (lum_double_power_law, SinglePowerLawLF,
                           DoublePowerLawLF, Parameter)



class ShenXuejian2020QLF_b(DoublePowerLawLF):
    """
    Shen+2020 bolometric quasar luminosity function; global fit B
    """


    def __init__(self):
        """

        """


        # Parameters

        # alpha
        a0 = Parameter(0.3653, 'a0',
                       # one_sigma_unc=[0.06,0.06]
                       )
        a1 = Parameter(-0.6006, 'a1',
                       # one_sigma_unc=[0.06,0.06]
                       )
        # a2 = Parameter(0, 'a2',
        #                # one_sigma_unc=[0.06,0.06]
        #                )

        # beta
        b0 = Parameter(2.4709, 'b0',
                       # one_sigma_unc=[0.06,0.06]
                       )
        b1 = Parameter(-0.9963, 'b1',
                       # one_sigma_unc=[0.06,0.06]
                       )
        b2 = Parameter(1.0716, 'b2',
                       # one_sigma_unc=[0.06,0.06]
                       )

        # log L_star
        c0 = Parameter(12.9656, 'c0',
                       # one_sigma_unc=[0.06,0.06]
                       )
        c1 = Parameter(-0.5758, 'c1',
                       # one_sigma_unc=[0.06,0.06]
                       )
        c2 = Parameter(0.4698, 'c2',
                       # one_sigma_unc=[0.06,0.06]
                       )

        # log phi_star
        d0 = Parameter(-3.6276, 'd0',
                       # one_sigma_unc=[0.06,0.06]
                       )
        d1 = Parameter(-0.3444, 'd1',
                       # one_sigma_unc=[0.06,0.06]
                       )

        z_ref = Parameter(2.0, 'z_ref')

        parameters = {'a0':a0,
                      'a1':a1,
                      # 'a2':a2,
                      'b0':b0,
                      'b1':b1,
                      'b2':b2,
                      'c0':c0,
                      'c1':c1,
                      'c2':c2,
                      'd0':d0,
                      'd1':d1,
                      'z_ref':z_ref}

        param_functions = {'alpha': self.alpha,
                           'beta': self.beta,
                           'lum_star': self.lum_star,
                           'phi_star': self.phi_star
                           }

        lum_type = 'bolometric'

        super(ShenXuejian2020QLF_b, self).__init__(parameters, param_functions,
                                             lum_type=lum_type)

    @staticmethod
    def alpha(redsh, a0, a1, z_ref):
        """

        :param redsh:
        :param a0:
        :param a1:
        :param z_ref:
        :return:
        """

        zterm = (1. + redsh) / (1. + z_ref)

        # T0 = 1
        # T1 = (1+redsh)
        # T2 = 2 * (1+redsh)**2 -1
        #
        # gamma_1 = a0*T0 + a1*T1 + a2*T2


        return a0 * zterm**a1

    @staticmethod
    def beta(redsh, b0, b1, b2, z_ref):
        """

        :param redsh:
        :param b0:
        :param b1:
        :param b2:
        :param z_ref:
        :return:
        """

        zterm = (1. + redsh) / (1. + z_ref)

        return 2 * b0 / (zterm ** b1 + zterm ** b2)

    @staticmethod
    def lum_star(redsh, c0, c1, c2, z_ref):
        """

        :param redsh:
        :param c0:
        :param c1:
        :param c2:
        :param z_ref:
        :return:
        """

        zterm = (1. + redsh) / (1. + z_ref)

        log_lum_star = 2 * c0 / (zterm ** c1 + zterm ** c2)

        return 10**log_lum_star # in L_sun

    @staticmethod
    def phi_star(redsh, d0, d1):

        T0 = 1
        T1 = (1+redsh)

        log_phi_star = d0*T0 + d1*T1

        return 10**log_phi_star


    def evaluate(self, lum, redsh, parameters=None):
        """Evaluate the Shen+2020 bolometric luminosity function.

        Function to be evaluated: atelier.lumfun.lum_double_power_law()

        :param lum: Luminosity for evaluation
        :type lum: float or numpy.ndarray
        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param parameters: Dictionary of parameters used for this specific
            calculation. This does not replace the parameters with which the
            luminosity function was initialized. (default=None)
        :type parameters: dict(atelier.lumfun.Parameters)
        :return: Luminosity function value
        :rtype: (numpy.ndarray,numpy.ndarray)
        """

        if parameters is None:
            parameters = self.parameters.copy()

        main_parameter_values = self.evaluate_main_parameters(lum, redsh,
                                                        parameters=parameters)

        phi_star = main_parameter_values['phi_star']
        lum_star = main_parameter_values['lum_star']
        # convert to erg/s
        lum_star = lum_star * const.L_sun.to(units.erg/units.s).value

        alpha = main_parameter_values['alpha']
        beta = main_parameter_values['beta']

        return lum_double_power_law(np.power(10, lum), phi_star, lum_star,
                                              alpha, beta)


class ShenXuejian2020QLF_a(DoublePowerLawLF):
    """
    Shen+2020 bolometric quasar luminosity function; global fit A
    """


    def __init__(self):
        """

        """


        # Parameters

        # alpha
        a0 = Parameter(0.8569, 'a0',
                       # one_sigma_unc=[0.06,0.06]
                       )
        a1 = Parameter(-0.2614, 'a1',
                       # one_sigma_unc=[0.06,0.06]
                       )
        a2 = Parameter(0.02, 'a2',
                       # one_sigma_unc=[0.06,0.06]
                       )

        # beta
        b0 = Parameter(2.5375, 'b0',
                       # one_sigma_unc=[0.06,0.06]
                       )
        b1 = Parameter(-1.0425, 'b1',
                       # one_sigma_unc=[0.06,0.06]
                       )
        b2 = Parameter(1.1201, 'b2',
                       # one_sigma_unc=[0.06,0.06]
                       )

        # log L_star
        c0 = Parameter(13.0088, 'c0',
                       # one_sigma_unc=[0.06,0.06]
                       )
        c1 = Parameter(-0.5759, 'c1',
                       # one_sigma_unc=[0.06,0.06]
                       )
        c2 = Parameter(0.4554, 'c2',
                       # one_sigma_unc=[0.06,0.06]
                       )

        # log phi_star
        d0 = Parameter(-3.5426, 'd0',
                       # one_sigma_unc=[0.06,0.06]
                       )
        d1 = Parameter(-0.3936, 'd1',
                       # one_sigma_unc=[0.06,0.06]
                       )

        z_ref = Parameter(2.0, 'z_ref')

        parameters = {'a0':a0,
                      'a1':a1,
                      'a2':a2,
                      'b0':b0,
                      'b1':b1,
                      'b2':b2,
                      'c0':c0,
                      'c1':c1,
                      'c2':c2,
                      'd0':d0,
                      'd1':d1,
                      'z_ref':z_ref}

        param_functions = {'alpha': self.alpha,
                           'beta': self.beta,
                           'lum_star': self.lum_star,
                           'phi_star': self.phi_star
                           }

        lum_type = 'bolometric'

        super(ShenXuejian2020QLF_a, self).__init__(parameters, param_functions,
                                             lum_type=lum_type)

    @staticmethod
    def alpha(redsh, a0, a1, a2):
        """

        :param redsh:
        :param a0:
        :param a1:
        :param z_ref:
        :return:
        """


        T0 = 1
        T1 = (1+redsh)
        T2 = 2 * (1+redsh)**2 - 1

        gamma_1 = a0*T0 + a1*T1 + a2*T2


        return gamma_1

    @staticmethod
    def beta(redsh, b0, b1, b2, z_ref):
        """

        :param redsh:
        :param b0:
        :param b1:
        :param b2:
        :param z_ref:
        :return:
        """

        zterm = (1. + redsh) / (1. + z_ref)

        return 2 * b0 / (zterm ** b1 + zterm ** b2)

    @staticmethod
    def lum_star(redsh, c0, c1, c2, z_ref):
        """

        :param redsh:
        :param c0:
        :param c1:
        :param c2:
        :param z_ref:
        :return:
        """

        zterm = (1. + redsh) / (1. + z_ref)

        log_lum_star = 2 * c0 / (zterm ** c1 + zterm ** c2)

        return 10**log_lum_star # in L_sun

    @staticmethod
    def phi_star(redsh, d0, d1):

        T0 = 1
        T1 = (1+redsh)

        log_phi_star = d0*T0 + d1*T1

        return 10**log_phi_star

    def evaluate(self, lum, redsh, parameters=None):
        """Evaluate the Shen+2020 bolometric luminosity function.

        Function to be evaluated: atelier.lumfun.lum_double_power_law()

        :param lum: Luminosity for evaluation
        :type lum: float or numpy.ndarray
        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param parameters: Dictionary of parameters used for this specific
            calculation. This does not replace the parameters with which the
            luminosity function was initialized. (default=None)
        :type parameters: dict(atelier.lumfun.Parameters)
        :return: Luminosity function value
        :rtype: (numpy.ndarray,numpy.ndarray)
        """

        if parameters is None:
            parameters = self.parameters.copy()

        main_parameter_values = self.evaluate_main_parameters(lum, redsh,
                                                        parameters=parameters)

        phi_star = main_parameter_values['phi_star']
        lum_star = main_parameter_values['lum_star']
        # convert to erg/s
        lum_star = lum_star * const.L_sun.to(units.erg/units.s).value

        alpha = main_parameter_values['alpha']
        beta = main_parameter_values['beta']

        return lum_double_power_law(np.power(10, lum), phi_star, lum_star,
                                              alpha, beta)


class Hopkins2007QLF(DoublePowerLawLF):
    """Implementation of the bolometric quasar luminosity function of
    Hopkins+2007.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2007ApJ...654..731H/abstract

    The luminosity function is described by Equations 6, 9, 10, 17, 19.
    The values for the best fit model adopted here are found in Table 3 in
    the row named "Full".

    """

    def __init__(self):
        """Initialize the Hopkins+2007 bolometric quasar luminosity function.
        """

        # OLD properties to maybe be incorporated in Luminosity Function model
        # self.name = "Hopkins2007"
        # self.band = "bolometric"
        # self.band_wavelength = None  # in nm
        # self.type = 1  # 0 = magnitudes, 1 = luminosity double power law
        #
        # self.z_min = 0  # lower redshift limit of data for the QLF fit
        # self.z_max = 4.5  # upper redshift limit of data for the QLF fit
        #
        # self.x_max = 18  # log(L_bol)
        # self.x_min = 8  # log(L_bol)
        #
        # self.x = 12  # default magnitude value
        # self.z = 1.0  # default redshift value

        # best fit values Table 7
        log_phi_star = Parameter(-4.825, 'log_phi_star', one_sigma_unc=[0.06,
                                                                        0.06])
        log_lum_star = Parameter(13.036, 'log_lum_star', one_sigma_unc=[
            0.043, 0.043])
        gamma_one = Parameter(0.417, 'gamma_one', one_sigma_unc=[0.055, 0.055])
        gamma_two = Parameter(2.174, 'gamma_two', one_sigma_unc=[0.055, 0.055])

        kl1 = Parameter(0.632, 'kl1', one_sigma_unc=[0.077, 0.077])
        kl2 = Parameter(-11.76, 'kl2', one_sigma_unc=[0.38, 0.38])
        kl3 = Parameter(-14.25, 'kl2', one_sigma_unc=[0.8, 0.8])

        kg1 = Parameter(-0.623, 'kg1', one_sigma_unc=[0.132, 0.132])
        kg2_1 = Parameter(1.46, 'kg2_1', one_sigma_unc=[0.096, 0.096])
        kg2_2 = Parameter(-0.793, 'kg2_2', one_sigma_unc=[0.057, 0.057])

        z_ref = Parameter(2.0, 'z_ref', vary=False)

        parameters = {'log_phi_star': log_phi_star,
                      'log_lum_star': log_lum_star,
                      'gamma_one': gamma_one,
                      'gamma_two': gamma_two,
                      'kl1': kl1,
                      'kl2': kl2,
                      'kl3': kl3,
                      'kg1': kg1,
                      'kg2_1': kg2_1,
                      'kg2_2': kg2_2,
                      'z_ref': z_ref}

        param_functions = {'lum_star': self.lum_star,
                           'phi_star': self.phi_star,
                           'alpha': self.alpha,
                           'beta': self.beta}

        lum_type = 'bolometric'

        super(Hopkins2007QLF, self).__init__(parameters, param_functions,
                                             lum_type=lum_type)

    @staticmethod
    def lum_star(redsh, z_ref, log_lum_star, kl1, kl2, kl3):
        """Calculate the redshift dependent break luminosity (Eq. 9, 10)

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param z_ref: Reference redshift
        :type z_ref: float
        :param log_lum_star: Logarithmic break magnitude at z_ref
        :type log_lum_star: float
        :param kl1: Function parameter kl1
        :type kl1: float
        :param kl2: Function parameter kl2
        :type kl2: float
        :param kl3: Function parameter kl3
        :type kl3: float
        :return: Redshift dependent break luminosity
        :rtype: float
        """

        # Equation 10
        xi = np.log10((1 + redsh) / (1 + z_ref))

        # Equation 9
        log_lum_star = log_lum_star + kl1 * xi + kl2 * xi ** 2 + kl3 * xi ** 3

        lum_star = pow(10, log_lum_star)

        return lum_star

    @staticmethod
    def phi_star(log_phi_star):
        """ Calculate the break luminosity number density

        :param log_phi_star: Logarithmic break luminosity number density
        :return:
        """
        return pow(10, log_phi_star)

    @staticmethod
    def alpha(redsh, z_ref, gamma_one, kg1):
        """Calculate the redshift dependent luminosity function slope alpha.

        Equations 10, 17

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param z_ref: Reference redshift
        :type z_ref: float
        :param gamma_one: Luminosity function power law slope at z_ref
        :type gamma_one: float
        :param kg1: Evolutionary parameter
        :type kg1: float
        :return:
        """
        # Equation 10
        xi = np.log10((1 + redsh) / (1 + z_ref))

        # Equation 17
        alpha = gamma_one * pow(10, kg1 * xi)

        return alpha

    @staticmethod
    def beta(redsh, z_ref, gamma_two, kg2_1, kg2_2):
        """Calculate the redshift dependent luminosity function slope beta.

        Equations 10, 19 and text on page 744 (bottom right column)

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param z_ref: Reference redshift
        :type z_ref: float
        :param gamma_two: Luminosity function power law slope at z_ref
        :type gamma_two: float
        :param kg2_1: Evolutionary parameter
        :type kg2_1: float
        :param kg2_2: Evolutionary parameter
        :type kg2_2: float
        :return:
        """

        # Equation 10
        xi = np.log10((1 + redsh) / (1 + z_ref))

        # Equation 19
        beta = gamma_two * 2 /  (pow(10, kg2_1 * xi) +
                                      ( pow(10,kg2_2 *  xi)))

        # note pg. 744 right column bottom
        if (beta < 1.3) & (redsh > 5.0):
            beta = 1.3

        return beta

    def evaluate(self, lum, redsh, parameters=None):
        """Evaluate the Hopkins+2007 bolometric luminosity function.

        Function to be evaluated: atelier.lumfun.lum_double_power_law()

        :param lum: Luminosity for evaluation
        :type lum: float or numpy.ndarray
        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param parameters: Dictionary of parameters used for this specific
            calculation. This does not replace the parameters with which the
            luminosity function was initialized. (default=None)
        :type parameters: dict(atelier.lumfun.Parameters)
        :return: Luminosity function value
        :rtype: (numpy.ndarray,numpy.ndarray)
        """

        if parameters is None:
            parameters = self.parameters.copy()

        main_parameter_values = self.evaluate_main_parameters(lum, redsh,
                                                        parameters=parameters)

        phi_star = main_parameter_values['phi_star']
        lum_star = main_parameter_values['lum_star']
        alpha = main_parameter_values['alpha']
        beta = main_parameter_values['beta']

        return lum_double_power_law(np.power(10, lum), phi_star, lum_star,
                                              alpha, beta)


class McGreer2018QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    McGreer+2018 at z~5 (z=4.9).

    ADS reference: https://ui.adsabs.harvard.edu/abs/2018AJ....155..131M/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    This implementation adopts the best maximum likelihood estimate fit from
    the second column in Table 2.


    """

    def __init__(self, cosmology=None):
        """ Initialize the McGreer+2018 type-I quasar UV luminosity function.
        """

        # best MLE fit values Table 2 second column
        log_phi_star_z6 = Parameter(-8.97, 'log_phi_star_z6',
                                    one_sigma_unc=[0.18, 0.15])
        lum_star = Parameter(-27.47, 'lum_star',
                             one_sigma_unc=[0.26, 0.22])
        alpha = Parameter(-1.97, 'alpha', one_sigma_unc=[0.09, 0.09])
        beta = Parameter(-4.0, 'beta', one_sigma_unc=None)

        k = Parameter(-0.47, 'k')

        z_ref = Parameter(6, 'z_ref')

        parameters = {'log_phi_star_z6': log_phi_star_z6,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta,
                      'k': k,
                      'z_ref': z_ref}

        param_functions = {'phi_star': self.phi_star}

        lum_type = 'M1450'

        # Hinshaw+2013
        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.272)
        ref_redsh = 5.0

        super(McGreer2018QLF, self).__init__(parameters, param_functions,
                                             lum_type=lum_type,
                                             cosmology=cosmology,
                                             ref_cosmology=ref_cosmology,
                                             ref_redsh=ref_redsh)


    @staticmethod
    def phi_star(redsh, log_phi_star_z6, k, z_ref):
        """Calculate the redshift dependent luminosity function normalization.

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param log_phi_star_z6: Logarithmic source density at z=6
        :type log_phi_star_z6: float
        :param k: Power law exponent of density evolution
        :type k: float
        :param z_ref: Reference redshift
        :type z_ref: float
        :return:
        """

        log_phi_star = log_phi_star_z6 + k * (redsh-z_ref)

        return pow(10, log_phi_star)


class Willott2010QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    McGreer+2018 at z~5 (z=4.9).

    ADS reference: https://ui.adsabs.harvard.edu/abs/2018AJ....155..131M/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    This implementation adopts the best maximum likelihood estimate fit from
    the second column in Table 2.


    """

    def __init__(self, cosmology=None):
        """ Initialize the McGreer+2018 type-I quasar UV luminosity function.
        """

        # best MLE fit values Table 2 second column
        phi_star_z6 = Parameter(1.14e-8, 'phi_star_z6')
        lum_star = Parameter(-25.13, 'lum_star',)
        alpha = Parameter(-1.5, 'alpha')
        beta = Parameter(-2.81, 'beta', one_sigma_unc=None)

        k = Parameter(-0.47, 'k')

        z_ref = Parameter(6, 'z_ref')

        parameters = {'phi_star_z6': phi_star_z6,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta,
                      'k': k,
                      'z_ref': z_ref}

        param_functions = {'phi_star': self.phi_star}

        lum_type = 'M1450'

        # Komatsu+2009
        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.28)
        ref_redsh = 6.0

        super(Willott2010QLF, self).__init__(parameters, param_functions,
                                             lum_type=lum_type,
                                             cosmology=cosmology,
                                             ref_cosmology=ref_cosmology,
                                             ref_redsh=ref_redsh)


    @staticmethod
    def phi_star(redsh, phi_star_z6, k, z_ref):
        """Calculate the redshift dependent luminosity function normalization.

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param log_phi_star_z6: Logarithmic source density at z=6
        :type log_phi_star_z6: float
        :param k: Power law exponent of density evolution
        :type k: float
        :param z_ref: Reference redshift
        :type z_ref: float
        :return:
        """

        log_phi_star = phi_star_z6 * 10**(k * (redsh-z_ref))

        return pow(10, log_phi_star)


class WangFeige2019SPLQLF(SinglePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Wang+2019 at z~6.7.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2019ApJ...884...30W/abstract

    The luminosity function is parameterized as a single power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    This implementation adopts the single power law fit described in Section 5.5
    """

    def __init__(self, cosmology=None):

        phi_star = Parameter(6.34e-10, 'phi_star', one_sigma_unc=[1.73e-10,
                                                                  1.73e-10])
        alpha = Parameter(-2.35, 'alpha', one_sigma_unc=[0.22, 0.22])

        lum_ref = Parameter(-26, 'lum_ref')


        parameters = {'phi_star': phi_star,
                      'alpha': alpha,
                      'lum_ref': lum_ref}

        param_functions = {}

        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 6.7

        super(WangFeige2019SPLQLF, self).__init__(parameters, param_functions,
                                                  lum_type=lum_type,
                                                  ref_cosmology=ref_cosmology,
                                                  cosmology = cosmology,
                                                  ref_redsh=ref_redsh)


class Matsuoka2023DPLQLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Wang+2019 at z~6.7.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2019ApJ...884...30W/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    This implementation adopts the double power law fit described in Section 5.5
    """

    def __init__(self, cosmology=None):
        """Initialize the Wang+2019 type-I quasar UV luminosity function.

        """

        phi_star_z7 = Parameter(1.35e-9, 'phi_star_z6p7', one_sigma_unc=None)
        lum_star = Parameter(-25.6, 'lum_star', one_sigma_unc=None)

        alpha = Parameter(-1.2, 'gamma_one', one_sigma_unc=None)
        beta = Parameter(-3.34, 'gamma_two', one_sigma_unc=None)

        k = Parameter(-0.78, 'k')

        z_ref = Parameter(7., 'z_ref')

        parameters = {'phi_star_z7': phi_star_z7,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta,
                      'k': k,
                      'z_ref': z_ref}

        param_functions = {'phi_star': self.phi_star}

        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 7.

        super(Matsuoka2023DPLQLF, self).__init__(parameters, param_functions,
                                                  lum_type=lum_type,
                                                  ref_cosmology=ref_cosmology,
                                                  ref_redsh=ref_redsh,
                                                  cosmology=cosmology)


    @staticmethod
    def phi_star(redsh, phi_star_z7, k, z_ref):
        """Calculate the redshift dependent luminosity function normalization.

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param phi_star_z7: Logarithmic source density at z=7
        :type phi_star_z7: float
        :param k: Power law exponent of density evolution
        :type k: float
        :param z_ref: Reference redshift
        :type z_ref: float
        :return:
        """

        return phi_star_z7 * 10**(k * (redsh - z_ref))


class WangFeige2019DPLQLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Wang+2019 at z~6.7.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2019ApJ...884...30W/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    This implementation adopts the double power law fit described in Section 5.5
    """

    def __init__(self, cosmology=None):
        """Initialize the Wang+2019 type-I quasar UV luminosity function.

        """

        phi_star_z6p7 = Parameter(3.17e-9, 'phi_star_z6p7',
                                one_sigma_unc=[0.85e-9, 0.85e-9])
        lum_star = Parameter(-25.2, 'lum_star', one_sigma_unc=None)

        alpha = Parameter(-1.9, 'gamma_one', one_sigma_unc=None)
        beta = Parameter(-2.54, 'gamma_two', one_sigma_unc=[0.29, 0.29])

        k = Parameter(-0.78, 'k')

        z_ref = Parameter(6.7, 'z_ref')

        parameters = {'phi_star_z6p7': phi_star_z6p7,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta,
                      'k': k,
                      'z_ref': z_ref}

        param_functions = {'phi_star': self.phi_star}

        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 6.7

        super(WangFeige2019DPLQLF, self).__init__(parameters, param_functions,
                                                  lum_type=lum_type,
                                                  ref_cosmology=ref_cosmology,
                                                  ref_redsh=ref_redsh,
                                                  cosmology=cosmology)


    @staticmethod
    def phi_star(redsh, phi_star_z6p7, k, z_ref):
        """Calculate the redshift dependent luminosity function normalization.

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param phi_star_z6p7: Logarithmic source density at z=6
        :type phi_star_z6p7: float
        :param k: Power law exponent of density evolution
        :type k: float
        :param z_ref: Reference redshift
        :type z_ref: float
        :return:
        """

        return phi_star_z6p7 * 10**(k * (redsh - z_ref))


class JiangLinhua2016QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Jiang+2016 at z~6.

    ADS reference:

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    This implementation adopts the double power law fit described in Section 4.5
    """

    def __init__(self, cosmology=None):
        """Initialize the Jiang+2016 type-I quasar UV luminosity function.
        """

        phi_star_z6 = Parameter(9.93e-9, 'phi_star_z6', one_sigma_unc=[])

        lum_star = Parameter(-25.2, 'lum_star', one_sigma_unc=[3.8, 1.2])

        alpha = Parameter(-1.9, 'alpha', one_sigma_unc=[0.58, 0.44])

        beta = Parameter(-2.8, 'beta', one_sigma_unc=None)

        k = Parameter(-0.72, 'k')

        z_ref = Parameter(6, 'z_ref')

        parameters = {'phi_star_z6': phi_star_z6,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta,
                      'k': k,
                      'z_ref': z_ref}

        param_functions = {'phi_star': self.phi_star}

        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 6.05

        super(JiangLinhua2016QLF, self).__init__(parameters, param_functions,
                                                 lum_type=lum_type,
                                                 ref_cosmology=ref_cosmology,
                                                 ref_redsh=ref_redsh,
                                                 cosmology=cosmology)

    @staticmethod
    def phi_star(redsh, phi_star_z6, k, z_ref):
        """Calculate the redshift dependent luminosity function normalization.

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param phi_star_z6: Logarithmic source density at z=6
        :type phi_star_z6: float
        :param k: Power law exponent of density evolution
        :type k: float
        :param z_ref: Reference redshift
        :type z_ref: float
        :return:
        """

        return phi_star_z6 * 10**(k * (redsh - z_ref))


class Akiyama2018QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Akiyama+2018 at z~4.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2018ApJ...869..150M/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    This implementation adopts the double power law fit presented in Table 5
    ("Maximum Likelihood").
    """

    def __init__(self, cosmology=None):
        """Initialize the Akiyama+2018 type-I quasar UV luminosity function.
        """

        # ML fit parameters from the "standard" model in Table 5
        phi_star = Parameter(2.66e-7, 'phi_star',
                             one_sigma_unc=[0.05e-7, 0.05e-7])

        lum_star = Parameter(-25.37, 'lum_star', one_sigma_unc=[0.13, 0.13])

        alpha = Parameter(-1.30, 'alpha', one_sigma_unc=[0.05, 0.05])

        beta = Parameter(-3.11, 'beta', one_sigma_unc=[0.07, 0.07])


        parameters = {'phi_star': phi_star,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta}

        param_functions = {}

        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 4.0

        super(Akiyama2018QLF, self).__init__(parameters, param_functions,
                                              lum_type=lum_type,
                                              ref_cosmology=ref_cosmology,
                                              ref_redsh=ref_redsh,
                                              cosmology=cosmology)

class Matsuoka2018QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Matsuoka+2018 at z~6.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2018ApJ...869..150M/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    This implementation adopts the double power law fit presented in Table 5
    ("standard").
    """

    def __init__(self, cosmology=None):
        """Initialize the Matsuoka+2018 type-I quasar UV luminosity function.
        """


        # ML fit parameters from the "standard" model in Table 5
        phi_star_z6 = Parameter(10.9e-9, 'phi_star_z6', one_sigma_unc=[6.8e-9,
                                                                       10e-9])

        lum_star = Parameter(-24.9, 'lum_star', one_sigma_unc=[0.9, 0.75])

        alpha = Parameter(-1.23, 'alpha', one_sigma_unc=[0.34, 0.44])

        beta = Parameter(-2.73, 'beta', one_sigma_unc=[0.31, 0.23])

        k = Parameter(-0.7, 'k')

        z_ref = Parameter(6, 'z_ref')

        parameters = {'phi_star_z6': phi_star_z6,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta,
                      'k': k,
                      'z_ref': z_ref}

        param_functions = {'phi_star': self.phi_star}

        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 6.1

        super(Matsuoka2018QLF, self).__init__(parameters, param_functions,
                                                 lum_type=lum_type,
                                                 ref_cosmology=ref_cosmology,
                                                 ref_redsh=ref_redsh,
                                                 cosmology=cosmology)

    @staticmethod
    def phi_star(redsh, phi_star_z6, k, z_ref):
        """Calculate the redshift dependent luminosity function normalization.

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param phi_star_z6: Logarithmic source density at z=6
        :type phi_star_z6: float
        :param k: Power law exponent of density evolution
        :type k: float
        :param z_ref: Reference redshift
        :type z_ref: float
        :return:
        """

        return phi_star_z6 * 10**(k * (redsh - z_ref))



class Schindler2023QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Schindler+2023 at z~6.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2023ApJ...943...67S/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    This implementation adopts the double power law fit presented in Table 4
    (first row).
    """

    def __init__(self, cosmology=None):
        """Initialize the Schindler+2023 type-I quasar UV luminosity function.
        """


        # ML fit parameters from the "standard" model in Table 5
        log_phi_star_z6 = Parameter(-8.75, 'log_phi_star_z6')

        lum_star = Parameter(-26.38, 'lum_star', one_sigma_unc=[0.60, 0.79])

        alpha = Parameter(-1.70, 'alpha', one_sigma_unc=[0.19, 0.29])

        beta = Parameter(-3.84, 'beta', one_sigma_unc=[1.21, 0.63])

        k = Parameter(-0.7, 'k')

        z_ref = Parameter(6, 'z_ref')

        parameters = {'log_phi_star_z6': log_phi_star_z6,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta,
                      'k': k,
                      'z_ref': z_ref}

        param_functions = {'phi_star': self.phi_star}

        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 6.0

        super(Schindler2023QLF, self).__init__(parameters, param_functions,
                                                 lum_type=lum_type,
                                                 ref_cosmology=ref_cosmology,
                                                 ref_redsh=ref_redsh,
                                                 cosmology=cosmology)

    @staticmethod
    def phi_star(redsh, log_phi_star_z6, k, z_ref):
        """Calculate the redshift dependent luminosity function normalization.

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param phi_star_z6: Logarithmic source density at z=6
        :type phi_star_z6: float
        :param k: Power law exponent of density evolution
        :type k: float
        :param z_ref: Reference redshift
        :type z_ref: float
        :return:
        """

        phi_star_z6 = 10**(log_phi_star_z6)

        return phi_star_z6 * 10**(k * (redsh - z_ref))


class Matsuoka2023QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Matsuoka+2023 at z~7.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2023arXiv230511225M/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    This implementation adopts the double power law fit presented in Table 7
    (standard model).
    """

    def __init__(self, cosmology=None):
        """Initialize the Matsuoka+2023 type-I quasar UV luminosity function.
        """


        # ML fit parameters from the "standard" model in Table 5
        phi_star_z7 = Parameter(1.35E-9, 'phi_star_z7', one_sigma_unc=[
            0.3E-9, 0.47E-9])

        lum_star = Parameter(-25.60, 'lum_star', one_sigma_unc=[0.30, 0.40])

        alpha = Parameter(-1.20, 'alpha')

        beta = Parameter(-3.34, 'beta', one_sigma_unc=[0.57, 0.49])

        k = Parameter(-0.78, 'k')

        z_ref = Parameter(7, 'z_ref')

        parameters = {'phi_star_z7': phi_star_z7,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta,
                      'k': k,
                      'z_ref': z_ref}

        param_functions = {'phi_star': self.phi_star}

        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 7.0

        super(Matsuoka2023QLF, self).__init__(parameters, param_functions,
                                                 lum_type=lum_type,
                                                 ref_cosmology=ref_cosmology,
                                                 ref_redsh=ref_redsh,
                                                 cosmology=cosmology)

    @staticmethod
    def phi_star(redsh, phi_star_z7, k, z_ref):
        """Calculate the redshift dependent luminosity function normalization.

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param phi_star_z7: Source density at z=6
        :type phi_star_z7: float
        :param k: Power law exponent of density evolution
        :type k: float
        :param z_ref: Reference redshift
        :type z_ref: float
        :return:
        """

        return phi_star_z7 * 10**(k * (redsh - z_ref))


class Willott2010QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Willott+2010 at z~6.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2010AJ....139..906W/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    This implementation adopts the double power law fit presented in Section
    5.2.
    """


    def __init__(self, cosmology=None):
        """Initialize the Willott+2010 type-I quasar UV luminosity function.
        """

        # ML fit parameters from Section 5.1
        phi_star_z6 = Parameter(1.14e-8, 'phi_star_z6')

        lum_star = Parameter(-25.13, 'lum_star')

        alpha = Parameter(-1.5, 'alpha')

        beta = Parameter(-2.81, 'beta')

        k = Parameter(-0.47, 'k')

        z_ref = Parameter(6, 'z_ref')

        parameters = {'phi_star_z6': phi_star_z6,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta,
                      'k': k,
                      'z_ref': z_ref}

        param_functions = {'phi_star': self.phi_star}

        lum_type = 'M1450'

        # Komatsu+2009
        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.28)
        ref_redsh = 6.0

        super(Willott2010QLF, self).__init__(parameters, param_functions,
                                                     lum_type=lum_type,
                                                     ref_cosmology=ref_cosmology,
                                                     ref_redsh=ref_redsh,
                                                     cosmology=cosmology)

    @staticmethod
    def phi_star(redsh, phi_star_z6, k, z_ref):
        """Calculate the redshift dependent luminosity function normalization.

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param phi_star_z6: Logarithmic source density at z=6
        :type phi_star_z6: float
        :param k: Power law exponent of density evolution
        :type k: float
        :param z_ref: Reference redshift
        :type z_ref: float
        :return:
        """

        return phi_star_z6 * 10**(k * (redsh - z_ref))




class YangJinyi2016QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Yang+2016 at z~5.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2016ApJ...829...33Y/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    The maximum likelihood fit in Yang+2016 includes the quasar samples of
    McGreer+2013 at fainter magnitudes (i.e., the SDSS DR7 and Stripe 82
    samples).

    This implementation adopts the double power law fit presented in Section
    5.2.
    """


    def __init__(self, cosmology=None):
        """Initialize the Willott+2010 type-I quasar UV luminosity function.
        """

        # ML fit parameters from Section 5.1
        log_phi_star_z6 = Parameter(-8.82, 'phi_star_z6', one_sigma_unc=[
            0.15, 0.15])

        lum_star = Parameter(-26.98, 'lum_star', one_sigma_unc=[0.23, 0.23])

        alpha = Parameter(-2.03, 'alpha') # motivated by McGreer+2013

        beta = Parameter(-3.58, 'beta', one_sigma_unc=[0.24, 0.24])

        k = Parameter(-0.47, 'k') # motivated by Fan+2001

        z_ref = Parameter(6, 'z_ref')

        parameters = {'log_phi_star_z6': log_phi_star_z6,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta,
                      'k': k,
                      'z_ref': z_ref}

        param_functions = {'phi_star': self.phi_star}

        lum_type = 'M1450'

        # Komatsu+2009
        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.272, Ob0=0.0456)
        ref_redsh = 5.05

        super(YangJinyi2016QLF, self).__init__(parameters, param_functions,
                                                     lum_type=lum_type,
                                                     ref_cosmology=ref_cosmology,
                                                     ref_redsh=ref_redsh,
                                                     cosmology=cosmology)

    @staticmethod
    def phi_star(redsh, log_phi_star_z6, k, z_ref):
        """Calculate the redshift dependent luminosity function normalization.

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param phi_star_z6: Logarithmic source density at z=6
        :type phi_star_z6: float
        :param k: Power law exponent of density evolution
        :type k: float
        :param z_ref: Reference redshift
        :type z_ref: float
        :return:
        """

        return 10**log_phi_star_z6 * 10**(k * (redsh - z_ref))


class Schindler2019_LEDE_QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Schindler+2019 with LEDE evolution.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2019ApJ...871..258S/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    The LEDE model was fit to a range of binned QLF measurements using
    chi-squared minimzation.

    This implementation adopts the LEDE double power law fit presented in
    Table 8.
    """


    def __init__(self, cosmology=None):
        """Initialize the Schindler+2019 type-I quasar UV luminosity function.
        """

        # ML fit parameters from Table 7
        log_phi_star_z2p2 = Parameter(-6.11, 'log_phi_star_z2p2',
                                  one_sigma_unc=[0.05,
                                                 0.05]
                                  )

        lum_star_z2p2 = Parameter(-26.09, 'lum_star_z2p2',
                                  one_sigma_unc=[0.05, 0.05])

        alpha = Parameter(-1.55, 'alpha', one_sigma_unc=[0.02, 0.02])

        beta = Parameter(-3.65, 'beta', one_sigma_unc=[0.06, 0.06])

        c1 = Parameter(-0.61, 'c1', one_sigma_unc=[0.02, 0.02])

        c2 = Parameter(-0.1, 'c2', one_sigma_unc=[0.03, 0.03])


        parameters = {'log_phi_star_z2p2': log_phi_star_z2p2,
                      'lum_star_z2p2': lum_star_z2p2,
                      'alpha': alpha,
                      'beta': beta,
                      'c1': c1,
                      'c2': c2}

        param_functions = {'phi_star': self.phi_star,
                           'lum_star': self.lum_star}


        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 2.9

        super(Schindler2019_LEDE_QLF, self).__init__(parameters, param_functions,
                                                     lum_type=lum_type,
                                                     ref_cosmology=ref_cosmology,
                                                     ref_redsh=ref_redsh,
                                                     cosmology=cosmology)

    @staticmethod
    def phi_star(redsh,log_phi_star_z2p2, c1):
        """Calculate the redshift dependent luminosity function normalization.

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param log_phi_star_z2p2: Logarithmic source density at z=2.2
        :type log_phi_star_z2p2: float
        :param c1: Redshift evolution parameter
        :type c1: float
        :return:
        """

        return 10**(log_phi_star_z2p2 + c1 * (redsh-2.2))

    @staticmethod
    def lum_star(redsh, lum_star_z2p2, c2):
        """Calculate the redshift dependent break magnitude.

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param lum_star_z2p2: Break magnitude at z=2.2
        :type lum_star_z2p2: float
        :param c2: Redshift evolution parameter
        :type c2: float
        :return:
        """

        return lum_star_z2p2 + c2 * (redsh-2.2)


class Schindler2019_4p25_QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Schindler+2019 at z~4.25.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2019ApJ...871..258S/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    The maximum likelihood fit in Schindler+2019 includes the quasar sample of
    Richards+2096 at fainter magnitudes.

    This implementation adopts the double power law fit presented in Table 7.
    """


    def __init__(self, cosmology=None):
        """Initialize the Schindler+2019 type-I quasar UV luminosity function.
        """

        # ML fit parameters from Table 7
        phi_star = Parameter(10**(-8.16), 'phi_star',
                             one_sigma_unc=[3.96*1E-9, 3.96*1E-9])

        lum_star = Parameter(-27.57, 'lum_star', one_sigma_unc=[0.24, 0.24])

        alpha = Parameter(-1.65, 'alpha', one_sigma_unc=[0.46, 0.46])

        beta = Parameter(-4.5, 'beta', one_sigma_unc=[0.18, 0.18])


        parameters = {'phi_star': phi_star,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta}

        param_functions = {}


        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 4.25

        super(Schindler2019_4p25_QLF, self).__init__(parameters,
                                                     param_functions,
                                                     lum_type=lum_type,
                                                     ref_cosmology=ref_cosmology,
                                                     ref_redsh=ref_redsh,
                                                     cosmology=cosmology)

class Schindler2019_3p75_QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Schindler+2019 at z~3.75.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2019ApJ...871..258S/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    The maximum likelihood fit in Schindler+2019 includes the quasar sample of
    Richards+2096 at fainter magnitudes.

    This implementation adopts the double power law fit presented in Table 7.
    """


    def __init__(self, cosmology=None):
        """Initialize the Schindler+2019 type-I quasar UV luminosity function.
        """

        # ML fit parameters from Table 7
        phi_star = Parameter(10**(-7.65), 'phi_star',
                             one_sigma_unc=[15.51*1E-9, 15.51*1E-9])

        lum_star = Parameter(-27.17, 'lum_star', one_sigma_unc=[0.28, 0.28])

        alpha = Parameter(-1.7, 'alpha', one_sigma_unc=[0.66, 0.66])

        beta = Parameter(-4.52, 'beta', one_sigma_unc=[0.15, 0.15])


        parameters = {'phi_star': phi_star,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta}

        param_functions = {}


        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 3.75

        super(Schindler2019_3p75_QLF, self).__init__(parameters,
                                                     param_functions,
                                                     lum_type=lum_type,
                                                     ref_cosmology=ref_cosmology,
                                                     ref_redsh=ref_redsh,
                                                     cosmology=cosmology)

class Schindler2019_3p25_QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Schindler+2019 at z~3.25.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2019ApJ...871..258S/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    The maximum likelihood fit in Schindler+2019 includes the quasar sample of
    Ross+2013 at fainter magnitudes.

    This implementation adopts the double power law fit presented in Table 7.
    """


    def __init__(self, cosmology=None):
        """Initialize the Schindler+2019 type-I quasar UV luminosity function.
        """

        # ML fit parameters from Table 7
        phi_star = Parameter(10**(-7.33), 'phi_star',
                             one_sigma_unc=[22.07*1E-9, 22.07*1E-9])

        lum_star = Parameter(-27.13, 'lum_star', one_sigma_unc=[0.21, 0.21])

        alpha = Parameter(-1.92, 'alpha', one_sigma_unc=[0.16, 0.16])

        beta = Parameter(-4.58, 'beta', one_sigma_unc=[0.18, 0.18])


        parameters = {'phi_star': phi_star,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta}

        param_functions = {}


        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 3.25

        super(Schindler2019_3p25_QLF, self).__init__(parameters, param_functions,
                                                     lum_type=lum_type,
                                                     ref_cosmology=ref_cosmology,
                                                     ref_redsh=ref_redsh,
                                                     cosmology=cosmology)

class Schindler2019_2p9_QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Schindler+2019 at z~2.9.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2019ApJ...871..258S/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    The maximum likelihood fit in Schindler+2019 includes the quasar sample of
    Ross+2013 at fainter magnitudes.

    This implementation adopts the double power law fit presented in Table 7.
    """


    def __init__(self, cosmology=None):
        """Initialize the Schindler+2019 type-I quasar UV luminosity function.
        """

        # ML fit parameters from Table 7
        phi_star = Parameter(10**(-6.23), 'phi_star',
                             one_sigma_unc=[185.93*1E-9, 185.93*1E-9])

        lum_star = Parameter(-25.58, 'lum_star', one_sigma_unc=[0.22, 0.22])

        alpha = Parameter(-1.27, 'alpha', one_sigma_unc=[0.2, 0.2])

        beta = Parameter(-3.44, 'beta', one_sigma_unc=[0.07, 0.07])


        parameters = {'phi_star': phi_star,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta}

        param_functions = {}


        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 2.9

        super(Schindler2019_2p9_QLF, self).__init__(parameters, param_functions,
                                                     lum_type=lum_type,
                                                     ref_cosmology=ref_cosmology,
                                                     ref_redsh=ref_redsh,
                                                     cosmology=cosmology)



class PanZhiwei2022_3p8_QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Zhiwei Pan+2022 at z~3.8.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2022ApJ...928..172P/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.


    This implementation adopts the double power law fit presented in Table 5
    denoted as (O+S+L) "Best fit".
    """


    def __init__(self, cosmology=None):
        """Initialize the PanZhiwei+2022 type-I quasar UV luminosity function.
        """

        # Fit parameters from Table 5
        log_phi_star = Parameter(-7.2, 'log_phi_star',
                             one_sigma_unc=[0.2, 0.2])

        lum_star = Parameter(-26.7, 'lum_star', one_sigma_unc=[0.2, 0.3])

        alpha = Parameter(-1.7, 'alpha', one_sigma_unc=[0.1, 0.2])

        beta = Parameter(-4.0, 'beta', one_sigma_unc=[0.2, 0.2])


        parameters = {'log_phi_star': log_phi_star,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta}

        param_functions = {'phi_star': self.phi_star}


        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 3.8

        super(PanZhiwei2022_3p8_QLF, self).__init__(parameters, param_functions,
                                                     lum_type=lum_type,
                                                     ref_cosmology=ref_cosmology,
                                                     ref_redsh=ref_redsh,
                                                     cosmology=cosmology)

    @staticmethod
    def phi_star(redsh, log_phi_star):
        """Calculate the redshift dependent luminosity function normalization.

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param log_phi_star: Logarithmic source density at z=6
        :type log_phi_star: float
        :return:
        """

        return 10 ** log_phi_star


class PanZhiwei2022_4p25_QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Zhiwei Pan+2022 at z~4.25.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2022ApJ...928..172P/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.


    This implementation adopts the double power law fit presented in Table 5
    denoted as (O+S+L) "Best fit".
    """


    def __init__(self, cosmology=None):
        """Initialize the PanZhiwei+2022 type-I quasar UV luminosity function.
        """

        # Fit parameters from Table 5
        log_phi_star = Parameter(-7.6, 'log_phi_star',
                             one_sigma_unc=[0.4, 0.3])

        lum_star = Parameter(-26.6, 'lum_star', one_sigma_unc=[0.5, 0.5])

        alpha = Parameter(-1.6, 'alpha', one_sigma_unc=[0.3, 0.4])

        beta = Parameter(-3.7, 'beta', one_sigma_unc=[0.4, 0.3])


        parameters = {'log_phi_star': log_phi_star,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta}

        param_functions = {'phi_star': self.phi_star}


        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 4.25

        super(PanZhiwei2022_4p25_QLF, self).__init__(parameters,
                                                    param_functions,
                                                     lum_type=lum_type,
                                                     ref_cosmology=ref_cosmology,
                                                     ref_redsh=ref_redsh,
                                                     cosmology=cosmology)

    @staticmethod
    def phi_star(redsh, log_phi_star):
        """Calculate the redshift dependent luminosity function normalization.

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param log_phi_star: Logarithmic source density at z=6
        :type log_phi_star: float
        :return:
        """

        return 10 ** log_phi_star



class PanZhiwei2022_4p7_QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Zhiwei Pan+2022 at z~4.7.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2022ApJ...928..172P/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.


    This implementation adopts the double power law fit presented in Table 5
    denoted as (O+S+L) "Best fit".
    """


    def __init__(self, cosmology=None):
        """Initialize the PanZhiwei+2022 type-I quasar UV luminosity function.
        """

        # Fit parameters from Table 5
        log_phi_star = Parameter(-8.0, 'log_phi_star',
                             one_sigma_unc=[0.5, 0.8])

        lum_star = Parameter(-26.7, 'lum_star', one_sigma_unc=[0.8, 1.5])

        alpha = Parameter(-1.8, 'alpha', one_sigma_unc=[0.2, 0.4])

        beta = Parameter(-3.5, 'beta', one_sigma_unc=[1.2, 0.7])


        parameters = {'log_phi_star': log_phi_star,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta}

        param_functions = {'phi_star': self.phi_star}


        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 4.7

        super(PanZhiwei2022_4p7_QLF, self).__init__(parameters,
                                                    param_functions,
                                                     lum_type=lum_type,
                                                     ref_cosmology=ref_cosmology,
                                                     ref_redsh=ref_redsh,
                                                     cosmology=cosmology)

    @staticmethod
    def phi_star(redsh, log_phi_star):
        """Calculate the redshift dependent luminosity function normalization.

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param log_phi_star: Logarithmic source density at z=6
        :type log_phi_star: float
        :return:
        """

        return 10 ** log_phi_star


class Onken2022_Niida_4p52_QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Onken+2022 at z~4.52.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2021arXiv210512215O/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    The maximum likelihood fit in Onken+2022 includes constraints of
    Niida+2020 at fainter magnitudes.

    This implementation adopts the double power law fit presented in Table 4.
    """


    def __init__(self, cosmology=None):
        """Initialize the Onken+2022 type-I quasar UV luminosity function.
        """

        # ML fit parameters from Table 7
        phi_star = Parameter(10**(-8.24), 'phi_star')

        lum_star = Parameter(-27.32, 'lum_star', one_sigma_unc=[0.13, 0.13])

        alpha = Parameter(-2.00, 'alpha')

        beta = Parameter(-3.92, 'beta', one_sigma_unc=[0.32, 0.32])


        parameters = {'phi_star': phi_star,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta}

        param_functions = {}


        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 4.52

        super(Onken2022_Niida_4p52_QLF, self).__init__(parameters, param_functions,
                                                     lum_type=lum_type,
                                                     ref_cosmology=ref_cosmology,
                                                     ref_redsh=ref_redsh,
                                                     cosmology=cosmology)


class Onken2022_Niida_4p83_QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Onken+2022 at z~4.83.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2021arXiv210512215O/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    The maximum likelihood fit in Onken+2022 includes constraints of
    Niida+2020 at fainter magnitudes.

    This implementation adopts the double power law fit presented in Table 4.
    """


    def __init__(self, cosmology=None):
        """Initialize the Onken+2022 type-I quasar UV luminosity function.
        """

        # ML fit parameters from Table 7
        phi_star = Parameter(10**(-8.32), 'phi_star')

        lum_star = Parameter(-27.09, 'lum_star', one_sigma_unc=[0.3, 0.3])

        alpha = Parameter(-2.00, 'alpha')

        beta = Parameter(-3.6, 'beta', one_sigma_unc=[0.37, 0.37])


        parameters = {'phi_star': phi_star,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta}

        param_functions = {}


        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 4.83

        super(Onken2022_Niida_4p83_QLF, self).__init__(parameters,
                                                      param_functions,
                                                     lum_type=lum_type,
                                                     ref_cosmology=ref_cosmology,
                                                     ref_redsh=ref_redsh,
                                                     cosmology=cosmology)


class Boutsia2021_QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Boutsia+2021 at z~3.9.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2021ApJ...912..111B/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    The fit in Boutsia+2021 includes QLF determinations of Fontanot+2007,
    Glikman+2011, Boutsia+2018, and Giallongo+2019 at fainter magnitudes.

    This implementation adopts the double power law fit presented in Table 4.
    """


    def __init__(self, cosmology=None):
        """Initialize the Boutsia+2021 type-I quasar UV luminosity function.
        """

        # ML fit parameters from Table 7
        phi_star = Parameter(10**(-6.85), 'phi_star',
                             one_sigma_unc=[0.45, 0.6])

        lum_star = Parameter(-26.5, 'lum_star', one_sigma_unc=[0.6, 0.85])

        alpha = Parameter(-1.85, 'alpha', one_sigma_unc=[0.25, 0.15])

        beta = Parameter(-4.025, 'beta', one_sigma_unc=[0.425, 0.575])


        parameters = {'phi_star': phi_star,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta}

        param_functions = {}


        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 3.9

        super(Boutsia2021_QLF, self).__init__(parameters,
                                                      param_functions,
                                                     lum_type=lum_type,
                                                     ref_cosmology=ref_cosmology,
                                                     ref_redsh=ref_redsh,
                                                     cosmology=cosmology)


class Kim2020_QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Kim+2020 at z~5.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2020ApJ...904..111K/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    The fit in Kim+2020 includes data from Yang+2016 at brighter luminosities.

    This implementation adopts the double power law fit presented in Table 6,
    Case 1.
    """

    def __init__(self, cosmology=None):
        """Initialize the Boutsia+2021 type-I quasar UV luminosity function.
        """

        # ML fit parameters from Table 7
        log_phi_star = Parameter(-7.36, 'log_phi_star',
                             one_sigma_unc=[0.81, 0.56])

        lum_star = Parameter(-25.78, 'lum_star', one_sigma_unc=[1.1, 1.35])

        alpha = Parameter(-1.21, 'alpha', one_sigma_unc=[0.64, 1.36])

        beta = Parameter(-3.44, 'beta', one_sigma_unc=[0.84, 0.66])


        parameters = {'log_phi_star': log_phi_star,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta}

        param_functions = {'phi_star': self.phi_star}


        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 5.0

        super(Kim2020_QLF, self).__init__(parameters,
                                          param_functions,
                                          lum_type=lum_type,
                                          ref_cosmology=ref_cosmology,
                                          ref_redsh=ref_redsh,
                                          cosmology=cosmology)


    @staticmethod
    def phi_star(redsh, log_phi_star):
        """

        :param redsh:
        :param log_phi_star:
        :return:
        """

        return 10**log_phi_star



class Niida2020_QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Niida+2020 at z~5.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2020ApJ...904...89N/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    The fit in Kim+2020 includes data from SDSS at brighter luminosities.

    This implementation adopts the double power law fit presented in Table 6,
    Case 1.
    """


    def __init__(self, cosmology=None):
        """Initialize the Boutsia+2021 type-I quasar UV luminosity function.
        """

        # ML fit parameters from Table 7
        phi_star = Parameter(1.01e-7, 'log_phi_star',
                             one_sigma_unc=[0.29e-7, 0.21e-7])

        lum_star = Parameter(-25.05, 'lum_star', one_sigma_unc=[0.24, 0.1])

        alpha = Parameter(-1.22, 'alpha', one_sigma_unc=[0.1, 0.03])

        beta = Parameter(-2.9, 'beta')


        parameters = {'phi_star': phi_star,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta}

        param_functions = {}


        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 5.0

        super(Niida2020_QLF, self).__init__(parameters,
                                                      param_functions,
                                                     lum_type=lum_type,
                                                     ref_cosmology=ref_cosmology,
                                                     ref_redsh=ref_redsh,
                                                     cosmology=cosmology)

class Giallongo2019_4p5_QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Giallongo+2019 at z~4.5.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2019ApJ...884...19G/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    The fit in Giallongo+2019 (model 1) includes QLF determinations of
    Fontanot+2007, Boutsia+2018, and Akiyama+2018 at brighter magnitudes.

    This implementation adopts the double power law fit presented in Table 3
    (model 1).
    """


    def __init__(self, cosmology=None):
        """Initialize the Giallongo+2019 type-I quasar UV luminosity function.
        """

        # ML fit parameters from Table 7
        phi_star = Parameter(10**(-6.68), 'phi_star')

        lum_star = Parameter(-25.81, 'lum_star')

        alpha = Parameter(-1.7, 'alpha')

        beta = Parameter(-3.71, 'beta')


        parameters = {'phi_star': phi_star,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta}

        param_functions = {}


        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 4.5

        super(Giallongo2019_4p5_QLF, self).__init__(parameters,
                                                      param_functions,
                                                     lum_type=lum_type,
                                                     ref_cosmology=ref_cosmology,
                                                     ref_redsh=ref_redsh,
                                                     cosmology=cosmology)

class Giallongo2019_5p6_QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Giallongo+2019 at z~5.6.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2019ApJ...884...19G/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    The fit in Giallongo+2019 (model 4) includes data from CANDELS and SDSS.

    This implementation adopts the double power law fit presented in Table 3
    (model 4).
    """


    def __init__(self, cosmology=None):
        """Initialize the Giallongo+2019 type-I quasar UV luminosity function.
        """

        # ML fit parameters from Table 7
        phi_star = Parameter(10**(-7.05), 'phi_star')

        lum_star = Parameter(-25.37, 'lum_star')

        alpha = Parameter(-1.74, 'alpha')

        beta = Parameter(-3.72, 'beta')


        parameters = {'phi_star': phi_star,
                      'lum_star': lum_star,
                      'alpha': alpha,
                      'beta': beta}

        param_functions = {}


        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 5.6

        super(Giallongo2019_5p6_QLF, self).__init__(parameters,
                                                      param_functions,
                                                     lum_type=lum_type,
                                                     ref_cosmology=ref_cosmology,
                                                     ref_redsh=ref_redsh,
                                                     cosmology=cosmology)


class Richards2006QLF(SinglePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
       Richards+2006 (z=1-5).

       ADS reference:

       The luminosity function is parameterized as a double power law with the
       luminosity variable in absolute magnitudes Mi(z=2. We convert the Mi(
       z=2) magnitudes to M1450 using a simple conversion factor (see
       Ross+2013).

       M1450(z=0) = Mi(z=2) + 1.486

       This implementation adopts the double power law fit presented in Table 7
       (variable power law).
       """


    def __init__(self, cosmology=None):
        """Initialize the Richards2006 type-I quasar UV luminosity function.
        """
        z_pivot = Parameter(2.4, 'z_pivot')
        a1_upp = Parameter(0.83, 'a1_upp', one_sigma_unc=0.01)
        a2_upp = Parameter(-0.11, 'a2_upp', one_sigma_unc=0.01)
        b1_upp = Parameter(1.43, 'b1_upp', one_sigma_unc=0.04)
        b2_upp = Parameter(36.63, 'b2_upp', one_sigma_unc=0.1)
        b3_upp = Parameter(34.39, 'b3_upp', one_sigma_unc=0.26)

        a1_low = Parameter(0.84, 'a1_low')
        a2_low = Parameter(0, 'a2_low')
        b1_low = Parameter(1.43, 'b1_low', one_sigma_unc=0.04)
        b2_low = Parameter(36.63, 'b2_low', one_sigma_unc=0.1)
        b3_low = Parameter(34.39, 'b3_low', one_sigma_unc=0.26)

        z_ref = Parameter(2.45, 'z_ref')
        log_phi_star = Parameter(-5.7, 'log_phi_star')
        lum_ref_star = Parameter(-26 + 1.486, 'lum_ref_star')

        parameters = {'z_pivot': z_pivot,
                      'a1_low': a1_low,
                      'a2_low': a2_low,
                      'a1_upp': a1_upp,
                      'a2_upp': a2_upp,
                      'b1_low': b1_low,
                      'b2_low': b2_low,
                      'b3_low': b3_low,
                      'b1_upp': b1_upp,
                      'b2_upp': b2_upp,
                      'b3_upp': b3_upp,
                      'z_ref': z_ref,
                      'log_phi_star': log_phi_star,
                      'lum_ref_star': lum_ref_star}

        param_functions = {'phi_star': self.phi_star,
                           'lum_ref': self.lum_ref,
                           'alpha': self.alpha}

        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = 2.4

        super(Richards2006QLF, self).__init__(parameters, param_functions,
                                              lum_type=lum_type,
                                              ref_cosmology=ref_cosmology,
                                              ref_redsh=ref_redsh,
                                              cosmology=cosmology)

    @staticmethod
    def lum_ref(redsh, lum_ref_star, b1_low, b2_low, b3_low, b1_upp, b2_upp,
                 b3_upp, z_ref, z_pivot):


        psi = np.log10( (1+redsh) / (1+z_ref))

        if redsh <= z_pivot:
            return lum_ref_star + (b1_low * psi + b2_low * psi**2 + b3_low *
                               psi**3 )
        else:
            return lum_ref_star + (b1_upp * psi + b2_upp * psi**2 + b3_upp *
                               psi**3 )


    @staticmethod
    def alpha(redsh, a1_low, a2_low, a1_upp, a2_upp, z_ref, z_pivot):

        if redsh <= z_pivot:
            return a1_low + a2_low * (redsh - z_ref)
        else:
            return a1_upp + a2_upp * (redsh - z_ref)


    @staticmethod
    def phi_star(redsh, log_phi_star):
        """

        :param redsh:
        :param log_phi_star:
        :return:
        """

        return 10**log_phi_star


    def evaluate(self, lum, redsh, parameters=None):
        """Evaluate the single power law as a function of magnitude ("lum")
        and redshift ("redsh") for the Richards 2006 QLF.

        Function to be evaluated: atelier.lumfun.richards_single_power_law()

        :param lum: Luminosity for evaluation
        :type lum: float or numpy.ndarray
        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param parameters: Dictionary of parameters used for this specific
            calculation. This does not replace the parameters with which the
            luminosity function was initialized. (default=None)
        :type parameters: dict(atelier.lumfun.Parameters)
        :return: Luminosity function value
        :rtype: (numpy.ndarray,numpy.ndarray)
        """

        if self.lum_type != 'M1450':
            raise ValueError('[ERROR] Luminosity function is not defined as a'
                             ' function of M1450. Therefore, this calculating'
                             ' the ionizing emissivity with this function is'
                             ' not valid')

        if parameters is None:
            parameters = self.parameters.copy()

        main_parameter_values = self.evaluate_main_parameters(lum, redsh,
                                                        parameters=parameters)

        phi_star = main_parameter_values['phi_star']
        lum_ref = main_parameter_values['lum_ref']
        alpha = main_parameter_values['alpha']

        # TODO: Try to precalculate factors in init for better performance
        if self.cosmology is not None and self.ref_cosmology is not \
                None:


            distmod_ref = self.ref_cosmology.distmod(self.ref_redsh)
            distmod_cos = self.cosmology.distmod(self.ref_redsh)

            # Convert luminosity according to new cosmology
            if self.lum_type in ['M1450']:
                self.cosm_lum_conv = distmod_ref.value - distmod_cos.value
            else:
                raise NotImplementedError(
                    '[ERROR] Conversions for luminosity '
                    'type {} are not implemented.'.format(
                        self.lum_type))

            self.cosm_density_conv = self.ref_cosmology.h ** 3 / \
                                     self.cosmology.h ** 3

            lum_ref = lum_ref + self.cosm_lum_conv
            phi_star = phi_star * self.cosm_density_conv

        return richards_single_power_law(lum, phi_star, lum_ref, alpha)


class Kulkarni2019QLF(DoublePowerLawLF):
    """Implementation of the type-I quasar UV(M1450) luminosity function of
    Kulkarni+2019 at z~1-6.

    ADS reference: https://ui.adsabs.harvard.edu/abs/2019MNRAS.488.1035K/abstract

    The luminosity function is parameterized as a double power law with the
    luminosity variable in absolute magnitudes at 1450A, M1450.

    This implementation adopts the double power law fit presented in Table 3
    ("Model 3").
    """

    def __init__(self, cosmology=None):
        """Initialize the Kulkarni+2019 type-I quasar UV luminosity function.
        """

        # ML fit parameters from of Model 3 from Table 3.
        c0_0 = Parameter(-6.942, 'c0_0', one_sigma_unc=[0.086, 0.086])
        c0_1 = Parameter(0.629, 'c0_1', one_sigma_unc=[0.045, 0.046])
        c0_2 = Parameter(-0.086, 'c0_2', one_sigma_unc=[0.003, 0.003])

        c1_0 = Parameter(-15.038, 'c1_0', one_sigma_unc=[0.150, 0.156])
        c1_1 = Parameter(-7.046, 'c1_1', one_sigma_unc=[0.101, 0.100])
        c1_2 = Parameter(0.772, 'c1_2', one_sigma_unc=[0.013, 0.013])
        c1_3 = Parameter(-0.030, 'c1_3', one_sigma_unc=[0.001, 0.001])

        c2_0 = Parameter(-2.888, 'c2_0', one_sigma_unc=[0.093, 0.097])
        c2_1 = Parameter(-0.383, 'c2_1', one_sigma_unc=[0.041, 0.039])

        c3_0 = Parameter(-1.602, 'c3_0', one_sigma_unc=[0.028, 0.029])
        c3_1 = Parameter(-0.082, 'c3_1', one_sigma_unc=[0.009, 0.009])

        parameters = {'c0_0': c0_0,
                      'c0_1': c0_1,
                      'c0_2': c0_2,
                      'c1_0': c1_0,
                      'c1_1': c1_1,
                      'c1_2': c1_2,
                      'c1_3': c1_3,
                      'c2_0': c2_0,
                      'c2_1': c2_1,
                      'c3_0': c3_0,
                      'c3_1': c3_1}

        param_functions = {'phi_star': self.phi_star,
                           'lum_star': self.lum_star,
                           'alpha': self.alpha,
                           'beta': self.beta}

        lum_type = 'M1450'

        ref_cosmology = FlatLambdaCDM(H0=70, Om0=0.3)
        ref_redsh = None

        super(Kulkarni2019QLF, self).__init__(parameters, param_functions,
                                              lum_type=lum_type,
                                              ref_cosmology=ref_cosmology,
                                              ref_redsh=ref_redsh,
                                              cosmology=cosmology)


    @staticmethod
    def lum_star(redsh, c1_0, c1_1, c1_2, c1_3):
        """

        :param redsh:
        :param c1_0:
        :param c1_1:
        :param c1_2:
        :param c1_3:
        :return:
        """

        return np.polynomial.chebyshev.chebval(1+redsh,
                                               c=[c1_0, c1_1, c1_2, c1_3])

    @staticmethod
    def phi_star(redsh, c0_0, c0_1, c0_2):
        """

        :param redsh:
        :param c0_0:
        :param c0_1:
        :param c0_2:
        :return:
        """

        log_phi_star = np.polynomial.chebyshev.chebval(1+redsh,
                                                       c=[c0_0, c0_1, c0_2])

        return 10**log_phi_star

    @staticmethod
    def alpha(redsh, c2_0, c2_1):
        """

        :param redsh:
        :param c2_0:
        :param c2_1:
        :return:
        """

        return np.polynomial.chebyshev.chebval(1+redsh,
                                               c=[c2_0, c2_1])

    @staticmethod
    def beta(redsh, c3_0, c3_1):
        """

        :param redsh:
        :param c3_0:
        :param c3_1:
        :return:
        """

        return np.polynomial.polynomial.polyval(1+redsh, c=[c3_0, c3_1])

