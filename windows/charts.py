# coding: utf-8
"""
windows/charts.py - Jendela Diagram Kaos (Lyapunov, Bifurkasi, Scatter)
Versi berbingkai rapi (LabelFrame card container) dan responsif.
Matplotlib figure dibungkus di dalam frame card berbatas tegas dengan padding aman,
menggunakan layout="constrained" dan skala sumbu terpadu (consistent scales).
"""

import tkinter as tk
from tkinter import messagebox
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui_utils import (
    _Base, _btn, _lbl, _lframe, _entry,
    BG, BG2, BG3, ACCENT, FG, FG2, BORDER, DANGER, SUCCESS,
    F9, F10B, _InfoDialog
)
from chaos_map import (
    _iterate_ms_map,
    _iterate_gauss_map,
    _iterate_ms_gauss_gof,
    _iterate_ms_gauss_fog,
)

PLOT_BG   = BG2         # Mengikuti warna card (#FFFFFF)
PLOT_FACE = "#FFFFFF"
PLOT_GRID = "#E2E8F0"
PLOT_TEXT = "#0F172A"

# ============================================================
# Definisi 5 Algoritma
# ============================================================

# (id, label_pendek, label_panjang, warna_plot, default_checked)
ALGO_DEFS = [
    ("ms",    "MS Map",       "MS Map f(x)",        "#2563EB", False),
    ("gauss", "Gauss Map",    "Gauss Map g(x)",     "#D97706", False),
    ("gof",   "GoF (gof)",   "GoF g(f(x))",        "#059669", True ),
    ("fog",   "FoG (fog)",   "FoG f(g(x))",        "#7C3AED", True ),
    ("seq",   "Sequential",  "Sequential (MS+G)/2", "#DC2626", False),
]


def _get_sequence(algo_id, x0, n, r, lam, alpha, beta):
    """
    Bangkitkan deret kaotik untuk satu algoritma.
    Sequential direpresentasikan sebagai rata-rata deret MS Map dan Gauss Map.
    """
    if algo_id == "ms":
        return _iterate_ms_map(x0, n, r, lam)
    elif algo_id == "gauss":
        return _iterate_gauss_map(x0, n, alpha, beta)
    elif algo_id == "gof":
        return _iterate_ms_gauss_gof(x0, n, r, lam, alpha, beta)
    elif algo_id == "fog":
        return _iterate_ms_gauss_fog(x0, n, r, lam, alpha, beta)
    else:  # seq
        s1 = _iterate_ms_map(x0, n, r, lam)
        s2 = _iterate_gauss_map(x0, n, alpha, beta)
        return (s1 + s2) / 2.0


# ============================================================
# Helpers UI & Plot
# ============================================================

def _style_ax(ax, fig, title, xlabel, ylabel, initial=False):
    fig.patch.set_facecolor(PLOT_BG)
    ax.set_facecolor(PLOT_FACE)
    ax.set_title(title, color=PLOT_TEXT, fontsize=9, pad=6)
    ax.set_xlabel(xlabel, color=FG2, fontsize=8)
    ax.set_ylabel(ylabel, color=FG2, fontsize=8)
    ax.tick_params(colors=FG2, labelsize=7)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
    if initial:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        ax.text(0.5, 0.5, "Pilih algoritma lalu klik Hitung",
                color=FG2, fontsize=8, ha="center", va="center",
                style="italic", transform=ax.transAxes)
    else:
        ax.grid(True, color=PLOT_GRID, linewidth=0.5, linestyle="--", alpha=0.7)


def _subplot_grid(n):
    """Kembalikan (nrows, ncols) subplot yang pas untuk n plot."""
    if n <= 1: return 1, 1
    if n == 2: return 1, 2
    if n == 3: return 1, 3
    if n == 4: return 2, 2
    return 2, 3   # 5 algo


def _build_algo_selector(parent, algo_vars):
    """
    Buat 5 checkbox pilihan algoritma di dalam frame parent.
    algo_vars : dict {algo_id: tk.BooleanVar}
    """
    fr = tk.Frame(parent, bg=BG2)
    tk.Label(fr, text="Algoritma:", bg=BG2, fg=FG2, font=F9).pack(side="left", padx=(0, 4))
    for algo_id, label, _, color, _ in ALGO_DEFS:
        var = algo_vars[algo_id]
        cb = tk.Checkbutton(
            fr, text=label, variable=var,
            bg=BG2, fg=color, selectcolor=BG3,
            activebackground=BG2, activeforeground=color,
            font=F9, cursor="hand2"
        )
        cb.pack(side="left", padx=3)
    return fr


