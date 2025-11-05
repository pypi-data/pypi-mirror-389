"""Professional visualization tools for quantum simulations."""

from collections.abc import Callable

import matplotlib.pyplot as plt
import numpy as np
from jax import Array
from matplotlib import animation
from matplotlib.figure import Figure

COLORS = {
    "real": "#2E86AB",  # Ocean blue
    "imag": "#A23B72",  # Magenta
    "prob": "#F18F01",  # Amber
    "phase": "#C73E1D",  # Crimson
    "grid": "#999999",  # Gray
}

plt.style.use("dark_background")

# Publication-quality settings with Times New Roman and LaTeX
try:
    plt.rcParams.update(
        {
            "text.usetex": True,
            "text.latex.preamble": r"\usepackage{amsmath}",
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 11,
            "axes.labelsize": 12,
            "axes.titlesize": 13,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "figure.dpi": 100,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "axes.grid": True,
            "grid.alpha": 0.3,
            "grid.linestyle": "--",
            "axes.axisbelow": True,
        }
    )
except Exception:
    # Fallback if LaTeX is not available
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 11,
            "axes.labelsize": 12,
            "axes.titlesize": 13,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "figure.dpi": 100,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "axes.grid": True,
            "grid.alpha": 0.3,
            "grid.linestyle": "--",
            "axes.axisbelow": True,
        }
    )


def plot_wavefunction(
    x: Array,
    psi: Array,
    title: str = "",
    show_real_imag: bool = True,
    show_probability: bool = True,
    figsize: tuple[float, float] = (12, 4),
    units: str = "a.u.",
) -> Figure:
    r"""Plot 1D wavefunction with publication quality.

    Args:
        x: Spatial grid (1D array)
        psi: Wavefunction values (complex)
        title: Plot title
        show_real_imag: Show Re($\psi$) and Im($\psi$)
        show_probability: Show $|\psi|^2$
        figsize: Figure size (width, height) in inches
        units: Physical units label (default: "a.u.")

    Returns:
        Matplotlib Figure object
    """
    x_np = np.array(x)
    psi_np = np.array(psi)

    n_plots = int(show_real_imag) + int(show_probability)
    fig, axes = plt.subplots(1, n_plots, figsize=figsize)

    if n_plots == 1:
        axes = [axes]

    plot_idx = 0

    if show_real_imag:
        ax = axes[plot_idx]
        ax.plot(
            x_np, psi_np.real, label=r"Re$(\psi)$", linewidth=2, color=COLORS["real"], alpha=0.9
        )
        ax.plot(
            x_np, psi_np.imag, label=r"Im$(\psi)$", linewidth=2, color=COLORS["imag"], alpha=0.9
        )
        ax.axhline(0, color="k", linewidth=0.5, alpha=0.3)
        ax.set_xlabel(f"$x$ ({units})")
        ax.set_ylabel(r"$\psi(x)$")
        if title:
            ax.set_title(f"{title} — Wavefunction Components")
        ax.legend(frameon=True, fancybox=True, shadow=True)
        ax.grid(True, alpha=0.3, linestyle="--")
        plot_idx += 1

    if show_probability:
        ax = axes[plot_idx]
        prob = np.abs(psi_np) ** 2
        ax.plot(x_np, prob, linewidth=2.5, color=COLORS["prob"], alpha=0.9)
        ax.fill_between(x_np, prob, alpha=0.25, color=COLORS["prob"])
        ax.set_xlabel(f"$x$ ({units})")
        ax.set_ylabel(r"$|\psi(x)|^2$")
        if title:
            ax.set_title(f"{title} — Probability Density")
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.set_ylim(bottom=0)

    plt.tight_layout()
    return fig


