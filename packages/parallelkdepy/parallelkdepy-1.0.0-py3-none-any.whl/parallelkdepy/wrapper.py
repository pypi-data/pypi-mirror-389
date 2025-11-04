"""
High-level API: Functions and objects that wrap Julia calls.
"""

from typing import Sequence, Optional

from . import core
import numpy as np

# initialize Julia once
core._init_julia()


class Grid:
    """
    Higher level implementation of a grid to use over meshgrid.
    """

    def __init__(
        self,
        ranges: Sequence[tuple] = [],
        *,
        device: str = "cpu",
        b32: Optional[bool] = None,
        grid_jl=None,
    ) -> None:
        if grid_jl is None:
            if (ranges is None) or (len(ranges) == 0):
                raise ValueError("Ranges must be provided to create a grid.")

            grid_jl = core.create_grid(ranges, device=device, b32=b32)

            self._grid_jl = grid_jl
            self._device = device
            self._shape = core.grid_shape(grid_jl)
        else:
            self._grid_jl = grid_jl
            self._device = core.grid_device(grid_jl)
            self._shape = core.grid_shape(grid_jl)

    @property
    def grid_jl(self):
        """
        Underlying Julia grid object.
        """
        return self._grid_jl

    @property
    def device(self):
        """
        Device type, e.g., 'cpu' or 'cuda'.
        """
        return self._device

    @property
    def shape(self):
        """
        Shape of the grid.
        """
        return self._shape

    def to_meshgrid(self) -> tuple[np.ndarray, ...]:
        """
        Mesh grid coordinates
        """
        return core.grid_coordinates(self._grid_jl)

    def step(self) -> list:
        """
        List of step sizes for each dimension of the grid.
        """
        return core.grid_step(self._grid_jl)

    def bounds(self) -> list[tuple]:
        """
        List of tuples of bounds for each dimension of the grid.
        """
        return core.grid_bounds(self._grid_jl)

    def lower_bounds(self) -> list:
        """
        List of lower bounds for each dimension of the grid.
        """
        return [lb for lb, _ in self.bounds()]

    def upper_bounds(self) -> list:
        """
        List of lower bounds for each dimension of the grid.
        """
        return [hb for _, hb in self.bounds()]

    def initial_bandwidth(self) -> list:
        """
        List of the minimum bandwidth that the grid can support in each dimension.
        """
        return core.grid_initial_bandwidth(self._grid_jl)

    def fftgrid(self) -> "Grid":
        """
        Returns a grid of frequency components.
        """
        return Grid(grid_jl=core.grid_fftgrid(self._grid_jl))

    def __eq__(self, other: object) -> bool:
        """
        Check equality with another Grid object.
        """
        if not isinstance(other, Grid):
            return False

        equal_arrays = True
        meshgrid_self = self.to_meshgrid()
        meshgrid_other = other.to_meshgrid()
        for i in range(len(self.shape)):
            if not np.allclose(meshgrid_self[i], meshgrid_other[i]):
                equal_arrays = False
                break

        return (
            self.device == other.device and self.shape == other.shape and equal_arrays
        )


def initialize_dirac_sequence(
    data: np.ndarray,
    grid: Grid,
    *,
    bootstrap_indices: Optional[np.ndarray] = None,
    device: str = "cpu",
    method: Optional[str] = None,
) -> np.ndarray:
    """
    Initialize a Dirac sequence on the given grid.

    Parameters
    ----------
    data : np.ndarray
        Data points to initialize the Dirac sequence.
    grid : Grid
        The grid on which to initialize the Dirac sequence.
    bootstrap_indices : Optional[np.ndarray], optional
        Numpy array of bootstrap indices, by default None. If provided,
        the shape should be (n_bootstraps, n_samples).
    device : str, optional
        Device to store the array, e.g., 'cpu' or 'cuda', by default 'cpu'.
    method : str, optional
        Method to use for initialization, e.g., 'serial' or 'parallel', by default 'serial'.

    Returns
    -------
    np.ndarray
        Numpy array representing the initialized Dirac sequence.
    """
    return core.initialize_dirac_sequence(
        data,
        grid.grid_jl,
        bootstrap_indices=bootstrap_indices,
        device=device,
        method=method,
    )


