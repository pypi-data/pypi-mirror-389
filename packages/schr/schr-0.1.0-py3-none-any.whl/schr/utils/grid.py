"""Grid generation utilities for quantum simulations."""

import jax.numpy as jnp
from jax import Array


def create_grid_1d(
    x_min: float, x_max: float, nx: int, dtype: jnp.dtype = jnp.float32
) -> tuple[Array, float]:
    """Create 1D spatial grid.

    Args:
        x_min: Minimum x coordinate (a.u.).
        x_max: Maximum x coordinate (a.u.).
        nx: Number of grid points.
        dtype: JAX dtype (default: float32).

    Returns:
        Tuple (x, dx): Grid points and spacing (a.u.).

    Raises:
        ValueError: If nx < 2 or x_max <= x_min.
    """
    if nx < 2:
        raise ValueError(f"Grid size nx must be at least 2, got {nx}")
    if x_max <= x_min:
        raise ValueError(f"x_max ({x_max}) must be > x_min ({x_min})")

    dx = (x_max - x_min) / (nx - 1)
    x = jnp.linspace(x_min, x_max, nx, dtype=dtype)
    return x, dx


def create_grid_2d(
    x_min: float,
    x_max: float,
    nx: int,
    y_min: float,
    y_max: float,
    ny: int,
    dtype: jnp.dtype = jnp.float32,
) -> tuple[Array, Array, float, float]:
    """Create 2D spatial grid.

    Args:
        x_min: Minimum x coordinate (a.u.).
        x_max: Maximum x coordinate (a.u.).
        nx: Number of x grid points.
        y_min: Minimum y coordinate (a.u.).
        y_max: Maximum y coordinate (a.u.).
        ny: Number of y grid points.
        dtype: JAX dtype (default: float32).

    Returns:
        Tuple (X, Y, dx, dy): 2D meshgrid arrays (shape: ny × nx) and spacings (a.u.).

    Raises:
        ValueError: If grid parameters are invalid.
    """
    if nx < 2 or ny < 2:
        raise ValueError(f"Grid sizes must be at least 2, got nx={nx}, ny={ny}")
    if x_max <= x_min:
        raise ValueError(f"x_max ({x_max}) must be > x_min ({x_min})")
    if y_max <= y_min:
        raise ValueError(f"y_max ({y_max}) must be > y_min ({y_min})")

    dx = (x_max - x_min) / (nx - 1)
    dy = (y_max - y_min) / (ny - 1)

    x = jnp.linspace(x_min, x_max, nx, dtype=dtype)
    y = jnp.linspace(y_min, y_max, ny, dtype=dtype)
    X, Y = jnp.meshgrid(x, y, indexing="xy")

    return X, Y, dx, dy


def create_grid_3d(
    x_min: float,
    x_max: float,
    nx: int,
    y_min: float,
    y_max: float,
    ny: int,
    z_min: float,
    z_max: float,
    nz: int,
    dtype: jnp.dtype = jnp.float32,
) -> tuple[Array, Array, Array, float, float, float]:
    """Create 3D spatial grid.

    Args:
        x_min: Minimum x coordinate (a.u.).
        x_max: Maximum x coordinate (a.u.).
        nx: Number of x grid points.
        y_min: Minimum y coordinate (a.u.).
        y_max: Maximum y coordinate (a.u.).
        ny: Number of y grid points.
        z_min: Minimum z coordinate (a.u.).
        z_max: Maximum z coordinate (a.u.).
        nz: Number of z grid points.
        dtype: JAX dtype (default: float32).

    Returns:
        Tuple (X, Y, Z, dx, dy, dz): 3D meshgrid arrays (shape: nz × ny × nx) and spacings (a.u.).

    Raises:
        ValueError: If grid parameters are invalid.
    """
    if nx < 2 or ny < 2 or nz < 2:
        raise ValueError(f"Grid sizes must be at least 2, got nx={nx}, ny={ny}, nz={nz}")
    if x_max <= x_min:
        raise ValueError(f"x_max ({x_max}) must be > x_min ({x_min})")
    if y_max <= y_min:
        raise ValueError(f"y_max ({y_max}) must be > y_min ({y_min})")
    if z_max <= z_min:
        raise ValueError(f"z_max ({z_max}) must be > z_min ({z_min})")

    dx = (x_max - x_min) / (nx - 1)
    dy = (y_max - y_min) / (ny - 1)
    dz = (z_max - z_min) / (nz - 1)

    x = jnp.linspace(x_min, x_max, nx, dtype=dtype)
    y = jnp.linspace(y_min, y_max, ny, dtype=dtype)
    z = jnp.linspace(z_min, z_max, nz, dtype=dtype)
    X, Y, Z = jnp.meshgrid(x, y, z, indexing="xy")

    return X, Y, Z, dx, dy, dz
