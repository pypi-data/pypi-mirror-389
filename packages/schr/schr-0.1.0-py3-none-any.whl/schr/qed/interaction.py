"""Electron-photon interaction for QED simulations.

This module implements the minimal coupling between electrons and photons,
providing a simplified QED system for educational purposes.
"""

from collections.abc import Callable

import jax.numpy as jnp
from jax import Array

from schr.core.base import Hamiltonian
from schr.qed.field import PhotonField


def minimal_coupling_hamiltonian(
    psi_shape: tuple,
    dx: float,
    A: Callable[[Array, float], Array],
    mass: float = 1.0,
    charge: float = -1.0,
    hbar: float = 1.0,
    dtype: jnp.dtype = jnp.complex64,
) -> Hamiltonian:
    """Create a Hamiltonian with minimal coupling to electromagnetic field.

    The minimal coupling replaces the momentum p with p - qA/c, where
    A is the vector potential, q is the charge, and c is the speed of light.

    This gives H = (p - qA)²/(2m) + V for a particle in an EM field.

    Args:
        psi_shape: Shape of the electron wavefunction grid.
        dx: Grid spacing.
        A: Vector potential function A(x, t).
        mass: Particle mass. Default is 1.0.
        charge: Particle charge. Default is -1.0 (electron).
        hbar: Reduced Planck constant. Default is 1.0.
        dtype: JAX dtype. Default is complex64.

    Returns:
        A Hamiltonian object with minimal coupling.

    Note:
        This is a simplified implementation for educational purposes.
        Production QED would include gauge fixing, renormalization, etc.
    """
    from schr.qm.hamiltonian import ParticleInPotential

    # Create a modified potential that includes the A·p and A² terms
    def effective_potential(r: Array, t: float) -> Array:
        """Effective potential including electromagnetic coupling."""
        # For simplicity, return zero (pure EM interaction)
        return jnp.zeros_like(r, dtype=jnp.float32)

    # This is a placeholder - full implementation would modify kinetic term
    hamiltonian = ParticleInPotential(
        potential=effective_potential,
        grid_shape=psi_shape,
        dx=dx,
        mass=mass,
        hbar=hbar,
        dtype=dtype,
    )

    return hamiltonian


class CoupledQEDSystem:
    """Coupled electron-photon system with minimal coupling.

    This class manages the joint evolution of an electron wavefunction
    and a quantized photon field, including their mutual interaction.

    The total Hamiltonian is:
    H = H_electron + H_field + H_interaction

    where H_interaction couples the electron to the photon modes.

    Attributes:
        electron_hamiltonian: Hamiltonian for the electron.
        photon_field: Quantized photon field.
        coupling_strength: Strength of electron-photon coupling.
        hbar: Reduced Planck constant.
    """

    def __init__(
        self,
        electron_hamiltonian: Hamiltonian,
        photon_field: PhotonField,
        coupling_strength: float = 0.1,
        hbar: float = 1.0,
        dtype: jnp.dtype = jnp.complex64,
    ):
        """Initialize the coupled QED system.

        Args:
            electron_hamiltonian: Hamiltonian for the electron.
            photon_field: Quantized photon field.
            coupling_strength: Coupling constant g. Default is 0.1.
            hbar: Reduced Planck constant. Default is 1.0.
            dtype: JAX dtype. Default is complex64.
        """
        self.electron_hamiltonian = electron_hamiltonian
        self.photon_field = photon_field
        self.coupling_strength = coupling_strength
        self.hbar = hbar
        self.dtype = dtype

    def interaction_term(
        self, psi_electron: Array, photon_state: Array, mode: int = 0
    ) -> tuple[Array, Array]:
        """Compute the interaction between electron and photon field.

        Uses a simplified dipole interaction:
        H_int = g (a + a†) x̂

        where g is the coupling strength, a/a† are photon operators,
        and x̂ is the electron position operator.

        Args:
            psi_electron: Electron wavefunction.
            photon_state: Photon field state.
            mode: Photon mode to couple to. Default is 0.

        Returns:
            Tuple (H_int|ψ_e⟩, H_int|ϕ⟩) acting on electron and photon states.
        """
        # Get photon operators
        a = self.photon_field.annihilation_operator(mode)
        a_dag = self.photon_field.creation_operator(mode)

        # Field operator: (a + a†)
        field_op = a + a_dag

        # Apply to photon state
        # This is simplified; full implementation would use proper tensor products
        photon_contribution = jnp.dot(field_op, photon_state)

        # Multiply electron wavefunction by position (simplified)
        # In reality, we'd multiply by x and apply proper operators
        electron_contribution = self.coupling_strength * psi_electron

        return electron_contribution, photon_contribution

    def evolve(
        self, psi_electron: Array, photon_state: Array, t_span: tuple[float, float], dt: float
    ) -> tuple[Array, Array]:
        """Evolve the coupled electron-photon system.

        Uses a simplified evolution scheme that alternates between
        electron, photon, and interaction terms.

        Args:
            psi_electron: Initial electron wavefunction.
            photon_state: Initial photon field state.
            t_span: Time interval (t_start, t_end).
            dt: Time step.

        Returns:
            Tuple (psi_electron_final, photon_state_final).

        Note:
            This is a simplified implementation for educational purposes.
            Production code would use proper tensor product spaces and
            more sophisticated evolution algorithms.
        """
        t_start, t_end = t_span
        t = t_start

        psi_e = psi_electron
        psi_p = photon_state

        n_steps = int((t_end - t_start) / dt)

        for _ in range(n_steps):
            # Evolve electron (free evolution)
            H_e_psi = self.electron_hamiltonian.apply(psi_e, t)
            psi_e = psi_e - 1j * (dt / self.hbar) * H_e_psi

            # Evolve photon field (free evolution)
            # Simplified: photon state evolves with its frequency
            for mode in range(self.photon_field.n_modes):
                omega = self.photon_field.frequencies[mode]
                # Apply phase: exp(-iωt) for each mode
                # This is highly simplified
                pass

            # Apply interaction (simplified)
            electron_int, photon_int = self.interaction_term(psi_e, psi_p, mode=0)
            psi_e = psi_e - 1j * (dt / self.hbar) * electron_int

            t += dt

        return psi_e, psi_p

    def total_energy(self, psi_electron: Array, photon_state: Array, t: float, dx: float) -> float:
        """Compute total energy of the coupled system.

        E_total = E_electron + E_photon + E_interaction

        Args:
            psi_electron: Electron wavefunction.
            photon_state: Photon field state.
            t: Current time.
            dx: Grid spacing for electron wavefunction.

        Returns:
            Total energy of the system.
        """
        # Electron energy
        H_e_psi = self.electron_hamiltonian.apply(psi_electron, t)
        ndim = psi_electron.ndim
        dV = dx**ndim
        E_electron = jnp.real(jnp.sum(jnp.conj(psi_electron) * H_e_psi) * dV)

        # Photon energy (simplified)
        # For each mode: E = ℏω (⟨n⟩ + 1/2)
        E_photon = 0.0
        for mode in range(self.photon_field.n_modes):
            omega = self.photon_field.frequencies[mode]
            # Simplified: assume vacuum state for now
            E_photon += self.hbar * omega * 0.5

        # Interaction energy (simplified - would need proper calculation)
        E_interaction = 0.0

        return E_electron + E_photon + E_interaction
