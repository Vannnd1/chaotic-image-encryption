"""
windows/analysis_win.py — Jendela Analisis Keamanan Enkripsi (GUI)
===================================================================
File ini menampilkan halaman-halaman analisis statistik dan kriptografis
dari hasil enkripsi gambar secara visual dan interaktif.

HALAMAN (WINDOW) YANG ADA:
  1. AnalisisWindow   → halaman utama analisis metrik lengkap
                         menampilkan: entropi, korelasi, NPCR, UACI,
                         Chi-Square, NIST, Key Space, sensitivitas kunci
  2. NISTWindow       → halaman khusus hasil uji NIST SP800-22
                         (Monobit Test & Runs Test)
  3. CorrelationWindow → halaman visualisasi grafik korelasi piksel
                         (arah horizontal, vertikal, diagonal)

FUNGSI UTAMA FILE INI:
  1. Menerima gambar asli dan gambar terenkripsi sebagai input
  2. Memanggil fungsi analisis dari analysis.py
  3. Menampilkan hasil metrik dalam bentuk tabel dan grafik
  4. Memungkinkan pengguna menyimpan hasil analisis sebagai gambar/CSV

CATATAN:
  - File ini hanya menampilkan hasil, semua perhitungan ada di analysis.py
  - Tema: Dark Mode Modern
"""

import tkinter as tk
from tkinter import messagebox
import numpy as np
import cv2
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui_utils import (
    _Base, _btn, _btn_secondary, _btn_danger, _lbl, _lframe, _entry,
    BG, BG2, BG3, ACCENT, FG, FG2, BORDER, SUCCESS, DANGER,
    F9, F10, F10B,
)
from analysis import (
    full_analysis, compute_entropy,
    compute_lyapunov_exponent, run_nist_tests,
)
from chaos_map import generate_keystream

# Matplotlib light style
PLOT_BG   = "#F8FAFC"
PLOT_FACE = "#FFFFFF"
PLOT_GRID = "#E2E8F0"
PLOT_TEXT = "#0F172A"


# ═══════════════════════════════════════════════════════════════════════════════
# WINDOW ANALISIS LENGKAP
# ═══════════════════════════════════════════════════════════════════════════════

