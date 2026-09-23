"""
gui_utils.py — Pustaka Komponen & Tema Visual GUI
==================================================
File ini berisi semua "bahan bangunan" tampilan grafis yang digunakan
bersama oleh seluruh halaman (window) dalam aplikasi.
Tidak berdiri sendiri — selalu di-import oleh file GUI lainnya.

FUNGSI UTAMA FILE INI:
  1. Mendefinisikan palet warna tema Dark Mode seluruh aplikasi
  2. Mendefinisikan ukuran & gaya font yang dipakai secara konsisten
  3. Menyediakan fungsi-fungsi pembuat widget siap pakai (tombol, label, dll.)
  4. Menyediakan kelas dasar _Base sebagai induk semua jendela (window)
  5. Menyediakan fungsi bantuan seperti tampilkan gambar dari array OpenCV

KOMPONEN YANG ADA:
  Warna   : BG, BG2, BG3, ACCENT (biru), ACCENT2 (ungu), SUCCESS, WARNING, DANGER
  Font    : F9, F10, F10B, F11B, F12B, F14B  (angka = ukuran, B = Bold)
  Widget  : _btn(), _btn_secondary(), _btn_danger()  → tombol siap pakai
            _lbl()     → label teks siap pakai
            _lframe()  → frame dengan label (group box)
            _entry()   → kotak input teks siap pakai
  Lainnya : show_cv2() → menampilkan gambar OpenCV ke dalam widget Tkinter
            _Base      → kelas induk dengan setup tema otomatis

CATATAN:
  - Ubah warna di sini untuk mengubah tema SELURUH aplikasi sekaligus
  - Font: Segoe UI (tampil modern di Windows)
"""

import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk

# ── Palet Warna (Light Mode Modern) ──────────────────────────────────────────
BG       = "#F8FAFC"   # background utama — sangat terang
BG2      = "#FFFFFF"   # background card/panel — putih
BG3      = "#F1F5F9"   # background elemen tertier
ACCENT   = "#3B82F6"   # biru terang — tombol utama
ACCENT2  = "#6366F1"   # ungu nila — highlight secondary
SUCCESS  = "#10B981"   # hijau terang — status berhasil
WARNING  = "#F59E0B"   # amber/kuning — peringatan
DANGER   = "#EF4444"   # merah — error / chaos threshold
FG       = "#0F172A"   # teks utama — gelap
FG2      = "#475569"   # teks sekunder — abu-abu
BORDER   = "#E2E8F0"   # warna border

BTN      = ACCENT      # alias tombol (backward compat)
BTN_FG   = "#FFFFFF"

# ── Font (Segoe UI — modern di Windows) ──────────────────────────────────────
_FONT_FAMILY = "Segoe UI"
F8   = (_FONT_FAMILY, 8)
F9   = (_FONT_FAMILY, 9)
F10  = (_FONT_FAMILY, 10)
F10B = (_FONT_FAMILY, 10, "bold")
F11  = (_FONT_FAMILY, 11)
F11B = (_FONT_FAMILY, 11, "bold")
F12B = (_FONT_FAMILY, 12, "bold")
F14B = (_FONT_FAMILY, 14, "bold")


# ── Helper Widget Factories ───────────────────────────────────────────────────

def _btn(parent, text, cmd, width=14, color=ACCENT, fg=BTN_FG, **kw):
    """Tombol dengan warna accent."""
    return tk.Button(
        parent, text=text, command=cmd,
        bg=color, fg=fg, font=F10B,
        width=width, relief="flat",
        padx=8, pady=5,
        activebackground=ACCENT2, activeforeground=BTN_FG,
        cursor="hand2", **kw
    )


def _btn_secondary(parent, text, cmd, width=14, **kw):
    """Tombol sekunder — background BG3."""
    return tk.Button(
        parent, text=text, command=cmd,
        bg=BG3, fg=FG, font=F10,
        width=width, relief="flat",
        padx=8, pady=5,
        activebackground=BORDER, activeforeground=FG,
        cursor="hand2", **kw
    )


def _btn_danger(parent, text, cmd, width=14, **kw):
    """Tombol danger/exit — warna merah."""
    return tk.Button(
        parent, text=text, command=cmd,
        bg="#7F1D1D", fg="#FCA5A5", font=F10,
        width=width, relief="flat",
        padx=8, pady=5,
        activebackground=DANGER, activeforeground="white",
        cursor="hand2", **kw
    )


