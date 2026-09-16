"""
keystream_generator.py — Pembangkit Keystream dari Peta Kaos
=============================================================
File ini bertanggung jawab mengubah barisan bilangan kaotik (chaos sequence)
yang dihasilkan oleh peta kaos menjadi keystream byte (uint8) yang siap
digunakan untuk operasi XOR pada proses enkripsi/dekripsi.

FUNGSI UTAMA FILE INI:
  1. Membangkitkan barisan kaotik (chaos sequence) menggunakan algoritma
     peta kaos yang dipilih
  2. Mengubah barisan kaotik menjadi keystream byte (0–255)
  3. Mendukung mode Sequential (dua keystream berlapis: K1 dari MS Map,
     K2 dari Gauss Map)

FORMULA KONVERSI KEYSTREAM:
  Kk = floor(Xk × 10⁶) mod 256   →   menghasilkan byte 0–255

ALGORITMA YANG DIDUKUNG:
  - MS Map          (ALGO_MS_MAP)
  - Gauss Map       (ALGO_GAUSS_MAP)
  - Gauss MS Map    (ALGO_MS_GAUSS)      ← komposisi g∘f, algoritma utama
  - MS Gauss Map    (ALGO_MS_GAUSS_FOG) ← komposisi f∘g
  - Sequential      (ALGO_SEQUENTIAL)   ← MS Map + Gauss Map berlapis

CATATAN:
  - Kernel iterasi peta kaos berada di chaos_map.py
  - File ini hanya menangani logika pembangkitan dan konversi ke byte
"""

import numpy as np
from chaos_map import (
    _extract_params,
    _iterate_ms_map,
    _iterate_gauss_map,
    _iterate_ms_gauss_gof,
    _iterate_ms_gauss_fog,
    DEFAULT_PARAMS,
    ALGO_MS_GAUSS,
    ALGO_MS_MAP,
    ALGO_GAUSS_MAP,
    ALGO_SEQUENTIAL,
    ALGO_MS_GAUSS_FOG,
)


# ─── Pembangkit Barisan Kaotik ────────────────────────────────────────────────

def generate_chaos_sequence(n: int, params: dict = None,
                             algo: str = ALGO_MS_GAUSS) -> np.ndarray:
    """
    Bangkitkan barisan kaotik sepanjang n setelah membuang transient awal (skip).

    Routing algoritma:
      ALGO_MS_MAP       → MS Map mandiri
      ALGO_GAUSS_MAP    → Gauss Map mandiri
      ALGO_MS_GAUSS_FOG → MS Gauss Map  = f∘g = f(g(x)), MS OUTER
      ALGO_MS_GAUSS     → Gauss MS Map  = g∘f = g(f(x)), Gauss OUTER

    Parameters
    ----------
    n      : int  — panjang barisan yang diinginkan (setelah skip)
    params : dict — parameter kaos (x0, r, lam, alpha, beta, skip)
    algo   : str  — nama algoritma peta kaos

    Returns
    -------
    seq : np.ndarray float64, panjang n, nilai di (0, 1)
    """
    x0, r, lam, alpha, beta, skip = _extract_params(params)
    total = n + skip

    if algo == ALGO_MS_MAP:
        raw = _iterate_ms_map(x0, total, r, lam)
    elif algo == ALGO_GAUSS_MAP:
        raw = _iterate_gauss_map(x0, total, alpha, beta)
    elif algo == ALGO_MS_GAUSS_FOG:           # MS Gauss Map  — f(g(x)), fog
        raw = _iterate_ms_gauss_fog(x0, total, r, lam, alpha, beta)
    else:                                     # Gauss MS Map  — g(f(x)), gof (default)
        raw = _iterate_ms_gauss_gof(x0, total, r, lam, alpha, beta)

    return raw[skip:]


# ─── Pembangkit Keystream (Single) ───────────────────────────────────────────

def generate_keystream(shape: tuple, params: dict = None,
                        algo: str = ALGO_MS_GAUSS) -> np.ndarray:
    """
    Bangkitkan keystream uint8 dengan formula: Kk = floor(Xk × 10⁶) mod 256

    Untuk semua algoritma kecuali Sequential, hasilkan satu keystream.
    Mode Sequential dikelola oleh generate_keystream_sequential().

    Parameters
    ----------
    shape  : tuple — bentuk array keystream (harus sama dengan shape gambar)
    params : dict  — parameter kaos
    algo   : str   — nama algoritma peta kaos

    Returns
    -------
    key : np.ndarray uint8, shape == shape
    """
    if params is None:
        params = DEFAULT_PARAMS

    n   = int(np.prod(shape))
    seq = generate_chaos_sequence(n, params, algo)
    key = (np.floor(seq * 1_000_000).astype(np.int64) % 256).astype(np.uint8)
    return key.reshape(shape)


# ─── Pembangkit Keystream Sequential (Dua Lapis) ─────────────────────────────

def generate_keystream_sequential(shape: tuple, params: dict = None) -> tuple:
    """
    Bangkitkan DUA keystream untuk mode Sequential (MS Map + Gauss Map):
        K1 dari MS Map
        K2 dari Gauss Map
    Digunakan untuk enkripsi berlapis: C = (P ⊕ K1) ⊕ K2

    Parameters
    ----------
    shape  : tuple — bentuk array keystream (sama dengan shape gambar)
    params : dict  — parameter kaos

    Returns
    -------
    (K1, K2) : tuple of np.ndarray uint8, keduanya shape == shape
    """
    x0, r, lam, alpha, beta, skip = _extract_params(params)
    n     = int(np.prod(shape))
    total = n + skip

    seq1 = _iterate_ms_map(x0, total, r, lam)[skip:]
    seq2 = _iterate_gauss_map(x0, total, alpha, beta)[skip:]

    k1 = (np.floor(seq1 * 1_000_000).astype(np.int64) % 256).astype(np.uint8).reshape(shape)
    k2 = (np.floor(seq2 * 1_000_000).astype(np.int64) % 256).astype(np.uint8).reshape(shape)
    return k1, k2
