# -*- coding: utf-8 -*-
"""
This script demonstrates non-linear least-square fitting using scipy module
The example is based on the docstring of the curve_fit function
"""
from constants import BAR_Y_COLOR, BAR_Y_TICKNESS, CM_SIG_DIGITS, CM_SIG_DIGITS_NO_ERROR, MODEL_NUMPOINTS, REPORT_FONT, REPORT_SIZE, SIGNIFICANT_DIGITS, SORT_RESIDUALS, TICK_COLOR, XERRORWARNING
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from curvefitgui import curve_fit_gui
import configparser

def compare_to_scipy():
    #define the fitting function
    def myfunc(x, a, b, c):
        return a * np.exp(-b * x) + c

    #define some data
    rng = np.random.default_rng()
    xdata = np.linspace(0, 4, 50)
    ydata = myfunc(xdata, 2.5, 1.3, 0.5)
    ydata = ydata + rng.normal(0, 0.2, size=xdata.size)  #add some noise
    yerr = np.ones_like(ydata) * 0.2

    #perform the fit. The function is passed as an argument
    a0, b0, c0 = 3, 2, 1  #make an initial guess of fit parameters
    popt, pcov = curve_fit(myfunc, xdata, ydata, sigma=yerr, p0=[a0, b0, c0], absolute_sigma=True)
    print('fitpar:', popt)
    print('std.dev.:', np.sqrt(np.diag(pcov)))    
    popt, pcov = curve_fit_gui(myfunc, xdata, ydata, p0=[a0, b0, c0], sigma=yerr,  absolute_sigma=True)
    print('fitpar:', popt)
    print('std.dev.:', np.sqrt(np.diag(pcov)))    

def check_value_to_string():
    from tools import value_to_string
    name = 'x'
    value = 0.0001
    error = 23.456
    fixed = False
    latex = value_to_string(name, value, error, fixed)
    plt.plot([],[])
    plt.text(0,0,latex)
    plt.show()


def config_reader():
    config = configparser.ConfigParser()
    config.read('config.txt')
    print(config.sections())
    # general
    MODEL_NUMPOINTS = int(config['general']['MODEL_NUMPOINTS'])
    SIGNIFICANT_DIGITS = int(config['general']['SIGNIFICANT_DIGITS'])
    XERRORWARNING = config.getboolean('general','XERRORWARNING')
    SORT_RESIDUALS = config.getboolean('general','SORT_RESIDUALS')
    
    # fitparameters
    CM_SIG_DIGITS = int(config['fitparameter']['CM_SIG_DIGITS'])
    CM_SIG_DIGITS_NO_ERROR = int(config['fitparameter']['CM_SIG_DIGITS_NO_ERROR'])

    # reportview
    REPORT_FONT = config['reportview']['REPORT_FONT']
    REPORT_SIZE = int(config['reportview']['REPORT_SIZE'])

    # ticklabels
    TICK_COLOR = config['ticklabels']['TICK_COLOR']
    TICK_FONT = config['ticklabels']['TICK_FONT']
    TICK_SIZE = int(config['ticklabels']['TICK_SIZE'])

    # text
    TEXT_FONT = config['text']['TEXT_FONT']
    TEXT_SIZE = int(config['text']['TEXT_SIZE'])

    # errorbars
    BAR_Y_COLOR = config['errorbars']['BAR_Y_COLOR']
    BAR_X_COLOR = config['errorbars']['BAR_X_COLOR']
    BAR_Y_THICKNESS = int(config['errorbars']['BAR_Y_THICKNESS'])
    BAR_X_THICKNESS = int(config['errorbars']['BAR_X_THICKNESS'])


#compare_to_scipy()    
#check_value_to_string()
config_reader()