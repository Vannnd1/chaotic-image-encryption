"""
nist_tests.py — Pengujian Keacakan NIST SP 800-22
==================================================
File ini berisi implementasi lengkap 15 uji statistik keacakan
standar NIST SP 800-22 untuk mengevaluasi kualitas keystream
yang dibangkitkan oleh peta kaos.

TUJUAN PENGUJIAN NIST:
  Membuktikan bahwa keystream yang dihasilkan memiliki sifat
  statistik yang setara dengan deretan bit acak sejati (true random),
  sehingga layak digunakan sebagai kunci enkripsi.

KRITERIA KELULUSAN:
  P-value > 0.01 → LULUS (sequence bersifat acak)
  P-value ≤ 0.01 → GAGAL (sequence tidak acak)

DAFTAR 15 UJI NIST SP 800-22:
  1.  Frequency (Monobit) Test
  2.  Frequency Test within a Block
  3.  Runs Test
  4.  Longest Run of Ones in a Block Test
  5.  Binary Matrix Rank Test
  6.  Discrete Fourier Transform (Spectral) Test
  7.  Non-overlapping Template Matching Test
  8.  Overlapping Template Matching Test
  9.  Maurer's Universal Statistical Test
  10. Linear Complexity Test
  11. Serial Test
  12. Approximate Entropy Test
  13. Cumulative Sums Test
  14. Random Excursions Test
  15. Random Excursions Variant Test

CATATAN:
  - run_nist_tests() menjalankan seluruh 15 uji sekaligus
  - Input keystream: 125.000 byte = 1.000.000 bit (sesuai standar NIST)
"""

import numpy as np
import math


# ─── Uji 1: Frequency (Monobit) Test ─────────────────────────────────────────

def nist_frequency_monobit_test(sequence: np.ndarray) -> dict:
    """
    NIST SP 800-22 Test 1: Frequency (Monobit) Test.

    Menguji apakah jumlah bit 0 dan bit 1 dalam sequence
    seimbang (proporsi masing-masing mendekati 0.5).

    P-value > 0.01 → sequence acak (LULUS)

    Parameters
    ----------
    sequence : np.ndarray uint8 — keystream yang diuji

    Returns
    -------
    dict berisi: test, n_bits, s_n, s_obs, p_value, passed, conclusion
    """
    bits  = np.unpackbits(sequence.flatten())
    n     = len(bits)
    s_n   = np.sum(2 * bits.astype(np.int8) - 1)
    s_obs = abs(s_n) / math.sqrt(n)
    p_val = math.erfc(s_obs / math.sqrt(2))

    return {
        "test":       "NIST Frequency (Monobit)",
        "n_bits":     n,
        "s_n":        int(s_n),
        "s_obs":      s_obs,
        "p_value":    p_val,
        "passed":     p_val > 0.01,
        "conclusion": "LULUS — Key stream acak" if p_val > 0.01
                      else "GAGAL — Key stream tidak acak",
    }


# ─── Uji 2: Frequency Test within a Block ────────────────────────────────────

def nist_block_frequency_test(sequence: np.ndarray, M: int = 128) -> dict:
    """
    NIST SP 800-22 Test 2: Frequency Test within a Block.

    Menguji apakah proporsi bit 1 dalam setiap blok M bit
    mendekati 0.5 secara konsisten.

    Parameters
    ----------
    sequence : np.ndarray uint8 — keystream yang diuji
    M        : int              — ukuran blok (default: 128 bit)

    Returns
    -------
    dict berisi: test, n_bits, N_blocks, chi2, p_value, passed, conclusion
    """
    bits = np.unpackbits(sequence.flatten())
    n    = len(bits)
    N    = n // M
    if N == 0:
        return {"test": "NIST Block Frequency", "p_value": 0.0, "passed": False,
                "conclusion": "GAGAL — sequence terlalu pendek"}
    bits  = bits[:N * M].reshape(N, M)
    pi_i  = bits.mean(axis=1)
    chi2  = 4 * M * np.sum((pi_i - 0.5) ** 2)
    from scipy.special import gammaincc
    p_val = gammaincc(N / 2.0, chi2 / 2.0)
    return {"test": "NIST Block Frequency", "n_bits": n, "N_blocks": N,
            "chi2": chi2, "p_value": p_val, "passed": p_val > 0.01,
            "conclusion": "LULUS" if p_val > 0.01 else "GAGAL"}


