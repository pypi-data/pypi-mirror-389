""""Wrapper function to quantify several identified peaks."""

import numpy as np


def quantify_peaks(peaks, ids, db):
    """Quantify the given peaks using the information in the database.

    Parameters
    ----------
    peaks: list
        The peaks to quantify
    ids: list
        The name of the analyte for each peak, or None if unidentified (will not be quantified)
    db: pd.DataFrame
        A DataFrame with the columns:
        - "analyte", the name of the analyte
        - "slope": the quantification units / area unit for the analyte
        - "intercept": the value (in quantification units) at an area of 0
    """
    quantities = []
    for peak, name in zip(peaks, ids):
        if name is None:
            quantities.append(np.nan)
            continue
        m, b = db[db["analyte"] == name][["slope", "intercept"]].squeeze()
        quantities.append(peak.area * m + b)

    return quantities


def quantify_analytes(peaks, ids, db):
    """Quantify the given peaks using the information in the database.

    Parameters
    ----------
    peaks: list
        The peaks to quantify
    ids: list
        The name of the analyte for each peak, or None if unidentified (will not be quantified)
    db: pd.DataFrame
        A DataFrame with the columns:
        - "analyte", the name of the analyte
        - "slope": the quantification units / area unit for the analyte
        - "intercept": the value (in quantification units) at an area of 0

    Returns
    -------
    dict
        The analyte name : concentration for every analyte in the DB. The concentration is 0 if the analyte was not found.
    """
    quantities = dict()
    for i, row in db.iterrows():
        analyte = row["analyte"]
        try:
            idx = list(ids).index(analyte)
        except ValueError:
            quantities[row["analyte"]] = 0
            continue

        m, b = row[["slope", "intercept"]].squeeze()
        quantities[analyte] = peaks[idx].area * m + b

    return quantities