def animate_wavefunction(
    x: Array,
    psi_frames: list[Array],
    dt: float,
    title: str = "",
    show_real_imag: bool = True,
    show_probability: bool = True,
    interval: int = 50,
    figsize: tuple[float, float] = (12, 5),
    units: str = "a.u.",
) -> animation.FuncAnimation:
    r"""Create publication-quality animation of time-evolving wavefunction.

    Args:
        x: Spatial grid (1D array)
        psi_frames: List of wavefunction snapshots (complex)
        dt: Time step between frames (a.u.)
        title: Animation title
        show_real_imag: Show Re($\psi$) and Im($\psi$)
        show_probability: Show $|\psi|^2$
        interval: Time between frames in milliseconds
        figsize: Figure size (width, height) in inches
        units: Physical units label (default: "a.u.")

    Returns:
        Matplotlib FuncAnimation object

    Example:
        >>> x, dx = create_grid_1d(-10, 10, 512)
        >>> psi_frames = []  # List of wavefunctions at different times
        >>> anim = animate_wavefunction(x, psi_frames, dt=0.01)
        >>> plt.show()
    """
    x_np = np.array(x)
    psi_frames_np = [np.array(psi) for psi in psi_frames]

    # Determine consistent axes ranges
    all_real = np.concatenate([psi.real for psi in psi_frames_np])
    all_imag = np.concatenate([psi.imag for psi in psi_frames_np])
    all_prob = np.concatenate([np.abs(psi) ** 2 for psi in psi_frames_np])

    if show_real_imag:
        y_min = min(all_real.min(), all_imag.min())
        y_max = max(all_real.max(), all_imag.max())
        y_range = y_max - y_min
        ylim_real_imag = (y_min - 0.1 * y_range, y_max + 0.1 * y_range)

    if show_probability:
        prob_max = all_prob.max()
        ylim_prob = (-0.05 * prob_max, 1.1 * prob_max)

    n_plots = int(show_real_imag) + int(show_probability)
    fig, axes = plt.subplots(1, n_plots, figsize=figsize)

    if n_plots == 1:
        axes = [axes]

    lines = []
    plot_idx = 0

    if show_real_imag:
        ax = axes[plot_idx]
        (line_real,) = ax.plot(
            [], [], label=r"Re$(\psi)$", linewidth=2, color=COLORS["real"], alpha=0.9
        )
        (line_imag,) = ax.plot(
            [], [], label=r"Im$(\psi)$", linewidth=2, color=COLORS["imag"], alpha=0.9
        )
        ax.axhline(0, color="k", linewidth=0.5, alpha=0.3)
        ax.set_xlabel(f"$x$ ({units})")
        ax.set_ylabel(r"$\psi(x)$")
        if title:
            ax.set_title(f"{title} — Wavefunction Components")
        ax.set_xlim(x_np[0], x_np[-1])
        ax.set_ylim(*ylim_real_imag)
        ax.legend(frameon=True, fancybox=True, shadow=True)
        ax.grid(True, alpha=0.3, linestyle="--")
        lines.extend([line_real, line_imag])
        plot_idx += 1

    if show_probability:
        ax = axes[plot_idx]
        (line_prob,) = ax.plot([], [], linewidth=2.5, color=COLORS["prob"], alpha=0.9)
        ax.set_xlabel(f"$x$ ({units})")
        ax.set_ylabel(r"$|\psi(x)|^2$")
        if title:
            ax.set_title(f"{title} — Probability Density")
        ax.set_xlim(x_np[0], x_np[-1])
        ax.set_ylim(*ylim_prob)
        ax.grid(True, alpha=0.3, linestyle="--")
        lines.append(line_prob)

    plt.tight_layout()

    def init():
        for line in lines:
            line.set_data([], [])
        return lines

    def animate(frame_idx):
        psi = psi_frames_np[frame_idx]

        line_idx = 0
        if show_real_imag:
            lines[line_idx].set_data(x_np, psi.real)
            lines[line_idx + 1].set_data(x_np, psi.imag)
            line_idx += 2

        if show_probability:
            prob = np.abs(psi) ** 2
            lines[line_idx].set_data(x_np, prob)

        return lines

    anim = animation.FuncAnimation(
        fig, animate, init_func=init, frames=len(psi_frames), interval=interval, blit=True
    )

    return anim


