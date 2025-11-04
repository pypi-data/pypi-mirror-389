#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Peter Sun

"""Collection of calculations of relative changes in polarization."""

import numba
import numpy as np
from .math import as_strided_x
from .field import B_offset

HBAR = 1.054571628e-7  # aN nm s - reduced Planck constant
KB = 1.3806504e4  # aN nm K^{-1} - Boltzmann constant


@numba.jit(nopython=True, parallel=True)
def rel_dpol_sat_steadystate(B_offset, B1, dB_sat, dB_hom):
    r"""Relative change in polarization for steady-state.

    Compute and return the sample's *relative* steady-state spin
    polarization. As given by the Bloch equations,

    .. math::
        \Delta\rho_{\text{rel}} = \dfrac{\Delta {\cal M}_z}
        {{\cal M}_{z}^{\text{eq}}} = - \dfrac{(B_1 / \Delta B_{\text{sat}})^2}
        {1 + (\Delta B_{\text{offset}} / \Delta B_{\text{homog}})^2 +
            (B_1 / \Delta B_{\text{sat}})^2}

    At resonance,

    .. math::
        \rho_{\text{rel}} = \dfrac{S}{1+S}

    and the change in polarization is governed by the *saturation factor*

    .. math::
        S = (B_1 / \Delta B_{\text{sat}})^2

    :math:`\rho_{\text{rel}}` under irradiation.

    :param float dB_hom: the homogeneous linewidth
        :math:`\Delta B_{\text{homog}}` [mT]
    :param float dB_sat: the saturation linewidth
        :math:`\Delta B_{\text{sat}}` [mT]
    :param float B_offset: resonant offset
        :math:`\Delta B_{\text{offset}}` [mT]
    :param float B_1: the amplitude of the applied transverse field
        :math:`B_1` [mT]
    :return: relative polarization
    :rtype: np.array, the same shape as B_offset
    """

    s2_term = (B1**2) / (dB_sat**2)  # S-squared term

    return -1 * s2_term / (1 + B_offset**2 / dB_hom**2 + s2_term)


@numba.jit(nopython=True, parallel=True)
def rel_dpol_ibm_cyclic(B_offset, df_fm, Gamma):
    r"""Relative change in polarization for IBM adiabatic rapid passage.

    .. math::
        \eta \, (\Delta B_{\text{offset}}) = \begin{cases}
         \cos^2 \left(\dfrac{\gamma \Delta B_{\text{offset}}}
         {2 \: \Delta f_{\text{FM}}} \right) & \text{for }
         \Delta B_{\text{offset}}
         \leq \pi \Delta f_{\text{FM}} / \gamma, \\
         0 & \text{otherwise.} \end{cases}

    with

    .. math::
        \Delta B_{\text{offset}} = B_0 - 2 \pi f_{\text{rf}} / \, \gamma
        [\mathrm{mT}]

    The result added in pol_arp
    the negative sign for it is the signal of final - initial.

    :param float Gamma: the gyromagnetic ratio [rad/s.mT]
    :param float B_offset: resonant offset
        :math:`\Delta B_{\text{offset}}` [mT]
    :param float df_fm: the peak-to-peak frequency modulation
        :math:`\Delta df_{\text{FM}}` of the applied transverse
        radio frequency magnetic field [Hz]
    :return: relative change in polarization
    :rtype: np.array, the same shape as B_offset
    """

    b_crit = np.pi * df_fm / Gamma
    pol_arp = -np.cos(B_offset * Gamma / (2.0 * df_fm)) ** 2

    # enforce the limit of b_offset, if b_offset > b_crit or
    # b_offset < - b_crit, the polarization is 0
    return (np.abs(B_offset) < b_crit) * pol_arp


