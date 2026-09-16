"""
analysis.py — Metrik Statistik Kualitas Enkripsi
=================================================
File ini berisi fungsi-fungsi untuk menghitung metrik statistik yang
digunakan untuk mengukur dan mengevaluasi kualitas enkripsi citra.

TANGGUNG JAWAB FILE INI:
  1. Menghitung metrik kualitas enkripsi secara statistik
  2. Menggabungkan semua metrik dalam satu fungsi full_analysis()
  3. Mencetak dan menyimpan hasil analisis

METRIK YANG DIHITUNG:
  ✅ Entropi Shannon      → mengukur keacakan distribusi piksel (ideal ≈ 8.0)
  ✅ Korelasi Piksel      → mengukur kemiripan piksel bertetangga (ideal ≈ 0.0)
  ✅ MSE & PSNR           → mengukur perbedaan antara dua gambar
  ✅ NPCR (%)             → mengukur perubahan piksel saat 1 bit kunci berubah (ideal ≥ 99.6%)
  ✅ UACI (%)             → mengukur rata-rata intensitas perubahan (ideal ≈ 33.46%)
  ✅ Chi-Square           → menguji apakah distribusi piksel seragam (uniform)

MODUL ANALISIS LANJUTAN (file terpisah):
  → bifurcation.py       — Diagram Bifurkasi
  → lyapunov.py          — Eksponen Lyapunov
  → nist_tests.py        — 15 Uji NIST SP 800-22
  → histogram_plot.py    — Plot Histogram & Perbandingan Gambar
  → scatter_plot.py      — Scatter Plot Keystream & Korelasi Piksel

CATATAN:
  - File ini TIDAK melakukan enkripsi/dekripsi
  - Re-import dari modul analisis lanjutan disediakan untuk backward compatibility
"""

import numpy as np
import cv2
import matplotlib.pyplot as plt
import csv
import math
from pathlib import Path
from scipy import stats as scipy_stats


# ─── Helper ──────────────────────────────────────────────────────────────────

def _gray(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img


def _u8(img: np.ndarray) -> np.ndarray:
    return img.astype(np.uint8)


# ─── Metrik Standar ──────────────────────────────────────────────────────────

def compute_entropy(img: np.ndarray) -> float:
    """Shannon Entropy — ideal ≈ 8.0 untuk citra terenkripsi."""
    hist = np.bincount(img.flatten(), minlength=256).astype(np.float64)
    p    = hist / hist.sum()
    p    = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def compute_correlation(img: np.ndarray, direction: str = "horizontal") -> float:
    """Korelasi piksel bertetangga (Pearson). Ideal ≈ 0.0."""
    if img.ndim == 3:
        corr_sum = 0.0
        for i in range(3):
            c = img[:, :, i].astype(np.float64)
            if direction == "horizontal":
                x, y = c[:, :-1].ravel(), c[:, 1:].ravel()
            elif direction == "vertical":
                x, y = c[:-1, :].ravel(), c[1:, :].ravel()
            elif direction == "diagonal":
                x, y = c[:-1, :-1].ravel(), c[1:, 1:].ravel()
            else:
                raise ValueError("direction: 'horizontal' | 'vertical' | 'diagonal'")
            
            # Mencegah peringatan pembagian dengan nol jika array konstan
            if np.std(x) == 0 or np.std(y) == 0:
                corr_sum += 0.0
            else:
                corr_sum += float(np.corrcoef(x, y)[0, 1])
        return corr_sum / 3.0
    else:
        g = img.astype(np.float64)
        if direction == "horizontal":
            x, y = g[:, :-1].ravel(), g[:, 1:].ravel()
        elif direction == "vertical":
            x, y = g[:-1, :].ravel(), g[1:, :].ravel()
        elif direction == "diagonal":
            x, y = g[:-1, :-1].ravel(), g[1:, 1:].ravel()
        else:
            raise ValueError("direction: 'horizontal' | 'vertical' | 'diagonal'")
            
        if np.std(x) == 0 or np.std(y) == 0:
            return 0.0
        return float(np.corrcoef(x, y)[0, 1])


def compute_mse(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2))


def compute_psnr(original: np.ndarray, other: np.ndarray) -> float:
    mse = compute_mse(original, other)
    return float("inf") if mse == 0 else float(10 * np.log10(255.0**2 / mse))


def calculate_psnr_mse(a: np.ndarray, b: np.ndarray):
    """Alias untuk kompatibilitas: return (psnr, mse)."""
    mse  = compute_mse(a, b)
    psnr = float("inf") if mse == 0 else float(10 * np.log10(255.0**2 / mse))
    return psnr, mse


