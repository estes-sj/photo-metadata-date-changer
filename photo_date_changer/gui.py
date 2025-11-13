"""Tkinter GUI application."""
import os
import sys
import threading
import queue
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import webbrowser

from .tooltips import ToolTip
from .runner import OperationRunner

DEFAULT_FOLDER = os.path.abspath(r"./")
DEFAULT_DATETIME_STR = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
DEFAULT_INCREMENT_SECONDS = 1
DEFAULT_SORT_BY = "name"
DEFAULT_MODE = "increment"
DEFAULT_DRY_RUN = True
APP_VERSION = "v0.1.0"
GITHUB_URL = "https://github.com/estes-sj/photo-metadata-date-changer"

class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Metadata Date Changer")
        self.log_queue = queue.Queue()
        self.worker_thread = None
        self.cancel_event = threading.Event()  # event used to request cancellation
        self._syncing = False  # guard for two-way sync
        self._build_ui()
        self.root.after(200, self._process_log_queue)

    def _build_ui(self):
        frm = ttk.Frame(self.root, padding=12)
        frm.grid(sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # --- Folder selection ---
        folder_row = ttk.Frame(frm)
        folder_row.grid(sticky="ew", pady=(0, 8))
        folder_row.columnconfigure(1, weight=1)
        ttk.Label(folder_row, text="Folder:").grid(row=0, column=0, sticky="w")
        self.folder_var = tk.StringVar(value=DEFAULT_FOLDER)
        self.folder_entry = ttk.Entry(folder_row, textvariable=self.folder_var)
        self.folder_entry.grid(row=0, column=1, sticky="ew", padx=(6, 6))
        self.folder_btn = ttk.Button(folder_row, text="Browse...", command=self._choose_folder)
        self.folder_btn.grid(row=0, column=2)
        ToolTip(self.folder_entry, "Select the folder containing photos to process (relative or absolute path).")
        ToolTip(self.folder_btn, "Open a folder chooser to select the photos folder.")

        # --- Datetime picker + manual entry (synced) ---
        picker_frame = ttk.Frame(frm)
        picker_frame.grid(sticky="ew", pady=(0, 8))
        picker_frame.columnconfigure(1, weight=1)

        # Picker controls (year, month, day, hour, minute, second)
        now = datetime.now()
        current_year = now.year
        year_range = list(range(current_year - 40, current_year + 41))
        self.year_var = tk.IntVar(value=current_year)
        self.month_var = tk.IntVar(value=now.month)
        self.day_var = tk.IntVar(value=now.day)
        self.hour_var = tk.IntVar(value=now.hour)
        self.minute_var = tk.IntVar(value=now.minute)
        self.second_var = tk.IntVar(value=now.second)

        ttk.Label(picker_frame, text="Datetime picker:").grid(row=0, column=0, sticky="w")
        picker_controls = ttk.Frame(picker_frame)
        picker_controls.grid(row=0, column=1, sticky="w")

        self.year_cb = ttk.Combobox(picker_controls, values=[str(y) for y in year_range], width=6, textvariable=self.year_var, state="readonly")
        self.year_cb.grid(row=0, column=0, padx=(0, 4))
        self.month_cb = ttk.Combobox(picker_controls, values=[f"{m:02d}" for m in range(1, 13)], width=3, textvariable=self.month_var, state="readonly")
        self.month_cb.grid(row=0, column=1, padx=(0, 4))
        self.day_cb = ttk.Combobox(picker_controls, values=[f"{d:02d}" for d in range(1, 32)], width=3, textvariable=self.day_var, state="readonly")
        self.day_cb.grid(row=0, column=2, padx=(0, 4))
        self.hour_cb = ttk.Combobox(picker_controls, values=[f"{h:02d}" for h in range(0, 24)], width=3, textvariable=self.hour_var, state="readonly")
        self.hour_cb.grid(row=0, column=3, padx=(8, 4))
        self.minute_cb = ttk.Combobox(picker_controls, values=[f"{m:02d}" for m in range(0, 60)], width=3, textvariable=self.minute_var, state="readonly")
        self.minute_cb.grid(row=0, column=4, padx=(0, 4))
        self.second_cb = ttk.Combobox(picker_controls, values=[f"{s:02d}" for s in range(0, 60)], width=3, textvariable=self.second_var, state="readonly")
        self.second_cb.grid(row=0, column=5, padx=(0, 4))

        # Buttons: now only (picker and manual always synced)
        self.now_picker_btn = ttk.Button(picker_frame, text="Now", command=self._set_now_picker)
        self.now_picker_btn.grid(row=0, column=2, padx=(8, 4))
        ToolTip(self.year_cb, "Year (picker).")
        ToolTip(self.month_cb, "Month (picker).")
        ToolTip(self.day_cb, "Day (picker).")
        ToolTip(self.hour_cb, "Hour (picker, 24-hour).")
        ToolTip(self.minute_cb, "Minute (picker).")
        ToolTip(self.second_cb, "Second (picker).")
        ToolTip(self.now_picker_btn, "Set picker and manual entry to the current date/time.")

        # Manual entry (kept for advanced users)
        row2 = ttk.Frame(frm)
        row2.grid(sticky="ew", pady=(0, 8))
        ttk.Label(row2, text="Base datetime (manual):").grid(row=0, column=0, sticky="w")
        self.datetime_var = tk.StringVar(value=DEFAULT_DATETIME_STR)
        self.datetime_entry = ttk.Entry(row2, textvariable=self.datetime_var, width=28)
        self.datetime_entry.grid(row=0, column=1, sticky="w", padx=(6, 12))
        ttk.Label(row2, text="Increment (s):").grid(row=0, column=2, sticky="w")
        self.increment_var = tk.IntVar(value=DEFAULT_INCREMENT_SECONDS)
        self.increment_entry = ttk.Entry(row2, textvariable=self.increment_var, width=6)
        self.increment_entry.grid(row=0, column=3, sticky="w", padx=(6, 6))
        ToolTip(self.datetime_entry, "Base date/time to apply (format: YYYY:MM:DD HH:MM:SS). In increment mode, first file uses this time.")
        ToolTip(self.increment_entry, "Seconds to add between files in increment mode (e.g., 1).")
        
        # set up traces for two-way sync
        for var in (self.year_var, self.month_var, self.day_var, self.hour_var, self.minute_var, self.second_var):
            var.trace_add("write", self._on_picker_change)
        self.datetime_var.trace_add("write", self._on_manual_change)

        # --- Mode selection ---
        mode_row = ttk.LabelFrame(frm, text="Mode")
        mode_row.grid(sticky="ew", pady=(0, 8))
        self.mode_var = tk.StringVar(value=DEFAULT_MODE)
        self.mode_inc_rb = ttk.Radiobutton(mode_row, text="Increment (per-file)", value="increment", variable=self.mode_var)
        self.mode_inc_rb.grid(row=0, column=0, sticky="w", padx=6, pady=3)
        self.mode_align_rb = ttk.Radiobutton(mode_row, text="Align earliest", value="align-earliest", variable=self.mode_var)
        self.mode_align_rb.grid(row=0, column=1, sticky="w", padx=6, pady=3)
        ToolTip(self.mode_inc_rb, "Assign timestamps sequentially using base datetime + incremental offset per file.")
        ToolTip(self.mode_align_rb, "Shift all files so the earliest original file equals the base datetime; preserves gaps.")
        self.mode_var.trace_add("write", self._on_mode_change)

        # --- Options ---
        opts_row = ttk.Frame(frm)
        opts_row.grid(sticky="ew", pady=(0, 8))
        self.no_increment_var = tk.BooleanVar(value=False)
        self.no_increment_cb = ttk.Checkbutton(opts_row, text="No increment (same time for all)", variable=self.no_increment_var)
        self.no_increment_cb.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.recursive_var = tk.BooleanVar(value=False)
        self.recursive_cb = ttk.Checkbutton(opts_row, text="Recursive (include subfolders)", variable=self.recursive_var)
        self.recursive_cb.grid(row=0, column=1, sticky="w", padx=(0, 8))
        ttk.Label(opts_row, text="Sort by:").grid(row=0, column=2, sticky="w", padx=(8, 4))
        self.sort_by_var = tk.StringVar(value=DEFAULT_SORT_BY)
        self.sort_by_cb = ttk.Combobox(opts_row, values=["name", "mtime"], textvariable=self.sort_by_var, width=8, state="readonly")
        self.sort_by_cb.grid(row=0, column=3, sticky="w")
        ToolTip(self.no_increment_cb, "If checked, every file will get exactly the same timestamp.")
        ToolTip(self.recursive_cb, "Include files in subdirectories as well.")
        ToolTip(self.sort_by_cb, "When in increment mode, sort files by name or original modification time before assigning timestamps.")

        # --- Dry-run and skip confirmation ---
        bottom_opts = ttk.Frame(frm)
        bottom_opts.grid(sticky="ew", pady=(0, 8))
        self.dry_run_var = tk.BooleanVar(value=DEFAULT_DRY_RUN)
        self.dry_run_cb = ttk.Checkbutton(bottom_opts, text="Dry-run (no writes)", variable=self.dry_run_var)
        self.dry_run_cb.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.yes_var = tk.BooleanVar(value=False)
        self.yes_cb = ttk.Checkbutton(bottom_opts, text="Skip confirmation", variable=self.yes_var)
        self.yes_cb.grid(row=0, column=1, sticky="w", padx=(0, 8))
        ToolTip(self.dry_run_cb, "Preview the exact changes that would be made without writing anything.")
        ToolTip(self.yes_cb, "If checked, the tool will not prompt for confirmation before making changes.")

        # --- Buttons ---
        btn_row = ttk.Frame(frm)
        btn_row.grid(sticky="ew", pady=(0, 8))
        self.start_btn = ttk.Button(btn_row, text="Start", command=self._on_start)
        self.start_btn.grid(row=0, column=0, padx=(0, 6))
        self.clear_btn = ttk.Button(btn_row, text="Clear log", command=self._clear_log)
        self.clear_btn.grid(row=0, column=1)
        self.open_btn = ttk.Button(btn_row, text="Open folder in Explorer", command=self._open_folder)
        self.open_btn.grid(row=0, column=2, padx=(6, 0))
        # Cancel button for cooperative cancellation
        self.cancel_btn = ttk.Button(btn_row, text="Cancel", command=self._on_cancel, state="disabled")
        self.cancel_btn.grid(row=0, column=3, padx=(6, 0))
        ToolTip(self.start_btn, "Begin processing using the current settings.")
        ToolTip(self.clear_btn, "Clear the log/preview area.")
        ToolTip(self.open_btn, "Open the selected folder in your system file explorer.")
        ToolTip(self.cancel_btn, "Cancel the currently running operation.")

        # --- Progress bar ---
        ttk.Label(frm, text="Progress:").grid(sticky="w", pady=(6,0))
        self.progress_bar = ttk.Progressbar(frm, orient="horizontal", length=600, mode="determinate")
        self.progress_bar.grid(sticky="ew")
        ToolTip(self.progress_bar, "Shows how many files have been processed so far.")

        # --- Log / preview ---
        ttk.Label(frm, text="Log / Preview:").grid(sticky="w")
        self.log_widget = scrolledtext.ScrolledText(frm, width=90, height=18, wrap="none")
        self.log_widget.grid(sticky="nsew", pady=(6, 0))
        self.log_widget.configure(state="disabled")
        ToolTip(self.log_widget, "Detailed run log and dry-run preview (use Clear log to reset).")
        frm.rowconfigure(6, weight=1)

        # --- Bottom bar: version + GitHub button ---
        bottom_bar = ttk.Frame(frm)
        bottom_bar.grid(sticky="ew", pady=(6, 0))
        bottom_bar.columnconfigure(0, weight=1)

        self.version_label = ttk.Label(bottom_bar, text=f"Version: {APP_VERSION}", anchor="w")
        self.version_label.grid(row=0, column=0, sticky="w")

        self.github_btn = ttk.Button(bottom_bar, text="View on GitHub", command=self._open_github)
        self.github_btn.grid(row=0, column=1, sticky="e")
        ToolTip(self.github_btn, "Open the project GitHub repository.")

    # ---------- Sync handlers ----------
    def _on_picker_change(self, *args):
        if self._syncing:
            return
        try:
            self._syncing = True
            y = int(self.year_var.get())
            m = int(self.month_var.get())
            d = int(self.day_var.get())
            H = int(self.hour_var.get())
            M = int(self.minute_var.get())
            S = int(self.second_var.get())
            dt = datetime(y, m, d, H, M, S)
            self.datetime_var.set(dt.strftime("%Y:%m:%d %H:%M:%S"))
        except Exception:
            pass
        finally:
            self._syncing = False

    def _on_manual_change(self, *args):
        if self._syncing:
            return
        s = self.datetime_var.get().strip()
        try:
            dt = datetime.strptime(s, "%Y:%m:%d %H:%M:%S")
            self._syncing = True
            self.year_var.set(dt.year)
            self.month_var.set(dt.month)
            self.day_var.set(dt.day)
            self.hour_var.set(dt.hour)
            self.minute_var.set(dt.minute)
            self.second_var.set(dt.second)
        except Exception:
            pass
        finally:
            self._syncing = False

    def _on_mode_change(self, *args):
        mode = self.mode_var.get()
        if mode == "align-earliest":
            self.increment_entry.configure(state="disabled")
        else:
            self.increment_entry.configure(state="normal")

    def _set_now_picker(self):
        now = datetime.now()
        self._syncing = True
        try:
            self.year_var.set(now.year)
            self.month_var.set(now.month)
            self.day_var.set(now.day)
            self.hour_var.set(now.hour)
            self.minute_var.set(now.minute)
            self.second_var.set(now.second)
            self.datetime_var.set(now.strftime("%Y:%m:%d %H:%M:%S"))
        finally:
            self._syncing = False

    def _choose_folder(self):
        selected = filedialog.askdirectory(initialdir=self.folder_var.get() or os.getcwd())
        if selected:
            self.folder_var.set(selected)

    def _open_folder(self):
        folder = self.folder_var.get()
        if not os.path.isdir(folder):
            messagebox.showerror("Error", "Folder does not exist")
            return
        if os.name == "nt":
            os.startfile(folder)
        else:
            os.system(f"open '{folder}'" if sys.platform == "darwin" else f"xdg-open '{folder}'")

    def _log_put(self, msg):
        self.log_queue.put(msg)

    def _process_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_widget.configure(state="normal")
                self.log_widget.insert("end", msg + "\n")
                self.log_widget.see("end")
                self.log_widget.configure(state="disabled")
        except queue.Empty:
            pass
        self.root.after(200, self._process_log_queue)

    def _clear_log(self):
        self.log_widget.configure(state="normal")
        self.log_widget.delete("1.0", "end")
        self.log_widget.configure(state="disabled")

    def _on_start(self):
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showinfo("Running", "Operation already in progress")
            return
        folder = self.folder_var.get().strip() or DEFAULT_FOLDER
        try:
            replacement_datetime = datetime.strptime(self.datetime_var.get().strip(), "%Y:%m:%d %H:%M:%S")
        except Exception:
            messagebox.showerror("Invalid datetime", "Datetime must be in format YYYY:MM:DD HH:MM:SS")
            return
        increment_seconds = int(self.increment_var.get())
        no_increment = bool(self.no_increment_var.get())
        recursive = bool(self.recursive_var.get())
        sort_by = self.sort_by_var.get()
        mode = self.mode_var.get()
        dry_run = bool(self.dry_run_var.get())
        yes = bool(self.yes_var.get())

        self.start_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")  # enable cancel button
        self.progress_bar['value'] = 0
        self.cancel_event.clear()  # ensure event is cleared before starting

        self._on_mode_change()

        self.worker_thread = threading.Thread(
            target=self._worker_wrapper,
            args=(folder, replacement_datetime, increment_seconds, no_increment, recursive, sort_by, mode, dry_run, yes),
            daemon=True
        )
        self.worker_thread.start()

    def _on_cancel(self):
        # confirmation optional; keeps accidental clicks from stopping a run instantly
        if messagebox.askyesno("Cancel", "Are you sure you want to cancel the running operation?"):
            self.cancel_event.set()
            self.cancel_btn.config(state="disabled")
            self._log_put("🛑 Cancellation requested. Stopping after current file...")

    def _worker_wrapper(self, folder, replacement_datetime, increment_seconds, no_increment, recursive, sort_by, mode, dry_run, yes):
        def gui_log(msg):
            self._log_put(msg)

        def gui_confirm(msg):
            return messagebox.askyesno("Confirm", msg)

        def progress_fn(current, total):
            try:
                self.progress_bar['maximum'] = total
                self.progress_bar['value'] = current
            except Exception:
                pass

        try:
            runner = OperationRunner()
            runner.run(
                folder=folder,
                replacement_datetime=replacement_datetime,
                increment_seconds=increment_seconds,
                no_increment=no_increment,
                recursive=recursive,
                sort_by=sort_by,
                mode=mode,
                dry_run=dry_run,
                yes=yes,
                log_fn=gui_log,
                confirm_fn=gui_confirm,
                progress_fn=progress_fn,
                cancel_event=self.cancel_event,  # pass event for cooperative cancellation
            )
        finally:
            # re-enable start and ensure cancel is disabled when operation finishes
            self.start_btn.config(state="normal")
            self.cancel_btn.config(state="disabled")

    def _open_github(self):
        webbrowser.open(GITHUB_URL)