class DensityEstimation:
    """
    Main API object for density estimation.
    """

    def __init__(
        self,
        data: np.ndarray,
        *,
        grid: Grid | bool = False,
        dims: Optional[Sequence] = None,
        grid_bounds: Optional[Sequence] = None,
        grid_padding: Optional[Sequence] = None,
        device: str = "cpu",
    ) -> None:
        self._data = data
        self._device = device

        if isinstance(grid, Grid):
            if grid.device != device:
                raise ValueError(
                    f"Grid device {grid.device} does not match DensityEstimation device {device}."
                )
            self._grid = grid
        elif grid is True:
            self._grid = Grid(
                grid_jl=core.find_grid(
                    data,
                    grid_dims=dims,
                    grid_bounds=grid_bounds,
                    grid_padding=grid_padding,
                    device=device,
                )
            )
        elif grid is False:
            self._grid = None
        else:
            raise ValueError(
                "Grid must be a Grid object, True to find an appropriate grid, or False to not use a grid."
            )

        if self._grid is not None:
            self._densityestimation_jl = core.create_density_estimation(
                data, grid=self._grid.grid_jl, device=device
            )
        else:
            self._densityestimation_jl = core.create_density_estimation(
                data,
                grid=False,
                dims=dims,
                grid_bounds=grid_bounds,
                grid_padding=grid_padding,
                device=device,
            )
        self._density = core.get_density(self._densityestimation_jl)

    @property
    def data(self):
        """
        Numpy array of data points for density estimation.
        """
        return self._data

    @property
    def device(self):
        """
        Device type, e.g., 'cpu' or 'cuda'.
        """
        return self._device

    @property
    def grid(self):
        """
        Grid used for density estimation, if any.
        """
        return self._grid

    @grid.setter
    def grid(self, value: Grid):
        if not isinstance(value, Grid):
            raise ValueError("Grid must be an instance of the Grid class.")
        if value.device != self.device:
            raise ValueError(
                f"Grid device {value.device} does not match DensityEstimation device {self._device}."
            )
        self._grid = value
        self._densityestimation_jl = core.create_density_estimation(
            self.data, grid=self._grid.grid_jl, device=self._device
        )

    @property
    def density(self):
        """
        Numpy array representing the estimated density.
        """
        return self.get_density()

    def generate_grid(
        self,
        dims: Optional[Sequence] = None,
        grid_bounds: Optional[Sequence] = None,
        grid_padding: Optional[Sequence] = None,
        overwrite: bool = False,
    ) -> Grid:
        """
        Generates a grid based on the data and specified parameters.

        Returns
        -------
        Grid
            A Grid object representing the generated grid.
        """
        if overwrite:
            self.grid = Grid(
                grid_jl=core.find_grid(
                    self.data,
                    grid_dims=dims,
                    grid_bounds=grid_bounds,
                    grid_padding=grid_padding,
                    device=self.device,
                )
            )

            return self.grid
        else:
            if isinstance(self.grid, Grid):
                return self.grid
            else:
                return Grid(
                    grid_jl=core.find_grid(
                        self.data,
                        grid_dims=dims,
                        grid_bounds=grid_bounds,
                        grid_padding=grid_padding,
                        device=self.device,
                    )
                )

    def estimate_density(self, estimation: str, **kwargs) -> None:
        """
        Executes the density estimation algorithm on the data.
        """
        core.estimate_density(self._densityestimation_jl, estimation, **kwargs)
        self._density = core.get_density(self._densityestimation_jl)

    def get_density(self, **kwargs) -> np.ndarray:
        """
        Returns the estimated density as a Numpy array.
        """
        self._density = core.get_density(self._densityestimation_jl, **kwargs)
        return self._density