def _lbl(parent, text, bold=False, size=10, color=FG, **kw):
    f = (_FONT_FAMILY, size, "bold") if bold else (_FONT_FAMILY, size)
    return tk.Label(parent, text=text, bg=BG, fg=color, font=f, **kw)


def _lbl2(parent, text, bold=False, **kw):
    """Label di atas background BG2 (card)."""
    f = F10B if bold else F10
    return tk.Label(parent, text=text, bg=BG2, fg=FG, font=f, **kw)


def _lframe(parent, text, bg=BG2, **kw):
    """LabelFrame dengan gaya dark mode."""
    return tk.LabelFrame(
        parent, text=text,
        bg=bg, fg=ACCENT,
        font=F10B, relief="flat",
        bd=0, highlightbackground=BORDER,
        highlightthickness=1, **kw
    )


def _entry(parent, default="", readonly=False, width=12, bg=BG3, **kw):
    """Return (Entry widget, StringVar) dengan tema dark."""
    v = tk.StringVar(value=str(default))
    s = "readonly" if readonly else "normal"
    e = tk.Entry(
        parent, textvariable=v, state=s, width=width,
        font=F10, bg=bg, fg=FG,
        insertbackground=FG,
        readonlybackground=BG3,
        relief="flat", bd=1,
        highlightbackground=BORDER,
        highlightthickness=1, **kw
    )
    return e, v


def _separator(parent, orient="horizontal", pad=4):
    """Garis pemisah tipis."""
    f = tk.Frame(parent, bg=BORDER,
                 height=1 if orient == "horizontal" else 0,
                 width=0 if orient == "horizontal" else 1)
    return f


def _section_header(parent, text, bg=BG):
    """Header section dengan accent bar di kiri."""
    f = tk.Frame(parent, bg=bg)
    bar = tk.Frame(f, bg=ACCENT, width=3)
    bar.pack(side="left", fill="y", padx=(0, 8))
    tk.Label(f, text=text, bg=bg, fg=FG, font=F11B).pack(side="left")
    return f


def _info_btn(parent, title, message, width=14):
    """Tombol ℹ yang membuka dialog informasi."""
    def _show():
        _InfoDialog(parent, title, message)
    return tk.Button(
        parent, text="ℹ  " + title, command=_show,
        bg=BG3, fg=ACCENT, font=F10,
        width=width, relief="flat", padx=8, pady=4,
        activebackground=BG2, activeforeground=ACCENT,
        cursor="hand2", anchor="w"
    )


# ── Dialog Info Custom (bukan messagebox) ─────────────────────────────────────

class _InfoDialog:
    """Dialog popup bertema dark untuk menampilkan teks panjang."""
    def __init__(self, parent, title, message):
        self.dlg = tk.Toplevel(parent)
        self.dlg.title(title)
        self.dlg.configure(bg=BG)
        self.dlg.geometry("560x420")
        self.dlg.resizable(False, False)
        self.dlg.grab_set()

        # Header
        hdr = tk.Frame(self.dlg, bg=ACCENT, height=40)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  " + title, bg=ACCENT, fg="white",
                 font=F12B, anchor="w").pack(fill="both", expand=True)

        # Body
        body = tk.Frame(self.dlg, bg=BG, padx=20, pady=16)
        body.pack(fill="both", expand=True)

        txt = tk.Text(body, wrap="word", bg=BG2, fg=FG, font=F10,
                      relief="flat", bd=0, padx=12, pady=12,
                      insertbackground=FG, state="normal",
                      highlightthickness=0)
        txt.insert("1.0", message)
        txt.configure(state="disabled")
        txt.pack(fill="both", expand=True)

        # Close button
        _btn(self.dlg, "Tutup", self.dlg.destroy, width=10).pack(pady=10)


# ── Window Bantuan Popup (Gaya Visual Sesuai Panduan Skripsi) ─────────────────

