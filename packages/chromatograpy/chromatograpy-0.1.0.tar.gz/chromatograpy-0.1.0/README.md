# Chromatograpy

A Python library to analyze chromatograms with support for multiple instrument formats and comprehensive analysis tools.

## Features

- **File I/O**: Read chromatograms from multiple instrument formats
  - Thermo Chromeleon CSV exports
  - Waters MassLynx RAW files
- **Peak Detection**: Detect peaks using prominence-based algorithms
- **Baseline Correction**: Apply airPLS baseline correction algorithm
- **Peak Identification**: Identify peaks by retention time matching
- **Quantification**: Quantify analytes using calibration curves
- **Visualization**: Plot chromatograms with peak annotations

## Installation

```bash
pip install chromatograpy
```

## Requirements

- Python >= 3.13
- pandas
- numpy
- scipy
- matplotlib
- rainbow-api

## Quick Start

```python
import chromatograpy as chm

# Read a chromatogram file
chrom = chm.open("path/to/chromatogram.csv")

# Detect peaks
peaks = chm.peaks.by_prominence(chrom, prominence=0.1)

# Identify peaks using a retention time database
ids = chm.identify.by_retention_time(peaks, db)

# Quantify peaks
quantities = chm.quantify_peaks(peaks, ids, calibration_db)

# Plot the chromatogram with peaks
chm.plot(chrom, peaks=peaks, identification=ids, quantification=quantities)
```

## Supported File Formats

### Thermo Chromeleon
Read CSV exports from Chromeleon:
```python
chrom = chm.open("sample.csv")
```

### Waters MassLynx
Read MassLynx RAW files:
```python
# Read all detectors
chroms = chm.open("sample.raw")

# Read specific detector
chrom = chm.open("sample.raw", detector="UV")

# Read with metadata filtering
chrom = chm.open("sample.raw", metadata={"polarity": "+"})
```

## Core Classes

- `Chromatogram1D`: Single channel chromatogram (pandas Series subclass)
- `Chromatogram2D`: Multi-channel chromatogram (pandas DataFrame subclass)
- `Peak1D`: A detected peak with properties like area, height, and retention time

## API Overview

### Reading Files
- `chromatograpy.open(path, *args, **kwargs)`: Universal file reader that auto-detects format

### Peak Detection
- `chromatograpy.peaks.by_prominence(chromatogram, prominence=0.1)`: Detect peaks based on prominence

### Baseline Correction
- `chromatograpy.baseline.airPLS(x, lambda_=100, porder=1, itermax=15)`: Apply airPLS baseline correction

### Peak Identification
- `chromatograpy.identify.by_retention_time(peaks, db)`: Identify peaks using retention time database

### Quantification
- `chromatograpy.quantify_peaks(peaks, ids, db)`: Quantify individual peaks
- `chromatograpy.quantify_analytes(peaks, ids, db)`: Quantify all analytes in database

### Visualization
- `chromatograpy.plot(chrom, peaks=None, identification=None, quantification=None, ...)`: Plot chromatogram with optional annotations

## License

MIT

## Author

c.moevus@gmail.com