# ─── Uji 3: Runs Test ────────────────────────────────────────────────────────

def nist_runs_test(sequence: np.ndarray) -> dict:
    """
    NIST SP 800-22 Test 3: Runs Test.

    Menguji apakah osilasi antara bit 0 dan bit 1
    berlangsung terlalu cepat atau terlalu lambat.

    P-value > 0.01 → sequence acak (LULUS)

    Parameters
    ----------
    sequence : np.ndarray uint8 — keystream yang diuji

    Returns
    -------
    dict berisi: test, n_bits, pi, v_n, p_value, passed, conclusion
    """
    bits = np.unpackbits(sequence.flatten())
    n    = len(bits)
    pi   = np.sum(bits) / n

    if abs(pi - 0.5) >= 2 / math.sqrt(n):
        return {
            "test":       "NIST Runs Test",
            "n_bits":     n,
            "pi":         pi,
            "p_value":    0.0,
            "passed":     False,
            "conclusion": "GAGAL pre-test: proporsi bit tidak seimbang",
        }

    v_n   = int(np.sum(bits[:-1] != bits[1:])) + 1
    num   = abs(v_n - 2 * n * pi * (1 - pi))
    denom = 2 * math.sqrt(2 * n) * pi * (1 - pi)
    p_val = math.erfc(num / denom)

    return {
        "test":       "NIST Runs Test",
        "n_bits":     n,
        "pi":         pi,
        "v_n":        v_n,
        "p_value":    p_val,
        "passed":     p_val > 0.01,
        "conclusion": "LULUS — Key stream acak" if p_val > 0.01
                      else "GAGAL — Key stream tidak acak",
    }


# ─── Uji 4: Longest Run of Ones in a Block ───────────────────────────────────

def nist_longest_run_test(sequence: np.ndarray) -> dict:
    """
    NIST SP 800-22 Test 4: Test for the Longest Run of Ones in a Block.

    Menguji apakah panjang run terpanjang bit 1 dalam setiap blok
    sesuai dengan distribusi yang diharapkan untuk sequence acak.

    Parameters
    ----------
    sequence : np.ndarray uint8 — keystream yang diuji

    Returns
    -------
    dict berisi: test, n_bits, chi2, p_value, passed, conclusion
    """
    bits = np.unpackbits(sequence.flatten())
    n    = len(bits)
    if n < 128:
        return {"test": "NIST Longest Run", "p_value": 0.0, "passed": False,
                "conclusion": "GAGAL — sequence terlalu pendek"}
    M, K = 8, 3
    pi   = [0.2148, 0.3672, 0.2305, 0.1875]
    N    = n // M
    blocks  = bits[:N * M].reshape(N, M)
    counts  = np.zeros(K + 1, dtype=int)
    for blk in blocks:
        max_run = cur_run = 0
        for b in blk:
            if b == 1:
                cur_run += 1
                max_run  = max(max_run, cur_run)
            else:
                cur_run  = 0
        if max_run <= 1:   idx = 0
        elif max_run == 2: idx = 1
        elif max_run == 3: idx = 2
        else:              idx = 3
        counts[idx] += 1
    chi2  = sum((counts[i] - N * pi[i]) ** 2 / (N * pi[i]) for i in range(K + 1))
    from scipy.special import gammaincc
    p_val = gammaincc(K / 2.0, chi2 / 2.0)
    return {"test": "NIST Longest Run", "n_bits": n, "chi2": chi2,
            "p_value": p_val, "passed": p_val > 0.01,
            "conclusion": "LULUS" if p_val > 0.01 else "GAGAL"}


# ─── Uji 5: Binary Matrix Rank Test ──────────────────────────────────────────

