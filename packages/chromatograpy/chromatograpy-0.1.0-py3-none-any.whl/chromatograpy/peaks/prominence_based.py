"""Detect peaks based on prominence"""

import numpy as np
import scipy as sp

from .peak import Peak1D
from ..chromatogram import Chromatogram2D


def by_prominence(chromatogram, prominence=0.1):
    """Return the peaks in a given chromatogram.

    Parameters
    ----------
    chromatogram: Chromatogram1D
        The chromatogram to read
    prominence: float
        The peak prominence, as defined in `sp.signal.find_peaks`

    Returns
    -------
    peaks: list of Peak
        The peaks identified, as `Peak` objects
    """
    if isinstance(chromatogram, Chromatogram2D):
        raise NotImplementedError("2D data is not supported yet")

    peak_pos, peak_props = sp.signal.find_peaks(
        chromatogram, prominence=prominence / 10
    )
    peak_prominences = peak_props["prominences"]
    peak_edges = np.array(
        list(zip(peak_props["left_bases"], peak_props["right_bases"]))
    )
    edge_diffs = np.diff(peak_edges, axis=0)
    wrong_edge_pos = np.array(np.where(edge_diffs <= 0)).T + [[1, 0]]

    at_start = wrong_edge_pos[wrong_edge_pos[:, 1] == 0]
    at_stop = wrong_edge_pos[wrong_edge_pos[:, 1] == 1]
    peak_edges[at_start[:, 0], 0] = peak_edges[at_start[:, 0] - 1, 1]
    peak_edges[at_stop[:, 0] - 1, 1] = peak_edges[at_stop[:, 0], 0]
    # # Loop-based alternative, slower than filter for large sets, faster for small sets
    # for r, c in wrong_edge_pos:
    #     if c == 1:
    #         peak_edges[r - 1, 1] = peak_edges[r, 0]
    #     else:
    #         peak_edges[r, 0] = peak_edges[r - 1, 1]

    peaks = []
    for i, (start, stop) in enumerate(peak_edges):
        if peak_prominences[i] < prominence or stop - start <= 0:
            continue
        peak = Peak1D(chromatogram.iloc[start:stop])
        peak.chromatogram = chromatogram
        if len(peak) > 0:
            peaks.append(peak)
    return peaks
