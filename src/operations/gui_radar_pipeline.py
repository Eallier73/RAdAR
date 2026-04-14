from __future__ import annotations

import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from .config import ALLOWED_MODES, DEFAULT_MODEL_RUNNER, DEFAULT_SOURCES, SOURCE_NAMES, STAGE_NAMES


ROOT_DIR = Path(__file__).resolve().parents[2]


class RadarPipelineGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Radar Pipeline Control")
        self.geometry("980x760")
        self.output_queue: queue.Queue[str] = queue.Queue()
        self.process: subprocess.Popen[str] | None = None

        self.week_var = tk.StringVar()
        self.resume_var = tk.StringVar()
        self.mode_var = tk.StringVar(value=ALLOWED_MODES[0])
        self.from_stage_var = tk.StringVar()
        self.to_stage_var = tk.StringVar()
        self.model_runner_var = tk.StringVar(value=DEFAULT_MODEL_RUNNER)
        self.model_run_id_var = tk.StringVar()
        self.model_args_var = tk.StringVar()
        self.fail_fast_var = tk.BooleanVar(value=True)
        self.allow_partial_var = tk.BooleanVar(value=False)
        self.dry_run_var = tk.BooleanVar(value=False)
        self.source_vars = {source: tk.BooleanVar(value=source in DEFAULT_SOURCES) for source in SOURCE_NAMES}

        self._build_widgets()
        self.after(200, self._drain_output_queue)

    def _build_widgets(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)

        form = ttk.Frame(root)
        form.pack(fill=tk.X)

        self._add_entry(form, "Week", self.week_var, 0, "2026-W14 o 2026-03-31")
        self._add_entry(form, "Resume Run ID", self.resume_var, 1, "radar_2026W14_001")
        self._add_entry(form, "Model Runner", self.model_runner_var, 2, DEFAULT_MODEL_RUNNER)
        self._add_entry(form, "Model Run ID", self.model_run_id_var, 3, "opcional")
        self._add_entry(form, "Model Args", self.model_args_var, 4, "--horizons=1 --lags=1,2,3,4")

        ttk.Label(form, text="Mode").grid(row=0, column=2, sticky="w", padx=(20, 6), pady=4)
        ttk.Combobox(form, textvariable=self.mode_var, values=ALLOWED_MODES, state="readonly", width=20).grid(
            row=0, column=3, sticky="ew", pady=4
        )
        ttk.Label(form, text="From Stage").grid(row=1, column=2, sticky="w", padx=(20, 6), pady=4)
        ttk.Combobox(form, textvariable=self.from_stage_var, values=("", *STAGE_NAMES), width=20).grid(
            row=1, column=3, sticky="ew", pady=4
        )
        ttk.Label(form, text="To Stage").grid(row=2, column=2, sticky="w", padx=(20, 6), pady=4)
        ttk.Combobox(form, textvariable=self.to_stage_var, values=("", *STAGE_NAMES), width=20).grid(
            row=2, column=3, sticky="ew", pady=4
        )
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        toggles = ttk.Frame(root)
        toggles.pack(fill=tk.X, pady=(8, 8))
        ttk.Checkbutton(toggles, text="Fail Fast", variable=self.fail_fast_var).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Checkbutton(toggles, text="Allow Partial", variable=self.allow_partial_var).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Checkbutton(toggles, text="Dry Run", variable=self.dry_run_var).pack(side=tk.LEFT, padx=(0, 12))

        sources_frame = ttk.LabelFrame(root, text="Sources", padding=8)
        sources_frame.pack(fill=tk.X, pady=(0, 8))
        for idx, source in enumerate(SOURCE_NAMES):
            ttk.Checkbutton(sources_frame, text=source, variable=self.source_vars[source]).grid(
                row=0, column=idx, sticky="w", padx=(0, 16)
            )

        buttons = ttk.Frame(root)
        buttons.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(buttons, text="Run", command=self.run_pipeline).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons, text="Stop", command=self.stop_pipeline).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons, text="Clear Output", command=self.clear_output).pack(side=tk.LEFT, padx=(0, 8))

        self.command_preview = tk.Text(root, height=4, wrap="word")
        self.command_preview.pack(fill=tk.X, pady=(0, 8))
        self.command_preview.insert("1.0", "Aquí se mostrará el comando a ejecutar.")
        self.command_preview.configure(state=tk.DISABLED)

        self.output_text = tk.Text(root, wrap="word")
        self.output_text.pack(fill=tk.BOTH, expand=True)

    def _add_entry(self, parent: ttk.Frame, label: str, variable: tk.StringVar, row: int, hint: str) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 6), pady=4)
        ttk.Entry(parent, textvariable=variable, width=48).grid(row=row, column=1, sticky="ew", pady=4)
        tk.Label(parent, text=hint, fg="#555555").grid(row=row, column=4, sticky="w", padx=(12, 0), pady=4)

    def _build_command(self) -> list[str]:
        command = [sys.executable, "-m", "src.operations.run_radar_pipeline"]
        if self.week_var.get().strip():
            command.extend(["--week", self.week_var.get().strip()])
        if self.resume_var.get().strip():
            command.extend(["--resume-run-id", self.resume_var.get().strip()])
        command.extend(["--mode", self.mode_var.get().strip()])

        if self.from_stage_var.get().strip():
            command.extend(["--from-stage", self.from_stage_var.get().strip()])
        if self.to_stage_var.get().strip():
            command.extend(["--to-stage", self.to_stage_var.get().strip()])

        selected_sources = [source for source, var in self.source_vars.items() if var.get()]
        if selected_sources:
            command.append("--sources")
            command.extend(selected_sources)

        command.append("--fail-fast" if self.fail_fast_var.get() else "--no-fail-fast")
        if self.allow_partial_var.get():
            command.append("--allow-partial")
        if self.dry_run_var.get():
            command.append("--dry-run")

        if self.model_runner_var.get().strip():
            command.extend(["--model-runner", self.model_runner_var.get().strip()])
        if self.model_run_id_var.get().strip():
            command.extend(["--model-run-id", self.model_run_id_var.get().strip()])
        for token in self.model_args_var.get().strip().split():
            command.extend(["--model-arg", token])
        return command

    def _set_command_preview(self, command: list[str]) -> None:
        self.command_preview.configure(state=tk.NORMAL)
        self.command_preview.delete("1.0", tk.END)
        self.command_preview.insert("1.0", " ".join(command))
        self.command_preview.configure(state=tk.DISABLED)

    def run_pipeline(self) -> None:
        if self.process and self.process.poll() is None:
            self.output_queue.put("Ya hay una corrida en ejecución.\n")
            return
        command = self._build_command()
        self._set_command_preview(command)
        self.output_queue.put(f"$ {' '.join(command)}\n")

        def worker() -> None:
            self.process = subprocess.Popen(
                command,
                cwd=str(ROOT_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            assert self.process.stdout is not None
            for line in self.process.stdout:
                self.output_queue.put(line)
            self.process.wait()
            self.output_queue.put(f"\n[exit_code={self.process.returncode}]\n")

        threading.Thread(target=worker, daemon=True).start()

    def stop_pipeline(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.output_queue.put("\n[process_terminated]\n")

    def clear_output(self) -> None:
        self.output_text.delete("1.0", tk.END)

    def _drain_output_queue(self) -> None:
        while True:
            try:
                chunk = self.output_queue.get_nowait()
            except queue.Empty:
                break
            self.output_text.insert(tk.END, chunk)
            self.output_text.see(tk.END)
        self.after(200, self._drain_output_queue)


def main() -> None:
    app = RadarPipelineGui()
    app.mainloop()


if __name__ == "__main__":
    main()
