"""Import data from Chromeleon."""

from datetime import datetime
from io import StringIO
from pathlib import Path
import pandas as pd
from ..chromatogram import Chromatogram1D


def can_read(path):
    """Check that the file is a Thermo Chromeleon CSV export.

    Parameters
    ----------
    path : str
        The path to the file

    Returns
    -------
    bool
        True if the file is a Chromeleon-exported CSV file, False otherwise.
    """

    path = Path(path)
    if path.suffix.lower() != ".csv":
        return False
    if not path.is_file():
        return False
    with open(path, encoding="utf-8-sig") as open_file:
        first_line = open_file.readline()
        if not first_line.startswith("URL"):
            return False

    return True


def read(path):
    """Read the given Thermo Chromeleon-exported CSV file.

    Parameters
    ----------
    path : str
        The path of the file to read

    Returns
    -------
    Chromatogram
        The chromatogram contained in the given file.
    """
    with open(path, "r", encoding="UTF-8") as f:
        content = f.read()

    raw_data_start_line = (
        content.find("Chromatogram Data:\n") + 19
    )  # "19" is to account for the lenght of the string and remove it from the actual data

    parse_data = parse_1d_data
    if raw_data_start_line == 18:
        # Data not found, it may be a 2D chromatogram.
        raw_data_start_line = content.find("Raw Data:\n") + 10
        if raw_data_start_line == 9:
            # 2D data not found, it's not a Chromeleon CSV as far as I know
            raise ValueError(
                f"The file provided ({path}) is not a valid Chromeleon CSV file."
            )
        parse_data = parse_2d_data

    raw_metadata = content[:raw_data_start_line]
    metadata = parse_metadata(raw_metadata)

    raw_data = content[raw_data_start_line:]
    data = parse_data(raw_data)

    data.metadata = metadata

    return data


metadata_name_map = {
    "Instrument Method": "Method",
}


def parse_metadata(raw_data):
    """Transform the metadata part of the file into a dictionary.

    Parameters
    -----------
    raw_data: str
        The metadata part of the Chromeleon CSV
    """
    csv_data = pd.read_csv(StringIO(raw_data), header=None).set_index(0)
    as_dict = csv_data[1].to_dict()
    metadata = {k: v for k, v in as_dict.items() if k[-1] != ":"}

    translated_metadata = {
        k if k not in metadata_name_map.keys() else metadata_name_map[k]: v
        for k, v in metadata.items()
        if v != "" and k not in ["Inject Time"]
    }

    translated_metadata["Timestamp"] = datetime.strptime(
        metadata["Inject Time"], "%m/%d/%Y %I:%M:%S %p %z"
    )

    return translated_metadata


def parse_1d_data(raw_data):
    """Transform the data part of a 1D chromatogram file into a pandas Series.

    Parameters
    -----------
    raw_data: str
        The chromatogram section of the file
    """
    csv_data = pd.read_csv(StringIO(raw_data))
    csv_data.columns = ["time", "step", "value"]
    csv_data = csv_data.set_index("time")
    return Chromatogram1D(csv_data["value"])


def parse_2d_data(raw_data):
    """Transform the data part of a 1D chromatogram file into a pandas Series.

    Parameters
    -----------
    raw_data: str
        The chromatogram section of the file
    """
    raise NotImplementedError("2D chromatograms have not yet been implemented.")
