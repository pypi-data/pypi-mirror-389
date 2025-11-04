import numpy as np
import numba as nb
from dataclasses import dataclass, field
from mrfmsim.component import ComponentBase


@dataclass
class SphereMagnet(ComponentBase):
    """Spherical magnet object with its Bz, Bzx, Bzxx calculations.

    :param float magnet_radius: sphere magnet radius [nm]
    :param list magnet_origin: the position of the magnet origin
        :math:`(x, y, z)` [nm]
    :param float mu0_Ms: saturation magnetization [mT]
    """

    magnet_radius: float = field(metadata={"unit": "nm", "format": ".1f"})
    magnet_origin: list[float] = field(metadata={"unit": "nm", "format": ".1f"})
    mu0_Ms: float = field(metadata={"unit": "mT"})

    def Bz_method(self, x, y, z):
        r"""Calculate magnetic field :math:`B_z` [mT].

        :param float x: :math:`x` coordinate of sample grid [nm]
        :param float y: :math:`y` coordinate of sample grid [nm]
        :param float z: :math:`z` coordinate of sample grid [nm]

        The magnetic field is calculated as

        .. math::
            B_z = \dfrac{\mu_0 M_s}{3}
            \left( 3 \dfrac{Z^2}{R^5} - \dfrac{1}{R^3} \right)
            R = \sqrt{X^2+Y^2+Z^2}

        Here :math:`(x,y,z)` is the location at which we want to know the field;
        :math:`(x_0, y_0, z_0)` is the location of the center of the magnet;
        :math:`r` is the radius of the magnet; :math:`X = (x-x_0)/r`;
        :math:`Y = (y-y_0)/r`, and :math:`Z = (z-z_0)/r` are normalized
        distances to the center of the magnet;
        :math:`\mu_0 M_s` is the magnetic sphere's saturation
        magnetization in mT.
        """

        dx = (x - self.magnet_origin[0]) / self.magnet_radius
        dy = (y - self.magnet_origin[1]) / self.magnet_radius
        dz = (z - self.magnet_origin[2]) / self.magnet_radius

        pre_term = self.mu0_Ms / 3.0

        return pre_term * self._bz(dx, dy, dz)

    @staticmethod
    @nb.vectorize(
        [nb.float64(nb.float64, nb.float64, nb.float64)],
        nopython=True,
        target="parallel",
    )
    def _bz(dx, dy, dz):
        """Internal calculation for bz, optimized with numba.

        :param float dx: normalized distances to the center of the magnet in
            :math:`x` direction [nm]
        :param float dy: normalized distances to the center of the magnet in
            :math:`y` direction [nm]
        :param float dz: normalized distances to the center of the magnet in
            :math:`z` direction [nm]

        :return: bz without pre-term
        :rtype: float
        """

        return (
            -1.0 / np.sqrt(dx**2 + dy**2 + dz**2) ** 3
            + 3.0 * dz**2 / np.sqrt(dx**2 + dy**2 + dz**2) ** 5
        )

    def Bzx_method(self, x, y, z):
        r"""Calculate magnetic field gradient :math:`B_{zx}`.

        :math:`B_{zx} \equiv \partial B_z / \partial x`
        [ :math:`\mathrm{mT} \: \mathrm{nm}^{-1}` ].
        With :math:`X`, :math:`Y`, :math:`Z`, :math:`R`, :math:`r`, and
        :math:`\mu_0 M_s` defined in Bz(x, y, z), the magnetic field
        gradient is calculated as

        .. math::
            B_{zx} = \dfrac{\partial B_z}{\partial x}
            = \dfrac{\mu_0 M_s}{r} X \:
            \left( \dfrac{1}{R^5} - 5 \dfrac{Z^2}{R^7} \right)
            R = \sqrt{X^2+Y^2+Z^2}

        :param float x: :math:`x` coordinate of sample grid [nm]
        :param float y: :math:`y` coordinate of sample grid [nm]
        :param float z: :math:`z` coordinate of sample grid [nm]
        :return: magnetic field gradient
        :rtype: np.array
        """

        dx = (x - self.magnet_origin[0]) / self.magnet_radius
        dy = (y - self.magnet_origin[1]) / self.magnet_radius
        dz = (z - self.magnet_origin[2]) / self.magnet_radius
        pre_term = self.mu0_Ms / self.magnet_radius

        return pre_term * self._bzx(dx, dy, dz)

    @staticmethod
    @nb.vectorize(
        [nb.float64(nb.float64, nb.float64, nb.float64)],
        nopython=True,
        target="parallel",
    )
    def _bzx(dx, dy, dz):
        """Internal calculation for bzx, optimized with numba.

        :param float dx: normalized distances to the center of the magnet in
            :math:`x` direction [nm]
        :param float dy: normalized distances to the center of the magnet in
            :math:`y` direction [nm]
        :param float dz: normalized distances to the center of the magnet in
            :math:`z` direction [nm]

        :return: bzx without pre-term
        :rtype: float
        """

        return dx * (
            1.0 / np.sqrt(dx**2 + dy**2 + dz**2) ** 5
            - 5.0 * dz**2 / np.sqrt(dx**2 + dy**2 + dz**2) ** 7
        )

    def Bzxx_method(self, x, y, z):
        r"""Calculate magnetic field second derivative :math:`B_{zxx}`.

        :math:`B_{zxx} \equiv \partial^2 B_z / \partial x^2`
        [:math:`\mathrm{mT} \: \mathrm{nm}^{-2}`]. The inputs are
        With :math:`X`, :math:`Y`, :math:`Z`, :math:`R`, :math:`r`, and
        :math:`\mu_0 M_s` defined as above, the magnetic field
        second derivative is calculated as

        .. math::
            B_{zxx} = \dfrac{\partial^2 B_z}{\partial x^2}
            = \dfrac{\mu_0 M_s}{r^2} \:
            \left( \dfrac{1}{R^5} - 5 \dfrac{X^2}{R^7}
            - 5 \dfrac{Z^2}{R^7} + 35 \dfrac{X^2 Z^2}{R^9} \right)
            R = \sqrt{X^2+Y^2+Z^2}

        :param float x: :math:`x` coordinate of sample grid [nm]
        :param float y: :math:`y` coordinate of sample grid [nm]
        :param float z: :math:`z` coordinate of sample grid [nm]
        :return: magnetic field second derivative
        :rtype: np.array
        """

        dx = (x - self.magnet_origin[0]) / self.magnet_radius
        dy = (y - self.magnet_origin[1]) / self.magnet_radius
        dz = (z - self.magnet_origin[2]) / self.magnet_radius
        pre_term = self.mu0_Ms / (self.magnet_radius**2)

        return pre_term * self._bzxx(dx, dy, dz)

    @staticmethod
    @nb.vectorize(
        [nb.float64(nb.float64, nb.float64, nb.float64)],
        nopython=True,
        target="parallel",
    )
    def _bzxx(dx, dy, dz):
        """Internal calculation for bzxx, optimized with numba.

        :param float dx: normalized distances to the center of the magnet in
            :math:`x` direction [nm]
        :param float dy: normalized distances to the center of the magnet in
            :math:`y` direction [nm]
        :param float dz: normalized distances to the center of the magnet in
            :math:`z` direction [nm]

        :return: bzxx without pre-term
        :rtype: float
        """

        return (
            1.0 / np.sqrt(dx**2 + dy**2 + dz**2) ** 5
            - 5.0 * (dx**2) / np.sqrt(dx**2 + dy**2 + dz**2) ** 7
            - 5.0 * (dz**2) / np.sqrt(dx**2 + dy**2 + dz**2) ** 7
            + 35.0 * (dx**2) * (dz**2) / np.sqrt(dx**2 + dy**2 + dz**2) ** 9
        )


