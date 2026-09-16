# Chaotic Image Encryption System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Cryptography](https://img.shields.io/badge/Domain-Digital%20Image%20Cryptography-red.svg)]()

Implementasi sistem enkripsi dan dekripsi citra digital berbasis **Peta Kaos Hibrida (Chaotic Maps)** dengan evaluasi metrik keamanan kriptografi serta analisis keacakan statistik NIST SP 800-22.

Proyek ini merupakan implementasi perangkat lunak untuk penelitian skripsi oleh **Novandi Ahmad Ramdhan** (NPM: **51422256**).

---

## 📌 Fitur Utama

1. **Kernel Peta Kaos (5 Algoritma)**:
   - **MS Map** (Modified Sine Map mandiri): \( f(x) = \left[ \frac{r \cdot \lambda \cdot x}{1 + \lambda (1 - x)^2} \right] \bmod 1 \)
   - **Gauss Map** (mandiri): \( g(x) = \exp(-\alpha x^2) + \beta \)
   - **Gauss-MS Map (GoF)** *(Algoritma Utama)*: Komposisi \( (g \circ f)(x) = \left[ \exp(-\alpha (f(x))^2) + \beta \right] \bmod 1 \)
   - **MS-Gauss Map (FoG)**: Komposisi \( (f \circ g)(x) = \left[ \frac{r \cdot \lambda \cdot g(x)}{1 + \lambda (1 - g(x))^2} \right] \bmod 1 \)
   - **Sequential (Berlapis)**: Difusi bertingkat dua keystream \( C = (P \oplus K_1) \oplus K_2 \)
   - Dioptimasi menggunakan **Numba JIT** (Just-In-Time compilation) dengan *NumPy fallback*.

2. **Pipeline Kriptografi Citra**:
   - Pembangkitan keystream 8-bit (\(uint8\)) terdistribusi seragam: \( K_k = \lfloor X_k \times 10^6 \rfloor \bmod 256 \).
   - Enkripsi difusi XOR cepat untuk citra Grayscale (2D) maupun RGB/BGR (3D).
   - Dekripsi simetris presisi tinggi (reversibilitas 100% tanpa kehilangan informasi piksel).

3. **Analisis Metrik Keamanan Kriptografi Citra**:
   - **Entropi Shannon** (mengukur keacakan distribusi piksel citra terenkripsi, ideal \(\approx 8.0\)).
   - **Koefisien Korelasi Piksel Bertetangga** (arah Horizontal, Vertikal, dan Diagonal, ideal \(\approx 0.0\)).
   - **Analisis Sensitivitas Diferensial**: NPCR (*Number of Pixels Change Rate*, ideal \(\ge 99.6\%\)) dan UACI (*Unified Average Changing Intensity*, ideal \(\approx 33.46\%\)).
   - **Uji Chi-Square** keseragaman histogram.
   - **MSE & PSNR** untuk validasi dekripsi sempurna.

4. **Pengujian Dinamika Kaos & Keacakan Statistik**:
   - Diagram Bifurkasi.
   - Eksponen Lyapunov Terbesar (Largest Lyapunov Exponent / LLE).
   - Evaluasi Uji Statistik **NIST SP 800-22** (Frequency, Runs, Longest Run, Approximate Entropy, FFT, Cumulative Sums, dll.).

5. **Antarmuka Grafis Pengguna (GUI)**:
   - Pengujian enkripsi dan dekripsi citra secara interaktif.
   - Visualisasi perbandingan citra asli vs terenkripsi.
   - Plot histogram dan *scatter plot* korelasi piksel secara *real-time*.
   - Riwayat pengujian dan ekspor laporan hasil analisis.

---

## 📂 Struktur Berkas Repositori

```text
├── chaos_map.py           # Kernel matematis iterasi 5 algoritma peta kaos
├── keystream_generator.py # Konversi barisan kaotik menjadi keystream byte (uint8)
├── encryption.py          # Pipeline proses enkripsi citra (XOR diffusion)
├── decryption.py          # Pipeline proses dekripsi citra (inverse diffusion)
├── analysis.py            # Metrik evaluasi statistik kriptografi (NPCR, UACI, Entropi, Korelasi)
├── lyapunov.py            # Perhitungan Eksponen Lyapunov (LLE)
├── bifurcation.py         # Pembangkitan data dan diagram bifurkasi
├── nist_tests.py          # Implementasi pengujian statistik NIST SP 800-22
├── histogram_plot.py      # Modul visualisasi histogram citra
├── scatter_plot.py        # Modul visualisasi diagram tebar korelasi piksel
├── gui_main.py            # Kode utama antarmuka pengguna (GUI)
├── gui_utils.py           # Utilitas pendukung tampilan antarmuka
├── history_manager.py     # Manajemen penyimpanan riwayat pengujian
├── windows/               # Dialog dan jendela pendukung antarmuka
├── requirements.txt       # Daftar dependensi pustaka Python
├── .gitignore             # Aturan berkas yang diabaikan oleh Git
└── README.md              # Dokumentasi teknis proyek
```

---

## 🚀 Instalasi & Cara Menjalankan

### 1. Kloning Repositori
```bash
git clone https://github.com/Vannnd1/chaotic-image-encryption.git
cd chaotic-image-encryption
```

### 2. Buat & Aktifkan Virtual Environment (Disarankan)
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Pasang Dependensi
```bash
pip install -r requirements.txt
```

### 4. Jalankan Aplikasi GUI
```bash
python gui_main.py
```

---

## ⚙️ Parameter Default Penelitian

| Parameter | Simbol | Nilai Default | Keterangan |
| :--- | :---: | :---: | :--- |
| Kondisi Awal | \(X_0\) | 0.3 | Nilai awal iterasi kaos |
| Parameter Bifurkasi MS Map | \(r\) | 3.5 | Faktor kendali keacakan MS Map |
| Parameter Kendali MS Map | \(\lambda\) | 3.5 | Konstanta bentuk MS Map |
| Parameter Bentuk Gauss | \(\alpha\) | 5.8 | Lebar fungsi Gauss |
| Parameter Pergeseran Gauss | \(\beta\) | 2.5 | Offset vertikal Gauss |
| Transient Iterations | *skip* | 200 | Iterasi awal yang dibuang untuk kestabilan |

---

## 👨‍💻 Penulis / Pengembang

* **Novandi Ahmad Ramdhan**
* NPM: **51422256**
* Program Studi Informatika / Sistem Komputer
* GitHub: [@Vannnd1](https://github.com/Vannnd1)

---

## 📄 Lisensi
Didistribusikan di bawah lisensi MIT. Lihat berkas `LICENSE` untuk rincian selengkapnya.
