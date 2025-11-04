# Copyright (C) 2025  Arthur Coqué, RBINS

"""The Command Line Interface (CLI) of pyDINEOF.

Available command
-----------------
run
    Run a monovariate DINEOF reconstruction of a given 1D or 2D time series.
"""

from pathlib import Path

import click
import pandas as pd
import xarray as xr

from pydineof import __about__, run_1D, run_2D


@click.group()
@click.version_option(version=__about__.VERSION, prog_name=__about__.name)
def cli():
    """A Python version of DINEOF.

    DINEOF (https://github.com/aida-alvera/DINEOF) is an EOF-based method to fill in missing
    data from geophysical fields, such as clouds in sea surface temperature, and is
    available as compiled Fortran code.
    For more information on how DINEOF works, please refer to Alvera-Azcarate et al. (2005)
    and Beckers and Rixen (2003). The multivariate application of DINEOF is explained in
    Alvera-Azcarate et al. (2007), and in Beckers et al0 (2006) the error calculation using
    an optimal interpolation approach is explained.
    For more information about the Lanczos solver, see Toumazou and Cretaux (2001).

    pyDINEOF  Copyright (C) 2025  Arthur Coqué
    This program comes with ABSOLUTELY NO WARRANTY. This is free software, and you are
    welcome to redistribute it under certain conditions.
    """


@cli.command()  # TODO: add help texts
@click.argument(
    'file',
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    '--out_file',
    '-o',
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
)
@click.option('--var', 'var_name', type=str, default=None)
@click.option('--mask', 'mask_name', type=str, default=None)
@click.option('--nev', default=5)
@click.option('--ncv', default=10)
@click.option('--nitemax', default=350)
@click.option('--tol', default=1.0e-8)
@click.option('--toliter', default=1.0e-3)
@click.option('--alpha', default=0.01)
@click.option('--numit', default=3)
@click.option('--clouds', default=None)
@click.option('--seed', default=None)
def run(
    file,
    out_file,
    var_name,
    mask_name,
    nev,
    ncv,
    nitemax,
    tol,
    toliter,
    alpha,
    numit,
    clouds,
    seed,
):
    """Run pyDINEOF on the given FILE.

    FILE is the path to the gappy time series.
    """
    if file.suffix == '.csv':
        df = pd.read_csv(file)
        if len(df.columns) == 1:
            data = df.iloc[:, -1]
        else:
            data = df[var_name]
        data = run_1D(data, nev, ncv, nitemax, tol, toliter, alpha, numit, clouds, seed)
        data.to_csv(out_file)
    elif file.suffix == '.nc':
        try:
            data = xr.open_dataarray(file)
            mask = None
        except ValueError:
            ds = xr.open_dataset(file)
            data = ds[var_name]
            if mask_name is not None:
                mask = ds[mask_name]
            else:
                mask = None
        data = run_2D(
            data, mask, nev, ncv, nitemax, tol, toliter, alpha, numit, clouds, seed
        )
        data.to_netcdf(out_file)
