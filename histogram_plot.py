"""
histogram_plot.py — Visualisasi Histogram dan Perbandingan Citra
================================================================
File ini berisi fungsi untuk menghasilkan grafik histogram dan
plot perbandingan citra (asli, terenkripsi, terdekripsi) sebagai
alat evaluasi visual kualitas enkripsi.

TUJUAN VISUALISASI:
  Histogram yang seragam (flat) pada citra terenkripsi menandakan
  distribusi piksel acak yang baik — salah satu indikator utama
  kualitas enkripsi berbasis peta kaos.

FUNGSI UTAMA FILE INI:
  1. plot_histogram_comparison() — histogram 3 citra side by side
     (asli, terenkripsi, terdekripsi) dalam satu figure
  2. plot_image_comparison()     — tampilkan 3 citra side by side
     untuk perbandingan visual langsung

CATATAN:
  - Histogram citra asli biasanya tidak seragam (ada pola distribusi)
  - Histogram citra terenkripsi idealnya seragam/datar (distribusi merata)
  - Histogram citra terdekripsi harus identik dengan citra asli
"""

import numpy as np
import cv2
import matplotlib.pyplot as plt


# ─── Helper ──────────────────────────────────────────────────────────────────

def _gray(img: np.ndarray) -> np.ndarray:
    """Konversi citra ke grayscale jika belum grayscale."""
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img


def _to_rgb(img: np.ndarray) -> np.ndarray:
    """Konversi BGR ke RGB untuk ditampilkan dengan matplotlib."""
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if img.ndim == 3 else img


# ─── Plot Histogram Perbandingan ──────────────────────────────────────────────

def plot_histogram_comparison(
    original:  np.ndarray,
    encrypted: np.ndarray,
    decrypted: np.ndarray,
    save_path: str = None,
) -> None:
    """
    Plot histogram piksel untuk tiga citra secara berdampingan (side by side).

    Sumbu X  : nilai intensitas piksel (0–255)
    Sumbu Y  : frekuensi kemunculan setiap nilai intensitas

    Interpretasi:
    - Histogram asli      : distribusi bervariasi (ada pola/kontur)
    - Histogram terenkripsi : distribusi seragam/datar (ideal untuk enkripsi)
    - Histogram terdekripsi : identik dengan histogram asli (dekripsi sempurna)

    Parameters
    ----------
    original  : np.ndarray — citra asli (BGR atau grayscale)
    encrypted : np.ndarray — citra terenkripsi
    decrypted : np.ndarray — citra terdekripsi
    save_path : str        — path file output (PNG), None = hanya tampilkan
    """
    imgs   = [original,    encrypted,  decrypted]
    titles = ["Original",  "Encrypted", "Decrypted"]
    colors = ["steelblue", "crimson",   "seagreen"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle("Histogram Perbandingan", fontsize=14, fontweight="bold")

    for ax, img, title, color in zip(axes, imgs, titles, colors):
        ax.hist(_gray(img).flatten(), bins=256, range=(0, 256),
                color=color, alpha=0.85, edgecolor="none")
        ax.set_title(title)
        ax.set_xlabel("Intensitas")
        ax.set_ylabel("Frekuensi")
        ax.set_xlim([0, 255])

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[OK] Histogram -> {save_path}")
    plt.show()


# ─── Plot Perbandingan Visual Citra ──────────────────────────────────────────

def plot_image_comparison(
    original:  np.ndarray,
    encrypted: np.ndarray,
    decrypted: np.ndarray,
    save_path: str = None,
) -> None:
    """
    Tampilkan tiga citra secara berdampingan untuk perbandingan visual.

    Citra ditampilkan dalam satu figure dengan 3 kolom:
    [Asli] | [Terenkripsi] | [Terdekripsi]

    Parameters
    ----------
    original  : np.ndarray — citra asli (BGR atau grayscale)
    encrypted : np.ndarray — citra terenkripsi
    decrypted : np.ndarray — citra terdekripsi
    save_path : str        — path file output (PNG), None = hanya tampilkan
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Perbandingan Citra", fontsize=14, fontweight="bold")

    for ax, img, title in zip(axes,
                               [original, encrypted, decrypted],
                               ["Original", "Encrypted", "Decrypted"]):
        ax.imshow(_to_rgb(img), cmap="gray" if img.ndim == 2 else None)
        ax.set_title(title)
        ax.axis("off")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[OK] Comparison -> {save_path}")
    plt.show()
