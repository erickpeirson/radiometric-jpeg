from typing import Generator
import os
from math import log

import numpy as np

from .image import RadiometricImage
from .metadata import ImageMetadata


class Dataset(object):
    """A collection of radiometric JPEG images."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._load()
        self._S_min = None
        self._S_max = None

    def _load(self) -> None:
        params = []
        self.metadata = {}
        for fn in os.listdir(self._path):
            if fn.startswith('.') or fn.endswith('_'):
                continue
            if fn.lower().endswith('.jpeg') or fn.lower().endswith('.jpg'):
                m = ImageMetadata(os.path.join(self._path, fn))
                params.append(
                    (m.B, m.R_1, m.R_2, m.raw_min, m.raw_max, m.O, m.F)
                )
                self.metadata[fn] = m

        self.params = np.array(params).T

    @property
    def B(self) -> np.array:
        """Planck B constant."""
        return self.params[0, :]

    @property
    def R_1(self) -> np.array:
        """Planck R1 constant."""
        return self.params[1, :]

    @property
    def R_2(self) -> np.array:
        """Planck R2 constant."""
        return self.params[2, :]

    @property
    def raw_min(self) -> np.array:
        """Minimum raw thermal value."""
        return self.params[3, :]

    @property
    def raw_max(self) -> np.array:
        """Maximum raw thermal value."""
        return self.params[4, :]

    @property
    def O(self) -> np.array:
        """Planck O constant."""
        return self.params[5, :]

    @property
    def F(self) -> np.array:
        """Planck F constant."""
        return self.params[6, :]

    @property
    def S_min(self) -> np.float:
        """Minimum raw value, used to scale all images together."""
        if self._S_min is None:
            self._S_min = np.min(self.B / np.log(self.R_1 / (self.R_2 * (self.raw_min + self.O)) + self.F))
        return self._S_min

    @property
    def S_max(self) -> np.float:
        """Maximum raw value, used to scale all images together."""
        if self._S_max is None:
            self._S_max = np.max(self.B / np.log(self.R_1 / (self.R_2 * (self.raw_max + self.O)) + self.F))
        return self._S_max

    @property
    def images(self) -> Generator[RadiometricImage, None, None]:
        """Generate :class:`RadiometricImage`s from the dataset."""
        for fname, meta in self.metadata.items():
            yield RadiometricImage(os.path.join(self._path, fname))
