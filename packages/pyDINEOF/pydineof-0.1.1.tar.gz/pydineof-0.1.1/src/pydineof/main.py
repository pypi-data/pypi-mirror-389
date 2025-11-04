# Copyright (C) 2025  Arthur Coqué, RBINS

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""The main module of pyDINEOF.

Available functions
-------------------
run_1D
    Run a monovariate DINEOF reconstruction of a given 1-D time series.
run_2D
    Run a monovariate DINEOF reconstruction of a given 2-D time series.
"""

import datetime
import math
import time

import numpy as np
import pandas as pd
import xarray as xr
from numpy.typing import NDArray
from scipy.sparse.linalg import eigsh

__version__ = '0.1.0'


def run_1D(
    data: pd.Series,
    nev: int = 5,
    ncv: int = 10,
    tol: float = 1.0e-8,
    nitemax: int = 350,
    toliter: float = 1.0e-3,
    alpha: float = 0.01,
    numit: int = 3,
    clouds=None,
    rec: bool = True,
    seed: int | None = None,
) -> pd.Series:
    """Run a monovariate DINEOF reconstruction of a given 1-D time series.

    Args:
        data: Gappy time series to be filled with DINEOF.
        nev: Maximum number of EOF modes to compute.
        ncv: Maximal size of the Krylov subspace. Must satisfy "ncv > nev + 5"
            and "ncv < len(data)".
        tol: Convergence tolerance for the Lanczos algorithm.
        nitemax: Maximum number of iterations allowed for the stabilisation of the
            <EOF decomposition> / <truncated reconstruction and replacement of missing
            data> cycle.
        toliter: Automatic-stop threshold: the iteration stops when the ratio
            "RMS(successive_reconstructed_missing_data) / std(existing data)" falls
            below this value.
        alpha: Parameter controlling the strength of the smoothing term of the
            temporal filter. If 0, deactivate the filter.
        numit: Number of iterations performed by the temporal filter.
        clouds: User-provided cross-validation points. If "None",
            points are selected randomly.
        rec: If "True" (default), reconstruct the entire series; if
            "False", only the missing entries.
        seed: Seed for the NumPy random generator to obtain reproducible
            cross-validation splits.

    Returns:
        Gap-filled time series (pd.Series) with the same index as "data".

    Raises:
        ValueError: If "ncv" does not satisfy "ncv > nev + 5" or "ncv < len(data)".
    """
    if ncv <= nev + 5:
        raise ValueError(f'ncv > nev + 5, got ncv={ncv} and nev={nev}')
    if ncv >= len(data):
        raise ValueError(
            f'ncv < len(data) expected, got ncv={ncv} and len(data)={data}'
        )
    X = np.atleast_2d(data.to_numpy())
    X = np.where(X > 0, X, np.nan)  # filter data
    mean_ = np.nanmean(np.log(X))
    arr_time = _get_arr_time(data.index.to_numpy())
    X = np.exp(
        _main(
            np.log(X) - mean_,
            arr_time,
            nev,
            ncv,
            tol,
            nitemax,
            toliter,
            alpha,
            numit,
            clouds,
            rec,
            seed,
        )
        + mean_
    ).ravel()
    data = pd.Series(X, index=data.index, name=data.name)
    print('\n...done!')
    return data


def run_2D(
    data: xr.DataArray,
    mask: xr.DataArray | None = None,
    nev: int = 5,
    ncv: int = 10,
    tol: float = 1.0e-8,
    nitemax: int = 350,
    toliter: float = 1.0e-3,
    alpha: float = 0.01,
    numit: int = 3,
    clouds=None,
    rec: bool = True,
    seed: int | None = None,
) -> xr.DataArray:
    """Run a monovariate DINEOF reconstruction of a given 2-D time series.

    Args:
        data: Gappy time series to be filled with DINEOF.
        mask: Binary mask to select the area to be processed. "1" or "True" for pixels
            to be used in DINEOF, "0" or "False" for pixels to be excluded.
        nev: Maximum number of EOF modes to compute.
        ncv: Maximal size of the Krylov subspace. Must satisfy "ncv > nev + 5"
            and "ncv < len(time)".
        tol: Convergence tolerance for the Lanczos algorithm.
        nitemax: Maximum number of iterations allowed for the stabilisation of the
            <EOF decomposition> / <truncated reconstruction and replacement of missing
            data> cycle.
        toliter: Automatic-stop threshold: the iteration stops when the ratio
            "RMS(successive_reconstructed_missing_data) / std(existing data)" falls
            below this value.
        alpha: Parameter controlling the strength of the smoothing term of the
            temporal filter. If 0, deactivate the filter.
        numit: Number of iterations performed by the temporal filter.
        clouds: User-provided cross-validation points. If "None",
            points are selected randomly.
        rec: If "True" (default), reconstruct the entire series; if
            "False", only the missing entries.
        seed: Seed for the NumPy random generator to obtain reproducible
            cross-validation splits.

    Returns:
        Gap-filled time series with the same structure and metadata as "data".

    Raises:
        ValueError: If "ncv" does not satisfy "ncv > nev + 5" or "ncv < len(time)".
    """
    if ncv <= nev + 5:
        raise ValueError(f'ncv > nev + 5, got ncv={ncv} and nev={nev}')
    if ncv >= len(data.time):
        raise ValueError(
            f'ncv < len(time) expected, got ncv={ncv} and len(data)={data.time}'
        )
    try:
        X = (
            data.astype(np.float32)
            .stack(M=('y', 'x'))
            .rename(time='N')
            .transpose('M', 'N')
        )
        if mask is not None:
            mask = mask.astype(bool).stack(M=('y', 'x')).values  # type: ignore
    except KeyError:
        X = (
            data.astype(np.float32)
            .stack(M=('lat', 'lon'))
            .rename(time='N')
            .transpose('M', 'N')
        )
        if mask is not None:
            mask = mask.astype(bool).stack(M=('lat', 'lon')).values  # type: ignore
    X = X.where(X > 0)  # filter data
    mean_ = np.nanmean(np.log(X))
    arr_time = _get_arr_time(X.N.values)
    if mask is None:
        mask = np.ones((X.M.size), dtype=bool)
    X.values[mask] = np.exp(
        _main(
            np.log(X.values[mask].copy()) - mean_,  # center data
            arr_time,
            nev,
            ncv,
            tol,
            nitemax,
            toliter,
            alpha,
            numit,
            clouds,
            rec,
            seed,
        )
        + mean_
    )
    img = X.transpose('N', 'M').rename(N='time').unstack('M')
    print('\n...done!')
    return img


def _main(
    Xo: NDArray[np.float32],
    arr_time: NDArray[np.uint16],
    nev: int,
    ncv: int,
    tol: float,
    nitemax: int,
    toliter: float,
    alpha: float,
    numit: int,
    clouds=None,
    rec: bool = True,
    seed: int | None = None,
) -> NDArray[np.float32]:
    """Apply DINEOF to a given observed field.

    Args:
        Xo: The observed field with gappy data (as NaNs).
        nev: Maximum number of EOF modes to compute.
        ncv: Maximal size of the Krylov subspace. Must satisfy "ncv > nev + 5"
            and "ncv < len(Xo.N)".
        tol: Convergence tolerance for the Lanczos algorithm.
        nitemax: Maximum number of iterations allowed for the stabilisation of the
            <EOF decomposition> / <truncated reconstruction and replacement of missing
            data> cycle.
        toliter: Automatic-stop threshold: the iteration stops when the ratio
            "RMS(successive_reconstructed_missing_data) / std(existing data)" falls
            below this value.
        alpha: Parameter controlling the strength of the smoothing term of the
            temporal filter.
        numit: Number of iterations performed by the temporal filter.
        clouds: User-provided cross-validation points. If "None",
            points are selected randomly.
        rec: If "True" (default), reconstruct the entire series; if
            "False", only the missing entries.
        seed: Seed for the NumPy random generator to obtain reproducible
            cross-validation splits.

    Raises:
        ValueError: If "ncv" does not satisfy "ncv > nev + 5" or "ncv < len(data)".
        ValueError: If not enough observations (i.e. if too much gaps).

    Returns:
        The analyzed field (i.e. the observed field where missing data were filled in).
    """
    ###########################################################################
    # Init --------------------------------------------------------------------
    if ncv <= nev + 5:
        raise ValueError(f'ncv > nev + 5, got ncv={ncv} and nev={nev}')
    nan_rows = np.isnan(Xo).all(axis=1)
    Xo = Xo[~nan_rows]
    M, N = Xo.shape  # M = x*y, N = time
    if ncv >= N:
        raise ValueError(f'ncv < N expected, got ncv={ncv} and N={N}')
    print(
        'Matrix loaded... Constant timeseries removed...\n'
        f'\tSize of the input matrix: {M + nan_rows.sum()} x {N}\n'
        f'\tSize of the matrix used in DINEOF: {M} x {N}\n'
    )
    # "missing" data (gaps + cross-validation)
    idx_miss = np.isnan(Xo).nonzero()
    n_miss = len(idx_miss[0])
    n_cv = math.floor(min(0.01 * M * N + 40, 0.03 * M * N))
    if n_miss + n_cv >= M * N:
        raise ValueError('Not enough valid observations.')  # for cross-validation
    if clouds is not None:
        idx_cv = clouds
        n_cv = len(idx_cv[0])
    else:
        idx_cv = _select_test_set(Xo, n_cv, seed)
    print(
        f'Missing data: {n_miss} out of {M * N} ({100 * n_miss / M / N}%)\nNumber of cross-validation points: {n_cv}\n'
    )
    idx_misst = tuple((np.append(idx_miss[i], idx_cv[i]) for i in range(2)))

    ###########################################################################
    # First guess of EOF 1 ----------------------------------------------------
    Xo = np.nan_to_num(Xo)  # type: ignore
    Xo_cv = Xo[idx_cv]
    # stats
    varini = (Xo**2).sum() / (M * N - n_miss)
    stdvini = np.sqrt(varini)
    # remove test set from the observed field
    Xa = Xo
    Xa[idx_cv] = 0
    # first guess
    mytol = 0
    t1 = time.perf_counter()
    u, s, v = _ssvd_lancz(
        Xa,
        nev,  # according to papers, it is supposed to be k=1...
        ncv,
        tol,
        mytol,
        arr_time,
        alpha=alpha,
        numit=numit,
        u=np.empty((M, nev), dtype=np.float32),
        s=np.empty((nev), dtype=np.float32),
        v=np.empty((N, nev), dtype=np.float32),
    )
    t2 = time.perf_counter()
    print(f'Time (in seconds) for 1 EOF mode calculation in DINEOF: {(t2 - t1):0.4f}\n')
    Xa[idx_misst] = (u @ np.diag(s) @ np.transpose(v))[idx_misst]

    ###########################################################################
    # Loop on "nev" modes asked for reconstruction
    print(
        f'EOF modes asked: {nev}    Convergence level required: {toliter}\n'
        'Starting with the EOF mode calculation...\n'
        'EOF mode    Expected Error    Iterations made   Convergence achieved\n'
        '________    ______________    _______________   ____________________'
    )
    # main loop
    valc = []
    valcopt = 10000
    valosc = -np.ones((nev, nitemax))
    nitedone = np.zeros(nev, dtype=np.uint16)
    Xlast_misst = np.zeros(n_miss + n_cv)
    for p in range(nev):
        for nite in range(nitemax):
            u, s, v = _ssvd_lancz(
                Xa,
                p + 1,
                ncv,
                tol,
                mytol,
                arr_time,
                alpha=alpha,
                numit=numit,
                u=u,
                s=s,
                v=v,
            )
            Xa[idx_misst] = (
                u[:, : p + 1] @ np.diag(s[: p + 1]) @ np.transpose(v)[: p + 1]
            )[idx_misst]
            val = (
                np.sqrt(((Xa[idx_misst] - Xlast_misst) ** 2).sum() / (n_miss + n_cv))
                / stdvini
            )
            Xlast_misst = Xa[idx_misst]
            valosc[p, nite] = val
            nitedone[p] = nite + 1
            # print(p + 1, nite + 1)
            if val < toliter:
                break
        # calculate cross-validator
        valc.append(np.sqrt(((Xa[idx_cv] - Xo_cv) ** 2).sum() / n_cv))
        # store best guess
        if valc[p] < valcopt:
            valcopt = valc[p]
            popt = p
            Xmiss_best = Xa[idx_miss]
        print(
            f'{str(p + 1).rjust(8, " ")}    {str(valc[p]).rjust(14, " ")}    '
            f'{str(nitedone[p]).rjust(15, " ")}    '
            f'{str(valosc[p, nitedone[p] - 1]).rjust(20, " ")}'
        )
        mytol = (valc[p] - valc[p - 1]) / 100 / valc[p]
        if p > 2:
            if (
                (valc[p] > valc[p - 1])
                and (valc[p - 1] > valc[p - 2])
                and (valc[p - 2] > valc[p - 3])
            ):
                print('STOP')
                break

    ###########################################################################
    # Recalculate the EOFs for Popt with the points initially put aside for the
    # cross-validation --------------------------------------------------------
    t3 = time.perf_counter()
    p = popt + 1
    print(f'Minimum reached in cross-validation.\nNumber of optimal EOF modes: {p}\n')
    Xa[idx_miss] = Xmiss_best
    Xa[idx_cv] = Xo_cv
    valosclast = -np.ones(nitemax)
    nite = 0
    Xlast_miss = np.zeros_like(Xmiss_best)
    print('Make last reconstruction, including data put aside for cross-validation.')
    while nite < nitemax:
        u, s, v = _ssvd_lancz(
            Xa,
            p,
            ncv,
            tol,
            mytol,
            arr_time,
            alpha=alpha,
            numit=numit,
            u=u,
            s=s,
            v=v,
            resid=v[:, 0].copy(),
        )
        Xa[idx_miss] = (u[:, :p] @ np.diag(s[:p]) @ np.transpose(v[:, :p]))[
            idx_miss
        ]  # MISST (and not MISS) in original DINEOF
        val = np.sqrt(((Xa[idx_miss] - Xlast_miss) ** 2).sum() / n_miss) / stdvini
        Xlast_miss = Xa[idx_miss]
        valosclast[nite] = val
        nite += 1
        if val < toliter:
            break
    print(
        f'{p}    {valc[popt]}    {nitedone[popt]}    {valosc[popt, nitedone[popt] - 1]}'
    )
    print(f'\tStop after iteration {nite}, with valosc={valosclast[nite - 1]}\n')
    varend = (Xa**2).sum() / (M * N - len(np.isnan(Xa).nonzero()))
    # Reconstruct the matrix with the EOFs retained as optimal
    if rec:
        Xa = u[:, :p] @ np.diag(s[:p]) @ np.transpose(v[:, :p])
    print(
        'DINEOF finished!\n'
        f'Number of eigenvalues retained for the reconstruction: {p}\n'
        f'Expected error calculated by cross-validation: {valc[popt]}\n'
        f'Total time (in minutes) in lanczos process: {(t3 - t1) / 60}'
    )
    print('\nNow writing data...\n')
    print(
        f'Total variance of the initial matrix: {varini}\n'
        f'Total variance of the reconstructed matrix: {varend}\n'
        f'Sum of the squares of the singular values of the {s[:p].size} '
        f'EOFs retained {np.sum(100.0 * s[:p] ** 2 / (M * N * varend))}'
    )
    X = np.full((M + nan_rows.sum(), N), np.nan, dtype=np.float32)  # type: ignore
    X[~nan_rows] = Xa
    return X


def _get_arr_time(time_coordinate: list | NDArray) -> NDArray[np.uint16]:
    # TODO: write docstring
    if isinstance(time_coordinate, list):
        time_coordinate = np.array(time_coordinate)
    if np.issubdtype(time_coordinate.dtype, np.integer) or np.issubdtype(
        time_coordinate.dtype, np.floating
    ):
        ts_coordinate = time_coordinate - time_coordinate[0]
    else:
        if isinstance(
            time_coordinate.dtype, datetime.date | datetime.datetime | pd.Timestamp
        ):
            time_coordinate = time_coordinate.astype(np.datetime64)
        ts_coordinate = (
            time_coordinate - np.datetime64('1970-01-01')
        ) / np.timedelta64(1, 's')
        ts_coordinate -= ts_coordinate[0]
    return ts_coordinate.astype(np.uint16)


def _select_test_set(
    Xo: NDArray[np.float32], n_cv: int, seed: int | None = None
) -> tuple[NDArray[np.intp], ...]:
    """Randomly select 'n_cv' pixels (test set) from the array 'Xo'.

    Args:
        Xo: The observed field with gappy data (as NaNs).
        n_cv: The number of pixels to extract.
        seed: A seed to initialize the Generator (from numpy.random).
            If none, then fresh, unpredictable entropy will be pulled from the OS.
            If an (non negative) int is passed, it will be used instead.

    Returns:
        Indices of all test pixels.
    """
    ss = np.random.SeedSequence(seed)
    print(f'seed = {ss.entropy}')  # NOTE: should be add to output product metatada
    rng = np.random.default_rng(ss)
    idx_valid = (~np.isnan(Xo)).nonzero()
    sample = rng.choice(len(idx_valid[0]), size=n_cv, replace=False)
    return tuple(idx_valid[i][sample] for i in range(2))


def _ssvd_lancz(A, nev, ncv, tol, mytol, arr_time, alpha, numit, u, s, v, resid=None):
    """Compute 'nev' singular values (along with left/right singular vectors).

    The computation of the singular elements is performed using scipy.eigsh(), a wrapper
    to the ARPACK SSEUPD function (which uses the Implicitly Restarted Lanczos Method
    to find the eigenvalues and eigenvectors).

    Args:
        A: _description_
        nev: Maximum number of EOF modes to compute.
        ncv: Maximal size of the Krylov subspace.
        tol: Convergence tolerance for the Lanczos algorithm.
        mytol: _description_
        arr_time: _description_
        alpha: Parameter controlling the strength of the smoothing term of the
            temporal filter.
        numit: Number of iterations performed by the temporal filter.
        u: _description_
        s: _description_
        v: _description_
        resid: Starting vector for iteration.

    Returns:
        A tuple containing u, s, and v, with u the left singular vectors, s the singular
        values, and v the right singular vector.
    """  # TODO: complete docstring
    M, N = A.shape
    B = np.transpose(A) @ A
    B = _get_diff(B, arr_time, alpha, numit)
    B = _get_diff(B, arr_time, alpha, numit)  # NOTE: why twice?
    newtol = np.float32(max(tol, mytol))
    eigenvalues, eigenvectors = eigsh(
        B, k=nev, which='LA', ncv=ncv, maxiter=N, tol=newtol, v0=resid
    )
    v[:, :nev] = np.flip(eigenvectors, axis=1)
    s[:nev] = np.sqrt(np.flip(eigenvalues))
    for k in range(nev):
        lsv = A @ v[:, k]
        lsv /= s[k]
        u[:, k] = lsv / np.linalg.norm(lsv)  # ord=2?
    return u, s, v


def _get_diff(B, arr_time, alpha, numit):
    # TODO: write docstring
    Bp = np.zeros_like(B)
    for i in range(B.shape[1]):
        Bp2 = B[i]
        Bp[i] = _dindiff(arr_time, Bp2, alpha, numit)
    return np.transpose(Bp)  # adjoint of Bp


def _dindiff(x, B, alpha, numit):  # x <=> time; B <=> Bp2
    """Setup temporal filter.

    To know the length of the filter: 2*pi sqrt(alpha*numit). For example,
    2*pi * sqrt(0.01*3) = 1.09 days filter (in case of daily time step).
    See http://www.ocean-sci.net/5/475/2009/os-5-475-2009.pdf for more information.

    Args:
        x: Time vector, indicating the increment between time steps in data file (must
            have same time dimension as data file).
        B: Input hermitian matrix.
        alpha: Parameter specifying the strength of the filter. If 0, deactivates the filter.
        numit: Number of iterations for the filter.

    Returns:
        The input hermitian matrix, "(temporally) smoothed".
    """
    BF = np.zeros(len(B) + 1, dtype=np.float32)
    xe = np.zeros(len(x) + 1, dtype=np.float32)  # len(x) = len(B)
    xe[0] = 1.5 * x[0] - 0.5 * x[1]
    xe[1:-1] = (x[:-1] + x[1:]) / 2
    xe[-1] = 1.5 * x[-1] - 0.5 * x[-2]
    for _ in range(numit):
        BF[1:-1] = alpha * (B[1:] - B[:-1]) / (x[1:] - x[:-1])
        B = B + (BF[1:] - BF[:-1]) / (xe[1:] - xe[:-1])
    return B
