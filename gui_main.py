"""
gui_main.py — Halaman Utama (Menu Utama) Aplikasi GUI
======================================================
File ini adalah pintu masuk utama program berbasis tampilan grafis (GUI).
Menampilkan halaman awal dengan menu navigasi ke semua fitur aplikasi.

FUNGSI UTAMA FILE INI:
  1. Menginisialisasi jendela utama aplikasi Tkinter
  2. Menampilkan logo, judul, dan deskripsi singkat aplikasi
  3. Menyediakan tombol navigasi ke semua fitur:
       → Enkripsi Gambar      (windows/encrypt.py — EncryptionWindow)
       → Dekripsi Gambar      (windows/encrypt.py — DecryptionWindow)
       → Analisis Keamanan    (windows/analysis_win.py — AnalisisWindow)
       → Diagram Kaos         (windows/charts.py — LyapunovWindow/BifurkasiWindow)
       → Riwayat Operasi      (windows/history_win.py — HistoryWindow)
  4. Menampilkan informasi algoritma yang tersedia

ALGORITMA YANG BISA DIPILIH PENGGUNA:
  1. MS Map
  2. Gauss Map
  3. MS Map + Gauss Map  (Sequential/Berlapis)
  4. Gauss MS Map        (Komposisi g∘f)
  5. MS Gauss Map        (Komposisi f∘g)

CATATAN:
  - Jalankan file ini untuk memulai program GUI: python gui_main.py
  - Tema: Dark Mode Modern dengan font Segoe UI
"""

import tkinter as tk
from tkinter import messagebox

from gui_utils import (
    BG, BG2, BG3, ACCENT, ACCENT2, FG, FG2, BORDER,
    F9, F10, F10B, F11B, F12B, F14B,
    _btn, _btn_secondary, _btn_danger, _lbl, _lframe, _info_btn,
    _section_header, _separator,
)
from chaos_map import ALGO_MS_MAP, ALGO_GAUSS_MAP, ALGO_SEQUENTIAL, ALGO_MS_GAUSS, ALGO_MS_GAUSS_FOG

from windows.charts      import LyapunovWindow, BifurcationWindow, ScatterPlotWindow
from windows.encrypt     import EncryptionWindow, DecryptionWindow
from windows.analysis_win import AnalisisWindow, NISTWindow, CorrelationWindow
from windows.compare     import HistogramRGBWindow, HistogramGrayWindow, PSNRWindow, VisualSensitivityWindow
from windows.history_win  import HistoryWindow


# ── Deskripsi algoritma untuk tooltip ────────────────────────────────────────
ALGO_INFO = {
    ALGO_MS_MAP: (
        "MS Map — Mandiri\n\n"
        "Formula:\n"
        "  X(n+1) = [ r·λ·Xn / (1 + λ·(1 - Xn)²) ] mod 1\n\n"
        "Keystream K dibangkitkan dari deret chaotic MS Map.\n"
        "Enkripsi: C = P ⊕ K\n\n"
        "Parameter chaos: r (3.1–4.0), λ (3.5–5.0)"
    ),
    ALGO_GAUSS_MAP: (
        "Gauss Map — Mandiri\n\n"
        "Formula:\n"
        "  X(n+1) = [ exp(-α·Xn²) + β ] mod 1\n\n"
        "Keystream K dibangkitkan dari deret chaotic Gauss Map.\n"
        "Enkripsi: C = P ⊕ K\n\n"
        "Parameter chaos: α (≥3.1), β (≥3.1)"
    ),
    ALGO_SEQUENTIAL: (
        "MS Map + Gauss Map — Sequential (Berlapis)\n\n"
        "Dua keystream berbeda digunakan secara berlapis:\n"
        "  K1 dari MS Map,  K2 dari Gauss Map\n\n"
        "Enkripsi:\n"
        "  C1 = P  ⊕ K1   ← lapisan pertama (MS Map)\n"
        "  C  = C1 ⊕ K2   ← lapisan kedua  (Gauss Map)\n\n"
        "Dekripsi (urutan terbalik):\n"
        "  C1 = C  ⊕ K2\n"
        "  P  = C1 ⊕ K1"
    ),
    ALGO_MS_GAUSS: (
        "Gauss MS Map — Komposisi (g∘f)(x)\n\n"
        "Fungsi chaos BARU hasil komposisi MS Map dan Gauss Map:\n"
        "  h(x) = g(f(x))\n\n"
        "  f(x) = [ r·λ·x / (1+λ·(1-x)²) ] mod 1  ← MS Map (dalam)\n"
        "  g(y) = [ exp(-α·y²) + β ] mod 1          ← Gauss Map (luar)\n\n"
        "Keystream K dibangkitkan dari satu deret h(x).\n"
        "Enkripsi: C = P ⊕ K\n\n"
        "Parameter: X0=0.3, r=3.5, α=5.8, β=3.1, λ=3.5"
    ),
    ALGO_MS_GAUSS_FOG: (
        "MS Gauss Map — Komposisi (f∘g)(x)\n\n"
        "Komposisi TERBALIK: Gauss Map diterapkan dahulu (fungsi dalam),\n"
        "kemudian MS Map diterapkan pada hasilnya (fungsi luar).\n\n"
        "  h(x) = f(g(x))\n\n"
        "  g(x) = [ exp(-α·x²) + β ] mod 1          ← Gauss Map (dalam)\n"
        "  f(y) = [ r·λ·y / (1 + λ·(1 - y)²) ] mod 1  ← MS Map (luar)\n\n"
        "Keystream K dibangkitkan dari satu deret h(x).\n"
        "Enkripsi: C = P ⊕ K\n\n"
        "Parameter: X0=0.3, r=3.5, α=5.8, β=3.1, λ=3.5"
    ),
}

