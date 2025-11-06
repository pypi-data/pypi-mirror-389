#!/usr/bin/env python

import emcee
import numpy as np
from astropy import units
from scipy import integrate
from scipy.interpolate import interp1d


# Basic functionality needed for this class
def interp_dVdzdO(redsh_range, cosmo):
    """Interpolate the differential comoving solid volume element
    :math:`(dV/dz){d\\Omega}` over the specified redshift range
    zrange = :math:`(z_1,z_2)`.

    This interpolation speeds up volume (redshift, solid angle) integrations
    for the luminosity function without significant loss in accuracy.

    The resolution of the redshift array, which will be interpolated is
    :math:`\\Delta z=0.025`.

    :param redsh_range: Redshift range for interpolation
    :type redsh_range: tuple
    :param cosmo: Cosmology
    :type cosmo: astropy.cosmology.Cosmology
    :return: 1D interpolation function
    """

    redsharray = np.arange(redsh_range[0] - 0.01, redsh_range[1] + 0.0251, 0.025)
    diff_co_vol = [cosmo.differential_comoving_volume(redsh).value for redsh in
                   redsharray]
    return interp1d(redsharray, diff_co_vol)


def mag_schechter_function(mag, phi_star, mag_star, alpha):
    """ Evaluate a Schechter luminosity function as a function of magnitude.

    :param mag:
    :param phi_star:
    :param mag_star:
    :param alpha:
    :return:
    """

    power_law = pow(10, 0.4 * (alpha + 1) * (mag_star - mag))
    exponential = np.exp(-pow(10, 0.4 * (mag_star - mag)))

    return phi_star*np.log(10)/2.5 * power_law * exponential


def lum_schechter_function(lum, phi_star, lum_star, alpha):
    """ Evaluate a Schechter luminosity function as a function of luminosity.

    :param lum: Logarithmic luminosity
    :param phi_star:
    :param lum_star:
    :param alpha:
    :return:
    """

    lum = pow(10, lum)

    power_law = pow(lum / lum_star, alpha+1)
    exponential = np.exp(-lum / lum_star)

    return np.log(10) * phi_star * power_law * exponential


def mag_double_power_law(mag, phi_star, mag_star, alpha, beta):
    """Evaluate a broken double power law luminosity function as a function
    of magnitude.

    :param mag: Magnitude
    :type mag: float or np.ndarray
    :param phi_star: Normalization of the broken power law at a value of
     mag_star
    :type phi_star: float
    :param mag_star: Break magnitude of the power law
    :type mag_star: float
    :param alpha: First slope of the broken power law
    :type alpha: float
    :param beta: Second slope of the broken power law
    :type beta: float
    :return: Value of the broken double power law at a magnitude of M
    :rtype: float or np.ndarray
    """
    A = pow(10, 0.4 * (alpha + 1) * (mag - mag_star))
    B = pow(10, 0.4 * (beta + 1) * (mag - mag_star))

    return phi_star / (A + B)


def mag_smooth_double_power_law(mag, phi_star, mag_star, alpha,
                                           beta, log_delta):
    """Evaluate a smooth broken double power law luminosity function as a
    function of magnitude.

       :param mag: Magnitude
       :type mag: float or np.ndarray
       :param phi_star: Normalization of the broken power law at a value of
        mag_star
       :type phi_star: float
       :param mag_star: Break magnitude of the power law
       :type mag_star: float
       :param alpha: First slope of the broken power law
       :type alpha: float
       :param beta: Second slope of the broken power law
       :type beta: float
       :param delta: Smoothness parameter
       :type delta: float
       :return: Value of the broken double power law at a magnitude of M
       :rtype: float or np.ndarray
       """

    delta = 10**log_delta

    A = pow(10, 0.4 * (alpha + 1) * (mag - mag_star) * delta)
    B = pow(10, 0.4 * (beta + 1) * (mag - mag_star) * delta)

    C = A + B

    return phi_star * C**(-1/delta)


def lum_double_power_law(lum, phi_star, lum_star, alpha, beta):
    """Evaluate a broken double power law luminosity function as a function
    of luminosity.

    :param lum: Luminosity
    :type lum: float or np.ndarray
    :param phi_star: Normalization of the broken power law at a value of
     lum_star
    :type phi_star: float
    :param lum_star: Break luminosity of the power law
    :type lum_star: float
    :param alpha: First slope of the broken power law
    :type alpha: float
    :param beta: Second slope of the broken power law
    :type beta: float
    :return: Value of the broken double power law at a magnitude of M
    :rtype: float or np.ndarray
    """

    A = pow((lum / lum_star), alpha)
    B = pow((lum / lum_star), beta)

    return phi_star / (A + B)


def mag_single_power_law(mag, phi_star, mag_ref, alpha):
    """Evaluate a power law luminosity function as a function as a function
    of magnitude

    :param mag: Magnitude
    :type mag: float or np.ndarray
    :param phi_star: Normalization of the power law at a value of mag_ref
    :type phi_star: float
    :param mag_ref: Reference magnitude of the power law
    :type mag_ref: float
    :param alpha: Slope of the power law
    :type alpha: float
    :return: Value of the broken double power law at a magnitude of M
    :rtype: float or np.ndarray
    """

    A = pow(10, 0.4 * (alpha + 1) * (mag - mag_ref))

    return phi_star / A


def richards_single_power_law(mag, phi_star, mag_ref, alpha):
    """

    :param mag:
    :param phi_star:
    :param mag_ref:
    :param alpha:
    :return:
    """
    return phi_star * 10**(alpha*(mag - mag_ref))


# Class functions
class Parameter(object):
    """ A class providing a data container for a parameter used in the
    luminosity function class.

    Attributes
    ----------
    value : float
        Value of the parameter
    name : string
        Name of the parameter
    bounds : tuple
        Bounds of the parameter, used in fitting
    vary : bool
        Boolean to indicate whether this parameter should be varied, used in
        fitting
    one_sigma_unc: list (2 elements)
        1 sigma uncertainty of the parameter.

    """

    def __init__(self, value, name, bounds=None, vary=True, one_sigma_unc=None):
        """Initialize the Parameter class and its attributes.

        """

        self.value = value
        self.name = name
        self.bounds = bounds
        self.vary = vary
        self.one_sigma_unc = one_sigma_unc


