
import numpy as np
import matplotlib.pyplot as plt

from qsopop import qlf



def verification_plots_kulkarni2019QLF():

    # plot_defaults.set_paper_defaults()

    lf = qlf.Kulkarni2019QLF()

    redshifts = np.linspace(0, 7, 200)
    lum = -27

    main_parameters = np.zeros((4, len(redshifts)))

    for idx, redsh in enumerate(redshifts):

        params = lf.evaluate_main_parameters(lum, redsh)
        main_parameters[0, idx] = params['phi_star']
        main_parameters[1, idx] = params['lum_star']
        main_parameters[2, idx] = params['alpha']
        main_parameters[3, idx] = params['beta']

    # Set up figure
    fig = plt.figure(num=None, figsize=(6, 4), dpi=120)
    fig.subplots_adjust(left=0.13, bottom=0.15, right=0.87, top=0.92,
                        hspace=0.3, wspace=0.3)

    ax1 = fig.add_subplot(2, 2, 1)
    ax1.plot(redshifts, np.log10(main_parameters[0, :]))
    ax1.set_xlabel(r'$\rm{Redshift}$', fontsize=12)
    ax1.set_ylabel(r'$\log (\Phi^*/\rm{mag}^{-1}\rm{cMpc}^{-3})$', fontsize=12)

    ax2 = fig.add_subplot(2, 2, 2)
    ax2.plot(redshifts, main_parameters[1, :])
    ax2.set_xlabel(r'$\rm{Redshift}$', fontsize=12)
    ax2.set_ylabel(r'$M_{1450}^*$', fontsize=12)

    ax3 = fig.add_subplot(2, 2, 3)
    ax3.plot(redshifts, main_parameters[2, :])
    ax3.set_xlabel(r'$\rm{Redshift}$', fontsize=12)
    ax3.set_ylabel(r'$\alpha$', fontsize=12)

    ax4 = fig.add_subplot(2, 2, 4)
    ax4.plot(redshifts, main_parameters[3, :])
    ax4.set_xlabel(r'$\rm{Redshift}$', fontsize=12)
    ax4.set_ylabel(r'$\beta$', fontsize=12)

    lum = np.linspace(-32, -19, 200)
    redshifts = [4.4, 5.1, 6.0, 7.0]

    # Set up figure
    fig2 = plt.figure(num=None, figsize=(6, 4), dpi=120)
    fig2.subplots_adjust(left=0.13, bottom=0.15, right=0.87, top=0.92)

    ax = fig2.add_subplot(1, 1, 1)

    ax.plot(lum, np.log10(lf(lum, redshifts[0])), label='z=4.4')
    ax.plot(lum, np.log10(lf(lum, redshifts[1])), label='z=5.1')
    ax.plot(lum, np.log10(lf(lum, redshifts[2])), label='z=6.0')
    ax.plot(lum, np.log10(lf(lum, redshifts[3])), label='z=7.0')

    ax.set_xlabel(r'$M_{1450}$', fontsize=14)
    ax.set_ylabel(r'$\log (\Phi/\rm{mag}^{-1}\rm{cMpc}^{-3})$', fontsize=14)
    ax.set_xlim(-19, -32)
    ax.set_ylim(-12, -4)
    ax.legend(fontsize=12)

    plt.show()


def verification_plots_richards2006QLF():

    # plot_defaults.set_paper_defaults()

    lf = qlf.Richards2006QLF()

    # Set up figure
    fig = plt.figure(num=None, figsize=(6, 4), dpi=120)
    fig.subplots_adjust(left=0.13, bottom=0.15, right=0.87, top=0.92,
                        hspace=0.3, wspace=0.3)

    lum = np.arange(-30, -24, 0.1)

    redsh = 2.01
    ax1 = fig.add_subplot(2, 2, 1)
    ax1.plot(lum, np.log10(lf(lum, redsh)))
    ax1.set_xlabel(r'$\rm{Redshift}$', fontsize=12)
    ax1.set_ylabel(r'$\log (\Phi^*/\rm{mag}^{-1}\rm{cMpc}^{-3})$', fontsize=12)


    redsh = 0.49
    ax1.plot(lum, np.log10(lf(lum, redsh)))

    redsh = 5.0
    ax1.plot(lum, np.log10(lf(lum, redsh)))

    redsh = 2.4
    ax2 = fig.add_subplot(2, 2, 2)
    ax2.plot(lum, np.log10(lf(lum, redsh)))
    ax2.set_xlabel(r'$\rm{Redshift}$', fontsize=12)
    ax2.set_ylabel(r'$\log (\Phi^*/\rm{mag}^{-1}\rm{cMpc}^{-3})$', fontsize=12)

    redsh = 2.8
    ax3 = fig.add_subplot(2, 2, 3)
    ax3.plot(lum, np.log10(lf(lum, redsh)))
    ax3.set_xlabel(r'$\rm{Redshift}$', fontsize=12)
    ax3.set_ylabel(r'$\log (\Phi^*/\rm{mag}^{-1}\rm{cMpc}^{-3})$', fontsize=12)

    redsh = 3.25
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.plot(lum, np.log10(lf(lum, redsh)))
    ax4.set_xlabel(r'$\rm{Redshift}$', fontsize=12)
    ax4.set_ylabel(r'$\log (\Phi^*/\rm{mag}^{-1}\rm{cMpc}^{-3})$', fontsize=12)

    plt.show()


    # Set up figure
    fig = plt.figure(num=None, figsize=(6, 4), dpi=120)
    fig.subplots_adjust(left=0.13, bottom=0.15, right=0.87, top=0.92,
                        hspace=0.3, wspace=0.3)

    redshifts = np.arange(0.5, 5, 0.01)
    qso_density = np.zeros_like(redshifts)
    mlow = -31
    mupp = -26

    for idx, redsh in enumerate(redshifts):

        qso_density[idx] = lf.integrate_lum(redsh, [mlow, mupp]) / 1e-9

    ax = fig.add_subplot(1, 1, 1)
    ax.plot(redshifts, qso_density)
    ax.semilogy()
    ax.set_ylabel(r'$n\,(M_{1450}<-26,z)\ (\rm{cGpc}^{-3})$',
                  fontsize=15)
    ax.set_xlabel(r'$\rm{Redshift}$', fontsize=15)
    plt.show()