HELP_TEXT = (
    "PANDUAN PENGGUNAAN PROGRAM\n"
    "═══════════════════════════════════════════\n\n"
    "1. PILIH ALGORITMA\n"
    "   Pilih salah satu dari 4 algoritma chaos di panel tengah.\n"
    "   Klik tombol ℹ di sebelah nama algoritma untuk melihat\n"
    "   penjelasan formula dan cara kerjanya.\n\n"
    "2. ENKRIPSI GAMBAR\n"
    "   • Klik [Enkripsi] → jendela enkripsi terbuka\n"
    "   • Klik [Open Image] → pilih file gambar (PNG/JPG/BMP)\n"
    "   • Sesuaikan parameter chaos jika diperlukan\n"
    "   • Klik [Enkripsi] → gambar dienkripsi\n"
    "   • Klik [Save Image] → simpan hasil enkripsi\n\n"
    "3. DEKRIPSI GAMBAR\n"
    "   • Klik [Dekripsi] → jendela dekripsi terbuka\n"
    "   • Gunakan PARAMETER YANG SAMA persis seperti saat enkripsi\n"
    "   • Klik [Dekripsi] → gambar dipulihkan\n\n"
    "4. DIAGRAM LYAPUNOV\n"
    "   • Pilih parameter (r / α / β / λ) yang ingin dianalisis\n"
    "   • Klik tombol parameter → diagram terbuka\n"
    "   • µ > 0 = sistem chaotic, µ ≤ 0 = sistem stabil/periodik\n\n"
    "5. DIAGRAM BIFURKASI\n"
    "   • Menunjukkan sebaran nilai Xn saat parameter berubah\n"
    "   • Area padat/gelap = perilaku chaotic\n\n"
    "6. ANALISIS & COMPARE\n"
    "   • Histogram RGB/Grayscale: bandingkan distribusi piksel\n"
    "   • Hitung PSNR: ukur kualitas rekonstruksi setelah dekripsi\n\n"
    "Format gambar yang didukung: PNG, JPG, BMP, TIFF"
)




# ═══════════════════════════════════════════════════════════════════════════════
# KELAS APP — Main Menu (root window)
# ═══════════════════════════════════════════════════════════════════════════════

