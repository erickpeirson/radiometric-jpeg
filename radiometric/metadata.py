"""
Provides :class:`ImageMetadata`, for working with EXIF IR metadata.

.. todo::

   Many of the names of constants are from
   https://github.com/joshuapinter/flir/blob/master/flir.php. Someone more
   familiar with the maths should revisit naming/docstrings.

"""

from typing import Dict
from subprocess import run, STDOUT, PIPE
import shlex
import json
from math import exp, pow, sqrt, log
import numpy as np
import pandas as pd
from attrdict import AttrDict
from PIL import Image


class ImageMetadata(object):
    """
    Terms in equations as in Tran et al, 2017[1].

    [1] Tran, Quang Huy, et al. "Effects of ambient temperature and relative
        humidity on subsurface defect detection in concrete structures by
        active thermal imaging." Sensors 17.8 (2017): 1718.

    """


    T_ref: float
    """Reflected apparent temperature, °C."""

    T_atm: float
    """Atmospheric temperature, °C."""

    T_min: float
    """Lowest temperature in the image."""

    T_max: float
    """Highest temperature in the image."""

    d: float
    """Distance to object (ground surface), m."""

    ω_pct: float
    """Relative humidity, %."""

    ε: float
    """Emissivity, ratio in (0-1)."""

    R_1: float
    """Planck R1 constant."""

    R2: float
    """Planck R2 constant."""

    B: float
    """Planck B constant."""

    O: float
    """Planck O constant."""

    F: float
    """Planck F constant."""

    α_1: float
    """Attenuation for atmosphere without water vapor (with :prop:`α_2`)."""

    α_2: float
    """Attenuation for atmosphere without water vapor (with :prop:`α_1`)."""

    β_1: float
    """Attenuation for water vapor (with :prop:`β_2`)."""

    β_2: float
    """Attenuation for water vapor (with :prop:`β_1`)."""

    K_atm: float
    """Scaling factor for atmosphere damping."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._exif = None
        self._load()

    @property
    def exif(self) -> None:
        if self._exif is None:
            p = run(shlex.split(f'exiftool -json {self.path}'),
                    stdout=PIPE, stderr=PIPE)
            self._exif = AttrDict(json.loads(p.stdout)[0])
        return self._exif

    def temperature(self, data: np.array, precision: int = 2) -> np.array:
        raw = self.B / \
            np.log(self.R_1 / (self.R_2 * (data + self.O)) + self.F) - 273.15
        return np.round(raw, precision)

    def _load(self) -> None:
        self.T_ref = float(self.exif.ReflectedApparentTemperature.split()[0])
        self.T_atm = float(self.exif.AtmosphericTemperature.split()[0])
        self.d = float(self.exif.ObjectDistance.split()[0])
        self.ω_pct = float(self.exif.RelativeHumidity.split()[0]) / 100.
        self.ε = float(self.exif.Emissivity)
        self.R_1 = self.exif.PlanckR1
        self.R_2 = self.exif.PlanckR2
        self.B = self.exif.PlanckB
        self.O = self.exif.PlanckO
        self.F = self.exif.PlanckF
        self.α_1 = self.exif.AtmosphericTransAlpha1
        self.α_2 = self.exif.AtmosphericTransAlpha2

        self.β_1 = self.exif.AtmosphericTransBeta1
        self.β_2 = self.exif.AtmosphericTransBeta2
        self.K_atm = self.exif.AtmosphericTransX

        # Constants used for calculation of water vapor content.
        h_1 = 1.5587
        h_2 = 6.939e-2
        h_3 = 2.7816e-4
        h_4 = 6.8455e-7

        # Coefficient for for content of water vapor in the atmosphere.
        ω = (self.ω_pct) * exp(h_1 + h_2 * self.T_atm - h_3 * pow(self.T_atm, 2) + h_4 * pow(self.T_atm, 3))

        # Atmospheric transmission.
        τ = self.K_atm * exp(-sqrt(self.d) * (self.α_1 + self.β_1 * sqrt(ω))) \
            + (1 - self.K_atm) * exp(-sqrt(self.d) * (self.α_2 + self.β_2 * sqrt(ω)))

        # Amount of radiance from the atmosphere.
        self.raw_atm = self.R_1 / (self.R_2 * (exp(self.B / (self.T_atm + 273.15)) - self.F)) - self.O
        # Amount of radiance of reflected objects (Emissivity < 1).
        self.raw_refl = self.R_1 / (self.R_2 * (exp(self.B / (self.T_ref + 273.15)) - self.F)) - self.O

        self.raw_max = self.exif.RawValueMedian + (self.exif.RawValueRange / 2)
        self.raw_min = self.raw_max - self.exif.RawValueRange
        raw_min_obj = (self.raw_min - (1 - τ) * self.raw_atm - (1 - self.ε) * τ * self.raw_refl) / (self.ε * τ)
        raw_max_obj = (self.raw_max - (1 - τ) * self.raw_atm - (1 - self.ε) * τ * self.raw_refl) / (self.ε * τ)

        # Minimum and maximum temperature in the picture.
        self.T_min = self.temperature(raw_min_obj)
        self.T_max = self.temperature(raw_max_obj)
