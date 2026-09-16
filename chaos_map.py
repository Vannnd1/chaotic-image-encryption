"""
chaos_map.py — Kernel Matematika Peta Kaos (Chaotic Map Engine)
================================================================
File ini adalah inti matematis dari sistem enkripsi. Berisi semua
rumus dan kernel iterasi peta kaos yang menghasilkan barisan bilangan
kaotik sebagai dasar pembangkitan kunci enkripsi.

TANGGUNG JAWAB FILE INI:
  1. Mendefinisikan rumus iterasi 5 algoritma peta kaos
  2. Mengeksekusi iterasi peta kaos (kernel Numba/NumPy)
  3. Menyediakan konstanta nama algoritma dan parameter default

ALGORITMA YANG TERSEDIA:
  1. MS Map (mandiri)
       → Peta kaos berbasis fungsi sinus termodifikasi
       → Rumus: f(x) = [ r·λ·x / (1 + λ·(1 - x)²) ] mod 1

  2. Gauss Map (mandiri)
       → Peta kaos berbasis fungsi eksponensial Gauss
       → Rumus: g(x) = exp(-α·x²) + β   (tanpa mod 1)

  3. Gauss MS Map — komposisi (g∘f)(x)  [ALGO UTAMA]
       → Gauss Map bekerja di LUAR, MS Map di dalam
       → Rumus: h(x) = [ exp(-α·(f(x))²) + β ] mod 1

  4. MS Gauss Map — komposisi (f∘g)(x)
       → MS Map bekerja di LUAR, Gauss Map di dalam
       → Rumus: h(x) = [ r·λ·g(x) / (1 + λ·(1-g(x))²) ] mod 1

  5. MS Map + Gauss Map (Sequential / Berlapis)
       → Dua keystream digabung: C = (P ⊕ K1) ⊕ K2
       → K1 dari MS Map, K2 dari Gauss Map

PARAMETER DEFAULT (sesuai referensi disertasi):
  X0=0.3, r=3.5, α=5.8, β=2.5, λ=3.5, skip=200 (iterasi awal dibuang)

CATATAN TEKNIS:
  - Menggunakan Numba JIT (jika tersedia) untuk percepatan komputasi
  - Jika Numba tidak ada, otomatis pakai NumPy biasa sebagai fallback
  - HANYA MS Map yang menggunakan mod 1; Gauss Map mandiri tidak
  - Pembangkitan keystream byte (uint8) ada di keystream_generator.py
"""

import numpy as np

# ─── Deteksi Numba (sekali saja di level modul) ───────────────────────────────
try:
    from numba import njit as _njit
    _NUMBA_OK = True
except ImportError:  # pragma: no cover
    _NUMBA_OK = False
    def _njit(*args, **kwargs):  # dummy decorator
        def _wrap(fn): return fn
        return _wrap


# ─── Parameter Default ────────────────────────────────────────────────────────

DEFAULT_PARAMS = {
    "r":       3.5,
    "lam":     3.5,
    "alpha":   5.8,
    "beta":    2.5,
    "x0":      0.3,
    "skip":    200,

}


# ─── Helper Ekstrak Parameter ─────────────────────────────────────────────────

def _extract_params(params: dict) -> tuple:
    """Ekstrak 5 parameter chaos dari dict (dengan fallback ke DEFAULT_PARAMS).
    Return: (x0, r, lam, alpha, beta, skip)
    """
    p = params or DEFAULT_PARAMS
    return (
        float(p.get("x0",    DEFAULT_PARAMS["x0"])),
        float(p.get("r",     DEFAULT_PARAMS["r"])),
        float(p.get("lam",   DEFAULT_PARAMS["lam"])),
        float(p.get("alpha", DEFAULT_PARAMS["alpha"])),
        float(p.get("beta",  DEFAULT_PARAMS["beta"])),
        int(p.get("skip",    DEFAULT_PARAMS["skip"])),
    )

ALGO_MS_GAUSS     = "Gauss MS Map"    # g∘f = g(f(x)) → Gauss OUTER, MS inner
ALGO_MS_MAP       = "MS Map"
ALGO_GAUSS_MAP    = "Gauss Map"
ALGO_SEQUENTIAL   = "MS Map + Gauss Map"
ALGO_MS_GAUSS_FOG = "MS Gauss Map"    # f∘g = f(g(x)) → MS OUTER, Gauss inner


