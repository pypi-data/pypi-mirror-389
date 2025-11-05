"""Quantum mechanics module for schr package.

This module provides implementations of quantum mechanical systems,
including Hamiltonians, wavefunctions, and Schrödinger equation solvers.
"""

from schr.qm.hamiltonian import (
    FreeParticle,
    HarmonicOscillator,
    ParticleInPotential,
)
from schr.qm.solvers import (
    CrankNicolson,
    RungeKutta4,
    SplitStepFourier,
    estimate_stable_timestep,
)
from schr.qm.wavefunction import gaussian_wavepacket, normalize

__all__ = [
    # Hamiltonians
    "ParticleInPotential",
    "FreeParticle",
    "HarmonicOscillator",
    # Solvers
    "SplitStepFourier",
    "CrankNicolson",
    "RungeKutta4",
    "estimate_stable_timestep",
    # Wavefunction utilities
    "gaussian_wavepacket",
    "normalize",
]
