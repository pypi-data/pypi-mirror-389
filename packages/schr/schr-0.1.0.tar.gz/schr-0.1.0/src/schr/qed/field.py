"""Photon field representation for QED simulations.

This module implements a finite-mode photon field with creation and
annihilation operators in the Fock space representation.
"""

import jax.numpy as jnp
from jax import Array

from schr.core.base import Field


class PhotonField(Field):
    r"""Finite-mode photon field in Fock space.

    Represents a quantized electromagnetic field using a finite number of
    photon modes. Each mode is characterized by a frequency :math:`\omega` and can be
    in various number states :math:`|n\rangle`.

    The field is represented as a state vector in the truncated Fock space,
    where each mode can have 0 to max_photons photons.

    Attributes:
        n_modes: Number of photon modes.
        max_photons: Maximum photon number per mode (truncation).
        frequencies: Angular frequencies of each mode (:math:`\omega_i`).
        state: Current state vector in Fock space.
        dtype: JAX dtype for the field.
    """

    def __init__(
        self,
        n_modes: int,
        frequencies: Array,
        max_photons: int = 10,
        dtype: jnp.dtype = jnp.complex64,
    ):
        """Initialize the photon field.

        Args:
            n_modes: Number of photon modes.
            frequencies: Array of angular frequencies for each mode.
            max_photons: Maximum number of photons per mode (default: 10).
            dtype: JAX dtype for the field (default: complex64).

        Raises:
            ValueError: If n_modes doesn't match length of frequencies.
        """
        super().__init__(dtype=dtype)

        if len(frequencies) != n_modes:
            raise ValueError(f"Expected {n_modes} frequencies, got {len(frequencies)}")

        self.n_modes = n_modes
        self.max_photons = max_photons
        self.frequencies = jnp.array(frequencies, dtype=jnp.float32)

        state_shape = tuple([max_photons + 1] * n_modes)
        self.state = jnp.zeros(state_shape, dtype=dtype)

        vacuum_index = tuple([0] * n_modes)
        self.state = self.state.at[vacuum_index].set(1.0)

    def get_state(self) -> Array:
        """Get the current state of the field.

        Returns:
            The field state as a JAX array.
        """
        return self.state

    def set_state(self, state: Array) -> None:
        """Set the field state.

        Args:
            state: The new field state.

        Raises:
            ValueError: If state shape doesn't match expected shape.
        """
        expected_shape = tuple([self.max_photons + 1] * self.n_modes)
        if state.shape != expected_shape:
            raise ValueError(f"Expected state shape {expected_shape}, got {state.shape}")
        self.state = state

    def creation_operator(self, mode: int) -> Array:
        r"""Get the creation operator :math:`a^\dagger` for a given mode.

        The creation operator increases the photon number in mode i:
        :math:`a^\dagger_i |n_i\rangle = \sqrt{n_i + 1} |n_i + 1\rangle`.

        Args:
            mode: Mode index (0 to n_modes-1).

        Returns:
            Matrix representation of the creation operator for this mode.

        Raises:
            ValueError: If mode index is out of range.
        """
        if mode < 0 or mode >= self.n_modes:
            raise ValueError(f"Mode index {mode} out of range [0, {self.n_modes})")

        dim = self.max_photons + 1
        a_dag = jnp.zeros((dim, dim), dtype=self.dtype)

        for n in range(dim - 1):
            a_dag = a_dag.at[n + 1, n].set(jnp.sqrt(n + 1))

        return a_dag

    def annihilation_operator(self, mode: int) -> Array:
        r"""Get the annihilation operator :math:`a` for a given mode.

        The annihilation operator decreases the photon number in mode i:
        :math:`a_i |n_i\rangle = \sqrt{n_i} |n_i - 1\rangle`.

        Args:
            mode: Mode index (0 to n_modes-1).

        Returns:
            Matrix representation of the annihilation operator for this mode.

        Raises:
            ValueError: If mode index is out of range.
        """
        if mode < 0 or mode >= self.n_modes:
            raise ValueError(f"Mode index {mode} out of range [0, {self.n_modes})")

        dim = self.max_photons + 1
        a = jnp.zeros((dim, dim), dtype=self.dtype)

        for n in range(1, dim):
            a = a.at[n - 1, n].set(jnp.sqrt(n))

        return a

    def number_operator(self, mode: int) -> Array:
        r"""Get the number operator :math:`\hat{n} = a^\dagger a` for a given mode.

        Args:
            mode: Mode index (0 to n_modes-1).

        Returns:
            Matrix representation of the number operator for this mode.

        Raises:
            ValueError: If mode index is out of range.
        """
        if mode < 0 or mode >= self.n_modes:
            raise ValueError(f"Mode index {mode} out of range [0, {self.n_modes})")

        dim = self.max_photons + 1
        n_op = jnp.diag(jnp.arange(dim, dtype=jnp.float32))
        return n_op.astype(self.dtype)

    def hamiltonian(self, hbar: float = 1.0) -> Array:
        r"""Get the free-field Hamiltonian :math:`H = \sum_i \hbar\omega_i (a^\dagger_i a_i + 1/2)`.

        Args:
            hbar: Reduced Planck constant (default: 1.0).

        Returns:
            Matrix representation of the field Hamiltonian.

        Note:
            For multi-mode fields, this returns the sum over all modes.
            The zero-point energy (1/2) is included.
        """
        # For simplicity, we compute the diagonal elements
        # H|n1,n2,...⟩ = Σ_i ℏω_i (n_i + 1/2) |n1,n2,...⟩

        # Create energy function that computes total energy for a state
        def energy_for_state(indices):
            """Compute energy for state |n1, n2, ..., n_k⟩."""
            energy = 0.0
            for i, n in enumerate(indices):
                energy += hbar * self.frequencies[i] * (n + 0.5)
            return energy

        # For now, return energy eigenvalues as a flat array
        # Full implementation would construct the operator matrix
        state_shape = self.state.shape

        # Generate all possible state indices
        import itertools

        all_indices = list(itertools.product(*[range(dim) for dim in state_shape]))
        energies = jnp.array([energy_for_state(idx) for idx in all_indices])

        return energies

    def expectation_photon_number(self, mode: int) -> float:
        r"""Compute expectation value of photon number in a mode.

        Computes :math:`\langle\psi|\hat{n}_i|\psi\rangle` where :math:`\hat{n}_i = a^\dagger_i a_i`.

        Args:
            mode: Mode index.

        Returns:
            Expected number of photons in the specified mode.

        Raises:
            NotImplementedError: For multi-mode expectation (not yet implemented).
        """
        n_op = self.number_operator(mode)

        if self.n_modes == 1:
            psi = self.state
            n_psi = jnp.dot(n_op, psi)
            return jnp.real(jnp.sum(jnp.conj(psi) * n_psi))
        else:
            raise NotImplementedError("Multi-mode expectation not fully implemented")
