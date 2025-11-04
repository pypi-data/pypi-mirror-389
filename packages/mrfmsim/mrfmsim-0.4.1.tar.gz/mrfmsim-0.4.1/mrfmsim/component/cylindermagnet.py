import numpy as np
import numba as nb
from dataclasses import dataclass, field
from mrfmsim.component import ComponentBase


@dataclass
class CylinderMagnetApprox(ComponentBase):
    """Cylinder magnet object approximated by Rectangular Magnets.

    :param float magnet_radius: cylinder magnet radius [nm]
    :param float magnet_length: cylinder magnet length [nm]
    :param tuple magnet_origin: the position of the magnet origin
        :math:`(x, y, z)` [nm]
    :param float mu0_Ms: saturation magnetization [mT]
    """

    magnet_radius: float = field(metadata={"unit": "nm", "format": ".1f"})
    magnet_length: float = field(metadata={"unit": "nm", "format": ".1f"})
    magnet_origin: tuple[float, float, float] = field(
        metadata={"unit": "nm", "format": ".1f"}
    )
    mu0_Ms: float = field(metadata={"unit": "mT"})

    def __post_init__(self):
        d = self.magnet_radius / 10

        self._range = np.array(
            [
                [
                    self.magnet_origin[0] - 3 * d,
                    self.magnet_origin[0] + 3 * d,
                    self.magnet_origin[1] - 10 * d,
                    self.magnet_origin[1] + 10 * d,
                    self.magnet_origin[2] - self.magnet_length / 2,
                    self.magnet_origin[2] + self.magnet_length / 2,
                ],
                [
                    self.magnet_origin[0] - 5 * d,
                    self.magnet_origin[0] - 3 * d,
                    self.magnet_origin[1] - 9 * d,
                    self.magnet_origin[1] + 9 * d,
                    self.magnet_origin[2] - self.magnet_length / 2,
                    self.magnet_origin[2] + self.magnet_length / 2,
                ],
                [
                    self.magnet_origin[0] + 3 * d,
                    self.magnet_origin[0] + 5 * d,
                    self.magnet_origin[1] - 9 * d,
                    self.magnet_origin[1] + 9 * d,
                    self.magnet_origin[2] - self.magnet_length / 2,
                    self.magnet_origin[2] + self.magnet_length / 2,
                ],
                [
                    self.magnet_origin[0] - 7 * d,
                    self.magnet_origin[0] - 5 * d,
                    self.magnet_origin[1] - 8 * d,
                    self.magnet_origin[1] + 8 * d,
                    self.magnet_origin[2] - self.magnet_length / 2,
                    self.magnet_origin[2] + self.magnet_length / 2,
                ],
                [
                    self.magnet_origin[0] + 5 * d,
                    self.magnet_origin[0] + 7 * d,
                    self.magnet_origin[1] - 8 * d,
                    self.magnet_origin[1] + 8 * d,
                    self.magnet_origin[2] - self.magnet_length / 2,
                    self.magnet_origin[2] + self.magnet_length / 2,
                ],
                [
                    self.magnet_origin[0] - 8 * d,
                    self.magnet_origin[0] - 7 * d,
                    self.magnet_origin[1] - 7 * d,
                    self.magnet_origin[1] + 7 * d,
                    self.magnet_origin[2] - self.magnet_length / 2,
                    self.magnet_origin[2] + self.magnet_length / 2,
                ],
                [
                    self.magnet_origin[0] + 7 * d,
                    self.magnet_origin[0] + 8 * d,
                    self.magnet_origin[1] - 7 * d,
                    self.magnet_origin[1] + 7 * d,
                    self.magnet_origin[2] - self.magnet_length / 2,
                    self.magnet_origin[2] + self.magnet_length / 2,
                ],
                [
                    self.magnet_origin[0] - 9 * d,
                    self.magnet_origin[0] - 8 * d,
                    self.magnet_origin[1] - 5 * d,
                    self.magnet_origin[1] + 5 * d,
                    self.magnet_origin[2] - self.magnet_length / 2,
                    self.magnet_origin[2] + self.magnet_length / 2,
                ],
                [
                    self.magnet_origin[0] + 8 * d,
                    self.magnet_origin[0] + 9 * d,
                    self.magnet_origin[1] - 5 * d,
                    self.magnet_origin[1] + 5 * d,
                    self.magnet_origin[2] - self.magnet_length / 2,
                    self.magnet_origin[2] + self.magnet_length / 2,
                ],
                [
                    self.magnet_origin[0] - 10 * d,
                    self.magnet_origin[0] - 9 * d,
                    self.magnet_origin[1] - 3 * d,
                    self.magnet_origin[1] + 3 * d,
                    self.magnet_origin[2] - self.magnet_length / 2,
                    self.magnet_origin[2] + self.magnet_length / 2,
                ],
                [
                    self.magnet_origin[0] + 9 * d,
                    self.magnet_origin[0] + 10 * d,
                    self.magnet_origin[1] - 3 * d,
                    self.magnet_origin[1] + 3 * d,
                    self.magnet_origin[2] - self.magnet_length / 2,
                    self.magnet_origin[2] + self.magnet_length / 2,
                ],
            ]
        )
        self._pre_term = self.mu0_Ms / (4 * np.pi)

    def Bz_method(self, x, y, z):
        r"""Calculate magnetic field :math:`B_z` [mT].

        Approximating Cylinder Magnet by 11 Rectangular Magnets. When viewed from the
        vertical direction, we are using a row of rectangles to approximate a circle,
        these rectangular blocks are arranged side by side.

        The magnetic field of each rectangular magnet is calculated following the
        method described in Ravaud2009 [#]_.  The magnet is set up so that the
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
                \arctan \left( \dfrac{(x - x_i)(y - y_i))}{(z - z_k)R} \right)

        Here :math:`(x,y,z)` are the coordinates for the location at which we
        want to know the field;
        The magnet spans from :math:`x_1` to :math:`x_2` in the :math:`x`-direction,
        :math:`y_1` to :math:`y_2` in the :math:`y`-direction, and :math:`z_1` to 
        :math:`z_2` in the :math:`z`-direction;

        .. math::
            R = \sqrt{(x - x_i)^2 + (y - y_j)^2 + (z - z_k)^2}

        where :math:`\mu_0 M_s` is the magnet's saturation magnetization in mT.

        .. [#] Ravaud, R. and Lemarquand, G. "Magnetic field produced by a
           parallelepipedic magnet of various and uniform polarization",
           *PIER*, **2009**, *98*, 207-219
           [`10.2528/PIER09091704 <http://dx.doi.org/10.2528/PIER09091704>`__].


        :param float x: :math:`x` coordinate of sample grid [nm]
        :param float y: :math:`y` coordinate of sample grid [nm]
        :param float z: :math:`z` coordinate of sample grid [nm]
        """
        dx11, dx12 = x - self._range[0][0], x - self._range[0][1]
        dy11, dy12 = y - self._range[0][2], y - self._range[0][3]
        dz11, dz12 = z - self._range[0][4], z - self._range[0][5]

        dx21, dx22 = x - self._range[1][0], x - self._range[1][1]
        dy21, dy22 = y - self._range[1][2], y - self._range[1][3]
        dz21, dz22 = z - self._range[1][4], z - self._range[1][5]

        dx31, dx32 = x - self._range[2][0], x - self._range[2][1]
        dy31, dy32 = y - self._range[2][2], y - self._range[2][3]
        dz31, dz32 = z - self._range[2][4], z - self._range[2][5]

        dx41, dx42 = x - self._range[3][0], x - self._range[3][1]
        dy41, dy42 = y - self._range[3][2], y - self._range[3][3]
        dz41, dz42 = z - self._range[3][4], z - self._range[3][5]

        dx51, dx52 = x - self._range[4][0], x - self._range[4][1]
        dy51, dy52 = y - self._range[4][2], y - self._range[4][3]
        dz51, dz52 = z - self._range[4][4], z - self._range[4][5]

        dx61, dx62 = x - self._range[5][0], x - self._range[5][1]
        dy61, dy62 = y - self._range[5][2], y - self._range[5][3]
        dz61, dz62 = z - self._range[5][4], z - self._range[5][5]

        dx71, dx72 = x - self._range[6][0], x - self._range[6][1]
        dy71, dy72 = y - self._range[6][2], y - self._range[6][3]
        dz71, dz72 = z - self._range[6][4], z - self._range[6][5]

        dx81, dx82 = x - self._range[7][0], x - self._range[7][1]
        dy81, dy82 = y - self._range[7][2], y - self._range[7][3]
        dz81, dz82 = z - self._range[7][4], z - self._range[7][5]

        dx91, dx92 = x - self._range[8][0], x - self._range[8][1]
        dy91, dy92 = y - self._range[8][2], y - self._range[8][3]
        dz91, dz92 = z - self._range[8][4], z - self._range[8][5]

        dx101, dx102 = x - self._range[9][0], x - self._range[9][1]
        dy101, dy102 = y - self._range[9][2], y - self._range[9][3]
        dz101, dz102 = z - self._range[9][4], z - self._range[9][5]

        dx111, dx112 = x - self._range[10][0], x - self._range[10][1]
        dy111, dy112 = y - self._range[10][2], y - self._range[10][3]
        dz111, dz112 = z - self._range[10][4], z - self._range[10][5]

        return self._pre_term * (
            self._bz(dx11, dx12, dy11, dy12, dz11, dz12)
            + self._bz(dx21, dx22, dy21, dy22, dz21, dz22)
            + self._bz(dx31, dx32, dy31, dy32, dz31, dz32)
            + self._bz(dx41, dx42, dy41, dy42, dz41, dz42)
            + self._bz(dx51, dx52, dy51, dy52, dz51, dz52)
            + self._bz(dx61, dx62, dy61, dy62, dz61, dz62)
            + self._bz(dx71, dx72, dy71, dy72, dz71, dz72)
            + self._bz(dx81, dx82, dy81, dy82, dz81, dz82)
            + self._bz(dx91, dx92, dy91, dy92, dz91, dz92)
            + self._bz(dx101, dx102, dy101, dy102, dz101, dz102)
            + self._bz(dx111, dx112, dy111, dy112, dz111, dz112)
        )

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

        :param float dx1: distance between grid and one end of magnet
                    in :math:`x` direction [nm]
        :param float dx2: distance between grid and other end of magnet
                    in :math:`x` direction [nm]
        :param float dy1: distance between grid and one end of magnet
                    in :math:`y` direction [nm]
        :param float dy2: distance between grid and other end of magnet
                    in :math:`y` direction [nm]
        :param float dz1: distance between grid and one end of magnet
                    in :math:`z` direction [nm]
        :param float dz2: distance between grid and other end of magnet
                    in :math:`z` direction [nm]
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

        Approximating Cylinder Magnet by 11 Rectangular Magnets. When viewed from the
        vertical direction, we are using a row of rectangles to approximate a circle,
        these rectangular blocks are arranged side by side.

        The magnetic field gradient for RectangularMagnet is:
        :math:`B_{zx} = \dfrac{\partial{B_z}}{\partial x}` is
        given by the following:

        .. math::
           B_{zx} = \dfrac{\mu_0 M_s}{4 \pi} \sum_{i=1}^2 \sum_{j=1}^2
               \sum_{k=1}^2(-1)^{i+j+k}
               \left( \dfrac{(y-y_j)(z-z_k)}{ R((x-x_i)^2 + (z-z_k)^2))}
               \right)

        As described above, :math:`(x,y,z)` are coordinates for the location
        at which we want to know the field gradient; the magnet spans from
        x1 to x2 in the :math:`x`-direction, y1 to y2 in the :math:`y`-direction, and
        from z1 to z2 in the :math:`z`-direction;

        .. math::
            R = \sqrt{(x - x_i)^2 + (y - y_j)^2 + (z - z_k)^2}

        :math:`\mu_0 M_s` is the magnet's saturation magnetization in mT.

        :param float x: :math:`x` coordinate [nm]
        :param float y: :math:`y` coordinate [nm]
        :param float z: :math:`z` coordinate [nm]
        """

        dx11, dx12 = x - self._range[0][0], x - self._range[0][1]
        dy11, dy12 = y - self._range[0][2], y - self._range[0][3]
        dz11, dz12 = z - self._range[0][4], z - self._range[0][5]

        dx21, dx22 = x - self._range[1][0], x - self._range[1][1]
        dy21, dy22 = y - self._range[1][2], y - self._range[1][3]
        dz21, dz22 = z - self._range[1][4], z - self._range[1][5]

        dx31, dx32 = x - self._range[2][0], x - self._range[2][1]
        dy31, dy32 = y - self._range[2][2], y - self._range[2][3]
        dz31, dz32 = z - self._range[2][4], z - self._range[2][5]

        dx41, dx42 = x - self._range[3][0], x - self._range[3][1]
        dy41, dy42 = y - self._range[3][2], y - self._range[3][3]
        dz41, dz42 = z - self._range[3][4], z - self._range[3][5]

        dx51, dx52 = x - self._range[4][0], x - self._range[4][1]
        dy51, dy52 = y - self._range[4][2], y - self._range[4][3]
        dz51, dz52 = z - self._range[4][4], z - self._range[4][5]

        dx61, dx62 = x - self._range[5][0], x - self._range[5][1]
        dy61, dy62 = y - self._range[5][2], y - self._range[5][3]
        dz61, dz62 = z - self._range[5][4], z - self._range[5][5]

        dx71, dx72 = x - self._range[6][0], x - self._range[6][1]
        dy71, dy72 = y - self._range[6][2], y - self._range[6][3]
        dz71, dz72 = z - self._range[6][4], z - self._range[6][5]

        dx81, dx82 = x - self._range[7][0], x - self._range[7][1]
        dy81, dy82 = y - self._range[7][2], y - self._range[7][3]
        dz81, dz82 = z - self._range[7][4], z - self._range[7][5]

        dx91, dx92 = x - self._range[8][0], x - self._range[8][1]
        dy91, dy92 = y - self._range[8][2], y - self._range[8][3]
        dz91, dz92 = z - self._range[8][4], z - self._range[8][5]

        dx101, dx102 = x - self._range[9][0], x - self._range[9][1]
        dy101, dy102 = y - self._range[9][2], y - self._range[9][3]
        dz101, dz102 = z - self._range[9][4], z - self._range[9][5]

        dx111, dx112 = x - self._range[10][0], x - self._range[10][1]
        dy111, dy112 = y - self._range[10][2], y - self._range[10][3]
        dz111, dz112 = z - self._range[10][4], z - self._range[10][5]

        return self._pre_term * (
            self._bzx(dx11, dx12, dy11, dy12, dz11, dz12)
            + self._bzx(dx21, dx22, dy21, dy22, dz21, dz22)
            + self._bzx(dx31, dx32, dy31, dy32, dz31, dz32)
            + self._bzx(dx41, dx42, dy41, dy42, dz41, dz42)
            + self._bzx(dx51, dx52, dy51, dy52, dz51, dz52)
            + self._bzx(dx61, dx62, dy61, dy62, dz61, dz62)
            + self._bzx(dx71, dx72, dy71, dy72, dz71, dz72)
            + self._bzx(dx81, dx82, dy81, dy82, dz81, dz82)
            + self._bzx(dx91, dx92, dy91, dy92, dz91, dz92)
            + self._bzx(dx101, dx102, dy101, dy102, dz101, dz102)
            + self._bzx(dx111, dx112, dy111, dy112, dz111, dz112)
        )

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

        Optimized with numba. See method ``Bzx_method`` for the explanation.

        :param float dx1: distance between grid and one end of magnet
                    in :math:`x` direction [nm]
        :param float dx2: distance between grid and other end of magnet
                    in :math:`x` direction [nm]
        :param float dy1: distance between grid and one end of magnet
                    in :math:`y` direction [nm]
        :param float dy2: distance between grid and other end of magnet
                    in :math:`y` direction [nm]
        :param float dz1: distance between grid and one end of magnet
                    in :math:`z` direction [nm]
        :param float dz2: distance between grid and other end of magnet
                    in :math:`z` direction [nm]
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

        Approximating Cylinder Magnet by 11 Rectangular Magnets. When viewed from the
        vertical direction, we are using a row of rectangles to approximate a circle,
        these rectangular blocks are arranged side by side.

        The magnetic field second derivative for RectangularMagnet is:
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

        dx11, dx12 = x - self._range[0][0], x - self._range[0][1]
        dy11, dy12 = y - self._range[0][2], y - self._range[0][3]
        dz11, dz12 = z - self._range[0][4], z - self._range[0][5]

        dx21, dx22 = x - self._range[1][0], x - self._range[1][1]
        dy21, dy22 = y - self._range[1][2], y - self._range[1][3]
        dz21, dz22 = z - self._range[1][4], z - self._range[1][5]

        dx31, dx32 = x - self._range[2][0], x - self._range[2][1]
        dy31, dy32 = y - self._range[2][2], y - self._range[2][3]
        dz31, dz32 = z - self._range[2][4], z - self._range[2][5]

        dx41, dx42 = x - self._range[3][0], x - self._range[3][1]
        dy41, dy42 = y - self._range[3][2], y - self._range[3][3]
        dz41, dz42 = z - self._range[3][4], z - self._range[3][5]

        dx51, dx52 = x - self._range[4][0], x - self._range[4][1]
        dy51, dy52 = y - self._range[4][2], y - self._range[4][3]
        dz51, dz52 = z - self._range[4][4], z - self._range[4][5]

        dx61, dx62 = x - self._range[5][0], x - self._range[5][1]
        dy61, dy62 = y - self._range[5][2], y - self._range[5][3]
        dz61, dz62 = z - self._range[5][4], z - self._range[5][5]

        dx71, dx72 = x - self._range[6][0], x - self._range[6][1]
        dy71, dy72 = y - self._range[6][2], y - self._range[6][3]
        dz71, dz72 = z - self._range[6][4], z - self._range[6][5]

        dx81, dx82 = x - self._range[7][0], x - self._range[7][1]
        dy81, dy82 = y - self._range[7][2], y - self._range[7][3]
        dz81, dz82 = z - self._range[7][4], z - self._range[7][5]

        dx91, dx92 = x - self._range[8][0], x - self._range[8][1]
        dy91, dy92 = y - self._range[8][2], y - self._range[8][3]
        dz91, dz92 = z - self._range[8][4], z - self._range[8][5]

        dx101, dx102 = x - self._range[9][0], x - self._range[9][1]
        dy101, dy102 = y - self._range[9][2], y - self._range[9][3]
        dz101, dz102 = z - self._range[9][4], z - self._range[9][5]

        dx111, dx112 = x - self._range[10][0], x - self._range[10][1]
        dy111, dy112 = y - self._range[10][2], y - self._range[10][3]
        dz111, dz112 = z - self._range[10][4], z - self._range[10][5]

        return self._pre_term * (
            self._bzxx(dx11, dx12, dy11, dy12, dz11, dz12)
            + self._bzxx(dx21, dx22, dy21, dy22, dz21, dz22)
            + self._bzxx(dx31, dx32, dy31, dy32, dz31, dz32)
            + self._bzxx(dx41, dx42, dy41, dy42, dz41, dz42)
            + self._bzxx(dx51, dx52, dy51, dy52, dz51, dz52)
            + self._bzxx(dx61, dx62, dy61, dy62, dz61, dz62)
            + self._bzxx(dx71, dx72, dy71, dy72, dz71, dz72)
            + self._bzxx(dx81, dx82, dy81, dy82, dz81, dz82)
            + self._bzxx(dx91, dx92, dy91, dy92, dz91, dz92)
            + self._bzxx(dx101, dx102, dy101, dy102, dz101, dz102)
            + self._bzxx(dx111, dx112, dy111, dy112, dz111, dz112)
        )

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

        :param float dx1: distance between grid and one end of magnet
                        in :math:`x` direction [nm]
        :param float dx2: distance between grid and other end of magnet
                        in :math:`x` direction [nm]
        :param float dy1: distance between grid and one end of magnet
                        in :math:`y` direction [nm]
        :param float dy2: distance between grid and other end of magnet
                        in :math:`y` direction [nm]
        :param float dz1: distance between grid and one end of magnet
                        in :math:`z` direction [nm]
        :param float dz2: distance between grid and other end of magnet
                        in :math:`z` direction [nm]
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
