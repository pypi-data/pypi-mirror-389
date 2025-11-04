#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from dataclasses import dataclass, field
from mrfmsim.component import ComponentBase


@dataclass
class Cantilever(ComponentBase):
    """Cantilever object.

    :param float k_c: spring constant [aN/nm]
    :param float f_c: mechanical resonance frequency [Hz]

    :ivar float k2f_modulated: spring constant to frequency ratio for modulated
        cantilever (lockin) [Hz.nm/aN]
    :ivar float k2f: spring constant to frequency ratio for non-modulated
        cantilever [Hz.nm/aN]
    """

    k_c: float = field(metadata={"unit": "aN/nm", "format": ".3e"})
    f_c: float = field(metadata={"unit": "Hz", "format": ".3e"})
    k2f_modulated: float = field(
        init=False, repr=False, metadata={"unit": "Hz.nm/aN", "format": ".3e"}
    )
    k2f: float = field(
        init=False, repr=False, metadata={"unit": "Hz.nm/aN", "format": ".3e"}
    )

    def __post_init__(self):
        self.k2f_modulated = self.f_c / (self.k_c * np.pi * np.sqrt(2))
        self.k2f = self.f_c / (2 * self.k_c)