class AnalisisWindow(_Base):
    def __init__(self, parent, app, original, encrypted, decrypted, mode="encrypt"):
        super().__init__(parent, app, "Analisis Lengkap Enkripsi", "950x460" if mode == "encrypt" else "450x300")
        try:
            self.win.state("normal")  # Jendela ini tidak perlu full-screen
        except Exception:
            pass
        self.original  = original
        self.encrypted = encrypted
        self.decrypted = decrypted
        self.mode = mode
        self._build()

    def _build(self):
        w = self.win
        title_txt = "📊  Analisis Lengkap Enkripsi" if self.mode == "encrypt" else "📊  Analisis Pemulihan Dekripsi"
        sub_txt = "Statistik · Diferensial · Kualitas" if self.mode == "encrypt" else "Kualitas · Entropy"
        self._title_bar(w, title_txt, sub_txt)

        if self.original is None or (self.mode == "encrypt" and self.encrypted is None) or (self.mode == "decrypt" and self.decrypted is None):
            # Mode "KOSONG" untuk keperluan screenshot UI (Bab 3)
            m = {
                'entropy_original': 0.0, 'entropy_encrypted': 0.0, 'entropy_decrypted': 0.0,
                'corr_orig_H': 0.0, 'corr_orig_V': 0.0, 'corr_orig_D': 0.0,
                'corr_enc_H': 0.0, 'corr_enc_V': 0.0, 'corr_enc_D': 0.0,
                'mse_orig_enc': 0.0, 'psnr_orig_enc': 0.0, 'mse_orig_dec': 0.0, 'psnr_orig_dec': 0.0,
                'npcr': 0.0, 'uaci': 0.0,
                'chi2_value': 0.0, 'chi2_critical': 0.0, 'chi2_uniform': False
            }
        else:
            orig_for_analysis = self.original
            enc = self.encrypted if self.encrypted is not None else orig_for_analysis
            dec = self.decrypted if self.decrypted is not None else orig_for_analysis
            try:
                m = full_analysis(orig_for_analysis, enc, dec)
            except Exception as ex:
                tk.Label(w, text=f"Error analisis: {ex}",
                         bg=BG, fg=DANGER, font=F10).pack(pady=20)
                return

        body = tk.Frame(w, bg=BG)
        body.pack(fill="both", expand=True, padx=14, pady=8)

        if self.mode == "encrypt":
            chi_ok = "✓  Seragam" if m['chi2_uniform'] else "✗  Tidak seragam"
            if self.original is None or self.encrypted is None:
                chi_ok = "—"
            
            # Kolom Kiri
            left_col = tk.Frame(body, bg=BG)
            left_col.pack(side="left", fill="both", expand=True, padx=(0, 6))

            # Kolom Kanan
            right_col = tk.Frame(body, bg=BG)
            right_col.pack(side="left", fill="both", expand=True, padx=(6, 0))

            # Kolom 1: Statistik (Kiri)
            f1 = _lframe(left_col, "  Uji Statistik")
            f1.pack(side="top", fill="x", pady=4)
            is_rgb = (self.encrypted is not None and len(self.encrypted.shape) == 3 and self.encrypted.shape[2] == 3)
            chi_label = f"R:{m['chi2_r']:.2f} G:{m['chi2_g']:.2f} B:{m['chi2_b']:.2f}" if is_rgb else f"{m['chi2_value']:.2f}"

            rows_stat = [
                ("Entropy Citra Asli", f"{m['entropy_original']:.6f} bit", None),
                ("Entropy Citra Enkripsi",  f"{m['entropy_encrypted']:.6f} bit", "ideal ≈ 8.0"),
                ("Korelasi Asli (Horizontal)",  f"{m['corr_orig_H']:+.6f}", "ideal ≈ 1"),
                ("Korelasi Asli (Vertikal)",  f"{m['corr_orig_V']:+.6f}", "ideal ≈ 1"),
                ("Korelasi Asli (Diagonal)",  f"{m['corr_orig_D']:+.6f}", "ideal ≈ 1"),
                ("Korelasi Enkripsi (Horizontal)",   f"{m['corr_enc_H']:+.6f}", "ideal ≈ 0"),
                ("Korelasi Enkripsi (Vertikal)",   f"{m['corr_enc_V']:+.6f}", "ideal ≈ 0"),
                ("Korelasi Enkripsi (Diagonal)",   f"{m['corr_enc_D']:+.6f}", "ideal ≈ 0"),
                ("Chi-Square Citra Enkripsi",     chi_label, f"kritis: {m['chi2_critical']:.2f}"),
                ("Distribusi Nilai Piksel",   chi_ok, None),
            ]
            self._build_rows(f1, rows_stat)

            # Kolom 2: Diferensial (Kanan Atas)
            f2 = _lframe(right_col, "  Uji Diferensial")
            f2.pack(side="top", fill="x", pady=(4, 6))
            rows_diff = [
                ("NPCR (Sensitivitas Piksel)", f"{m['npcr']:.4f} %", "ideal ≥ 99.6%"),
                ("UACI (Intensitas Berubah)", f"{m['uaci']:.4f} %", "ideal ≈ 33.46%"),
            ]
            self._build_rows(f2, rows_diff)

            # Kolom 3: Kualitas Enkripsi (Kanan Bawah)
            f3 = _lframe(right_col, "  Kualitas Enkripsi")
            f3.pack(side="top", fill="x", pady=(6, 4))
            rows_qual = [
                ("MSE (Asli vs Enkripsi)",  f"{m['mse_orig_enc']:.4f}",  None),
                ("PSNR (Asli vs Enkripsi)", f"{m['psnr_orig_enc']:.4f} dB", None),
            ]
            self._build_rows(f3, rows_qual)

        else: # decrypt
            psnr_dec = m['psnr_orig_dec']
            psnr_dec_str = "∞ dB" if psnr_dec == float('inf') else f"{psnr_dec:.4f} dB"
            
            f1 = _lframe(body, "  Kualitas & Dekripsi")
            f1.pack(fill="both", expand=True, padx=10, pady=4)
            rows_dec = [
                ("Entropy Citra Dekripsi",     f"{m['entropy_decrypted']:.6f} bit", None),
                ("MSE (Asli vs Dekripsi)",  f"{m['mse_orig_dec']:.6f}",  "ideal = 0"),
                ("PSNR (Asli vs Dekripsi)", psnr_dec_str,                "ideal = ∞"),
            ]
            self._build_rows(f1, rows_dec)

        # Nav
        _btn(w, "Tutup", self.win.destroy, width=12).pack(pady=10)

    def _build_rows(self, parent, rows):
        for ri, (label, val, hint) in enumerate(rows):
            tk.Label(parent, text=label + " :", bg=BG2, fg=FG2, font=F9,
                     anchor="e").grid(row=ri, column=0, sticky="e",
                                      padx=(10, 4), pady=3)
            e, _ = _entry(parent, val, readonly=True, width=22)
            e.grid(row=ri, column=1, padx=(4, 6), pady=3)
            if hint:
                tk.Label(parent, text=hint, bg=BG2, fg=FG2, font=F9,
                         anchor="w").grid(row=ri, column=2, sticky="w",
                                          padx=(2, 8))