def plot_wavefunction_2d(
    X: Array,
    Y: Array,
    psi: Array,
    title: str = "",
    plot_type: str = "probability",
    figsize: tuple[float, float] = (8, 7),
    cmap: str = "viridis",
    units: str = "a.u.",
    vmin: float | None = None,
    vmax: float | None = None,
) -> Figure:
    r"""Plot 2D wavefunction with publication quality.

    Args:
        X: X-coordinate grid (2D array)
        Y: Y-coordinate grid (2D array)
        psi: Wavefunction values (complex 2D array)
        title: Plot title
        plot_type: "probability", "real", "imag", or "phase"
        figsize: Figure size (width, height) in inches
        cmap: Colormap name (viridis, plasma, inferno, twilight)
        units: Physical units label (default: "a.u.")
        vmin: Minimum value for colormap (auto if None)
        vmax: Maximum value for colormap (auto if None)

    Returns:
        Matplotlib Figure object

    Example:
        >>> X, Y, dx, dy = create_grid_2d(-5, 5, 256, -5, 5, 256)
        >>> psi = jnp.exp(-(X**2 + Y**2) / 2)
        >>> fig = plot_wavefunction_2d(X, Y, psi)
        >>> plt.show()
    """
    X_np = np.array(X)
    Y_np = np.array(Y)
    psi_np = np.array(psi)

    fig, ax = plt.subplots(figsize=figsize)

    if plot_type == "probability":
        data = np.abs(psi_np) ** 2
        label = r"$|\psi|^2$"
        if cmap == "viridis":
            cmap = "inferno"  # Better for probability density
    elif plot_type == "real":
        data = psi_np.real
        label = r"Re$(\psi)$"
        if cmap == "viridis":
            cmap = "RdBu_r"  # Diverging for real/imaginary
    elif plot_type == "imag":
        data = psi_np.imag
        label = r"Im$(\psi)$"
        if cmap == "viridis":
            cmap = "RdBu_r"
    elif plot_type == "phase":
        data = np.angle(psi_np)
        label = r"arg$(\psi)$"
        cmap = "twilight"  # Cyclic colormap for phase
    else:
        raise ValueError(
            f"Unknown plot_type: {plot_type}. Use 'probability', 'real', 'imag', or 'phase'."
        )

    im = ax.pcolormesh(X_np, Y_np, data, cmap=cmap, shading="auto", vmin=vmin, vmax=vmax)
    ax.set_xlabel(f"$x$ ({units})")
    ax.set_ylabel(f"$y$ ({units})")
    if title:
        ax.set_title(f"{title} — {label}")
    else:
        ax.set_title(label)
    ax.set_aspect("equal")

    cbar = plt.colorbar(im, ax=ax, label=label, format="%.2e")
    cbar.ax.tick_params(labelsize=10)

    plt.tight_layout()
    return fig


