"""
encryption.py — Pipeline Enkripsi Citra Digital
=================================================
File ini mengatur alur (pipeline) proses enkripsi gambar dari awal hingga akhir.
Bertugas menggabungkan semua komponen: pembangkitan kunci + XOR.

FUNGSI UTAMA FILE INI:
  1. Menerima gambar asli sebagai input
  2. Membangkitkan keystream dari peta kaos pilihan (via chaos_map.py)
  3. Mengenkripsi gambar dengan operasi XOR antara piksel dan keystream
  4. Mengembalikan gambar terenkripsi beserta informasi metadata

PIPELINE ENKRIPSI (urutan tahapan):
  [Gambar Asli]
      ↓  Difusi XOR dengan keystream peta kaos
  [Gambar Terenkripsi]

MODE ENKRIPSI YANG DIDUKUNG:
  1. MS Map          → XOR dengan 1 keystream dari MS Map
  2. Gauss Map       → XOR dengan 1 keystream dari Gauss Map
  3. Gauss MS Map    → XOR dengan 1 keystream dari komposisi (g∘f)
  4. MS Gauss Map    → XOR dengan 1 keystream dari komposisi (f∘g)
  5. Sequential      → XOR berlapis dua keystream:
                         C1 = P  ⊕ K1  (K1 dari MS Map)
                         C  = C1 ⊕ K2  (K2 dari Gauss Map)

CATATAN:
  - File ini TIDAK memiliki rumus kaos sendiri; semua kunci diambil dari chaos_map.py
  - Fungsi encrypt_image() adalah fungsi utama yang dipanggil oleh GUI
"""

import numpy as np
import cv2
from chaos_map import (
    DEFAULT_PARAMS,
    ALGO_MS_GAUSS, ALGO_MS_MAP, ALGO_GAUSS_MAP, ALGO_SEQUENTIAL, ALGO_MS_GAUSS_FOG,
)
from keystream_generator import generate_keystream, generate_keystream_sequential



def validate_image(img: np.ndarray) -> np.ndarray:
    """Validasi dan pastikan dtype uint8."""
    if img is None or not isinstance(img, np.ndarray):
        raise TypeError("Input harus numpy.ndarray yang valid.")
    if img.ndim not in (2, 3):
        raise ValueError("Gambar harus 2D (grayscale) atau 3D (BGR/RGB).")
    return img.astype(np.uint8)





def encrypt_image(img: np.ndarray, params: dict = None,
                  algo: str = ALGO_MS_GAUSS) -> tuple:
    """
    Enkripsi citra.

    Parameters
    ----------
    img    : numpy.ndarray — citra asli
    params : dict          — parameter chaos
    algo   : str           — pilihan algoritma:
                             'MS Gauss Map', 'MS Map', 'Gauss Map',
                             'MS Map + Gauss Map'

    Returns
    -------
    encrypted : np.ndarray uint8
    meta      : dict (params + orig_shape + algo)
    """
    img = validate_image(img)
    if params is None:
        params = DEFAULT_PARAMS

    orig_shape = img.shape

    # XOR Diffusion sesuai algoritma
    if algo == ALGO_SEQUENTIAL:
        # Sequential: C1 = P ⊕ K1 (MS Map), C = C1 ⊕ K2 (Gauss Map)
        k1, k2 = generate_keystream_sequential(img.shape, params)
        c1 = (img.astype(np.uint16) ^ k1.astype(np.uint16)).astype(np.uint8)
        encrypted = (c1.astype(np.uint16) ^ k2.astype(np.uint16)).astype(np.uint8)
    else:
        # MS Map / Gauss Map / MS Gauss Map — satu keystream
        keystream = generate_keystream(img.shape, params, algo)
        encrypted = (img.astype(np.uint16) ^ keystream.astype(np.uint16)).astype(np.uint8)

    meta = dict(params)
    meta["orig_shape"] = orig_shape
    meta["algo"]       = algo
    return encrypted.astype(np.uint8), meta


def encrypt_from_file(filepath: str, params: dict = None,
                       algo: str = ALGO_MS_GAUSS,
                       as_grayscale: bool = False) -> tuple:
    """Baca file lalu enkripsi. Return (original, encrypted, meta)."""
    flag = cv2.IMREAD_GRAYSCALE if as_grayscale else cv2.IMREAD_COLOR
    img  = cv2.imread(filepath, flag)
    if img is None:
        raise FileNotFoundError(f"File tidak ditemukan: {filepath}")
    enc, meta = encrypt_image(img, params, algo)
    return img, enc, meta


def save_encrypted(encrypted: np.ndarray, path: str) -> None:
    if not cv2.imwrite(path, encrypted):
        raise IOError(f"Gagal menyimpan: {path}")
    print(f"[OK] Encrypted -> {path}")
