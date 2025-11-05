"""Solvers for the time-dependent Schrödinger equation."""

from functools import partial

import jax.numpy as jnp
from jax import Array, jit

from schr.core.base import Hamiltonian, Solver


class SplitStepFourier(Solver):
    r"""Split-Step Fourier Method (SSFM) solver.

    Pseudo-spectral method alternating between position and momentum space:

    .. math::
        \psi(t+dt) \approx e^{-iV dt/(2\hbar)} e^{-iT dt/\hbar} e^{-iV dt/(2\hbar)} \psi(t)

    Accuracy: :math:`O(dt^3)`, preserves unitarity.

    Attributes:
        hamiltonian: Hamiltonian operator.
        hbar: Reduced Planck constant (a.u., default: 1.0).
        kinetic_operator: Precomputed :math:`T(k) = \hbar^2k^2/(2m)`.
    """

    def __init__(
        self, hamiltonian: Hamiltonian, hbar: float = 1.0, dtype: jnp.dtype = jnp.complex64
    ):
        """Initialize SSFM solver.

        Args:
            hamiltonian: Hamiltonian with kinetic_operator and potential attributes.
            hbar: Reduced Planck constant (a.u., default: 1.0).
            dtype: JAX dtype (default: complex64).

        Raises:
            AttributeError: If hamiltonian lacks required attributes.
        """
        super().__init__(hamiltonian, dtype=dtype)
        self.hbar = hbar

        if not hasattr(hamiltonian, "kinetic_operator"):
            raise AttributeError("Hamiltonian must have 'kinetic_operator' for SSFM")
        if not hasattr(hamiltonian, "potential"):
            raise AttributeError("Hamiltonian must have 'potential' for SSFM")

        self.kinetic_operator = hamiltonian.kinetic_operator
        self.potential = hamiltonian.potential

    @partial(jit, static_argnums=(0,))
    def step(self, psi: Array, t: float, dt: float) -> Array:
        r"""Perform single SSFM time step.

        Args:
            psi: Wavefunction at time :math:`t`.
            t: Current time (a.u.).
            dt: Time step (a.u.).

        Returns:
            Wavefunction at time :math:`t + dt`.
        """
        v = self.potential(psi, t)
        psi = psi * jnp.exp(-1j * v * dt / (2 * self.hbar))

        psi_k = jnp.fft.fftn(psi)
        psi_k = psi_k * jnp.exp(-1j * self.kinetic_operator * dt / self.hbar)
        psi = jnp.fft.ifftn(psi_k)

        v = self.potential(psi, t + dt)
        psi = psi * jnp.exp(-1j * v * dt / (2 * self.hbar))

        return psi


class RungeKutta4(Solver):
    r"""Fourth-order Runge-Kutta solver.

    General-purpose ODE solver for :math:`i\hbar\partial_t|\psi\rangle = \hat{H}|\psi\rangle`.
    Accuracy: :math:`O(dt^4)`.

    .. warning::
        RK4 has limited stability for the Schrödinger equation. For best results:

        * Use small timesteps: :math:`dt < 0.05` (in atomic units)
        * For grid-based problems: :math:`dt \lesssim \Delta x^2`
        * For strong potentials, reduce :math:`dt` further
        * Consider SplitStepFourier for better stability and speed

    Notes:
        Unlike implicit methods (Crank-Nicolson) or operator splitting (SSFM),
        standard RK4 is **not unconditionally stable** for the Schrödinger equation.
        Large timesteps or strong potentials can cause exponential error growth leading
        to NaN values.
    """

    def __init__(
        self, hamiltonian: Hamiltonian, hbar: float = 1.0, dtype: jnp.dtype = jnp.complex64
    ):
        """Initialize RK4 solver.

        Args:
            hamiltonian: Hamiltonian operator.
            hbar: Reduced Planck constant (a.u., default: 1.0).
            dtype: JAX dtype (default: complex64).
        """
        super().__init__(hamiltonian, dtype=dtype)
        self.hbar = hbar

    @partial(jit, static_argnums=(0,))
    def step(self, psi: Array, t: float, dt: float) -> Array:
        r"""Perform single RK4 time step.

        Args:
            psi: Wavefunction at time :math:`t`.
            t: Current time (a.u.).
            dt: Time step (a.u.).

        Returns:
            Wavefunction at time :math:`t + dt`.

        Note:
            This method uses the standard RK4 formula for the Schrödinger equation
            :math:`i\hbar\partial_t|\psi\rangle = \hat{H}|\psi\rangle`:

            .. math::
                k_1 &= -\frac{i}{\hbar}\hat{H}|\psi(t)\rangle \\
                k_2 &= -\frac{i}{\hbar}\hat{H}\left(|\psi(t)\rangle + \frac{dt}{2}k_1\right) \\
                k_3 &= -\frac{i}{\hbar}\hat{H}\left(|\psi(t)\rangle + \frac{dt}{2}k_2\right) \\
                k_4 &= -\frac{i}{\hbar}\hat{H}\left(|\psi(t)\rangle + dt \cdot k_3\right) \\
                |\psi(t+dt)\rangle &= |\psi(t)\rangle + \frac{dt}{6}(k_1 + 2k_2 + 2k_3 + k_4)

            **Stability**: Not unconditionally stable. Becomes unstable for
            :math:`dt \gtrsim 0.05` a.u. or with strong potentials.
        """

        k1 = (-1j / self.hbar) * self.hamiltonian.apply(psi, t)
        k2 = (-1j / self.hbar) * self.hamiltonian.apply(psi + dt * k1 / 2, t + dt / 2)
        k3 = (-1j / self.hbar) * self.hamiltonian.apply(psi + dt * k2 / 2, t + dt / 2)
        k4 = (-1j / self.hbar) * self.hamiltonian.apply(psi + dt * k3, t + dt)

        return psi + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)