def animate_wavefunction_2d(
    X: Array,
    Y: Array,
    psi_frames: list[Array],
    times: list[float],
    figsize: tuple[float, float] = (10, 8),
    plot_type: str = "probability",
    cmap: str = "inferno",
    units: str = "a.u.",
    scale_factor: float = 1.0,
    scale_units: str | None = None,
    interval: int = 50,
    title: str = "",
    setup_callback: Callable | None = None,
    update_callback: Callable | None = None,
) -> animation.FuncAnimation:
    r"""Animate 2D wavefunction evolution with optional custom setup/update.

    Args:
        X, Y: Coordinate grids (2D arrays)
        psi_frames: List of wavefunction snapshots (complex 2D arrays)
        times: List of time values for each frame
        figsize: Figure size (width, height) in inches
        plot_type: "probability", "real", "imag", or "phase"
        cmap: Colormap (inferno for probability, RdBu_r for real/imag, twilight for phase)
        units: Physical units label (default: "a.u.")
        scale_factor: Coordinate scaling (e.g., 1000 for nm→μm)
        scale_units: Scaled units label (e.g., "μm")
        interval: Time between frames (ms)
        title: Animation title
        setup_callback: Optional function(fig, axes, X, Y, psi0) -> dict
            Called once to set up custom visualization elements.
            Should return dict of objects to update in animation.
        update_callback: Optional function(frame_idx, psi, t, objects) -> None
            Called each frame to update custom elements.
            objects is the dict returned by setup_callback.

    Returns:
        Matplotlib FuncAnimation object

    Example:
        >>> # Simple usage
        >>> anim = animate_wavefunction_2d(X, Y, psi_frames, times)

        >>> # With custom barrier visualization
        >>> def setup(fig, axes, X, Y, psi0):
        ...     ax = axes[0]
        ...     barrier_contour = ax.contour(X, Y, V > 0, colors='cyan')
        ...     return {'barrier': barrier_contour}
        >>> anim = animate_wavefunction_2d(X, Y, psi_frames, times,
        ...                                setup_callback=setup)
    """
    X_np = np.array(X)
    Y_np = np.array(Y)
    psi_frames_np = [np.array(psi) for psi in psi_frames]

    # Determine plot type and colormap
    if plot_type == "probability":
        label = r"$|\psi|^2$"
        if cmap == "viridis":
            cmap = "inferno"
    elif plot_type == "real":
        label = r"Re$(\psi)$"
        if cmap == "inferno":
            cmap = "RdBu_r"
    elif plot_type == "imag":
        label = r"Im$(\psi)$"
        if cmap == "inferno":
            cmap = "RdBu_r"
    elif plot_type == "phase":
        label = r"arg$(\psi)$"
        cmap = "twilight"
    else:
        raise ValueError(
            f"Unknown plot_type: {plot_type}. Use 'probability', 'real', 'imag', or 'phase'."
        )

    # Apply coordinate scaling
    if scale_factor != 1.0:
        X_scaled = X_np / scale_factor
        Y_scaled = Y_np / scale_factor
        display_units = scale_units if scale_units else units
    else:
        X_scaled = X_np
        Y_scaled = Y_np
        display_units = units

    # Get initial data based on plot type
    psi_initial = psi_frames_np[0]
    if plot_type == "probability":
        data_initial = np.abs(psi_initial) ** 2
        vmin_init, vmax_init = 0, data_initial.max()
    elif plot_type == "real":
        data_initial = psi_initial.real
        vmax_init = max(abs(data_initial.min()), abs(data_initial.max()))
        vmin_init = -vmax_init
    elif plot_type == "imag":
        data_initial = psi_initial.imag
        vmax_init = max(abs(data_initial.min()), abs(data_initial.max()))
        vmin_init = -vmax_init
    elif plot_type == "phase":
        data_initial = np.angle(psi_initial)
        vmin_init, vmax_init = -np.pi, np.pi

    fig, ax = plt.subplots(figsize=figsize)

    # Create initial plot
    im = ax.pcolormesh(
        X_scaled, Y_scaled, data_initial, cmap=cmap, vmin=vmin_init, vmax=vmax_init, shading="auto"
    )

    ax.set_xlabel(f"$x$ ({display_units})", fontsize=12)
    ax.set_ylabel(f"$y$ ({display_units})", fontsize=12)
    if title:
        ax.set_title(f"{title} — {label}", fontsize=13)
    else:
        ax.set_title(label, fontsize=13)
    ax.set_aspect("equal")

    cbar = plt.colorbar(im, ax=ax, label=label)
    cbar.ax.tick_params(labelsize=9)

    # Call setup callback if provided
    custom_objects = {}
    if setup_callback is not None:
        custom_objects = setup_callback(fig, ax, X_scaled, Y_scaled, psi_frames_np[0])
        if custom_objects is None:
            custom_objects = {}

    def animate_frame(frame_idx):
        """Update animation frame."""
        psi = psi_frames_np[frame_idx]
        t = times[frame_idx]

        # Get data based on plot type
        if plot_type == "probability":
            data = np.abs(psi) ** 2
            im.set_clim(vmin=0, vmax=data.max() * 0.9)
        elif plot_type == "real":
            data = psi.real
            vmax = max(abs(data.min()), abs(data.max()))
            im.set_clim(vmin=-vmax, vmax=vmax)
        elif plot_type == "imag":
            data = psi.imag
            vmax = max(abs(data.min()), abs(data.max()))
            im.set_clim(vmin=-vmax, vmax=vmax)
        elif plot_type == "phase":
            data = np.angle(psi)
            im.set_clim(vmin=-np.pi, vmax=np.pi)

        im.set_array(data.ravel())

        # Call update callback if provided
        if update_callback is not None:
            update_callback(frame_idx, psi, t, custom_objects)

        return [im]

    anim = animation.FuncAnimation(
        fig, animate_frame, frames=len(psi_frames), interval=interval, blit=False
    )

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    return anim