@dataclass
class RectangularMagnet(ComponentBase):
    """Rectangular magnet object with the bz, bzx, bzxx calculations.

    :param list magnet_length: length of rectangular magnet in
        :math:`(x, y, z)` direction [nm]
    :param list magnet_origin: the position of the magnet origin
        :math:`(x, y, z)` [nm]
    :param float mu0_Ms: saturation magnetization [mT]
    """

    magnet_length: list[float] = field(metadata={"unit": "nm", "format": ".1f"})
    magnet_origin: list[float] = field(metadata={"unit": "nm", "format": ".1f"})
    mu0_Ms: float = field(metadata={"unit": "mT"})

    def __post_init__(self):
        self._range = np.column_stack(
            (
                -np.array(self.magnet_length) / 2 + self.magnet_origin,
                np.array(self.magnet_length) / 2 + self.magnet_origin,
            )
        ).ravel()
        self._pre_term = self.mu0_Ms / (4 * np.pi)

    def Bz_method(self, x, y, z):
        r"""Calculate magnetic field :math:`B_z` [mT].

        The magnetic field is calculated following Ravaud2009 [#]_.

        The magnet is set up so that the
        :math:`x` and :math:`y`  dimensions are centered about the zero point. 
        The translation in :math:`z` shifts the tip of the magnet in the 
        :math:`z`-direction to be the given distance from the surface.

        Using the Coulombian model, assuming a uniform magnetization throughout
        the volume of the magnet and modeling each face of the magnet as a
        layer of continuous current density. The total field is found by
        summing over the faces.

        The magnetic field is given by:

        .. math::
            B_z = \dfrac{\mu_0 M_s}{4\pi} \sum_{i=1}^{2}
                \sum_{j=1}^2 \sum_{k=1}^2(-1)^{i+j+k}
                arctan \left( \dfrac{(x - x_i)(y - y_i))}{(z - z_k)R} \right)

        Here :math:`(x,y,z)` are the coordinates for the location at which we
        want to know the field;
        The magnet spans from x1 to x2 in the :math:`x`-direction,
        y1 to y2 in the :math:`y`-direction, and z1 to z2 in
        the :math:`z`-direction;

        .. math::
            R = \sqrt{(x - x_i)^2 + (y - y_j)^2 + (z - z_k)^2}

        where :math:`\mu_0 M_s` is the magnet's saturation magnetization in mT.

        .. [#] Ravaud, R. and Lemarquand, G. "Magnetic field produced by a
           parallelepipedic magnet of various and uniform polarization" ,
           *PIER*, **2009**, *98*, 207-219
           [`10.2528/PIER09091704 <http://dx.doi.org/10.2528/PIER09091704>`__].


        :param float x: :math:`x` coordinate of sample grid [nm]
        :param float y: :math:`y` coordinate of sample grid [nm]
        :param float z: :math:`z` coordinate of sample grid [nm]
        """

        dx1, dx2 = x - self._range[0], x - self._range[1]
        dy1, dy2 = y - self._range[2], y - self._range[3]
        dz1, dz2 = z - self._range[4], z - self._range[5]

        return self._pre_term * self._bz(dx1, dx2, dy1, dy2, dz1, dz2)

    @staticmethod
    @nb.vectorize(
        [
            nb.float64(
                nb.float64,
                nb.float64,
                nb.float64,
                nb.float64,
                nb.float64,
                nb.float64,
            )
        ],
        nopython=True,
        target="parallel",
    )
    def _bz(dx1, dx2, dy1, dy2, dz1, dz2):
        """Calculate the summation term for magnetic field optimized by numba.

        See method Bz_method for the explanation.

        :param float dx1: distance between grid and one end of magnet in
            :math:`x` direction [nm]
        :param float dx2: distance between grid and other end of magnet in
            :math:`x` direction [nm]
        :param float dy1: distance between grid and one end of magnet in
            :math:`y` direction [nm]
        :param float dy2: distance between grid and other end of magnet in
            :math:`y` direction [nm]
        :param float dz1: distance between grid and one end of magnet in
            :math:`z` direction [nm]
        :param float dz2: distance between grid and other end of magnet in
            :math:`z` direction [nm]
        """

        return (
            -np.arctan2(dx1 * dy1, (np.sqrt(dx1**2 + dy1**2 + dz1**2) * dz1))
            + np.arctan2(dx2 * dy1, (np.sqrt(dx2**2 + dy1**2 + dz1**2) * dz1))
            + np.arctan2(dx1 * dy2, (np.sqrt(dx1**2 + dy2**2 + dz1**2) * dz1))
            - np.arctan2(dx2 * dy2, (np.sqrt(dx2**2 + dy2**2 + dz1**2) * dz1))
            + np.arctan2(dx1 * dy1, (np.sqrt(dx1**2 + dy1**2 + dz2**2) * dz2))
            - np.arctan2(dx2 * dy1, (np.sqrt(dx2**2 + dy1**2 + dz2**2) * dz2))
            - np.arctan2(dx1 * dy2, (np.sqrt(dx1**2 + dy2**2 + dz2**2) * dz2))
            + np.arctan2(dx2 * dy2, (np.sqrt(dx2**2 + dy2**2 + dz2**2) * dz2))
        )

    def Bzx_method(self, x, y, z):
        r"""Calculate magnetic field gradient :math:`B_{zx}`.

        :math:`B_{zx} \equiv \partial B_z / \partial x`
        [:math:`\mathrm{mT} \: \mathrm{nm}^{-1}`].
        The magnetic field gradient
        :math:`B_{zx} = \dfrac{\partial{B_z}}{\partial x}` is
        given by the following:

        .. math::
           B_{zx} = \dfrac{\mu_0 M_s}{4 \pi} \sum_{i=1}^2 \sum_{j=1}^2
               \sum_{k=1}^2(-1)^{i+j+k}
               \left( \dfrac{(y-y_j)(z-z_k)}{ R((x-x_i)^2 + (z-z_k)^2))}
               \right)

        As described above, :math:`(x,y,z)` are coordinates for the location
        at which we want to know the field gradient; the magnet spans from
        x1 to x2 in the ``x``-direction, y1 to y2 in the ``y``-direction, and
        from z1 to z2 in the ``z``-direction;

        .. math::
            R = \sqrt{(x - x_i)^2 + (y - y_j)^2 + (z - z_k)^2}

        :math:`\mu_0 M_s` is the magnet's saturation magnetization in mT.

        :param float x: :math:`x` coordinate [nm]
        :param float y: :math:`y` coordinate [nm]
        :param float z: :math:`z` coordinate [nm]
        """

        dx1, dx2 = x - self._range[0], x - self._range[1]
        dy1, dy2 = y - self._range[2], y - self._range[3]
        dz1, dz2 = z - self._range[4], z - self._range[5]

        return self._pre_term * self._bzx(dx1, dx2, dy1, dy2, dz1, dz2)

    @staticmethod
    @nb.vectorize(
        [
            nb.float64(
                nb.float64,
                nb.float64,
                nb.float64,
                nb.float64,
                nb.float64,
                nb.float64,
            )
        ],
        nopython=True,
        target="parallel",
    )
    def _bzx(dx1, dx2, dy1, dy2, dz1, dz2):
        """Calculate the summation term for magnetic field gradient.

        Optimized with numba. See method Bzx_method for the explanation.

        :param float dx1: distance between grid and one end of magnet in
            :math:`x` direction [nm]
        :param float dx2: distance between grid and other end of magnet in
            :math:`x` direction [nm]
        :param float dy1: distance between grid and one end of magnet in
            :math:`y` direction [nm]
        :param float dy2: distance between grid and other end of magnet in
            :math:`y` direction [nm]
        :param float dz1: distance between grid and one end of magnet in
            :math:`z` direction [nm]
        :param float dz2: distance between grid and other end of magnet in
            :math:`z` direction [nm]
        """

        return (
            -dy1 * dz1 / (np.sqrt(dx1**2 + dy1**2 + dz1**2) * (dx1**2 + dz1**2))
            + dy1 * dz1 / (np.sqrt(dx2**2 + dy1**2 + dz1**2) * (dx2**2 + dz1**2))
            + dy2 * dz1 / (np.sqrt(dx1**2 + dy2**2 + dz1**2) * (dx1**2 + dz1**2))
            - dy2 * dz1 / (np.sqrt(dx2**2 + dy2**2 + dz1**2) * (dx2**2 + dz1**2))
            + dy1 * dz2 / (np.sqrt(dx1**2 + dy1**2 + dz2**2) * (dx1**2 + dz2**2))
            - dy1 * dz2 / (np.sqrt(dx2**2 + dy1**2 + dz2**2) * (dx2**2 + dz2**2))
            - dy2 * dz2 / (np.sqrt(dx1**2 + dy2**2 + dz2**2) * (dx1**2 + dz2**2))
            + dy2 * dz2 / (np.sqrt(dx2**2 + dy2**2 + dz2**2) * (dx2**2 + dz2**2))
        )

    def Bzxx_method(self, x, y, z):
        r"""Calculate magnetic field second derivative :math:`B_{zxx}`.

        :math:`B_{zxx} \equiv \partial^2 B_z / \partial x^2`
        [ :math:`\mathrm{mT} \; \mathrm{nm}^{-2}`]
        The magnetic field's second derivative is given by the following:

        .. math::
           B_{zxx} = \dfrac{\partial^2 B_z}{\partial x^2}
               = \dfrac{\mu_0 M_s}{4 \pi} \sum_{i=1}^2
                   \sum_{j=1}^2 \sum_{k=1}^2(-1)^{i+j+k}
                   \left( \dfrac{-(x-x_i)(y-y_j)(z-z_k)
                   (3(x-x_i)^2 +2(y-y_j)^2 + 3(z-z_k)^2)}
                   {((x-x_i)^2 + (y-y_j)^2 + (z-z_k)^2)^{3/2}
                   ((x-x_i)^2 + (z-z_k)^2)^2} \right)

        with the variables defined above.

        :param float x: :math:`x` coordinate [nm]
        :param float y: :math:`y` coordinate [nm]
        :param float z: :math:`z` coordinate [nm]
        """

        dx1, dx2 = x - self._range[0], x - self._range[1]
        dy1, dy2 = y - self._range[2], y - self._range[3]
        dz1, dz2 = z - self._range[4], z - self._range[5]

        return self._pre_term * self._bzxx(dx1, dx2, dy1, dy2, dz1, dz2)

    @staticmethod
    @nb.vectorize(
        [
            nb.float64(
                nb.float64,
                nb.float64,
                nb.float64,
                nb.float64,
                nb.float64,
                nb.float64,
            )
        ],
        nopython=True,
        target="parallel",
    )
    def _bzxx(dx1, dx2, dy1, dy2, dz1, dz2):
        """The summation term for the second derivative of magnetic field.

        Optimized by numba. See Bzxx_method for the explanation.

        :param float dx1: distance between grid and one end of magnet in
            :math:`x` direction [nm]
        :param float dx2: distance between grid and other end of magnet in
            :math:`x` direction [nm]
        :param float dy1: distance between grid and one end of magnet in
            :math:`y` direction [nm]
        :param float dy2: distance between grid and other end of magnet in
            :math:`y` direction [nm]
        :param float dz1: distance between grid and one end of magnet in
            :math:`z` direction [nm]
        :param float dz2: distance between grid and other end of magnet in
            :math:`z` direction [nm]
        """

        return (
            +dx1
            * dy1
            * dz1
            * (3.0 * dx1**2 + 2.0 * dy1**2 + 3.0 * dz1**2)
            / ((dx1**2 + dy1**2 + dz1**2) ** 1.5 * (dx1**2 + dz1**2) ** 2)
            - dx2
            * dy1
            * dz1
            * (3.0 * dx2**2 + 2.0 * dy1**2 + 3.0 * dz1**2)
            / ((dx2**2 + dy1**2 + dz1**2) ** 1.5 * (dx2**2 + dz1**2) ** 2)
            - dx1
            * dy2
            * dz1
            * (3.0 * dx1**2 + 2.0 * dy2**2 + 3.0 * dz1**2)
            / ((dx1**2 + dy2**2 + dz1**2) ** 1.5 * (dx1**2 + dz1**2) ** 2)
            + dx2
            * dy2
            * dz1
            * (3.0 * dx2**2 + 2.0 * dy2**2 + 3.0 * dz1**2)
            / ((dx2**2 + dy2**2 + dz1**2) ** 1.5 * (dx2**2 + dz1**2) ** 2)
            - dx1
            * dy1
            * dz2
            * (3.0 * dx1**2 + 2.0 * dy1**2 + 3.0 * dz2**2)
            / ((dx1**2 + dy1**2 + dz2**2) ** 1.5 * (dx1**2 + dz2**2) ** 2)
            + dx2
            * dy1
            * dz2
            * (3.0 * dx2**2 + 2.0 * dy1**2 + 3.0 * dz2**2)
            / ((dx2**2 + dy1**2 + dz2**2) ** 1.5 * (dx2**2 + dz2**2) ** 2)
            + dx1
            * dy2
            * dz2
            * (3.0 * dx1**2 + 2.0 * dy2**2 + 3.0 * dz2**2)
            / ((dx1**2 + dy2**2 + dz2**2) ** 1.5 * (dx1**2 + dz2**2) ** 2)
            - dx2
            * dy2
            * dz2
            * (3.0 * dx2**2 + 2.0 * dy2**2 + 3.0 * dz2**2)
            / ((dx2**2 + dy2**2 + dz2**2) ** 1.5 * (dx2**2 + dz2**2) ** 2)
        )