class LuminosityFunction(object):
    """ The base luminosity function class.

    In this implementation a luminosity function is defined in terms of

    - luminosity ("lum") and
    - redshift ("redsh")
    - a list of main parameters ("main_parameters")

    The number of main parameters depend on the functional form and can
    themselves be functions ("param_functions") of luminosity, redshift or
    additional "parameters".

    This general framework should facilitate the implementation of a wide
    range of luminosity functions without confining limits.

    An automatic initialization will check whether the parameter functions
    and parameters define all necessary main parameters.

    While the code does not distinguish between continuum luminosities,
    broad band luminosities or magnitudes, some inherited functionality is
    based on specific luminosity definitions.
    In order for these functions to work a luminosity type "lum_type" has to
    be specified. The following luminosity types have special functionality:

    - "M1450" : Absolute continuum magnitude measured at 1450A in the
      rest-frame.


    Attributes
    ----------
    parameters : dict(atelier.lumfun.Parameter)
        Dictionary of Parameter objects, which are used either as a main
        parameters for the calculation of the luminosity function or as an
        argument for calculating a main parameter using a specified parameter
        function "param_function".
    param_functions : dict(functions}
        Dictionary of functions with argument names for which the parameter
        attribute provides a Parameter or the luminosity "lum" or the
        redshift "redsh".
    main_parameters : list(string)
        List of string providing names for the main parameters of the
        luminosity function. During the initialization the main parameters
        need to be either specified as a Parameter within the "parameters"
        attribute or as a function by the "param_functions" attribute.
    lum_type : string (default=None)
        Luminosity type checked for specific functionality
    verbose : int
        Verbosity (0: no output, 1: minimal output)

    """

    def __init__(self, parameters, param_functions, main_parameters,
                 lum_type=None, cosmology=None, ref_cosmology=None,
                 ref_redsh=None, verbose=1):
        """ Initialize the base luminosity function class.
        """

        self.verbose = verbose
        self.parameters = parameters

        # The main parameters are the parameters which get passed into the
        # functional form of the luminosity function, they can themselves be
        # functions parameters (incl. redshift and luminosity dependence).
        self.main_parameters = main_parameters
        self.param_functions = param_functions

        self.lum_type = lum_type

        self._initialize_parameters_and_functions()

        self.free_parameters = self.get_free_parameters()
        self.free_parameter_names = list(self.free_parameters.keys())

        self.cosmology = cosmology
        self.ref_cosmology = ref_cosmology
        self.ref_redsh = ref_redsh

        if self.cosmology is not None and self.ref_cosmology is not \
                None:
            print('[INFO] Cosmology and reference cosmology are not the '
                  'sample. Cosmological conversions will be applied.')


    def __call__(self, lum, redsh, parameters=None):
        """ Call function that evaluates luminosity function at the given
        luminosity and redshift.

        :param lum: float or numpy.ndarray
        :type lum: Luminosity for evaluation
        :param redsh: float or numpy.ndarray
        :type redsh: Redshift for evaluation
        :param parameters: Dictionary of parameters used for this specific
            calculation. This does not replace the parameters with which the
            luminosity function was initialized.
        :type parameters: dict(atelier.lumfunParameters)
        :return: Luminosity function value at the provided luminosity and
            redshift
        :rtype: float or numpy.ndarray
        """
        if parameters is None:
            parameters = self.parameters

        return self.evaluate(lum, redsh, parameters)


    def _initialize_parameters_and_functions(self):
        """Internal function that checks the supplied parameters and
        parameter functions.

        """

        if self.verbose > 0:
            print('[INFO]---------------------------------------------------')
            print('[INFO] Performing initialization checks ')
            print('[INFO]---------------------------------------------------')

        # Check if main parameters are represented within the supplied
        # parameters and param_functions

        for main_param in self.main_parameters:

            if self.verbose > 0:
                print(
                    '[INFO]---------------------------------------------------')

            if main_param in self.param_functions and callable(
                    self.param_functions[main_param]):

                if self.verbose > 0:
                    print('[INFO] Main parameter {} is described by a '
                          'function.'.format(main_param))

                # Retrieve all parameter function parameters.
                function = self.param_functions[main_param]
                n_arg = function.__code__.co_argcount
                func_params = list(function.__code__.co_varnames[:n_arg])

                if self.verbose >0:
                    print('[INFO] The function parameters are: {}'.format(
                        func_params))

                # Remove parameters that are arguments of the luminosity.
                # function itself.
                if 'lum' in func_params:
                    func_params.remove('lum')
                if 'redsh' in func_params:
                    func_params.remove('redsh')

                # Check if all parameter function parameters are available.
                if all(param_name in self.parameters.keys() for param_name in
                       func_params):
                    if self.verbose > 0:
                        print('[INFO] All parameters are supplied.')
                        print('[INFO] Parameters "lum" and "redsh" were '
                              'ignored as they are luminosity function '
                              'arguments.')
                else:
                    raise ValueError('[ERROR] Main parameter function {} has '
                                     'not supplied parameters.'.format(
                        main_param))
            elif main_param in self.param_functions and not callable(
                    self.param_functions[main_param]):
                raise ValueError(
                    '[ERROR] Main parameter function {} is not callable'.format(
                        main_param))
            elif main_param in self.parameters:

                if self.verbose > 0:
                    print('[INFO] Main parameter {} is supplied as a normal '
                          'parameter.'.format(main_param))
            else:
                raise ValueError('[ERROR] Main parameter {} is not supplied '
                                 'as a parameter function or simple '
                                 'parameter.'.format(main_param))
        if self.verbose > 0:
            print('[INFO]---------------------------------------------------')
            print('[INFO] Initialization check passed.')
            print('[INFO]---------------------------------------------------')

    @staticmethod
    def _evaluate_param_function(param_function, parameters):
        """Internal function to evaluate the parameters function at the given
        parameter values.

        :param param_function: Parameter function
        :type param_function:
        :param parameters: Parameters of the luminosity function. Luminosity
        "lum" and redshift "redsh" need to be included along with the other
        parameters.
        :type parameters: dict(atelier.lumfun.Parameter)

        :return: Value of parameter function given the parameters
        :rtype: float
        """

        # Retrieve function parameters
        n_arg = param_function.__code__.co_argcount
        func_params = list(param_function.__code__.co_varnames[:n_arg])
        # Retrive the parameter values from the parameter dictionary
        parameter_values = [parameters[par_name].value for par_name in
                            func_params]

        # Evaluate the function and return the value
        return param_function(*parameter_values)

    def get_free_parameters(self):
        """Return a dictionary with all parameters for which vary == True.

        :return: All parameters with vary == True
        :rtype: dict(atelier.lumfun.Parameter)
        """

        free_parameters = {p: self.parameters[p] for p in self.parameters if
                           self.parameters[p].vary}

        if 'redsh' in free_parameters.keys():
            free_parameters.pop('redsh')
        if 'lum' in free_parameters.keys():
            free_parameters.pop('lum')

        return free_parameters

    def get_free_parameter_names(self):
        """Return a list of names with all parameters for which vary == True.

        :return: Names of parameters with vary == True
        :rtype: list(str)
        """

        if self.free_parameters is None:
            self.free_parameters = self.get_free_parameters()

        return list(self.free_parameters.keys())

    def print_free_parameters(self):
        """Print a list of all free (vary==True) parameters.
        """

        for param in self.free_parameters:
            name = self.free_parameters[param].name
            value = self.free_parameters[param].value
            bounds = self.free_parameters[param].bounds
            vary = self.free_parameters[param].vary

            print('Parameter {} = {}, bounds={}, vary={}'.format(name, value,
                                                                 bounds, vary))

    def print_parameters(self):
        """Print a list of all parameters.
        """

        for param in self.parameters:
            name = self.parameters[param].name
            value = self.parameters[param].value
            bounds = self.parameters[param].bounds
            vary = self.parameters[param].vary
            unc = self.parameters[param].one_sigma_unc

            print('Parameter {} = {}, bounds={}, vary={}, unc={}'.format(name,
                                                                     value,
                                                                 bounds,
                                                                         vary,
                                                                         unc))

    def update(self):
        """ Update the lumfun class parameters after a manual input.

        :return:
        """

        self.free_parameters = self.get_free_parameters()
        self.free_parameter_names = list(self.free_parameters.keys())



    def update_free_parameter_values(self, values):
        """Update all free parameters with new values.

        :param values: Values in the same order as the order of free parameters.
        :type values: list(float)
        """

        for idx, value in enumerate(values):
            param_name = self.free_parameter_names[idx]
            if self.verbose > 1:
                print(
                    '[INFO] Updating {} from {} to {}'.format(param_name, value,
                                                              self.parameters[
                                                                  param_name].value))
            self.parameters[param_name].value = value

    def evaluate_main_parameters(self, lum, redsh, parameters=None):
        """Evaluate the main parameters of the luminosity function

        :param lum: float or numpy.ndarray
        :type lum: Luminosity for evaluation
        :param redsh: float or numpy.ndarray
        :type redsh: Redshift for evaluation
        :param parameters: Dictionary of parameters used for this specific
            calculation. This does not replace the parameters with which the
            luminosity function was initialized.
        :type parameters: dict(atelier.lumfun.Parameters)
        :return:
        """

        if parameters is None:
            parameters = self.parameters.copy()

        parameters['redsh'] = Parameter(redsh, 'redsh')
        parameters['lum'] = Parameter(lum, 'lum')

        main_param_values = {}

        for main_param in self.main_parameters:
            # If main parameter is a parameter function, evaluate the function.
            if main_param in self.param_functions:
                function = self.param_functions[main_param]

                main_param_values[main_param] = \
                    self._evaluate_param_function(function, parameters)
            # If main parameter is a parameter, get its value.
            elif main_param in self.parameters:
                main_param_values[main_param] = self.parameters[
                    main_param].value
            # Else, raise value error
            else:
                raise ValueError('[ERROR] Main parameter {} cannot be '
                                 'evaluated. Neither a function or a '
                                 'parameter could be associated with '
                                 'the main parameter. This should have '
                                 'been caught at the initialization '
                                 'stage.'.format(
                    main_param))

        return main_param_values

    def evaluate(self, lum, redsh, parameters=None):
        """Evaluate the luminosity function at the given luminosity and
        redshift.

        :raise NotImplementedError

        :param lum: Luminosity for evaluation
        :type lum: float or numpy.ndarray
        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param parameters: Dictionary of parameters used for this specific
            calculation. This does not replace the parameters with which the
            luminosity function was initialized. (default=None)
        :type parameters: dict(atelier.lumfun.Parameters)
        """
        raise NotImplementedError

    def _redshift_density_integrand(self, lum, redsh, dVdzdO):
        """Internal function providing the integrand for the sample function.

        :param lum: float or numpy.ndarray
        :type lum: Luminosity for evaluation
        :param redsh: float or numpy.ndarray
        :type redsh: Redshift for evaluation
        :param dVdzdO: Differential comoving solid volume element
        :type dVdzdO: function
        :return: Returns :math:`\\Phi(L,z)\times (dV/dz){d\\Omega}`
        :rtype: float or numpy.ndarray
        """

        return self.evaluate(lum, redsh) * dVdzdO(redsh)

    def _redshift_density_integrand_selfun(self, lum, redsh, dVdzdO, selfun):
        """Internal function providing the integrand for the sample function
        including a selection function contribution.

        :param lum: float or numpy.ndarray
        :type lum: Luminosity for evaluation
        :param redsh: float or numpy.ndarray
        :type redsh: Redshift for evaluation
        :param dVdzdO: Differential comoving solid volume element
        :type dVdzdO: function
        :param selfun: Selection function
        :type selfun: atelier.selfun.QsoSelectionFunction
        :return: Returns :math:`\\Phi(L,z)\times (dV/dz){d\\Omega}`
        :rtype: float or numpy.ndarray
        """

        return self.evaluate(lum, redsh) * dVdzdO(redsh) * selfun.evaluate(lum,
                                                                  redsh)

    def integrate_over_lum_redsh(self, lum_range, redsh_range, dVdzdO=None,
                                 selfun=None, cosmology=None, **kwargs):
        """Calculate the number of sources described by the luminosity function
        over a luminosity and redshift interval in units of per steradian.

        Either a cosmology or dVdzdO have to be supplied.

        :param lum_range: Luminosity range
        :type lum_range: tuple
        :param redsh_range: Redshift range
        :type redsh_range: tuple
        :param dVdzdO: Differential comoving solid volume element (default =
            None)
        :type dVdzdO: function
        :param selfun: Selection function (default = None)
        :type selfun: atelier.selfun.QsoSelectionFunction
        :param cosmology: Cosmology (default = None)
        :type cosmology: astropy.cosmology.Cosmology
        :param kwargs:
        :return: :math:`N = \\int\\int\\Phi(L,z) (dV/(dz d\\Omega)) dL dz`
        :rtype: float
        """

        # Sort input lum/redsh ranges
        lum_range = np.sort(np.array(lum_range))
        redsh_range = np.sort(np.array(redsh_range))

        # Get keyword arguments for the integration
        int_kwargs = {}
        int_kwargs.setdefault('divmax', kwargs.pop('divmax', 20))
        int_kwargs.setdefault('tol', kwargs.pop('epsabs', 1e-3))
        int_kwargs.setdefault('rtol', kwargs.pop('epsrel', 1e-3))

        # Set up the interpolated differential comoving solid volume element
        if dVdzdO is None and cosmology is not None:
            dVdzdO = interp_dVdzdO(redsh_range, cosmology)
        elif dVdzdO is None and cosmology is None:
            raise ValueError(
                '[ERROR] Either a cosmology or dVdzdO have to be supplied.')

        if selfun is None:
            # Integrate over the luminosity and redshift range
            integrand = self._redshift_density_integrand

            inner_integral = lambda redsh: integrate.romberg(integrand,
                                                             *lum_range,
                                                             args=(redsh,
                                                                   dVdzdO),
                                                             **int_kwargs)
            outer_integral = integrate.romberg(inner_integral, *redsh_range,
                                               **int_kwargs)

        else:
            # Integrate over the luminosity and redshift range, including the
            # selection function.

            integrand = self._redshift_density_integrand_selfun

            inner_integral = lambda redsh: integrate.romberg(integrand,
                                                             *lum_range,
                                                             args=(redsh,
                                                                   dVdzdO,
                                                                   selfun),
                                                             **int_kwargs)
            outer_integral = integrate.romberg(inner_integral, *redsh_range,
                                               **int_kwargs)

        return outer_integral

    def integrate_over_lum_redsh_simpson(self, lum_range, redsh_range,
                                       dVdzdO=None, selfun=None,
                                 cosmology=None, initial_lum_bin_width=0.1,
                                         initial_redsh_bin_width=0.05,
                                         minimum_probability=1e-3,
                                         **kwargs):
        """Calculate the number of sources described by the luminosity function
        over a luminosity and redshift interval in units of per steradian.

        The integration is done on a grid using the Simpson rule.

        This allows the selection function to be precalculated on the grid
        values for speed up of the integration process.

        This code is in large part adopted from
        https://github.com/imcgreer/simqso/blob/master/simqso/lumfun.py
        lines 591 and following.

        Either a cosmology or dVdzdO have to be supplied.

        :param lum_range: Luminosity range
        :type lum_range: tuple
        :param redsh_range: Redshift range
        :type redsh_range: tuple
        :param dVdzdO: Differential comoving solid volume element (default =
            None)
        :type dVdzdO: function
        :param selfun: Selection function (default = None)
        :type selfun: atelier.selfun.QsoSelectionFunction
        :param cosmology: Cosmology (default = None)
        :type cosmology: astropy.cosmology.Cosmology
        :param kwargs:
        :return: :math:`N = \\int\\int\\Phi(L,z) (dV/(dz d\\Omega)) dL dz`
        :rtype: float
        """

        # Set up the interpolated differential comoving solid volume element
        if dVdzdO is None and cosmology is not None:
            dVdzdO = interp_dVdzdO(redsh_range, cosmology)
        elif dVdzdO is None and cosmology is None:
            raise ValueError(
                '[ERROR] Either a cosmology or dVdzdO have to be supplied.')

        # Sort input lum/redsh ranges
        lum_range = np.sort(np.array(lum_range))
        redsh_range = np.sort(np.array(redsh_range))

        # Setting up the integration grid
        num_lum_bins = int(np.diff(lum_range) / initial_lum_bin_width) + 1
        num_redsh_bins = int(np.diff(redsh_range) / initial_redsh_bin_width) + 1

        lum_edges = np.linspace(lum_range[0], lum_range[1], num_lum_bins)
        redsh_edges = np.linspace(redsh_range[0], redsh_range[1],
                                  num_redsh_bins)

        lum_bin_width = np.diff(lum_edges)[0]
        redsh_bin_width = np.diff(redsh_edges)[0]
        diffvol_grid = dVdzdO(redsh_edges)

        # Generate grid points
        lum_points, redsh_points = np.meshgrid(lum_edges, redsh_edges,
                                           indexing='ij')

        # Calculate selection function grid
        if selfun is not None:
            if selfun.simps_grid is None:
                selfun_grid = selfun.evaluate(lum_points, redsh_points)
                selfun.simps_grid = selfun_grid
            else:
                selfun_grid = selfun.simps_grid

            # selection_mask = selfun_grid > minimum_probability

        # Calculate the luminosity function grid
        lumfun_grid = self.evaluate(lum_points, redsh_points)

        # Calculate the double integral via the Simpson rule
        if selfun is not None:
            inner_integral = integrate.simps(lumfun_grid * selfun_grid *
                                             diffvol_grid,
                                             dx=redsh_bin_width)
        else:
            inner_integral = integrate.simps(lumfun_grid *
                                             diffvol_grid,
                                             dx=redsh_bin_width)

        outer_integral = integrate.simps(inner_integral, dx=lum_bin_width)

        return outer_integral

    # TODO: New, needs to be tested

    def _luminosity_density_integrand(self, lum, redsh):
        """Internal function providing the integrand for the luminosity density
        integration.

        :param lum: float or numpy.ndarray
        :type lum: Luminosity for evaluation
        :param redsh: float or numpy.ndarray
        :type redsh: Redshift for evaluation
        :param dVdzdO: Differential comoving solid volume element
        :type dVdzdO: function
        :return: Returns :math:`\\Phi(L,z)\times (dV/dz){d\\Omega}`
        :rtype: float or numpy.ndarray
        """

        return self.evaluate(lum, redsh) * 10**lum

    def integrate_to_luminosity_density(self, lum_range, redsh,
                                        **kwargs):
        """

        :param lum_range:
        :param redsh:
        :param dVdzdO:
        :return: :math:`\\int \\Phi(L,z) L (dV/dz){d\\Omega} dL`
        """

        # Get keyword arguments for the integration
        int_kwargs = {}
        int_kwargs.setdefault('epsabs', kwargs.pop('epsabs', 1e-3))
        int_kwargs.setdefault('epsrel', kwargs.pop('epsrel', 1e-3))

        integrand = self._luminosity_density_integrand

        # lum_den = integrate.romberg(integrand, *lum_range, args=(redsh,),
        #                             **int_kwargs)

        lum_den = integrate.quad(integrand, *lum_range, args=(redsh,),
                                    **int_kwargs)[0]

        return lum_den

    def integrate_over_lum_redsh_appmag_limit(self, lum_range, redsh_range,
                                              appmag_limit, kcorrection,
                                       dVdzdO=None, selfun=None,
                                 cosmology=None, initial_lum_bin_width=0.1,
                                         initial_redsh_bin_width=0.05,
                                         minimum_probability=1e-3,
                                         **kwargs):
        """

        :param lum_range:
        :param redsh_range:
        :param appmag_limit:
        :param kcorrection:
        :param dVdzdO:
        :param selfun:
        :param cosmology:
        :param initial_lum_bin_width:
        :param initial_redsh_bin_width:
        :param minimum_probability:
        :param kwargs:
        :return:
        """

        # Set up the interpolated differential comoving solid volume element
        if dVdzdO is None and cosmology is not None:
            dVdzdO = interp_dVdzdO(redsh_range, cosmology)
        elif dVdzdO is None and cosmology is None:
            raise ValueError(
                '[ERROR] Either a cosmology or dVdzdO have to be supplied.')

        # Sort input lum/redsh ranges
        lum_range = np.sort(np.array(lum_range))
        redsh_range = np.sort(np.array(redsh_range))

        # Setting up the integration grid
        num_lum_bins = int(np.diff(lum_range) / initial_lum_bin_width) + 1
        num_redsh_bins = int(np.diff(redsh_range) / initial_redsh_bin_width) + 1

        lum_edges = np.linspace(lum_range[0], lum_range[1], num_lum_bins)
        redsh_edges = np.linspace(redsh_range[0], redsh_range[1],
                                  num_redsh_bins)

        lum_bin_width = np.diff(lum_edges)[0]
        redsh_bin_width = np.diff(redsh_edges)[0]
        diffvol_grid = dVdzdO(redsh_edges)

        # Generate grid points
        lum_points, redsh_points = np.meshgrid(lum_edges, redsh_edges,
                                               indexing='ij')

        # Calculate selection function grid
        if selfun is not None:
            if selfun.simps_grid is None:
                selfun_grid = selfun.evaluate(lum_points, redsh_points)
                selfun.simps_grid = selfun_grid
            else:
                selfun_grid = selfun.simps_grid



        # Mask by apparent magnitude limit
        lum_lim = lambda redsh: np.clip(kcorrection.m2M(appmag_limit, redsh),
                                        lum_range[0], lum_range[1])[0]

        # Create mask for bins outside apparent magnitude limit
        m = lum_points > lum_lim(redsh_points)

        # Calculate the luminosity function grid
        lumfun_grid = self.evaluate(lum_points, redsh_points)

        # Set the lum function to 0, where the mask is false
        lumfun_grid[m] = 0

        # Calculate the double integral via the Simpson rule
        if selfun is not None:

            inner_integral = integrate.simps(lumfun_grid * selfun_grid *
                                             diffvol_grid,
                                             dx=redsh_bin_width)
        else:
            inner_integral = integrate.simps(lumfun_grid *
                                             diffvol_grid,
                                             dx=redsh_bin_width)

        outer_integral = integrate.simps(inner_integral, dx=lum_bin_width)

        return outer_integral

    def redshift_density(self, redsh, lum_range, dVdzdO, app2absmag=lambda x: x[0], **kwargs):
        """Calculate the volumetric source density described by the luminosity
        function at a given redshift and over a luminosity interval in units of
        per steradian per redshift.

        :param redsh: Redshift
        :type redsh: float
        :param lum_range: Luminosity range
        :type lum_range: tuple
        :param dVdzdO: Differential comoving solid volume element (default =
            None)
        :type dVdzdO: function
        :param app2absmag: Function to convert between different magnitudes, argument is x = (magnitude, redshift) (default = indentity function w.r.t. magnitude)
        :type app2absmag: function
        :param kwargs:
        :return: :math:`\\int \\Phi(L,z) (dV/dz){d\\Omega} dL`
        :rtype: float
        """

        # Get keyword arguments for the integration
        int_kwargs = {}
        # int_kwargs.setdefault('divmax', kwargs.pop('divmax', 20))
        # int_kwargs.setdefault('tol', kwargs.pop('epsabs', 1e-3))
        # int_kwargs.setdefault('rtol', kwargs.pop('epsrel', 1e-3))
        int_kwargs.setdefault('epsabs', kwargs.pop('epsabs', 1.49e-08))
        int_kwargs.setdefault('epsrel', kwargs.pop('epsrel', 1.49e-08))

        # integral = integrate.romberg(self._redshift_density_integrand,
        #                              lum_range[0],
        #                              lum_range[1],
        #                              args=(redsh, dVdzdO), **int_kwargs)

        integral = integrate.quad(self._redshift_density_integrand,
                                     app2absmag([lum_range[0], redsh]),
                                     app2absmag([lum_range[1], redsh]),
                                     args=(redsh, dVdzdO), **int_kwargs)[0]

        return integral

    def integrate_lum(self, redsh, lum_range, **kwargs):
        """Calculate the volumetric source density described by the luminosity
        function at a given redshift and over a luminosity interval in units of
        per Mpc^3.

        :param redsh: Redshift
        :type redsh: float
        :param lum_range: Luminosity range
        :type lum_range: tuple
        :param kwargs:
        :return: :math:`\\int \\Phi(L,z) dL`
        :rtype: float
        """

        # Get keyword arguments for the integration
        int_kwargs = {}
        # int_kwargs.setdefault('divmax', kwargs.pop('divmax', 20))
        # int_kwargs.setdefault('tol', kwargs.pop('epsabs', 1e-3))
        # int_kwargs.setdefault('rtol', kwargs.pop('epsrel', 1e-3))
        int_kwargs.setdefault('epsabs', kwargs.pop('epsabs', 1.49e-08))
        int_kwargs.setdefault('epsrel', kwargs.pop('epsrel', 1.49e-08))

        integral = integrate.quad(self.evaluate,
                                     lum_range[0],
                                     lum_range[1],
                                     args=(redsh,), **int_kwargs)[0]

        return integral


    def sample(self, lum_range, redsh_range, cosmology, sky_area,
               seed=1234, lum_res=1e-2, redsh_res=1e-2, verbose=1, **kwargs):
        """Sample the luminosity function over a given luminosity and
            redshift range.

        This sampling routine is in large part adopted from
        https://github.com/imcgreer/simqso/blob/master/simqso/lumfun.py
        , lines 219 and following.

        If the integral over the luminosity function does not have an
        analytical implementation, integrals are calculated using
        integrate.romberg, which can take a substantial amount of time.

        :param lum_range: Luminosity range
        :type lum_range: tuple
        :param redsh_range: Redshift range
        :type redsh_range: tuple
        :param cosmology: Cosmology (default = None)
        :type cosmology: astropy.cosmology.Cosmology
        :param sky_area: Area of the sky to be sampled in square degrees
        :type sky_area: float
        :param seed: Random seed for the sampling
        :type seed: int
        :param lum_res: Luminosity resolution (default = 1e-2, equivalent to
            100 bins)
        :type lum_res: float
        :param redsh_res: Redshift resolution (default = 1e-2, equivalent to
            100 bins)
        :type redsh_res: float
        :param verbose: Verbosity
        :type verbose: int
        :return: Source sample luminosities and redshifts
        :rtype: (numpy.ndarray,numpy.ndarray)
        """

        # Get keyword arguments for the integration accuracy
        epsabs = kwargs.pop('epsabs', 1e-3)
        epsrel = kwargs.pop('epsrel', 1e-3)

        # Sky area in steradian
        sky_area_srd = sky_area / 41253. * 4 * np.pi

        # Instantiate differential comoving solid volume element
        dVdzdO = interp_dVdzdO(redsh_range, cosmology)

        # Number of luminosity and redshift ranges for the discrete
        # integrations below.
        n_lum = int(np.diff(lum_range) / lum_res)
        n_redsh = int(np.diff(redsh_range) / redsh_res)

        # Calculate the dN/dz distribution
        redsh_bins = np.linspace(redsh_range[0], redsh_range[1], n_redsh)

        # An array to store the number of sources within a given redshift bin
        redsh_n = np.zeros_like(redsh_bins)

        for idx in range(len(redsh_bins)-1):

            redsh_n[idx+1] = integrate.quad(self.redshift_density,
                                            redsh_bins[idx],
                                            redsh_bins[idx+1],
                                            args=(lum_range, dVdzdO),
                                            epsabs=epsabs,
                                            epsrel=epsrel)[0]

        # The total number of sources of the integration per steradian
        total = np.sum(redsh_n)
        # Interpolation of luminosity function in redshift space
        redsh_func = interp1d(np.cumsum(redsh_n)/total, redsh_bins)
        # The total number of sources as rounded to an integer value across
        # the sky_area specified in the input argument.
        total = int(np.round(total * sky_area_srd))
        if verbose > 0:
            print('[INFO] Integration returned {} sources'.format(total))

        # Draw random values from the total number of sources
        np.random.seed(seed)
        redsh_rand = np.random.random(total)
        lum_rand = np.random.random(total)

        # Sample the redshift values using the interpolation above
        redsh_sample = redsh_func(redsh_rand)
        # Set up the luminosity range
        lum_sample = np.zeros_like(redsh_sample)

        for source in range(total):
            lum_bins = np.linspace(lum_range[0], lum_range[1], n_lum)

            # An array to store the number of sources within a given
            # luminosity bin.
            lum_n = np.zeros_like(lum_bins)

            for idx in range(len(lum_bins)-1):

                lum_n[idx] = self.redshift_density(redsh_sample[source],
                                                     [lum_bins[idx],
                                                     lum_bins[idx+1]],
                                                     dVdzdO)

            # Interpolation of the luminosity function an redshift of the
            # random source over luminosity
            lum_func = interp1d(np.cumsum(lum_n) / np.sum(lum_n), lum_bins)

            # Draw a random luminosity value for the source
            lum_sample[source] = lum_func(lum_rand[source])

        return lum_sample, redsh_sample


    def qlf_mcmc_wrapper(self, x, lum_range, redsh_range, cosmo, app2absmag):
        """Wrapper function for the MCMC sampling routine in sample_mcmc.

        :param x: Arguments of the probability density to sample from,
         i.e. x = (lum, redsh)
        :type x: tuple
        :param lum_range: Luminosity range to sample from
        :type lum_range: tuple
        :param redsh_range: Redshift range to sample from
        :type redsh_range: tuple
        :param cosmo: Cosmology
        :type cosmo: astropy.cosmology.Cosmology
        :param app2absmag: Function to convert between different magnitudes,
         argument is x = (lum, redsh) (default = indentity function w.r.t. lum)
        :type app2absmag: function
        :return: Log probability given the arguments x = (lum, redsh)
        :rtype: float
        """

        # Get the separate arguments of the QLF
        lum, redsh = x[0], x[1]

        # If arguments are within the specified ranges,
        # set the log probability according to the QLF value,
        # otherwise assign zero probability
        if (lum >= lum_range[0] and lum <= lum_range[1] and
                redsh >= redsh_range[0] and redsh <= redsh_range[1]):
            dVdzdO = cosmo.differential_comoving_volume(redsh).value
            return np.log(self.evaluate(app2absmag([lum, redsh]), redsh) * dVdzdO)
        else:
            return -np.inf


    def sample_mcmc(self, lum_range, redsh_range, cosmology, sky_area,
                    seed=1234, nwalkers=8, nsteps_warmup=5000,
                    app2absmag=lambda x: x[0], verbose=1, **kwargs):
        """Sample the luminosity function over a given luminosity and
            redshift range using an MCMC sampler.

        :param lum_range: Luminosity range
        :type lum_range: tuple
        :param redsh_range: Redshift range
        :type redsh_range: tuple
        :param cosmology: Cosmology (default = None)
        :type cosmology: astropy.cosmology.Cosmology
        :param sky_area: Area of the sky to be sampled in square degrees
        :type sky_area: float
        :param seed: Random seed for the MCMC sampling
        :type seed: int
        :param nwalkers: Number of walkers for the MCMC sampler
        :type nwalkers: int
        :param nsteps_warmup: Number of warmup steps for the MCMC sampler
        :type nsteps_warmup: int
        :param app2absmag: Function to convert between different magnitudes,
        argument is x = (lum, redsh) (default = identity function w.r.t. lum)
        :type app2absmag: function
        :param verbose: Verbosity
        :type verbose: int
        :return: Source sample luminosities and redshifts
        :rtype: (numpy.ndarray,numpy.ndarray)
        """

        # Get keyword arguments for the integration accuracy
        epsabs = kwargs.pop('epsabs', 1e-3)
        epsrel = kwargs.pop('epsrel', 1e-3)

        # Sky area in steradian
        sky_area_srd = sky_area / 41253. * 4 * np.pi

        # Instantiate differential comoving solid volume element
        dVdzdO = interp_dVdzdO(redsh_range, cosmology)

        # The total number of sources of the integration per steradian
        total = integrate.quad(self.redshift_density, *redsh_range,
                               args=(lum_range, dVdzdO, app2absmag),
                               epsabs=epsabs, epsrel=epsrel)[0]

        # The total number of sources as rounded to an integer value across
        # the sky_area specified in the input argument.
        total = int(np.round(total * sky_area_srd))
        if verbose > 0:
            print('[INFO] Integration returned {} sources'.format(total))

        # Dimension of the distribution to sample from is 2 (luminosity + redshift)
        ndim = 2

        # Number of effective samples needed per MCMC walker
        neffsamples = int(np.ceil(total/nwalkers))

        # Randomly initializing the initial positions for the MCMC walkers
        np.random.seed(seed)
        x0 = np.random.rand(ndim, nwalkers)
        p0 = np.stack([lum_range[0]+(lum_range[1]-lum_range[0])*x0[0],
                       redsh_range[0]+(redsh_range[1]-redsh_range[0])*x0[1]]).T

        # Instantiating the MCMC sampler
        sampler = emcee.EnsembleSampler(nwalkers, ndim, self.qlf_mcmc_wrapper,
                                        args=[lum_range, redsh_range, cosmology, app2absmag])

        # Running nsteps_warmup MCMC steps to determine the autocorrelation
        # time which sets the total number of samples needed
        state = sampler.run_mcmc(p0, nsteps_warmup)
        tau = int(np.ceil(np.max(sampler.get_autocorr_time())))
        print("Acceptance fraction: {}".format(sampler.acceptance_fraction))
        print("Autocorrelation time: {} steps".format(tau))
        sampler.reset()

        # Running the MCMC sampler for 5*tau*neffsamples steps and only keeping
        # every 5tau-th sample to avoid autocorrelations among the samples
        sampler.run_mcmc(state, 5*tau*neffsamples)
        samples = sampler.get_chain(flat=True).reshape(nwalkers*5*tau*neffsamples, ndim)
        return samples[::5*tau, 0], samples[::5*tau, 1]


