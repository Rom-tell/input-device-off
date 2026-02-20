#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
入力デバイスオフ - 掃除用デバイス無効化アプリ
"""

import ctypes
import tkinter as tk
from tkinter import messagebox
import keyboard

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("keyboard-off")

# ── カラーパレット ──────────────────────────────
BG        = "#f1f5f9"   # アプリ背景
CARD      = "#ffffff"   # カード背景
BORDER    = "#e2e8f0"   # カードボーダー
TITLE_C   = "#0f172a"   # タイトルテキスト
BODY_C    = "#64748b"   # サブテキスト
ACCENT    = "#6366f1"   # アクセント（ボタン・ラベル）
ACCENT_H  = "#4f46e5"   # ボタンホバー

ACT_BG    = "#1e293b"   # 無効化中：背景
ACT_CARD  = "#0f172a"   # 無効化中：カード背景
ACT_BORD  = "#334155"   # 無効化中：ボーダー
ACT_TEXT  = "#e2e8f0"   # 無効化中：テキスト
ACT_ACNT  = "#f59e0b"   # 無効化中：アクセント（アンバー）
ACT_BTN   = "#334155"   # 無効化中：ボタン背景
ACT_BTN_H = "#475569"   # 無効化中：ボタンホバー

RADIO_OPTIONS = [
    ("keyboard", "キーボード"),
    ("mouse",    "マウス"),
]

DEVICE_DESC = {
    "keyboard": "接続しているすべてのキーボードが無効になります",
    "mouse":    "接続しているすべてのマウスが無効になります",
}


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.device_var      = tk.StringVar(value="keyboard")
        self.recovery_hotkey = "ctrl+shift+f12"
        self.is_active       = False
        self.mouse_listener  = None
        self._capturing      = False
        self._captured_keys  = set()
        self._device_trace_id = None

        self.root.iconbitmap("icon.ico")
        self._build_main()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ──────────────────────────────────────────────
    # ユーティリティ
    # ──────────────────────────────────────────────

    def _on_close(self):
        if self.is_active:
            return
        self.root.destroy()

    def _clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def _card(self, parent, bg=CARD, border=BORDER):
        return tk.Frame(
            parent, bg=bg,
            highlightbackground=border,
            highlightthickness=1
        )

    def _hover_btn(self, parent, text, command, bg, hover, fg="white", **kw):
        btn = tk.Button(
            parent, text=text, command=command,
            bg=bg, fg=fg,
            activebackground=hover, activeforeground=fg,
            relief="flat", cursor="hand2", **kw
        )
        btn.bind("<Enter>", lambda e: btn.config(bg=hover))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        return btn

    # ──────────────────────────────────────────────
    # メイン画面
    # ──────────────────────────────────────────────

    def _build_main(self):
        if self._device_trace_id:
            try:
                self.device_var.trace_remove("write", self._device_trace_id)
            except Exception:
                pass
            self._device_trace_id = None

        self._radio_cvs = {}   # value → Canvas（インジケーター）

        self._clear()
        self.root.title("入力デバイスオフ")
        self.root.geometry("320x350")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", False)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── アクセントバー
        tk.Frame(self.root, bg=ACCENT, height=4).pack(fill="x")

        # ── ヘッダー
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(18, 8))
        tk.Label(hdr, text="入力デバイスオフ",
                 font=("Yu Gothic UI", 16, "bold"),
                 bg=BG, fg=TITLE_C).pack(anchor="w")
        tk.Label(hdr, text="無効化するデバイスを選んでね",
                 bg=BG, fg=BODY_C, font=("Yu Gothic UI", 10)).pack(anchor="w")

        # ── デバイス選択カード
        dev_card = self._card(self.root)
        dev_card.pack(padx=24, fill="x")
        dev_inner = tk.Frame(dev_card, bg=CARD)
        dev_inner.pack(fill="x", padx=16, pady=14)

        tk.Label(dev_inner, text="デバイス選択",
                 bg=CARD, fg=BODY_C,
                 font=("Yu Gothic UI", 8, "bold")).pack(anchor="w", pady=(0, 8))

        for value, label in RADIO_OPTIONS:
            self._make_radio(dev_inner, value, label)

        # ── ショートカット設定カード（マウス選択時のみ）
        self._sc_card = self._card(self.root)
        sc_inner = tk.Frame(self._sc_card, bg=CARD)
        sc_inner.pack(fill="x", padx=16, pady=14)

        tk.Label(sc_inner, text="復帰ショートカット",
                 bg=CARD, fg=BODY_C,
                 font=("Yu Gothic UI", 8, "bold")).pack(anchor="w", pady=(0, 6))

        self._shortcut_lbl = tk.Label(
            sc_inner, text=self.recovery_hotkey,
            font=("Consolas", 13, "bold"), fg=ACCENT,
            bg=BG, padx=10, pady=5,
            cursor="hand2", relief="flat"
        )
        self._shortcut_lbl.pack(anchor="w")

        tk.Label(sc_inner, text="クリックして別のキーに変更できるよ",
                 bg=CARD, fg=BODY_C,
                 font=("Yu Gothic UI", 9)).pack(anchor="w", pady=(3, 0))

        self._shortcut_lbl.bind("<Button-1>", lambda e: self._begin_capture())

        # ── 説明文（選択に応じて変わる）
        self._desc_lbl = tk.Label(
            self.root, text="",
            bg=BG, fg=BODY_C,
            font=("Yu Gothic UI", 9),
            wraplength=272, justify="left"
        )
        self._desc_lbl.pack(fill="x", padx=24, pady=(8, 0))

        # ── 無効化ボタン
        self._btn_frame = tk.Frame(self.root, bg=BG)
        self._btn_frame.pack(fill="x", padx=24, pady=(8, 16))

        self._hover_btn(
            self._btn_frame, text="無効化する",
            command=self._on_disable_click,
            bg=ACCENT, hover=ACCENT_H,
            font=("Yu Gothic UI", 12, "bold"), height=2
        ).pack(fill="x")

        # ── デバイス選択変化を監視
        self._device_trace_id = self.device_var.trace_add(
            "write", self._on_device_toggle
        )
        self._on_device_toggle()

    def _make_radio(self, parent, value, label):
        row = tk.Frame(parent, bg=CARD, cursor="hand2")
        row.pack(fill="x", pady=(0, 4))

        cv = tk.Canvas(row, width=20, height=20, bg=CARD,
                       highlightthickness=0, cursor="hand2")
        cv.pack(side="left", padx=(0, 8), pady=2)
        self._radio_cvs[value] = cv
        self._draw_radio(cv, False)

        lbl = tk.Label(row, text=label, bg=CARD, fg=TITLE_C,
                       font=("Yu Gothic UI", 11, "bold"), cursor="hand2")
        lbl.pack(side="left")

        for w in [row, cv, lbl]:
            w.bind("<Button-1>", lambda e, v=value: self.device_var.set(v))

    def _draw_radio(self, canvas, selected):
        canvas.delete("all")
        if selected:
            canvas.create_oval(2, 2, 18, 18, outline=ACCENT, fill=ACCENT, width=2)
            canvas.create_oval(7, 7, 13, 13, outline="white", fill="white", width=0)
        else:
            canvas.create_oval(2, 2, 18, 18, outline="#94a3b8", fill=CARD, width=2)

    def _on_device_toggle(self, *_):
        selected = self.device_var.get()

        # ラジオインジケーターを更新
        for val, cv in self._radio_cvs.items():
            self._draw_radio(cv, val == selected)

        # 説明文を更新
        self._desc_lbl.config(text=DEVICE_DESC.get(selected, ""))

        # ショートカットカードの表示切り替え
        if selected == "mouse":
            self._desc_lbl.pack_forget()
            self._btn_frame.pack_forget()
            self._sc_card.pack(padx=24, pady=(8, 0), fill="x")
            self._desc_lbl.pack(fill="x", padx=24, pady=(8, 0))
            self._btn_frame.pack(fill="x", padx=24, pady=(8, 16))
            self.root.geometry("320x420")
        else:
            self._capturing = False
            self._sc_card.pack_forget()
            self.root.geometry("320x310")

    # ──────────────────────────────────────────────
    # 無効化ボタン押下
    # ──────────────────────────────────────────────

    def _on_disable_click(self):
        if not self.device_var.get():
            messagebox.showwarning(
                "選択してね", "無効化するデバイスを選んでね", parent=self.root
            )
            return
        self._start()

    # ──────────────────────────────────────────────
    # ショートカットキー入力キャプチャ
    # ──────────────────────────────────────────────

    def _begin_capture(self):
        self._capturing     = True
        self._captured_keys = set()
        self._shortcut_lbl.config(text="キーを押してね...", fg=ACT_ACNT)
        self.root.bind("<KeyPress>",   self._on_key_down)
        self.root.bind("<KeyRelease>", self._on_key_up)
        self.root.focus_set()

    _MOD_MAP = {
        "control_l": "ctrl",  "control_r": "ctrl",
        "shift_l":   "shift", "shift_r":   "shift",
        "alt_l":     "alt",   "alt_r":     "alt",
    }
    _MODS = {"ctrl", "shift", "alt"}

    def _on_key_down(self, e):
        if not self._capturing:
            return "break"
        key = self._MOD_MAP.get(e.keysym.lower(), e.keysym.lower())
        self._captured_keys.add(key)
        self._shortcut_lbl.config(text=self._fmt_combo(), fg=ACT_ACNT)
        return "break"

    def _on_key_up(self, e):
        if not self._capturing:
            return "break"
        released = self._MOD_MAP.get(e.keysym.lower(), e.keysym.lower())
        if released not in self._MODS:
            self._capturing = False
            combo = self._fmt_combo()
            if combo:
                self.recovery_hotkey = combo
                self._shortcut_lbl.config(text=combo, fg=ACCENT)
            self.root.unbind("<KeyPress>")
            self.root.unbind("<KeyRelease>")
        return "break"

    def _fmt_combo(self):
        parts  = [m for m in ["ctrl", "shift", "alt"] if m in self._captured_keys]
        parts += [k for k in self._captured_keys if k not in self._MODS]
        return "+".join(parts)

    # ──────────────────────────────────────────────
    # 無効化開始
    # ──────────────────────────────────────────────

    def _start(self):
        self.is_active = True
        self._build_active()

        device = self.device_var.get()

        if device == "mouse":
            try:
                keyboard.add_hotkey(self.recovery_hotkey, self._restore_safe)
            except Exception:
                pass
            self._block_mouse()
        else:
            try:
                keyboard.hook(lambda e: None, suppress=True)
            except Exception:
                pass

    def _block_mouse(self):
        try:
            from pynput import mouse as _m
            self.mouse_listener = _m.Listener(suppress=True)
            self.mouse_listener.start()
        except Exception as ex:
            messagebox.showerror(
                "エラー", f"マウスのブロックに失敗したよ:\n{ex}",
                parent=self.root
            )

    # ──────────────────────────────────────────────
    # 無効化中の画面
    # ──────────────────────────────────────────────

    def _build_active(self):
        self._clear()
        self.root.configure(bg=ACT_BG)
        self.root.attributes("-topmost", True)
        self.root.geometry("320x300")

        device = self.device_var.get()
        is_mouse = (device == "mouse")
        device_label = "マウス" if is_mouse else "キーボード"

        # ── アクセントバー
        tk.Frame(self.root, bg=ACT_ACNT, height=4).pack(fill="x")

        # ── ヘッダー
        hdr = tk.Frame(self.root, bg=ACT_BG)
        hdr.pack(fill="x", padx=24, pady=(18, 8))
        tk.Label(hdr, text="入力デバイスオフ",
                 font=("Yu Gothic UI", 16, "bold"),
                 bg=ACT_BG, fg=ACT_TEXT).pack(anchor="w")
        tk.Label(hdr, text="無効化中",
                 bg=ACT_BG, fg=ACT_ACNT,
                 font=("Yu Gothic UI", 10, "bold")).pack(anchor="w")

        # ── ブロック中デバイス表示カード
        sc = self._card(self.root, bg=ACT_CARD, border=ACT_BORD)
        sc.pack(padx=24, fill="x")
        tk.Label(
            sc, text=f"{device_label}  をブロック中",
            bg=ACT_CARD, fg=ACT_TEXT,
            font=("Yu Gothic UI", 11), pady=14
        ).pack()

        if is_mouse:
            # ショートカット表示カード
            kc = self._card(self.root, bg=ACT_CARD, border=ACT_BORD)
            kc.pack(padx=24, pady=(8, 0), fill="x")
            kc_inner = tk.Frame(kc, bg=ACT_CARD)
            kc_inner.pack(fill="x", padx=16, pady=12)

            tk.Label(kc_inner, text="復帰するにはこのキーを押してね",
                     bg=ACT_CARD, fg=BODY_C,
                     font=("Yu Gothic UI", 9)).pack(anchor="w")
            tk.Label(kc_inner, text=self.recovery_hotkey,
                     bg=ACT_BG, fg=ACT_ACNT,
                     font=("Consolas", 14, "bold"),
                     padx=10, pady=6).pack(anchor="w", pady=(4, 0))
        else:
            self._hover_btn(
                self.root, text="解除する",
                command=self._restore,
                bg=ACT_BTN, hover=ACT_BTN_H,
                font=("Yu Gothic UI", 12, "bold"), height=2
            ).pack(fill="x", padx=24, pady=16)

    # ──────────────────────────────────────────────
    # 復帰処理
    # ──────────────────────────────────────────────

    def _restore_safe(self):
        self.root.after(0, self._restore)

    def _restore(self):
        if not self.is_active:
            return
        self.is_active = False

        keyboard.unhook_all()

        if self.mouse_listener:
            try:
                self.mouse_listener.stop()
            except Exception:
                pass
            self.mouse_listener = None

        self.root.configure(bg=BG)
        self.root.attributes("-topmost", False)
        self._build_main()

    # ──────────────────────────────────────────────
    # 起動
    # ──────────────────────────────────────────────

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = App()
    app.run()
