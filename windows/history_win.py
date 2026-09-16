"""
windows/history_win.py — Jendela Riwayat Enkripsi & Dekripsi (GUI)
====================================================================
File ini menampilkan halaman riwayat yang mencatat semua operasi
enkripsi dan dekripsi yang telah dilakukan selama sesi program berjalan.

FUNGSI UTAMA FILE INI:
  1. Menampilkan daftar semua operasi yang pernah dilakukan (scrollable)
  2. Menyediakan filter berdasarkan jenis operasi (Enkripsi / Dekripsi)
  3. Menyediakan fitur pencarian riwayat berdasarkan kata kunci
  4. Menampilkan detail lengkap operasi yang dipilih di panel kanan
  5. Mengekspor seluruh riwayat ke file CSV atau JSON

TATA LETAK HALAMAN:
  ┌─────────────────────────────────────────────────┐
  │  Toolbar: [Filter] [Cari] [Hapus Semua] [Export] │
  ├──────────────────────┬──────────────────────────┤
  │  Panel Kiri          │  Panel Kanan             │
  │  (Daftar Riwayat)    │  (Detail Operasi Dipilih)│
  │  - scrollable list   │  - waktu & algoritma     │
  │  - tiap item = 1 op  │  - parameter kunci       │
  │                      │  - metrik hasil          │
  └──────────────────────┴──────────────────────────┘

CATATAN:
  - Data riwayat diambil dari objek `history` di history_manager.py
  - Riwayat hanya ada selama sesi berjalan (tidak tersimpan otomatis)
  - Gunakan tombol Export untuk menyimpan riwayat ke file permanen
  - Tema: Dark Mode Modern
"""

import tkinter as tk
from tkinter import filedialog, messagebox

from gui_utils import (
    _Base, _btn, _btn_secondary, _btn_danger, _lbl, _lframe, _entry,
    BG, BG2, BG3, ACCENT, ACCENT2, FG, FG2, BORDER,
    SUCCESS, WARNING, DANGER,
    F9, F10, F10B, F11B, F12B,
)
from history_manager import history, OP_ENCRYPT, OP_DECRYPT


# ── Warna badge operasi ───────────────────────────────────────────────────────
COLOR_ENC = "#D1FAE5"   # hijau terang — enkripsi
COLOR_DEC = "#DBEAFE"   # biru terang  — dekripsi
FG_ENC    = "#047857"   # teks hijau gelap
FG_DEC    = "#1D4ED8"   # teks biru gelap


# ══════════════════════════════════════════════════════════════════════════════
# HISTORY WINDOW
# ══════════════════════════════════════════════════════════════════════════════