class DoublePowerLawLF(LuminosityFunction):
    """ Luminosity function, which takes the functional form of a double
    power law with the luminosity in absolute magnitudes.

    The luminosity function has four main parameters:

    - "phi_star": the overall normalization
    - "lum_star": the break luminosity/magnitude where the power law slopes
      change.
    - "alpha": the first power law slope
    - "beta": the second power law slope

    """

    def __init__(self, parameters, param_functions, lum_type=None,
                 cosmology=None, ref_cosmology=None, ref_redsh=None, verbose=1):
        """Initialization of the double power law luminosity function class.
        """

        # The main parameters are the parameters which get passed into the
        # functional form of the luminosity function, they can themselves be
        # functions parameters (incl. redshift and luminosity dependence).
        self.main_parameters = ['phi_star', 'lum_star', 'alpha', 'beta']

        # Initialize the parent class
        super(DoublePowerLawLF, self).__init__(parameters, param_functions,
                                               self.main_parameters,
                                               lum_type=lum_type,
                                               cosmology=cosmology,
                                               ref_cosmology=ref_cosmology,
                                               ref_redsh = ref_redsh,
                                               verbose=verbose)

    def evaluate(self, lum, redsh, parameters=None):
        """Evaluate the double power law as a function of magnitude ("lum")
        and redshift ("redsh").

        Function to be evaluated: atelier.lumfun.mag_double_power_law()

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

            lum_star = lum_star + self.cosm_lum_conv
            phi_star = phi_star * self.cosm_density_conv

        return mag_double_power_law(lum, phi_star, lum_star, alpha, beta)

    def calc_ionizing_emissivity_at_1450A(self, redsh, lum_range, **kwargs):
        """Calculate the ionizing emissivity at rest-frame 1450A,
        :math:`\\epsilon_{1450}`, in units of
        erg s^-1 Hz^-1 Mpc^-3.

        This function integrates the luminosity function at redshift "redsh"
        over the luminosity interval "lum_range" to calculate the ionizing
        emissivity at rest-frame 1450A.

        Calling this function is only valid if the luminosity function
        "lum_type" argument is "lum_type"="M1450".

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param lum_range: Luminosity range
        :type lum_range: tuple
        :return: Ionizing emissivity (erg s^-1 Hz^-1 Mpc^-3)
        :rtype: float
        """

        if self.lum_type != 'M1450':
            raise ValueError('[ERROR] Luminosity function is not defined as a'
                             ' function of M1450. Therefore, calculating'
                             ' the ionizing emissivity with this function is'
                             ' not valid')

        # Get keyword arguments for the integration
        int_kwargs = {}
        int_kwargs.setdefault('epsabs', kwargs.pop('epsabs', 1.49e-08))
        int_kwargs.setdefault('epsrel', kwargs.pop('epsrel', 1.49e-08))

        # Integrate luminosity function times L1450 over luminosity
        integral = integrate.quad(self._ionizing_emissivity_integrand,
                                     lum_range[0],
                                     lum_range[1],
                                     args=(redsh,),
                                     **int_kwargs)[0]

        return integral

    def _ionizing_emissivity_integrand(self, lum, redsh):
        """Internal function that provides the integrand for the ionizing
        emissivity.

        :param lum: Luminosity for evaluation
        :type lum: float or numpy.ndarray
        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :return: Ionizing emissivity per magnitude (erg s^-1 Hz^-1 Mpc^-3
        M_1450^-1)
        :rtype: float

        """
        # Evaluate parameters
        parameters = self.parameters.copy()
        main_parameter_values = self.evaluate_main_parameters(lum, redsh,
                                                              parameters=parameters)
        # Modify slopes to integrate over Phi L dM
        phi_star = main_parameter_values['phi_star']
        lum_star = main_parameter_values['lum_star']
        alpha = main_parameter_values['alpha']+1
        beta = main_parameter_values['beta']+1

        # Convert to different cosmology
        # TODO: Move to integral function for better performance!
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

            lum_star = lum_star + self.cosm_lum_conv
            phi_star = phi_star * self.cosm_density_conv

        # Reproducing Ian's function (for now)
        c = 4. * np.pi * (10 * units.pc.to(units.cm)) ** 2
        LStar_nu = c * 10 ** (-0.4 * (lum_star + 48.6))

        return mag_double_power_law(lum, phi_star, lum_star, alpha, beta) * LStar_nu




class SmoothDoublePowerLawLF(LuminosityFunction):
    """ Luminosity function, which takes the functional form of a double
    power law with the luminosity in absolute magnitudes.

    The luminosity function has four main parameters:

    - "phi_star": the overall normalization
    - "lum_star": the break luminosity/magnitude where the power law slopes
      change.
    - "alpha": the first power law slope
    - "beta": the second power law slope
    - "delta": the smoothing parameter

    """

    def __init__(self, parameters, param_functions, lum_type=None,
                 cosmology=None, ref_cosmology=None, ref_redsh=None, verbose=1):
        """Initialization of the double power law luminosity function class.
        """

        # The main parameters are the parameters which get passed into the
        # functional form of the luminosity function, they can themselves be
        # functions parameters (incl. redshift and luminosity dependence).
        self.main_parameters = ['phi_star', 'lum_star', 'alpha', 'beta',
                                'log_delta']

        # Initialize the parent class
        super(SmoothDoublePowerLawLF, self).__init__(parameters, param_functions,
                                               self.main_parameters,
                                               lum_type=lum_type,
                                               cosmology=cosmology,
                                               ref_cosmology=ref_cosmology,
                                               ref_redsh = ref_redsh,
                                               verbose=verbose)

    def evaluate(self, lum, redsh, parameters=None):
        """Evaluate the double power law as a function of magnitude ("lum")
        and redshift ("redsh").

        Function to be evaluated: atelier.lumfun.mag_double_power_law()

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
        log_delta = main_parameter_values['log_delta']

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

            lum_star = lum_star + self.cosm_lum_conv
            phi_star = phi_star * self.cosm_density_conv

        return mag_smooth_double_power_law(lum, phi_star, lum_star, alpha,
                                           beta, log_delta)

    def calc_ionizing_emissivity_at_1450A(self, redsh, lum_range, **kwargs):
        """Calculate the ionizing emissivity at rest-frame 1450A,
        :math:`\\epsilon_{1450}`, in units of
        erg s^-1 Hz^-1 Mpc^-3.

        This function integrates the luminosity function at redshift "redsh"
        over the luminosity interval "lum_range" to calculate the ionizing
        emissivity at rest-frame 1450A.

        Calling this function is only valid if the luminosity function
        "lum_type" argument is "lum_type"="M1450".

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param lum_range: Luminosity range
        :type lum_range: tuple
        :return: Ionizing emissivity (erg s^-1 Hz^-1 Mpc^-3)
        :rtype: float
        """

        if self.lum_type != 'M1450':
            raise ValueError('[ERROR] Luminosity function is not defined as a'
                             ' function of M1450. Therefore, this calculating'
                             ' the ionizing emissivity with this function is'
                             ' not valid')

        # Get keyword arguments for the integration
        int_kwargs = {}
        int_kwargs.setdefault('epsabs', kwargs.pop('epsabs', 1.49e-08))
        int_kwargs.setdefault('epsrel', kwargs.pop('epsrel', 1.49e-08))

        # Integrate luminosity function times L1450 over luminosity
        integral = integrate.quad(self._ionizing_emissivity_integrand,
                                     lum_range[0],
                                     lum_range[1],
                                     args=(redsh,),
                                     **int_kwargs)[0]

        return integral

    def _ionizing_emissivity_integrand(self, lum, redsh):
        """Internal function that provides the integrand for the ionizing
        emissivity.

        :param lum: Luminosity for evaluation
        :type lum: float or numpy.ndarray
        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :return: Ionizing emissivity per magnitude (erg s^-1 Hz^-1 Mpc^-3
        M_1450^-1)
        :rtype: float

        """
        # Evaluate parameters
        parameters = self.parameters.copy()
        main_parameter_values = self.evaluate_main_parameters(lum, redsh,
                                                              parameters=parameters)
        # Modify slopes to integrate over Phi L dM
        phi_star = main_parameter_values['phi_star']
        lum_star = main_parameter_values['lum_star']
        alpha = main_parameter_values['alpha']+1
        beta = main_parameter_values['beta']+1

        # Convert to different cosmology
        # TODO: Move to integral function for better performance!
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

            lum_star = lum_star + self.cosm_lum_conv
            phi_star = phi_star * self.cosm_density_conv

        # Reproducing Ian's function (for now)
        c = 4. * np.pi * (10 * units.pc.to(units.cm)) ** 2
        LStar_nu = c * 10 ** (-0.4 * (lum_star + 48.6))

        return mag_double_power_law(lum, phi_star, lum_star, alpha, beta) * LStar_nu



