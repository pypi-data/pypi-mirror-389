"""Plot chromatograms"""

import numpy as np
from matplotlib import pyplot as plt

from .peaks import Peak


def plot(
    chrom,
    peaks=None,
    identification=None,
    quantification=None,
    ax=None,
    quant_units="g/L",
    peak_style="marker",
    **kwargs,
):
    """Plot the given chromatogram and peak data

    Parameters
    ----------
    chrom: Chromatogram1D
        The chromatogram to plot onto
    peaks: list of Peak1D or floats or None
        The peaks to label, or their retention times
    identification: list of str or None
        The names of the peaks
    quantification: list of floats or None
        The concentrations of the peaks
    ax: plt.Axes
        The axes to draw onto
    quant_units: str
        The units to write with the quantification value. Default: g/L
    peak_style: str
        The way to identify peaks:
        - 'marker' will draw a short line above the peak
        - 'fill' will fill the area underneath the peak with a color
    **kwargs: extra arguments for `plt.plot` for the chromatogram
    """
    if ax is None:
        ax = plt.gca()

    ax.plot(chrom, **kwargs)
    ax.spines[["right", "top"]].set_visible(False)

    if peaks is not None:
        if identification is None:
            identification = [None for i in peaks]
        if quantification is None:
            quantification = [None for i in peaks]

        ydiff = np.diff(ax.get_ylim())

        for p, i, q in zip(peaks, identification, quantification):
            rt = p.rt if isinstance(p, Peak) else p
            # Label the peak
            top = chrom[rt] + 0.01 * ydiff
            text = ""
            if i is not None:
                text += f"{i} "
            if q is not None and not np.isnan(q):
                text += f"{q:.2f} {quant_units}"
            if text:
                ax.text(
                    rt,
                    top + 0.03 * ydiff,
                    text,
                    ha="center",
                    va="bottom",
                    rotation="vertical",
                    fontsize="x-small",
                )

            # Mark the peak
            if text != "" or peak_style == "marker":
                ax.vlines(rt, top, top + 0.02 * ydiff, linestyle="-", color="k")
            if peak_style == "fill":
                ax.fill_between(p.index, p)
