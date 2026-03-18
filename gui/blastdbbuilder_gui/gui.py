#!/usr/bin/env python3
"""
blastdbbuilder GUI using Tkinter (no external GUI dependencies)

Features:
- Choose working directory
- Select genome groups for download
- Choose action: Download / Concat / Build / Run all
- Run in BACKGROUND mode (job continues if GUI closes)
- Create PID/log/state files in working directory
- Reopen GUI later -> Detect running job -> show summary/progress
- Stop / Force Kill from GUI

Files created in working directory:
  .blastdbbuilder.pid
  .blastdbbuilder_gui.log
  .blastdbbuilder_gui.state.json

Note:
- This GUI displays ONLY progress/summary lines (from summary.log) to keep the panel clean.
- summary.log is appended across runs in the same working directory (handled by blastdbbuilder downloader).
"""

import os
import json
import time
import signal
import shutil
import re
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from importlib.resources import files

BASE_DIR = Path(__file__).resolve().parent

APP_TITLE = "blastdbbuilder (GUI)"

GROUP_FLAGS = {
    "Archaea": "--archaea",
    "Bacteria": "--bacteria",
    "Fungi": "--fungi",
    "Virus": "--virus",
    "Plants": "--plants",
}

ACTIONS = [
    ("Download only (Step 1)", "download"),
    ("Concat only (Step 2)", "concat"),
    ("Build only (Step 3)", "build"),
    ("Run all (1 → 2 → 3)", "all"),
]

PID_FILE = ".blastdbbuilder.pid"
LOG_FILE = ".blastdbbuilder_gui.log"
STATE_FILE = ".blastdbbuilder_gui.state.json"

# Progress/summary file produced by the downloader (append-only in the working directory)
SUMMARY_FILE = "summary.log"

# NCBI metadata summary file produced/used by blastdbbuilder
METADATA_FILE = "summary.txt"