class SinglePowerLawLF(LuminosityFunction):
    """ Luminosity function, which takes the functional form of a single
    power law with the luminosity in absolute magnitudes.

    The luminosity function has three main parameters:

    - "phi_star": the overall normalization
    - "alpha": the first power law slope
    - "lum_ref": the break luminosity/magnitude where the power law slopes
      change.


    """

    def __init__(self, parameters, param_functions, lum_type=None,
                 ref_cosmology=None, ref_redsh=None, cosmology=None,
        verbose=1):
        """Initialize the single power law luminosity function class.
        """

        self.main_parameters = ['phi_star', 'alpha', 'lum_ref']

        # Initialize the parent class
        super(SinglePowerLawLF, self).__init__(parameters, param_functions,
                                               self.main_parameters,
                                               lum_type=lum_type,
                                               ref_cosmology=ref_cosmology,
                                               ref_redsh=ref_redsh,
                                               cosmology=cosmology,
                                               verbose=verbose)

    def evaluate(self, lum, redsh, parameters=None):
        """Evaluate the single power law as a function of magnitude ("lum")
        and redshift ("redsh").

        Function to be evaluated: atelier.lumfun.mag_single_power_law()

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

        return mag_single_power_law(lum, phi_star, lum_ref, alpha)


    def calc_ionizing_emissivity_at_1450A(self, redsh, lum_range, **kwargs):
        """Calculate the ionizing emissivity at rest-frame 1450A,
        :math:`\\epsilon_{1450}`, in units of
        erg s^-1 Hz^-1 Mpc^-3.

        This function integrates the luminosity function at redshift "redsh"
        over the luminosity interval "lum_range" to calculate the ionizing
        emissivity at rest-frame 1450A.

        Calling this function is only valid if the luminosity function
        "lum_type" argument is "lum_type"="M1450".

        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :param lum_range: Luminosity range
        :type lum_range: tuple
        :return: Ionizing emissivity (erg s^-1 Hz^-1 Mpc^-3)
        :rtype: float
        """

        # Get keyword arguments for the integration
        int_kwargs = {}
        int_kwargs.setdefault('epsabs', kwargs.pop('epsabs', 1.49e-08))
        int_kwargs.setdefault('epsrel', kwargs.pop('epsrel', 1.49e-08))

        # Integrate luminosity function times L1450 over luminosity
        integral = integrate.quad(self._ionizing_emissivity_integrand,
                                     lum_range[0],
                                     lum_range[1],
                                     args=(redsh,),
                                     **int_kwargs)[0]

        return integral

    def _ionizing_emissivity_integrand(self, lum, redsh):
        """Internal function that provides the integrand for the ionizing
        emissivity.

        :param lum: Luminosity for evaluation
        :type lum: float or numpy.ndarray
        :param redsh: Redshift for evaluation
        :type redsh: float or numpy.ndarray
        :return: Ionizing emissivity per magnitude (erg s^-1 Hz^-1 Mpc^-3
        M_1450^-1)
        :rtype: float

        """
        # Evaluate parameters
        parameters = self.parameters.copy()
        main_parameter_values = self.evaluate_main_parameters(lum, redsh,
                                                              parameters=parameters)
        # Modify slopes to integrate over Phi L dM
        phi_star = main_parameter_values['phi_star']
        lum_ref = main_parameter_values['lum_ref']
        alpha = main_parameter_values['alpha'] + 1

        # Convert to different cosmology
        # TODO: Move to integral function for better performance!
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


        # Reproducing Ians function (for now)
        c = 4. * np.pi * (10 * units.pc.to(units.cm)) ** 2
        LStar_nu = c * 10 ** (-0.4 * (lum_ref + 48.6))

        return mag_single_power_law(lum, phi_star, lum_ref, alpha) * LStar_nu


class SchechterLF(LuminosityFunction):
    """
    Schechter luminosity function
    """

    def __init__(self, parameters, param_functions, lum_type=None,
                 ref_cosmology=None, ref_redsh=None, cosmology=None,
                 verbose=1):
        """Initialize the single power law luminosity function class.
        """

        self.main_parameters = ['phi_star', 'alpha', 'mag_star']

        # Initialize the parent class
        super(SchechterLF, self).__init__(parameters, param_functions,
                                               self.main_parameters,
                                               lum_type=lum_type,
                                               ref_cosmology=ref_cosmology,
                                               ref_redsh=ref_redsh,
                                               cosmology=cosmology,
                                               verbose=verbose)

    def evaluate(self, lum, redsh, parameters=None):
        """Evaluate the Schechter function as a function of magnitude ("lum")
        and redshift ("redsh").

        Function to be evaluated: atelier.lumfun.mag_schechter

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
        mag_star = main_parameter_values['mag_star']
        alpha = main_parameter_values['alpha']

        return mag_schechter_function(lum, phi_star, mag_star, alpha)


