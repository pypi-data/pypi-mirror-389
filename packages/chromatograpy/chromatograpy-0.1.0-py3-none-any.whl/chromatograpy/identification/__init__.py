"""Functions to identify analytes in chromatograms."""

import numpy as np


def get_closest_peak(peaks, rt_range):
    """Get the closest peak to the retention time for the given retention time in the format [low, expected, high] or [low, high]."""
    if len(rt_range) == 2:
        rt_range = (rt_range[0], np.mean(rt_range), rt_range[1])
    rts = np.array([p.rt for p in peaks])

    if len(rts) == 0:
        return None

    distances = np.abs(rts - rt_range[1])
    distpos = [(rt, p) for p, rt in enumerate(distances)]
    return peaks[sorted(distpos)[0][1]]


def _keep_first_occurence(matches):
    """Keep the first occurence of an element in a list of match if that element shows several times in the list."""
    sorted_a_idx = np.array(range(len(matches)))
    sorted_b_idx = np.argsort(matches[:, 1])
    a_idx_to_keep = [True] + list(np.diff(matches[sorted_a_idx, 0]) != 0)
    b_idx_to_keep = [True] + list(np.diff(matches[sorted_b_idx, 1]) != 0)
    rows_to_keep = set(sorted_a_idx[a_idx_to_keep]).intersection(
        sorted_b_idx[b_idx_to_keep]
    )
    return matches[list(rows_to_keep)]


def by_retention_time(peaks, db):
    """Identify the given peaks using the given retention time.

    Parameters
    ----------
    peaks: list of Peaks
        The peaks to identify
    db: pandas.DataFrame
        The database of peaks to retention time with columns:
        - "analyte", the name of the analyte eluting in the given retention time range,
        - "rt_low", the lower end of retention time range,
        - "rt_high", the upper end of retention time range for that analyte

    Returns
    -------
     list of str or None, same shape as peaks
        The name of the analyte for each peak. If unidentified, None.
    """
    # Get DB RTs
    db_rts = ((db["rt_low"] + db["rt_high"]) / 2).to_numpy()
    db_min_rts = db["rt_low"].to_numpy()
    db_max_rts = db["rt_high"].to_numpy()

    # Get peak RTs
    peak_rts = np.array([p.rt for p in peaks])

    # Set the lower and upper bounds
    unmatchable = (peak_rts[:, np.newaxis] < db_min_rts) | (
        peak_rts[:, np.newaxis] >= db_max_rts
    )

    # Match retention times
    distances = np.ma.array((peak_rts[:, np.newaxis] - db_rts) ** 2, mask=unmatchable)
    matches = []
    while not np.all(distances.mask) and not np.all(np.isinf(distances)):
        # Get the unique matches
        iteration_matches = np.array(np.where(distances == distances.min())).T
        iteration_matches = _keep_first_occurence(iteration_matches)

        # Save the matches, prevent them from being used again
        matches.extend(iteration_matches)
        distances.mask[iteration_matches[:, 0]] = True
        distances.mask[:, iteration_matches[:, 1]] = True

    idx_to_name = {i: db["analyte"].iloc[j] for i, j in matches}
    return [idx_to_name.get(i, None) for i in range(len(peaks))]