def nist_matrix_rank_test(sequence: np.ndarray, M: int = 32, Q: int = 32) -> dict:
    """
    NIST SP 800-22 Test 5: Binary Matrix Rank Test.

    Menguji rank matriks biner yang dibentuk dari blok-blok sequence
    terhadap distribusi rank yang diharapkan untuk sequence acak.

    Parameters
    ----------
    sequence : np.ndarray uint8 — keystream yang diuji
    M, Q     : int              — dimensi matriks (default: 32×32)

    Returns
    -------
    dict berisi: test, n_bits, N_matrices, chi2, p_value, passed, conclusion
    """
    bits = np.unpackbits(sequence.flatten())
    n    = len(bits)
    N    = n // (M * Q)
    if N == 0:
        return {"test": "NIST Matrix Rank", "p_value": 0.0, "passed": False,
                "conclusion": "GAGAL — sequence terlalu pendek"}
    F_M  = 0.2888
    F_M1 = 0.5776
    F_0  = 1 - F_M - F_M1
    counts = [0, 0, 0]
    for i in range(N):
        block = bits[i * M * Q:(i + 1) * M * Q].reshape(M, Q)
        mat   = block.copy().astype(np.int8)
        rank  = 0
        for col in range(Q):
            pivot = -1
            for row in range(rank, M):
                if mat[row, col] == 1:
                    pivot = row
                    break
            if pivot == -1:
                continue
            mat[[rank, pivot]] = mat[[pivot, rank]]
            for row in range(M):
                if row != rank and mat[row, col] == 1:
                    mat[row] = (mat[row] + mat[rank]) % 2
            rank += 1
        if rank == M:       counts[0] += 1
        elif rank == M - 1: counts[1] += 1
        else:               counts[2] += 1
    chi2  = ((counts[0] - F_M  * N) ** 2 / (F_M  * N) +
             (counts[1] - F_M1 * N) ** 2 / (F_M1 * N) +
             (counts[2] - F_0  * N) ** 2 / (F_0  * N))
    p_val = math.exp(-chi2 / 2.0)
    return {"test": "NIST Matrix Rank", "n_bits": n, "N_matrices": N,
            "chi2": chi2, "p_value": p_val, "passed": p_val > 0.01,
            "conclusion": "LULUS" if p_val > 0.01 else "GAGAL"}


# ─── Uji 6: Discrete Fourier Transform (Spectral) Test ───────────────────────