def is_pgid_running(pgid: int) -> bool:
    """Return True if there is at least one *non-zombie* process in the given process group
    that belongs to the current user.

    Why:
    - Download/Concat/Build/All can spawn child processes; watching only the launcher PID is unreliable.
    - On some systems the launcher can become a zombie until reaped; zombies must NOT count as "running".
    - On shared systems, PID reuse / permission issues must not block UI re-enable.

    Implementation:
    - Prefer `ps` scoped to (PGID, UID) and require at least one member with a non-zombie STAT.
    - Fallback to os.killpg probes if ps is unavailable.
    """
    try:
        pgid = int(pgid)
    except Exception:
        return False

    uid = str(os.getuid())

    # Preferred: list processes in this process-group owned by us, with their STAT.
    try:
        out = subprocess.check_output(
            ["ps", "-o", "pid=,stat=", "-g", str(pgid), "-u", uid],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if not out:
            return False

        # Any non-zombie process => running. (STAT starts with 'Z' for zombies)
        for ln in out.splitlines():
            parts = ln.strip().split(None, 1)
            if len(parts) != 2:
                continue
            _pid_s, stat = parts
            if stat and not stat.startswith("Z"):
                return True
        return False
    except Exception:
        # Fallback: coarse OS probe (can be tripped by PermissionError on shared systems).
        try:
            os.killpg(os.getpgid(pgid), 0)
            return True
        except (ProcessLookupError, PermissionError, OSError):
            return False

def read_pidfile(pid_path: str):
    """Read PID file supporting legacy (single integer), JSON, and key=value formats.
    Returns (pid, status).
    """
    try:
        if not os.path.exists(pid_path):
            return None, None
        raw = open(pid_path, "r", encoding="utf-8", errors="replace").read().strip()
        if not raw:
            return None, None

        # JSON format (optional)
        if raw.startswith("{") and raw.endswith("}"):
            try:
                obj = json.loads(raw)
                pid = obj.get("PID") or obj.get("pid")
                status = obj.get("STATUS") or obj.get("status")
                return (int(pid) if pid is not None else None), (str(status) if status is not None else None)
            except Exception:
                pass

        # key=value lines format
        if "=" in raw and "\n" in raw:
            pid = None
            status = None
            for line in raw.splitlines():
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip().upper()
                v = v.strip()
                if k == "PID":
                    try:
                        pid = int(v)
                    except Exception:
                        pid = None
                elif k == "STATUS":
                    status = v
            return pid, status

        # Legacy: first line is integer PID
        try:
            return int(raw.splitlines()[0].strip()), None
        except Exception:
            return None, None
    except Exception:
        return None, None


def write_pidfile(pid_path: str, pid: int, status=None):
    """Write PID file. If status is provided, write key=value lines."""
    try:
        if status is None:
            with open(pid_path, "w", encoding="utf-8") as f:
                f.write(str(int(pid)) + "\n")
        else:
            with open(pid_path, "w", encoding="utf-8") as f:
                f.write(f"PID={int(pid)}\nSTATUS={status}\n")
    except Exception:
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)

        icon_path = files("blastdbbuilder_gui").joinpath("icons/blastdbbuilder.png")

        try:
            self.iconphoto(True, tk.PhotoImage(file=str(icon_path)))
        except Exception as e:
            print(f"Icon not loaded: {icon_path} ({e})")

        self.geometry("1000x720")

        self.log_q = queue.Queue()

        # Follow state for summary.log
        self._tail_fp = None
        self._tail_pos = 0
        self._tail_path = None

        # Progress UI state
        self._waiting_for_progress = False
        self._ignore_next_finish_progress = False

        self._last_attached_pid = None


        # Job watcher: re-enable Run when a job ends (no restart required)
        self._watch_after_id = None
        self._watched_pid = None

        self._build_ui()
        self._poll_log_queue()

        if shutil.which("blastdbbuilder") is None:
            self._log("WARNING: 'blastdbbuilder' not found on PATH. Activate the environment where it is installed.\n")

        self.after(200, self._auto_detect_job)

    def _set_try_failed_enabled(self, enabled: bool) -> None:
        """Enable/disable the 'Try again (failed)' button to prevent accidental presses."""
        if not hasattr(self, "try_failed_btn"):
            return
        try:
            if enabled:
                self.try_failed_btn.state(["!disabled"])
            else:
                self.try_failed_btn.state(["disabled"])
        except Exception:
            # If the widget has been destroyed or state() not available, ignore.
            pass

    def _build_ui(self):
        pad = {"padx": 8, "pady": 6}

        top = ttk.Frame(self)
        top.pack(fill="x", **pad)

        ttk.Label(top, text="Working directory:").pack(side="left")
        self.cwd_var = tk.StringVar(value=os.getcwd())
        self.cwd_entry = ttk.Entry(top, textvariable=self.cwd_var)
        self.cwd_entry.pack(side="left", padx=8, fill="x", expand=True)
        ttk.Button(top, text="Browse...", command=self._choose_dir).pack(side="left")
        ttk.Button(top, text="Detect running job", command=self._detect_job_clicked).pack(side="left", padx=6)

        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, **pad)

        left = ttk.Frame(main)
        left.pack(side="left", fill="y", padx=(0, 10))

        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True)

        grp_box = ttk.LabelFrame(left, text="Genome groups (Download step)")
        grp_box.pack(fill="x", **pad)

        self.group_vars = {}
        self.group_checkbuttons = []
        for name in GROUP_FLAGS.keys():
            v = tk.BooleanVar(value=False)  # do not pre-select anything
            self.group_vars[name] = v
            cb = ttk.Checkbutton(grp_box, text=name, variable=v, command=self._refresh_preview)
            cb.pack(anchor="w")
            self.group_checkbuttons.append(cb)

        act_box = ttk.LabelFrame(left, text="Action")
        act_box.pack(fill="x", **pad)

        self.action_var = tk.StringVar(value="")
        for label, key in ACTIONS:
            ttk.Radiobutton(act_box, text=label, value=key, variable=self.action_var, command=self._refresh_preview).pack(anchor="w")

        mode_box = ttk.LabelFrame(left, text="Execution mode")
        mode_box.pack(fill="x", **pad)
        self.background_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(mode_box, text="Run in background (safe to close GUI)", variable=self.background_var).pack(anchor="w")
        ttk.Label(mode_box, text="(Recommended for long downloads)", foreground="gray").pack(anchor="w")
        prev_box = ttk.LabelFrame(left, text="Command preview")
        prev_box.pack(fill="x", **pad)

        self.preview_var = tk.StringVar(value="")
        self.preview_entry = ttk.Entry(prev_box, textvariable=self.preview_var, width=45, state="readonly")
        self.preview_entry.pack(fill="x", padx=6, pady=6)
        ttk.Button(prev_box, text="Refresh", command=self._refresh_all).pack(pady=(0, 6))

        btns = ttk.Frame(left)
        btns.pack(fill="x", **pad)

        self.run_btn = ttk.Button(btns, text="Run", command=self._run, width=12)
        self.run_btn.pack(side="left", padx=(0, 6))

        ttk.Button(btns, text="Stop", command=self._stop, width=10).pack(side="left")
        ttk.Button(btns, text="Force Kill", command=self._kill, width=10).pack(side="left", padx=6)

        ttk.Button(btns, text="Clear view", command=self._clear_log).pack(side="left", padx=6)
        ttk.Button(btns, text="Exit", command=self.destroy).pack(side="left")

        log_box = ttk.LabelFrame(right, text=f"Progress (showing {SUMMARY_FILE})")
        log_box.pack(fill="both", expand=True, **pad)

        self.log_text = tk.Text(log_box, wrap="none")
        yscroll = ttk.Scrollbar(log_box, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=yscroll.set)

        # Allow copying from the Progress panel even while it is being updated
        def _copy_sel(event=None):
            try:
                sel = self.log_text.get("sel.first", "sel.last")
                if sel:
                    self.clipboard_clear()
                    self.clipboard_append(sel)
            except Exception:
                pass
            return "break"

        # Ctrl/Cmd+C copy
        self.log_text.bind("<Control-c>", _copy_sel)
        self.log_text.bind("<Control-C>", _copy_sel)
        self.log_text.bind("<Control-Insert>", _copy_sel)

        # Simple right-click context menu (Copy)
        menu = tk.Menu(self.log_text, tearoff=0)
        menu.add_command(label="Copy", command=lambda: _copy_sel())
        def _popup(e):
            try:
                menu.tk_popup(e.x_root, e.y_root)
            finally:
                try:
                    menu.grab_release()
                except Exception:
                    pass
        self.log_text.bind("<Button-3>", _popup)

        # Extra tools: show failed / skipped accessions (read from summary.log)
        tools = ttk.Frame(log_box)

        ttk.Button(tools, text="Show failed genomes", command=self._show_failed_genomes).pack(side="left", padx=(0, 6))
        self.try_failed_btn = ttk.Button(tools, text="Try again (failed)", command=self._try_again_failed)
        self.try_failed_btn.pack(side="left", padx=(0, 18))

        ttk.Button(tools, text="Show skipped genomes", command=self._show_skipped_genomes).pack(side="left", padx=(0, 6))
        # "Try again (skipped)" removed: skipped usually means already present/processed.

        tools.pack(side="bottom", anchor="w", fill="x", padx=6, pady=(0, 6))

        self.log_text.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=(6, 2))
        yscroll.pack(side="right", fill="y", padx=(0, 6), pady=(6, 2))

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var).pack(anchor="w", padx=10, pady=(0, 8))

        self._refresh_preview()

    def _choose_dir(self):
        current = self.cwd_var.get().strip() or os.getcwd()
        d = filedialog.askdirectory(initialdir=current)
        if not d:
            return
        d = os.path.abspath(os.path.expanduser(d))
        self.cwd_var.set(d)
        try:
            os.chdir(d)
        except Exception as e:
            messagebox.showwarning("Directory warning", f"Selected folder set in GUI, but could not change directory:\n{e}")
        self._refresh_preview()
        self._auto_detect_job()
        try:
            self._cleanup_metadata_layout(d)
        except Exception:
            pass

    def _selected_groups(self):
        return [name for name, v in self.group_vars.items() if v.get()]

    def _cmds_for_action(self):
        groups = self._selected_groups()
        action = self.action_var.get()
        if action not in ("download", "concat", "build", "all"):
            return []

        def download_cmd():
            cmd = ["blastdbbuilder", "--download"]
            for g in groups:
                cmd.append(GROUP_FLAGS[g])
            return cmd

        concat_cmd = ["blastdbbuilder", "--concat"]
        build_cmd = ["blastdbbuilder", "--build"]

        if action == "download":
            return [("download", download_cmd())]
        if action == "concat":
            return [("concat", concat_cmd)]
        if action == "build":
            return [("build", build_cmd)]
        return [("download", download_cmd()), ("concat", concat_cmd), ("build", build_cmd)]

    def _update_group_controls_state(self):
        enable = self.action_var.get() not in ("concat", "build")
        for cb in getattr(self, "group_checkbuttons", []):
            if enable:
                cb.state(["!disabled"])
            else:
                cb.state(["disabled"])

    def _refresh_preview(self):
        self._update_group_controls_state()

        action = self.action_var.get()
        if action not in ("download", "concat", "build", "all"):
            self.preview_var.set("Select an action.")
            return
        if action in ("download", "all") and not self._selected_groups():
            self.preview_var.set("Select at least one genome group for Download.")
            return
        cmds = self._cmds_for_action()
        if not cmds:
            self.preview_var.set("Select an action.")
            return
        self.preview_var.set(" && ".join(" ".join(cmd) for _, cmd in cmds))


    def _refresh_all(self):
        """Refresh command preview AND restore the log view to whatever Detect running job would display."""
        self._refresh_preview()
        # Always sync the log panel with the job-detection view (running -> tail follow, stopped -> static summary)
        self._detect_and_attach(silent=True)

    def _is_job_running_in_cwd(self) -> bool:
        _cwd, pid_path, _log_path, _state_path, _summary_path = self._paths()
        if not os.path.exists(pid_path):
            return False
        pid, status = read_pidfile(pid_path)
        # Treat stopping/stale as NOT running (Run can be re-enabled immediately after Stop/Kill)
        if status is not None and str(status).lower() in ("stopping", "stale"):
            return False
        return bool(pid and is_pgid_running(pid))

    def _retry_download_accessions(self, rows, label: str):
        """
        Retry by re-running the Download step for the relevant genome group(s).
        blastdbbuilder does not support per-accession retry; already-downloaded genomes should be skipped quickly.
        """
        if not rows:
            messagebox.showinfo("Try again", "No genomes listed to retry.")
            return

        if shutil.which("blastdbbuilder") is None:
            messagebox.showerror("blastdbbuilder not found", "blastdbbuilder is not on PATH. Activate its environment first.")
            return

        if self._is_job_running_in_cwd():
            messagebox.showinfo("Job running", "A job is currently running in this working directory. Stop it first, then Try again.")
            return

        # Determine which genome group flags are needed based on the log group token
        groups = []
        gseen = set()
        for g, _acc in rows:
            if g not in gseen:
                gseen.add(g)
                groups.append(g)

        lower_map = {
            "archaea": GROUP_FLAGS["Archaea"],
            "bacteria": GROUP_FLAGS["Bacteria"],
            "fungi": GROUP_FLAGS["Fungi"],
            "virus": GROUP_FLAGS["Virus"],
            "plants": GROUP_FLAGS["Plants"],
        }

        cmd = ["blastdbbuilder", "--download"]
        used_any = False
        for g in groups:
            if g in lower_map:
                cmd.append(lower_map[g])
                used_any = True

        if not used_any:
            messagebox.showwarning(
                "Try again",
                "Could not infer genome group flags from the log. Please select group(s) and run Download step manually."
            )
            return

        # Run using the same background/foreground mode selected in the GUI
        cwd, pid_path, log_path, _state_path, summary_path = self._paths()
        cmds = [(label, cmd)]

        self.status_var.set("Starting retry download...")
        self.run_btn.state(["disabled"])
        self._set_try_failed_enabled(False)

        # Show a clear message in Command preview while retry is running
        self.preview_var.set("Re-trying downloading the failed genomes")

        self._waiting_for_progress = True
        self._ignore_next_finish_progress = False
        self.log_text.delete("1.0", "end")
        self._log(f"Retrying download for {len(rows)} genome(s) (failed list)...")

        if self.background_var.get():
            self._start_background(cmds, cwd, pid_path, log_path)
            self._start_follow_summary(summary_path)
            self.status_var.set("Retry running in background. You can close the GUI safely.")
        else:
            self._start_foreground(cmds, cwd, pid_path, log_path, summary_path)

    def _try_again_failed(self):
        rows = self._current_rows_with_status("failed_download")
        self._retry_download_accessions(rows, label="retry_failed")

    def _clear_log(self):
        self.log_text.delete("1.0", "end")
        self.status_var.set("Cleared view.")

    def _log(self, msg: str):
        # Progress-panel cleanup: suppress repeated startup spam
        try:
            if not hasattr(self, "_last_panel_line"):
                self._last_panel_line = None
            s = (msg or "").strip()
            if self._last_panel_line == s and (
                s.startswith("Preparing to start") or
                s.startswith("Waiting for summary.log")
            ):
                return
            self._last_panel_line = s
        except Exception:
            pass
        self.log_q.put(msg)

    def _poll_log_queue(self):
        try:
            while True:
                msg = self.log_q.get_nowait()
                # Fix A: normalize emoji symbols for GUI compatibility
                msg = (msg.replace("[OK]", "[OK]")
                          .replace("->", "->")
                          .replace("[WARN]", "[WARN]"))
                self.log_text.insert("end", msg + ("\n" if not msg.endswith("\n") else ""))
                self.log_text.see("end")
        except queue.Empty:
            pass
        self.after(150, self._poll_log_queue)

    def _paths(self):
        cwd = os.path.abspath(os.path.expanduser(self.cwd_var.get().strip()))
        return (
            cwd,
            os.path.join(cwd, PID_FILE),
            os.path.join(cwd, LOG_FILE),
            os.path.join(cwd, STATE_FILE),
            os.path.join(cwd, SUMMARY_FILE),
        )

    def _cleanup_metadata_layout(self, cwd: str) -> None:
        """Align filesystem layout with the CLI contract.

        - Persistent metadata lives ONLY in: ./metadata/
        - Working assembly summaries live ONLY in: ./db/<group>/assembly_summary.txt
        - Remove deprecated locations/files that can confuse resume logic.
        """
        try:
            names = [
                "assembly_summary.txt",
                "assembly_summary_refseq.txt",
                "assembly_summary_genbank.txt",
                "summary.txt",
            ]
            # project root stray files
            for nm in names:
                p = os.path.join(cwd, nm)
                if os.path.isfile(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass

            # db root stray files (not group dirs)
            db_root = os.path.join(cwd, "db")
            for nm in names:
                p = os.path.join(db_root, nm)
                if os.path.isfile(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass

            # Remove deprecated db/metadata (CLI writes to ./metadata)
            db_meta = os.path.join(db_root, "metadata")
            if os.path.isdir(db_meta):
                shutil.rmtree(db_meta, ignore_errors=True)

            # Ensure ./metadata exists
            os.makedirs(os.path.join(cwd, "metadata"), exist_ok=True)
        except Exception:
            return


    def _groups_from_state(self, cwd: str):
        """Best-effort: read previously selected groups from the saved STATE file.

        Returns lowercase group directory names (e.g. ['archaea']).
        """
        try:
            state_path = os.path.join(cwd, STATE_FILE)
            if not os.path.exists(state_path):
                return []
            with open(state_path, "r", encoding="utf-8", errors="replace") as f:
                st = json.load(f)
            groups = st.get("groups") or st.get("selected_groups") or st.get("genome_groups") or []
            out = []
            for g in groups:
                if not g:
                    continue
                gs = str(g).strip()
                if not gs:
                    continue
                # Convert display names to directory names (Archaea -> archaea)
                out.append(gs.lower())
            # De-dup preserve order
            seen = set()
            final = []
            for g in out:
                if g in seen:
                    continue
                seen.add(g)
                final.append(g)
            return final
        except Exception:
            return []


        # --- NCBI metadata (assembly summary) handling -----------------------------

    def _metadata_dir(self, cwd: str) -> str:
        """Directory to keep dated metadata snapshots (same level as db/)."""
        return os.path.join(cwd, "metadata")


    def _metadata_path(self) -> str:
        """Destination path for the latest-only assembly summary snapshot (for diagnostics/UI).

        This matches the CLI behavior:
          ./metadata/assembly_summary_<group>.txt
        """
        try:
            cwd, _, _, _, _ = self._paths()
        except Exception:
            cwd = os.path.abspath(os.path.expanduser(self.cwd_var.get().strip())) if hasattr(self, "cwd_var") else os.getcwd()
        try:
            groups = self._selected_groups()
        except Exception:
            groups = []
        g = (groups[0] if groups else "unknown").lower()
        return os.path.join(self._metadata_dir(cwd), f"assembly_summary_{g}.txt")

    def _candidate_summary_paths(self, cwd: str, group: str | None):
        """Return possible locations of the NCBI assembly summary TSV.

        blastdbbuilder historically used a few names/locations across versions.
        We check a small set conservatively.
        """
        group_l = (group or "").lower().strip()
        paths = []

        # Common locations
        db_root = os.path.join(cwd, "db")
        if group_l:
            paths += [
                os.path.join(db_root, group_l, "assembly_summary.txt"),
                os.path.join(db_root, group_l, "assembly_summary_refseq.txt"),
                os.path.join(db_root, group_l, "assembly_summary_genbank.txt"),
                os.path.join(db_root, group_l, "summary.txt"),
            ]

        paths += [
            os.path.join(db_root, "assembly_summary.txt"),
            os.path.join(db_root, "assembly_summary_refseq.txt"),
            os.path.join(db_root, "assembly_summary_genbank.txt"),
            os.path.join(db_root, "summary.txt"),
            os.path.join(cwd, "assembly_summary.txt"),
            os.path.join(cwd, "assembly_summary_refseq.txt"),
            os.path.join(cwd, "assembly_summary_genbank.txt"),
            os.path.join(cwd, "summary.txt"),
        ]

        # De-dup while preserving order
        seen = set()
        out = []
        for p in paths:
            if p in seen:
                continue
            seen.add(p)
            out.append(p)
        return out

    def _metadata_file_is_valid(self, path: str) -> bool:
        """Validate an NCBI assembly_summary-style TSV.

        The file may start with 1+ comment/metadata lines. We accept the first
        tab-delimited header-like line (often begins with '# assembly_accession')
        and require at least one subsequent non-empty, non-comment data row.
        """
        try:
            header_line = None
            data_line = None
            with open(path, "r", encoding="utf-8", errors="replace") as fp:
                # Find header-like line
                for line in fp:
                    if not line.strip():
                        continue
                    # Candidate header must be tab-delimited
                    if "	" in line:
                        header_line = line
                        break
                if not header_line:
                    return False
                # Find first data line after header
                for line in fp:
                    if not line.strip():
                        continue
                    # Skip comment lines
                    if line.lstrip().startswith("#"):
                        continue
                    data_line = line
                    break

            if not data_line:
                return False

            # Basic sanity: header has at least 2 columns
            if header_line.count("	") < 1:
                return False

            return True
        except Exception:
            return False

    def _rename_invalid_metadata(self, path: str):
        """Rename an invalid summary file to *.bak (timestamped if needed)."""
        try:
            bak = path + ".bak"
            if os.path.exists(bak):
                ts = time.strftime("%Y%m%d%H%M%S")
                bak = bak + f".{ts}"
            os.replace(path, bak)
        except Exception:
            try:
                os.remove(path)
            except Exception:
                pass

    def _prepare_metadata_before_download(self, cwd: str, groups):
        """Resume-safe assembly summary logic (Improvement 1).

        On resume, if an assembly summary exists:
          - verify header + nonzero rows
          - if valid -> reuse (do not re-download)
          - if invalid -> rename to *.bak so a clean re-download happens
        """
        if not groups:
            # Still validate any top-level summary.txt / db/assembly_summary.txt if present
            groups = []

        # Validate per-group paths first (most specific), then shared paths.
        checked = set()
        for g in (groups or [None]):
            for p in self._candidate_summary_paths(cwd, g):
                if p in checked:
                    continue
                checked.add(p)
                if not os.path.exists(p):
                    continue
                if self._metadata_file_is_valid(p):
                    # Reuse: keep as-is.
                    continue
                # Invalid: quarantine and force clean fetch
                self._rename_invalid_metadata(p)

    def _metadata_archive_name(self, group: str | None) -> str:
        date_tag = time.strftime("%Y%m%d")
        g = (group or "unknown").lower()
        return f"summary_{g}_{date_tag}.tsv"


    def _archive_metadata_snapshot(self, cwd: str, groups):
        """Persist only the latest per-group assembly summary into ./metadata/.

        Writes (overwrites):
          ./metadata/assembly_summary_<group>.txt

        Also removes any legacy dated files like summary_<group>_<date>.tsv in ./metadata/.
        """
        try:
            meta_dir = self._metadata_dir(cwd)
            os.makedirs(meta_dir, exist_ok=True)
        except Exception:
            return

        if not groups:
            groups = ["unknown"]

        for g in groups:
            gl = (g or "unknown").lower().strip()

            # Prefer the working copy produced by the CLI: db/<group>/assembly_summary.txt
            src = os.path.join(cwd, "db", gl, "assembly_summary.txt")
            if not os.path.exists(src):
                # Fallback to older layouts if present
                src = None
                for p in self._candidate_summary_paths(cwd, g):
                    if os.path.exists(p):
                        src = p
                        break
            if not src:
                continue

            dst = os.path.join(meta_dir, f"assembly_summary_{gl}.txt")
            try:
                shutil.copy2(src, dst)
            except Exception:
                pass

        # Remove legacy dated snapshots (GUI older behavior)
        try:
            for fn in os.listdir(meta_dir):
                if fn.startswith("summary_") and fn.endswith(".tsv"):
                    try:
                        os.remove(os.path.join(meta_dir, fn))
                    except Exception:
                        pass
        except Exception:
            pass


    def _finalize_job_end(self, cwd: str, pid: int | None, reason: str) -> None:
        """Unified finalizer for BOTH natural completion and Stop/Force-Kill.

        This is the single place that:
        - archives a metadata snapshot (best-effort)
        - stops summary tail-follow
        - marks PID file stale (so UI won't stay 'running')
        - re-enables Run
        - sets a clear status message
        """
        try:
            _cwd, pid_path, _log_path, _state_path, summary_path = self._paths()
        except Exception:
            pid_path, summary_path = None, None

        # Best-effort archive of metadata snapshot
        try:
            self._archive_metadata_snapshot(cwd, self._groups_from_state(cwd) or self._selected_groups())
        except Exception:
            pass

        # Stop tail-following (if any)
        try:
            self._stop_follow_summary()
        except Exception:
            pass

        # Mark PID file as stale (or remove it) so future Detect doesn't treat it as running
        if pid_path and os.path.exists(pid_path):
            try:
                old_pid, _old_status = read_pidfile(pid_path)
                if pid is None or old_pid is None or int(old_pid) == int(pid):
                    # Preserve the numeric PID for forensics, but mark it stale.
                    write_pidfile(pid_path, old_pid, status="stale")
            except Exception:
                # If pidfile is corrupt, just remove it.
                try:
                    os.remove(pid_path)
                except Exception:
                    pass

        # Cancel watcher
        try:
            if self._watch_after_id is not None:
                self.after_cancel(self._watch_after_id)
        except Exception:
            pass
        self._watch_after_id = None
        self._watched_pid = None

        # Refresh progress panel content (summary.log)
        try:
            if summary_path:
                self._show_summary_if_exists(summary_path)
        except Exception:
            pass

        # Re-enable Run (core requirement)
        try:
            self.run_btn.state(["!disabled"])
        except Exception:
            pass

        # Allow Try-again buttons again
        try:
            self._set_try_failed_enabled(True)
        except Exception:
            pass

        # Status line
        try:
            if reason == "stopped":
                self.status_var.set("Job stopped. Run is ready.")
            elif reason == "killed":
                self.status_var.set("Job killed. Run is ready.")
            else:
                # Natural completion
                self.status_var.set(self._completion_status_text(cwd) + " Run is ready.")
        except Exception:
            pass


    def _finalize_after_job_if_needed(self, cwd: str) -> None:
        """Backward compatible wrapper (used by older call sites)."""
        self._finalize_job_end(cwd, pid=None, reason="completed")


    def _completion_status_text(self, cwd: str) -> str:
        """Best-effort status line after a natural completion."""
        try:
            state_path = os.path.join(cwd, STATE_FILE)
            if os.path.exists(state_path):
                with open(state_path, "r", encoding="utf-8", errors="replace") as f:
                    st = json.load(f)
                act = (st.get("action") or "").lower().strip()
            else:
                act = ""
        except Exception:
            act = ""

        if act == "download":
            return "Download completed successfully."
        if act == "concat":
            return "Concat completed successfully."
        if act == "build":
            return "Build completed successfully."
        if act == "all":
            return "Run all completed successfully."
        return "Job completed successfully."

    # ---------------- Natural completion detection from summary.log ----------------
    def _summary_indicates_natural_completion(self, cwd: str) -> bool:
        """Return True if summary.log clearly indicates that the selected action finished,
        even if the PID/process group lingers (common for concat/build wrappers).

        We only scan the tail to keep it fast.
        """
        try:
            summary_path = os.path.join(cwd, SUMMARY_FILE)
            if not os.path.exists(summary_path):
                return False

            # What action are we expecting to finish?
            action = (self.action_var.get() or "").strip().lower()
            if not action:
                # If action isn't selected (e.g. reopened GUI), try STATE_FILE
                try:
                    st_path = os.path.join(cwd, STATE_FILE)
                    if os.path.exists(st_path):
                        with open(st_path, "r", encoding="utf-8", errors="replace") as f:
                            st = json.load(f)
                        action = (st.get("action") or "").strip().lower()
                except Exception:
                    action = ""

            # Read last ~300 lines (enough to catch completion markers)
            with open(summary_path, "r", encoding="utf-8", errors="replace") as fp:
                lines = fp.readlines()[-300:]

            text = "\n".join(lines)

            # --- Completion signatures ---
            # Concat: you log a line containing "[OK]" and "Concatenated ... into ..."
            concat_done = (("Concatenated" in text) and (" into " in text) and (("[OK]" in text) or ("[OK]" in text)))

            # Build: summary.log may include makeblastdb output OR your own GUI-level success wording.
            # Keep it permissive but anchored to build context.
            t_low = text.lower()

            # Common GUI marker seen in your summary panel:
            #   [OK] BLAST DB built: /path/to/db
            ok_blastdb_built = ("blast db built" in t_low) or ("[ok] blast db built" in t_low) or ("ok] blast db built" in t_low)

            # Some runs may only show makeblastdb stdout/stderr
            makeblastdb_done = ("makeblastdb" in t_low) and (
                ("finished" in t_low) or ("completed" in t_low) or ("success" in t_low) or ("done" in t_low)
            )

            build_done = ok_blastdb_built or makeblastdb_done

            # Download / All: blastdbbuilder often prints "All genomes processed for ..."
            download_done = ("All genomes processed for" in text)

            if action == "concat":
                return concat_done
            if action == "build":
                return build_done
            if action == "download":
                return download_done
            if action == "all":
                # For "all", accept any strong terminal marker
                return download_done or build_done

            # If unknown action, be conservative.
            return False
        except Exception:
            return False

    def _force_finalize_if_summary_says_done(self, cwd: str, pid: int | None) -> bool:
        """If summary.log says the action is done, finalize immediately and mark pidfile stale,
        even if process group still exists.
        """
        if not self._summary_indicates_natural_completion(cwd):
            return False

        self._finalize_job_end(cwd, pid, reason="completed")
        return True

    # ---------------- Job lifecycle watcher ----------------
    def _start_job_watch(self, pid: int) -> None:
        """Poll the job PID and refresh UI once it ends (covers normal exit / Stop / Force Kill)."""
        try:
            pid = int(pid)
        except Exception:
            return

        self._watched_pid = pid

        # Cancel any existing watch
        if self._watch_after_id is not None:
            try:
                self.after_cancel(self._watch_after_id)
            except Exception:
                pass
            self._watch_after_id = None

        self._watch_after_id = self.after(800, self._poll_job_watch)

    def _poll_job_watch(self) -> None:
        """Internal: check watched PID (or PID file) and refresh once it is gone."""
        cwd, pid_path, _log_path, _state_path, _summary_path = self._paths()

        pid = None
        if os.path.exists(pid_path):
            pid, _status = read_pidfile(pid_path)

        if pid is None:
            pid = self._watched_pid

        if pid is None:
            self._watch_after_id = None
            return

        if is_pgid_running(pid):
            self._watch_after_id = self.after(800, self._poll_job_watch)
            return

        # Job ended -> finalize (re-enable Run) and refresh UI
        self._watch_after_id = None
        ended_pid = pid
        self._watched_pid = None

        # Determine end reason from pidfile status (Stop/Kill mark status=stopping)
        reason = "completed"
        try:
            if os.path.exists(pid_path):
                _p, st = read_pidfile(pid_path)
                if st is not None and str(st).lower() in ("stopping", "stale"):
                    reason = "stopped"
        except Exception:
            pass

        self._finalize_job_end(cwd, ended_pid, reason)
        # Keep UI consistent with Detect running job view
        self._detect_and_attach(silent=True)


    def _poll_pid_and_refresh(self, pid: int):
        """Re-enable Run once PID is no longer running (used by Stop/Force Kill)."""
        # Delegate to the unified watcher (kept for backward compatibility with existing callers)
        self._start_job_watch(pid)
        
    def _auto_detect_job(self):
        self._detect_and_attach(silent=True)

    def _detect_job_clicked(self):
        self._detect_and_attach(silent=False)

    def _detect_and_attach(self, silent: bool):
        cwd, pid_path, _log_path, _state_path, summary_path = self._paths()
        if not cwd or not os.path.isdir(cwd):
            return

        pid, status = (None, None)
        if os.path.exists(pid_path):
            pid, status = read_pidfile(pid_path)

        # If a Stop/Kill was requested, treat job as not running for UI purposes
        stopping = (status is not None and str(status).lower() in ("stopping", "stale"))
        running = bool((not stopping) and pid and is_pgid_running(pid))

        # NEW: If summary.log proves completion, do NOT stay stuck in \"running\"
        if running and self._force_finalize_if_summary_says_done(cwd, pid):
            running = False
            stopping = True  # prevents re-attaching to tail as \"running\"

        prev_pid = getattr(self, "_last_attached_pid", None)

        # Always show full summary.log contents if it exists (even if job already finished)
        self._show_summary_if_exists(summary_path)

        if running:
            self._start_follow_summary(summary_path)
            self._last_attached_pid = pid
            self._start_job_watch(pid)
            self.status_var.set(f"Detected running job (PID {pid}). Monitoring progress.")
            self.run_btn.state(["disabled"])
            self._set_try_failed_enabled(False)
        else:
            # If we were previously attached to a running job and it ended, finalize (shared with Stop/Kill).
            if prev_pid is not None:
                reason = "completed" if not stopping else "stopped"
                self._finalize_job_end(cwd, prev_pid, reason)
                self._last_attached_pid = None
            else:
                self.status_var.set("No running job detected in this working directory.")
                self.run_btn.state(["!disabled"])
                self._stop_follow_summary()
                self._set_try_failed_enabled(True)

        if (not silent) and (pid is None) and (not os.path.exists(summary_path)):
            messagebox.showinfo("No job found", "No PID/summary found in this working directory.")


    def _clean_summary_file(self, summary_path: str) -> None:
        """Remove noisy per-accession download lines and redundant finish markers from summary.log."""
        if not os.path.exists(summary_path):
            return
        try:
            with open(summary_path, "r", encoding="utf-8", errors="replace") as fp:
                lines = fp.readlines()

            def _is_noise(ln: str) -> bool:
                return (
                    ("[OK] Downloaded " in ln) or
                    ("[OK] Downloaded " in ln) or
                    (" Downloaded GCF_" in ln) or
                    (" status=finish ok=" in ln)
                )

            filtered = [ln for ln in lines if not _is_noise(ln)]
            if filtered == lines:
                return

            tmp_path = summary_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8", errors="replace") as fp:
                fp.writelines(filtered)
            os.replace(tmp_path, summary_path)
        except Exception:
            return


    def _job_active_for_ui(self) -> bool:
        """Return True if a job is considered active (running/starting) so we should NOT print the idle Ready message."""
        try:
            _cwd, pid_path, _log_path, _state_path, _summary_path = self._paths()
            if pid_path and os.path.exists(pid_path):
                pid, status = read_pidfile(pid_path)
                stopping = (status is not None and str(status).lower() in ("stopping", "stale"))
                if (not stopping) and pid and is_pgid_running(pid):
                    return True
        except Exception:
            pass
        return bool(getattr(self, "_watched_pid", None) or getattr(self, "_waiting_for_progress", False))


    def _show_summary_if_exists(self, summary_path: str):
        """Load summary.log into the panel (static view) and keep it clean.

        - Always filters per-accession 'Downloaded' noise lines.
        - Uses _clean_summary_file() to optionally rewrite the file too.
        """
        if not os.path.exists(summary_path):
            if self._job_active_for_ui():
                return
            self.log_text.delete("1.0", "end")
            self._waiting_for_progress = False
            self._ignore_next_finish_progress = False
            if not self._job_active_for_ui():
                self._log("Ready. Select options and click Run.")
            return

        # Clean file (best-effort)
        try:
            self._clean_summary_file(summary_path)
        except Exception:
            pass

        try:
            with open(summary_path, "r", encoding="utf-8", errors="replace") as fp:
                data = fp.read()
        except Exception:
            return

        # Filter redundant per-accession 'Downloaded' lines from display on EVERY reload
        try:
            data_lines = data.splitlines(True)
            data_lines = [
                ln for ln in data_lines
                if ("[OK] Downloaded " not in ln)
                and ("[OK] Downloaded " not in ln)
                and (" Downloaded GCF_" not in ln)
            ]
            data = "".join(data_lines)
        except Exception:
            pass

        self.log_text.delete("1.0", "end")
        if not data.strip():
            if not self._job_active_for_ui():
                self._log("Ready. Select options and click Run.")
            return

        self.log_text.insert("end", data if data.endswith("\n") else (data + "\n"))
        self.log_text.see("end")


    def _latest_status_map(self):
        """Return {accession: (group, status)} where status is the *latest* status seen in summary.log.
        This is important because summary.log is append-only across retries; we want the most recent status to win.
        """
        _cwd, _pid_path, _log_path, _state_path, summary_path = self._paths()
        status_map = {}
        if not os.path.exists(summary_path):
            return status_map

        try:
            with open(summary_path, "r", encoding="utf-8", errors="replace") as fp:
                for line in fp:
                    # Extract accession
                    acc = None
                    for part in line.strip().split():
                        if part.startswith("GCF_") or part.startswith("GCA_"):
                            acc = part
                            break
                    if not acc:
                        continue

                    m = re.search(r"status=([A-Za-z0-9_]+)", line)
                    if not m:
                        continue
                    status = m.group(1)

                    toks = re.findall(r"\[(.*?)\]", line)
                    group = toks[2] if len(toks) >= 3 else (toks[-1] if toks else "unknown")

                    # Last occurrence wins
                    status_map[acc] = (group, status)
        except Exception:
            return {}

        return status_map

    def _current_rows_with_status(self, wanted_status: str):
        """Return sorted list of (group, accession) for accessions whose *latest* status equals wanted_status."""
        m = self._latest_status_map()
        rows = [(g, acc) for acc, (g, st) in m.items() if st == wanted_status]
        rows.sort(key=lambda x: (x[0], x[1]))
        return rows

    def _show_failed_genomes(self):
        rows = self._current_rows_with_status("failed_download")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "Failed genomes (latest status=failed_download)\n\n")
        if not rows:
            self.log_text.insert("end", "No failed genomes found.\n")
        else:
            for g, acc in rows:
                self.log_text.insert("end", f"[{g}] {acc}\n")
        self.log_text.see("end")
        self.status_var.set(f"Showing failed genomes: {len(rows)} (Click Refresh to return to live log)")

    def _show_skipped_genomes(self):
        rows = self._current_rows_with_status("skipped")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "Skipped genomes (latest status=skipped)\n\n")
        if not rows:
            self.log_text.insert("end", "No skipped genomes found.\n")
        else:
            for g, acc in rows:
                self.log_text.insert("end", f"[{g}] {acc}\n")
        self.log_text.see("end")
        self.status_var.set(f"Showing skipped genomes: {len(rows)} (Click Refresh to return to live log)")

    def _start_follow_summary(self, summary_path: str):
        if not os.path.exists(summary_path):
            self._waiting_for_progress = True
            self.log_text.delete("1.0", "end")
            self._log("Waiting for summary.log to appear...")
            self._stop_follow_summary()
            return

        self._clean_summary_file(summary_path)
        try:
            if self._tail_fp is None or self._tail_path != summary_path:
                self._tail_path = summary_path
                self._tail_fp = open(summary_path, "r", encoding="utf-8", errors="replace")
                self._tail_fp.seek(0, os.SEEK_END)
                self._tail_pos = self._tail_fp.tell()
        except Exception:
            self._tail_fp = None
            self._tail_path = None
            return

        self.after(500, self._poll_tail_summary)

    def _stop_follow_summary(self):
        try:
            if self._tail_fp is not None:
                self._tail_fp.close()
        except Exception:
            pass
        self._tail_fp = None
        self._tail_path = None
        self._tail_pos = 0

    def _poll_tail_summary(self):
        if self._tail_fp is None:
            return

        # If background/foreground job ended, stop tailing and re-enable Run
        try:
            cwd, pid_path, _log_path, _state_path, _summary_path = self._paths()
            if os.path.exists(pid_path):
                pid, status = read_pidfile(pid_path)
                # NEW: Natural completion from summary.log overrides lingering PID/processes
                if self._force_finalize_if_summary_says_done(cwd, pid):
                    self._detect_and_attach(silent=True)
                    return
                # Even if PID lingers, stopping status means user already requested stop
                if (status is not None and str(status).lower() in ("stopping", "stale")) or (pid and (not is_pgid_running(pid))):
                    # Job ended -> unified finalizer
                    reason = "completed"
                    try:
                        if status is not None and str(status).lower() in ("stopping", "stale"):
                            reason = "stopped"
                    except Exception:
                        pass
                    self._finalize_job_end(cwd, pid, reason)
                    self._detect_and_attach(silent=True)
                    return
        except Exception:
            pass
        try:
            self._tail_fp.seek(self._tail_pos)
            chunk = self._tail_fp.read()
            self._tail_pos = self._tail_fp.tell()
            if chunk:
                saw_noise = False
                for line in chunk.splitlines():
                    if ("[OK] Downloaded " in line) or ("[OK] Downloaded " in line) or (" Downloaded GCF_" in line) or (" status=finish ok=" in line):
                        saw_noise = True
                        continue

                    # ---- Phase completion detection (concat/build) ----
                    if ("[OK]" in line) and ("Concatenated" in line) and (" into " in line):
                        self.status_var.set("Concatenation completed successfully")
                    if ("makeblastdb" in line.lower()) and (("finished" in line.lower()) or ("completed" in line.lower()) or ("success" in line.lower())):
                        self.status_var.set("BLAST database build completed")

                    if self._waiting_for_progress:
                        self.log_text.delete("1.0", "end")
                        self._waiting_for_progress = False
                    self._log(line)

                if saw_noise and self._tail_path:
                    self._clean_summary_file(self._tail_path)
        except Exception:
            return
        self.after(700, self._poll_tail_summary)

    def _filter_summary_line_for_display(self, line: str):
        s = line.strip()
        if not s:
            return None

        if "All genomes processed for" in s:
            self._ignore_next_finish_progress = True
            return s

        if s.startswith("[progress]"):
            if self._ignore_next_finish_progress and "status=finish" in s:
                self._ignore_next_finish_progress = False
                return None
            if ("status=downloaded" in s) or ("status=skipped" in s) or ("status=failed" in s):
                return s
            return None

        return None

        def _load_summary_into_panel(self, summary_path: str, *, tail_follow: bool):

            """Load existing summary.log so the user can scroll; optionally follow/tail if job still running."""

            try:

                if not os.path.exists(summary_path):

                    self.log_text.delete("1.0", "end")

                    if not self._job_active_for_ui():
                        self._log("Ready. Select options and click Run.")

                    self._waiting_for_progress = False

                    return


                with open(summary_path, "r", encoding="utf-8", errors="replace") as fp:

                    lines = fp.read().splitlines()


                out = []

                for ln in lines:

                    s = ln.strip()

                    if "All genomes processed for" in s:

                        out.append(s)

                        continue

                    if "[progress]" in s:

                        if "status=finish" in s:

                            continue

                        if ("status=downloaded" in s) or ("status=skipped" in s) or ("status=failed" in s):

                            out.append(s)


                self.log_text.delete("1.0", "end")

                if out:

                    self.log_text.insert("end", "\n".join(out) + "\n")

                    self.log_text.see("end")

                    self._waiting_for_progress = False

                else:

                    if not self._job_active_for_ui():
                        self._log("Ready. Select options and click Run.")

                    self._waiting_for_progress = False


                if tail_follow:

                    try:

                        if self._tail_fp is None or getattr(self._tail_fp, "name", None) != summary_path:

                            self._tail_fp = open(summary_path, "r", encoding="utf-8", errors="replace")

                        self._tail_fp.seek(0, os.SEEK_END)

                        self._tail_pos = self._tail_fp.tell()

                        self.after(500, self._poll_tail)

                    except Exception as e:

                        self._log(f"[Tail ERROR] {e}")

            except Exception as e:

                self.log_text.delete("1.0", "end")

                self._log(f"[Read ERROR] {e}")

                self._waiting_for_progress = False


    def _stop(self):
        _, pid_path, _, _, _ = self._paths()
        if not os.path.exists(pid_path):
            messagebox.showinfo("Stop", "No PID file found in this working directory.")
            return
        pid, _status = read_pidfile(pid_path)
        if pid is None:
            messagebox.showerror("Stop", "PID file is invalid.")
            return

        if not is_pgid_running(pid):
            messagebox.showinfo("Stop", f"Process {pid} is not running.")
            self._detect_and_attach(silent=True)
            return

        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM) 
            self._log(f"[Stop] Sent SIGTERM to process group PID {pid}")
            self._log("[INFO] Download interrupted by user.")
            self.status_var.set(f"Stopping job (PID {pid})...")
            # Mark as stopping so Run can re-enable immediately (even if PID lingers briefly)
            write_pidfile(pid_path, pid, status="stopping")
            self._detect_and_attach(silent=True)

            # Re-enable Run immediately (even before PID fully exits)
            try:
                self.run_btn.state(["!disabled"])
            except Exception:
                pass
            try:
                self._set_try_failed_enabled(True)
            except Exception:
                pass

            # Still watch PID to finalize once it truly exits
            self._poll_pid_and_refresh(pid)
            # Ensure metadata dir exists and snapshot what we have so far (kept even if Keep downloads = NO)
            try:
                cwd, _, _, _, _ = self._paths()
                os.makedirs(self._metadata_dir(cwd), exist_ok=True)
                self._archive_metadata_snapshot(cwd, self._groups_from_state(cwd) or self._selected_groups())
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Stop failed", str(e))

    def _kill(self):
        _, pid_path, _, _, _ = self._paths()
        if not os.path.exists(pid_path):
            messagebox.showinfo("Force Kill", "No PID file found in this working directory.")
            return
        pid, _status = read_pidfile(pid_path)
        if pid is None:
            messagebox.showerror("Force Kill", "PID file is invalid.")
            return

        if not is_pgid_running(pid):
            messagebox.showinfo("Force Kill", f"Process {pid} is not running.")
            return

        if not messagebox.askyesno("Force Kill", "This will immediately kill the job. Continue?"):
            return

        try:
            os.killpg(os.getpgid(pid), signal.SIGKILL)
            self._log(f"[Force Kill] Sent SIGKILL to process group PID {pid}")
            self._log("[INFO] Download interrupted by user.")
            self.status_var.set(f"Killed job (PID {pid}).")
            # Mark as stopping so Run can re-enable immediately
            write_pidfile(pid_path, pid, status="stopping")
            self._detect_and_attach(silent=True)

            # Re-enable Run immediately
            try:
                self.run_btn.state(["!disabled"])
            except Exception:
                pass
            try:
                self._set_try_failed_enabled(True)
            except Exception:
                pass

            self._poll_pid_and_refresh(pid)
            # Ensure metadata dir exists and snapshot what we have so far (kept even if Keep downloads = NO)
            try:
                cwd, _, _, _, _ = self._paths()
                os.makedirs(self._metadata_dir(cwd), exist_ok=True)
                self._archive_metadata_snapshot(cwd, self._groups_from_state(cwd) or self._selected_groups())
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Force Kill failed", str(e))

    def _run(self):
        cwd, pid_path, log_path, state_path, summary_path = self._paths()


        # Align metadata layout with the CLI (./metadata only; no stray root files)
        self._cleanup_metadata_layout(cwd)

        if not cwd or not os.path.isdir(cwd):
            messagebox.showerror("Invalid directory", "Please select a valid working directory.")
            return

        if shutil.which("blastdbbuilder") is None:
            messagebox.showerror("blastdbbuilder not found", "blastdbbuilder is not on PATH. Activate its environment first.")
            return

        if self.action_var.get() in ("download", "all") and not self._selected_groups():
            messagebox.showerror("No groups selected", "Select at least one genome group for Download.")
            return

        if os.path.exists(pid_path):
            try:
                old_pid, old_status = read_pidfile(pid_path)
                if (old_status is None or str(old_status).lower() not in ("stopping", "stale")) and old_pid and is_pgid_running(old_pid):
                    messagebox.showinfo("Already running", f"A job is already running in this directory (PID {old_pid}).")
                    self._detect_and_attach(silent=True)
                    return
            except Exception:
                pass

        cmds = self._cmds_for_action()
        self.status_var.set("Starting job...")
        self.run_btn.state(["disabled"])
        self._set_try_failed_enabled(False)

        state = {
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "cwd": cwd,
            "action": self.action_var.get(),
            "groups": self._selected_groups(),
            "commands": [{"step": tag, "cmd": cmd} for tag, cmd in cmds],
        }
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

        # Robust logging (to GUI log file, not the progress panel)
        try:
            meta_path = self._metadata_path()
            with open(log_path, "a", encoding="utf-8", errors="replace") as lf:
                lf.write(f"\n[Diag] summary destination path: {meta_path}\n")
        except Exception:
            pass

        self._waiting_for_progress = True
        self._ignore_next_finish_progress = False
        self.log_text.delete("1.0", "end")

        act = self.action_var.get()

        # --- Resume-aware metadata handling (summary.txt) ---
        if act in ("download", "all"):
            self._prepare_metadata_before_download(cwd, self._selected_groups())
            # Ensure metadata directory exists immediately (even if Keep downloads = NO).
            try:
                os.makedirs(self._metadata_dir(cwd), exist_ok=True)
            except Exception:
                pass
            # Try an early snapshot (may be a no-op if assembly summary not downloaded yet).
            try:
                self._archive_metadata_snapshot(cwd, self._groups_from_state(cwd) or self._selected_groups())
            except Exception:
                pass


            # Progress panel: show only the requested clean startup lines
            self._log("===== METADATA =====")
            self._log(f"[Diag] summary destination path: {self._metadata_path()}")
            self._log("Preparing to start download... (waiting for summary.log updates)")
            self._log("")
            self._log("===== GENOME DOWNLOAD =====")
        else:
            # Non-download steps keep a simple, single-line startup message
            start_msg = "Preparing to start blastdbbuilder..."
            if act == "concat":
                start_msg = "Preparing to start concatenation... (this step may be quiet until it finishes)"
            elif act == "build":
                start_msg = "Preparing to start BLAST database build... (this step may be quiet until it finishes)"
            self._log(start_msg)

        if self.background_var.get():
            self._start_background(cmds, cwd, pid_path, log_path)
            self._start_follow_summary(summary_path)
            self.status_var.set("Running in background. You can close the GUI safely.")
            return

        self._start_foreground(cmds, cwd, pid_path, log_path, summary_path)

    def _start_background(self, cmds, cwd, pid_path, log_path):
        # Best-effort UI status at launch (background steps run in bash)
        try:
            if cmds:
                first_tag = cmds[0][0]
                if first_tag == "concat":
                    self.status_var.set("Concatenation running...")
                    self._log("[Phase] Concatenation running...")
                elif first_tag == "build":
                    self.status_var.set("BLAST database build running...")
                    self._log("[Phase] BLAST database build running...")
                elif first_tag == "download":
                    self.status_var.set("Downloading genomes...")
                    self._log("[Phase] Download running...")
        except Exception:
            pass
        bash_lines = [
            "set -e",
            'echo "=== blastdbbuilder GUI started: $(date) ==="',
            f'echo "Working dir: {cwd}"',
        ]
        for tag, cmd in cmds:
            bash_lines.append('echo ""')
            bash_lines.append(f'echo "$ (step={tag}) {" ".join(cmd)}"')
            bash_lines.append(" ".join(cmd))
            bash_lines.append(f'echo "[{tag} finished] return=$?"')
        bash_lines.append('echo "=== blastdbbuilder GUI finished: $(date) ==="')

        script = "\n".join(bash_lines)
        open(log_path, "a", encoding="utf-8").close()

        log_fp = open(log_path, "a", encoding="utf-8", errors="replace")
        p = subprocess.Popen(
            ["/bin/bash", "-lc", script],
            cwd=cwd,
            stdout=log_fp,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            text=True,
        )

        with open(pid_path, "w", encoding="utf-8") as f:
            f.write(str(p.pid) + "\n")

        self._log(f"[Started] Background job PID {p.pid}")
        self._detect_and_attach(silent=True)

    def _start_foreground(self, cmds, cwd, pid_path, log_path, summary_path):
        def worker():
            with open(log_path, "a", encoding="utf-8", errors="replace") as log_fp:
                # Follow summary.log live in foreground too
                self._start_follow_summary(summary_path)

                for tag, cmd in cmds:
                    # Update UI status by phase (helps during quiet steps like concat/build)
                    if tag == "concat":
                        self.status_var.set("Concatenation running...")
                        self._log("[Phase] Concatenation running...")
                    elif tag == "build":
                        self.status_var.set("BLAST database build running...")
                        self._log("[Phase] BLAST database build running...")
                    elif tag == "download":
                        self.status_var.set("Downloading genomes...")
                        self._log("[Phase] Download running...")
                    log_fp.write(f"\n$ (step={tag}) {' '.join(cmd)}\n")
                    log_fp.flush()
                    p = subprocess.Popen(
                        cmd,
                        cwd=cwd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        start_new_session=True,
                        bufsize=1,
                        universal_newlines=True,
                    )

                    with open(pid_path, "w", encoding="utf-8") as f:
                        f.write(str(p.pid) + "\n")

                    if p.stdout is not None:
                        for line in p.stdout:
                            # Build completion hint from makeblastdb output
                            try:
                                ll = line.lower()
                                if tag == "build" and ("makeblastdb" in ll) and ("finished" in ll or "completed" in ll or "success" in ll):
                                    self.status_var.set("BLAST database build completed")
                            except Exception:
                                pass
                            log_fp.write(line)
                            log_fp.flush()

                    rc = p.wait()
                    log_fp.write(f"[{tag} finished] return={rc}\n")
                    log_fp.flush()

                    if rc != 0:
                        self.status_var.set(f"Failed at {tag} (return={rc})")
                        # Archive metadata snapshot if present
                        try:
                            self._archive_metadata_snapshot(cwd, self._groups_from_state(cwd) or self._selected_groups())
                        except Exception:
                            pass
                        self.run_btn.state(["!disabled"])
                        self._set_try_failed_enabled(True)
                        return

            try:
                self._archive_metadata_snapshot(cwd, self._groups_from_state(cwd) or self._selected_groups())
            except Exception:
                pass

            self.status_var.set("Finished successfully.")
            self.run_btn.state(["!disabled"])
            self._set_try_failed_enabled(True)

        threading.Thread(target=worker, daemon=True).start()
        self.status_var.set("Running (foreground mode). Closing GUI will stop it.")
        self._detect_and_attach(silent=True)


def main():
    App().mainloop()

if __name__ == "__main__":
    main()

