"""
windows/compare.py — Jendela Perbandingan Visual & Histogram (GUI)
===================================================================
File ini menampilkan halaman-halaman untuk membandingkan gambar asli
dengan gambar terenkripsi secara visual menggunakan grafik dan histogram.

HALAMAN (WINDOW) YANG ADA:
  1. HistogramRGBWindow  → histogram saluran warna R, G, B secara terpisah
                            Membandingkan distribusi warna gambar asli vs terenkripsi
                            Enkripsi baik = histogram terenkripsi rata/seragam

  2. HistogramGrayWindow → histogram gambar grayscale (satu saluran)
                            Visualisasi distribusi intensitas piksel 0–255

  3. PSNRWindow           → menampilkan nilai PSNR dan MSE
                            PSNR rendah (misal: 8 dB) = enkripsi sangat berbeda dari asli
                            PSNR tinggi = gambar masih mirip asli (dekripsi berhasil)

FUNGSI UTAMA FILE INI:
  1. Menerima gambar asli dan terenkripsi sebagai input perbandingan
  2. Menampilkan kedua gambar berdampingan (side by side)
  3. Memplot histogram distribusi piksel untuk perbandingan visual
  4. Menghitung dan menampilkan nilai PSNR & MSE

CATATAN:
  - Histogram yang RATA pada gambar terenkripsi menandakan enkripsi yang baik
  - File ini bergantung pada analysis.py untuk perhitungan PSNR/MSE
  - Tema: Dark Mode Modern
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
import numpy as np
import math
import cv2
from encryption import encrypt_image
from decryption import decrypt_image
from chaos_map import ALGO_MS_GAUSS_FOG, ALGO_MS_GAUSS
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui_utils import (
    _Base, _btn, _btn_secondary, _btn_danger, _lbl, _lframe, _entry,
    BG, BG2, BG3, ACCENT, FG, FG2, BORDER, F9, F10, F10B,
    SUCCESS, DANGER,
    show_cv2,
)

PLOT_BG   = "#F8FAFC"
PLOT_FACE = "#FFFFFF"
PLOT_GRID = "#E2E8F0"
PLOT_TEXT = "#0F172A"


# ═══════════════════════════════════════════════════════════════════════════════
# WINDOW — Histogram RGB
# ═══════════════════════════════════════════════════════════════════════════════

class HistogramRGBWindow(_Base):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Compare Histogram RGB", "1100x680")
        self.img1 = None
        self.img2 = None
        self._build()

    def _build(self):
        w = self.win
        self._title_bar(w, "🔍  Perbandingan Histogram Citra Warna (RGB)",
                        "Distribusi piksel per channel  R · G · B")

        # Metadata bar
        info = tk.Frame(w, bg=BG2, pady=8)
        info.pack(fill="x", padx=0)
        _btn(info, "▶  Compare RGB", self._compare, width=16).pack(side="left", padx=14)

        meta_fields = ["Height", "Width", "Bit Depth", "Color Type"]
        self.meta1, self.meta2 = {}, {}
        for mf in meta_fields:
            tk.Label(info, text=mf + ":", bg=BG2, fg=FG2, font=F9).pack(
                side="left", padx=(8, 2))
            e1, v1 = _entry(info, "—", readonly=True, width=6)
            e1.pack(side="left")
            self.meta1[mf] = v1
            e2, v2 = _entry(info, "—", readonly=True, width=6)
            e2.pack(side="left", padx=(2, 4))
            self.meta2[mf] = v2

        # PENTING: Paksa baris navigasi (Main Menu & Keluar) dipack LEBIH DULU
        # agar posisi di bawah terdistribusikan dengan aman tanpa pernah terdorong keluar layar!
        self._nav_row(w)

        body = tk.Frame(w, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=8)
        body.columnconfigure(0, weight=1, uniform="g1")
        body.columnconfigure(1, weight=1, uniform="g1")
        body.rowconfigure(0, weight=1)

        self._build_side(body, 0,  "Citra Pertama (Input 1)", 1)
        self._build_side(body, 1,  "Citra Kedua (Input 2)",   2)

    def _build_side(self, parent, side, title, n):
        fr = _lframe(parent, f"  📂  {title}")
        fr.grid(row=0, column=side, sticky="nsew", padx=6, pady=4)

        # Panel Kiri di dalam kartu: Pratinjau gambar & Tombol Buka
        left_panel = tk.Frame(fr, bg=BG2)
        left_panel.pack(side="left", anchor="n", padx=10, pady=10)

        img_box = tk.Frame(left_panel, width=240, height=220, bg=BG3,
                           highlightbackground=BORDER, highlightthickness=1)
        img_box.pack_propagate(False)
        img_box.pack(pady=(0, 10))

        img_lbl = tk.Label(img_box, bg=BG3,
                           text="Belum ada gambar\n\n Klik Open Image",
                           fg=FG2, font=F9)
        img_lbl.place(relx=0.5, rely=0.5, anchor="center")
        open_cmd = self._open1 if n == 1 else self._open2
        _btn(left_panel, "📂  Open Image", open_cmd, width=18).pack(fill="x", ipady=2)

        # Panel Kanan: histogram R, G, B responsif mengikuti lebar right_panel
        right_panel = tk.Frame(fr, bg=BG2)
        right_panel.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=6)

        fig = plt.Figure()
        fig.patch.set_facecolor(PLOT_BG)
        ax_r = fig.add_subplot(311)
        ax_g = fig.add_subplot(312)
        ax_b = fig.add_subplot(313)
        for ch, color, ax in zip(["R", "G", "B"], ["#EF4444", "#22C55E", "#3B82F6"], (ax_r, ax_g, ax_b)):
            ax.set_facecolor(PLOT_FACE)
            for sp in ax.spines.values(): sp.set_edgecolor(BORDER)
            ax.set_xlim(0, 255)
            ax.set_ylim(0, 100)
            ax.set_yticks([])
            ax.set_title(f"Channel {ch}", fontsize=8, color=color, fontweight="bold", pad=2)
            ax.tick_params(colors=FG2, labelsize=7)
            ax.text(127.5, 50, "Buka gambar dan klik Compare RGB", color=FG2, fontsize=8,
                    ha="center", va="center", style="italic")
        fig.subplots_adjust(hspace=0.65, left=0.10, right=0.90, top=0.88, bottom=0.18)

        canvas = FigureCanvasTkAgg(fig, master=right_panel)
        cw = canvas.get_tk_widget()
        cw.pack(fill="both", expand=True)

        if n == 1:
            self.lbl_img1, self.fig1, self.axs1 = img_lbl, fig, (ax_r, ax_g, ax_b)
        else:
            self.lbl_img2, self.fig2, self.axs2 = img_lbl, fig, (ax_r, ax_g, ax_b)

    def _open_img(self, lbl_widget):
        path = filedialog.askopenfilename(parent=self.win,
            filetypes=[("Image", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff")])
        if not path:
            return None
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            messagebox.showerror("Error", "Gagal membuka gambar!", parent=self.win)
            return None
        show_cv2(lbl_widget, img, 230, 210)
        return img

    def _update_meta(self, img, meta_dict):
        h, w = img.shape[:2]
        meta_dict["Height"].set(str(h))
        meta_dict["Width"].set(str(w))
        meta_dict["Color Type"].set("BGR")
        meta_dict["Bit Depth"].set("8")

    def _open1(self):
        self.img1 = self._open_img(self.lbl_img1)
        if self.img1 is not None:
            self._update_meta(self.img1, self.meta1)

    def _open2(self):
        self.img2 = self._open_img(self.lbl_img2)
        if self.img2 is not None:
            self._update_meta(self.img2, self.meta2)

    def _compare(self):
        for img, fig, axs in [(self.img1, self.fig1, self.axs1), (self.img2, self.fig2, self.axs2)]:
            if img is None:
                continue
            for ax, ch, color in zip(axs, ["R", "G", "B"], ["#EF4444", "#22C55E", "#3B82F6"]):
                idx = {"R": 2, "G": 1, "B": 0}[ch]
                ax.clear()
                ax.set_facecolor(PLOT_FACE)
                for sp in ax.spines.values(): sp.set_edgecolor(BORDER)
                
                hist = cv2.calcHist([img], [idx], None, [256], [0, 256])
                E = (img.shape[0] * img.shape[1]) / 256.0
                chi2 = float(np.sum(((hist - E) ** 2) / E))
                
                ax.hist(img[:, :, idx].flatten(), bins=256, range=(0, 256),
                        color=color, alpha=0.85, edgecolor="none")
                ax.set_xlim([0, 255])
                ax.set_ylabel("Freq", fontsize=7, color=FG2)
                ax.set_title(f"Channel {ch} (Chi-Square: {chi2:.2f})", fontsize=8, color=color, fontweight="bold", pad=2)
                ax.tick_params(colors=FG2, labelsize=7)
            fig.subplots_adjust(hspace=0.65, left=0.14, right=0.90, top=0.88, bottom=0.18)
            fig.canvas.draw()


# ═══════════════════════════════════════════════════════════════════════════════
# WINDOW — Histogram Grayscale
# ═══════════════════════════════════════════════════════════════════════════════

class HistogramGrayWindow(_Base):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Compare Histogram Grayscale", "1100x680")
        self.img1 = None
        self.img2 = None
        self._build()

    def _build(self):
        w = self.win
        self._title_bar(w, "🔍  Perbandingan Histogram Grayscale",
                        "Distribusi intensitas piksel (0–255)")

        # Metadata bar
        info = tk.Frame(w, bg=BG2, pady=8)
        info.pack(fill="x", padx=0)
        _btn(info, "▶  Compare Grayscale", self._compare, width=18).pack(side="left", padx=14)

        meta_fields = ["Height", "Width", "Bit Depth", "Color Type"]
        self.meta1, self.meta2 = {}, {}
        for mf in meta_fields:
            tk.Label(info, text=mf + ":", bg=BG2, fg=FG2, font=F9).pack(
                side="left", padx=(8, 2))
            e1, v1 = _entry(info, "—", readonly=True, width=6)
            e1.pack(side="left")
            self.meta1[mf] = v1
            e2, v2 = _entry(info, "—", readonly=True, width=6)
            e2.pack(side="left", padx=(2, 4))
            self.meta2[mf] = v2

        self._nav_row(w)

        body = tk.Frame(w, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=8)
        body.columnconfigure(0, weight=1, uniform="g1")
        body.columnconfigure(1, weight=1, uniform="g1")
        body.rowconfigure(0, weight=1)

        self._build_side(body, 0,  "Citra Pertama (Input 1)", 1)
        self._build_side(body, 1,  "Citra Kedua (Input 2)",   2)

    def _build_side(self, parent, side, title, n):
        fr = _lframe(parent, f"  📂  {title}")
        fr.grid(row=0, column=side, sticky="nsew", padx=6, pady=4)

        # Panel Kiri di dalam kartu: Pratinjau gambar & Tombol Buka
        left_panel = tk.Frame(fr, bg=BG2)
        left_panel.pack(side="left", anchor="n", padx=10, pady=10)

        img_box = tk.Frame(left_panel, width=240, height=220, bg=BG3,
                           highlightbackground=BORDER, highlightthickness=1)
        img_box.pack_propagate(False)
        img_box.pack(pady=(0, 10))

        img_lbl = tk.Label(img_box, bg=BG3,
                           text="Belum ada gambar\n\n Klik Open Image",
                           fg=FG2, font=F9)
        img_lbl.place(relx=0.5, rely=0.5, anchor="center")
        open_cmd = self._open1 if n == 1 else self._open2
        _btn(left_panel, "📂  Open Image", open_cmd, width=18).pack(fill="x", ipady=2)

        # Panel Kanan: histogram Grayscale
        right_panel = tk.Frame(fr, bg=BG2)
        right_panel.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=6)

        fig = plt.Figure()
        fig.patch.set_facecolor(PLOT_BG)
        ax = fig.add_subplot(111)
        ax.set_facecolor(PLOT_FACE)
        for sp in ax.spines.values(): sp.set_edgecolor(BORDER)
        ax.set_xlim(0, 255)
        ax.set_ylim(0, 100)
        ax.set_yticks([])
        ax.set_title("Histogram Grayscale", fontsize=9, color=FG, fontweight="bold", pad=2)
        ax.tick_params(colors=FG2, labelsize=7)
        ax.text(127.5, 50, "Buka gambar dan klik Compare Grayscale", color=FG2, fontsize=8,
                ha="center", va="center", style="italic")
        fig.subplots_adjust(left=0.10, right=0.90, top=0.85, bottom=0.15)

        canvas = FigureCanvasTkAgg(fig, master=right_panel)
        cw = canvas.get_tk_widget()
        cw.pack(fill="both", expand=True)

        if n == 1:
            self.lbl_img1, self.fig1, self.ax1 = img_lbl, fig, ax
        else:
            self.lbl_img2, self.fig2, self.ax2 = img_lbl, fig, ax

    def _open_img(self, lbl_widget):
        path = filedialog.askopenfilename(parent=self.win,
            filetypes=[("Image", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff")])
        if not path:
            return None
        # Buka sebagai grayscale langsung
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            messagebox.showerror("Error", "Gagal membuka gambar!", parent=self.win)
            return None
        show_cv2(lbl_widget, img, 230, 210)
        return img

    def _update_meta(self, img, meta_dict):
        h, w = img.shape[:2]
        meta_dict["Height"].set(str(h))
        meta_dict["Width"].set(str(w))
        meta_dict["Color Type"].set("GRAY")
        meta_dict["Bit Depth"].set("8")

    def _open1(self):
        self.img1 = self._open_img(self.lbl_img1)
        if self.img1 is not None:
            self._update_meta(self.img1, self.meta1)

    def _open2(self):
        self.img2 = self._open_img(self.lbl_img2)
        if self.img2 is not None:
            self._update_meta(self.img2, self.meta2)

    def _compare(self):
        for img, fig, ax in [(self.img1, self.fig1, self.ax1), (self.img2, self.fig2, self.ax2)]:
            if img is None:
                continue
            ax.clear()
            ax.set_facecolor(PLOT_FACE)
            for sp in ax.spines.values(): sp.set_edgecolor(BORDER)
            
            hist = cv2.calcHist([img], [0], None, [256], [0, 256])
            E = (img.shape[0] * img.shape[1]) / 256.0
            chi2 = float(np.sum(((hist - E) ** 2) / E))
            
            ax.hist(img.flatten(), bins=256, range=(0, 256),
                    color=ACCENT, alpha=0.85, edgecolor="none")
            ax.set_xlim([0, 255])
            ax.set_ylabel("Freq", fontsize=8, color=FG2)
            ax.set_xlabel("Intensitas", fontsize=8, color=FG2)
            ax.set_title(f"Histogram ($\chi^2$: {chi2:.2f})", fontsize=10, color=FG, fontweight="bold", pad=4)
            ax.tick_params(colors=FG2, labelsize=7)
            fig.subplots_adjust(left=0.12, right=0.92, top=0.88, bottom=0.18)
            fig.canvas.draw()


# ===============================================================================
# WINDOW — Hitung PSNR
# ===============================================================================

class PSNRWindow(_Base):
    def __init__(self, parent, app):
        super().__init__(parent, app, "PSNR & MSE", "800x600")
        self.img1 = None
        self.img2 = None
        self._build()

    def _build(self):
        w = self.win
        self._title_bar(w, "Perhitungan PSNR & MSE", "Menghitung kemiripan gambar asli dengan gambar terdekripsi atau terenkripsi.")
        self._nav_row(w)
        
        fr_top = _lframe(w, "  Kontrol PSNR")
        fr_top.pack(fill="x", padx=12, pady=10)
        
        _btn(fr_top, "📂  Buka Citra Asli", self._open_img1, width=20).grid(row=0, column=0, padx=10, pady=10)
        _btn(fr_top, "📂  Buka Citra Kedua", self._open_img2, width=20).grid(row=0, column=1, padx=10, pady=10)
        _btn_secondary(fr_top, "▶  Hitung", self._compute, width=20).grid(row=0, column=2, padx=10, pady=10)
        
        fl = tk.Frame(w, bg=BG)
        fl.pack(fill="both", expand=True, padx=12, pady=4)
        
        f1 = _lframe(fl, "  Citra Asli")
        f1.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.lbl_1 = tk.Label(f1, bg=BG3, fg=FG2, font=F9)
        self.lbl_1.pack(expand=True, fill="both", padx=5, pady=5)

        f2 = _lframe(fl, "  Citra Kedua")
        f2.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.lbl_2 = tk.Label(f2, bg=BG3, fg=FG2, font=F9)
        self.lbl_2.pack(expand=True, fill="both", padx=5, pady=5)

        self.lbl_res = tk.Label(w, bg=BG, fg=SUCCESS, font=F10B, text="MSE: - | PSNR: - dB")
        self.lbl_res.pack(pady=10)

    def _open_img1(self):
        path = filedialog.askopenfilename(parent=self.win)
        if path:
            self.img1 = cv2.imread(path, cv2.IMREAD_COLOR)
            show_cv2(self.lbl_1, self.img1, 300, 300)

    def _open_img2(self):
        path = filedialog.askopenfilename(parent=self.win)
        if path:
            self.img2 = cv2.imread(path, cv2.IMREAD_COLOR)
            show_cv2(self.lbl_2, self.img2, 300, 300)

    def _compute(self):
        if self.img1 is None or self.img2 is None: 
            messagebox.showwarning("Peringatan", "Pilih kedua gambar dulu!", parent=self.win)
            return
        
        import analysis
        try:
            h, w = self.img1.shape[:2]
            img2_res = cv2.resize(self.img2, (w, h))
            psnr, mse = analysis.calculate_psnr_mse(self.img1, img2_res)
            if psnr == float('inf'):
                self.lbl_res.config(text=f"MSE: {mse:.4f} | PSNR: Tak Terhingga (Identik)")
            else:
                self.lbl_res.config(text=f"MSE: {mse:.4f} | PSNR: {psnr:.2f} dB")
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self.win)


# ═══════════════════════════════════════════════════════════════════════════════
# WINDOW — Visual Sensitivity
# ═══════════════════════════════════════════════════════════════════════════════
class VisualSensitivityWindow(_Base):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Uji Sensitivitas Visual", "1280x800")
        self.img_orig = None
        try:
            self.win.state("zoomed")
        except:
            pass
        self._build()

    def _build(self):
        w = self.win

        # ── 1. Title bar (atas) ──────────────────────────────────────────────
        self._title_bar(w, "🦋  Uji Sensitivitas Visual — Butterfly Effect",
                        "Pilih algoritma, parameter kunci, dan selisih presisi untuk menguji kekuatan avalanche effect.")

        # ── 2. Nav row (bawah) — HARUS dipack SEBELUM konten tengah ─────────
        self._nav_row(w)

        # ── 3. Kontrol Panel ────────────────────────────────────────────────
        fr_top = _lframe(w, "  Kontrol Uji Sensitivitas")
        fr_top.pack(fill="x", padx=12, pady=(4, 0))

        # Baris pertama kontrol
        fr_ctrl = tk.Frame(fr_top, bg=BG2)
        fr_ctrl.pack(fill="x", pady=5)
        
        _btn(fr_ctrl, "📂  Buka Citra Asli", self._open_img, width=18).grid(row=0, column=0, padx=12, pady=5)
        
        tk.Label(fr_ctrl, text="Algoritma:", bg=BG2, fg=FG, font=F9).grid(row=0, column=1, padx=(5, 2))
        self.cb_algo = ttk.Combobox(fr_ctrl, values=[ALGO_MS_GAUSS, ALGO_MS_GAUSS_FOG], state="readonly", width=14)
        self.cb_algo.set(ALGO_MS_GAUSS)
        self.cb_algo.grid(row=0, column=2, padx=5)

        tk.Label(fr_ctrl, text="Parameter:", bg=BG2, fg=FG, font=F9).grid(row=0, column=3, padx=(5, 2))
        self.cb_param = ttk.Combobox(fr_ctrl, values=["x₀", "r", "α", "β", "λ"], state="readonly", width=6)
        self.cb_param.set("x₀")
        self.cb_param.grid(row=0, column=4, padx=5)

        tk.Label(fr_ctrl, text="Selisih (+):", bg=BG2, fg=FG, font=F9).grid(row=0, column=5, padx=(5, 2))
        self.cb_diff = ttk.Combobox(fr_ctrl, values=["10^-6", "10^-14", "10^-15", "10^-16"], state="readonly", width=8)
        self.cb_diff.set("10^-15")
        self.cb_diff.grid(row=0, column=6, padx=5)

        _btn(fr_ctrl, "▶ Jalankan", self._compute, width=15).grid(row=0, column=7, padx=(10, 12))

        # Status bar
        self.lbl_status = tk.Label(fr_top, text="Status: Belum ada gambar dimuat.", bg=BG2, fg=FG2, font=F9)
        self.lbl_status.pack(anchor="w", padx=12, pady=(0, 5))

        # ── 4. Kontainer Kotak (Grid 2x2) ───────────────────────────────────
        fl = tk.Frame(w, bg=BG)
        fl.pack(fill="both", expand=True, padx=12, pady=4)
        fl.columnconfigure(0, weight=1, uniform="col")
        fl.columnconfigure(1, weight=1, uniform="col")
        fl.rowconfigure(0, weight=1, uniform="row")
        fl.rowconfigure(1, weight=1, uniform="row")

        # Kotak 1: Citra Asli
        f1 = _lframe(fl, "  1. Citra Asli")
        f1.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.lbl_1 = tk.Label(f1, bg=BG3, text="(belum ada)", fg=FG2, font=F9)
        self.lbl_1.pack(expand=True, fill="both", padx=8, pady=8)

        # Kotak 2: Citra Terenkripsi
        f2 = _lframe(fl, "  2. Citra Terenkripsi")
        f2.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        self.lbl_2 = tk.Label(f2, bg=BG3, text="(belum diproses)", fg=FG2, font=F9)
        self.lbl_2.pack(expand=True, fill="both", padx=8, pady=8)

        # Kotak 3: Dekripsi (Kunci Salah)
        f3 = _lframe(fl, "  3. Dekripsi (Kunci Salah)")
        f3.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        self.lbl_3 = tk.Label(f3, bg=BG3, text="(belum diproses)", fg=FG2, font=F9)
        self.lbl_3.pack(expand=True, fill="both", padx=8, pady=(8, 2))
        self.lbl_k3 = tk.Label(f3, bg=BG, fg=DANGER, font=F9, text="")
        self.lbl_k3.pack(pady=(0,4))

        # Kotak 4: Dekripsi (Kunci Benar)
        f4 = _lframe(fl, "  4. Dekripsi (Kunci Benar)")
        f4.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)
        self.lbl_4 = tk.Label(f4, bg=BG3, text="(belum diproses)", fg=FG2, font=F9)
        self.lbl_4.pack(expand=True, fill="both", padx=8, pady=(8, 2))
        self.lbl_k4 = tk.Label(f4, bg=BG, fg=SUCCESS, font=F9, text="")
        self.lbl_k4.pack(pady=(0,4))

    def _open_img(self):
        path = filedialog.askopenfilename(parent=self.win,
            filetypes=[("Image", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff")])
        if not path: return
        
        self.img_orig = cv2.imread(path, cv2.IMREAD_COLOR)
        if self.img_orig is not None:
            self.lbl_status.config(text=f"Status: Gambar dimuat ({self.img_orig.shape[1]}x{self.img_orig.shape[0]}).", fg=SUCCESS)
            show_cv2(self.lbl_1, self.img_orig, 300, 200)
            for lbl in [self.lbl_2, self.lbl_3, self.lbl_4]:
                lbl.config(image="", text="Klik 'Jalankan'")
            self.lbl_k3.config(text="")
            self.lbl_k4.config(text="")
        else:
            self.lbl_status.config(text="Status: Gagal memuat gambar!", fg=DANGER)

    def _compute(self):
        if self.img_orig is None:
            messagebox.showwarning("Peringatan", "Harap buka citra asli terlebih dahulu!", parent=self.win)
            return
            
        self.lbl_status.config(text="Status: Memproses enkripsi dan dekripsi... (Mohon tunggu)", fg=FG)
        self.win.update()
        
        try:
            h, w = self.img_orig.shape[:2]
            max_dim = 320
            if max(h, w) > max_dim:
                scale = max_dim / float(max(h, w))
                img = cv2.resize(self.img_orig, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            else:
                img = self.img_orig.copy()
            
            algo = self.cb_algo.get()
            param_symbol = self.cb_param.get()
            diff_str = self.cb_diff.get()
            
            # Mapping symbol to dict key
            sym_to_key = {"x₀": "x0", "r": "r", "α": "alpha", "β": "beta", "λ": "lam"}
            param = sym_to_key[param_symbol]
            
            diff_val = 0.0
            if diff_str == "10^-6": diff_val = 1e-6
            elif diff_str == "10^-14": diff_val = 1e-14
            elif diff_str == "10^-15": diff_val = 1e-15
            elif diff_str == "10^-16": diff_val = 1e-16
            
            correct_key = {"x0": 0.3, "r": 3.5, "alpha": 5.8, "beta": 3.1, "lam": 3.5, "acm_iter": 1}
            wrong_key = correct_key.copy()
            wrong_key[param] += diff_val

            encrypted_img, _ = encrypt_image(img, correct_key, algo)
            decrypted_wrong = decrypt_image(encrypted_img, wrong_key, algo)
            decrypted_correct = decrypt_image(encrypted_img, correct_key, algo)
            
            show_cv2(self.lbl_1, self.img_orig, 300, 200)
            show_cv2(self.lbl_2, encrypted_img, 300, 200)
            show_cv2(self.lbl_3, decrypted_wrong, 300, 200)
            self.lbl_k3.config(text=f"[KUNCI SALAH] {param_symbol} = {wrong_key[param]}")
            show_cv2(self.lbl_4, decrypted_correct, 300, 200)
            self.lbl_k4.config(text=f"[KUNCI BENAR] {param_symbol} = {correct_key[param]}")
            
            self.lbl_status.config(text=f"Status: Uji Sensitivitas selesai! Algoritma {algo}, Perubahan {param_symbol} + {diff_str}", fg=SUCCESS)
            
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan:\
{str(e)}", parent=self.win)
            self.lbl_status.config(text="Status: Error saat komputasi.", fg=DANGER)