# ============================================================
# LyapunovWindow
# ============================================================

class LyapunovWindow(_Base):
    PARAM_MAP = {
        "r":      ("r",     np.linspace(1.0, 4.0, 100), "r"),
        "a":      ("alpha", np.linspace(1.0, 8.0, 100), "alpha"),
        "b":      ("beta",  np.linspace(1.0, 5.0, 100), "beta"),
        "lambda": ("lam",   np.linspace(1.0, 5.0, 100), "lambda"),
    }

    def __init__(self, parent, app, default_param="r"):
        self.dparam = default_param
        super().__init__(parent, app, "Eksponen Lyapunov", "1100x620")
        self._build()

    def _build(self):
        w = self.win
        self._title_bar(w, "Eksponen Lyapunov - Analisis Sifat Kaotik", "u > 0 = Chaotic")
        self._nav_row(w)

        fr_top = _lframe(w, " Parameter & Pilih Algoritma")
        fr_top.pack(fill="x", padx=12, pady=(4, 0))

        fields = [
            ("X0", "x0", "0.3"), ("r", "r", "3.5"),
            ("a", "alpha", "5.8"), ("b", "beta", "3.1"), ("l", "lam", "3.5"),
        ]
        self.evars = {}
        col = 0
        for ltext, key, dflt in fields:
            tk.Label(fr_top, text=ltext, bg=BG2, fg=FG2, font=F9).grid(row=0, column=col, padx=3, pady=4)
            e, v = _entry(fr_top, dflt, width=7)
            e.grid(row=0, column=col + 1, padx=(0, 8), pady=4)
            self.evars[key] = v
            col += 2

        # Checkbox algoritma
        self.algo_vars = {aid: tk.BooleanVar(value=default_on)
                         for aid, _, _, _, default_on in ALGO_DEFS}
        _build_algo_selector(fr_top, self.algo_vars).grid(row=0, column=col, padx=10, pady=4)
        col += 1
        _btn(fr_top, "Hitung Lyapunov", self._compute, width=16).grid(row=0, column=col, padx=8, pady=4)

        # Frame pembatas grafik (Card Container)
        self.fl = _lframe(w, " Area Visualisasi Eksponen Lyapunov")
        self.fl.pack(fill="both", expand=True, padx=12, pady=(4, 6))

        # Matplotlib figure dengan layout="constrained" (responsif & terbingkai rapi)
        self.fig = plt.Figure(layout="constrained")
        self.fig.patch.set_facecolor(PLOT_BG)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.fl)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.configure(bg=BG2, highlightthickness=0, bd=0)
        canvas_widget.pack(fill="both", expand=True, padx=6, pady=6)

        selected = [aid for aid, _, _, _, on in ALGO_DEFS if on]
        self._setup_axes(selected, initial=True)

    def _setup_axes(self, selected, initial=False):
        self.fig.clf()
        n = max(len(selected), 1)
        nr, nc = _subplot_grid(n)
        _, _, p_label = self.PARAM_MAP.get(self.dparam, ("r", None, self.dparam))
        self.axes = []
        for i in range(n):
            ax = self.fig.add_subplot(nr, nc, i + 1)
            label = next((lb for aid, _, lb, _, _ in ALGO_DEFS if aid == selected[i]), selected[i])
            _style_ax(ax, self.fig, f"Lyapunov: {label}", p_label, "u", initial=initial)
            self.axes.append(ax)
        if initial:
            self.canvas.draw_idle()

    def _compute(self):
        try:
            selected = [aid for aid in [d[0] for d in ALGO_DEFS] if self.algo_vars[aid].get()]
            if not selected:
                messagebox.showwarning("Pilihan Kosong", "Pilih minimal 1 algoritma.")
                return

            x0 = float(self.evars["x0"].get())
            rp = float(self.evars["r"].get())
            ap = float(self.evars["alpha"].get())
            bp = float(self.evars["beta"].get())
            lp = float(self.evars["lam"].get())

            p_key, prange, p_label = self.PARAM_MAP[self.dparam]
            self._setup_axes(selected, initial=False)

            N, d0 = 100, 1e-8
            results = []

            for algo_id in selected:
                lyap = []
                _, _, long_label, color, _ = next(d for d in ALGO_DEFS if d[0] == algo_id)

                for val in prange:
                    p = {"r": rp, "alpha": ap, "beta": bp, "lam": lp}
                    p[p_key] = val
                    cr, cl, ca, cb = p["r"], p["lam"], p["alpha"], p["beta"]

                    if algo_id == "seq":
                        # Sequential: rata-rata Lyapunov MS + Gauss
                        x1, x2, s1 = x0, x0 + d0, 0
                        for _ in range(N):
                            xn1 = _iterate_ms_map(x1, 1, cr, cl)[0]
                            xn2 = _iterate_ms_map(x2, 1, cr, cl)[0]
                            d1 = abs(xn1 - xn2)
                            if d1 > 0:
                                s1 += np.log(d1 / d0)
                                x2 = xn1 + d0 * (xn2 - xn1) / d1
                            else:
                                x2 = xn1 + d0
                            x1 = xn1
                        x1, x2, s2 = x0, x0 + d0, 0
                        for _ in range(N):
                            xn1 = _iterate_gauss_map(x1, 1, ca, cb)[0]
                            xn2 = _iterate_gauss_map(x2, 1, ca, cb)[0]
                            d1 = abs(xn1 - xn2)
                            if d1 > 0:
                                s2 += np.log(d1 / d0)
                                x2 = xn1 + d0 * (xn2 - xn1) / d1
                            else:
                                x2 = xn1 + d0
                            x1 = xn1
                        lyap.append((s1 + s2) / (2 * N))
                    else:
                        x1, x2, s = x0, x0 + d0, 0
                        for _ in range(N):
                            xn1 = _get_sequence(algo_id, x1, 1, cr, cl, ca, cb)[0]
                            xn2 = _get_sequence(algo_id, x2, 1, cr, cl, ca, cb)[0]
                            d1 = abs(xn1 - xn2)
                            if d1 > 0:
                                s += np.log(d1 / d0)
                                x2 = xn1 + d0 * (xn2 - xn1) / d1
                            else:
                                x2 = xn1 + d0
                            x1 = xn1
                        lyap.append(s / N)
                results.append((algo_id, np.array(lyap), long_label, color))

            # Skala Y terpadu (Unified Y-axis) agar konsisten di seluruh subplot
            all_min = min(arr.min() for _, arr, _, _ in results)
            all_max = max(arr.max() for _, arr, _, _ in results)
            y_low = min(all_min - 0.2, -0.3)
            y_high = max(all_max + 0.2, 0.5)

            for idx, (algo_id, arr, long_label, color) in enumerate(results):
                ax = self.axes[idx]
                ax.clear()

                # Tambahkan keterangan jika algoritma tidak dipengaruhi parameter yang diuji
                sub_title = f"Lyapunov: {long_label}"
                if algo_id == "gauss" and self.dparam in ("r", "lambda"):
                    sub_title += f" [konstan vs {p_label}]"
                elif algo_id == "ms" and self.dparam in ("a", "b"):
                    sub_title += f" [konstan vs {p_label}]"

                _style_ax(ax, self.fig, sub_title, p_label, "u")
                ax.plot(prange, arr, color=color, linewidth=1.5)
                ax.axhline(0, color="r", linestyle="--", linewidth=0.9)
                ax.fill_between(prange, arr, 0, where=(arr > 0), alpha=0.2, color=SUCCESS)
                ax.fill_between(prange, arr, 0, where=(arr <= 0), alpha=0.1, color=DANGER)
                ax.set_ylim(y_low, y_high)

            self.canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ============================================================