class App:
    def __init__(self):
        # DPI Awareness fix agar gambar tidak burik (pecah) di layar modern (Windows)
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
            
        self.root = tk.Tk()
        self.root.title("Enkripsi Citra Digital")
        self.root.configure(bg=BG)
        
        # Maximize window otomatis agar semua tombol muat setelah DPI HD aktif
        try:
            self.root.state("zoomed")
        except:
            self.root.geometry("1280x800")
            
        self.root.resizable(True, True)

        # State enkripsi terakhir
        self.last_original  = None
        self.last_encrypted = None
        self.last_decrypted = None

        self.algorithm = tk.StringVar(value=ALGO_MS_GAUSS)
        self._build()

    # ── Build Main Menu ───────────────────────────────────────────────────────
    def _build(self):
        root = self.root

        # ── Accent bar paling atas ────────────────────────────────────────
        tk.Frame(root, bg=ACCENT, height=3).pack(fill="x")

        # ── Header (Ditengahkan agar seimbang & profesional) ──────────────
        hdr = tk.Frame(root, bg=BG2, pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Enkripsi Citra Digital Berbasis Chaos",
                 bg=BG2, fg=FG, font=("Segoe UI", 16, "bold"), justify="center").pack(anchor="center")
        tk.Frame(hdr, bg=ACCENT, height=2).pack(fill="x", pady=(10, 0))

        # ── Body (Kontainer Tengah agar jarak antar kolom tidak terlalu jauh)
        body = tk.Frame(root, bg=BG)
        body.pack(fill="both", expand=True, pady=12)

        wrapper = tk.Frame(body, bg=BG)
        wrapper.pack(anchor="n", pady=8)

        # ── KOLOM KIRI 1 — Pengujian Kunci & Sifat Chaos ──────────────────
        left = tk.Frame(wrapper, bg=BG)
        left.pack(side="left", anchor="n", padx=8)

        fKey = _lframe(left, "  🔑  Pengujian Sifat Chaos")
        fKey.pack(fill="x", pady=(0, 8), ipady=4)

        # Sub-header: Diagram Lyapunov
        boxL = tk.Frame(fKey, bg=BG3)
        boxL.pack(fill="x", padx=8, pady=(4, 0))
        tk.Label(boxL, text="Diagram Lyapunov", bg=BG3, fg=FG, font=F9).pack(anchor="w", padx=6, pady=(4, 0))
        lrow = tk.Frame(boxL, bg=BG3)
        lrow.pack(padx=4, pady=(2, 6), fill="x")
        for p in [("r", "r"), ("α", "a"), ("β", "b"), ("λ", "lambda")]:
            b = tk.Button(lrow, text=p[0], command=lambda x=p[1]: self._open_lyapunov(x),
                          bg=BG2, fg=ACCENT, font=F10B, width=4, relief="flat", padx=3, pady=4,
                          activebackground=ACCENT, activeforeground="white", cursor="hand2")
            b.pack(side="left", fill="x", expand=True, padx=2)

        # Sub-header: Diagram Bifurkasi
        boxB = tk.Frame(fKey, bg=BG3)
        boxB.pack(fill="x", padx=8, pady=(8, 0))
        tk.Label(boxB, text="Diagram Bifurkasi", bg=BG3, fg=FG, font=F9).pack(anchor="w", padx=6, pady=(4, 0))
        brow = tk.Frame(boxB, bg=BG3)
        brow.pack(padx=4, pady=(2, 6), fill="x")
        for p in [("r", "r"), ("α", "a"), ("β", "b"), ("λ", "lambda")]:
            b = tk.Button(brow, text=p[0], command=lambda x=p[1]: self._open_bifurcation(x),
                          bg=BG2, fg=ACCENT, font=F10B, width=4, relief="flat", padx=3, pady=4,
                          activebackground=ACCENT, activeforeground="white", cursor="hand2")
            b.pack(side="left", fill="x", expand=True, padx=2)

        _separator(fKey).pack(fill="x", padx=8, pady=10)
        
        # Tombol Analisis Keacakan Kunci
        _btn_secondary(fKey, "📌  Scatter Keystream", self._open_scatter, width=24).pack(padx=8, pady=4)
        _btn_secondary(fKey, "🔬  Uji Acak NIST SP 800", self._open_nist, width=24).pack(padx=8, pady=(4, 8))

        # ── KOLOM KIRI 2 — Pengujian Keamanan Citra ───────────────────────
        left2 = tk.Frame(wrapper, bg=BG)
        left2.pack(side="left", anchor="n", padx=8)

        fSec = _lframe(left2, "  🔍  Pengujian Keamanan Citra")
        fSec.pack(fill="x", pady=(0, 8), ipady=4)
        
        _btn_secondary(fSec, "Histogram RGB",       self._open_hist_rgb,  width=22).pack(padx=8, pady=6)
        _btn_secondary(fSec, "Histogram Grayscale", self._open_hist_gray, width=22).pack(padx=8, pady=6)
        _btn_secondary(fSec, "Hitung MSE & PSNR",   self._open_psnr,      width=22).pack(padx=8, pady=6)
        _btn_secondary(fSec, "Sensitivitas Visual", self._open_visual_sensitivity, width=22).pack(padx=8, pady=6)

        # ── KOLOM TENGAH — Pilih Algoritma (Modern Buttons) & Aksi ────────
        mid = tk.Frame(wrapper, bg=BG)
        mid.pack(side="left", anchor="n", padx=8)

        fm = _lframe(mid, "  ⚙️  Pilih Algoritma Chaos")
        fm.pack(fill="x", pady=(0, 10), ipady=6)

        algos = [
            (ALGO_MS_MAP,         "MS Map",                 "fungsi mandiri — f(x)"),
            (ALGO_GAUSS_MAP,      "Gauss Map",               "fungsi mandiri — g(x)"),
            (ALGO_SEQUENTIAL,     "MS Map + Gauss Map",      "sequential / berlapis"),
            (ALGO_MS_GAUSS,       "Gauss MS Map (g∘f)",     "komposisi — h(x)=g(f(x))"),
            (ALGO_MS_GAUSS_FOG,   "MS Gauss Map (f∘g)",     "komposisi — h(x)=f(g(x))"),
        ]

        self.algo_buttons = {}
        for val, name, desc in algos:
            row = tk.Frame(fm, bg=BG2)
            row.pack(fill="x", padx=10, pady=3)

            btn = tk.Button(
                row, text=f"   {name}  —  {desc}",
                command=lambda v=val: self._select_algorithm(v),
                bg=BG3, fg=FG, font=F9, anchor="w",
                relief="flat", pady=8, padx=12,
                activebackground=ACCENT, activeforeground="white",
                cursor="hand2"
            )
            btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

            ib = tk.Button(
                row, text="ℹ",
                command=lambda v=val, n=name: self._show_algo_info(v, n),
                bg=BG3, fg=ACCENT, font=F10B,
                relief="flat", width=3, pady=8,
                cursor="hand2",
                activebackground=ACCENT, activeforeground="white"
            )
            ib.pack(side="right")
            self.algo_buttons[val] = (btn, name, desc)

        # Indikator algoritma terpilih
        self.lbl_algo_active = tk.Label(
            fm, text=f"● Aktif: {ALGO_MS_GAUSS}",
            bg=BG2, fg=ACCENT, font=F10B, padx=10
        )
        self.lbl_algo_active.pack(anchor="w", padx=10, pady=(6, 2))

        # Tombol aksi utama
        fa = tk.Frame(mid, bg=BG)
        fa.pack(fill="x")
        _btn(fa, "🔒  Enkripsi Citra", self._open_encryption, width=32).pack(fill="x", pady=(0, 6), ipady=3)
        _btn(fa, "🔓  Dekripsi Citra", self._open_decryption, width=32,
             color="#1D4ED8").pack(fill="x", pady=(0, 6), ipady=3)

        # Inisialisasi tampilan tombol algoritma aktif awal
        self._select_algorithm(self.algorithm.get())

        # ── KOLOM KANAN — Utilitas ────────────────────────────────────────
        right = tk.Frame(wrapper, bg=BG)
        right.pack(side="left", anchor="n", padx=8)

        fur = _lframe(right, "  🛠  Utilitas")
        fur.pack(fill="x", ipady=4)
        _btn_secondary(fur, "⏳  Riwayat",   self._open_history,          width=16).pack(padx=8, pady=4)
        _btn_secondary(fur, "❓  Bantuan",  self._show_help,             width=16).pack(padx=8, pady=4)
        _separator(fur).pack(fill="x", padx=8, pady=4)
        _btn_danger(fur,    "✕  Keluar",   self.exit_app,               width=16).pack(padx=8, pady=4)

    # ── Event: Algoritma Berubah (Button Selection) ────────────────────────────
    def _select_algorithm(self, val):
        self.algorithm.set(val)
        for v, (btn, name, desc) in self.algo_buttons.items():
            if v == val:
                btn.configure(
                    text=f" ●   {name}  —  {desc}",
                    bg=ACCENT, fg="white", font=F10B
                )
            else:
                btn.configure(
                    text=f" ○   {name}  —  {desc}",
                    bg=BG3, fg=FG, font=F9
                )
        self.lbl_algo_active.configure(
            text=f"● Aktif: {val}"
        )

    # ── Window Openers ────────────────────────────────────────────────────────
    def _open_history(self):
        HistoryWindow(self.root, self)

    def _open_lyapunov(self, param="r"):
        LyapunovWindow(self.root, self, param)

    def _open_bifurcation(self, param="r"):
        BifurcationWindow(self.root, self, param)

    def _open_scatter(self):
        ScatterPlotWindow(self.root, self)

    def _open_encryption(self):
        EncryptionWindow(self.root, self)

    def _open_decryption(self):
        DecryptionWindow(self.root, self)

    def _open_hist_rgb(self):
        HistogramRGBWindow(self.root, self)

    def _open_hist_gray(self):
        HistogramGrayWindow(self.root, self)

    def _open_psnr(self):
        PSNRWindow(self.root, self)

    def _open_visual_sensitivity(self):
        VisualSensitivityWindow(self.root, self)

    def _open_nist(self):
        NISTWindow(self.root, self)

    def open_correlation(self, original=None, encrypted=None, decrypted=None):
        CorrelationWindow(self.root, self, original, encrypted, decrypted)

    # ── Dialogs ───────────────────────────────────────────────────────────────
    def _show_algo_info(self, algo_val, algo_name):
        from gui_utils import _InfoDialog
        _InfoDialog(self.root, f"Algoritma: {algo_name}", ALGO_INFO[algo_val])

    def _show_help(self):
        from gui_utils import HelpWindow
        HelpWindow(self.root, program_type="lengkap")

    def exit_app(self):
        if messagebox.askokcancel("Keluar", "Yakin ingin keluar dari program?",
                                  parent=self.root):
            self.root.quit()
            self.root.destroy()

    def run(self):
        self.root.mainloop()


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = App()
    app.run()