def compute_npcr(a: np.ndarray, b: np.ndarray) -> float:
    """NPCR (%) — ideal ≥ 99.6%"""
    return float(np.count_nonzero(a.astype(np.int16) - b.astype(np.int16)) / a.size * 100)


def compute_uaci(a: np.ndarray, b: np.ndarray) -> float:
    """UACI (%) — ideal ≈ 33.46%"""
    return float(np.mean(np.abs(a.astype(np.float64) - b.astype(np.float64)) / 255) * 100)


def compute_chi_square(img: np.ndarray, alpha: float = 0.05) -> dict:
    """
    Chi-square test terhadap distribusi seragam.
    Dibandingkan dengan nilai kritis dari tabel χ².
    df = 255, α = 0.05 → χ²_kritis ≈ 293.25

    Return dict dengan nilai χ², nilai kritis, dan kesimpulan.
    """
    hist     = np.bincount(img.flatten(), minlength=256).astype(np.float64)
    expected = img.size / 256.0
    chi2_val = float(np.sum((hist - expected) ** 2 / expected))

    # Nilai kritis Chi-square (df=255, α=0.05)
    chi2_critical = scipy_stats.chi2.ppf(1 - alpha, df=255)
    is_uniform    = chi2_val < chi2_critical

    return {
        "chi2_value":    chi2_val,
        "chi2_critical": chi2_critical,
        "df":            255,
        "alpha":         alpha,
        "is_uniform":    is_uniform,
        "conclusion":    "Distribusi SERAGAM (enkripsi baik)" if is_uniform
                         else "Distribusi TIDAK seragam",
    }


# ─── Re-import untuk Backward Compatibility ───────────────────────────────────
# Fungsi-fungsi di bawah telah dipindah ke modul terpisah.
# Re-import ini memastikan kode lama yang mengimport dari analysis
# tetap berfungsi tanpa perubahan.

from lyapunov import compute_lyapunov_exponent, plot_lyapunov_exponent      # noqa: E402
from bifurcation import compute_bifurcation_data, plot_bifurcation_diagram   # noqa: E402
from nist_tests import (                                                      # noqa: E402
    nist_frequency_monobit_test,
    nist_block_frequency_test,
    nist_runs_test,
    nist_longest_run_test,
    nist_matrix_rank_test,
    nist_dft_test,
    nist_non_overlapping_template_test,
    nist_overlapping_template_test,
    nist_universal_test,
    nist_linear_complexity_test,
    nist_serial_test,
    nist_approximate_entropy_test,
    nist_cumulative_sums_test,
    nist_random_excursions_test,
    nist_random_excursions_variant_test,
    run_nist_tests,
)
from histogram_plot import plot_histogram_comparison, plot_image_comparison   # noqa: E402
from scatter_plot import plot_keystream_scatter, plot_correlation_scatter     # noqa: E402


# ─── MODUL BARU: Sensitivitas Kunci (Ill Condition) ─────────────────────────

def key_sensitivity_analysis(base_params: dict, n_show: int = 10) -> dict:
    """
    Uji Ill Condition / Sensitivitas Kunci:
    Bandingkan key stream untuk X0=0.3, X0=0.3001, X0=0.30001.
    Tampilkan tabel iterasi 1–10 dan 200–209 (sesuai disertasi).

    Juga hitung persentase perbedaan bit.
    """
    from chaos_map import generate_chaos_sequence

    x0_values = [0.3, 0.3001, 0.30001]
    seqs = {}
    for x0 in x0_values:
        p = dict(base_params)
        p["x0"] = x0
        # Generate cukup panjang untuk lihat iterasi 1–10 dan 200–209
        p["skip"] = 0  # jangan skip dulu agar bisa lihat iterasi awal
        seqs[x0] = generate_chaos_sequence(210, p)

    # Tabel iterasi 1–10
    table_early = {}
    for x0 in x0_values:
        table_early[x0] = seqs[x0][:10].tolist()

    # Tabel iterasi 200–209
    table_late = {}
    for x0 in x0_values:
        table_late[x0] = seqs[x0][200:210].tolist()

    # Persentase perbedaan bit antara X0=0.3 vs X0=0.3001
    p_base = dict(base_params)
    p_diff = dict(base_params); p_diff["x0"] = 0.3001
    from chaos_map import generate_keystream
    k1 = generate_keystream((1000,), p_base).flatten()
    k2 = generate_keystream((1000,), p_diff).flatten()

    bits1 = np.unpackbits(k1)
    bits2 = np.unpackbits(k2)
    diff_pct = float(np.mean(bits1 != bits2) * 100)

    return {
        "table_iter_1_10":   table_early,
        "table_iter_200_209": table_late,
        "bit_diff_pct":      diff_pct,
        "x0_values":         x0_values,
    }