@numba.jit(nopython=True, parallel=True)
def rel_dpol_arp(B_offset, B1, df_fm, Gamma):
    r"""Relative change in polarization for adiabatic rapid passage.

    Compute the resonance offset at each point in the sample and compute
    the change in the polarization at each point in the sample following the
    adiabatic rapid passage. The experiment here is a swept-field experiment
    or a swept-tip experiment, where

    .. math::
        \Delta B_\text{offset} =
        B_0 + B_\text{tip} - 2 \pi f_\text{rf}/\gamma

    and

    .. math::
        \Omega_\text{initial} = B_0 + B_\text{tip} -
        (2 \pi f_\text{rf}/\gamma - 2 \pi \Delta f_\text{FM}/\gamma)
        = \Delta B_\text{offset} + 2 \pi \Delta f_\text{FM} / \gamma

    :param float Gamma: the gyromagnetic ratio [rad/s.mT]
    :param float B_offset: resonance offset field :math:`\Delta B_{\text{offset}}` [mT]
    :param float B_1: amplitude :math:`B_1` of the applied transverse field [mT]
    :param float df_fm: the peak-to-peak frequency modulation :math:`\Delta f_{\text{FM}}`
        of the applied transverse radio frequency magnetic field [Hz]
    :return: relative change in polarization
    :rtype: np.array, the same shape as B_offset
    """

    om_i = (B_offset + 2 * np.pi * df_fm / (2.0 * Gamma)) / B1
    om_f = (B_offset - 2 * np.pi * df_fm / (2.0 * Gamma)) / B1

    return om_i * om_f / np.sqrt((om_i * om_i + 1.0) * (om_f * om_f + 1.0)) - 1.0


@numba.jit(nopython=True, parallel=True)
def rel_dpol_periodic_irrad(B_offset, B1, dB_sat, dB_hom, T1, t_on, t_off):
    r"""Relative change in polarization for intermittent irradiation.

    .. math::
        \langle \Delta M_z \rangle = - \frac{S^2 \, M_0}{1 + S^2 + \Omega^2}
        \left(\frac{1}{r_1} \frac{1}{\tau_\text{on}+\tau_\text{off}}
        \frac{(1 - E_\text{on})(1 - E_\text{off})}
        {1 - E_\text{on} \, E_\text{off}}
        \frac{S^2}{1 + S^2 + \Omega^2} + \frac{\tau_\text{on}}
         {\tau_\text{on}+\tau_\text{off}}\right)

    :param float dB_hom: the homogeneous linewidth [mT]
    :param float dB_sat: the saturation linewidth [mT]
    :param float B_offset: resonant offset
        :math:`\Delta B_{\text{offset}}` [mT]
    :param float B_1: the amplitude
        :math:`B_1` of the applied transverse field [mT]
    :param float t_1: spin-lattice relaxation [s]
    :param float t_on: time with the microwaves on [s]
    :param float t_off: time with the microwaves off [s]
    :return: relative change in polarization
    :rtype: np.array, the same shape as B_offset
    """

    r1 = 1 / T1
    s2_term = B1**2 / dB_sat**2  # S-squared term

    e_on = np.exp(-r1 * t_on * (1 + s2_term / (1 + B_offset**2 / dB_hom**2)))
    e_off = np.exp(-r1 * t_off)
    ratio = s2_term / (1 + B_offset**2 / dB_hom**2 + s2_term)

    return -ratio * (
        (1 / r1)
        * (1 / (t_off + t_on))
        * (1 - e_on)
        * (1 - e_off)
        / (1 - e_on * e_off)
        * ratio
        + t_on / (t_on + t_off)
    )


@numba.jit(nopython=True, parallel=True)
def rel_dpol_nut(B_offset, B1, Gamma, t_p):
    r"""Relative change in polarization under the evolution of irradiation.

    Equations:

    .. math::
        \rho_{\mathrm{rel}} = \frac{\Delta M_{z}}{M_{z}(0)}
        = \frac{1}{\Omega^2+1}
        (1 + \cos{(\Omega_1 t_p \sqrt{\Omega^2+1})})

    with

    .. math::
        \Delta B_{\mathrm{offset}} = B_z(\vec{r}) - \omega/\gamma

    the resonance offset field and

    .. math::
        \Omega_1 = \gamma B_1

    .. math::
        \Omega = \frac{\Delta B_{\mathrm{offset}}}{B_1}

    the unitless resonance offset.

    :param float Gamma: the gyromagnetic ratio. [rad/s.mT]
    :param float B_offset: resonance offset field
        :math:`\Delta B_{\text{offset}}` [mT]
    :param float B_1: amplitude of the applied transverse field
        :math:`B_{\text{1}}` [mT]
    :param float t_p: pulse time :math:`t_{\mathrm{p}}` [s]
    :return: relative polarization
    :rtype: np.array, the same shape as B_offset
    """
    omega_term = (B_offset / B1) ** 2 + 1
    theta = B1 * Gamma * t_p
    rel_dpol = np.cos(theta * np.sqrt(omega_term)) / omega_term - 1

    return rel_dpol


