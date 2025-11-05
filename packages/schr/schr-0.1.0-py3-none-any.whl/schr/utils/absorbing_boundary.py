r"""Absorbing boundary conditions for quantum simulations.

This module provides various implementations of absorbing boundary conditions
to prevent artificial reflections from domain edges in quantum dynamics simulations.

Available implementations:

- Polynomial masks (:math:`\cos^n` profiles)
- Exponential decay masks
- Complex absorbing potentials (CAP)
- Perfectly matched layers (PML-like)
"""

from typing import Literal

import jax.numpy as jnp
from jax import Array


def polynomial_absorbing_mask(
    coords: Array | tuple[Array, ...],
    domain: tuple[float, float] | tuple[tuple[float, float], ...],
    width: float | tuple[float, ...],
    order: int = 4,
    dtype: jnp.dtype = jnp.float32,
) -> Array:
    r"""Create polynomial absorbing boundary mask using :math:`\cos^n` profile.

    Uses a smooth polynomial profile based on :math:`\cos(\pi t/2)^n` where :math:`t` is the
    normalized distance from the boundary. Higher orders provide stronger absorption.

    Args:
        coords: Grid coordinates. Single 1D array or tuple of arrays for 2D/3D.
        domain: Domain boundaries. (min, max) for 1D or tuple of tuples for 2D/3D.
        width: Absorption layer width (uniform float or per-dimension tuple).
        order: Polynomial order (higher = stronger absorption). Typical: 2-8.
        dtype: JAX dtype for the mask.

    Returns:
        Absorption mask (multiplicative factor from 0 to 1).
        Returns 1.0 in interior and smoothly decreases to 0 near boundaries.

    Raises:
        ValueError: If dimensions are inconsistent.

    Example:
        >>> x = jnp.linspace(-10, 10, 512)
        >>> mask = polynomial_absorbing_mask(x, (-10, 10), width=2.0, order=4)
        >>>
        >>> X, Y = jnp.meshgrid(jnp.linspace(-5, 5, 256), jnp.linspace(-3, 3, 128))
        >>> mask = polynomial_absorbing_mask(
        ...     (X, Y),
        ...     ((-5, 5), (-3, 3)),
        ...     width=1.0,
        ...     order=6
        ... )
    """
    # Normalize inputs
    if isinstance(coords, Array):
        coords = (coords,)

    if not isinstance(domain[0], tuple):
        domain = (domain,)

    ndim = len(coords)
    if len(domain) != ndim:
        raise ValueError(f"Coordinates ({ndim}D) and domain ({len(domain)}D) dimensions mismatch")

    # Handle width
    if isinstance(width, (int, float)):
        widths = (float(width),) * ndim
    else:
        widths = tuple(width)

    if len(widths) != ndim:
        raise ValueError(f"Width dimensions ({len(widths)}) don't match coordinates ({ndim}D)")

    # Initialize mask
    mask = jnp.ones_like(coords[0], dtype=dtype)

    # Apply absorption for each dimension
    for dim_idx, (coord, (coord_min, coord_max), w) in enumerate(zip(coords, domain, widths)):
        # Distance from boundaries
        dist_min = coord - coord_min
        dist_max = coord_max - coord

        # Normalized distance parameter t ∈ [0, 1]
        # t = 0 at boundary, t = 1 at edge of absorption layer
        t_min = jnp.clip(dist_min / w, 0.0, 1.0)
        t_max = jnp.clip(dist_max / w, 0.0, 1.0)

        # Polynomial profile: cos^n(π(1-t)/2)
        # At t=0 (boundary): cos(π/2)^n = 0 (full absorption)
        # At t=1 (interior): cos(0)^n = 1 (no absorption)
        profile_min = jnp.cos(jnp.pi * (1.0 - t_min) / 2.0) ** order
        profile_max = jnp.cos(jnp.pi * (1.0 - t_max) / 2.0) ** order

        # Multiply masks from both boundaries
        mask = mask * profile_min * profile_max

    return mask