class SchechterLFLum(LuminosityFunction):
    """
    Schechter luminosity function
    """

    def __init__(self, parameters, param_functions, lum_type=None,
                 ref_cosmology=None, ref_redsh=None, cosmology=None,
                 verbose=1):
        """Initialize the single power law luminosity function class.
        """

        self.main_parameters = ['phi_star', 'alpha', 'lum_star']

        # Initialize the parent class
        super(SchechterLFLum, self).__init__(parameters, param_functions,
                                               self.main_parameters,
                                               lum_type=lum_type,
                                               ref_cosmology=ref_cosmology,
                                               ref_redsh=ref_redsh,
                                               cosmology=cosmology,
                                               verbose=verbose)

    def evaluate(self, lum, redsh, parameters=None):
        """Evaluate the Schechter function as a function of magnitude ("lum")
        and redshift ("redsh").

        Function to be evaluated: atelier.lumfun.mag_schechter

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

        return lum_schechter_function(lum, phi_star, lum_star, alpha)



class BinnedLuminosityFunction(object):

    def __init__(self, lum=None, lum_type=None, lum_unit=None,
                 phi=None, log_phi=None, phi_unit=None,
                 sigma_phi=None, sigma_log_phi=None, ref_cosmology=None,
                 redshift=None, redshift_range=None, cosmology=None, **kwargs):

        self.redshift = redshift
        self.redshift_range =redshift_range

        if lum is not None:
            self.lum = lum

            if lum_type is None:
                raise ValueError('[ERROR] Luminosity type not specified!')
            else:
                self.lum_type = lum_type
            if lum_unit is None:
                raise ValueError('[ERROR] Luminosity unit not specified!')
            else:
                self.lum_unit = lum_unit

        if phi is not None or log_phi is not None:

            if phi_unit is None:
                raise ValueError('[ERROR] Luminosity function unit not '
                                 'specified!')

            if phi is not None and log_phi is None:
                self.phi = phi
                self._get_logphi_from_phi()
            elif log_phi is not None and phi is None:
                self.log_phi = log_phi
                self._get_phi_from_logphi()

            elif log_phi is not None and phi is not None:
                self.phi = phi
                self.log_phi = log_phi

        if sigma_phi is not None or sigma_log_phi is not None:

            if sigma_phi is not None and sigma_log_phi is None:

                self.sigma_phi = sigma_phi
                self._get_sigma_logphi_from_sigma_phi()

            elif sigma_log_phi is not None and sigma_phi is None:

                self.sigma_log_phi = sigma_log_phi
                self._get_sigma_phi_from_sigma_logphi()

            else:
                self.sigma_phi = sigma_phi
                self.sigma_log_phi = sigma_log_phi

        if ref_cosmology is None:
            raise ValueError('[ERROR] No reference cosmology specified!')
        else:
            self.ref_cosmology = ref_cosmology

        if cosmology is None:
            print('[INFO] No cosmology specified, reference cosmology is '
                  'used.')
        else:
            print('[INFO] Converting measurements from reference to specified'
                  ' cosmology.')

            self.cosmology = cosmology

            self._convert_to_cosmology()

    def _get_logphi_from_phi(self):

        self.log_phi = np.log10(self.phi)

    def _get_phi_from_logphi(self):

        self.phi = np.power(10, self.log_phi)

    def _get_sigma_logphi_from_sigma_phi(self):

        if self.sigma_phi.ndim == 1:
            s_logphi_low = np.log10(self.phi-self.sigma_phi) - self.log_phi
            s_logphi_upp = np.log10(self.phi+self.sigma_phi) - self.log_phi

            self.sigma_log_phi = np.abs(np.array([s_logphi_low, s_logphi_upp]))

        if self.sigma_phi.ndim == 2:

            s_logphi_low = np.log10(self.phi - self.sigma_phi[0, :]) \
                           - self.log_phi
            s_logphi_upp = np.log10(self.phi + self.sigma_phi[1, :]) \
                           - self.log_phi

            self.sigma_log_phi = np.abs(np.array([s_logphi_low, s_logphi_upp]))

    def _get_sigma_phi_from_sigma_logphi(self):

        if self.sigma_log_phi.ndim == 1:
            s_phi_low = 10**(-self.sigma_log_phi + self.log_phi) - self.phi
            s_phi_upp = 10**(self.sigma_log_phi + self.log_phi) - self.phi

            self.sigma_phi = np.abs(np.array([s_phi_low, s_phi_upp]))

        if self.sigma_log_phi.ndim == 2:
            s_phi_low = 10 ** (-self.sigma_log_phi[0, :] + self.log_phi) - \
                        self.phi
            s_phi_upp = 10 ** (self.sigma_log_phi[1, :] + self.log_phi) - \
                        self.phi

            self.sigma_phi = np.abs(np.array([s_phi_low, s_phi_upp]))

    def _convert_to_cosmology(self):

        # Luminosity conversion
        distmod_ref = self.ref_cosmology.distmod(self.redshift)
        distmod_cos = self.cosmology.distmod(self.redshift)

        # Convert luminosity according to new cosmology
        if self.lum_type in ['M1450']:
            self.lum = self.lum + distmod_ref.value - distmod_cos.value
        else:
            raise NotImplementedError('[ERROR] Conversions for luminosity '
                                      'type {} are not implemented.'.format(
                                      self.lum_type))

        # Convert density according to new cosmology
        # Note: number density scales as h^-3
        # phi
        phi_h_inv = self.phi * self.ref_cosmology.h**3
        self.phi = phi_h_inv / self.cosmology.h**3

        self._get_logphi_from_phi()
        # sigma_phi

        sigma_phi_inv = self.sigma_phi * self.ref_cosmology.h**3
        self.sigma_phi = sigma_phi_inv / self.cosmology.h**3

        self._get_sigma_logphi_from_sigma_phi()