def plot_wavefunction_3d(
    x: Array,
    psi: Array,
    title: str = "Quantum Wavefunction",
    figsize: tuple[float, float] = (14, 5),
    units: str = "a.u.",
    elev: float = 20,
    azim: float = -60,
) -> Figure:
    r"""Plot 1D wavefunction in 3D showing real, imaginary, and probability.

    Visualizes $\psi(x) = \text{Re}(\psi) + i\cdot\text{Im}(\psi)$ as a 3D curve,
    making the complex nature of the wavefunction intuitive for beginners.

    Args:
        x: Spatial grid (1D array)
        psi: Wavefunction values (complex)
        title: Plot title
        figsize: Figure size (width, height) in inches
        units: Physical units label
        elev: Elevation angle for 3D view (degrees)
        azim: Azimuth angle for 3D view (degrees)

    Returns:
        Matplotlib Figure object with 3D visualization

    Example:
        >>> x = jnp.linspace(-5, 5, 200)
        >>> psi = jnp.exp(-x**2/2) * jnp.exp(1j * 2 * x)
        >>> fig = plot_wavefunction_3d(x, psi)
        >>> plt.show()
    """

    x_np = np.array(x)
    psi_np = np.array(psi)

    fig = plt.figure(figsize=figsize)

    # 3D plot of Re(psi), Im(psi), and |psi|^2
    ax1 = fig.add_subplot(121, projection="3d")

    real = psi_np.real
    imag = psi_np.imag
    prob = np.abs(psi_np) ** 2

    # Plot the wavefunction as a 3D curve
    ax1.plot(x_np, real, imag, linewidth=2, color=COLORS["prob"], alpha=0.8, label=r"$\psi(x)$")

    # Project onto walls
    ax1.plot(x_np, real, zs=imag.min(), zdir="z", linewidth=1, color=COLORS["real"], alpha=0.4)
    ax1.plot(x_np, imag, zs=real.min(), zdir="y", linewidth=1, color=COLORS["imag"], alpha=0.4)

    ax1.set_xlabel(f"$x$ ({units})", labelpad=10)
    ax1.set_ylabel(r"Re$(\psi)$", labelpad=10)
    ax1.set_zlabel(r"Im$(\psi)$", labelpad=10)
    ax1.set_title(f"{title}\nComplex Wavefunction", fontsize=12, pad=15)
    ax1.view_init(elev=elev, azim=azim)
    ax1.grid(True, alpha=0.3)

    # 2D plot of probability density
    ax2 = fig.add_subplot(122)
    ax2.plot(x_np, prob, linewidth=2.5, color=COLORS["prob"], alpha=0.9)
    ax2.fill_between(x_np, prob, alpha=0.3, color=COLORS["prob"])
    ax2.set_xlabel(f"$x$ ({units})")
    ax2.set_ylabel(r"$|\psi(x)|^2$")
    ax2.set_title(f"{title}\nProbability Density", fontsize=12)
    ax2.grid(True, alpha=0.3, linestyle="--")
    ax2.set_ylim(bottom=0)

    plt.tight_layout()
    return fig