class CrankNicolson(Solver):
    r"""Crank-Nicolson implicit solver.

    Solves :math:`(I + i\hat{H}dt/(2\hbar))|\psi(t+dt)\rangle = (I - i\hat{H}dt/(2\hbar))|\psi(t)\rangle`

    Unconditionally stable, preserves unitarity. Accuracy: :math:`O(dt^2)`.
    """

    def __init__(
        self,
        hamiltonian: Hamiltonian,
        hbar: float = 1.0,
        max_iter: int = 100,
        tol: float = 1e-8,
        dtype: jnp.dtype = jnp.complex64,
    ):
        """Initialize Crank-Nicolson solver.

        Args:
            hamiltonian: Hamiltonian operator.
            hbar: Reduced Planck constant (a.u., default: 1.0).
            max_iter: Maximum iterations for implicit solver (default: 100).
            tol: Convergence tolerance (default: 1e-8).
            dtype: JAX dtype (default: complex64).
        """
        super().__init__(hamiltonian, dtype=dtype)
        self.hbar = hbar
        self.max_iter = max_iter
        self.tol = tol

    @partial(jit, static_argnums=(0,))
    def step(self, psi: Array, t: float, dt: float) -> Array:
        r"""Perform single Crank-Nicolson time step.

        Uses fixed-point iteration for implicit equation.

        Args:
            psi: Wavefunction at time :math:`t`.
            t: Current time (a.u.).
            dt: Time step (a.u.).

        Returns:
            Wavefunction at time :math:`t + dt`.
        """
        h_psi = self.hamiltonian.apply(psi, t)
        rhs = psi - 1j * (dt / (2 * self.hbar)) * h_psi

        psi_new = psi
        for _ in range(self.max_iter):
            h_psi_new = self.hamiltonian.apply(psi_new, t + dt)
            psi_next = rhs - 1j * (dt / (2 * self.hbar)) * h_psi_new

            error = jnp.max(jnp.abs(psi_next - psi_new))
            psi_new = psi_next

            if error < self.tol:
                break

        return psi_new


def estimate_stable_timestep(
    dx: float, mass: float = 1.0, hbar: float = 1.0, safety_factor: float = 0.5
) -> float:
    r"""Estimate stable timestep for RK4 solver.

    For grid-based quantum simulations, RK4 has a stability limit related to
    the grid spacing. This function estimates a safe timestep using:

    .. math::
        dt_{\text{max}} \approx C \frac{m \Delta x^2}{\hbar}

    where C is a safety factor (default: 0.5).

    Args:
        dx: Grid spacing (a.u.).
        mass: Particle mass (a.u., default: 1.0).
        hbar: Reduced Planck constant (a.u., default: 1.0).
        safety_factor: Safety factor C (default: 0.5 for conservative estimate).

    Returns:
        Estimated maximum stable timestep (a.u.).

    Example:
        >>> dx = 0.1  # Grid spacing
        >>> dt_max = estimate_stable_timestep(dx)
        >>> print(f"Use dt < {dt_max:.4f}")
        Use dt < 0.0050

    Note:
        This is a conservative estimate. For strong potentials, you may need
        to reduce the timestep further. Always verify stability by monitoring
        wavefunction norm and energy conservation.
    """
    return safety_factor * mass * dx**2 / hbar


@jit
def compute_norm(psi: Array, dx: float) -> float:
    r"""Compute wavefunction norm :math:`\sqrt{\int|\psi|^2 dV}`.

    Args:
        psi: Wavefunction.
        dx: Grid spacing (a.u., uniform).

    Returns:
        Norm (should be 1 for normalized wavefunctions).
    """
    ndim = psi.ndim
    dv = dx**ndim
    return jnp.sqrt(jnp.sum(jnp.abs(psi) ** 2) * dv)


def compute_energy(psi: Array, hamiltonian: Hamiltonian, t: float, dx: float) -> float:
    r"""Compute energy expectation :math:`\langle\psi|\hat{H}|\psi\rangle / \langle\psi|\psi\rangle`.

    Args:
        psi: Wavefunction.
        hamiltonian: Hamiltonian operator.
        t: Time (a.u.).
        dx: Grid spacing (a.u.).

    Returns:
        Energy expectation value (a.u.).
    """
    h_psi = hamiltonian.apply(psi, t)
    ndim = psi.ndim
    dv = dx**ndim

    numerator = jnp.sum(jnp.conj(psi) * h_psi) * dv
    denominator = jnp.sum(jnp.abs(psi) ** 2) * dv

    return jnp.real(numerator / denominator)
