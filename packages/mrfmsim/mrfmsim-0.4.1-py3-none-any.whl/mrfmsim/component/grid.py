#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from mrfmsim.component import ComponentBase
from dataclasses import dataclass, field


@dataclass
class Grid(ComponentBase):
    """Instantiate a rectangular grid with shape, step, and origin.

    The resulting grid has equal spacing in each dimension.
    The grid array uses numpy's open mesh-grid, which has speed and storage
    benefits.

    :param tuple[int, int, int] grid_shape: grid dimension
        (number of points in x, y, z direction)
    :param list[float] grid_step: grid step size in x, y, z direction [nm]
    :param list[float] grid_origin: the grid origin [nm]

    :ivar ndarray grid_length: array of lengths along (x, y, z)
    :ivar float grid_voxel: the volume of each grid voxel
    :ivar ndarray grid_range: range in (x, y, z direction), shape (3, 2)
    :ivar ndarray grid_length: actual lengths of the grid. This is recalculated
        based on the rounded value of grid shape and step size.
    :ivar ndarray grid_extents: the grid extents in (x, y, z direction), shape (3, 2)
    :ivar ndarray grid_array: the grid array in (x, y, z direction), shape (3, n)
    """

    grid_shape: tuple[int]
    grid_step: list[float] = field(metadata={"unit": "nm", "format": ".1f"})
    grid_origin: list[float] = field(metadata={"unit": "nm", "format": ".1f"})
    grid_voxel: float = field(init=False, metadata={"unit": "nm^3"})
    grid_range: np.array = field(init=False, metadata={"unit": "nm", "format": ".1f"})
    grid_length: np.array = field(init=False, metadata={"unit": "nm", "format": ".1f"})

    def __post_init__(self):
        """Calculate grid parameters."""

        self.grid_voxel = np.array(self.grid_step).prod()
        self.grid_range = (np.array(self.grid_shape) - [1, 1, 1]) * self.grid_step
        self.grid_length = np.array(self.grid_shape) * np.array(self.grid_step)
        self.grid_extents = self.grid_extents_method(self.grid_range, self.grid_origin)

    @staticmethod
    def grid_extents_method(length, origin):
        """Calculate grid extents based on the grid length and origin.

        The result is column stacked into a dimension of (3, 2)
        """

        return np.column_stack((-length / 2 + origin, length / 2 + origin))

    @property
    def grid_array(self):
        """Generate an open mesh-grid of the given grid dimensions.

        The benefit of the property is that it generates the grid array at run time.
        """

        # extents = self.grid_extents(self.grid_range, self.origin)

        return np.ogrid[
            self.grid_extents[0][0] : self.grid_extents[0][1] : self.grid_shape[0] * 1j,
            self.grid_extents[1][0] : self.grid_extents[1][1] : self.grid_shape[1] * 1j,
            self.grid_extents[2][0] : self.grid_extents[2][1] : self.grid_shape[2] * 1j,
        ]

    def extend_grid_by_points(self, ext_pts):
        """Extend the grid by the number of points in the x direction.

        :param int ext_pts: points (one side) to extend along x direction
            (cantilever motion direction). The points should be a list of
            three dimensions.
        """

        ext_shape = self.grid_shape + np.array(ext_pts) * 2
        ext_range = (ext_shape - [1, 1, 1]) * self.grid_step
        extents = self.grid_extents_method(ext_range, self.grid_origin)

        return np.ogrid[
            extents[0][0] : extents[0][1] : ext_shape[0] * 1j,
            extents[1][0] : extents[1][1] : ext_shape[1] * 1j,
            extents[2][0] : extents[2][1] : ext_shape[2] * 1j,
        ]

    def extend_grid_by_length(self, ext_length):
        """Extend the grid by the number of points in the x direction.

        This is used to extend the grid by the cantilever motion.
        The length needs to be more than the step size to count.

        :param int ext_length: distance (one side) to extend along x direction
            (cantilever motion direction). The length should be a list of
            three dimensions.
        """

        pts = np.floor(np.array(ext_length) / self.grid_step).astype(int)
        return self.extend_grid_by_points(pts)
