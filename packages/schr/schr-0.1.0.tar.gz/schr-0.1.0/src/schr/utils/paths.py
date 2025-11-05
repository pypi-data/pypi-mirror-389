"""Path utilities for managing output directories and files.

This module provides functions for generating standardized paths for
simulation results, ensuring they are saved to the user's ~/.schr directory.
"""

import os
from datetime import datetime
from pathlib import Path


def get_schr_home() -> Path:
    """Get the Schr home directory (~/.schr).

    Creates the directory if it doesn't exist.

    Returns:
        Path to ~/.schr directory.

    Example:
        >>> home = get_schr_home()
        >>> print(home)
        /Users/username/.schr
    """
    schr_home = Path.home() / ".schr"
    schr_home.mkdir(parents=True, exist_ok=True)
    return schr_home


def get_output_dir(
    simulation_name: str,
    create: bool = True,
) -> Path:
    """Get output directory for a simulation.

    Creates a subdirectory in ~/.schr for the simulation results.

    Args:
        simulation_name: Name of the simulation (e.g., "double_slit", "tunneling").
        create: If True, create the directory if it doesn't exist (default: True).

    Returns:
        Path to the simulation output directory.

    Example:
        >>> output_dir = get_output_dir("double_slit")
        >>> print(output_dir)
        /Users/username/.schr/double_slit
    """
    schr_home = get_schr_home()
    output_dir = schr_home / simulation_name

    if create:
        output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir


def get_output_path(
    simulation_name: str,
    filename: str,
    timestamp: bool = True,
    create_dir: bool = True,
) -> Path:
    """Get full path for an output file.

    Args:
        simulation_name: Name of the simulation.
        filename: Name of the output file (e.g., "animation.mp4", "final_state.npy").
        timestamp: If True, append timestamp to filename suffix (default: True).
        create_dir: If True, create the directory if needed (default: True).

    Returns:
        Full path to the output file.

    Example:
        >>> path = get_output_path("double_slit", "animation.mp4")
        >>> print(path)
        /Users/username/.schr/double_slit/animation_20251104_153022.mp4

        >>> path = get_output_path("double_slit", "animation.mp4", timestamp=False)
        >>> print(path)
        /Users/username/.schr/double_slit/animation.mp4
    """
    output_dir = get_output_dir(simulation_name, create=create_dir)

    if timestamp:
        # Split filename into stem and suffix
        file_path = Path(filename)
        stem = file_path.stem
        suffix = file_path.suffix
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_filename = f"{stem}_{timestamp_str}{suffix}"
        return output_dir / timestamped_filename
    else:
        return output_dir / filename


def get_data_dir(create: bool = True) -> Path:
    """Get directory for data files (potentials, initial conditions, etc.).

    Args:
        create: If True, create the directory if it doesn't exist (default: True).

    Returns:
        Path to ~/.schr/data directory.

    Example:
        >>> data_dir = get_data_dir()
        >>> print(data_dir)
        /Users/username/.schr/data
    """
    data_dir = get_schr_home() / "data"
    if create:
        data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_cache_dir(create: bool = True) -> Path:
    """Get directory for cached computations.

    Args:
        create: If True, create the directory if it doesn't exist (default: True).

    Returns:
        Path to ~/.schr/cache directory.

    Example:
        >>> cache_dir = get_cache_dir()
        >>> print(cache_dir)
        /Users/username/.schr/cache
    """
    cache_dir = get_schr_home() / "cache"
    if create:
        cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def list_simulations() -> list[str]:
    """List all simulation directories in ~/.schr.

    Returns:
        List of simulation directory names.

    Example:
        >>> simulations = list_simulations()
        >>> for sim in simulations:
        ...     print(sim)
        double_slit
        tunneling
        quantum_vortex
    """
    schr_home = get_schr_home()
    if not schr_home.exists():
        return []

    # Get all subdirectories, excluding special dirs like 'data' and 'cache'
    special_dirs = {"data", "cache"}
    simulations = [d.name for d in schr_home.iterdir() if d.is_dir() and d.name not in special_dirs]
    return sorted(simulations)


def clean_old_simulations(keep_recent: int = 10) -> list[Path]:
    """Clean old simulation directories, keeping only the most recent ones.

    Args:
        keep_recent: Number of recent simulations to keep (default: 10).

    Returns:
        List of paths that were removed.

    Example:
        >>> removed = clean_old_simulations(keep_recent=5)
        >>> print(f"Removed {len(removed)} old simulations")
        Removed 3 old simulations
    """
    schr_home = get_schr_home()
    if not schr_home.exists():
        return []

    # Get all simulation directories (excluding special dirs)
    special_dirs = {"data", "cache"}
    sim_dirs = [d for d in schr_home.iterdir() if d.is_dir() and d.name not in special_dirs]

    # Sort by modification time (newest first)
    sim_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)

    # Remove old ones
    removed = []
    for old_dir in sim_dirs[keep_recent:]:
        try:
            import shutil

            shutil.rmtree(old_dir)
            removed.append(old_dir)
        except Exception as e:
            print(f"Warning: Could not remove {old_dir}: {e}")

    return removed


def get_simulation_info(simulation_dir: Path) -> dict:
    """Get information about a simulation directory.

    Args:
        simulation_dir: Path to the simulation directory.

    Returns:
        Dictionary with simulation information.

    Example:
        >>> info = get_simulation_info(Path("~/.schr/double_slit"))
        >>> print(info)
        {
            'name': 'double_slit',
            'size_mb': 125.3,
            'num_files': 126,
            'created': '2025-11-04 15:30:22',
            'modified': '2025-11-04 15:35:45'
        }
    """
    if not simulation_dir.exists():
        return {}

    # Count files and calculate total size
    total_size = 0
    num_files = 0
    for root, dirs, files in os.walk(simulation_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                total_size += os.path.getsize(file_path)
                num_files += 1
            except OSError:
                pass

    # Get timestamps
    stat = simulation_dir.stat()
    created = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

    return {
        "name": simulation_dir.name,
        "size_mb": total_size / (1024 * 1024),
        "num_files": num_files,
        "created": created,
        "modified": modified,
    }
