"""Utility functions for schr package.

This module provides helper functions for grid generation, FFT operations,
visualization, and I/O operations.
"""

from schr.utils.absorbing_boundary import (
    complex_absorbing_potential,
    create_absorbing_boundary,
    create_absorption_mask,
    exponential_absorbing_mask,
    mask_absorbing_potential,
    polynomial_absorbing_mask,
)
from schr.utils.fft import fft_derivative, fftfreq_grid, momentum_operator
from schr.utils.grid import create_grid_1d, create_grid_2d, create_grid_3d
from schr.utils.paths import (
    clean_old_simulations,
    get_cache_dir,
    get_data_dir,
    get_output_dir,
    get_output_path,
    get_schr_home,
    get_simulation_info,
    list_simulations,
)
from schr.utils.visualization import (
    animate_wavefunction,
    animate_wavefunction_2d,
    plot_wavefunction,
    plot_wavefunction_2d,
)

__all__ = [
    # Absorbing boundary utilities
    "create_absorbing_boundary",
    "polynomial_absorbing_mask",
    "exponential_absorbing_mask",
    "complex_absorbing_potential",
    "mask_absorbing_potential",
    "create_absorption_mask",  # Legacy interface
    # FFT utilities
    "fft_derivative",
    "fftfreq_grid",
    "momentum_operator",
    # Grid utilities
    "create_grid_1d",
    "create_grid_2d",
    "create_grid_3d",
    # Path utilities
    "get_schr_home",
    "get_output_dir",
    "get_output_path",
    "get_data_dir",
    "get_cache_dir",
    "list_simulations",
    "clean_old_simulations",
    "get_simulation_info",
    # Visualization
    "plot_wavefunction",
    "plot_wavefunction_2d",
    "animate_wavefunction",
    "animate_wavefunction_2d",
    "animate_wavefunction_2d_dual",
]
