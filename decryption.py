"""
decryption.py — Pipeline Dekripsi Citra Digital
=================================================
File ini adalah kebalikan dari encryption.py. Bertugas mengembalikan
gambar yang sudah terenkripsi ke bentuk aslinya (gambar semula).

FUNGSI UTAMA FILE INI:
  1. Menerima gambar terenkripsi dan metadata kunci sebagai input
  2. Membangkitkan ulang keystream yang SAMA persis seperti saat enkripsi
  3. Membuka lapisan XOR (inverse diffusion) sesuai algoritma yang dipakai
  4. Memotong (crop) gambar kembali ke ukuran asli

PIPELINE DEKRIPSI (urutan tahapan — KEBALIKAN dari enkripsi):
  [Gambar Terenkripsi]
      ↓  Inverse Difusi XOR (buka lapisan keystream)
  [Gambar Asli Kembali]

URUTAN BUKA LAPISAN SEQUENTIAL (MS Map + Gauss Map):
  C1 = C  ⊕ K2   → buka lapisan Gauss Map terlebih dahulu
  P  = C1 ⊕ K1   → buka lapisan MS Map

CATATAN:
  - Kunci HARUS identik dengan yang digunakan saat enkripsi
  - Jika kunci berbeda satu digit pun, gambar tidak akan bisa dipulihkan
"""

import numpy as np
import cv2
from chaos_map import (
    DEFAULT_PARAMS,
    ALGO_MS_GAUSS, ALGO_MS_MAP, ALGO_GAUSS_MAP, ALGO_SEQUENTIAL,
)
from keystream_generator import generate_keystream, generate_keystream_sequential
from encryption import validate_image



def decrypt_image(encrypted: np.ndarray, params: dict = None,
                  algo: str = ALGO_MS_GAUSS) -> np.ndarray:
    """
    Dekripsi citra.

    Parameters
    ----------
    encrypted : np.ndarray — citra terenkripsi
    params    : dict       — parameter chaos (sama saat enkripsi)
    algo      : str        — algoritma yang digunakan saat enkripsi

    Returns
    -------
    decrypted : np.ndarray uint8
    """
    encrypted = validate_image(encrypted)
    if params is None:
        params = DEFAULT_PARAMS

    # Ambil algo dari params jika tidak diberikan eksplisit
    if algo == ALGO_MS_GAUSS and "algo" in params:
        algo = params["algo"]

    orig_shape = params.get("orig_shape", None)

    # Stage 1: Inverse Diffusion
    if algo == ALGO_SEQUENTIAL:
        # Buka urutan terbalik: K2 dulu, lalu K1
        k1, k2 = generate_keystream_sequential(encrypted.shape, params)
        c1         = (encrypted.astype(np.uint16) ^ k2.astype(np.uint16)).astype(np.uint8)
        decrypted  = (c1.astype(np.uint16) ^ k1.astype(np.uint16)).astype(np.uint8)
    else:
        keystream  = generate_keystream(encrypted.shape, params, algo)
        decrypted  = (encrypted.astype(np.uint16) ^ keystream.astype(np.uint16)).astype(np.uint8)

    # Stage 2: Crop ke ukuran asli
    if orig_shape is not None:
        H, W = orig_shape[0], orig_shape[1]
        decrypted = decrypted[:H, :W] if decrypted.ndim == 2 else decrypted[:H, :W, :]

    return decrypted.astype(np.uint8)


def decrypt_from_file(filepath: str, params: dict = None,
                       algo: str = ALGO_MS_GAUSS,
                       as_grayscale: bool = False) -> tuple:
    """Baca file encrypted lalu dekripsi. Return (encrypted, decrypted)."""
    flag = cv2.IMREAD_GRAYSCALE if as_grayscale else cv2.IMREAD_COLOR
    enc  = cv2.imread(filepath, flag)
    if enc is None:
        raise FileNotFoundError(f"File tidak ditemukan: {filepath}")
    dec = decrypt_image(enc, params, algo)
    return enc, dec


def save_decrypted(decrypted: np.ndarray, path: str) -> None:
    if not cv2.imwrite(path, decrypted):
        raise IOError(f"Gagal menyimpan: {path}")
    print(f"[OK] Decrypted -> {path}")
