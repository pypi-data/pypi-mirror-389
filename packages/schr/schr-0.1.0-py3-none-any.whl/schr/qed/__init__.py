"""Quantum Electrodynamics (QED) module for schr package.

This module provides a simplified QED implementation based on minimal coupling
between electrons and quantized electromagnetic fields.
"""

from schr.qed.field import PhotonField
from schr.qed.interaction import CoupledQEDSystem, minimal_coupling_hamiltonian

__all__ = [
    "PhotonField",
    "CoupledQEDSystem",
    "minimal_coupling_hamiltonian",
]