# ═══════════════════════════════════════════════════════════════════════════════
# WINDOW — Uji NIST
# ═══════════════════════════════════════════════════════════════════════════════

class NISTWindow(_Base):
    # Label tampilan dan deskripsi fokus untuk setiap kunci hasil run_nist_tests
    NIST_LABELS = [
        ("monobit",                   "1. Frequency (Monobit)",           "Proporsi keseluruhan bit '0' dan '1' di seluruh deret"),
        ("block_frequency",           "2. Block Frequency",               "Distribusi rasio bit di dalam blok-blok panjang tertentu"),
        ("runs",                      "3. Runs Test",                     "Frekuensi run (urutan bit identik berurutan) di seluruh deret"),
        ("longest_run",               "4. Longest Run of Ones",           "Panjang run bit '1' terpanjang dalam blok-blok yang ditentukan"),
        ("matrix_rank",               "5. Binary Matrix Rank",            "Dependensi linier di antara sub-string biner berurutan"),
        ("dft",                       "6. DFT (Spectral)",                "Deteksi puncak periodik melalui Transformasi Fourier Diskrit"),
        ("non_overlapping",           "7. Non-overlapping Template",      "Jumlah kemunculan pola target yang tidak saling tumpang tindih"),
        ("overlapping",               "8. Overlapping Template",          "Jumlah kemunculan pola target (template) yang saling tumpang tindih"),
        ("universal",                 "9. Maurer's Universal",            "Ukuran komprehensibilitas dan jarak antar pola yang cocok"),
        ("linear_complexity",         "10. Linear Complexity",            "Panjang ekivalen dari Linear Feedback Shift Register (LFSR)"),
        ("serial",                    "11. Serial Test",                  "Frekuensi kemunculan pola m-bit yang saling tumpang tindih"),
        ("approx_entropy",            "12. Approximate Entropy",          "Perbandingan frekuensi pola m-bit dengan pola (m+1)-bit"),
        ("cumulative_sums",           "13. Cumulative Sums",              "Ekskursi maksimal dari random walk kumulatif terhadap nol"),
        ("random_excursions",         "14. Random Excursions",            "Jumlah siklus dan frekuensi kunjungan status dalam random walk"),
        ("random_excursions_variant", "15. Excursions Variant",           "Distribusi total kunjungan ke berbagai status dalam ekskursi acak"),
    ]

    def __init__(self, parent, app, orig_img=None, enc_img=None, params=None):
        super().__init__(parent, app, "Uji Keacakan NIST SP 800-22 (15 Uji)", "1150x700")
        try:
            self.win.state("zoomed")
        except Exception:
            pass
        self.orig_img = orig_img
        self.enc_img  = enc_img
        self.default_params = params
        self.last_results = None
        self._build()

    def _build(self):
        w = self.win
        algo_name = self.app.algorithm.get() if hasattr(self.app, "algorithm") else "GoF (Gauss MS Map)"
        self._title_bar(w, f"🔬  Uji Keacakan NIST SP 800-22 — [{algo_name}]",
                        "15 Statistical Tests  ·  Syarat Lulus: P-value > 0.01  ·  1.000.000 Bit (Standar NIST)")

        body = tk.Frame(w, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=8)

        # ── Panel kanan: parameter + tombol ────────────────────────────────────
        fr = _lframe(body, "  Parameter Chaos & Algoritma")
        fr.pack(side="right", fill="y", padx=(10, 0), pady=4)

        # Indikator Algoritma Aktif
        algo_box = tk.Frame(fr, bg=BG3, pady=6, padx=8)
        algo_box.pack(fill="x", padx=10, pady=(6, 6))
        tk.Label(algo_box, text="⚙️ Algoritma Diuji:", bg=BG3, fg=FG2, font=F9).pack()
        tk.Label(algo_box, text=algo_name, bg=BG3, fg=ACCENT, font=F10B, wraplength=180, justify="center").pack(pady=(2, 0))

        fields = [
            ("X\u2080",         "x0",    "0.3"),
            ("r",               "r",     "3.5"),
            ("\u03b1 (alpha)",  "alpha", "5.8"),
            ("\u03b2 (beta)",   "beta",  "3.1"),
            ("\u03bb (lambda)", "lam",   "3.5"),
            ("Skip iterasi",    "skip",  "200"),
        ]
        self.evars = {}
        for ri, (ltext, key, dflt) in enumerate(fields):
            row = tk.Frame(fr, bg=BG2)
            row.pack(fill="x", padx=10, pady=3)
            tk.Label(row, text=ltext + ":", bg=BG2, fg=FG2, font=F9).pack(side="left")
            if self.default_params and key in self.default_params:
                dflt = str(self.default_params[key])
            e, v = _entry(row, dflt, width=11)
            e.pack(side="right", padx=6)
            self.evars[key] = v

        tk.Frame(fr, bg=BORDER, height=1).pack(fill="x", padx=8, pady=8)

        self.lbl_summary = tk.Label(fr, text="—", bg=BG2, fg=FG, font=F10B,
                                    wraplength=180, justify="center")
        self.lbl_summary.pack(padx=10, pady=4)

        self.lbl_prog = tk.Label(fr, text="", bg=BG2, fg=FG2, font=F9)
        self.lbl_prog.pack(padx=10, pady=2)

        _btn(fr, "\u25b6  Jalankan 15 Uji", self._run, width=20).pack(padx=10, pady=(8, 4))
        _btn_secondary(fr, "💾  Export CSV", self._export_csv, width=20).pack(padx=10, pady=4)
        _btn_secondary(fr, "← Kembali", self.win.destroy, width=20).pack(padx=10, pady=(4, 8))

        # ── Panel kiri: tabel hasil (Desain IMK Ergonomis & Seimbang) ─────────
        fl = _lframe(body, f"  Hasil 15 Uji NIST SP 800-22 — Algoritma: {algo_name}")
        fl.pack(side="left", fill="both", expand=True, pady=4)

        # Top Info Bar (Spesifikasi Pengujian, mengisi lebar penuh di atas tabel)
        info_bar = tk.Frame(fl, bg=BG3, pady=8, padx=12)
        info_bar.pack(side="top", fill="x", padx=10, pady=(8, 4))
        tk.Label(info_bar, text="💡 Spesifikasi Standard NIST:", bg=BG3, fg=FG, font=F10B).pack(side="left", padx=(2, 8))
        tk.Label(info_bar, text="Menguji 1.000.000 Bit (125 KB) deret biner chaos. Syarat kelulusan standar internasional: P-value > 0.01 (α = 1%).", 
                 bg=BG3, fg="#10B981", font=F9).pack(side="left")

        # Scrollable Area Container
        tbl_container = tk.Frame(fl, bg=BG2, bd=1, relief="solid")
        tbl_container.pack(side="top", fill="both", expand=True, padx=10, pady=(4, 10))

        canvas = tk.Canvas(tbl_container, bg=BG2, highlightthickness=0)
        sb = tk.Scrollbar(tbl_container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.tbl_frame = tk.Frame(canvas, bg=BG2)
        win_id = canvas.create_window((0, 0), window=self.tbl_frame, anchor="nw")

        # Dynamic Canvas Resizing agar kolom menempati 100% lebar layar tanpa rongga kosong
        def _on_canvas_resize(event):
            canvas.itemconfig(win_id, width=event.width)
        canvas.bind("<Configure>", _on_canvas_resize)
        self.tbl_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Proporsi kolom grid:
        # Col 0: No (50px), Col 1: Nama Uji (weight=2), Col 2: Fokus / Kriteria Uji (weight=3), Col 3: P-value (weight=1), Col 4: Status (weight=1)
        self.tbl_frame.columnconfigure(0, weight=0, minsize=45)
        self.tbl_frame.columnconfigure(1, weight=2, minsize=210)
        self.tbl_frame.columnconfigure(2, weight=3, minsize=320)
        self.tbl_frame.columnconfigure(3, weight=1, minsize=120)
        self.tbl_frame.columnconfigure(4, weight=1, minsize=140)

        # Header Tabel (Row 0) - Bergabung dalam Grid Tabel untuk perataan 100% akurat
        headers = [("No", "center"), ("Nama Uji NIST SP 800-22", "w"), 
                   ("Fokus / Kriteria Pengujian", "w"), ("P-value", "center"), ("Status Pengujian", "center")]
        for col, (txt, align) in enumerate(headers):
            cell = tk.Frame(self.tbl_frame, bg=BG3, pady=8, padx=8)
            cell.grid(row=0, column=col, sticky="nsew", padx=1, pady=1)
            tk.Label(cell, text=txt, bg=BG3, fg=ACCENT, font=F10B, anchor=align).pack(fill="x")

        # Buat 15 baris data uji
        self.row_vars = {}   # key → (pval_var, status_var, pval_label, status_label)
        for i, (key, label, desc) in enumerate(self.NIST_LABELS, start=1):
            bg_ = BG2 if i % 2 == 1 else BG3
            no_str = f"{i:02d}"
            nama_clean = label.split(". ", 1)[-1] if ". " in label else label

            # Col 0: No
            c0 = tk.Frame(self.tbl_frame, bg=bg_, pady=6, padx=6)
            c0.grid(row=i, column=0, sticky="nsew", padx=1, pady=1)
            tk.Label(c0, text=no_str, bg=bg_, fg=FG2, font=F9, anchor="center").pack(fill="both", expand=True)

            # Col 1: Nama Uji
            c1 = tk.Frame(self.tbl_frame, bg=bg_, pady=6, padx=10)
            c1.grid(row=i, column=1, sticky="nsew", padx=1, pady=1)
            tk.Label(c1, text=nama_clean, bg=bg_, fg=FG, font=F10B, anchor="w").pack(fill="both", expand=True)

            # Col 2: Deskripsi / Fokus Uji (Mengisi ruang tengah dengan konteks edukatif)
            c2 = tk.Frame(self.tbl_frame, bg=bg_, pady=6, padx=10)
            c2.grid(row=i, column=2, sticky="nsew", padx=1, pady=1)
            tk.Label(c2, text=desc, bg=bg_, fg=FG2, font=F9, anchor="w").pack(fill="both", expand=True)

            # Col 3: P-value
            c3 = tk.Frame(self.tbl_frame, bg=bg_, pady=6, padx=8)
            c3.grid(row=i, column=3, sticky="nsew", padx=1, pady=1)
            pv = tk.StringVar(value="—")
            pl = tk.Label(c3, textvariable=pv, bg=bg_, fg=FG2, font=F9, anchor="center")
            pl.pack(fill="both", expand=True)

            # Col 4: Status
            c4 = tk.Frame(self.tbl_frame, bg=bg_, pady=6, padx=8)
            c4.grid(row=i, column=4, sticky="nsew", padx=1, pady=1)
            sv = tk.StringVar(value="—")
            sl = tk.Label(c4, textvariable=sv, bg=bg_, fg=FG2, font=F10B, anchor="center")
            sl.pack(fill="both", expand=True)

            self.row_vars[key] = (pv, sv, pl, sl)

    def _run(self):
        try:
            params = {
                "x0":    float(self.evars["x0"].get()),
                "r":     float(self.evars["r"].get()),
                "alpha": float(self.evars["alpha"].get()),
                "beta":  float(self.evars["beta"].get()),
                "lam":   float(self.evars["lam"].get()),
                "skip":  int(self.evars["skip"].get()),
            }
        except ValueError:
            messagebox.showerror("Error", "Parameter tidak valid!", parent=self.win)
            return

        self.lbl_summary.config(text="Sedang menghitung...", fg=FG2)
        self.lbl_prog.config(text="Mohon tunggu ~15 detik...")
        self.win.update()

        try:
            results = run_nist_tests(params, algo=self.app.algorithm.get()
                                     if hasattr(self.app, "algorithm") else None)
            self.last_results = results
        except Exception as ex:
            messagebox.showerror("Error", f"Terjadi kesalahan:\n{ex}", parent=self.win)
            self.lbl_summary.config(text="Error!", fg=DANGER)
            return

        # Isi tabel
        lulus = 0
        for key, label, desc in self.NIST_LABELS:
            pv, sv, pl, sl = self.row_vars[key]
            if key not in results:
                pv.set("N/A"); sv.set("—")
                continue
            r = results[key]
            pv.set(f"{r['p_value']:.6f}")
            if r["passed"]:
                sv.set("✔ LULUS")
                sl.config(fg="#10B981")
                pl.config(fg="#10B981")
                lulus += 1
            else:
                sv.set("✘ GAGAL")
                sl.config(fg="#EF4444")
                pl.config(fg="#EF4444")

        total = len(self.NIST_LABELS)
        self.lbl_summary.config(
            text=f"{lulus} / {total} Uji LULUS",
            fg="#10B981" if lulus == total else "#F59E0B" if lulus >= total // 2 else "#EF4444"
        )
        self.lbl_prog.config(text="Selesai!")

    def _export_csv(self):
        if not getattr(self, "last_results", None):
            messagebox.showwarning("Peringatan", "Jalankan pengujian terlebih dahulu sebelum menyimpan!", parent=self.win)
            return

        from tkinter import filedialog
        import csv
        import datetime

        algo_name = self.app.algorithm.get() if hasattr(self.app, "algorithm") else "GoF"
        safe_algo = algo_name.replace(" ", "_").replace("(", "").replace(")", "").replace("∘", "_")
        default_filename = f"Hasil_NIST_{safe_algo}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        filepath = filedialog.asksaveasfilename(
            parent=self.win,
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv"), ("All files", "*.*")],
            initialfile=default_filename,
            title="Simpan Hasil Uji NIST ke CSV"
        )

        if not filepath:
            return

        try:
            with open(filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["=== LAPORAN HASIL UJI KEACAKAN NIST SP 800-22 ==="])
                writer.writerow(["Algoritma Diuji", algo_name])
                writer.writerow(["Waktu Pengujian", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                writer.writerow(["Panjang Data", "125.000 Byte (1.000.000 Bit)"])
                writer.writerow([])
                writer.writerow(["Parameter Chaos Digunakan:"])
                for k, v in self.evars.items():
                    writer.writerow([f"  - {k}", v.get()])
                writer.writerow([])
                writer.writerow(["No", "Nama Uji NIST SP 800-22", "P-Value", "Status", "Fokus Pengujian / Keterangan"])

                lulus = 0
                total = len(self.NIST_LABELS)
                for idx, (key, label, desc) in enumerate(self.NIST_LABELS, 1):
                    nama_uji = label.split('. ', 1)[-1] if '. ' in label else label
                    if key in self.last_results:
                        r = self.last_results[key]
                        p_val = f"{r['p_value']:.6f}"
                        status = "LULUS" if r["passed"] else "GAGAL"
                        if r["passed"]:
                            lulus += 1
                        ket = r.get("conclusion", desc)
                        writer.writerow([idx, nama_uji, p_val, status, ket])
                    else:
                        writer.writerow([idx, nama_uji, "N/A", "-", desc])

                writer.writerow([])
                writer.writerow(["Ringkasan Hasil", f"{lulus} dari {total} Uji LULUS (P-value > 0.01)"])

            messagebox.showinfo("Sukses", f"Hasil uji NIST berhasil disimpan ke:\n{filepath}", parent=self.win)
        except Exception as ex:
            messagebox.showerror("Error", f"Gagal menyimpan file CSV:\n{ex}", parent=self.win)


# ═══════════════════════════════════════════════════════════════════════════════
# WINDOW — Koefisien Korelasi
# ═══════════════════════════════════════════════════════════════════════════════

class CorrelationWindow(_Base):
    PANELS = [
        ("Asli (Horizontal)",  "original",  "horizontal"),
        ("Asli (Vertikal)",    "original",  "vertical"),
        ("Asli (Diagonal)",    "original",  "diagonal"),
        ("Enkripsi (Horizontal)", "encrypted", "horizontal"),
        ("Enkripsi (Vertikal)",   "encrypted", "vertical"),
        ("Enkripsi (Diagonal)",   "encrypted", "diagonal"),
    ]

    def __init__(self, parent, app, original=None, encrypted=None, decrypted=None):
        super().__init__(parent, app, "Analisis Koefisien Korelasi", "1080x520")
        self.imgs = {"original": original, "encrypted": encrypted, "decrypted": decrypted}
        self._build()

    def _build(self):
        w = self.win
        self._title_bar(w, "📉  Analisis Koefisien Korelasi",
                        "Scatter plot berdasarkan sampel acak N-pasang piksel bertetangga — ideal r ≈ 0 untuk citra terenkripsi")

        body = tk.Frame(w, bg=BG)
        body.pack(fill="both", expand=True, padx=8, pady=6)

        # Kontrol kanan (dideklarasikan dan di-pack lebih dulu agar tidak tertimpa/terdorong oleh grafik)
        ctrl = tk.Frame(body, bg=BG)
        ctrl.pack(side="right", fill="y", padx=8)

        fctrl = _lframe(ctrl, "  Kontrol")
        fctrl.pack(fill="x", ipady=4)
        tk.Label(fctrl, text="Jumlah Sampel:", bg=BG2, fg=FG2, font=F9).pack(
            pady=(10, 2), padx=10, anchor="w")

        # Grid 3×3
        grid_fr = tk.Frame(body, bg=BG)
        grid_fr.pack(side="left", fill="both", expand=True)

        self.panel_figs = []
        colors = {
            "original":  "#4F8EF7",   # biru
            "encrypted": "#F87171",   # merah
            "decrypted": "#34D399",   # hijau
        }
        for idx, (title, img_key, direction) in enumerate(self.PANELS):
            row_g, col_g = divmod(idx, 3)
            fr = _lframe(grid_fr, f"  {title}")
            fr.grid(row=row_g, column=col_g, padx=3, pady=3, sticky="nsew")
            grid_fr.columnconfigure(col_g, weight=1)
            grid_fr.rowconfigure(row_g, weight=1)

            fig = plt.Figure()
            fig.patch.set_facecolor(PLOT_BG)
            ax  = fig.add_subplot(111)
            ax.set_facecolor(PLOT_FACE)
            ax.set_xticks([])
            ax.set_yticks([])
            for sp in ax.spines.values(): sp.set_edgecolor(BORDER)
            ax.text(0.5, 0.5, "Belum dianalisis", color=FG2, fontsize=8,
                    ha="center", va="center", style="italic", transform=ax.transAxes)
            fig.subplots_adjust(left=0.14, right=0.90, top=0.88, bottom=0.16)
            canvas = FigureCanvasTkAgg(fig, master=fr)
            cw = canvas.get_tk_widget()
            cw.pack(fill="both", expand=True)
            self.panel_figs.append((fig, ax, canvas, img_key, direction, title,
                                    colors.get(img_key, "#4F8EF7")))
        self.spin_n = tk.Spinbox(fctrl, from_=100, to=5000, increment=100,
                                 width=10, font=F10,
                                 bg=BG3, fg=FG, relief="flat",
                                 buttonbackground=BG3)
        self.spin_n.delete(0, "end"); self.spin_n.insert(0, "1000")
        self.spin_n.pack(padx=10, pady=4)

        _btn(fctrl, "▶  Proses", self._run, width=14).pack(pady=10, padx=10)
        tk.Frame(fctrl, bg=BORDER, height=1).pack(fill="x", padx=8, pady=4)
        _btn_secondary(fctrl, "← Kembali ke Halaman Enkripsi", self.win.destroy, width=28).pack(pady=(4, 8))

        if any(v is not None for v in self.imgs.values()):
            self._run()

    def _run(self):
        try:
            n_samples = int(self.spin_n.get())
        except ValueError:
            n_samples = 1000

        for fig, ax, canvas, img_key, direction, title, color in self.panel_figs:
            img = self.imgs.get(img_key)
            ax.clear()
            ax.set_facecolor(PLOT_FACE)
            for spine in ax.spines.values():
                spine.set_edgecolor(BORDER)
            ax.tick_params(colors=FG2, labelsize=9)

            if img is None:
                ax.text(0.5, 0.5, "N/A", ha="center", va="center",
                        transform=ax.transAxes, fontsize=9, color=FG2)
                canvas.draw()
                continue

            g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(float) \
                if img.ndim == 3 else img.astype(float)

            if direction == "horizontal":   xp, yp = g[:, :-1].ravel(), g[:, 1:].ravel()
            elif direction == "vertical":   xp, yp = g[:-1, :].ravel(), g[1:, :].ravel()
            else:                           xp, yp = g[:-1, :-1].ravel(), g[1:, 1:].ravel()

            idx = np.random.choice(len(xp), min(n_samples, len(xp)), replace=False)
            xp, yp = xp[idx], yp[idx]
            corr = float(np.corrcoef(xp, yp)[0, 1]) if len(xp) > 1 else 0.0

            ax.scatter(xp, yp, s=1, alpha=0.35, color=color)
            ax.set_title(f"r = {corr:.4f}", fontsize=10, color=PLOT_TEXT, pad=4)
            ax.set_xlabel("pᵢ", fontsize=9, color=FG2)
            ax.set_ylabel("pᵢ₊₁", fontsize=9, color=FG2)
            canvas.draw()
