# ASDF Format Validator

This module serves to validate `ASDF` (*Adaptable Seismic Data Format*) files to
ensure consistency and compatibility between implementations.

While being written in Python it is completely independent of any ASDF
implementation.

## Installation

It requires HDF5 in a recent version to be installed (in particular the
`h5dump` and `h5ls` programs must be installed and in the `PATH`).

Python versions 2.7 and 3.4 have been tested; others might well work.
Additional required Python modules are:

* `lxml`
* `jsonschema>=2.4.0`
* `xmltodict`
* `pytest`


Cloning the repository is currently necessary:


```bash
$ git clone https://github.com/SeismicData/asdf_validate.git
$ cd asdf_validate
$ pip install -v -e .
```

## Usage

The module will install a single command: `asdf-validate`.

```bash
$ asdf-validate seismo.h5
Valid ASDF File!
```

Any other output mean your file is not valid. The error messages should hopefully give hints how to fix it.


## What Does it Do?

It performs a couple of validations:

1. Checks if the file exists.
2. Checks if its an HDF5 file.
3. Checks if the `file_format` and `file_format_version` attributes are set and correspond to expected values.
4. It transforms the structure of the file to a JSON respresentation which is then checked against a [JSON Schema](http://json-schema.org/). This assures a number of things:
  * The general layout and naming scheme is enforced.
  * Data spaces and data types of attributes are enforced.
  * Waveform data can only be 32/64 bit, little/big endian, IEEE floats or two's complement integers.
  * Waveform data sets must have `starttime` and `sampling_rate` attributes of the correct data space and type.
  * Naming scheme of the auxiliary data is enforced.
  * XML files are stored in a consistent manner.
5. It makes sure all waveforms are in the correct station group.
6. It validates the QuakeML file against the QuakeML schema.
7. It validates all found StationXML files against the StationXML schema.


## Missing Checks

A number of checks that should be implemented in the future in no particular order:

* The times in the data set names of the waveforms should correspond to the actual times of the data.
* The various event resource identifiers on the waveform datasets are valid identifiers.
* StationXML files only contain information about the current station.
* Provenance is not yet validated (this has to wait until SEIS-PROV is done).