def exponential_absorbing_mask(
    coords: Array | tuple[Array, ...],
    domain: tuple[float, float] | tuple[tuple[float, float], ...],
    width: float | tuple[float, ...],
    strength: float = 5.0,
    dtype: jnp.dtype = jnp.float32,
) -> Array:
    """Create exponential absorbing boundary mask.

    Uses exponential decay profile: exp(-strength * (1 - t)^2) where t is the
    normalized distance from boundary. Provides very strong absorption near edges.

    Args:
        coords: Grid coordinates (see polynomial_absorbing_mask).
        domain: Domain boundaries (see polynomial_absorbing_mask).
        width: Absorption layer width.
        strength: Absorption strength parameter (higher = stronger). Typical: 3-10.
        dtype: JAX dtype for the mask.

    Returns:
        Absorption mask (0 to 1).

    Example:
        >>> X, Y = jnp.meshgrid(jnp.linspace(-5, 5, 256), jnp.linspace(-3, 3, 128))
        >>> mask = exponential_absorbing_mask((X, Y), ((-5, 5), (-3, 3)), 1.0, strength=7.0)
    """
    # Normalize inputs
    if isinstance(coords, Array):
        coords = (coords,)

    if not isinstance(domain[0], tuple):
        domain = (domain,)

    ndim = len(coords)

    if isinstance(width, (int, float)):
        widths = (float(width),) * ndim
    else:
        widths = tuple(width)

    # Initialize mask
    mask = jnp.ones_like(coords[0], dtype=dtype)

    # Apply absorption for each dimension
    for coord, (coord_min, coord_max), w in zip(coords, domain, widths):
        dist_min = coord - coord_min
        dist_max = coord_max - coord

        t_min = jnp.clip(dist_min / w, 0.0, 1.0)
        t_max = jnp.clip(dist_max / w, 0.0, 1.0)

        # Exponential profile: exp(-strength * (1-t)^2)
        # Smooth and very strong near boundary
        profile_min = jnp.exp(-strength * (1.0 - t_min) ** 2)
        profile_max = jnp.exp(-strength * (1.0 - t_max) ** 2)

        mask = mask * profile_min * profile_max

    return mask


def complex_absorbing_potential(
    coords: Array | tuple[Array, ...],
    domain: tuple[float, float] | tuple[tuple[float, float], ...],
    width: float | tuple[float, ...],
    strength: float = 1.0,
    order: int = 2,
    dtype: jnp.dtype = jnp.complex64,
) -> Array:
    """Create complex absorbing potential (CAP).

    Generates an imaginary potential -i*η*f(x) that acts as an absorber when
    added to the Hamiltonian. The negative imaginary part causes exponential
    decay of the wavefunction amplitude.

    The CAP method is more sophisticated than simple masks as it properly
    absorbs incoming waves while minimizing reflections.

    Args:
        coords: Grid coordinates (see polynomial_absorbing_mask).
        domain: Domain boundaries (see polynomial_absorbing_mask).
        width: CAP layer width.
        strength: CAP strength parameter η. Typical: 0.1-2.0.
        order: Polynomial order for CAP profile. Typical: 2-4.
        dtype: JAX complex dtype for the potential.

    Returns:
        Complex absorbing potential (purely imaginary, negative values).
        Returns 0 in interior and -i*η*f(x) in absorption layer.

    Example:
        >>> # Use in Hamiltonian: V_total = V_physical + CAP
        >>> X, Y = jnp.meshgrid(jnp.linspace(-5, 5, 256), jnp.linspace(-3, 3, 128))
        >>> cap = complex_absorbing_potential((X, Y), ((-5, 5), (-3, 3)), 1.0, strength=0.5)
        >>> V_total = V_physical + cap
    """
    # Normalize inputs
    if isinstance(coords, Array):
        coords = (coords,)

    if not isinstance(domain[0], tuple):
        domain = (domain,)

    ndim = len(coords)

    if isinstance(width, (int, float)):
        widths = (float(width),) * ndim
    else:
        widths = tuple(width)

    # Initialize CAP (real-valued first, convert to complex at end)
    cap_magnitude = jnp.zeros_like(coords[0], dtype=jnp.float32)

    # Build CAP magnitude for each dimension
    for coord, (coord_min, coord_max), w in zip(coords, domain, widths):
        dist_min = coord - coord_min
        dist_max = coord_max - coord

        # Polynomial CAP: f(x) = ((w - d) / w)^order for d < w, 0 otherwise
        # where d is distance from boundary
        cap_min = jnp.where(dist_min < w, ((w - dist_min) / w) ** order, 0.0)
        cap_max = jnp.where(dist_max < w, ((w - dist_max) / w) ** order, 0.0)

        # Take maximum (not product) to avoid over-absorption at corners
        cap_magnitude = jnp.maximum(cap_magnitude, cap_min)
        cap_magnitude = jnp.maximum(cap_magnitude, cap_max)

    # Convert to complex potential: -i * strength * f(x)
    cap = -1j * strength * cap_magnitude

    return cap.astype(dtype)