def plot_wavefunction_components(
    x: Array,
    psi: Array,
    title: str = "Anatomy of a Wavefunction",
    figsize: tuple[float, float] = (14, 8),
    units: str = "a.u.",
) -> Figure:
    r"""Educational plot showing all aspects of a wavefunction for beginners.

    Creates a comprehensive 4-panel visualization:
    1. Real and imaginary parts
    2. Magnitude $|\psi|$
    3. Probability density $|\psi|^2$
    4. Phase arg$(\psi)$

    Args:
        x: Spatial grid (1D array)
        psi: Wavefunction values (complex)
        title: Overall plot title
        figsize: Figure size (width, height) in inches
        units: Physical units label

    Returns:
        Matplotlib Figure object

    Example:
        >>> x = jnp.linspace(-5, 5, 200)
        >>> psi = jnp.exp(-x**2/2) * jnp.exp(1j * 2 * x)
        >>> fig = plot_wavefunction_components(x, psi)
        >>> plt.show()
    """
    x_np = np.array(x)
    psi_np = np.array(psi)

    fig, axes = plt.subplots(2, 2, figsize=figsize)
    fig.suptitle(title, fontsize=14, fontweight="bold", y=0.995)

    # Panel 1: Real and Imaginary parts
    ax = axes[0, 0]
    ax.plot(x_np, psi_np.real, label=r"Re$(\psi)$", linewidth=2, color=COLORS["real"], alpha=0.9)
    ax.plot(x_np, psi_np.imag, label=r"Im$(\psi)$", linewidth=2, color=COLORS["imag"], alpha=0.9)
    ax.axhline(0, color="k", linewidth=0.5, alpha=0.3)
    ax.set_xlabel(f"Position $x$ ({units})")
    ax.set_ylabel(r"Wavefunction $\psi(x)$")
    ax.set_title("Components: Real & Imaginary Parts", fontsize=11)
    ax.legend(loc="best", frameon=True, fancybox=True)
    ax.grid(True, alpha=0.3)

    # Panel 2: Magnitude
    ax = axes[0, 1]
    magnitude = np.abs(psi_np)
    ax.plot(x_np, magnitude, linewidth=2.5, color=COLORS["phase"], alpha=0.9)
    ax.fill_between(x_np, magnitude, alpha=0.3, color=COLORS["phase"])
    ax.set_xlabel(f"Position $x$ ({units})")
    ax.set_ylabel(r"$|\psi(x)|$")
    ax.set_title(r"Magnitude $|\psi|$", fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)

    # Panel 3: Probability density
    ax = axes[1, 0]
    prob = magnitude**2
    ax.plot(x_np, prob, linewidth=2.5, color=COLORS["prob"], alpha=0.9)
    ax.fill_between(x_np, prob, alpha=0.3, color=COLORS["prob"])
    ax.set_xlabel(f"Position $x$ ({units})")
    ax.set_ylabel(r"$|\psi(x)|^2$")
    ax.set_title(r"Probability Density $|\psi|^2$ (Born Rule)", fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)

    # Add annotation for total probability
    total_prob = np.trapz(prob, x_np)
    ax.text(
        0.98,
        0.95,
        f"$\\int |\\psi|^2 dx = {total_prob:.3f}$",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=10,
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
    )

    # Panel 4: Phase
    ax = axes[1, 1]
    phase = np.angle(psi_np)
    ax.plot(x_np, phase, linewidth=2, color=COLORS["phase"], alpha=0.9)
    ax.axhline(0, color="k", linewidth=0.5, alpha=0.3)
    ax.set_xlabel(f"Position $x$ ({units})")
    ax.set_ylabel(r"$\arg(\psi)$ (radians)")
    ax.set_title(r"Phase $\arg(\psi)$", fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-np.pi - 0.2, np.pi + 0.2)
    ax.set_yticks([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi])
    ax.set_yticklabels([r"$-\pi$", r"$-\pi/2$", "0", r"$\pi/2$", r"$\pi$"])

    plt.tight_layout()
    return fig