def print_sensitivity_table(result: dict) -> None:
    """Cetak tabel sensitivitas kunci ke konsol."""
    x0s = result["x0_values"]
    print("\n" + "=" * 72)
    print("  UJI SENSITIVITAS KUNCI (ILL CONDITION)")
    print("=" * 72)

    for label, table in [("Iterasi 1–10", result["table_iter_1_10"]),
                          ("Iterasi 200–209", result["table_iter_200_209"])]:
        print(f"\n  {label}:")
        header = f"  {'Iter':>6} | " + " | ".join(f"X0={x0}" for x0 in x0s)
        print(header)
        print("  " + "-" * (len(header) - 2))
        for i in range(10):
            row = f"  {i+1:>6} | " + " | ".join(f"{table[x0][i]:.8f}" for x0 in x0s)
            print(row)

    print(f"\n  Perbedaan bit (X0=0.3 vs X0=0.3001): {result['bit_diff_pct']:.2f}%")
    print("  (Ideal: ~50% — perubahan kecil menghasilkan key yang sama sekali berbeda)")
    print("=" * 72)


# ─── MODUL BARU: Key Space Analysis ─────────────────────────────────────────

def compute_key_space(params: dict, precision: float = 1e-15) -> dict:
    """
    Analisis ruang kunci (Key Space Analysis).
    Hitung jumlah kombinasi parameter yang mungkin.

    Sensitivitas kunci: perubahan terkecil yang masih terdeteksi (default 10^-15).
    Disertasi: Key Space = 1.8×10^94
    """
    # Parameter kunci: X0, r, α, β, λ (masing-masing presisi float64 ~15 digit)
    param_ranges = {
        "x0":    (0.0, 1.0),
        "r":     (3.1, 4.0),
        "alpha": (3.1, 8.0),
        "beta":  (3.1, 5.0),
        "lam":   (3.5, 5.0),
    }

    total_combinations = 1
    details = {}
    for pname, (lo, hi) in param_ranges.items():
        n_values = int((hi - lo) / precision)
        total_combinations *= n_values
        details[pname] = {
            "range":    (lo, hi),
            "n_values": n_values,
        }

    return {
        "key_space":   total_combinations,
        "key_space_exp": math.log10(total_combinations) if total_combinations > 0 else 0,
        "precision":   precision,
        "details":     details,
    }


# ─── Full Analysis ────────────────────────────────────────────────────────────

def _crop_to(img: np.ndarray, ref: np.ndarray) -> np.ndarray:
    H, W = ref.shape[:2]
    if img.shape[:2] == (H, W):
        return img
    if img.ndim == 2:
        return img[:H, :W]
    return img[:H, :W, :]


def full_analysis(
    original: np.ndarray,
    encrypted: np.ndarray,
    decrypted: np.ndarray,
) -> dict:
    """Hitung semua metrik analisis enkripsi."""
    enc_cropped = _crop_to(encrypted, original)
    chi2_result = compute_chi_square(encrypted)
    
    # Chi-Square per channel
    chi2_r, chi2_g, chi2_b = chi2_result["chi2_value"], chi2_result["chi2_value"], chi2_result["chi2_value"]
    if len(encrypted.shape) == 3 and encrypted.shape[2] == 3:
        import cv2
        b_ch, g_ch, r_ch = cv2.split(encrypted)
        chi2_r = compute_chi_square(r_ch)["chi2_value"]
        chi2_g = compute_chi_square(g_ch)["chi2_value"]
        chi2_b = compute_chi_square(b_ch)["chi2_value"]

    return {
        "entropy_original":   compute_entropy(original),
        "entropy_encrypted":  compute_entropy(encrypted),
        "entropy_decrypted":  compute_entropy(decrypted),

        "corr_orig_H":  compute_correlation(original,  "horizontal"),
        "corr_orig_V":  compute_correlation(original,  "vertical"),
        "corr_orig_D":  compute_correlation(original,  "diagonal"),
        "corr_enc_H":   compute_correlation(encrypted, "horizontal"),
        "corr_enc_V":   compute_correlation(encrypted, "vertical"),
        "corr_enc_D":   compute_correlation(encrypted, "diagonal"),

        "mse_orig_enc":  compute_mse(original, enc_cropped),
        "psnr_orig_enc": compute_psnr(original, enc_cropped),
        "mse_orig_dec":  compute_mse(original, decrypted),
        "psnr_orig_dec": compute_psnr(original, decrypted),

        "npcr":          compute_npcr(original, enc_cropped),
        "uaci":          compute_uaci(original, enc_cropped),
        
        "chi2_value":    chi2_result["chi2_value"],
        "chi2_critical": chi2_result["chi2_critical"],
        "chi2_uniform":  chi2_result["is_uniform"],
        "chi2_r":        chi2_r,
        "chi2_g":        chi2_g,
        "chi2_b":        chi2_b,
    }