def mask_absorbing_potential(
    coords: Array | tuple[Array, ...],
    domain: tuple[float, float] | tuple[tuple[float, float], ...],
    width: float | tuple[float, ...],
    strength: float = 100.0,
    order: int = 2,
    dtype: jnp.dtype = jnp.float32,
) -> Array:
    """Create real-valued absorbing potential (mask potential).

    Similar to CAP but uses a large positive real potential instead of imaginary.
    This creates a "soft wall" that exponentially suppresses the wavefunction.
    Simpler than CAP but may cause more reflections.

    Args:
        coords: Grid coordinates.
        domain: Domain boundaries.
        width: Absorption layer width.
        strength: Potential height. Very large values (50-1000) recommended.
        order: Polynomial order for potential profile.
        dtype: JAX dtype for the potential.

    Returns:
        Real absorbing potential (positive values in absorption layer).

    Example:
        >>> x = jnp.linspace(-10, 10, 512)
        >>> V_absorb = mask_absorbing_potential(x, (-10, 10), width=2.0, strength=500.0)
        >>> V_total = V_physical + V_absorb
    """
    # Normalize inputs
    if isinstance(coords, Array):
        coords = (coords,)

    if not isinstance(domain[0], tuple):
        domain = (domain,)

    ndim = len(coords)

    if isinstance(width, (int, float)):
        widths = (float(width),) * ndim
    else:
        widths = tuple(width)

    # Initialize potential
    V_absorb = jnp.zeros_like(coords[0], dtype=dtype)

    # Build absorbing potential for each dimension
    for coord, (coord_min, coord_max), w in zip(coords, domain, widths):
        dist_min = coord - coord_min
        dist_max = coord_max - coord

        # Polynomial profile
        V_min = jnp.where(dist_min < w, strength * ((w - dist_min) / w) ** order, 0.0)
        V_max = jnp.where(dist_max < w, strength * ((w - dist_max) / w) ** order, 0.0)

        # Add potentials (corners get both)
        V_absorb = V_absorb + V_min + V_max

    return V_absorb


def create_absorbing_boundary(
    coords: Array | tuple[Array, ...],
    domain: tuple[float, float] | tuple[tuple[float, float], ...],
    width: float | tuple[float, ...],
    method: Literal["polynomial", "exponential", "cap", "mask_potential"] = "polynomial",
    **kwargs,
) -> Array:
    """Create absorbing boundary using specified method.

    Convenience function that dispatches to the appropriate absorbing boundary
    implementation.

    Args:
        coords: Grid coordinates.
        domain: Domain boundaries.
        width: Absorption layer width.
        method: Absorbing boundary method:
            - "polynomial": Polynomial mask (cos^n profile)
            - "exponential": Exponential mask
            - "cap": Complex absorbing potential
            - "mask_potential": Real absorbing potential
        **kwargs: Additional method-specific parameters:
            - order: Polynomial order (polynomial, cap, mask_potential)
            - strength: Absorption strength (exponential, cap, mask_potential)
            - dtype: Data type

    Returns:
        Absorbing boundary (mask or potential depending on method).

    Example:
        >>> # Polynomial mask (default)
        >>> X, Y = jnp.meshgrid(jnp.linspace(-5, 5, 256), jnp.linspace(-3, 3, 128))
        >>> mask = create_absorbing_boundary((X, Y), ((-5, 5), (-3, 3)), 1.0)
        >>>
        >>> # Complex absorbing potential
        >>> cap = create_absorbing_boundary(
        ...     (X, Y), ((-5, 5), (-3, 3)), 1.0,
        ...     method="cap", strength=0.5
        ... )
    """
    if method == "polynomial":
        return polynomial_absorbing_mask(coords, domain, width, **kwargs)
    elif method == "exponential":
        return exponential_absorbing_mask(coords, domain, width, **kwargs)
    elif method == "cap":
        return complex_absorbing_potential(coords, domain, width, **kwargs)
    elif method == "mask_potential":
        return mask_absorbing_potential(coords, domain, width, **kwargs)
    else:
        raise ValueError(
            f"Unknown method '{method}'. Choose from: "
            "'polynomial', 'exponential', 'cap', 'mask_potential'"
        )


# Aliases for backward compatibility and convenience
def create_absorption_mask(
    X: Array,
    Y: Array,
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    width: float = 1000.0,
    strength: float = 1.0,
    order: int = 4,
) -> Array:
    """Legacy interface for 2D polynomial absorbing mask.

    Provided for backward compatibility with existing code.

    Args:
        X, Y: 2D coordinate grids.
        x_range: (x_min, x_max) tuple.
        y_range: (y_min, y_max) tuple.
        width: Absorption region width.
        strength: Unused (kept for compatibility).
        order: Polynomial order.

    Returns:
        2D absorption mask.

    Example:
        >>> X, Y = jnp.meshgrid(jnp.linspace(-5, 5, 256), jnp.linspace(-3, 3, 128))
        >>> mask = create_absorption_mask(X, Y, (-5, 5), (-3, 3), width=1.0)
    """
    return polynomial_absorbing_mask((X, Y), (x_range, y_range), width, order=order)