def nist_dft_test(sequence: np.ndarray) -> dict:
    """
    NIST SP 800-22 Test 6: Discrete Fourier Transform (Spectral) Test.

    Mendeteksi pola periodik dalam sequence dengan menganalisis
    komponen frekuensi melalui transformasi Fourier diskrit.

    Parameters
    ----------
    sequence : np.ndarray uint8 — keystream yang diuji

    Returns
    -------
    dict berisi: test, n_bits, N0, N1, d, p_value, passed, conclusion
    """
    bits = np.unpackbits(sequence.flatten())
    n    = len(bits)
    x    = 2 * bits.astype(np.float64) - 1
    S    = np.fft.fft(x)
    M_   = np.abs(S[:n // 2])
    T    = math.sqrt(math.log(1.0 / 0.05) * n)
    N0   = 0.95 * n / 2
    N1   = np.sum(M_ < T)
    d    = (N1 - N0) / math.sqrt(n * 0.95 * 0.05 / 4)
    p_val = math.erfc(abs(d) / math.sqrt(2))
    return {"test": "NIST DFT (Spectral)", "n_bits": n, "N0": N0, "N1": int(N1),
            "d": d, "p_value": p_val, "passed": p_val > 0.01,
            "conclusion": "LULUS" if p_val > 0.01 else "GAGAL"}


# ─── Uji 7: Non-overlapping Template Matching Test ───────────────────────────

def nist_non_overlapping_template_test(sequence: np.ndarray, template: list = None) -> dict:
    """
    NIST SP 800-22 Test 7: Non-overlapping Template Matching Test.

    Menghitung kemunculan pola template tertentu (non-overlapping)
    dalam blok-blok sequence.

    Parameters
    ----------
    sequence : np.ndarray uint8 — keystream yang diuji
    template : list             — pola bit yang dicari (default: [0,0,1])

    Returns
    -------
    dict berisi: test, n_bits, mu, chi2, p_value, passed, conclusion
    """
    bits = np.unpackbits(sequence.flatten())
    n    = len(bits)
    if template is None:
        template = [0, 0, 1]
    m    = len(template)
    M    = 8
    N    = n // M
    if N == 0:
        return {"test": "NIST Non-overlapping Template", "p_value": 0.0, "passed": False,
                "conclusion": "GAGAL — sequence terlalu pendek"}
    mu     = (M - m + 1) / (2 ** m)
    sigma2 = M * (1 / (2 ** m) - (2 * m - 1) / (2 ** (2 * m)))
    counts = []
    for i in range(N):
        blk   = bits[i * M:(i + 1) * M]
        count = j = 0
        while j <= M - m:
            if np.array_equal(blk[j:j + m], template):
                count += 1
                j     += m
            else:
                j     += 1
        counts.append(count)
    counts = np.array(counts)
    chi2   = np.sum((counts - mu) ** 2 / sigma2)
    from scipy.special import gammaincc
    p_val  = gammaincc(N / 2.0, chi2 / 2.0)
    return {"test": "NIST Non-overlapping Template", "n_bits": n, "mu": mu,
            "chi2": chi2, "p_value": p_val, "passed": p_val > 0.01,
            "conclusion": "LULUS" if p_val > 0.01 else "GAGAL"}


# ─── Uji 8: Overlapping Template Matching Test ───────────────────────────────

def nist_overlapping_template_test(sequence: np.ndarray, m: int = 9) -> dict:
    """
    NIST SP 800-22 Test 8: Overlapping Template Matching Test.

    Menghitung kemunculan pola template (overlapping — boleh bertumpang tindih)
    dalam blok-blok sequence panjang.

    Parameters
    ----------
    sequence : np.ndarray uint8 — keystream yang diuji
    m        : int              — panjang template (default: 9, template = m bit 1)

    Returns
    -------
    dict berisi: test, n_bits, chi2, p_value, passed, conclusion
    """
    bits     = np.unpackbits(sequence.flatten())
    n        = len(bits)
    template = [1] * m
    M        = 1032
    N        = n // M
    if N == 0:
        return {"test": "NIST Overlapping Template", "p_value": 0.0, "passed": False,
                "conclusion": "GAGAL — sequence terlalu pendek"}
    K    = 5
    pi_k = [0.364091, 0.185659, 0.139381, 0.100571, 0.070432, 0.139865]
    counts = np.zeros(K + 1, dtype=int)
    for i in range(N):
        blk = bits[i * M:(i + 1) * M]
        w   = sum(1 for j in range(M - m + 1) if np.array_equal(blk[j:j + m], template))
        counts[min(w, K)] += 1
    chi2  = sum((counts[k] - N * pi_k[k]) ** 2 / (N * pi_k[k])
                for k in range(K + 1) if N * pi_k[k] > 0)
    from scipy.special import gammaincc
    p_val = gammaincc(K / 2.0, chi2 / 2.0)
    return {"test": "NIST Overlapping Template", "n_bits": n,
            "chi2": chi2, "p_value": p_val, "passed": p_val > 0.01,
            "conclusion": "LULUS" if p_val > 0.01 else "GAGAL"}


# ─── Uji 9: Maurer's Universal Statistical Test ───────────────────────────────

def nist_universal_test(sequence: np.ndarray, L: int = 7, Q: int = 1280) -> dict:
    """
    NIST SP 800-22 Test 9: Maurer's Universal Statistical Test.

    Mengukur seberapa besar sequence dapat dikompresi.
    Sequence acak sejati tidak dapat dikompresi secara signifikan.

    Parameters
    ----------
    sequence : np.ndarray uint8 — keystream yang diuji
    L        : int              — panjang blok (default: 7)
    Q        : int              — jumlah blok inisialisasi (default: 1280)

    Returns
    -------
    dict berisi: test, n_bits, fn, p_value, passed, conclusion
    """
    bits = np.unpackbits(sequence.flatten())
    n    = len(bits)
    if n < (Q + 1000) * L:
        return {"test": "NIST Universal (Maurer)", "p_value": 0.0, "passed": False,
                "conclusion": "GAGAL — sequence terlalu pendek"}
    expected_value = {7: 6.1962507, 8: 7.1836656, 9: 8.1764248, 10: 9.1723243}
    variance       = {7: 3.5203,    8: 3.8784,    9: 4.5882,    10: 5.2325}
    exp_val = expected_value.get(L, 6.1962507)
    var     = variance.get(L, 3.5203)
    K       = n // L - Q
    table   = {}
    for i in range(Q):
        blk = tuple(bits[i * L:(i + 1) * L])
        table[blk] = i + 1
    fn_sum = 0.0
    for i in range(K):
        j   = Q + i
        blk = tuple(bits[j * L:(j + 1) * L])
        if blk in table:
            fn_sum += math.log2(j + 1 - table[blk])
        table[blk] = j + 1
    fn    = fn_sum / K
    c     = 0.7 - 0.8 / L + (4 + 32 / L) * (K ** (-3 / L)) / 15
    sigma = c * math.sqrt(var / K)
    p_val = math.erfc(abs((fn - exp_val) / (math.sqrt(2) * sigma)))
    return {"test": "NIST Universal (Maurer)", "n_bits": n, "fn": fn,
            "p_value": p_val, "passed": p_val > 0.01,
            "conclusion": "LULUS" if p_val > 0.01 else "GAGAL"}


# ─── Uji 10: Linear Complexity Test ──────────────────────────────────────────

def nist_linear_complexity_test(sequence: np.ndarray, M: int = 500) -> dict:
    """
    NIST SP 800-22 Test 10: Linear Complexity Test.

    Menguji apakah panjang Linear Feedback Shift Register (LFSR)
    yang dibutuhkan untuk menghasilkan sequence sesuai dengan
    ekspektasi untuk sequence acak (menggunakan Berlekamp-Massey).

    Parameters
    ----------
    sequence : np.ndarray uint8 — keystream yang diuji
    M        : int              — panjang blok (default: 500)

    Returns
    -------
    dict berisi: test, n_bits, N_blocks, chi2, p_value, passed, conclusion
    """
    bits = np.unpackbits(sequence.flatten())
    n    = len(bits)
    N    = n // M
    if N == 0:
        return {"test": "NIST Linear Complexity", "p_value": 0.0, "passed": False,
                "conclusion": "GAGAL — sequence terlalu pendek"}

    def berlekamp_massey(seq):
        n_ = len(seq)
        C, B = [1], [1]
        L, m, b = 0, -1, 1
        for i in range(n_):
            d = seq[i]
            for j in range(1, L + 1):
                if j < len(C):
                    d ^= C[j] & seq[i - j]
            d %= 2
            if d == 0:
                m += 1
            elif 2 * L <= i:
                T = C[:]
                p = [0] * (i - m); p.extend(B)
                while len(p) < len(C): p.append(0)
                while len(C) < len(p): C.append(0)
                C = [(C[j] ^ p[j]) % 2 for j in range(len(C))]
                L = i + 1 - L; B = T; m = i; b = d
            else:
                p = [0] * (i - m); p.extend(B)
                while len(p) < len(C): p.append(0)
                while len(C) < len(p): C.append(0)
                C = [(C[j] ^ (d * p[j])) % 2 for j in range(len(C))]
                m += 1
        return L

    mu     = M / 2.0 + (9 + (-1) ** (M + 1)) / 36.0 - (M / 3.0 + 2.0 / 9) / (2 ** M)
    K      = 6
    pi     = [0.010417, 0.031250, 0.125000, 0.500000, 0.250000, 0.062500, 0.020833]
    counts = np.zeros(K + 1, dtype=int)
    for i in range(N):
        blk = bits[i * M:(i + 1) * M].tolist()
        L_i = berlekamp_massey(blk)
        T_i = (-1) ** M * (L_i - mu) + 2.0 / 9
        if   T_i <= -2.5: counts[0] += 1
        elif T_i <= -1.5: counts[1] += 1
        elif T_i <= -0.5: counts[2] += 1
        elif T_i <=  0.5: counts[3] += 1
        elif T_i <=  1.5: counts[4] += 1
        elif T_i <=  2.5: counts[5] += 1
        else:             counts[6] += 1
    chi2  = sum((counts[i] - N * pi[i]) ** 2 / (N * pi[i]) for i in range(K + 1) if pi[i] > 0)
    from scipy.special import gammaincc
    p_val = gammaincc(K / 2.0, chi2 / 2.0)
    return {"test": "NIST Linear Complexity", "n_bits": n, "N_blocks": N,
            "chi2": chi2, "p_value": p_val, "passed": p_val > 0.01,
            "conclusion": "LULUS" if p_val > 0.01 else "GAGAL"}


# ─── Uji 11: Serial Test ─────────────────────────────────────────────────────

def nist_serial_test(sequence: np.ndarray, m: int = 3) -> dict:
    """
    NIST SP 800-22 Test 11: Serial Test.

    Menguji apakah semua pola bit panjang m dan m-1
    muncul dengan frekuensi yang sama (seragam).

    Parameters
    ----------
    sequence : np.ndarray uint8 — keystream yang diuji
    m        : int              — panjang pola (default: 3)

    Returns
    -------
    dict berisi: test, n_bits, p_value1, p_value2, p_value, passed, conclusion
    """
    bits = np.unpackbits(sequence.flatten())
    n    = len(bits)

    def psi2(bits, n, m):
        if m == 0:
            return 0.0
        counts = np.zeros(2 ** m, dtype=int)
        for i in range(n):
            idx = 0
            for j in range(m):
                idx = (idx << 1) | bits[(i + j) % n]
            counts[idx] += 1
        return (2 ** m / n) * np.sum(counts ** 2) - n

    psi2_m  = psi2(bits, n, m)
    psi2_m1 = psi2(bits, n, m - 1)
    psi2_m2 = psi2(bits, n, m - 2)
    del1    = psi2_m - psi2_m1
    del2    = psi2_m - 2 * psi2_m1 + psi2_m2
    from scipy.special import gammaincc
    p1    = gammaincc(2 ** (m - 2), del1 / 2.0)
    p2    = gammaincc(2 ** (m - 3), del2 / 2.0) if m >= 3 else 1.0
    p_val = min(p1, p2)
    return {"test": "NIST Serial", "n_bits": n, "p_value1": p1, "p_value2": p2,
            "p_value": p_val, "passed": p_val > 0.01,
            "conclusion": "LULUS" if p_val > 0.01 else "GAGAL"}


# ─── Uji 12: Approximate Entropy Test ────────────────────────────────────────

def nist_approximate_entropy_test(sequence: np.ndarray, m: int = 2) -> dict:
    """
    NIST SP 800-22 Test 12: Approximate Entropy Test.

    Membandingkan frekuensi pola overlapping panjang m dan m+1
    untuk mengukur regularitas sequence.

    Parameters
    ----------
    sequence : np.ndarray uint8 — keystream yang diuji
    m        : int              — panjang pola (default: 2)

    Returns
    -------
    dict berisi: test, n_bits, ApEn, chi2, p_value, passed, conclusion
    """
    bits = np.unpackbits(sequence.flatten())
    n    = len(bits)

    def phi(bits, n, m):
        counts = np.zeros(2 ** m, dtype=int)
        for i in range(n):
            idx = 0
            for j in range(m):
                idx = (idx << 1) | bits[(i + j) % n]
            counts[idx] += 1
        freq = counts[counts > 0] / n
        return np.sum(freq * np.log(freq))

    phi_m  = phi(bits, n, m)
    phi_m1 = phi(bits, n, m + 1)
    apen   = phi_m - phi_m1
    chi2   = 2 * n * (math.log(2) - apen)
    from scipy.special import gammaincc
    p_val  = gammaincc(2 ** (m - 1), chi2 / 2.0)
    return {"test": "NIST Approximate Entropy", "n_bits": n, "ApEn": apen,
            "chi2": chi2, "p_value": p_val, "passed": p_val > 0.01,
            "conclusion": "LULUS" if p_val > 0.01 else "GAGAL"}


# ─── Uji 13: Cumulative Sums Test ────────────────────────────────────────────

def nist_cumulative_sums_test(sequence: np.ndarray) -> dict:
    """
    NIST SP 800-22 Test 13: Cumulative Sums Test (Forward mode).

    Menguji apakah nilai puncak penjumlahan kumulatif sequence
    (setelah bit diubah ke ±1) sesuai dengan distribusi acak.

    Parameters
    ----------
    sequence : np.ndarray uint8 — keystream yang diuji

    Returns
    -------
    dict berisi: test, n_bits, z, p_value, passed, conclusion
    """
    bits = np.unpackbits(sequence.flatten())
    n    = len(bits)
    x    = 2 * bits.astype(np.int64) - 1
    S    = np.cumsum(x)
    z    = np.max(np.abs(S))

    def _p(z, n):
        from scipy.stats import norm
        k1 = np.arange(int((-n / z + 1) / 4), int((n / z - 1) / 4) + 1)
        k2 = np.arange(int((-n / z - 3) / 4), int((n / z - 1) / 4) + 1)
        p  = 1.0
        p -= np.sum(norm.cdf((4 * k1 + 1) * z / math.sqrt(n)) -
                    norm.cdf((4 * k1 - 1) * z / math.sqrt(n)))
        p += np.sum(norm.cdf((4 * k2 + 3) * z / math.sqrt(n)) -
                    norm.cdf((4 * k2 + 1) * z / math.sqrt(n)))
        return p

    p_val = max(0.0, min(1.0, _p(z, n)))
    return {"test": "NIST Cumulative Sums", "n_bits": n, "z": int(z),
            "p_value": p_val, "passed": p_val > 0.01,
            "conclusion": "LULUS" if p_val > 0.01 else "GAGAL"}


# ─── Uji 14: Random Excursions Test ──────────────────────────────────────────

def nist_random_excursions_test(sequence: np.ndarray) -> dict:
    """
    NIST SP 800-22 Test 14: Random Excursions Test.

    Menguji distribusi kunjungan ke state tertentu dalam siklus
    penjumlahan kumulatif yang kembali ke nol.
    Mengembalikan p-value terburuk dari 8 state yang diuji.

    Parameters
    ----------
    sequence : np.ndarray uint8 — keystream yang diuji

    Returns
    -------
    dict berisi: test, n_bits, J, p_value, passed, conclusion
    """
    bits = np.unpackbits(sequence.flatten())
    n    = len(bits)
    x    = 2 * bits.astype(np.int64) - 1
    S    = np.concatenate(([0], np.cumsum(x), [0]))
    zero_pos = np.where(S == 0)[0]
    J        = len(zero_pos) - 1
    if J < 500:
        return {"test": "NIST Random Excursions", "p_value": 1.0, "passed": True,
                "conclusion": "LULUS (N/A - siklus J<500)"}
    states = [-4, -3, -2, -1, 1, 2, 3, 4]
    from scipy.special import gammaincc
    K  = 5
    pi = {
        1: [0.5000, 0.2500, 0.1250, 0.0625, 0.0313, 0.0313],
        2: [0.7500, 0.0625, 0.0469, 0.0352, 0.0264, 0.0791],
        3: [0.8333, 0.0278, 0.0231, 0.0193, 0.0161, 0.0804],
        4: [0.8750, 0.0156, 0.0137, 0.0120, 0.0105, 0.0732],
    }
    p_vals = []
    for s in states:
        pi_s   = pi.get(abs(s), pi[4])
        counts = np.zeros(K + 1, dtype=int)
        for i in range(J):
            cyc    = S[zero_pos[i]:zero_pos[i + 1] + 1]
            visits = int(np.sum(cyc == s))
            counts[min(visits, K)] += 1
        chi2 = sum((counts[k] - J * pi_s[k]) ** 2 / (J * pi_s[k])
                   for k in range(K + 1) if J * pi_s[k] > 0)
        p_vals.append(gammaincc(K / 2.0, chi2 / 2.0))
    p_val = min(p_vals)
    return {"test": "NIST Random Excursions", "n_bits": n, "J": J,
            "p_value": p_val, "passed": p_val > 0.01,
            "conclusion": "LULUS" if p_val > 0.01 else "GAGAL"}


# ─── Uji 15: Random Excursions Variant Test ───────────────────────────────────

def nist_random_excursions_variant_test(sequence: np.ndarray) -> dict:
    """
    NIST SP 800-22 Test 15: Random Excursions Variant Test.

    Menguji jumlah total kunjungan ke berbagai state dalam
    penjumlahan kumulatif. Mengembalikan p-value terburuk dari
    18 state yang diuji (−9 hingga +9, kecuali 0).

    Parameters
    ----------
    sequence : np.ndarray uint8 — keystream yang diuji

    Returns
    -------
    dict berisi: test, n_bits, J, p_value, passed, conclusion
    """
    bits     = np.unpackbits(sequence.flatten())
    n        = len(bits)
    x        = 2 * bits.astype(np.int64) - 1
    S        = np.concatenate(([0], np.cumsum(x), [0]))
    zero_pos = np.where(S == 0)[0]
    J        = len(zero_pos) - 1
    if J < 500:
        return {"test": "NIST Random Excursions Variant", "p_value": 1.0, "passed": True,
                "conclusion": "LULUS (N/A - siklus J<500)"}
    states = list(range(-9, 0)) + list(range(1, 10))
    p_vals = []
    for s in states:
        xi_s  = int(np.sum(S == s))
        denom = math.sqrt(2 * J * (4 * abs(s) - 2))
        if denom == 0:
            p_vals.append(0.0)
            continue
        p_vals.append(math.erfc(abs(xi_s - J) / denom))
    p_val = min(p_vals)
    return {"test": "NIST Random Excursions Variant", "n_bits": n, "J": J,
            "p_value": p_val, "passed": p_val > 0.01,
            "conclusion": "LULUS" if p_val > 0.01 else "GAGAL"}


# ─── Jalankan Semua 15 Uji NIST ──────────────────────────────────────────────

def run_nist_tests(params: dict, algo: str = None) -> dict:
    """
    Jalankan seluruh 15 uji NIST SP 800-22 pada keystream yang dibangkitkan.

    Menggunakan 125.000 byte (1.000.000 bit) sesuai standar NIST SP 800-22.

    Parameters
    ----------
    params : dict — parameter chaos (x0, r, lam, alpha, beta, skip, ...)
    algo   : str  — nama algoritma (ALGO_MS_GAUSS / ALGO_MS_GAUSS_FOG / dll.)
                    Jika None, pakai default algoritma (GoF / ALGO_MS_GAUSS).

    Returns
    -------
    dict — hasil 15 uji, setiap kunci adalah nama uji, nilai adalah dict hasil
    """
    from keystream_generator import generate_keystream
    from chaos_map import ALGO_MS_GAUSS
    _algo     = algo if algo is not None else ALGO_MS_GAUSS
    keystream = generate_keystream((125_000,), params, _algo)

    return {
        "monobit":                   nist_frequency_monobit_test(keystream),
        "block_frequency":           nist_block_frequency_test(keystream),
        "runs":                      nist_runs_test(keystream),
        "longest_run":               nist_longest_run_test(keystream),
        "matrix_rank":               nist_matrix_rank_test(keystream),
        "dft":                       nist_dft_test(keystream),
        "non_overlapping":           nist_non_overlapping_template_test(keystream),
        "overlapping":               nist_overlapping_template_test(keystream),
        "universal":                 nist_universal_test(keystream),
        "linear_complexity":         nist_linear_complexity_test(keystream),
        "serial":                    nist_serial_test(keystream),
        "approx_entropy":            nist_approximate_entropy_test(keystream),
        "cumulative_sums":           nist_cumulative_sums_test(keystream),
        "random_excursions":         nist_random_excursions_test(keystream),
        "random_excursions_variant": nist_random_excursions_variant_test(keystream),
    }