def plot_wavefunction_2d_comprehensive(
    X: Array,
    Y: Array,
    psi: Array,
    title: str = "2D Wavefunction",
    figsize: tuple[float, float] = (16, 4),
    units: str = "a.u.",
) -> Figure:
    r"""Educational 2D wavefunction visualization showing all components.

    Creates a 4-panel visualization of a 2D wavefunction:
    1. Probability density $|\psi|^2$
    2. Real part Re$(\psi)$
    3. Imaginary part Im$(\psi)$
    4. Phase arg$(\psi)$

    Args:
        X: X-coordinate grid (2D array)
        Y: Y-coordinate grid (2D array)
        psi: Wavefunction values (complex 2D array)
        title: Overall plot title
        figsize: Figure size (width, height) in inches
        units: Physical units label

    Returns:
        Matplotlib Figure object

    Example:
        >>> X, Y, dx, dy = create_grid_2d(-5, 5, 128, -5, 5, 128)
        >>> psi = jnp.exp(-(X**2 + Y**2) / 2)
        >>> fig = plot_wavefunction_2d_comprehensive(X, Y, psi)
        >>> plt.show()
    """
    X_np = np.array(X)
    Y_np = np.array(Y)
    psi_np = np.array(psi)

    fig, axes = plt.subplots(1, 4, figsize=figsize)

    # Panel 1: Probability
    ax = axes[0]
    prob = np.abs(psi_np) ** 2
    im = ax.pcolormesh(X_np, Y_np, prob, cmap="inferno", shading="auto")
    ax.set_xlabel(f"$x$ ({units})")
    ax.set_ylabel(f"$y$ ({units})")
    ax.set_title(r"$|\psi|^2$", fontsize=12, fontweight="bold")
    ax.set_aspect("equal")
    plt.colorbar(im, ax=ax, label=r"$|\psi|^2$")

    # Panel 2: Real part
    ax = axes[1]
    real = psi_np.real
    vmax = max(abs(real.min()), abs(real.max()))
    im = ax.pcolormesh(X_np, Y_np, real, cmap="RdBu_r", shading="auto", vmin=-vmax, vmax=vmax)
    ax.set_xlabel(f"$x$ ({units})")
    ax.set_ylabel(f"$y$ ({units})")
    ax.set_title(r"Re$(\psi)$", fontsize=12, fontweight="bold")
    ax.set_aspect("equal")
    plt.colorbar(im, ax=ax, label=r"Re$(\psi)$")

    # Panel 3: Imaginary part
    ax = axes[2]
    imag = psi_np.imag
    vmax = max(abs(imag.min()), abs(imag.max()))
    im = ax.pcolormesh(X_np, Y_np, imag, cmap="RdBu_r", shading="auto", vmin=-vmax, vmax=vmax)
    ax.set_xlabel(f"$x$ ({units})")
    ax.set_ylabel(f"$y$ ({units})")
    ax.set_title(r"Im$(\psi)$", fontsize=12, fontweight="bold")
    ax.set_aspect("equal")
    plt.colorbar(im, ax=ax, label=r"Im$(\psi)$")

    # Panel 4: Phase
    ax = axes[3]
    phase = np.angle(psi_np)
    im = ax.pcolormesh(X_np, Y_np, phase, cmap="twilight", shading="auto", vmin=-np.pi, vmax=np.pi)
    ax.set_xlabel(f"$x$ ({units})")
    ax.set_ylabel(f"$y$ ({units})")
    ax.set_title(r"$\arg(\psi)$", fontsize=12, fontweight="bold")
    ax.set_aspect("equal")
    plt.colorbar(im, ax=ax, label=r"$\arg(\psi)$ (rad)")

    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    return fig
