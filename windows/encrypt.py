"""
windows/encrypt.py — Jendela Enkripsi & Dekripsi (GUI)
=======================================================
File ini menampilkan dua halaman utama interaktif bagi pengguna:
  1. EncryptionWindow → halaman untuk mengenkripsi gambar
  2. DecryptionWindow → halaman untuk mendekripsi gambar

FUNGSI UTAMA FILE INI:
  1. Menyediakan form input parameter kunci (X0, r, α, β, λ, dll.)
  2. Memungkinkan pengguna memilih gambar dari file browser
  3. Memilih algoritma enkripsi yang ingin digunakan
  4. Menjalankan proses enkripsi/dekripsi dan menampilkan hasilnya
  5. Menyimpan gambar hasil ke folder output
  6. Mencatat operasi ke riwayat (history_manager)

ALGORITMA YANG BISA DIPILIH:
  1. MS Map
  2. Gauss Map
  3. MS Map + Gauss Map  (Sequential)
  4. Gauss MS Map        (Komposisi g∘f)
  5. MS Gauss Map        (Komposisi f∘g)

ALUR KERJA PENGGUNA:
  [Pilih Gambar] → [Atur Parameter] → [Pilih Algoritma] → [Klik Enkripsi]
  → [Lihat Hasil] → [Simpan Gambar Terenkripsi]

CATATAN:
  - File ini bergantung pada encryption.py dan decryption.py untuk proses utama
  - Semua logika matematika ada di chaos_map.py, bukan di sini
  - Tema: Dark Mode Modern
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import time

from gui_utils import (
    _Base, _btn, _btn_secondary, _btn_danger, _lbl, _lframe, _entry,
    BG, BG2, BG3, ACCENT, FG, FG2, F9, F10, F10B, BORDER,
    show_cv2,
)
from chaos_map import (
    generate_keystream, DEFAULT_PARAMS,
    ALGO_MS_GAUSS, ALGO_MS_MAP, ALGO_GAUSS_MAP, ALGO_SEQUENTIAL, ALGO_MS_GAUSS_FOG,
)
from encryption import encrypt_image, save_encrypted
from decryption import decrypt_image, save_decrypted
from windows.analysis_win import AnalisisWindow, NISTWindow
from history_manager import history, HistoryEntry, OP_ENCRYPT, OP_DECRYPT
from analysis import (
    compute_entropy, compute_npcr, compute_uaci, compute_psnr,
)


def _parse_params(evars):
    """Baca dan kembalikan dict parameter dari evars."""
    return {
        "x0":      float(evars["x0"].get()),
        "r":       float(evars["r"].get()),
        "alpha":   float(evars["alpha"].get()),
        "beta":    float(evars["beta"].get()),
        "lam":     float(evars["lam"].get()),
        "skip":    int(evars["skip"].get()),
    }


def _build_param_fields(parent, evars):
    """Bangun grid input parameter chaos."""
    fields = [
        ("X₀  (kondisi awal)",  "x0",    "0.3"),
        ("r   (MS Map)",        "r",     "3.5"),
        ("α   (alpha, Gauss)",  "alpha", "5.8"),
        ("β   (beta, Gauss)",   "beta",  "3.1"),
        ("λ   (lambda, MS)",    "lam",   "3.5"),
        ("Iterasi (skip)",       "skip",  "200"),
    ]
    for ri, (ltext, key, dflt) in enumerate(fields):
        tk.Label(parent, text=ltext, bg=BG2, fg=FG2, font=F9,
                 anchor="e").grid(row=ri, column=0, sticky="e", padx=(10, 4), pady=4)
        e, v = _entry(parent, dflt, width=10)
        e.grid(row=ri, column=1, padx=(4, 10), pady=4)
        evars[key] = v
    return len(fields)


# ═══════════════════════════════════════════════════════════════════════════════
# WINDOW — Enkripsi Citra
# ═══════════════════════════════════════════════════════════════════════════════

class EncryptionWindow(_Base):
    def __init__(self, parent, app):
        algo = getattr(app, "algorithm", None)
        self.algo = algo.get() if algo else ALGO_MS_GAUSS
        super().__init__(parent, app,
                         f"Enkripsi Citra — {self.algo}", "1000x620")
        self.orig_img   = None
        self.enc_img    = None
        self.meta       = None
        self._input_path  = ""    # path gambar yang dibuka
        self._output_path = ""    # path hasil simpan
        self._last_params = {}    # parameter enkripsi terakhir
        self._last_elapsed = 0.0  # waktu enkripsi terakhir
        self._build()

    def _build(self):
        import cv2
        self._cv2 = cv2
        w = self.win

        # Title bar
        self._title_bar(w,
                        f"🔒  Enkripsi Citra Digital",
                        f"Algoritma: {self.algo}")

        body = tk.Frame(w, bg=BG)
        body.pack(fill="both", expand=True, pady=12)

        wrapper = tk.Frame(body, bg=BG)
        wrapper.pack(anchor="n", pady=6)

        # ── Kolom Kiri — Citra Asli ────────────────────────────────────────
        fl = _lframe(wrapper, "  📂  Citra Asli")
        fl.pack(side="left", anchor="n", padx=10)

        img_box_orig = tk.Frame(fl, width=280, height=240, bg=BG3,
                                highlightbackground=BORDER, highlightthickness=1)
        img_box_orig.pack_propagate(False)
        img_box_orig.pack(padx=14, pady=(14, 10))

        self.lbl_orig = tk.Label(img_box_orig, bg=BG3,
                                 text="Belum ada gambar\n\n Klik Open Image",
                                 fg=FG2, font=F9)
        self.lbl_orig.place(relx=0.5, rely=0.5, anchor="center")

        _btn(fl, "📂  Open Image", self._open_image, width=22).pack(padx=14, pady=(4, 14), ipady=2)

        # ── Kolom Tengah — Parameter & Analisis ─────────────────────────────
        fm = _lframe(wrapper, "  ⚙️  Parameter Chaos")
        fm.pack(side="left", anchor="n", padx=10)

        self.evars = {}
        ri = _build_param_fields(fm, self.evars)

        # Checkbox simpan keystream
        self.var_ks = tk.BooleanVar(value=False)
        tk.Checkbutton(fm, text="Simpan Keystream (Excel)",
                       variable=self.var_ks,
                       bg=BG2, fg=FG, font=F9,
                       selectcolor=BG3,
                       activebackground=BG2).grid(
            row=ri, column=0, columnspan=2, pady=(8, 4), padx=10)
        ri += 1

        # Tombol enkripsi utama
        _btn(fm, "🔒  Enkripsi Sekarang", self._process, width=24).grid(
            row=ri, column=0, columnspan=2, pady=(6, 8), padx=12, ipady=4)
        ri += 1

        # Waktu
        tk.Label(fm, text="Waktu Enkripsi :", bg=BG2, fg=FG2, font=F9,
                 anchor="e").grid(row=ri, column=0, sticky="e", padx=(12, 4), pady=4)
        e_t, self.v_time = _entry(fm, "— ms", readonly=True, width=12)
        e_t.grid(row=ri, column=1, padx=(4, 12), pady=4)
        ri += 1

        tk.Frame(fm, bg=BORDER, height=1).grid(
            row=ri, column=0, columnspan=2, sticky="ew", padx=10, pady=8)
        ri += 1

        # Tombol analisis cepat
        _btn_secondary(fm, "📉  Uji Correlation",
                       lambda: self.app.open_correlation(self.orig_img, self.enc_img, None),
                       width=24).grid(row=ri, column=0, columnspan=2, pady=3, padx=12)
        ri += 1
        _btn_secondary(fm, "📊  Analisis Metrik Lengkap", self._analisis, width=24).grid(
            row=ri, column=0, columnspan=2, pady=(3, 12), padx=12)

        # ── Kolom Kanan — Hasil Enkripsi ───────────────────────────────────
        fr = _lframe(wrapper, "  🔒  Citra Hasil Enkripsi")
        fr.pack(side="left", anchor="n", padx=10)

        img_box_enc = tk.Frame(fr, width=280, height=240, bg=BG3,
                               highlightbackground=BORDER, highlightthickness=1)
        img_box_enc.pack_propagate(False)
        img_box_enc.pack(padx=14, pady=(14, 10))

        self.lbl_enc = tk.Label(img_box_enc, bg=BG3,
                                text="Belum dienkripsi\n\nJalankan proses enkripsi",
                                fg=FG2, font=F9)
        self.lbl_enc.place(relx=0.5, rely=0.5, anchor="center")

        _btn(fr, "💾  Save Image",  self._save_enc,   width=22).pack(padx=14, pady=(4, 4), ipady=2)
        _btn_secondary(fr, "← Kembali ke Menu Utama", self.win.destroy, width=22).pack(padx=14, pady=(3, 14))

    def _open_image(self):
        path = filedialog.askopenfilename(
            parent=self.win, title="Pilih Gambar",
            filetypes=[("Image", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff")])
        if not path:
            return
        self.orig_img = self._cv2.imread(path, self._cv2.IMREAD_COLOR)
        if self.orig_img is None:
            messagebox.showerror("Error", "Gagal membuka gambar!", parent=self.win)
            return
        self._input_path = path
        self._output_path = ""
        show_cv2(self.lbl_orig, self.orig_img, 260, 220)

    def _process(self):
        if self.orig_img is None:
            messagebox.showwarning("Peringatan", "Buka gambar dulu!", parent=self.win)
            return
        try:
            params = _parse_params(self.evars)
        except ValueError:
            messagebox.showerror("Error", "Parameter tidak valid!", parent=self.win)
            return

        t0 = time.perf_counter()
        self.enc_img, self.meta = encrypt_image(self.orig_img, params, self.algo)
        elapsed = time.perf_counter() - t0
        elapsed_ms = elapsed * 1000

        self._last_params  = params
        self._last_elapsed = elapsed_ms
        self._output_path  = ""   # reset sampai benar-benar disimpan

        self.v_time.set(f"{elapsed_ms:.2f} ms")
        show_cv2(self.lbl_enc, self.enc_img, 260, 220)
        self.app.last_original  = self.orig_img
        self.app.last_encrypted = self.enc_img

        # ── Hitung metrik & catat ke riwayat ─────────────────────────────
        self._record_history(params, elapsed_ms)

        if self.var_ks.get():
            self._save_keystream(params)

        messagebox.showinfo("Selesai",
                            f"Enkripsi berhasil!\n"
                            f"Algoritma: {self.algo}\n"
                            f"Waktu: {elapsed_ms:.2f} ms",
                            parent=self.win)

    def _record_history(self, params, elapsed_ms):
        """Hitung metrik ringan & tambah entri ke history manager."""
        metrics = {}
        try:
            metrics["entropy_original"]  = float(compute_entropy(self.orig_img))
            metrics["entropy_encrypted"] = float(compute_entropy(self.enc_img))
        except Exception:
            pass
        try:
            metrics["npcr"] = float(compute_npcr(self.orig_img, self.enc_img))
            metrics["uaci"] = float(compute_uaci(self.orig_img, self.enc_img))
        except Exception:
            pass
        entry = HistoryEntry(
            operation   = OP_ENCRYPT,
            algorithm   = self.algo,
            params      = params,
            image_shape = self.orig_img.shape,
            elapsed_ms  = elapsed_ms,
            input_path  = self._input_path,
            output_path = self._output_path,
            metrics     = metrics,
        )
        history.add(entry)
        self._last_history_entry = entry

    def _save_enc(self):
        if self.enc_img is None:
            messagebox.showwarning("Peringatan", "Belum ada hasil enkripsi!", parent=self.win)
            return
        path = filedialog.asksaveasfilename(
            parent=self.win, defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")])
        if path:
            save_encrypted(self.enc_img, path)
            self._output_path = path
            # Update output_path di entri riwayat terakhir
            if hasattr(self, "_last_history_entry") and self._last_history_entry:
                self._last_history_entry.output_path = path
            messagebox.showinfo("Berhasil", f"Gambar disimpan:\n{path}", parent=self.win)

    def _save_keystream(self, params):
        try:
            import openpyxl
        except ImportError:
            messagebox.showwarning("Info", "openpyxl belum terinstall.",
                                   parent=self.win)
            return
        ks = generate_keystream((100,), params, self.algo).flatten()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Keystream"
        ws.append(["Index", "Value"])
        for i, v in enumerate(ks):
            ws.append([i + 1, int(v)])
        path = filedialog.asksaveasfilename(
            parent=self.win, defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")])
        if path:
            wb.save(path)
            messagebox.showinfo("Berhasil", f"Keystream disimpan:\n{path}", parent=self.win)

    def _analisis(self):
        AnalisisWindow(self.win, self.app, self.orig_img, self.enc_img, None, mode="encrypt")


# ═══════════════════════════════════════════════════════════════════════════════
# WINDOW — Dekripsi Citra
# ═══════════════════════════════════════════════════════════════════════════════

class DecryptionWindow(_Base):
    def __init__(self, parent, app):
        algo = getattr(app, "algorithm", None)
        self.algo = algo.get() if algo else ALGO_MS_GAUSS
        super().__init__(parent, app,
                         f"Dekripsi Citra — {self.algo}", "1000x620")
        self.enc_img  = None
        self.dec_img  = None
        self._input_path  = ""
        self._output_path = ""
        self._last_history_entry = None
        self._build()

    def _build(self):
        w = self.win
        self._title_bar(w,
                        f"🔓  Dekripsi Citra Digital",
                        f"Algoritma: {self.algo}  (gunakan parameter SAMA saat enkripsi)")

        body = tk.Frame(w, bg=BG)
        body.pack(fill="both", expand=True, pady=12)

        wrapper = tk.Frame(body, bg=BG)
        wrapper.pack(anchor="n", pady=6)

        # ── Kolom Kiri — Citra Terenkripsi ────────────────────────────────
        fl = _lframe(wrapper, "  🔒  Citra Terenkripsi")
        fl.pack(side="left", anchor="n", padx=10)

        img_box_enc = tk.Frame(fl, width=280, height=240, bg=BG3,
                               highlightbackground=BORDER, highlightthickness=1)
        img_box_enc.pack_propagate(False)
        img_box_enc.pack(padx=14, pady=(14, 10))

        self.lbl_enc = tk.Label(img_box_enc, bg=BG3,
                                text="Belum ada gambar\n\n Klik Open Image",
                                fg=FG2, font=F9)
        self.lbl_enc.place(relx=0.5, rely=0.5, anchor="center")

        _btn(fl, "📂  Open Image", self._open_image, width=22).pack(padx=14, pady=(4, 14), ipady=2)

        # ── Kolom Tengah — Parameter ───────────────────────────────────────
        fm = _lframe(wrapper, "  ⚙️  Parameter Chaos")
        fm.pack(side="left", anchor="n", padx=10)

        self.evars = {}
        ri = _build_param_fields(fm, self.evars)

        _btn(fm, "🔓  Dekripsi Sekarang", self._process, width=24,
             color="#1D4ED8").grid(row=ri, column=0, columnspan=2, pady=(10, 8), padx=12, ipady=4)
        ri += 1

        tk.Label(fm, text="Waktu Dekripsi :", bg=BG2, fg=FG2, font=F9,
                 anchor="e").grid(row=ri, column=0, sticky="e", padx=(12, 4), pady=4)
        e_t, self.v_time = _entry(fm, "— ms", readonly=True, width=12)
        e_t.grid(row=ri, column=1, padx=(4, 12), pady=4)
        ri += 1

        tk.Frame(fm, bg=BORDER, height=1).grid(
            row=ri, column=0, columnspan=2, sticky="ew", padx=10, pady=8)
        ri += 1

        # ── Kolom Kanan — Hasil Dekripsi ───────────────────────────────────
        fr = _lframe(wrapper, "  🔓  Citra Hasil Dekripsi")
        fr.pack(side="left", anchor="n", padx=10)

        img_box_dec = tk.Frame(fr, width=280, height=240, bg=BG3,
                               highlightbackground=BORDER, highlightthickness=1)
        img_box_dec.pack_propagate(False)
        img_box_dec.pack(padx=14, pady=(14, 10))

        self.lbl_dec = tk.Label(img_box_dec, bg=BG3,
                                text="Belum didekripsi\n\nJalankan proses dekripsi",
                                fg=FG2, font=F9)
        self.lbl_dec.place(relx=0.5, rely=0.5, anchor="center")

        _btn(fr, "💾  Save Image",  self._save_dec,    width=22).pack(padx=14, pady=(4, 4), ipady=2)
        _btn_secondary(fr, "← Kembali ke Menu Utama", self.win.destroy, width=22).pack(padx=14, pady=(3, 14))

    def _open_image(self):
        import cv2
        path = filedialog.askopenfilename(
            parent=self.win, title="Pilih Gambar Terenkripsi",
            filetypes=[("Image", "*.png *.jpg *.jpeg *.bmp")])
        if not path:
            return
        self.enc_img = cv2.imread(path, cv2.IMREAD_COLOR)
        if self.enc_img is None:
            messagebox.showerror("Error", "Gagal membuka gambar!", parent=self.win)
            return
        self._input_path = path
        self._output_path = ""
        show_cv2(self.lbl_enc, self.enc_img, 260, 220)

    def _process(self):
        if self.enc_img is None:
            messagebox.showwarning("Peringatan", "Buka gambar dulu!", parent=self.win)
            return
        try:
            params = _parse_params(self.evars)
        except ValueError:
            messagebox.showerror("Error", "Parameter tidak valid!", parent=self.win)
            return

        t0 = time.perf_counter()
        self.dec_img = decrypt_image(self.enc_img, params, self.algo)
        elapsed = time.perf_counter() - t0
        elapsed_ms = elapsed * 1000

        self.v_time.set(f"{elapsed_ms:.2f} ms")
        show_cv2(self.lbl_dec, self.dec_img, 260, 220)
        self.app.last_decrypted = self.dec_img

        # ── Hitung metrik & catat ke riwayat ─────────────────────────────
        metrics = {}
        try:
            metrics["entropy_encrypted"] = float(compute_entropy(self.enc_img))
            metrics["entropy_decrypted"] = float(compute_entropy(self.dec_img))
        except Exception:
            pass
        try:
            psnr_val = compute_psnr(self.enc_img, self.dec_img)
            metrics["psnr"] = float(psnr_val)
        except Exception:
            pass

        entry = HistoryEntry(
            operation   = OP_DECRYPT,
            algorithm   = self.algo,
            params      = params,
            image_shape = self.enc_img.shape,
            elapsed_ms  = elapsed_ms,
            input_path  = self._input_path,
            output_path = self._output_path,
            metrics     = metrics,
        )
        history.add(entry)
        self._last_history_entry = entry

        messagebox.showinfo("Selesai",
                            f"Dekripsi berhasil!\n"
                            f"Algoritma: {self.algo}\n"
                            f"Waktu: {elapsed_ms:.2f} ms",
                            parent=self.win)

    def _save_dec(self):
        if self.dec_img is None:
            messagebox.showwarning("Peringatan", "Belum ada hasil dekripsi!", parent=self.win)
            return
        path = filedialog.asksaveasfilename(
            parent=self.win, defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")])
        if path:
            save_decrypted(self.dec_img, path)
            self._output_path = path
            if self._last_history_entry:
                self._last_history_entry.output_path = path
            messagebox.showinfo("Berhasil", f"Gambar disimpan:\n{path}", parent=self.win)


