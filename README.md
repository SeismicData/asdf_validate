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

1. Checks the file exists.
2. Checks its an HDF5 file.
3. Checks if the `file_format` and `file_format_version` attributes are set and correspond to the expected values.
4. It transforms the structure of the file to JSON respresentation.
5. It validates the QuakeML file against the QuakeML schema.
6. It validates all found StationXML files against the StationXML schema.
