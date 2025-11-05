"""Hamiltonian implementations for quantum mechanics."""

from collections.abc import Callable

import jax.numpy as jnp
from jax import Array

from schr.core.base import Hamiltonian
from schr.utils.fft import momentum_operator


class ParticleInPotential(Hamiltonian):
    r"""Hamiltonian for particle in arbitrary potential.

    .. math::
        \hat{H} = -\frac{\hbar^2}{2m}\nabla^2 + V(\mathbf{r}, t)

    Attributes:
        potential: Callable V(r, t) returning potential energy.
        mass: Particle mass (a.u., default: 1.0 = electron mass).
        hbar: Reduced Planck constant (a.u., default: 1.0).
        dx: Grid spacing (a.u.).
        kinetic_operator: Momentum space kinetic energy :math:`\hbar^2k^2/(2m)`.
    """

    def __init__(
        self,
        potential: Callable[[Array, float], Array],
        grid_shape: tuple,
        dx: float,
        mass: float = 1.0,
        hbar: float = 1.0,
        dtype: jnp.dtype = jnp.complex64,
    ):
        """Initialize Hamiltonian.

        Args:
            potential: Function V(r, t) returning potential energy (a.u.).
            grid_shape: Shape (nx,) for 1D, (ny, nx) for 2D, (nz, ny, nx) for 3D.
            dx: Grid spacing (a.u., uniform).
            mass: Particle mass (a.u., default: 1.0 = electron mass).
            hbar: Reduced Planck constant (a.u., default: 1.0).
            dtype: JAX dtype (default: complex64).
        """
        super().__init__(dtype=dtype)
        self.potential = potential
        self.mass = mass
        self.hbar = hbar
        self.dx = dx
        self.grid_shape = grid_shape

        k_components = momentum_operator(grid_shape, dx, hbar=hbar)
        k_squared = sum(k**2 for k in k_components)
        self.kinetic_operator = (hbar**2 / (2 * mass)) * k_squared

    def apply(self, psi: Array, t: float) -> Array:
        r"""Apply :math:`\hat{H}|\psi\rangle = (\hat{T} + \hat{V})|\psi\rangle` using split-operator method.

        Args:
            psi: Wavefunction.
            t: Time (a.u.).

        Returns:
            :math:`\hat{H}|\psi\rangle`.
        """
        psi_k = jnp.fft.fftn(psi)
        t_psi_k = self.kinetic_operator * psi_k
        t_psi = jnp.fft.ifftn(t_psi_k)

        v_psi = self.potential(psi, t) * psi

        return t_psi + v_psi

    def energy(self, psi: Array, t: float) -> float:
        r"""Compute energy expectation :math:`\langle\psi|\hat{H}|\psi\rangle`.

        Args:
            psi: Normalized wavefunction.
            t: Time (a.u.).

        Returns:
            Energy expectation value (a.u.).
        """
        h_psi = self.apply(psi, t)
        ndim = psi.ndim
        dv = self.dx**ndim
        return jnp.real(jnp.sum(jnp.conj(psi) * h_psi) * dv)

    def kinetic_energy(self, psi: Array) -> float:
        r"""Compute kinetic energy expectation :math:`\langle\psi|\hat{T}|\psi\rangle`.

        Args:
            psi: Normalized wavefunction.

        Returns:
            Kinetic energy (a.u.).
        """
        psi_k = jnp.fft.fftn(psi)
        t_psi_k = self.kinetic_operator * psi_k
        t_psi = jnp.fft.ifftn(t_psi_k)
        ndim = psi.ndim
        dv = self.dx**ndim
        return jnp.real(jnp.sum(jnp.conj(psi) * t_psi) * dv)

    def potential_energy(self, psi: Array, t: float) -> float:
        r"""Compute potential energy expectation :math:`\langle\psi|\hat{V}|\psi\rangle`.

        Args:
            psi: Normalized wavefunction.
            t: Time (a.u.).

        Returns:
            Potential energy (a.u.).
        """
        v_psi = self.potential(psi, t) * psi
        ndim = psi.ndim
        dv = self.dx**ndim
        return jnp.real(jnp.sum(jnp.conj(psi) * v_psi) * dv)


class FreeParticle(ParticleInPotential):
    r"""Free particle Hamiltonian (:math:`V = 0`).

    .. math::
        \hat{H} = -\frac{\hbar^2}{2m}\nabla^2
    """

    def __init__(
        self,
        grid_shape: tuple,
        dx: float,
        mass: float = 1.0,
        hbar: float = 1.0,
        dtype: jnp.dtype = jnp.complex64,
    ):
        """Initialize free particle Hamiltonian.

        Args:
            grid_shape: Shape of spatial grid.
            dx: Grid spacing (a.u.).
            mass: Particle mass (a.u., default: 1.0 = electron mass).
            hbar: Reduced Planck constant (a.u., default: 1.0).
            dtype: JAX dtype (default: complex64).
        """

        def zero_potential(r: Array, t: float) -> Array:
            return jnp.zeros_like(r, dtype=jnp.float32)

        super().__init__(
            potential=zero_potential,
            grid_shape=grid_shape,
            dx=dx,
            mass=mass,
            hbar=hbar,
            dtype=dtype,
        )


class HarmonicOscillator(ParticleInPotential):
    r"""Quantum harmonic oscillator Hamiltonian.

    .. math::
        \hat{H} = -\frac{\hbar^2}{2m}\nabla^2 + \frac{1}{2}m\omega^2r^2
    """

    def __init__(
        self,
        omega: float,
        grid_shape: tuple,
        dx: float,
        grid_coords: Array,
        mass: float = 1.0,
        hbar: float = 1.0,
        dtype: jnp.dtype = jnp.complex64,
    ):
        """Initialize harmonic oscillator Hamiltonian.

        Args:
            omega: Angular frequency (a.u.).
            grid_shape: Shape of spatial grid.
            dx: Grid spacing (a.u.).
            grid_coords: Spatial coordinates (x for 1D, (X, Y) for 2D, etc.).
            mass: Particle mass (a.u., default: 1.0 = electron mass).
            hbar: Reduced Planck constant (a.u., default: 1.0).
            dtype: JAX dtype (default: complex64).
        """
        self.omega = omega
        self.grid_coords = grid_coords

        def harmonic_potential(r: Array, t: float) -> Array:
            if isinstance(self.grid_coords, tuple):
                r_squared = sum(coord**2 for coord in self.grid_coords)
            else:
                r_squared = self.grid_coords**2
            return 0.5 * mass * omega**2 * r_squared

        super().__init__(
            potential=harmonic_potential,
            grid_shape=grid_shape,
            dx=dx,
            mass=mass,
            hbar=hbar,
            dtype=dtype,
        )
