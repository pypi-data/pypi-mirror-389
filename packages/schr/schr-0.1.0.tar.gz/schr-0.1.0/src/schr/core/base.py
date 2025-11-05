"""Abstract base classes for quantum simulations."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

import jax.numpy as jnp
from jax import Array


class Hamiltonian(ABC):
    r"""Abstract base class for quantum Hamiltonians.

    Represents the quantum operator :math:`\hat{H}` acting on wavefunctions
    :math:`|\psi\rangle`.

    Attributes:
        dtype: JAX dtype (complex64 or complex128).
    """

    def __init__(self, dtype: jnp.dtype = jnp.complex64):
        """Initialize Hamiltonian.

        Args:
            dtype: JAX dtype (default: complex64 for performance).
        """
        self.dtype = dtype

    @abstractmethod
    def apply(self, psi: Array, t: float) -> Array:
        r"""Apply :math:`\hat{H}|\psi\rangle`.

        Args:
            psi: Wavefunction :math:`|\psi\rangle`.
            t: Time (a.u.).

        Returns:
            :math:`\hat{H}|\psi\rangle`.
        """
        pass

    def energy(self, psi: Array, t: float) -> float:
        r"""Compute energy expectation :math:`\langle\psi|\hat{H}|\psi\rangle`.

        Args:
            psi: Normalized wavefunction.
            t: Time (a.u.).

        Returns:
            Energy expectation value (a.u.).
        """
        h_psi = self.apply(psi, t)
        return jnp.real(jnp.sum(jnp.conj(psi) * h_psi))


class Field(ABC):
    """Abstract base class for field representations.

    Attributes:
        dtype: JAX dtype for field values.
    """

    def __init__(self, dtype: jnp.dtype = jnp.complex64):
        """Initialize field.

        Args:
            dtype: JAX dtype (default: complex64).
        """
        self.dtype = dtype

    @abstractmethod
    def get_state(self) -> Array:
        """Get current field state.

        Returns:
            Current field state as JAX array.
        """
        pass

    @abstractmethod
    def set_state(self, state: Array) -> None:
        """Set field state.

        Args:
            state: New field state.
        """
        pass


class Solver(ABC):
    r"""Abstract base class for time evolution solvers.

    Implements numerical integration of the Schrödinger equation:

    .. math::
        i\hbar\frac{\partial|\psi\rangle}{\partial t} = \hat{H}|\psi\rangle

    Attributes:
        hamiltonian: Hamiltonian operator.
        dtype: JAX dtype for computations.
    """

    def __init__(self, hamiltonian: Hamiltonian, dtype: jnp.dtype = jnp.complex64):
        """Initialize solver.

        Args:
            hamiltonian: Hamiltonian operator.
            dtype: JAX dtype (default: complex64).
        """
        self.hamiltonian = hamiltonian
        self.dtype = dtype

    @abstractmethod
    def step(self, psi: Array, t: float, dt: float) -> Array:
        r"""Perform single time step :math:`|\psi(t)\rangle \to |\psi(t+dt)\rangle`.

        Args:
            psi: Wavefunction at time :math:`t`.
            t: Current time (a.u.).
            dt: Time step (a.u.).

        Returns:
            Wavefunction at time :math:`t + dt`.
        """
        pass

    def evolve(
        self,
        psi0: Array,
        t_span: tuple[float, float],
        dt: float,
        callback: Callable[[Array, float], Any] | None = None,
    ) -> Array:
        """Evolve wavefunction over time interval.

        Args:
            psi0: Initial wavefunction.
            t_span: Time interval (t_start, t_end) in a.u.
            dt: Time step (a.u.).
            callback: Optional function called at each step with (psi, t).

        Returns:
            Final wavefunction at t_end.

        Raises:
            ValueError: If t_end <= t_start or dt <= 0.
        """
        t_start, t_end = t_span
        if t_end <= t_start:
            raise ValueError(f"Invalid time span: t_end ({t_end}) must be > t_start ({t_start})")
        if dt <= 0:
            raise ValueError(f"Time step dt must be positive, got {dt}")

        psi = psi0
        t = t_start
        n_steps = int((t_end - t_start) / dt)

        for _ in range(n_steps):
            psi = self.step(psi, t, dt)
            t += dt
            if callback is not None:
                callback(psi, t)

        remaining = (t_end - t_start) - n_steps * dt
        if remaining > 1e-10:
            psi = self.step(psi, t, remaining)
            if callback is not None:
                callback(psi, t_end)

        return psi
