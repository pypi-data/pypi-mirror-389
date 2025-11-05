"""FFT utilities for quantum simulations."""

import jax.numpy as jnp
from jax import Array


def fftfreq_grid(n: int, d: float, dtype: jnp.dtype = jnp.float32) -> Array:
    """Create frequency grid for FFT operations.

    Args:
        n: Number of grid points.
        d: Grid spacing (a.u.).
        dtype: JAX dtype (default: float32).

    Returns:
        Frequency array (rad/a.u.).
    """
    return jnp.fft.fftfreq(n, d=d).astype(dtype) * 2 * jnp.pi


def momentum_operator(
    shape: tuple[int, ...], dx: float, hbar: float = 1.0, dtype: jnp.dtype = jnp.float32
) -> tuple[Array, ...]:
    r"""Create momentum operators in Fourier space.

    For kinetic energy: :math:`\hat{T} = \frac{\hbar^2k^2}{2m}`.

    Args:
        shape: Grid shape (nx,) for 1D, (ny, nx) for 2D, (nz, ny, nx) for 3D.
        dx: Grid spacing (a.u., uniform).
        hbar: Reduced Planck constant (a.u., default: 1.0).
        dtype: JAX dtype (default: float32).

    Returns:
        Tuple of momentum operators (one per dimension):
        - 1D: (kx,) of shape (nx,)
        - 2D: (kx, ky) of shapes (ny, nx) each
        - 3D: (kx, ky, kz) of shapes (nz, ny, nx) each

    Raises:
        ValueError: If ndim > 3.
    """
    ndim = len(shape)
    if ndim > 3:
        raise ValueError(f"Only 1D, 2D, and 3D grids supported, got {ndim}D")

    k_arrays = []
    for i, n in enumerate(shape):
        k = fftfreq_grid(n, dx, dtype=dtype) * hbar
        k_arrays.append(k)

    if ndim == 1:
        return (k_arrays[0],)
    elif ndim == 2:
        ny, nx = shape
        kx = jnp.broadcast_to(k_arrays[1][None, :], (ny, nx))
        ky = jnp.broadcast_to(k_arrays[0][:, None], (ny, nx))
        return kx, ky
    else:  # ndim == 3
        nz, ny, nx = shape
        kx = jnp.broadcast_to(k_arrays[2][None, None, :], (nz, ny, nx))
        ky = jnp.broadcast_to(k_arrays[1][None, :, None], (nz, ny, nx))
        kz = jnp.broadcast_to(k_arrays[0][:, None, None], (nz, ny, nx))
        return kx, ky, kz


def fft_derivative(f: Array, dx: float, axis: int = -1, order: int = 1) -> Array:
    r"""Compute spectral derivative using FFT.

    Spectral accuracy with periodic boundaries. Derivatives in Fourier space:

    - 1st order: multiply by :math:`ik`
    - 2nd order: multiply by :math:`-k^2`

    Args:
        f: Function values on uniform grid.
        dx: Grid spacing (a.u.).
        axis: Axis for derivative (default: -1 = last axis).
        order: Derivative order (1 or 2).

    Returns:
        :math:`\partial^n f/\partial x^n`.

    Raises:
        ValueError: If order not in {1, 2}.
    """
    if order not in (1, 2):
        raise ValueError(f"Only order 1 and 2 derivatives supported, got {order}")

    n = f.shape[axis]
    k = fftfreq_grid(n, dx, dtype=f.dtype if jnp.isrealobj(f) else jnp.float32)

    shape = [1] * f.ndim
    shape[axis] = n
    k = k.reshape(shape)

    f_hat = jnp.fft.fft(f, axis=axis)

    if order == 1:
        df_hat = 1j * k * f_hat
    else:  # order == 2
        df_hat = -(k**2) * f_hat

    df = jnp.fft.ifft(df_hat, axis=axis)

    if jnp.isrealobj(f):
        df = jnp.real(df)

    return df
