# pyDINEOF

## Table of Contents

- [About](#about)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [License](#license)

## About

pyDINEOF is a Python version of DINEOF.

[DINEOF](https://github.com/aida-alvera/DINEOF) is an EOF-based method to fill in missing data from geophysical fields,
such as clouds in sea surface temperature, and is available as compiled Fortran code.

For more information on how DINEOF works, please refer to
[Alvera-Azcarate et al. (2005)](https://doi.org/10.1016/j.ocemod.2004.08.001) and
[Beckers and Rixen (2003)](https://doi.org/10.1175/1520-0426(2003)020%3C1839:ECADFF%3E2.0.CO;2).
The multivariate application of DINEOF is explained in
[Alvera-Azcarate et al. (2007)](https://doi.org/10.1029/2006JC003660), and in
[Beckers et al. (2006)](https://doi.org/10.5194/os-2-183-2006) the error calculation using an optimal interpolation
approach is explained.
For more information about the Lanczos solver, see
[Toumazou and Cretaux (2001)](https://doi.org/10.1175/1520-0493(2001)129%3C1243:UALEIT%3E2.0.CO;2).

## Dependencies

pyDINEOF requires Python >= 3.10 and the following packages: numpy, pandas, scipy and xarray.

## Installation

pyDINEOF can be installed from source. To do so, you will first have to clone the GitHub repository:
```shell
$ git clone https://github.com/acoque/pyDINEOF.git
$ cd pyDINEOF
```

Then, you will need to create a virtual environment (optional, but strongly advised) and install pyDINEOF.

- using conda/mamba (recommended):

```shell
$ mamba env create -f environment.yml
$ mamba activate pyDINEOF
$ pip install .
```

- using venv and pip:

```shell
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -U .
```

Finally, you can use pyDINEOF as a Python package or through its CLI:

```shell
$ pyDINEOF run <file>
```

## Note

Most variables and functions have names similar to those in DINEOF for the sake of "continuity".


## License

Like DINEOF, pyDINEOF is distributed under the terms of the
[GNU General Public License version 3](https://www.gnu.org/licenses/gpl-3.0.html) license.
