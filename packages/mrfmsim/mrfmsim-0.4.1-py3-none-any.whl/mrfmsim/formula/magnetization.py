import numba as nb
import numpy as np

HBAR = 1.054571628e-7  # aN nm s - reduced Planck constant
KB = 1.3806504e4  # aN nm K^{-1} - Boltzmann constant


@nb.jit(nopython=True, parallel=True)
def mz_eq(B_tot, Gamma, J, temperature):
    r"""Magnetization per spin at the thermal equilibrium using the Brillouin function.

    :param float B_tot: total magnetic field [mT]
    :param float Gamma: the gyromagnetic ratio [rad/s.mT]
    :param float J: total spin angular momentum
    :param float temperature: the spin temperature [K]
    :return: equilibrium per-spin magnetization [aN.nm/mT]

    The outputs are calculated from the sample properties

    .. math::
        J &= \text{spin angular momentum quantum number}\:
            [\mathrm{unitless}]\\
        \gamma & = \text{gyromagnetic ratio} \:
        [\mathrm{s}^{-1} \mathrm{mT}^{-1}] \\
        B_0 &= \text{applied magnetic field} \: [\mathrm{mT}] \\
        T &= \text{temperature} \: [\mathrm{K}] \\
        \rho &= \text{spin density} \: [\mathrm{nm}^{-1}]

    as follows. From the sample properties, we compute the magnetic moment
    :math:`\mu` of the state with the largest :math:`m_J` quantum number,

    .. math::
        \mu = \hbar\gamma J \: [\mathrm{aN} \: \mathrm{nm} \:
        \mathrm{mT}^{-1}]

    We calculate the ratio of the energy level splitting of spin states to
    the thermal energy,

    .. math::
        x = \dfrac{\mu B_0}{k_b T} \: [\mathrm{unitless}],

    and define the following two unitless numbers:

    .. math::
        a &= \dfrac{2 \: J + 1}{2 \: J} \\
        b &= \dfrac{1}{2 \: J}

    In terms of these intermediate quantities, the thermal-equilibrium
    polarization is given by

    .. math::
        p_{\text{eq}} = a \coth{(a x)} - b \coth{(b x)}
            \: [\mathrm{unitless}].

    The equilibrium magnetization is given by

    .. math::
        {\cal M}_{z}^{\text{eq}} =
            p_{\text{eq}} \: \mu \:
            [\mathrm{aN} \: \mathrm{nm} \: \mathrm{mT}^{-1}].

    In the limit of low field or high temperature,
    the equilibrium magnetization
    tends towards the Curie-Weiss law,

    .. math::
        {\cal M}_{z}^{\text{eq}}
        \approx \dfrac{\hbar^2 \gamma^2 \: J (J + 1)}{3 \: k_b T} B_0
    """

    mu_z = HBAR * Gamma * J  # aN nm s * rad/s mT = aN nm/mT
    x = (mu_z * B_tot) / (KB * temperature)  # unitless
    a = (2.0 * J + 1.0) / (2.0 * J)  # unitless
    b = 1.0 / (2.0 * J)  # unitless
    pol_eq = a / np.tanh(a * x) - b / np.tanh(b * x)
    return mu_z * pol_eq  # [aN.nm/mT]


def mz2_eq(Gamma, J):
    r"""Compute the magnetization variance per spin.

    :param float Gamma: the gyromagnetic ratio [rad/s.mT]
    :param float J: total spin angular momentum
    :return: magnetization variance per spin [aN^2.nm^2/mT^2]
    :rtype: float
    """

    mu = HBAR * Gamma * np.sqrt(J * (J + 1) / 3.0)  # aN.nm/mT
    return mu**2  # aN^2