# ─── MS Map (mandiri) ─────────────────────────────────────────────────────────

# ─── JIT-compiled kernel (dikompilasi Numba sekali saat pertama dipanggil) ────

@_njit(cache=True)
def _kernel_ms(x: float, n: int, r: float, lam: float) -> np.ndarray:
    """Kernel iterasi MS Map."""
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        xn1 = (r * lam * x) / (1.0 + lam * (1.0 - x) ** 2) % 1.0
        if xn1 <= 0.0: xn1 = 1e-10
        if xn1 >= 1.0: xn1 = 1.0 - 1e-10
        x = xn1
        out[i] = x
    return out


@_njit(cache=True)
def _kernel_gauss(x: float, n: int, alpha: float, beta: float) -> np.ndarray:
    """Kernel iterasi Gauss Map (dengan mod 1 agar berada dalam domain chaotic [0, 1))."""
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        xn1 = (np.exp(-alpha * x * x) + beta) % 1.0
        if xn1 <= 0.0: xn1 = 1e-10
        if xn1 >= 1.0: xn1 = 1.0 - 1e-10
        x = xn1
        out[i] = x
    return out


@_njit(cache=True)
def _kernel_msgauss_gof(x: float, n: int, r: float, lam: float,
                        alpha: float, beta: float) -> np.ndarray:
    """Kernel MS Gauss Map komposisi (g∘f).
    f(x) = MS Map (mod 1).
    Gauss Map mandiri tidak pakai mod 1, tapi hasil fusi g(f(x)) pakai mod 1
    karena komposisi ini membentuk peta baru yang outputnya harus di [0,1).
    """
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        f_x = (r * lam * x / (1.0 + lam * (1.0 - x) ** 2)) % 1.0  # MS Map → mod 1
        if f_x <= 0.0: f_x = 1e-10
        if f_x >= 1.0: f_x = 1.0 - 1e-10
        xn1 = (np.exp(-alpha * f_x * f_x) + beta) % 1.0            # output fusi → mod 1
        if xn1 <= 0.0: xn1 = 1e-10
        if xn1 >= 1.0: xn1 = 1.0 - 1e-10
        x = xn1
        out[i] = x
    return out


@_njit(cache=True)
def _kernel_msgauss_fog(x: float, n: int, r: float, lam: float,
                        alpha: float, beta: float) -> np.ndarray:
    """Kernel MS Gauss Map komposisi (f∘g) sesuai rumus jurnal/skripsi:
    g(x) = exp(-alpha*x^2) + beta
    f(g(x)) = [ r*lam*g(x) / (1 + lam*(1 - g(x))^2) ] mod 1
    """
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        g_x = np.exp(-alpha * x * x) + beta
        xn1 = (r * lam * g_x / (1.0 + lam * (1.0 - g_x) ** 2)) % 1.0
        if xn1 <= 0.0: xn1 = 1e-10
        if xn1 >= 1.0: xn1 = 1.0 - 1e-10
        x = xn1
        out[i] = x
    return out


# ─── Fallback NumPy (dipakai jika Numba tidak tersedia) ──────────────────────

def _fallback_ms(x0: float, n: int, r: float, lam: float) -> np.ndarray:
    seq = np.empty(n, dtype=np.float64)
    x = x0
    for i in range(n):
        xn1 = (r * lam * x) / (1.0 + lam * (1.0 - x) ** 2)
        x = float(np.clip(xn1 % 1.0, 1e-10, 1.0 - 1e-10))
        seq[i] = x
    return seq


def _fallback_gauss(x0: float, n: int, alpha: float, beta: float) -> np.ndarray:
    """Gauss Map fallback (dengan mod 1 agar berada dalam domain chaotic [0, 1))."""
    seq = np.empty(n, dtype=np.float64)
    x = x0
    for i in range(n):
        xn1 = (np.exp(-alpha * x * x) + beta) % 1.0
        x = float(np.clip(xn1, 1e-10, 1.0 - 1e-10))
        seq[i] = x
    return seq