# BifurcationWindow
# ============================================================

class BifurcationWindow(_Base):
    PARAM_MAP = {
        "r":      ("r",     np.linspace(1.0, 4.0, 400), "r"),
        "a":      ("alpha", np.linspace(1.0, 8.0, 400), "alpha"),
        "b":      ("beta",  np.linspace(1.0, 5.0, 400), "beta"),
        "lambda": ("lam",   np.linspace(1.0, 5.0, 400), "lambda"),
    }

    def __init__(self, parent, app, default_param="r"):
        self.dparam = default_param
        super().__init__(parent, app, "Diagram Bifurkasi", "1100x620")
        self._build()

    def _build(self):
        w = self.win
        self._title_bar(w, "Diagram Bifurkasi - Analisis Sifat Kaotik", "Titik Padat = Chaotic")
        self._nav_row(w)

        fr_top = _lframe(w, " Parameter & Pilih Algoritma")
        fr_top.pack(fill="x", padx=12, pady=(4, 0))

        fields = [
            ("Iterasi", "iter", "300"), ("X0", "x0", "0.3"), ("r", "r", "3.5"),
            ("a", "alpha", "5.8"), ("b", "beta", "3.1"), ("l", "lam", "3.5"),
        ]
        self.evars = {}
        col = 0
        for ltext, key, dflt in fields:
            tk.Label(fr_top, text=ltext, bg=BG2, fg=FG2, font=F9).grid(row=0, column=col, padx=3, pady=4)
            e, v = _entry(fr_top, dflt, width=7)
            e.grid(row=0, column=col + 1, padx=(0, 8), pady=4)
            self.evars[key] = v
            col += 2

        self.algo_vars = {aid: tk.BooleanVar(value=default_on)
                         for aid, _, _, _, default_on in ALGO_DEFS}
        _build_algo_selector(fr_top, self.algo_vars).grid(row=0, column=col, padx=10, pady=4)
        col += 1
        _btn(fr_top, "Hitung Bifurkasi", self._compute, width=16).grid(row=0, column=col, padx=8, pady=4)

        # Frame pembatas grafik (Card Container)
        self.fl = _lframe(w, " Area Visualisasi Diagram Bifurkasi")
        self.fl.pack(fill="both", expand=True, padx=12, pady=(4, 6))

        # Matplotlib figure dengan layout="constrained" (responsif & terbingkai rapi)
        self.fig = plt.Figure(layout="constrained")
        self.fig.patch.set_facecolor(PLOT_BG)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.fl)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.configure(bg=BG2, highlightthickness=0, bd=0)
        canvas_widget.pack(fill="both", expand=True, padx=6, pady=6)

        selected = [aid for aid, _, _, _, on in ALGO_DEFS if on]
        self._setup_axes(selected, initial=True)

    def _setup_axes(self, selected, initial=False):
        self.fig.clf()
        n = max(len(selected), 1)
        nr, nc = _subplot_grid(n)
        _, _, p_label = self.PARAM_MAP.get(self.dparam, ("r", None, self.dparam))
        self.axes = []
        for i in range(n):
            ax = self.fig.add_subplot(nr, nc, i + 1)
            label = next((lb for aid, _, lb, _, _ in ALGO_DEFS if aid == selected[i]), selected[i])
            _style_ax(ax, self.fig, f"Bifurkasi: {label}", p_label, "Xn", initial=initial)
            self.axes.append(ax)
        if initial:
            self.canvas.draw_idle()

    def _compute(self):
        try:
            selected = [aid for aid in [d[0] for d in ALGO_DEFS] if self.algo_vars[aid].get()]
            if not selected:
                messagebox.showwarning("Pilihan Kosong", "Pilih minimal 1 algoritma.")
                return

            itrs = int(self.evars["iter"].get())
            x0   = float(self.evars["x0"].get())
            rp   = float(self.evars["r"].get())
            ap   = float(self.evars["alpha"].get())
            bp   = float(self.evars["beta"].get())
            lp   = float(self.evars["lam"].get())
            p_key, prange, p_label = self.PARAM_MAP[self.dparam]
            drop = 100

            self._setup_axes(selected, initial=False)

            for idx, algo_id in enumerate(selected):
                _, _, long_label, color, _ = next(d for d in ALGO_DEFS if d[0] == algo_id)
                ax = self.axes[idx]
                ax.clear()

                sub_title = f"Bifurkasi: {long_label}"
                if algo_id == "gauss" and self.dparam in ("r", "lambda"):
                    sub_title += f" [konstan vs {p_label}]"
                elif algo_id == "ms" and self.dparam in ("a", "b"):
                    sub_title += f" [konstan vs {p_label}]"

                _style_ax(ax, self.fig, sub_title, p_label, "Xn")

                for val in prange:
                    p = {"r": rp, "alpha": ap, "beta": bp, "lam": lp}
                    p[p_key] = val
                    cr, cl, ca, cb = p["r"], p["lam"], p["alpha"], p["beta"]
                    seq = _get_sequence(algo_id, x0, itrs + drop, cr, cl, ca, cb)[drop:]
                    ax.plot([val] * itrs, seq, ",", color=color, alpha=0.6)

                # Skala sumbu Y konsisten 0.0 sampai 1.0
                ax.set_ylim(-0.02, 1.02)
                ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])

            self.canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ============================================================
