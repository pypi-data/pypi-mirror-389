"""Implement chromatograms as objects.

Chromatograms are a subclass of pandas Series (1D) or DataFrame (2D).
"""

import pandas as pd


class Chromatogram:
    """A chromatogram."""

    _metadata = ["metadata"]

    @property
    def method(self):
        return self.metadata["Method"]

    @property
    def detector(self):
        return self.metadata["Detector"]


class Chromatogram1D(Chromatogram, pd.Series):
    """A single channel chromatogram."""

    @property
    def _constructor(self):
        return Chromatogram1D

    @property
    def _constructor_expanddim(self):
        return Chromatogram2D


class Chromatogram2D(Chromatogram, pd.DataFrame):
    """A multi-channel chromatogram."""

    @property
    def _constructor(self):
        return Chromatogram2D

    @property
    def _constructor_sliced(self):
        return Chromatogram1D

    @property
    def name(self):
        return self.metadata["Name"]


class Chromatograms(list):
    """A list of chromatograms."""

    def by(self, attribute):
        """Return the list as a dict.

        Returns
        --------
        dict
            The chromatograms gropuby by their detectors. If there is only one chromatogram per detector across all detectors, then the dict has the form: `"attribute value": Chromatogram`. If at least one detector has more than chromatogram, then the dict has the form `"attribute value": Chromatograms[Chromatogram]`.
        """
        exposed_values = [(chrom.metadata[attribute], chrom) for chrom in self]
        values = [i[0] for i in exposed_values]
        unique_values = set(values)
        if len(values) == len(unique_values):
            return {v: c for v, c in exposed_values}
        else:
            result = {v: Chromatograms() for v in unique_values}
            for v, c in exposed_values:
                result[v].append(c)
            return result

    def by_detector(self, detector=None):
        """Return the list as a dict with detectors as the key.

        Parameters
        ----------
        detector: str
            The detector to select chromatograms from. If None, returns from all chromatograms.

        Returns
        --------
        dict
            The chromatograms gropuby by their detectors. If there is only one chromatogram per detector across all detectors, then the dict has the form: `"detector name": Chromatogram`. If at least one detector has more than chromatogram, then the dict has the form `"detector name": Chromatograms[Chromatogram]`.
        """
        by_detectors = self.by("Detector")

        if detector is None:
            return by_detectors

        chroms = by_detectors[detector]
        if len(chroms) == 1:
            return chroms[0]
        return chroms
