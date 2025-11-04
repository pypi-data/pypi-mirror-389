import math
import numpy as np
import scipy.special
from functools import reduce

HBAR = 1.054571628e-7  # aN nm s - reduced Planck constant


def convert_grid_pts(distance, grid_step):
    """Convert distance to ext points.

    :param float distance: distance in the :math:`x` direction [nm]
    :param list[float] grid_step: grid step size [nm]
    :return: number of grid points
    :rtype: int
    """
    return math.floor(distance / grid_step[0])


def singlespin_analytical(
    Gamma, geometry, J, magnet_spin_dist, magnet_origin, magnet_radius, mu0_Ms, x_0p
):
    r"""The analytical calculation for a single spin.

    The analytical solution to the exact equations for the delta k
    without any approximations as derived below:
    :math:`\Delta f = - \frac{f}{k x_{pk}^2} \langle F_{ts} x \rangle`
    where :math:`x_{pk}` is the zero-to-peak amplitude of the cantilever.
    This equation can be expressed as an integral over an angle
    :math:`\theta`
    For the *hangdown* geometry,

    .. math::
        F_{ts} = \mu_z \mu_0 M r^3 \dfrac{x^3 - 4z^2x}{(z^2 + x^2)^{7/2}}

    For the *SPAM* geometry,
    :math:`F_{ts} = \dfrac{\mu_z \mu_0 M r^3 x}{(x^2 + y^2)^{5/2}}`
    where :math:`\mu_z` is the spin magnetic moment, :math:`\mu_0 M` is
    the saturation magnetization of the tip, and r is the tip radius.

    .. math::
        \Delta f =  \frac{f}{2 \pi k x_{pk}^2} \int_{-\pi}^{\pi}
        \mu(x,y,z,\theta) \times \frac{\partial B_{z}^{\mathrm{tip}}
        (x-x_{pk}\cos \theta, y, z)}{\partial x} x_{pk}\cos \theta d\theta

    Substituting into the integral and introducing a unitless variable
    :math:`\hat{z} = z/x_{peak}` for the *hangdown* geometry and
    :math:`\hat{y}/x_{peak}` for the SPAM geometry,
    we obtain the following integrals:

    .. math::
        \Delta f = \frac{f}{2 k x_{pk}}\frac{\mu_z \mu_0 M}{a}
        (\frac{a}{z})^4 \times \frac{\bar{z}^4}{\pi}
        \int_0^{2\pi} \frac{\cos^4 \theta - 4\hat{z}^2\cos^2\theta}
        {(\hat{z}^2 + \cos^2\theta)^{7/2}} d\theta

    This integral (along with the :math:`\frac{\hat{z}^4}{\pi}` prefactor)
    can be solved exactly in Mathematica to give a solution in terms of
    Elliptic Integrals

    .. math::
        \frac{\hat{z}^3}{3\pi(\hat{z}^2 +1)}(4(2\hat{z}^4 -
        7\hat{z}^2 -1)E(-1/\hat{z}^2) -8(\hat{z}^4 - 1)K(-1/\hat{z}^2))

    where :math:`K(m)` and :math:`E(m)` are, respectively,
    the complete elliptic integrals of the first and second kind.
    For the *SPAM* geometry,

    .. math::
        \Delta f = \frac{f}{2 k x_{pk}} \frac{\mu_z \mu_0 M}
        {z} \left(\frac{a}{y}\right)^4 \times \frac{\hat{z}^4}{\pi}
        \int_0^{2\pi}\frac{\cos^2 \theta}{(\cos^2 \theta +
        \hat{y}^2)^{5/2}}d\theta

    This integral (along with the :math:`\frac{\hat{y}^4}{\pi}` prefactor
    can be solved exactly in terms of Elliptic integrals:

    .. math::
        \frac{4\hat{y}^3}{3\pi(1+\hat{y}^2)^2}[(1+\hat{y}^2)E(-1/\hat{y}^2)
        - (\hat{y}^2 -1)K(-1/\hat{y}^2)

    :param float Gamma: the gyromagnetic ratio [rad/s.mT]
    :param str geometry: experiment geometry ('spam' or 'hangdown')
    :param float J: the spin angular momentum
    :param float magnet_spin_dist: magnet-spin distance [nm]
    :param list magnet_origin: the origin of the magnet [nm]
    :param float magnet_radius: the radius of the magnet [nm]
    :param float mu0_Ms: the saturation magnetization of the magnet [mT]
    :param float x_0p: zero-to-peak amplitude of the cantilever [nm]

    :return: The analytical solution for a single spin (effective force) [aN].
        The spin constant shift is the effective force divided by the 0 to peak amplitude.
    :rtype: float
    """

    mu_z = HBAR * Gamma * J

    if geometry.lower() == "spam":
        origin_sample_distance = magnet_origin[1] + magnet_spin_dist
        Y = origin_sample_distance / x_0p
        val = -1.0 / Y**2
        ek = scipy.special.ellipk(val)
        ee = scipy.special.ellipe(val)

        I_term = (
            4.0
            * Y**3
            / (3.0 * np.pi * (1.0 + Y**2) ** 2)
            * ((1.0 + Y**2) * ek - (Y**2 - 1.0) * ee)
        )

    elif geometry.lower() == "hangdown":
        origin_sample_distance = magnet_origin[2] + magnet_spin_dist
        Z = origin_sample_distance / x_0p
        val = -1.0 / Z**2
        ek = scipy.special.ellipk(val)
        ee = scipy.special.ellipe(val)

        I_term = (
            Z**3
            / (3.0 * np.pi * (1 + Z**2) ** 3)
            * (4.0 * (2.0 * Z**4 - 7.0 * Z**2 - 1.0) * ee - 8.0 * (Z**4 - 1.0) * ek)
        )

    else:
        raise ValueError("Invalid geometry")

    const_term = -(
        mu0_Ms * mu_z / magnet_radius * (magnet_radius / origin_sample_distance) ** 4
    )

    # Assuming the spin is completely saturated, from 1 to 0
    # polarization change is -1, hence the negative sign.
    dF_spin = -const_term * I_term

    return dF_spin


def sum_of_product(*args):
    """Calculate the sum of the product input values.

    The args can be a list of values since NumPy multiple can calculate
    the value.
    """
    return np.sum(reduce(np.multiply, args))


def neg_sum_of_product(*args):
    """Calculate the negative sum of the product input values.

    The args can be a list of values, since numpy multiple can calculate
    the value. The function is used to simplify the definition in some of
    the experiments. The approximation of the signal results in a negative
    sign at the front.
    """
    return -np.sum(reduce(np.multiply, args))
