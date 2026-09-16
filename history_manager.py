"""
history_manager.py — Manajer Riwayat Operasi Enkripsi & Dekripsi
=================================================================
File ini mencatat dan menyimpan semua operasi enkripsi/dekripsi
yang dilakukan pengguna selama program berjalan (dalam satu sesi).

FUNGSI UTAMA FILE INI:
  1. Menyimpan setiap operasi enkripsi/dekripsi ke dalam daftar riwayat
  2. Mencatat informasi lengkap setiap operasi (waktu, algoritma, durasi, dll.)
  3. Menyediakan fungsi untuk membaca, menghapus, dan mengekspor riwayat
  4. Mengekspor riwayat ke file CSV atau JSON untuk dokumentasi

INFORMASI YANG DICATAT SETIAP OPERASI:
  - Waktu operasi (tanggal & jam)
  - Jenis operasi: Enkripsi atau Dekripsi
  - Algoritma yang dipakai (MS Map, Gauss Map, dll.)
  - Parameter kunci yang digunakan (X0, r, α, β, λ)
  - Ukuran gambar (resolusi)
  - Durasi proses (dalam detik)
  - Path file input dan output
  - Metrik kualitas hasil (entropi, NPCR, UACI, dll.)

POLA DESAIN:
  - Menggunakan pola Singleton: satu objek `history` dipakai seluruh program
  - Data disimpan hanya di memori RAM (tidak ke file permanen secara otomatis)
  - Untuk menyimpan permanen, gunakan fitur Export CSV/JSON dari GUI

CATATAN:
  - Riwayat akan hilang saat program ditutup (kecuali sudah diekspor)
  - Import objek `history` dari file ini untuk menambah/membaca data
"""

import json
import time
from datetime import datetime
from pathlib import Path


# ── Konstanta jenis operasi ──────────────────────────────────────────────────

OP_ENCRYPT = "Enkripsi"
OP_DECRYPT  = "Dekripsi"


# ── Kelas entri riwayat ───────────────────────────────────────────────────────

