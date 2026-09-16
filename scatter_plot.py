"""
scatter_plot.py — Scatter Plot Keystream dan Korelasi Piksel
============================================================
File ini berisi fungsi untuk menghasilkan dua jenis scatter plot
yang digunakan sebagai bukti visual kualitas kaotik dan enkripsi.

JENIS SCATTER PLOT:
  1. Scatter Plot Keystream (Sensitivitas Kondisi Awal)
     → Membuktikan sifat sensitif terhadap kondisi awal (butterfly effect)
     → Tiga nilai X0 yang hampir sama (0.3, 0.3001, 0.30001) menghasilkan
       lintasan Xk yang sama sekali berbeda setelah beberapa iterasi

  2. Scatter Plot Korelasi Piksel
     → Membandingkan korelasi piksel bertetangga antara citra asli
       dan citra terenkripsi
     → Citra asli: titik-titik mengumpul (korelasi tinggi)
     → Citra terenkripsi: titik-titik tersebar acak (korelasi ~0)

CATATAN:
  - Scatter plot keystream menampilkan iterasi ke-200 hingga ke-240
  - Scatter plot korelasi menggunakan 3000 sampel piksel acak
  - Arah korelasi yang didukung: horizontal, vertical, diagonal
"""

import numpy as np
import cv2
import matplotlib.pyplot as plt
from keystream_generator import generate_chaos_sequence


# ─── Helper ──────────────────────────────────────────────────────────────────

def _gray(img: np.ndarray) -> np.ndarray:
    """Konversi citra ke grayscale jika belum grayscale."""
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img


# ─── Scatter Plot Keystream (Sensitivitas Kondisi Awal) ──────────────────────

def plot_keystream_scatter(
    base_params: dict,
    n_points:   int = 250,
    save_path:  str = None,
) -> None:
    """
    Scatter plot Xk vs nomor iterasi untuk 3 nilai X0 yang berbeda tipis.

    Menampilkan bahwa perbedaan kecil pada kondisi awal X0 menghasilkan
    lintasan kaotik yang sama sekali berbeda setelah beberapa iterasi
    (butterfly effect / sensitivitas kondisi awal).

    Nilai X0 yang digunakan: 0.3, 0.3001, 0.30001
    Rentang iterasi yang ditampilkan: 200 hingga 240

    Parameters
    ----------
    base_params : dict — parameter dasar peta kaos
    n_points    : int  — total iterasi yang dibangkitkan (default: 250)
    save_path   : str  — path file output (PNG), None = hanya tampilkan
    """
    x0_values = [0.3, 0.3001, 0.30001]
    colors    = ["#4472C4", "#C00000", "#70AD47"]
    markers   = ["o", "s", "^"]
    labels    = ["0.3", "0.3001", "0.30001"]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_title("Scatter Plot MS Gauss Map", fontsize=14, fontweight="bold")

    for x0, color, marker, label in zip(x0_values, colors, markers, labels):
        p = dict(base_params)
        p["x0"] = x0
        seq     = generate_chaos_sequence(n_points, p)

        # Ambil iterasi 200–240
        x_range = np.arange(200, 241)
        y_range = seq[200:241]

        ax.scatter(x_range, y_range, s=15, color=color,
                   marker=marker, label=label, alpha=0.8)

    ax.set_xlabel("iterasi ke i (200 - 300)", fontsize=11, labelpad=10)
    ax.set_ylabel("Xk+1", fontsize=11, rotation=0, labelpad=20)
    ax.set_ylim([0, 1])
    ax.set_xlim([200, 240])
    ax.set_xticks(np.arange(200, 241, 10))
    ax.set_yticks(np.arange(0, 1.1, 0.1))
    ax.grid(axis='y', linestyle='-', linewidth=1, color='gray', alpha=0.5)
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5),
              frameon=False, handletextpad=0.1, markerscale=0.8, fontsize=10)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[OK] Keystream scatter -> {save_path}")
    plt.show()


# ─── Scatter Plot Korelasi Piksel ─────────────────────────────────────────────

def plot_correlation_scatter(
    original:  np.ndarray,
    encrypted: np.ndarray,
    direction: str = "horizontal",
    n_samples: int = 3000,
    save_path: str = None,
) -> None:
    """
    Scatter plot korelasi piksel bertetangga: citra asli vs terenkripsi.

    Setiap titik mewakili pasangan piksel yang bertetangga.
    - Citra asli      : titik mengumpul di diagonal → korelasi tinggi
    - Citra terenkripsi : titik tersebar merata → korelasi mendekati 0

    Parameters
    ----------
    original  : np.ndarray — citra asli (BGR atau grayscale)
    encrypted : np.ndarray — citra terenkripsi
    direction : str        — arah tetangga: 'horizontal', 'vertical', 'diagonal'
    n_samples : int        — jumlah sampel piksel (default: 3000)
    save_path : str        — path file output (PNG), None = hanya tampilkan
    """
    from analysis import compute_correlation

    def _pairs(img):
        g = _gray(img).astype(np.float64)
        if direction == "horizontal":
            x, y = g[:, :-1].ravel(), g[:, 1:].ravel()
        elif direction == "vertical":
            x, y = g[:-1, :].ravel(), g[1:, :].ravel()
        else:
            x, y = g[:-1, :-1].ravel(), g[1:, 1:].ravel()
        idx = np.random.choice(len(x), min(n_samples, len(x)), replace=False)
        return x[idx], y[idx]

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    fig.suptitle(f"Scatter Korelasi Piksel — {direction.capitalize()}",
                 fontsize=13, fontweight="bold")

    for ax, img, title, color in zip(
        axes, [original, encrypted], ["Original", "Encrypted"], ["steelblue", "crimson"]
    ):
        px, py = _pairs(img)
        ax.scatter(px, py, s=1, alpha=0.3, color=color)
        ax.set_title(f"{title}  (r={compute_correlation(img, direction):.4f})")
        ax.set_xlabel("Piksel ke-i")
        ax.set_ylabel("Piksel ke-i+1")
        ax.set_xlim([0, 255])
        ax.set_ylim([0, 255])

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[OK] Scatter plot -> {save_path}")
    plt.show()