# ScatterPlotWindow
# ============================================================

class ScatterPlotWindow(_Base):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Scatter Plot Sensitivitas", "1100x620")
        self._build()

    def _build(self):
        w = self.win
        self._title_bar(w, "Scatter Plot - Kepekaan Kondisi Awal (Butterfly Effect)",
                        "Membandingkan 3 Kunci yang nyaris sama")
        self._nav_row(w)

        fr_top = _lframe(w, " Parameter & Pilih Algoritma")
        fr_top.pack(fill="x", padx=12, pady=(4, 0))

        fields = [
            ("r", "r", "3.99"), ("a", "alpha", "5.8"),
            ("b", "beta", "3.1"), ("l", "lam", "3.5"),
        ]
        self.evars = {}
        col = 0
        for ltext, key, dflt in fields:
            tk.Label(fr_top, text=ltext, bg=BG2, fg=FG2, font=F9).grid(row=0, column=col, padx=3, pady=4)
            e, v = _entry(fr_top, dflt, width=7)
            e.grid(row=0, column=col + 1, padx=(0, 8), pady=4)
            self.evars[key] = v
            col += 2

        self.algo_vars = {aid: tk.BooleanVar(value=default_on)
                         for aid, _, _, _, default_on in ALGO_DEFS}
        _build_algo_selector(fr_top, self.algo_vars).grid(row=0, column=col, padx=10, pady=4)
        col += 1
        _btn(fr_top, "Plot Sensitivitas", self._compute, width=16).grid(row=0, column=col, padx=8, pady=4)

        # Frame pembatas grafik (Card Container)
        self.fl = _lframe(w, " Area Visualisasi Scatter Plot Keystream")
        self.fl.pack(fill="both", expand=True, padx=12, pady=(4, 6))

        # Matplotlib figure dengan layout="constrained" (responsif & terbingkai rapi)
        self.fig = plt.Figure(layout="constrained")
        self.fig.patch.set_facecolor(PLOT_BG)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.fl)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.configure(bg=BG2, highlightthickness=0, bd=0)
        canvas_widget.pack(fill="both", expand=True, padx=6, pady=6)

        selected = [aid for aid, _, _, _, on in ALGO_DEFS if on]
        self._setup_axes(selected, initial=True)

    def _setup_axes(self, selected, initial=False):
        self.fig.clf()
        n = max(len(selected), 1)
        nr, nc = _subplot_grid(n)
        self.axes = []
        for i in range(n):
            ax = self.fig.add_subplot(nr, nc, i + 1)
            label = next((lb for aid, _, lb, _, _ in ALGO_DEFS if aid == selected[i]), selected[i])
            _style_ax(ax, self.fig, f"Scatter: {label}", "Indeks", "Xn", initial=initial)
            self.axes.append(ax)
        if initial:
            self.canvas.draw_idle()

    def _compute(self):
        try:
            selected = [aid for aid in [d[0] for d in ALGO_DEFS] if self.algo_vars[aid].get()]
            if not selected:
                messagebox.showwarning("Pilihan Kosong", "Pilih minimal 1 algoritma.")
                return

            rp = float(self.evars["r"].get())
            ap = float(self.evars["alpha"].get())
            bp = float(self.evars["beta"].get())
            lp = float(self.evars["lam"].get())

            n = 200
            X0_VALS   = [0.3, 0.3001, 0.30001]
            PT_COLORS = ["#2563EB", "#DC2626", "#059669"]
            PT_MARKS  = ["o", "x", "^"]
            PT_LABELS = ["x=0.3", "x=0.3001", "x=0.30001"]
            idx = np.arange(n)

            self._setup_axes(selected, initial=False)

            for plot_idx, algo_id in enumerate(selected):
                _, _, long_label, _, _ = next(d for d in ALGO_DEFS if d[0] == algo_id)
                ax = self.axes[plot_idx]
                ax.clear()
                _style_ax(ax, self.fig, f"Scatter: {long_label}", "Indeks", "Xn")

                for xv, pc, pm, pl in zip(X0_VALS, PT_COLORS, PT_MARKS, PT_LABELS):
                    seq = _get_sequence(algo_id, xv, n, rp, lp, ap, bp)
                    ax.scatter(idx, seq, c=pc, marker=pm, s=8, label=pl, alpha=0.8)
                ax.legend(loc="upper right", fontsize=7)

                # Skala sumbu Y konsisten 0.0 sampai 1.0
                ax.set_ylim(-0.02, 1.02)
                ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
                ax.set_xlim(-5, n + 5)

            self.canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", str(e))