class HistoryEntry:
    """Satu entri riwayat operasi."""

    _counter = 0  # auto-increment ID

    def __init__(
        self,
        operation: str,          # OP_ENCRYPT | OP_DECRYPT
        algorithm: str,
        params: dict,
        image_shape: tuple,      # (H, W) atau (H, W, C)
        elapsed_ms: float,
        input_path: str  = "",
        output_path: str = "",
        metrics: dict    = None,
    ):
        HistoryEntry._counter += 1
        self.id           = HistoryEntry._counter
        self.operation    = operation
        self.algorithm    = algorithm
        self.params       = dict(params)
        self.image_shape  = image_shape
        self.elapsed_ms   = elapsed_ms
        self.input_path   = input_path
        self.output_path  = output_path
        self.metrics      = metrics or {}
        self.timestamp    = datetime.now()

    # ── Properti turunan ─────────────────────────────────────────────────────

    @property
    def timestamp_str(self) -> str:
        return self.timestamp.strftime("%d/%m/%Y %H:%M:%S")

    @property
    def shape_str(self) -> str:
        if len(self.image_shape) == 3:
            h, w, c = self.image_shape
            mode = "RGB" if c == 3 else f"{c}ch"
            return f"{w}×{h} px  [{mode}]"
        elif len(self.image_shape) == 2:
            h, w = self.image_shape
            return f"{w}×{h} px  [Gray]"
        return str(self.image_shape)

    @property
    def pixel_count(self) -> int:
        if len(self.image_shape) >= 2:
            return self.image_shape[0] * self.image_shape[1]
        return 0

    @property
    def throughput_str(self) -> str:
        """Throughput dalam Mpx/s."""
        if self.elapsed_ms > 0 and self.pixel_count > 0:
            mpx = self.pixel_count / (self.elapsed_ms / 1000) / 1_000_000
            return f"{mpx:.2f} Mpx/s"
        return "—"

    @property
    def input_filename(self) -> str:
        return Path(self.input_path).name if self.input_path else "—"

    @property
    def output_filename(self) -> str:
        return Path(self.output_path).name if self.output_path else "—"

    # ── Serialisasi ──────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "timestamp":   self.timestamp.isoformat(),
            "operation":   self.operation,
            "algorithm":   self.algorithm,
            "params":      self.params,
            "image_shape": list(self.image_shape),
            "elapsed_ms":  round(self.elapsed_ms, 3),
            "input_path":  self.input_path,
            "output_path": self.output_path,
            "metrics":     self.metrics,
        }

    @classmethod
    def from_dict(cls, data: dict):
        entry = cls(
            operation=data.get("operation", ""),
            algorithm=data.get("algorithm", ""),
            params=data.get("params", {}),
            image_shape=tuple(data.get("image_shape", [])),
            elapsed_ms=data.get("elapsed_ms", 0.0),
            input_path=data.get("input_path", ""),
            output_path=data.get("output_path", ""),
            metrics=data.get("metrics", {})
        )
        if "id" in data:
            entry.id = data["id"]
        if "timestamp" in data:
            entry.timestamp = datetime.fromisoformat(data["timestamp"])
        return entry

    def detail_text(self) -> str:
        """Teks detail lengkap untuk ditampilkan di panel info."""
        lines = []
        a = lines.append

        a("═" * 54)
        icon = "🔒" if self.operation == OP_ENCRYPT else "🔓"
        a(f"  {icon}  {self.operation.upper()}  —  #{self.id}")
        a("═" * 54)

        a(f"\n📅  Waktu Operasi")
        a(f"    {self.timestamp_str}")

        a(f"\n⚙️   Algoritma")
        a(f"    {self.algorithm}")

        a(f"\n🖼️   Informasi Gambar")
        a(f"    Ukuran    : {self.shape_str}")
        a(f"    Pixel     : {self.pixel_count:,} px")

        a(f"\n⏱️   Performa")
        a(f"    Durasi    : {self.elapsed_ms:.2f} ms")
        a(f"    Throughput: {self.throughput_str}")

        a(f"\n📁  File")
        a(f"    Input     : {self.input_path or '—'}")
        a(f"    Output    : {self.output_path or '—'}")

        a(f"\n🔑  Parameter Chaos")
        param_labels = {
            "x0":      "X₀  (kondisi awal)",
            "r":       "r   (MS Map)",
            "alpha":   "α   (alpha, Gauss)",
            "beta":    "β   (beta, Gauss)",
            "lam":     "λ   (lambda, MS)",
            "skip":    "Skip (transient)",
        }
        for k, v in self.params.items():
            label = param_labels.get(k, k)
            a(f"    {label:<22}: {v}")

        if self.metrics:
            a(f"\n📊  Metrik Kualitas")
            metric_labels = {
                "entropy_original":  "Entropy Asli",
                "entropy_encrypted": "Entropy Terenkripsi",
                "entropy_decrypted": "Entropy Terdekripsi",
                "npcr":              "NPCR (%)",
                "uaci":              "UACI (%)",
                "psnr":              "PSNR (dB)",
                "mse":               "MSE",
                "corr_orig_H":       "Korelasi Asli (H)",
                "corr_enc_H":        "Korelasi Enkripsi (H)",
                "corr_orig_V":       "Korelasi Asli (V)",
                "corr_enc_V":        "Korelasi Enkripsi (V)",
                "corr_orig_D":       "Korelasi Asli (D)",
                "corr_enc_D":        "Korelasi Enkripsi (D)",
            }
            for k, v in self.metrics.items():
                label = metric_labels.get(k, k)
                if isinstance(v, float):
                    a(f"    {label:<28}: {v:.6f}")
                else:
                    a(f"    {label:<28}: {v}")

        a("\n" + "─" * 54)
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# SINGLETON: HistoryManager
# ══════════════════════════════════════════════════════════════════════════════

