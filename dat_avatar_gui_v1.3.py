import struct
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
import os
import math
import uuid

# ---------- Helpers for endianness and bytes ----------
def read_u32_le(b: bytes, off: int) -> int:
    return struct.unpack_from("<I", b, off)[0]

def write_u32_le(barr: bytearray, off: int, val: int):
    struct.pack_into("<I", barr, off, int(val))

def read_i32_le(b: bytes, off: int) -> int:
    return struct.unpack_from("<i", b, off)[0]

def write_i32_le(barr: bytearray, off: int, val: int):
    struct.pack_into("<i", barr, off, int(val))

def read_u8(b: bytes, off: int) -> int:
    return b[off]

def write_u8(barr: bytearray, off: int, val: int):
    barr[off] = int(val) & 0xFF

def read_str(b: bytes, off: int, length: int) -> str:
    s = b[off:off+length]
    s = s.split(b'\x00', 1)[0]
    try:
        return s.decode("utf-8")
    except:
        try:
            return s.decode("latin-1")
        except:
            return s.hex()

def write_str(barr: bytearray, off: int, length: int, text: str):
    raw = text.encode("utf-8", errors="ignore")[:length]
    barr[off:off+length] = b'\x00' * length
    barr[off:off+length] = raw + b'\x00' * (length - len(raw))

# ---------- Record maps (translated labels) ----------
NORMAL_SIZE = 644
EXITEM_SIZE = 684

NORMAL_MAP = {
    "avatar_code": (0, "u32", None),
    "image_number": (4, "u32", None),
    "name": (12, "str", 19),
    "show_in_shop": (35, "u8", None),
    "sell_weekly": (37, "u8", None),
    "sell_monthly": (60, "u8", None),
    "sell_eternal": (84, "u8", None),
    "price_weekly_gold": (40, "u32", None),
    "price_weekly_cash": (44, "u32", None),
    "price_monthly_gold": (64, "u32", None),
    "price_monthly_cash": (68, "u32", None),
    "price_eternal_gold": (88, "u32", None),
    "price_eternal_cash": (92, "u32", None),
    "enable_sale_gold": (96, "u8", None),
    "enable_sale_cash": (97, "u8", None),
    "description": (132, "str", 63),
    "crater_attack": (104, "i32", None),
    "attack": (108, "i32", None),
    "defense": (112, "i32", None),
    "energy": (116, "i32", None),
    "shield_regen": (120, "i32", None),
    "item_delay": (124, "i32", None),
    "popularity": (128, "i32", None),
}

EXITEM_MAP = {
    "avatar_code": (0, "u32", None),
    "ex_number": (8, "u32", None),
    "name": (20, "str", 19),
    "show_in_shop": (43, "u8", None),
    "sell_weekly": (45, "u8", None),
    "sell_monthly": (68, "u8", None),
    "sell_eternal": (92, "u8", None),
    "price_weekly_gold": (48, "u32", None),
    "price_weekly_cash": (52, "u32", None),
    "price_monthly_gold": (72, "u32", None),
    "price_monthly_cash": (76, "u32", None),
    "price_eternal_gold": (96, "u32", None),
    "price_eternal_cash": (100, "u32", None),
    "enable_sale_gold": (104, "u8", None),
    "enable_sale_cash": (105, "u8", None),
    "description": (132, "str", 63),
}

# Columns to show in the table (order)
COLUMNS = [
    "index",
    "type",
    "avatar_code",
    "image_number",
    "ex_number",
    "name",
    "show_in_shop",
    "enable_sale_gold",
    "enable_sale_cash",
    "sell_weekly",
    "price_weekly_gold",
    "price_weekly_cash",
    "sell_monthly",
    "price_monthly_gold",
    "price_monthly_cash",
    "sell_eternal",
    "price_eternal_gold",
    "price_eternal_cash",
    "attack",
    "defense",
    "energy",
    "shield_regen",
    "item_delay",
    "popularity",
]

@dataclass
class Record:
    index: int
    type: str  # "Normal" or "Ex-item"
    raw_off: int
    data: Dict[str, Any] = field(default_factory=dict)

