"""schr: A Python framework for Quantum Mechanics and QED simulations.

This package provides GPU-accelerated quantum simulations using JAX,
with modules for quantum mechanics (QM) and quantum electrodynamics (QED).
"""

__version__ = "0.1.0"

from schr import core, qed, qm, utils

__all__ = ["core", "qm", "qed", "utils", "__version__"]