class _HistoryManager:
    """Manajer riwayat global (singleton)."""

    def __init__(self):
        self._entries: list[HistoryEntry] = []
        self._listeners: list = []      # callback saat ada perubahan
        self._load_auto_save()

    def _load_auto_save(self):
        save_path = Path("auto_save_history.json")
        if save_path.exists():
            try:
                with open(save_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for d in data:
                    self._entries.append(HistoryEntry.from_dict(d))
                HistoryEntry._counter = max([e.id for e in self._entries], default=0)
            except Exception as e:
                print(f"Gagal memuat riwayat otomatis: {e}")

    def _save_auto_save(self):
        save_path = Path("auto_save_history.json")
        try:
            data = [e.to_dict() for e in self._entries]
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Gagal menyimpan riwayat otomatis: {e}")

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def add(self, entry: HistoryEntry) -> None:
        """Tambah entri baru dan notifikasi listener."""
        self._entries.append(entry)
        self._save_auto_save()
        self._notify()

    def clear(self) -> None:
        self._entries.clear()
        HistoryEntry._counter = 0
        self._save_auto_save()
        self._notify()

    def remove(self, entry_id: int) -> None:
        self._entries = [e for e in self._entries if e.id != entry_id]
        self._save_auto_save()
        self._notify()

    # ── Query ────────────────────────────────────────────────────────────────

    def all(self) -> list:
        return list(reversed(self._entries))   # terbaru di atas

    def filter(self, operation=None, algorithm=None, text=None) -> list:
        result = self._entries
        if operation:
            result = [e for e in result if e.operation == operation]
        if algorithm:
            result = [e for e in result if algorithm.lower() in e.algorithm.lower()]
        if text:
            t = text.lower()
            result = [e for e in result
                      if t in e.input_filename.lower()
                      or t in e.algorithm.lower()
                      or t in e.timestamp_str]
        return list(reversed(result))

    @property
    def count(self) -> int:
        return len(self._entries)

    @property
    def enc_count(self) -> int:
        return sum(1 for e in self._entries if e.operation == OP_ENCRYPT)

    @property
    def dec_count(self) -> int:
        return sum(1 for e in self._entries if e.operation == OP_DECRYPT)

    # ── Listener pattern ─────────────────────────────────────────────────────

    def subscribe(self, callback) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(self, callback) -> None:
        self._listeners = [cb for cb in self._listeners if cb != callback]

    def _notify(self) -> None:
        for cb in list(self._listeners):
            try:
                cb()
            except Exception:
                pass

    # ── Export ───────────────────────────────────────────────────────────────

    def export_json(self, path: str) -> None:
        data = [e.to_dict() for e in self._entries]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def export_csv(self, path: str) -> None:
        import csv
        fieldnames = [
            "id", "timestamp", "operation", "algorithm",
            "image_shape", "elapsed_ms", "throughput",
            "input_path", "output_path",
            "x0", "r", "alpha", "beta", "lam", "skip",
            "entropy_encrypted", "npcr", "uaci", "psnr",
        ]
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for e in self._entries:
                row = {
                    "id":                 e.id,
                    "timestamp":          e.timestamp_str,
                    "operation":          e.operation,
                    "algorithm":          e.algorithm,
                    "image_shape":        e.shape_str,
                    "elapsed_ms":         round(e.elapsed_ms, 3),
                    "throughput":         e.throughput_str,
                    "input_path":         e.input_path,
                    "output_path":        e.output_path,
                    **{k: v for k, v in e.params.items()
                       if k in ("x0", "r", "alpha", "beta", "lam", "skip")},
                    **{k: round(v, 6) if isinstance(v, float) else v
                       for k, v in e.metrics.items()
                       if k in ("entropy_encrypted", "npcr", "uaci", "psnr")},
                }
                writer.writerow(row)


# ── Instance global ───────────────────────────────────────────────────────────

history = _HistoryManager()