class DATModel:
    def __init__(self):
        self.path: Optional[str] = None
        self.data: bytearray = bytearray()
        self.records: List[Record] = []

    def load(self, path: str):
        with open(path, "rb") as f:
            buf = f.read()
        self.path = path
        self.data = bytearray(buf)
        self._parse()

    def detect_record_size(self, total: int) -> int:
        payload = max(0, total - 4)
        if payload % NORMAL_SIZE == 0:
            print(f"Detected Normal record size: {NORMAL_SIZE} bytes")
            return NORMAL_SIZE
        if payload % EXITEM_SIZE == 0:
            print(f"Detected Ex-item record size: {EXITEM_SIZE} bytes")
            return EXITEM_SIZE
        print(f"Fallback to Normal record size: {NORMAL_SIZE} bytes")
        return NORMAL_SIZE

    def _parse(self):
        self.records.clear()
        total = len(self.data)
        size = self.detect_record_size(total)
        header = 4
        count = (total - header) // size
        print(f"Parsing {count} records, header size: {header}, record size: {size}")
        for i in range(count):
            off = header + i * size
            print(f"Record {i}, start offset: {hex(off)}")
            rtype = "Normal" if size == NORMAL_SIZE else "Ex-item"
            m = NORMAL_MAP if rtype == "Normal" else EXITEM_MAP
            rec = {}
            for k, (o, t, L) in m.items():
                oo = off + o
                try:
                    if oo >= len(self.data):
                        raise IndexError(f"Offset {hex(oo)} exceeds file length {len(self.data)}")
                    if t == "u32":
                        rec[k] = read_u32_le(self.data, oo)
                    elif t == "i32":
                        rec[k] = read_i32_le(self.data, oo)
                    elif t == "u8":
                        val = read_u8(self.data, oo)
                        if k == "show_in_shop":
                            print(f"Record {i}, show_in_shop at offset {hex(oo)}, raw byte: {hex(val)}")
                            rec[k] = 1 if val != 0 else 0
                            print(f"Record {i}, show_in_shop normalized: {rec[k]}")
                        else:
                            rec[k] = val
                    elif t == "str":
                        rec[k] = read_str(self.data, oo, L)
                except Exception as e:
                    print(f"Error parsing {k} at offset {hex(oo)}: {e}")
                    rec[k] = None
            if rtype == "Normal":
                rec.setdefault("ex_number", None)
            else:
                rec.setdefault("image_number", None)
                for field in ["crater_attack", "attack", "defense", "energy", "shield_regen", "item_delay", "popularity"]:
                    rec.setdefault(field, None)
            self.records.append(Record(index=i, type=rtype, raw_off=off, data=rec))

    def save(self, path: Optional[str] = None):
        out = path or self.path
        if not out:
            raise RuntimeError("Tidak ada path output yang ditentukan")
        # Check file permissions and lock
        try:
            if os.path.exists(out):
                if not os.access(out, os.W_OK):
                    raise PermissionError(f"Tidak punya izin untuk menulis ke {out}")
                # Try opening file to check if it's locked
                with open(out, "ab") as f:
                    pass
        except PermissionError as e:
            raise PermissionError(f"Gagal menyimpan: Tidak bisa menulis ke {out}. Pastikan file tidak terkunci atau dibuka program lain.")
        except Exception as e:
            raise RuntimeError(f"Gagal memeriksa file {out}: {e}. Pastikan file tidak dibuka program lain.")
        # Check buffer size
        expected_size = 4 + len(self.records) * (NORMAL_SIZE if self.records and self.records[0].type == "Normal" else EXITEM_SIZE)
        print(f"Saving to {out}, expected buffer size: {expected_size}, actual: {len(self.data)}")
        if len(self.data) < expected_size:
            print(f"Warning: Buffer size {len(self.data)} smaller than expected {expected_size}")
        for rec in self.records:
            m = NORMAL_MAP if rec.type == "Normal" else EXITEM_MAP
            base = rec.raw_off
            for k, (o, t, L) in m.items():
                if k not in rec.data:
                    continue
                oo = base + o
                val = rec.data[k]
                try:
                    if oo >= len(self.data):
                        raise IndexError(f"Offset {hex(oo)} exceeds buffer length {len(self.data)}")
                    print(f"Writing {k} at offset {hex(oo)}, value: {val}")
                    if t == "u32":
                        write_u32_le(self.data, oo, int(val))
                    elif t == "i32":
                        write_i32_le(self.data, oo, int(val))
                    elif t == "u8":
                        if k == "show_in_shop":
                            write_u8(self.data, oo, 1 if val != 0 else 0)
                            print(f"Writing show_in_shop at offset {hex(oo)}: {1 if val != 0 else 0}")
                        else:
                            write_u8(self.data, oo, int(val))
                    elif t == "str":
                        write_str(self.data, oo, L, str(val or ""))
                except Exception as e:
                    print(f"Error writing {k} at offset {hex(oo)}: {e}")
                    raise RuntimeError(f"Gagal menulis {k} di offset {hex(oo)}: {e}")
        try:
            with open(out, "wb") as f:
                f.write(self.data)
            print(f"Successfully saved to {out}")
        except Exception as e:
            raise RuntimeError(f"Gagal menyimpan ke {out}: {e}. Pastikan file tidak dibuka program lain.")

    def export_sql_menu(self, path: str):
        """Export records with show_in_shop=1 to SQL INSERT statements for menu table."""
        sql = "#################################\n###   BY FIRELORDZ(Agasready)   ###\n#################################\n\n"
        for rec in self.records:
            if rec.data.get("show_in_shop", 0) != 1:
                continue
            gold_weekly = rec.data.get("price_weekly_gold", 0) if rec.data.get("enable_sale_gold", 0) == 1 and rec.data.get("sell_weekly", 0) == 1 else 0
            gold_monthly = rec.data.get("price_monthly_gold", 0) if rec.data.get("enable_sale_gold", 0) == 1 and rec.data.get("sell_monthly", 0) == 1 else 0
            gold_eternal = rec.data.get("price_eternal_gold", 0) if rec.data.get("enable_sale_gold", 0) == 1 and rec.data.get("sell_eternal", 0) == 1 else 0
            cash_weekly = rec.data.get("price_weekly_cash", 0) if rec.data.get("enable_sale_cash", 0) == 1 and rec.data.get("sell_weekly", 0) == 1 else 0
            cash_monthly = rec.data.get("price_monthly_cash", 0) if rec.data.get("enable_sale_cash", 0) == 1 and rec.data.get("sell_monthly", 0) == 1 else 0
            cash_eternal = rec.data.get("price_eternal_cash", 0) if rec.data.get("enable_sale_cash", 0) == 1 and rec.data.get("sell_eternal", 0) == 1 else 0
            avatar_code = rec.data.get("avatar_code", 0)
            sql += f"INSERT INTO menu (No, Item1, PriceByGoldForW, PriceByGoldForM, PriceByGoldForI, PriceByCashForW, PriceByCashForM, PriceByCashForI, Period1, Volume1) VALUES ('{avatar_code}', '{avatar_code}', '{gold_weekly}', '{gold_monthly}', '{gold_eternal}', '{cash_weekly}', '{cash_monthly}', '{cash_eternal}', '86400', '1');\n"
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(sql)
            print(f"Successfully exported SQL Menu to {path}")
        except Exception as e:
            raise RuntimeError(f"Gagal menyimpan SQL Menu ke {path}: {e}")

    def export_sql_item(self, path: str):
        """Export records with show_in_shop=1 to SQL INSERT statements for item table."""
        sql = "#################################\n###   BY FIRELORDZ(Agasready)   ###\n#################################\n\n"
        for rec in self.records:
            if rec.data.get("show_in_shop", 0) != 1:
                continue
            price_eternal_gold = rec.data.get("price_eternal_gold", 0)
            preco = math.floor((price_eternal_gold / 100) * 60)
            avatar_code = rec.data.get("avatar_code", 0)
            sql += f"INSERT INTO item (No, Refund_C, Refund_G, Refund_T, Refund_E) VALUES ('{avatar_code}', '{preco}', '{preco}', '{preco}', '{preco}');\n"
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(sql)
            print(f"Successfully exported SQL Item to {path}")
        except Exception as e:
            raise RuntimeError(f"Gagal menyimpan SQL Item ke {path}: {e}")