def print_metrics(m: dict) -> None:
    sep = "-" * 60
    print(f"\n{sep}")
    print("  HASIL ANALISIS ENKRIPSI CITRA")
    print(sep)
    print(f"  Entropy  Original   : {m['entropy_original']:.6f} bit")
    print(f"  Entropy  Encrypted  : {m['entropy_encrypted']:.6f} bit  (ideal ~8.0)")
    print(f"  Entropy  Decrypted  : {m['entropy_decrypted']:.6f} bit")
    print(sep)
    print(f"  Korelasi Original   H/V/D : {m['corr_orig_H']:+.6f} / {m['corr_orig_V']:+.6f} / {m['corr_orig_D']:+.6f}")
    print(f"  Korelasi Encrypted  H/V/D : {m['corr_enc_H']:+.6f} / {m['corr_enc_V']:+.6f} / {m['corr_enc_D']:+.6f}  (ideal ~0)")
    print(sep)
    print(f"  MSE  (orig<->enc)   : {m['mse_orig_enc']:.4f}")
    print(f"  PSNR (orig<->enc)   : {m['psnr_orig_enc']:.4f} dB")
    print(f"  MSE  (orig<->dec)   : {m['mse_orig_dec']:.4f}  (ideal = 0)")
    psnr_dec = m['psnr_orig_dec']
    psnr_str = "inf" if psnr_dec == float('inf') else f"{psnr_dec:.4f} dB"
    print(f"  PSNR (orig<->dec)   : {psnr_str}  (ideal = inf)")
    print(sep)
    print(f"  NPCR                : {m['npcr']:.4f}%  (ideal >= 99.6%)")
    print(f"  UACI                : {m['uaci']:.4f}%  (ideal ~33.46%)")
    print(sep)
    uniform_str = "YA ✓" if m['chi2_uniform'] else "TIDAK ✗"
    print(f"  Chi2 Encrypted      : {m['chi2_value']:.2f}  (kritis: {m['chi2_critical']:.2f})")
    print(f"  Distribusi Seragam  : {uniform_str}")
    print(sep)


def save_metrics_csv(metrics_list: list, path: str) -> None:
    if not metrics_list:
        return
    keys = list(metrics_list[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filename"] + keys)
        writer.writeheader()
        writer.writerows(metrics_list)
    print(f"[OK] Metrics CSV -> {path}")


# ─── Visualisasi Standar ──────────────────────────────────────────────────────

def _to_rgb(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if img.ndim == 3 else img


def plot_image_comparison(original, encrypted, decrypted, save_path=None) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Perbandingan Citra", fontsize=14, fontweight="bold")
    for ax, img, title in zip(axes,
                               [original, encrypted, decrypted],
                               ["Original", "Encrypted", "Decrypted"]):
        ax.imshow(_to_rgb(img), cmap="gray" if img.ndim == 2 else None)
        ax.set_title(title); ax.axis("off")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[OK] Comparison -> {save_path}")
    plt.show()


def plot_histogram_comparison(original, encrypted, decrypted, save_path=None) -> None:
    imgs   = [original, encrypted, decrypted]
    titles = ["Original", "Encrypted", "Decrypted"]
    colors = ["steelblue", "crimson", "seagreen"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle("Histogram Perbandingan", fontsize=14, fontweight="bold")
    for ax, img, title, color in zip(axes, imgs, titles, colors):
        ax.hist(_gray(img).flatten(), bins=256, range=(0, 256),
                color=color, alpha=0.85, edgecolor="none")
        ax.set_title(title)
        ax.set_xlabel("Intensitas"); ax.set_ylabel("Frekuensi")
        ax.set_xlim([0, 255])
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[OK] Histogram -> {save_path}")
    plt.show()


def plot_correlation_scatter(
    original: np.ndarray,
    encrypted: np.ndarray,
    direction: str = "horizontal",
    n_samples: int = 3000,
    save_path: str = None,
) -> None:
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
        ax.set_xlabel("Piksel ke-i"); ax.set_ylabel("Piksel ke-i+1")
        ax.set_xlim([0, 255]); ax.set_ylim([0, 255])
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[OK] Scatter plot -> {save_path}")
    plt.show()