class HistoryWindow(_Base):
    """Jendela utama riwayat."""

    def __init__(self, parent, app):
        super().__init__(parent, app, "Riwayat Enkripsi & Dekripsi", "1100x680")
        self._selected_entry = None
        self._build()
        # Subscribe ke history agar refresh otomatis saat ada entri baru
        history.subscribe(self._on_history_changed)
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        self._refresh_list()

    # ── Build UI ─────────────────────────────────────────────────────────────

    def _build(self):
        w = self.win

        # ── Title bar ────────────────────────────────────────────────────────
        self._title_bar(w, "🕓  Riwayat Operasi",
                        "Enkripsi & Dekripsi — rekam jejak lengkap sesi ini")

        # ── Toolbar ──────────────────────────────────────────────────────────
        tb = tk.Frame(w, bg=BG2, pady=6)
        tb.pack(fill="x", padx=0)

        tk.Frame(tb, bg=BORDER, width=1).pack(side="left", fill="y", padx=4)

        # Statistik ringkas
        self.lbl_stat = tk.Label(
            tb, text="", bg=BG2, fg=FG2, font=F9, padx=10)
        self.lbl_stat.pack(side="left")

        tk.Frame(tb, bg=BORDER, width=1).pack(side="left", fill="y", padx=8)

        # Filter operasi
        tk.Label(tb, text="Filter:", bg=BG2, fg=FG2, font=F9).pack(side="left")
        self.filter_var = tk.StringVar(value="Semua")
        for label, val in [("Semua", "Semua"),
                            (f"🔒 {OP_ENCRYPT}", OP_ENCRYPT),
                            (f"🔓 {OP_DECRYPT}",  OP_DECRYPT)]:
            rb = tk.Radiobutton(
                tb, text=label, variable=self.filter_var, value=val,
                bg=BG2, fg=FG, font=F9,
                selectcolor=ACCENT,
                activebackground=BG2, activeforeground=FG,
                command=self._refresh_list)
            rb.pack(side="left", padx=4)

        tk.Frame(tb, bg=BORDER, width=1).pack(side="left", fill="y", padx=8)

        # Kotak pencarian
        tk.Label(tb, text="Cari:", bg=BG2, fg=FG2, font=F9).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_list())
        se = tk.Entry(
            tb, textvariable=self.search_var, width=18,
            bg=BG3, fg=FG, font=F9, relief="flat", bd=1,
            insertbackground=FG,
            highlightbackground=BORDER, highlightthickness=1)
        se.pack(side="left", padx=4)

        # Tombol kanan toolbar
        _btn_danger(tb, "🗑  Hapus Semua", self._clear_history,
                    width=13).pack(side="right", padx=6)
        _btn_secondary(tb, "📄  Export JSON", self._export_json,
                       width=13).pack(side="right", padx=3)
        _btn_secondary(tb, "📊  Export CSV",  self._export_csv,
                       width=13).pack(side="right", padx=3)

        tk.Frame(w, bg=BORDER, height=1).pack(fill="x")

        # Navigasi bawah
        self._nav_row(w)

        # ── Body 2 kolom ──────────────────────────────────────────────────────
        body = tk.Frame(w, bg=BG)
        body.pack(fill="both", expand=True, padx=10, pady=8)

        # ─ Panel Kiri — Daftar Riwayat ───────────────────────────────────────
        left = _lframe(body, "  📋  Daftar Riwayat")
        left.pack(side="left", fill="both", expand=False,
                  padx=(0, 8), pady=4, ipadx=4, ipady=4)
        left.configure(width=400)
        left.pack_propagate(False)

        # Canvas + scrollbar untuk daftar
        self.list_canvas = tk.Canvas(left, bg=BG2, highlightthickness=0)
        self.list_scroll  = tk.Scrollbar(left, orient="vertical",
                                          command=self.list_canvas.yview,
                                          bg=BG3, troughcolor=BG)
        self.list_canvas.configure(yscrollcommand=self.list_scroll.set)
        self.list_scroll.pack(side="right", fill="y")
        self.list_canvas.pack(side="left", fill="both", expand=True)

        self.list_frame = tk.Frame(self.list_canvas, bg=BG2)
        self._list_window = self.list_canvas.create_window(
            (0, 0), window=self.list_frame, anchor="nw")

        self.list_frame.bind("<Configure>", self._on_frame_configure)
        self.list_canvas.bind("<Configure>", self._on_canvas_configure)
        self.list_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Placeholder teks kosong
        self.lbl_empty = tk.Label(
            self.list_frame,
            text="Belum ada riwayat.\n\nLakukan enkripsi atau\ndekripsi terlebih dahulu.",
            bg=BG2, fg=FG2, font=F9, justify="center", pady=40)

        # ─ Panel Kanan — Detail ───────────────────────────────────────────────
        right = _lframe(body, "  🔍  Detail Entri")
        right.pack(side="right", fill="both", expand=True, pady=4)

        # Placeholder saat tidak ada yang dipilih
        self.detail_placeholder = tk.Label(
            right,
            text="← Pilih entri di sebelah kiri\nuntuk melihat detail lengkap",
            bg=BG2, fg=FG2, font=F10, justify="center", pady=60)
        self.detail_placeholder.pack(expand=True)

        # Frame detail (tersembunyi awalnya)
        self.detail_frame = tk.Frame(right, bg=BG2)

        # Teks detail
        txt_frame = tk.Frame(self.detail_frame, bg=BG2)
        txt_frame.pack(fill="both", expand=True, padx=6, pady=(6, 4))

        sb_detail = tk.Scrollbar(txt_frame, bg=BG3, troughcolor=BG)
        sb_detail.pack(side="right", fill="y")
        self.detail_text = tk.Text(
            txt_frame,
            bg=BG2, fg=FG, font=("Consolas", 9),
            relief="flat", bd=0,
            padx=10, pady=10,
            wrap="word",
            state="disabled",
            highlightthickness=0,
            yscrollcommand=sb_detail.set)
        self.detail_text.pack(side="left", fill="both", expand=True)
        sb_detail.config(command=self.detail_text.yview)

        # Tag warna untuk teks detail
        self.detail_text.tag_configure("header",
            foreground=ACCENT, font=("Consolas", 9, "bold"))
        self.detail_text.tag_configure("section",
            foreground=WARNING, font=("Consolas", 9, "bold"))
        self.detail_text.tag_configure("value",
            foreground=FG)
        self.detail_text.tag_configure("metric_good",
            foreground=FG_ENC)
        self.detail_text.tag_configure("enc_badge",
            foreground=FG_ENC, font=("Consolas", 10, "bold"))
        self.detail_text.tag_configure("dec_badge",
            foreground=FG_DEC, font=("Consolas", 10, "bold"))

        # Tombol di bawah detail
        btn_row = tk.Frame(self.detail_frame, bg=BG2)
        btn_row.pack(fill="x", padx=6, pady=(0, 6))
        _btn_secondary(btn_row, "🗑  Hapus Entri Ini",
                       self._delete_selected, width=18).pack(side="left", padx=4)

    # ── Refresh daftar ────────────────────────────────────────────────────────

    def _refresh_list(self):
        """Bangun ulang list item."""
        # Ambil data sesuai filter
        op_filter    = self.filter_var.get()
        search_text  = self.search_var.get().strip()
        op_val       = None if op_filter == "Semua" else op_filter
        entries      = history.filter(operation=op_val, text=search_text or None)

        # Update statistik
        self.lbl_stat.configure(
            text=f"Total: {history.count}  |  "
                 f"🔒 {history.enc_count}  |  "
                 f"🔓 {history.dec_count}  |  "
                 f"Ditampilkan: {len(entries)}")

        # Bersihkan list frame
        for child in self.list_frame.winfo_children():
            child.destroy()

        if not entries:
            self.lbl_empty = tk.Label(
                self.list_frame,
                text="Belum ada riwayat.\n\nLakukan enkripsi atau\ndekripsi terlebih dahulu."
                     if history.count == 0 else
                     "Tidak ada entri yang cocok\ndengan filter/pencarian.",
                bg=BG2, fg=FG2, font=F9, justify="center", pady=40)
            self.lbl_empty.pack(expand=True)
            return

        for entry in entries:
            self._build_list_card(entry)

    def _build_list_card(self, entry):
        """Buat kartu satu entri di panel kiri."""
        is_enc  = entry.operation == OP_ENCRYPT
        b_color = COLOR_ENC if is_enc else COLOR_DEC
        fg_op   = FG_ENC    if is_enc else FG_DEC
        icon    = "🔒" if is_enc else "🔓"

        # Kartu (frame klik)
        card = tk.Frame(
            self.list_frame,
            bg=BG3 if self._selected_entry and
               self._selected_entry.id == entry.id else BG2,
            relief="flat", bd=0,
            highlightbackground=BORDER, highlightthickness=1,
            cursor="hand2")
        card.pack(fill="x", padx=6, pady=3)

        # Bind klik
        def _select(e, ent=entry, c=card):
            self._on_select(ent, c)
        for widget in [card]:
            widget.bind("<Button-1>", _select)

        # Baris atas: badge + ID + waktu
        top = tk.Frame(card, bg=card["bg"])
        top.pack(fill="x", padx=8, pady=(6, 2))
        top.bind("<Button-1>", _select)

        badge = tk.Label(top, text=f" {icon} {entry.operation} ",
                         bg=b_color, fg=fg_op, font=F9,
                         relief="flat", padx=4)
        badge.pack(side="left")
        badge.bind("<Button-1>", _select)

        tk.Label(top, text=f"  #{entry.id}",
                 bg=card["bg"], fg=FG2, font=F9).pack(side="left")
        tk.Label(top, text=f"{entry.timestamp_str}",
                 bg=card["bg"], fg=FG2, font=F9).pack(side="right")

        # Baris tengah: algoritma
        mid = tk.Frame(card, bg=card["bg"])
        mid.pack(fill="x", padx=8, pady=1)
        mid.bind("<Button-1>", _select)
        tk.Label(mid, text=entry.algorithm,
                 bg=card["bg"], fg=FG, font=F10B).pack(side="left")

        # Baris bawah: ukuran + durasi + file
        bot = tk.Frame(card, bg=card["bg"])
        bot.pack(fill="x", padx=8, pady=(1, 6))
        bot.bind("<Button-1>", _select)

        info_parts = [entry.shape_str, f"{entry.elapsed_ms:.1f} ms"]
        if entry.input_filename != "—":
            info_parts.append(f"📂 {entry.input_filename}")
        tk.Label(bot, text="  •  ".join(info_parts),
                 bg=card["bg"], fg=FG2, font=F9).pack(side="left")

        # Bind semua child juga
        def _bind_all(widget):
            widget.bind("<Button-1>", _select)
            for child in widget.winfo_children():
                _bind_all(child)
        _bind_all(card)

    # ── Seleksi entri ─────────────────────────────────────────────────────────

    def _on_select(self, entry, card_widget=None):
        self._selected_entry = entry
        self._refresh_list()   # recolor kartu
        self._show_detail(entry)

    def _show_detail(self, entry):
        """Tampilkan detail entri di panel kanan."""
        self.detail_placeholder.pack_forget()
        self.detail_frame.pack(fill="both", expand=True)

        txt = self.detail_text
        txt.configure(state="normal")
        txt.delete("1.0", "end")

        # Render teks dengan tag
        raw = entry.detail_text()
        for line in raw.split("\n"):
            stripped = line.lstrip()
            if line.startswith("═"):
                txt.insert("end", line + "\n", "header")
            elif line.startswith("  🔒") or line.startswith("  🔓"):
                tag = "enc_badge" if "🔒" in line else "dec_badge"
                txt.insert("end", line + "\n", tag)
            elif stripped.startswith("📅") or stripped.startswith("⚙️") \
                    or stripped.startswith("🖼️") or stripped.startswith("⏱️") \
                    or stripped.startswith("📁") or stripped.startswith("🔑") \
                    or stripped.startswith("📊"):
                txt.insert("end", line + "\n", "section")
            elif stripped.startswith("Entropy Terenkripsi") \
                    or stripped.startswith("NPCR") \
                    or stripped.startswith("UACI"):
                txt.insert("end", line + "\n", "metric_good")
            else:
                txt.insert("end", line + "\n", "value")

        txt.configure(state="disabled")
        txt.see("1.0")

    # ── Aksi toolbar ─────────────────────────────────────────────────────────

    def _clear_history(self):
        if history.count == 0:
            messagebox.showinfo("Info", "Riwayat sudah kosong.", parent=self.win)
            return
        if messagebox.askyesno(
                "Konfirmasi",
                f"Hapus semua {history.count} entri riwayat?\nTindakan ini tidak bisa dibatalkan.",
                parent=self.win):
            history.clear()
            self._selected_entry = None
            self.detail_frame.pack_forget()
            self.detail_placeholder.pack(expand=True)
            messagebox.showinfo("Selesai", "Riwayat berhasil dihapus.", parent=self.win)

    def _delete_selected(self):
        if not self._selected_entry:
            return
        if messagebox.askyesno(
                "Konfirmasi",
                f"Hapus entri #{self._selected_entry.id}?",
                parent=self.win):
            history.remove(self._selected_entry.id)
            self._selected_entry = None
            self.detail_frame.pack_forget()
            self.detail_placeholder.pack(expand=True)

    def _export_csv(self):
        if history.count == 0:
            messagebox.showinfo("Info", "Riwayat masih kosong.", parent=self.win)
            return
        path = filedialog.asksaveasfilename(
            parent=self.win,
            title="Simpan Riwayat sebagai CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            history.export_csv(path)
            messagebox.showinfo("Berhasil",
                                f"Riwayat berhasil disimpan:\n{path}",
                                parent=self.win)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self.win)

    def _export_json(self):
        if history.count == 0:
            messagebox.showinfo("Info", "Riwayat masih kosong.", parent=self.win)
            return
        path = filedialog.asksaveasfilename(
            parent=self.win,
            title="Simpan Riwayat sebagai JSON",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            history.export_json(path)
            messagebox.showinfo("Berhasil",
                                f"Riwayat berhasil disimpan:\n{path}",
                                parent=self.win)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self.win)

    # ── Scroll helpers ────────────────────────────────────────────────────────

    def _on_frame_configure(self, event=None):
        self.list_canvas.configure(
            scrollregion=self.list_canvas.bbox("all"))

    def _on_canvas_configure(self, event=None):
        self.list_canvas.itemconfig(
            self._list_window, width=event.width)

    def _on_mousewheel(self, event):
        # Hanya scroll jika mouse di atas list_canvas
        try:
            x, y = event.x_root, event.y_root
            cx = self.list_canvas.winfo_rootx()
            cy = self.list_canvas.winfo_rooty()
            cw = self.list_canvas.winfo_width()
            ch = self.list_canvas.winfo_height()
            if cx <= x <= cx + cw and cy <= y <= cy + ch:
                self.list_canvas.yview_scroll(
                    int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def _on_history_changed(self):
        """Dipanggil oleh history manager saat ada perubahan."""
        try:
            self._refresh_list()
        except Exception:
            pass

    def _on_close(self):
        history.unsubscribe(self._on_history_changed)
        self.win.destroy()