class HelpWindow:
    """Jendela popup panduan bantuan dengan antarmuka berbasis kartu, serasi dengan tema aplikasi."""
    def __init__(self, parent, program_type="lengkap"):
        self.dlg = tk.Toplevel(parent)
        self.dlg.title("bantuan")
        self.dlg.geometry("980x690")
        self.dlg.minsize(900, 620)
        self.dlg.configure(bg=BG)
        self.dlg.transient(parent)
        self.dlg.grab_set()

        # Posisi di tengah layar / parent
        self.dlg.update_idletasks()
        try:
            w, h = 980, 690
            x = max(0, parent.winfo_rootx() + (parent.winfo_width() - w) // 2)
            y = max(0, parent.winfo_rooty() + (parent.winfo_height() - h) // 2)
            self.dlg.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

        # Header Frame
        header = tk.Frame(self.dlg, bg=BG)
        header.pack(fill="x", padx=28, pady=(20, 10))

        lbl_title = tk.Label(
            header, text="Bantuan", font=F14B,
            bg=BG, fg=FG
        )
        lbl_title.pack(side="left")

        def _close_window():
            try:
                canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass
            self.dlg.destroy()

        btn_back = tk.Button(
            header, text="Kembali", font=F10B,
            bg=BG3, fg=FG, relief="flat", bd=1,
            highlightbackground=BORDER, highlightthickness=1,
            activebackground=BORDER, activeforeground=FG,
            padx=20, pady=4, cursor="hand2", command=_close_window
        )
        btn_back.pack(side="right")

        self.dlg.protocol("WM_DELETE_WINDOW", _close_window)

        # Garis pemisah tipis di bawah header
        sep = tk.Frame(self.dlg, bg=BORDER, height=1)
        sep.pack(fill="x", padx=28, pady=(0, 12))

        # Kontainer kartu dengan scrollbar
        canvas = tk.Canvas(self.dlg, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.dlg, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            try:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(24, 0), pady=(0, 18))
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=(0, 18))

        scroll_frame.columnconfigure(0, weight=1)
        scroll_frame.columnconfigure(1, weight=1)

        # Muat daftar kartu berdasarkan tipe program
        cards = self._get_cards(program_type)

        for idx, (title, content) in enumerate(cards):
            r, c = divmod(idx, 2)
            card = tk.Frame(
                scroll_frame, bg=BG2, bd=0, relief="flat",
                highlightbackground=BORDER, highlightthickness=1
            )
            card.grid(row=r, column=c, padx=8, pady=6, sticky="nsew")

            tk.Label(
                card, text=title, font=F10B,
                bg=BG2, fg=ACCENT, anchor="w"
            ).pack(fill="x", padx=14, pady=(10, 4))

            tk.Label(
                card, text=content, font=F9,
                bg=BG2, fg=FG, justify="left", anchor="w"
            ).pack(fill="x", padx=14, pady=(0, 10))

    def _get_cards(self, program_type):
        if program_type == "gof":
            algo_enkripsi = "-> Pilihan Algoritma: MS Map, Gauss Map, Sequential, Gauss-MS Map (g∘f)"
            algo_bif = "-> Pilihan Fungsi: MS Map, Gauss Map, Gauss-MS Map (g∘f)"
        elif program_type == "fog":
            algo_enkripsi = "-> Pilihan Algoritma: Gauss Map, MS Map, Sequential, MS-Gauss Map (f∘g)"
            algo_bif = "-> Pilihan Fungsi: Gauss Map, MS Map, MS-Gauss Map (f∘g)"
        else:  # lengkap
            algo_enkripsi = "-> Pilihan Algoritma: MS Map, Gauss Map, Sequential, Gauss-MS Map (g∘f), MS-Gauss Map (f∘g)"
            algo_bif = "-> Pilihan Fungsi: MS Map, Gauss Map, Sequential, Gauss-MS Map (g∘f), MS-Gauss Map (f∘g)"

        return [
            (
                "🔒  Tombol Enkripsi Citra",
                "Mengamankan citra digital medis (X-Ray, MRI, Histopatologi) menjadi cipherimage acak:\n"
                f"{algo_enkripsi}\n"
                "-> Pilih file citra (PNG/JPG/BMP)\n"
                "-> Masukkan parameter kunci (X0, r, α, β, λ, skip)\n"
                "-> Klik [Enkripsi Citra] -> Simpan hasil cipherimage"
            ),
            (
                "🔓  Tombol Dekripsi Citra",
                "Memulihkan citra acak menjadi citra asli secara lossless (tanpa penurunan kualitas):\n"
                "-> Masukkan citra terenkripsi (cipherimage)\n"
                "-> Masukkan parameter kunci yang SAMA PERSIS seperti saat enkripsi\n"
                "-> Klik [Dekripsi Citra] -> Output citra pulih 100% sempurna"
            ),
            (
                "📈  Tombol Diagram Bifurkasi",
                "Menganalisis sebaran nilai iterasi fungsi terhadap parameter kendali (r, α, β, λ):\n"
                f"{algo_bif}\n"
                "-> Pilih parameter kendali dan rentang iterasi\n"
                "-> Klik tombol [Diagram Bifurkasi]\n"
                "-> Area rapat/gelap menunjukkan rentang parameter dengan perilaku kaotik stabil"
            ),
            (
                "📉  Tombol Diagram Lyapunov (LLE)",
                "Membuktikan sifat chaos secara kuantitatif melalui Largest Lyapunov Exponent:\n"
                f"{algo_bif}\n"
                "-> Pilih parameter kendali yang diuji\n"
                "-> Nilai eksponen positif (µ > 0) membuktikan dinamika sistem bersifat chaotic\n"
                "-> Semakin tinggi nilai µ, semakin sensitif dan acak barisan bilangan yang dihasilkan"
            ),
            (
                "📌  Tombol Scatter Keystream & Korelasi",
                "Menguji independensi sebaran bilangan acak kunci dan korelasi piksel bertetangga:\n"
                "-> Menampilkan diagram tebar keystream (Xi vs Xi+1)\n"
                "-> Menghitung koefisien korelasi piksel arah Horizontal, Vertikal, dan Diagonal\n"
                "-> Nilai korelasi citra cipher ideal mendekati 0.0000 (tidak ada korelasi antar piksel)"
            ),
            (
                "🔬  Tombol Uji Acak NIST SP 800-22",
                "Menguji keacakan barisan bit keystream berdasarkan standar internasional NIST:\n"
                "-> Menjalankan 15 pengujian statistik (Frequency, Runs, Longest Run, FFT, dll.)\n"
                "-> Syarat kelulusan: Nilai p-value ≥ 0.01\n"
                "-> Hasil menampilkan status PASS/FAIL per uji beserta ringkasan kelulusan sistem"
            ),
            (
                "📊  Tombol Histogram RGB",
                "Menganalisis distribusi intensitas piksel per kanal warna (Merah, Hijau, Biru):\n"
                "-> Masukkan Citra Asli dan Citra Terenkripsi\n"
                "-> Klik [Compare]\n"
                "-> Histogram citra terenkripsi ideal menunjukkan distribusi yang rata/seragam (flat)"
            ),
            (
                "📊  Tombol Histogram Grayscale",
                "Menganalisis distribusi frekuensi intensitas derajat keabuan (0-255):\n"
                "-> Masukkan Citra Asli dan Citra Terenkripsi\n"
                "-> Klik [Compare]\n"
                "-> Distribusi seragam membuktikan citra kebal terhadap serangan analisis statistik"
            ),
            (
                "🎯  Tombol Hitung MSE & PSNR",
                "Memvalidasi keberhasilan rekonstruksi citra setelah proses dekripsi:\n"
                "-> Masukkan Citra Asli dan Citra Hasil Dekripsi\n"
                "-> Klik [Hitung MSE & PSNR]\n"
                "-> Hasil ideal: MSE = 0.0000 dan PSNR = Infinity dB (rekonstruksi 100% sempurna)"
            ),
            (
                "⚡  Tombol Sensitivitas Visual (NPCR & UACI)",
                "Menguji ketahanan terhadap serangan diferensial melalui perubahan 1-bit kunci:\n"
                "-> Masukkan Citra Asli dan atur selisih kunci 1-bit (Δ = 10⁻¹⁵)\n"
                "-> Standar ideal internasional: NPCR ≥ 99.60% dan UACI ≈ 33.46%\n"
                "-> Menampilkan citra selisih diferensial secara visual"
            ),
            (
                "⏳  Tombol Riwayat Operasi",
                "Melihat rekam jejak setiap aktivitas enkripsi dan dekripsi yang telah dilakukan:\n"
                "-> Menyimpan informasi tanggal, waktu, nama berkas, algoritma, parameter, dan metrik\n"
                "-> Fitur pencarian/filter serta ekspor riwayat data ke berkas JSON"
            ),
            (
                "👤  Tombol Tentang Peneliti & Aplikasi",
                "Informasi orisinalitas dan profil pengembang aplikasi:\n"
                "-> Peneliti: Novandi Ahmad Ramdhan (NPM: 51422256) — Universitas Gunadarma\n"
                "-> Dosen Pembimbing: Dr. Suci Br Kembaren, S.Kom., MMSI.\n"
                "-> Repositori Resmi GitHub: https://github.com/Vannnd1/chaotic-image-encryption"
            ),
        ]


# ── Window Tentang Peneliti Popup ─────────────────────────────────────────────

class AboutWindow:
    """Jendela popup informasi tentang peneliti dan aplikasi skripsi."""
    def __init__(self, parent):
        self.dlg = tk.Toplevel(parent)
        self.dlg.title("Tentang Peneliti & Aplikasi")
        self.dlg.geometry("860x650")
        self.dlg.minsize(760, 560)
        self.dlg.configure(bg=BG)
        self.dlg.transient(parent)
        self.dlg.grab_set()

        # Posisi di tengah layar / parent
        self.dlg.update_idletasks()
        try:
            w, h = 860, 650
            x = max(0, parent.winfo_rootx() + (parent.winfo_width() - w) // 2)
            y = max(0, parent.winfo_rooty() + (parent.winfo_height() - h) // 2)
            self.dlg.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

        # Header Frame
        header = tk.Frame(self.dlg, bg=BG)
        header.pack(fill="x", padx=28, pady=(20, 10))

        lbl_title = tk.Label(
            header, text="👤  Tentang Peneliti & Aplikasi", font=F14B,
            bg=BG, fg=FG
        )
        lbl_title.pack(side="left")

        btn_back = tk.Button(
            header, text="Tutup", font=F10B,
            bg=BG3, fg=FG, relief="flat", bd=1,
            highlightbackground=BORDER, highlightthickness=1,
            activebackground=BORDER, activeforeground=FG,
            padx=20, pady=4, cursor="hand2", command=self.dlg.destroy
        )
        btn_back.pack(side="right")

        # Garis pemisah
        sep = tk.Frame(self.dlg, bg=BORDER, height=1)
        sep.pack(fill="x", padx=28, pady=(0, 14))

        # Kontainer dengan Canvas Scroll jika layar kecil
        canvas = tk.Canvas(self.dlg, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.dlg, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            try:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(24, 0), pady=(0, 18))
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=(0, 18))

        # ── Kartu 1: Profil Peneliti ──────────────────────────────────────────
        c1 = tk.Frame(scroll_frame, bg=BG2, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        c1.pack(fill="x", padx=6, pady=(0, 12))

        tk.Label(c1, text="🎓  Identitas Peneliti", font=F11B, bg=BG2, fg=ACCENT, anchor="w").pack(fill="x", padx=18, pady=(12, 6))

        info_peneliti = [
            ("Nama Lengkap", "Novandi Ahmad Ramdhan"),
            ("NPM", "51422256"),
            ("Program Studi", "Informatika / Teknik Informatika"),
            ("Fakultas", "Fakultas Teknologi Industri"),
            ("Universitas", "Universitas Gunadarma"),
            ("Tahun Rilis", "2026"),
            ("Dosen Pembimbing", "Dr. Suci Br Kembaren, S.Kom., MMSI."),
            ("Judul Skripsi", "Pengembangan dan Perbandingan Algoritma Enkripsi Berbasis Fungsi Chaos MS Gauss Map dan Gauss MS Map untuk Keamanan Citra Digital Medis")
        ]

        for lbl, val in info_peneliti:
            row = tk.Frame(c1, bg=BG2)
            row.pack(fill="x", padx=18, pady=2)
            tk.Label(row, text=f"{lbl:<18} :", font=F9, bg=BG2, fg=FG2, width=20, anchor="w").pack(side="left")
            is_bold = lbl in ["Nama Lengkap", "NPM", "Universitas"]
            tk.Label(row, text=val, font=F10B if is_bold else F9, bg=BG2, fg=FG, justify="left", wraplength=540, anchor="w").pack(side="left", fill="x", expand=True)

        tk.Frame(c1, bg=BG2, height=10).pack()

        # ── Kartu 2: Spesifikasi Riset & Repositori ────────────────────────────
        c2 = tk.Frame(scroll_frame, bg=BG2, relief="flat", highlightbackground=BORDER, highlightthickness=1)
        c2.pack(fill="x", padx=6, pady=(0, 12))

        tk.Label(c2, text="💻  Sistem & Repositori Resmi", font=F11B, bg=BG2, fg=ACCENT2, anchor="w").pack(fill="x", padx=18, pady=(12, 6))

        info_riset = [
            ("Algoritma Kaotik", "Gauss MS Map (g∘f), MS Gauss Map (f∘g), MS Map, Gauss Map, Sequential"),
            ("Fitur Pengujian", "NIST SP 800-22, Entropi Shannon, Korelasi Piksel, NPCR, UACI, MSE, PSNR, LLE, Bifurkasi"),
            ("Repositori GitHub", "https://github.com/Vannnd1/chaotic-image-encryption"),
            ("Teknologi & Lib", "Python 3.10+, Tkinter, OpenCV, NumPy, SciPy, Matplotlib, Numba JIT"),
            ("Lisensi Perangkat", "MIT License (Hak Cipta © 2026 Novandi Ahmad Ramdhan)")
        ]

        for lbl, val in info_riset:
            row = tk.Frame(c2, bg=BG2)
            row.pack(fill="x", padx=18, pady=2)
            tk.Label(row, text=f"{lbl:<18} :", font=F9, bg=BG2, fg=FG2, width=20, anchor="w").pack(side="left")
            fg_color = ACCENT if "https://" in val else FG
            tk.Label(row, text=val, font=F10B if "https://" in val else F9, bg=BG2, fg=fg_color, justify="left", wraplength=540, anchor="w").pack(side="left", fill="x", expand=True)

        tk.Frame(c2, bg=BG2, height=10).pack()


# ── Preview Gambar ────────────────────────────────────────────────────────────

def _img_label(parent, w=250, h=200):
    """Placeholder label untuk preview gambar."""
    return tk.Label(
        parent, bg=BG3, width=w, height=h,
        text="(belum ada gambar)", fg=FG2, font=F9,
        relief="flat", bd=1
    )


def show_cv2(label_widget, cv2_img, max_w=250, max_h=220):
    """Tampilkan gambar OpenCV pada tk.Label."""
    if cv2_img is None:
        return
    rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB) if cv2_img.ndim == 3 else cv2_img
    pil = Image.fromarray(rgb)
    pil.thumbnail((max_w, max_h), Image.LANCZOS)
    photo = ImageTk.PhotoImage(pil)
    label_widget.configure(image=photo, text="", width=max_w, height=max_h)
    label_widget._ref = photo   # cegah GC


# ── Scrollable Text (untuk output panjang) ───────────────────────────────────

def _scrolltext(parent, height=8, **kw):
    """Frame berisi Text + Scrollbar bertema dark."""
    f = tk.Frame(parent, bg=BG2)
    sb = tk.Scrollbar(f, bg=BG3, troughcolor=BG)
    sb.pack(side="right", fill="y")
    t = tk.Text(f, height=height, wrap="word",
                bg=BG2, fg=FG, font=F10,
                relief="flat", bd=0, padx=8, pady=6,
                insertbackground=FG,
                yscrollcommand=sb.set, **kw)
    t.pack(side="left", fill="both", expand=True)
    sb.config(command=t.yview)
    return f, t


# ═══════════════════════════════════════════════════════════════════════════════
# BASE WINDOW (Toplevel)
# ═══════════════════════════════════════════════════════════════════════════════

class _Base:
    def __init__(self, parent, app, title, geometry="1050x620"):
        self.app = app
        self.win = tk.Toplevel(parent)
        self.win.title(title)
        self.win.configure(bg=BG)
        self.win.geometry(geometry)
        
        # Mengaktifkan mode Full Screen (zoomed) secara otomatis
        try:
            self.win.state("zoomed")
        except Exception:
            pass
            
        self.win.resizable(True, True)
        self.win.grab_set()

        # Thin accent bar di top
        accent_bar = tk.Frame(self.win, bg=ACCENT, height=3)
        accent_bar.pack(fill="x", side="top")

    def _nav_row(self, parent):
        """Baris navigasi bawah: Main Menu."""
        f = tk.Frame(parent, bg=BG)
        f.pack(side="bottom", fill="x", padx=10, pady=8)
        sep = _separator(parent)
        sep.pack(side="bottom", fill="x", pady=(4, 0))
        _btn_secondary(f, "← Main Menu", self.win.destroy, width=14).pack(side="right", padx=4)
        return f

    def _title_bar(self, parent, text, subtitle=None):
        """Header bar dengan judul dan opsional subtitle (rata tengah agar seimbang)."""
        f = tk.Frame(parent, bg=BG2, pady=12)
        f.pack(fill="x", padx=0)
        tk.Label(f, text=text, bg=BG2, fg=FG, font=("Segoe UI", 15, "bold"),
                 justify="center").pack(anchor="center")
        if subtitle:
            tk.Label(f, text=subtitle, bg=BG2, fg=FG2, font=F10,
                     justify="center").pack(anchor="center", pady=(3, 0))
        tk.Frame(f, bg=ACCENT, height=2).pack(fill="x", pady=(8, 0))
        return f
