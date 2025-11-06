"""Define peaks as objects."""

import scipy as sp
from ..chromatogram import Chromatogram, Chromatogram1D


class Peak(Chromatogram):
    """A peak"""


class Peak1D(Peak, Chromatogram1D):
    """A peak in a chromatogram."""

    _metadata = Chromatogram1D._metadata + ["chromatogram"]

    @property
    def area(self):
        if not hasattr(self, "_area"):
            self._area = sp.integrate.trapezoid(
                self, self.index
            )  # - sp.integrate.trapezoid(
            #     [self.iloc[0], self.iloc[-1]], [self.index[0], self.index[-1]]
            # )  # Remove the trapezoidal area under the peak (that is, the baseline)
            # # TODO: Better baseline substraction, if any?
        return self._area

    @property
    def height(self):
        if not hasattr(self, "_height"):
            self._height = self.max()
        return self._height

    @property
    def retention_time(self):
        if not hasattr(self, "_retention_time"):
            self._retention_time = self.idxmax()
        return self._retention_time

    @property
    def rt(self):
        return self.retention_time
