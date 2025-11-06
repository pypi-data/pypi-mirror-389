"""Tools to read raw and transformed instrument data.

Metadata fields
----------------
- Name: the name of the specific run/sample/chromatogram
- Method: the method used to obtain the chromatogram
- Timestamp: the time of injection of the sample
- Detector: the detector used for reading the chromatogram
- Injection volume: the volume injected to get the chromatogram
- Sequence: the sequence/job/list this run/sample/chromatogram was part of
- Position: the location of the sample on the sample container (e.g. the rack + vial number, rack + well, etc.), in the format Rack:Vial/Well
- Instrument: the name/id/serial of the instrument used to collect the data
- Any other field with data from the manufacturer will be added as-is to the metadata.
"""

from . import chromeleon_csv
from .masslynx import MassLynxRaw
from .wrapper import read as open