@numba.jit(nopython=True, parallel=True)
def rel_dpol_nut_multi_freq_pulse(B_tot, B1, f_rf_array, Gamma, t_p):
    """Nutation experiments where different frequencies are applied in steps.

    The polarization is aggregated as a product.
    """
    pol = np.ones(B_tot.shape)
    for f_rf in f_rf_array:
        b_offset = B_offset(B_tot, f_rf, Gamma)
        pol *= rel_dpol_nut(b_offset, B1, Gamma, t_p) + 1

    return pol - 1


def rel_dpol_sat_td(Bzx, B1, ext_B_offset, ext_pts, Gamma, T2, tip_v):
    """Relative change in polarization for time-dependent saturation.

    The result is not a steady-state solution because it ignores T1 relaxation.
    In the case where Bzx is 0, and B_offset is symmetric, the division will be nan.
    Here we try to adjust the nan values to the average of the surrounding values.
    However, if the resulting value is still nan or there are nan values at the boundary,
    an ValueError is raised.
    """
    # ignore division error the Exp takes care of the inf, and nan
    np.seterr(divide="ignore", invalid="ignore")

    omega_offset_atan = np.arctan(ext_B_offset * Gamma * T2)

    atan_omega_i = omega_offset_atan[: -ext_pts * 2]
    atan_omega_f = omega_offset_atan[ext_pts * 2 :]

    div = np.divide(atan_omega_f - atan_omega_i, Bzx)

    # adjust the nan values to the average of the surrounding values in x direction
    for idx in np.where(np.isnan(div))[0]:

        if idx == 0 or idx == len(div) - 1:
            raise ValueError(
                "Nan values at the boundary, check the Bzx and B_offset values."
            )
        value = (div[idx + 1] + div[idx - 1]) / 2

        # value can be a value or an array
        if np.any(np.isnan(value)):
            raise ValueError(
                "Nan value from division, check the Bzx and B_offset values."
            )
        div[idx] = value

    rt = Gamma * B1**2 * np.abs(div) / tip_v
    dpol = np.exp(-rt)

    return dpol - 1


def rel_dpol_sat_td_smallsteps(B1, ext_Bzx, ext_B_offset, ext_pts, Gamma, T2, tip_v):
    """Small step approximation of the time-dependent relative change in polarization."""
    # ignore division error
    np.seterr(divide="ignore", invalid="ignore")
    omega_offset_atan = np.arctan(ext_B_offset * Gamma * T2)

    # Using strides is faster than convolution on large datasets
    offset_atan_diff = np.diff(omega_offset_atan, axis=0)
    Bzx_rmean = as_strided_x(ext_Bzx, 2).mean(axis=1)

    f_array = np.nan_to_num(np.abs((offset_atan_diff) / Bzx_rmean))
    f_array_sum = as_strided_x(f_array, ext_pts * 2).sum(axis=1)

    rt = Gamma * B1**2 * f_array_sum / tip_v

    dpol = np.exp(-rt)

    return dpol - 1


def rel_dpol_multipulse(rel_dpol, T1, dt_pulse):
    """Calculate the average relative change in polarization after multiple pulses.

    The formula ignores relaxation during pulses.
    :param float dt_pulse: time between pulses
    """

    pol = rel_dpol + 1

    t_r = dt_pulse / T1
    rel_dpol_avg = (np.exp(t_r) - 1) * rel_dpol / t_r / (np.exp(t_r) - pol)

    return rel_dpol_avg
