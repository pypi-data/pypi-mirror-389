"""Wavefunction utilities for quantum mechanics."""

import jax.numpy as jnp
from jax import Array


def gaussian_wavepacket(
    x: Array | tuple[Array, ...],
    x0: float | tuple[float, ...],
    p0: float | tuple[float, ...],
    sigma: float,
    hbar: float = 1.0,
    dtype: jnp.dtype = jnp.complex64,
) -> Array:
    r"""Create Gaussian wave packet.

    .. math::
        \psi(\mathbf{r}) = (2\pi\sigma^2)^{-d/4} \exp\left[-\frac{(\mathbf{r}-\mathbf{r}_0)^2}{4\sigma^2}\right]
        \exp\left[\frac{i\mathbf{p}_0\cdot(\mathbf{r}-\mathbf{r}_0)}{\hbar}\right]

    where :math:`d` is the dimensionality.

    Args:
        x: Spatial grid. 1D: array (nx,). 2D: tuple (X, Y) of shape (ny, nx). 3D: tuple (X, Y, Z).
        x0: Center position (a.u.). Scalar for 1D, tuple for 2D/3D.
        p0: Initial momentum (a.u.). Scalar for 1D, tuple for 2D/3D.
        sigma: Width parameter (a.u.).
        hbar: Reduced Planck constant (default: 1.0 a.u.).
        dtype: JAX dtype (default: complex64).

    Returns:
        Normalized Gaussian wave packet.

    Raises:
        ValueError: If dimensions are inconsistent.
    """
    if isinstance(x, tuple):
        ndim = len(x)
        if ndim not in (2, 3):
            raise ValueError(f"Tuple x must have 2 or 3 elements, got {ndim}")
        if not isinstance(x0, tuple) or len(x0) != ndim:
            raise ValueError(f"x0 must be a tuple of length {ndim}")
        if not isinstance(p0, tuple) or len(p0) != ndim:
            raise ValueError(f"p0 must be a tuple of length {ndim}")
    else:
        ndim = 1
        if not isinstance(x0, (int, float)):
            raise ValueError("For 1D, x0 must be a scalar")
        if not isinstance(p0, (int, float)):
            raise ValueError("For 1D, p0 must be a scalar")

    norm = (2 * jnp.pi * sigma**2) ** (-ndim / 4)

    if ndim == 1:
        dx = x - x0
        r_squared = dx**2
        p_dot_r = p0 * dx
    else:
        dx_components = [x[i] - x0[i] for i in range(ndim)]
        r_squared = sum(dx**2 for dx in dx_components)
        p_dot_r = sum(p0[i] * dx_components[i] for i in range(ndim))

    psi = norm * jnp.exp(-r_squared / (4 * sigma**2))
    psi = psi * jnp.exp(1j * p_dot_r / hbar)

    return psi.astype(dtype)


def normalize(psi: Array, dx: float) -> Array:
    r"""Normalize wavefunction to :math:`\int|\psi|^2 dV = 1`.

    Args:
        psi: Wavefunction.
        dx: Grid spacing (a.u., uniform in all dimensions).

    Returns:
        Normalized wavefunction.
    """
    ndim = psi.ndim
    dv = dx**ndim
    norm = jnp.sqrt(jnp.sum(jnp.abs(psi) ** 2) * dv)
    return psi / norm


def plane_wave(
    x: Array | tuple[Array, ...],
    k: float | tuple[float, ...],
    dtype: jnp.dtype = jnp.complex64,
) -> Array:
    r"""Create plane wave :math:`\exp(i\mathbf{k}\cdot\mathbf{r})`.

    Args:
        x: Spatial grid (1D array or tuple of arrays).
        k: Wave vector (a.u.). Scalar for 1D, tuple for 2D/3D.
        dtype: JAX dtype (default: complex64).

    Returns:
        Plane wave (not normalized).

    Raises:
        ValueError: If dimensions are inconsistent.
    """
    if isinstance(x, tuple):
        ndim = len(x)
        if not isinstance(k, tuple) or len(k) != ndim:
            raise ValueError(f"k must be a tuple of length {ndim}")
        k_dot_x = sum(k[i] * x[i] for i in range(ndim))
    else:
        if not isinstance(k, (int, float)):
            raise ValueError("For 1D, k must be a scalar")
        k_dot_x = k * x

    return jnp.exp(1j * k_dot_x).astype(dtype)


def probability_density(psi: Array) -> Array:
    r"""Compute probability density :math:`|\psi|^2`.

    Args:
        psi: Wavefunction.

    Returns:
        Probability density.
    """
    return jnp.abs(psi) ** 2


def probability_current_1d(psi: Array, dx: float, mass: float = 1.0, hbar: float = 1.0) -> Array:
    r"""Compute probability current density in 1D.

    .. math::
        j = \frac{\hbar}{m} \text{Im}\left[\psi^* \frac{\partial\psi}{\partial x}\right]

    Args:
        psi: Wavefunction (1D).
        dx: Grid spacing (a.u.).
        mass: Particle mass (default: 1.0 a.u.).
        hbar: Reduced Planck constant (default: 1.0 a.u.).

    Returns:
        Probability current density.
    """
    dpsi_dx = jnp.gradient(psi, dx)
    j = (hbar / mass) * jnp.imag(jnp.conj(psi) * dpsi_dx)
    return j
