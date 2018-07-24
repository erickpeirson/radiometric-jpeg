import os
import tempfile
from typing import Dict, Optional
from subprocess import run, STDOUT, PIPE
import shlex
import json
from math import exp, pow, sqrt, log
import numpy as np
import pandas as pd
from attrdict import AttrDict
from PIL import Image

from .metadata import ImageMetadata


class RadiometricImage(object):
    def __init__(self, path: str) -> None:
        self._path = path
        self._temp = tempfile.mkdtemp()
        _, fname = os.path.split(path)
        self._name = fname.split('.', 1)[0]
        self._raw: Optional[str] = None
        self.meta = ImageMetadata(self._path)

    @property
    def csv_path(self) -> str:
        return os.path.join(self._dest, )

    @property
    def raw_path(self) -> str:
        return os.path.join(self._dest, f"{self._name}.raw.tiff")

    @property
    def tiff_path(self) -> str:
        return os.path.join(self._dest, f"{self._name}.ir.tiff")

    @property
    def raw(self) -> str:
        """Location of the raw thermal image data."""
        if self._raw is None or not os.path.exists(self._raw):
            target = os.path.join(self._temp, f"{self._name}.raw.tiff")
            p = run(f"exiftool -b -RawThermalImage {self._path} | convert - {target}", shell=True)
            self._raw = target
        return self._raw

    def to_csv(self, dest: str) -> str:
        """Extract the IR data (°C) as CSV."""
        img = Image.open(self.raw)
        raw = np.array([[img.getpixel((i, j)) for i in range(img.width)] for j in range(img.height)]).T
        data = self.meta.temperature(raw)
        target = os.path.join(dest, f"{self._name}.ir.csv")
        pd.DataFrame(data=data).to_csv(target, index=False, header=False)
        return target

    def convert_fnx(self, S_min: float, S_max: float) -> str:
        """
        Build a function-string for ImageMagick to convert raw TIFF to IR.

        A factor of 65535 is used to convert between double and 16-bit
        integer. Otherwise the calculation is just the same as in
        :func:`ImageMetadata.temperature`.
        """
        S_delta = S_max - S_min
        B = self.meta.B
        R_1 = self.meta.R_1
        R_2 = self.meta.R_2
        O = self.meta.O
        F = self.meta.F
        return f"({B}/ln({R_1}/({R_2}*((65535*u+{O})?(65535*u+{O}):1))+{F})-{S_min})/{S_delta}"

    def to_tiff(self, dest: str, convert_fnx: Optional[str] = None) -> str:
        """
        Extract IR data as TIFF.

        Convert every RAW-16-Bit Pixel with Planck's Law to a Temperature
        Grayscale value and append temp scale.
        """
        if convert_fnx is None:
            S_min, S_max = self.meta.T_min + 273.15, self.meta.T_max + 273.15
            convert_fnx = self.convert_fnx(S_min, S_max)
        target = os.path.join(dest, f"{self._name}.ir.tiff")
        run(f"convert {self.raw} -fx \"{convert_fnx}\" {target}",
            shell=True, stderr=PIPE, stdout=PIPE)
        return target
