"""
Low-level plumbing: Manage Julia session and interfacing between Python and Julia.
"""

from typing import Sequence, Optional
import time

import numpy as np

from juliacall import Main as jl

_initialized = False


def _init_julia():
    global _initialized

    if not _initialized:
        jl.seval("using ParallelKDE")
        _initialized = True


AvailableDevices = ["cpu", "cuda"]
AvailableImplementations = {"cpu": ["serial", "threaded"], "cuda": ["cuda"]}


def str_to_symbol(s: str):
    return jl.Symbol(s)


def device_to_str(device) -> str:
    devices = {
        jl.ParallelKDE.Devices.IsCPU(): "cpu",
        jl.ParallelKDE.Devices.IsCUDA(): "cuda",
    }

    return devices[device]


def create_grid(ranges: Sequence, device: str = "cpu", b32: Optional[bool] = None):
    """
    Create a grid instance of the Julia object `ParallelKDE.Grid`.

    Parameters
    ----------
    ranges : Sequence
        The ranges for the grid.
    device : str, optional
        The device type, e.g., 'cpu' or 'cuda'. Default is 'cpu'.
    b32 : Optional[bool], optional
        Whether to use 32-bit precision for GPU devices.
        Default is None, which behaves as True (32-bit precision) if the device is 'cuda'.
        Setting it as False for 'cuda' devices will use 64-bit precision. This keyword
        argument is ignored when device is 'cpu'.

    Returns
    -------
    juliacall.AnyValue
        The created grid object in Julia.
    """
    ranges = [jl.range(start, stop, length) for start, stop, length in ranges]
    if device not in AvailableDevices:
        raise ValueError(
            f"Unsupported device type: {device}. Available devices: {AvailableDevices}"
        )
    b32 = b32 if b32 is not None else (device != "cpu")

    if device == "cpu":
        grid = jl.initialize_grid(*ranges, b32=b32)
    else:
        grid = jl.initialize_grid(*ranges, device=str_to_symbol(device), b32=b32)

    return grid


def grid_shape(grid_jl) -> tuple:
    return jl.size(grid_jl)


def grid_device(grid_jl) -> str:
    device_jl = jl.ParallelKDE.get_device(grid_jl)
    try:
        return device_to_str(device_jl)
    except KeyError:
        raise ValueError(f"Unsupported device type: {device_jl}")


def grid_coordinates(grid_jl) -> tuple[np.ndarray, ...]:
    coords_np = jl.get_coordinates(grid_jl).to_numpy()

    return tuple(np.ascontiguousarray(coords_np[i]) for i in range(coords_np.shape[0]))


def grid_step(grid_jl) -> list:
    return list(jl.spacings(grid_jl).to_numpy())


def grid_bounds(grid_jl) -> list[tuple]:
    bounds_np = jl.bounds(grid_jl).to_numpy()

    return list(zip(bounds_np[0], bounds_np[1]))


def grid_initial_bandwidth(grid_jl) -> list:
    return list(jl.initial_bandwidth(grid_jl).to_numpy())


def grid_fftgrid(grid_jl):
    return jl.fftgrid(grid_jl)


def find_grid(
    data: np.ndarray,
    grid_bounds: Optional[Sequence[tuple]] = None,
    grid_dims: Optional[Sequence] = None,
    grid_steps: Optional[Sequence] = None,
    grid_padding: Optional[Sequence] = None,
    device: str = "cpu",
):
    data = data.transpose() if data.ndim > 1 else data
    device = str_to_symbol(device)

    return jl.find_grid(
        data,
        grid_bounds=grid_bounds,
        grid_dims=grid_dims,
        grid_steps=grid_steps,
        grid_padding=grid_padding,
        device=device,
    )


def initialize_dirac_sequence(
    data: np.ndarray,
    grid_jl=None,
    bootstrap_indices: Optional[np.ndarray] = None,
    device: str = "cpu",
    method: Optional[str] = None,
) -> np.ndarray:
    """
    Creates a numpy array with the dirac sequence obtained from the data on the grid.

    Parameters
    ----------
    data : np.ndarray
        Numpy array of the data with shape (n_samples, n_features).
    grid_jl
        Julia grid object.
    bootstrap_indices : Optional[np.ndarray], optional
        Optional numpy array of bootstrap indices. If provided, it should have shape (n_bootstraps, n_samples).
    device : str, optional
        The device to store the array, e.g., 'cpu' or 'cuda'. Default is 'cpu'.
    method : str, optional
        The method to use for initializing the Dirac sequence, e.g., 'serial' or 'parallel'. Default is 'serial'.
    """
    if data.ndim != 2:
        raise ValueError("Data must be 2-dimensional (n_samples, n_features).")

    data = data.transpose() if data.ndim > 1 else data

    if device not in AvailableDevices:
        raise ValueError(
            f"Unsupported device type: {device}. Available devices: {AvailableDevices}"
        )
    if (method is not None) and (method not in AvailableImplementations[device]):
        raise ValueError("Unsupported method for the given device type.")
    device = str_to_symbol(device)
    method = str_to_symbol(method) if method is not None else method

    bootstrap_indices = (
        bootstrap_indices.transpose()
        if ((bootstrap_indices is not None) and (bootstrap_indices.ndim > 1))
        else bootstrap_indices
    )

    dirac_sequences = jl.initialize_dirac_sequence(
        data,
        grid=grid_jl,
        bootstrap_idxs=bootstrap_indices,
        device=device,
        method=method,
    ).to_numpy()

    dirac_sequences = np.moveaxis(dirac_sequences, -1, 0)

    return np.ascontiguousarray(dirac_sequences)


def create_density_estimation(
    data: np.ndarray,
    grid,
    dims: Optional[Sequence] = None,
    grid_bounds: Optional[Sequence[tuple]] = None,
    grid_padding: Optional[Sequence] = None,
    device: str = "cpu",
):
    data = data.transpose() if data.ndim > 1 else data

    return jl.initialize_estimation(
        data,
        grid=grid,
        dims=dims,
        grid_bounds=grid_bounds,
        grid_padding=grid_padding,
        device=str_to_symbol(device),
    )


def estimate_density(density_estimation, estimation_method: str, **kwargs):
    kwargs = {
        k: str_to_symbol(v) if isinstance(v, str) else v for k, v in kwargs.items()
    }
    jl.estimate_density_b(
        density_estimation, str_to_symbol(estimation_method), **kwargs
    )

    return None


def get_density(density_estimation, **kwargs) -> np.ndarray:
    density = jl.get_density(density_estimation, **kwargs)
    density_np = density.to_numpy()

    return np.ascontiguousarray(density_np)
