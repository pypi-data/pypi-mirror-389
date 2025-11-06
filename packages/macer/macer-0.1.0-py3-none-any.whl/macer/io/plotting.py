import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def plot_relaxation_log(prefix, output_dir, energies, steps, forces_hist, stress_hist, isif, atoms):
    fig, ax1 = plt.subplots(figsize=(6, 4))
    if energies:
        ax1.plot(steps, energies, color="tab:blue", marker="o", lw=1.0, label="Total Energy (eV)")
    else:
        e_final = atoms.get_potential_energy()
        ax1.scatter([0], [e_final], color="tab:blue", label="Single-point Energy (eV)")
    ax1.set_xlabel("Optimization step" if energies else "Single point")
    ax1.set_ylabel("Energy (eV)", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")
    ax1.grid(alpha=0.3)

    if energies and forces_hist:
        ax2 = ax1.twinx()
        ax2.plot(steps, forces_hist, color="tab:red", marker="s", lw=1.0, label="Fmax (eV/Å)")
        if isif >= 3:
            ax2.plot(steps, stress_hist, color="tab:green", marker="^", lw=1.0, label="σmax (eV/Å³)")
        ax2.set_ylabel("Force / Stress", color="tab:red")
        ax2.tick_params(axis="y", labelcolor="tab:red")
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc="best")
    else:
        ax1.legend(loc="best")

    plt.title(f"Relaxation progress ({prefix})")
    plt.tight_layout()
    pdf_name = os.path.join(output_dir, f"relax-{prefix}_log.pdf")
    plt.savefig(pdf_name)
    plt.close(fig)
    print(f" Saved detailed log plot → {pdf_name}")
