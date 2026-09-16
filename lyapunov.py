"""
lyapunov.py — Eksponen Lyapunov Peta Kaos
==========================================
File ini berisi fungsi untuk menghitung dan memvisualisasikan
Eksponen Lyapunov (µ) dari peta kaos MS Gauss Map (komposisi g∘f).

PENGERTIAN EKSPONEN LYAPUNOV:
  Eksponen Lyapunov mengukur laju divergensi dua trajektori yang
  dimulai dari kondisi awal yang sangat berdekatan.

  Interpretasi:
    µ > 0  →  sistem bersifat KAOTIK (sensitif terhadap kondisi awal)
    µ = 0  →  batas chaos (titik bifurkasi)
    µ < 0  →  sistem STABIL (periodik/konvergen)

METODE PERHITUNGAN (Wolf Method):
  µ ≈ (1/N) Σ log[ |x1(n) - x2(n)| / dx ]

  di mana:
    x1 = trajektori referensi dengan nilai awal x0
    x2 = trajektori perturbed dengan nilai awal x0 + dx
    dx = 1e-8 (gangguan awal yang sangat kecil)

FUNGSI UTAMA FILE INI:
  1. compute_lyapunov_exponent() — hitung nilai µ untuk rentang parameter
  2. plot_lyapunov_exponent()    — plot µ vs parameter (4 subplot: r, α, β, λ)

CATATAN:
  - Menggunakan 1000 iterasi, skip 200, dx = 1e-8
  - Grafik mewarnai area µ > 0 (hijau = kaotik) dan µ ≤ 0 (merah = stabil)
"""

import numpy as np
import matplotlib.pyplot as plt
from chaos_map import _iterate_ms_gauss_gof


# ─── Konfigurasi Parameter Lyapunov ──────────────────────────────────────────

LYAPUNOV_PARAMS = {
    "r":     (np.linspace(2.5, 4.0, 200), "r (Komposisi GoF)"),
    "alpha": (np.linspace(2.0, 8.0, 200), "α (Komposisi GoF)"),
    "beta":  (np.linspace(2.0, 5.0, 200), "β (Komposisi GoF)"),
    "lam":   (np.linspace(2.5, 5.0, 200), "λ (Komposisi GoF)"),
}


# ─── Hitung Eksponen Lyapunov ─────────────────────────────────────────────────

def compute_lyapunov_exponent(
    param_name: str,
    param_range: np.ndarray,
    base_params: dict,
    n_iter: int = 1000,
    skip: int = 200,
) -> np.ndarray:
    """
    Hitung Eksponen Lyapunov (µ) untuk rentang nilai satu parameter.

    Menggunakan metode Wolf: dua trajektori dimulai dengan kondisi awal
    yang hampir sama (selisih dx = 1e-8), kemudian divergensinya diukur
    secara rata-rata di sepanjang iterasi.

    µ > 0 → sistem chaotic
    µ = 0 → batas chaos (bifurkasi)
    µ < 0 → sistem stabil (periodik)

    Parameters
    ----------
    param_name  : str        — nama parameter yang divariasikan
    param_range : np.ndarray — nilai-nilai parameter yang diuji
    base_params : dict       — parameter dasar peta kaos
    n_iter      : int        — jumlah iterasi (default: 1000)
    skip        : int        — iterasi transient yang dibuang (default: 200)

    Returns
    -------
    lyap : np.ndarray float64 — nilai µ untuk setiap nilai parameter
    """
    lyap = np.zeros(len(param_range))
    dx   = 1e-8

    for i, val in enumerate(param_range):
        p = dict(base_params)
        p[param_name] = val
        r     = float(p.get("r",     3.5))
        lam   = float(p.get("lam",   3.5))
        alpha = float(p.get("alpha", 5.8))
        beta  = float(p.get("beta",  3.1))
        x0    = float(p.get("x0",    0.3))

        total = n_iter + skip

        # Dua trajektori: referensi dan perturbed
        seq1 = _iterate_ms_gauss_gof(x0,      total, r, lam, alpha, beta)[skip:]
        seq2 = _iterate_ms_gauss_gof(x0 + dx, total, r, lam, alpha, beta)[skip:]

        # Selisih; hindari log(0)
        diff = np.abs(seq1 - seq2)
        diff = np.where(diff < 1e-300, 1e-300, diff)

        # Lyapunov = rata-rata log dari rasio divergensi terhadap dx awal
        lyap[i] = float(np.mean(np.log(diff / dx)))

    return lyap


# ─── Plot Eksponen Lyapunov ───────────────────────────────────────────────────

def plot_lyapunov_exponent(
    base_params: dict,
    save_path: str = None,
) -> None:
    """
    Plot Eksponen Lyapunov (µ) untuk 4 parameter: r, α, β, λ.

    Menampilkan 4 subplot dalam satu figure (2×2 grid).
    Area µ > 0 diarsir hijau (kaotik), area µ ≤ 0 diarsir merah (stabil).
    Garis putus-putus merah menunjukkan batas µ = 0.

    Parameters
    ----------
    base_params : dict — parameter dasar peta kaos
    save_path   : str  — path file output (PNG), None = hanya tampilkan
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Lyapunov Exponent (µ) vs Parameter\nµ > 0 = Chaotic",
                 fontsize=14, fontweight="bold")

    for ax, (pname, (prange, plabel)) in zip(axes.ravel(), LYAPUNOV_PARAMS.items()):
        print(f"  [Lyapunov] Menghitung untuk parameter {pname}...")
        lyap = compute_lyapunov_exponent(pname, prange, base_params)

        ax.plot(prange, lyap, color="steelblue", linewidth=0.8)
        ax.axhline(0, color="red", linestyle="--", linewidth=1.2, label="µ = 0 (batas chaos)")
        ax.fill_between(prange, lyap, 0,
                        where=(lyap > 0),  alpha=0.2, color="green", label="Chaotic (µ>0)")
        ax.fill_between(prange, lyap, 0,
                        where=(lyap <= 0), alpha=0.2, color="red",   label="Stabil (µ≤0)")
        ax.set_xlabel(plabel)
        ax.set_ylabel("Lyapunov Exponent (µ)")
        ax.set_title(f"µ vs {plabel}")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[OK] Lyapunov plot -> {save_path}")
    plt.show()
