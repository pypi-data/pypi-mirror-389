#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from dataclasses import dataclass, field
from mrfmsim.component import ComponentBase

spin_dict = {
    # note: not accounting for the g-factor of the electron spin;
    "e": {"Gamma": 1.760859708e8, "J": 0.5},  # rad/s.mT
    "1H": {"Gamma": 2.675222005e05, "J": 0.5},  # rad/s.mT
    "71Ga": {"Gamma": 2.0 * np.pi * 12.98e3, "J": 1.5},  # rad/s.mT
    "19F": {"Gamma": 2.0 * np.pi * 40.05e3, "J": 0.5},  # rad/s.mT
    "2H": {"Gamma": 2.0 * np.pi * 6.536e3, "J": 1.0},  # rad/s.mT
}


@dataclass
class Sample(ComponentBase):
    r"""Sample object for magnetic resonance force microscopy experiments.

    For spins 'e', '1H', '71Ga', '19F', or '2H' the Gamma and J are preset.
    For other spins, input the name, Gamma and J directly.

    :param str spin: spin type
    :param float T1: spin-lattice relaxation :math:`T_1` [s]
    :param float T2: spin-spin relaxation :math:`T_2` [s]
    :param float temperature: the sample temperature [K]
    :param float spin_density: the sample spin density :math:`\rho` [1/nm^3]
    :param float Gamma: spin gyromagnetic ratio [rad/s.mT]
        defaults to None if spin is one of the preset types
    :param float J: spin angular momentum [unitless]
        defaults to None if spin is one of the preset types
    :param float dB_hom: homogeneous linewidth [mT]
    :param float dB_sat: saturation linewidth [mT]
    """

    spin: str
    T1: float = field(metadata={"unit": "s", "format": ".3e"})
    T2: float = field(metadata={"unit": "s", "format": ".3e"})
    temperature: float = field(metadata={"unit": "K"})
    spin_density: float = field(metadata={"unit": "1/nm^3"})
    Gamma: float = field(default=None, metadata={"unit": "rad/(s.mT)", "format": ".3e"})
    J: float = field(default=None, metadata={"format": ".1f"})
    dB_hom: float = field(init=False, default=None, metadata={"unit": "mT"})
    dB_sat: float = field(init=False, default=None, metadata={"unit": "mT"})

    def __post_init__(self):
        self.Gamma = self.Gamma or spin_dict[self.spin]["Gamma"]  # rad/s.mT
        self.J = self.J or spin_dict[self.spin]["J"]
        self.dB_hom = 1 / (self.Gamma * self.T2)  # mT
        self.dB_sat = 1 / (self.Gamma * np.sqrt(self.T1 * self.T2))  # mT
