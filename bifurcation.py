"""
bifurcation.py — Diagram Bifurkasi Peta Kaos
=============================================
File ini berisi fungsi untuk menghasilkan dan memvisualisasikan
Diagram Bifurkasi dari peta kaos MS Gauss Map (komposisi g∘f).

PENGERTIAN DIAGRAM BIFURKASI:
  Diagram bifurkasi menampilkan nilai-nilai Xn yang dicapai oleh
  sistem kaotik untuk berbagai nilai parameter. Area yang padat
  (dense) menunjukkan perilaku kaotik, sedangkan titik-titik
  terpisah menunjukkan perilaku periodik.

FUNGSI UTAMA FILE INI:
  1. compute_bifurcation_data() — hitung data bifurkasi mentah
  2. plot_bifurcation_diagram() — tampilkan diagram bifurkasi
     untuk 4 parameter: r, α, β, λ

PARAMETER YANG DIANALISIS:
  - r     : rentang [2.5, 4.0]
  - α     : rentang [2.0, 8.0]
  - β     : rentang [2.0, 5.0]
  - λ     : rentang [2.5, 5.0]

CATATAN:
  - Menggunakan 500 titik per parameter
  - Menampilkan 100 iterasi terakhir setelah skip 200
  - Area padat pada diagram = sistem bersifat kaotik
"""

import numpy as np
import matplotlib.pyplot as plt
from chaos_map import _iterate_ms_gauss_gof


# ─── Konfigurasi Parameter Bifurkasi ─────────────────────────────────────────

BIFURCATION_PARAMS = {
    "r":     (np.linspace(2.5, 4.0, 500), "r (Komposisi GoF)"),
    "alpha": (np.linspace(2.0, 8.0, 500), "α (Komposisi GoF)"),
    "beta":  (np.linspace(2.0, 5.0, 500), "β (Komposisi GoF)"),
    "lam":   (np.linspace(2.5, 5.0, 500), "λ (Komposisi GoF)"),
}


# ─── Hitung Data Bifurkasi ────────────────────────────────────────────────────

def compute_bifurcation_data(
    param_name: str,
    param_range: np.ndarray,
    base_params: dict,
    n_skip: int = 200,
    n_last: int = 100,
) -> tuple:
    """
    Hitung data bifurkasi untuk satu parameter.

    Untuk setiap nilai parameter dalam param_range, iterasi peta kaos
    dijalankan sebanyak n_skip + n_last iterasi. Nilai n_last terakhir
    (setelah transient dibuang) dikumpulkan sebagai titik diagram.

    Parameters
    ----------
    param_name  : str          — nama parameter yang divariasikan ('r'/'alpha'/'beta'/'lam')
    param_range : np.ndarray   — nilai-nilai parameter yang diuji
    base_params : dict         — parameter dasar peta kaos
    n_skip      : int          — jumlah iterasi transient yang dibuang (default: 200)
    n_last      : int          — jumlah iterasi yang ditampilkan (default: 100)

    Returns
    -------
    (xs, ys) : tuple of list
        xs — nilai parameter (sumbu x)
        ys — nilai Xn yang dihasilkan (sumbu y)
    """
    xs, ys = [], []
    for val in param_range:
        p = dict(base_params)
        p[param_name] = val
        r     = float(p.get("r",     3.5))
        lam   = float(p.get("lam",   3.5))
        alpha = float(p.get("alpha", 5.8))
        beta  = float(p.get("beta",  3.1))
        x0    = float(p.get("x0",    0.3))

        seq  = _iterate_ms_gauss_gof(x0, n_skip + n_last, r, lam, alpha, beta)
        last = seq[n_skip:]
        xs.extend([val] * len(last))
        ys.extend(last.tolist())

    return xs, ys


# ─── Plot Diagram Bifurkasi ───────────────────────────────────────────────────

def plot_bifurcation_diagram(
    base_params: dict,
    save_path: str = None,
) -> None:
    """
    Plot Diagram Bifurkasi untuk 4 parameter: r, α, β, λ.

    Menampilkan 4 subplot dalam satu figure (2×2 grid).
    Setiap subplot memperlihatkan perilaku sistem kaotik terhadap
    perubahan nilai satu parameter.

    Area yang padat (banyak titik) pada diagram menandakan sistem
    berada dalam kondisi kaotik (chaos).

    Parameters
    ----------
    base_params : dict — parameter dasar peta kaos
    save_path   : str  — path file output (PNG), None = hanya tampilkan
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Diagram Bifurkasi\nArea Padat = Chaotic",
                 fontsize=14, fontweight="bold")

    for ax, (pname, (prange, plabel)) in zip(axes.ravel(), BIFURCATION_PARAMS.items()):
        print(f"  [Bifurkasi] Menghitung untuk parameter {pname}...")
        xs, ys = compute_bifurcation_data(pname, prange, base_params)

        ax.scatter(xs, ys, s=0.1, alpha=0.3, color="navy", rasterized=True)
        ax.set_xlabel(plabel)
        ax.set_ylabel("Xn")
        ax.set_title(f"Bifurkasi — {plabel}")
        ax.grid(True, alpha=0.2)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[OK] Bifurkasi plot -> {save_path}")
    plt.show()