def _fallback_msgauss_gof(x0: float, n: int, r: float, lam: float,
                          alpha: float, beta: float) -> np.ndarray:
    """MS Gauss Map (g∘f) fallback.
    f(x): MS Map → mod 1. g(f(x)): output fusi → mod 1.
    (Gauss mandiri tidak mod 1, tapi hasil fusi pakai mod 1.)
    """
    seq = np.empty(n, dtype=np.float64)
    x = x0
    for i in range(n):
        f_x = float(np.clip((r * lam * x / (1.0 + lam * (1.0 - x) ** 2)) % 1.0, 1e-10, 1.0 - 1e-10))  # MS Map → mod 1
        xn1 = (np.exp(-alpha * f_x * f_x) + beta) % 1.0                                                 # output fusi → mod 1
        x = float(np.clip(xn1, 1e-10, 1.0 - 1e-10))
        seq[i] = x
    return seq


def _fallback_msgauss_fog(x0: float, n: int, r: float, lam: float,
                          alpha: float, beta: float) -> np.ndarray:
    """MS Gauss Map (f∘g) fallback sesuai rumus jurnal/skripsi:
    g(x) = exp(-alpha*x^2) + beta
    f(g(x)) = [ r*lam*g(x) / (1 + lam*(1 - g(x))^2) ] mod 1
    """
    seq = np.empty(n, dtype=np.float64)
    x = x0
    for i in range(n):
        g_x = np.exp(-alpha * x * x) + beta
        xn1 = (r * lam * g_x / (1.0 + lam * (1.0 - g_x) ** 2)) % 1.0
        x = float(np.clip(xn1, 1e-10, 1.0 - 1e-10))
        seq[i] = x
    return seq


# ─── Public API — fungsi iterasi (otomatis pakai Numba atau NumPy) ─────────────

def _iterate_ms_map(x0: float, n: int, r, lam) -> np.ndarray:
    """
    MS Map mandiri:
        X(n+1) = [ r·λ·Xn / (1 + λ·(1 - Xn)²) ] mod 1
    """
    x0, r, lam = float(x0), float(r), float(lam)
    if _NUMBA_OK:
        return _kernel_ms(x0, n, r, lam)
    return _fallback_ms(x0, n, r, lam)


# ─── Gauss Map (mandiri) ──────────────────────────────────────────────────────

def _iterate_gauss_map(x0: float, n: int, alpha, beta) -> np.ndarray:
    """
    Gauss Map mandiri:
        X(n+1) = [ exp(-α·Xn²) + β ] mod 1
    """
    x0, alpha, beta = float(x0), float(alpha), float(beta)
    if _NUMBA_OK:
        return _kernel_gauss(x0, n, alpha, beta)
    return _fallback_gauss(x0, n, alpha, beta)



def _iterate_ms_gauss_gof(x0: float, n: int, r, lam, alpha, beta) -> np.ndarray:
    """
    MS Gauss Map sebagai komposisi (g∘f)(x)
        X(n+1) = g(f(Xn))  di mana f = MS Map, g = Gauss Map
    """
    x0, r, lam, alpha, beta = float(x0), float(r), float(lam), float(alpha), float(beta)
    if _NUMBA_OK:
        return _kernel_msgauss_gof(x0, n, r, lam, alpha, beta)
    return _fallback_msgauss_gof(x0, n, r, lam, alpha, beta)


# ─── MS Gauss Map (f∘g) — komposisi Gauss→MS ────────────────────────────────

def _iterate_ms_gauss_fog(x0: float, n: int, r, lam, alpha, beta) -> np.ndarray:
    """
    MS Gauss Map sebagai komposisi (f∘g)(x)
        X(n+1) = f(g(Xn))  di mana g = Gauss Map (dalam), f = MS Map (luar)
    """
    x0, r, lam, alpha, beta = float(x0), float(r), float(lam), float(alpha), float(beta)
    if _NUMBA_OK:
        return _kernel_msgauss_fog(x0, n, r, lam, alpha, beta)
    return _fallback_msgauss_fog(x0, n, r, lam, alpha, beta)


# ─── Re-import untuk Backward Compatibility ───────────────────────────────────
# Fungsi pembangkit keystream telah dipindah ke keystream_generator.py.
# Re-import di bawah memastikan kode lama yang mengimport dari chaos_map
# tetap berfungsi tanpa perubahan.

try:
    from keystream_generator import (       # noqa: E402
        generate_chaos_sequence,
        generate_keystream,
        generate_keystream_sequential,
    )
except ImportError:
    pass