# ---------- GUI ----------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Avatar Editor by Firelordz")
        self.geometry("1280x720")
        self.model = DATModel()
        self._build_ui()

    def _build_ui(self):
        # Top bar
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)
        ttk.Button(top, text="Open DAT", command=self.on_open).pack(side="left")
        ttk.Button(top, text="Save", command=self.on_save).pack(side="left", padx=6)
        ttk.Button(top, text="Save As...", command=self.on_save_as).pack(side="left")
        ttk.Button(top, text="Export SQL Menu", command=self.on_export_sql_menu).pack(side="left", padx=6)
        ttk.Button(top, text="Export SQL Item", command=self.on_export_sql_item).pack(side="left", padx=6)
        ttk.Label(top, text="Filter Type:").pack(side="left", padx=(20,4))
        self.type_filter = ttk.Combobox(top, values=["All","Normal","Ex-item"], state="readonly", width=10)
        self.type_filter.current(0)
        self.type_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
        self.type_filter.pack(side="left")
        ttk.Label(top, text="Avatar Image:").pack(side="left", padx=(20,4))
        self.avatar_image_var = tk.StringVar()
        self.avatar_image_cb = ttk.Combobox(top, textvariable=self.avatar_image_var, values=[str(i) for i in range(0,10000)], width=8)
        self.avatar_image_cb.bind("<<ComboboxSelected>>", self.on_change_image_number)
        self.avatar_image_cb.pack(side="left")
        # Batch edit controls
        batch = ttk.Frame(self)
        batch.pack(fill="x", padx=8, pady=(0,6))
        ttk.Label(batch, text="Batch edit selected → Field:").pack(side="left")
        self.batch_field = ttk.Combobox(batch, state="readonly", width=24,
            values=[
                "show_in_shop",
                "enable_sale_gold",
                "enable_sale_cash",
                "sell_weekly",
                "sell_monthly",
                "sell_eternal",
                "price_weekly_gold",
                "price_weekly_cash",
                "price_monthly_gold",
                "price_monthly_cash",
                "price_eternal_gold",
                "price_eternal_cash",
                "attack",
                "defense",
                "energy",
                "shield_regen",
                "item_delay",
                "popularity",
                "name"  # Ditambahkan untuk mendukung batch edit nama
            ])
        self.batch_field.pack(side="left", padx=6)
        ttk.Label(batch, text="Value:").pack(side="left")
        self.batch_value = tk.Entry(batch, width=12)
        self.batch_value.pack(side="left", padx=4)
        ttk.Button(batch, text="Apply to Selected", command=self.apply_batch).pack(side="left", padx=8)
        # Table with scrollbars
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=8, pady=6)
        v_scroll = ttk.Scrollbar(table_frame, orient="vertical")
        v_scroll.pack(side="right", fill="y")
        h_scroll = ttk.Scrollbar(table_frame, orient="horizontal")
        h_scroll.pack(side="bottom", fill="x")
        self.tree = ttk.Treeview(table_frame, columns=COLUMNS, show="headings", selectmode="extended",
                                 yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.tree.pack(fill="both", expand=True)
        v_scroll.configure(command=self.tree.yview)
        h_scroll.configure(command=self.tree.xview)
        headers = {
            "index": "#",
            "type": "Type",
            "avatar_code": "Avatar Code",
            "image_number": "Image #",
            "ex_number": "EX #",
            "name": "Name",
            "show_in_shop": "Visible",
            "enable_sale_gold": "Enable Gold",
            "enable_sale_cash": "Enable Cash",
            "sell_weekly": "Sell Weekly",
            "price_weekly_gold": "Weekly Gold",
            "price_weekly_cash": "Weekly Cash",
            "sell_monthly": "Sell Monthly",
            "price_monthly_gold": "Monthly Gold",
            "price_monthly_cash": "Monthly Cash",
            "sell_eternal": "Sell Eternal",
            "price_eternal_gold": "Eternal Gold",
            "price_eternal_cash": "Eternal Cash",
            "attack": "Attack",
            "defense": "Defense",
            "energy": "Energy",
            "shield_regen": "Shield Regen",
            "item_delay": "Item Delay",
            "popularity": "Popularity",
        }
        for col in COLUMNS:
            self.tree.heading(col, text=headers.get(col, col))
            self.tree.column(col, width=100 if col not in ("name", "description") else 220, anchor="center")
        self.tree.bind("<<TreeviewSelect>>", self.on_select_row)
        self.tree.bind("<Double-1>", self.on_double_click_cell)
        # Status
        self.status = tk.StringVar(value="No file loaded")
        ttk.Label(self, textvariable=self.status, anchor="w").pack(fill="x", padx=8, pady=(0,8))

    def on_open(self):
        p = filedialog.askopenfilename(title="Open DAT", filetypes=[("DAT files","*.dat"),("All files","*.*")])
        if not p: return
        try:
            self.model.load(p)
            self.status.set(f"Loaded: {p} ({len(self.model.records)} records)")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal load: {e}")

    def on_save(self):
        if not self.model.path:
            return self.on_save_as()
        try:
            self._sync_current_selection_edits()
            self.model.save(self.model.path)
            self.status.set(f"Tersimpan: {self.model.path}")
        except PermissionError as e:
            messagebox.showerror("Error", f"Gagal simpan: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal simpan: {e}")

    def on_save_as(self):
        p = filedialog.asksaveasfilename(title="Save DAT as...", defaultextension=".dat",
                                         filetypes=[("DAT files","*.dat"),("All files","*.*")])
        if not p: return
        try:
            self._sync_current_selection_edits()
            self.model.save(p)
            self.status.set(f"Tersimpan: {p}")
        except PermissionError as e:
            messagebox.showerror("Error", f"Gagal simpan: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal simpan: {e}")

    def on_export_sql_menu(self):
        if not self.model.records:
            messagebox.showerror("Error", "Tidak ada data untuk diekspor. Load file DAT terlebih dahulu.")
            return
        p = filedialog.asksaveasfilename(title="Save SQL Menu as...", defaultextension=".txt",
                                         filetypes=[("Text files","*.txt"),("All files","*.*")])
        if not p: return
        try:
            self.model.export_sql_menu(p)
            self.status.set(f"Tersimpan SQL Menu: {p}")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal ekspor SQL Menu: {e}")

    def on_export_sql_item(self):
        if not self.model.records:
            messagebox.showerror("Error", "Tidak ada data untuk diekspor. Load file DAT terlebih dahulu.")
            return
        p = filedialog.asksaveasfilename(title="Save SQL Item as...", defaultextension=".txt",
                                         filetypes=[("Text files","*.txt"),("All files","*.*")])
        if not p: return
        try:
            self.model.export_sql_item(p)
            self.status.set(f"Tersimpan SQL Item: {p}")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal ekspor SQL Item: {e}")

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        want = self.type_filter.get()
        for rec in self.model.records:
            if want != "All" and rec.type != want:
                continue
            row = []
            for col in COLUMNS:
                if col == "index":
                    row.append(rec.index)
                elif col == "type":
                    row.append(rec.type)
                else:
                    value = rec.data.get(col, "")
                    row.append(str(value) if value is not None else "")
            print(f"Record {rec.index}, row data for Treeview: {row}")
            self.tree.insert("", "end", iid=str(rec.index), values=row)

    def on_select_row(self, event=None):
        sels = self.tree.selection()
        if not sels:
            return
        idx = int(sels[0])
        rec = self.model.records[idx]
        if rec.type == "Normal":
            val = rec.data.get("image_number", 0)
        else:
            val = rec.data.get("ex_number", 0)
        self.avatar_image_var.set(str(val))

    def on_change_image_number(self, event=None):
        sels = self.tree.selection()
        if not sels:
            return
        try:
            newval = int(self.avatar_image_cb.get())
        except:
            messagebox.showerror("Invalid", "Pilih angka")
            return
        for iid in sels:
            idx = int(iid)
            rec = self.model.records[idx]
            if rec.type == "Normal":
                rec.data["image_number"] = newval
            else:
                rec.data["ex_number"] = newval
            vals = list(self.tree.item(iid, "values"))
            col_idx = COLUMNS.index("image_number" if rec.type=="Normal" else "ex_number")
            vals[col_idx] = newval
            self.tree.item(iid, values=vals)

    def apply_batch(self):
        field = self.batch_field.get()
        if not field:
            messagebox.showwarning("Batch Edit", "Pilih field untuk diedit.")
            return
        vtxt = self.batch_value.get().strip()
        if vtxt == "":
            messagebox.showwarning("Batch Edit", "Masukkan nilai.")
            return
        sels = self.tree.selection()
        if not sels:
            messagebox.showinfo("Batch Edit", "Tidak ada baris yang dipilih.")
            return
        for iid in sels:
            idx = int(iid)
            rec = self.model.records[idx]
            if field in ["crater_attack", "attack", "defense", "energy", "shield_regen", "item_delay", "popularity"] and rec.type == "Ex-item":
                continue
            if field == "name":
                if len(vtxt.encode("utf-8")) > 19:
                    messagebox.showerror("Invalid", "Nama maksimal 19 karakter (UTF-8).")
                    continue
                rec.data[field] = vtxt
            elif field == "show_in_shop":
                try:
                    val = int(vtxt)
                    if val not in (0, 1):
                        messagebox.showerror("Invalid", "Visible harus 0 atau 1")
                        return
                    rec.data[field] = 1 if val != 0 else 0
                except:
                    messagebox.showerror("Invalid", "Visible harus 0 atau 1")
                    return
            else:
                try:
                    val = int(vtxt)
                    rec.data[field] = val
                except:
                    messagebox.showerror("Invalid", f"{field} harus angka")
                    return
            if field in COLUMNS:
                vals = list(self.tree.item(iid, "values"))
                col_idx = COLUMNS.index(field)
                vals[col_idx] = str(rec.data.get(field, ""))
                self.tree.item(iid, values=vals)
        self.status.set(f"Batch edit: {field} = {vtxt} untuk {len(sels)} baris")

    def on_double_click_cell(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        rowid = self.tree.identify_row(event.y)
        colid = self.tree.identify_column(event.x)
        if not rowid or not colid:
            return
        col_index = int(colid.replace("#","")) - 1
        column = COLUMNS[col_index]
        if column in ("index","type"):
            return
        x,y,w,h = self.tree.bbox(rowid, colid)
        value = self.tree.set(rowid, column)
        edit = tk.Entry(self.tree)
        edit.place(x=x, y=y, width=w, height=h)
        edit.insert(0, value)
        edit.focus_set()
        def finish(event=None):
            newv = edit.get().strip()
            edit.destroy()
            idx = int(rowid)
            rec = self.model.records[idx]
            if column in ["crater_attack", "attack", "defense", "energy", "shield_regen", "item_delay", "popularity"] and rec.type == "Ex-item":
                messagebox.showerror("Invalid", f"{column} tidak tersedia untuk Ex-item")
                return
            if column == "name":
                if len(newv.encode("utf-8")) > 19:
                    messagebox.showerror("Invalid", "Nama maksimal 19 karakter (UTF-8).")
                    return
                rec.data[column] = newv
            elif column == "show_in_shop":
                try:
                    val = int(newv)
                    if val not in (0, 1):
                        messagebox.showerror("Invalid", "Visible harus 0 atau 1")
                        return
                    rec.data[column] = 1 if val != 0 else 0
                except:
                    messagebox.showerror("Invalid", "Visible harus 0 atau 1")
                    return
            elif column in ["description"]:
                if len(newv.encode("utf-8")) > 63:
                    messagebox.showerror("Invalid", "Deskripsi maksimal 63 karakter (UTF-8).")
                    return
                rec.data[column] = newv
            elif column in ["avatar_code", "image_number", "ex_number", "sell_weekly", "sell_monthly", "sell_eternal", 
                          "enable_sale_gold", "enable_sale_cash", "price_weekly_gold", "price_weekly_cash", 
                          "price_monthly_gold", "price_monthly_cash", "price_eternal_gold", "price_eternal_cash",
                          "crater_attack", "attack", "defense", "energy", "shield_regen", "item_delay", "popularity"]:
                try:
                    val = int(newv)
                    rec.data[column] = val
                except:
                    messagebox.showerror("Invalid", f"{column} harus angka")
                    return
            else:
                messagebox.showerror("Invalid", f"Kolom {column} tidak dapat diedit")
                return
            vals = list(self.tree.item(rowid, "values"))
            vals[col_index] = newv
            self.tree.item(rowid, values=vals)
        edit.bind("<Return>", finish)
        edit.bind("<FocusOut>", finish)

    def _sync_current_selection_edits(self):
        pass

if __name__ == "__main__":
    App().mainloop()