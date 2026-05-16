from __future__ import annotations

import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from .config import ALLOWED_MODES, DEFAULT_MODEL_RUNNER, DEFAULT_SOURCES, MODELING_PYTHON, OPS_PYTHON, SOURCE_NAMES, STAGE_NAMES


ROOT_DIR = Path(__file__).resolve().parents[2]
POST_W10_LAYER_PRESET = "Operación mínima post-W10"
POST_W10_LAYER_KIND = "__post_w10__"
POST_W10_OPERATION_PROFILE = "post_w10_controlled"
POST_W10_DEFAULT_FROM_WEEK = "2026-W11"

STAGE_LABELS = {
    "preflight": "Preflight",
    "extraction": "Extractors",
    "preprocessing": "Preprocessing",
    "nlp": "NLP",
    "modeling": "Modeling",
    "export": "Export",
    "report": "Reporting",
}
LABEL_TO_STAGE = {label: stage for stage, label in STAGE_LABELS.items()}
STAGE_DISPLAY_VALUES = tuple(STAGE_LABELS[stage] for stage in STAGE_NAMES)
POST_W10_STAGE_LABELS = (
    STAGE_LABELS["extraction"],
    STAGE_LABELS["preprocessing"],
    STAGE_LABELS["nlp"],
    STAGE_LABELS["modeling"],
)
LAYER_PRESETS = {
    "Pipeline completo": ("preflight", "report"),
    "Extractors": ("extraction", "extraction"),
    "Preprocessing": ("preprocessing", "preprocessing"),
    "NLP": ("nlp", "nlp"),
    "Modeling": ("modeling", "modeling"),
    "Export": ("export", "export"),
    "Reporting": ("report", "report"),
    POST_W10_LAYER_PRESET: POST_W10_LAYER_KIND,
    "Rango personalizado": None,
}


class RadarPipelineGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Radar Pipeline Control")
        self.geometry("1220x860")
        self.minsize(1080, 760)
        self.output_queue: queue.Queue[str] = queue.Queue()
        self.process: subprocess.Popen[str] | None = None

        self.layer_var = tk.StringVar(value="Pipeline completo")
        self.week_var = tk.StringVar()
        self.date_from_var = tk.StringVar()
        self.date_to_var = tk.StringVar()
        self.resume_var = tk.StringVar()
        self.mode_var = tk.StringVar(value=ALLOWED_MODES[0])
        self.post_w10_from_week_var = tk.StringVar(value=POST_W10_DEFAULT_FROM_WEEK)
        self.post_w10_to_week_var = tk.StringVar()
        self.post_w10_operation_id_var = tk.StringVar()
        self.post_w10_comment_var = tk.StringVar()
        self.post_w10_modeling_python_var = tk.StringVar(value=MODELING_PYTHON)
        self.from_stage_var = tk.StringVar(value=STAGE_LABELS["preflight"])
        self.to_stage_var = tk.StringVar(value=STAGE_LABELS["report"])
        self.model_runner_var = tk.StringVar(value=DEFAULT_MODEL_RUNNER)
        self.model_run_id_var = tk.StringVar()
        self.model_args_var = tk.StringVar()
        self.fail_fast_var = tk.BooleanVar(value=True)
        self.allow_partial_var = tk.BooleanVar(value=False)
        self.dry_run_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(
            value="Selecciona una capa u operación. La operación mínima post-W10 usa E1_v5_clean y E9_v2_clean sin tocar src/modeling."
        )
        self.source_vars = {source: tk.BooleanVar(value=source in DEFAULT_SOURCES) for source in SOURCE_NAMES}
        self.stage_selection_vars = {stage: tk.BooleanVar(value=stage in ("preflight", "extraction", "preprocessing", "nlp", "modeling", "export", "report")) for stage in STAGE_NAMES}

        self.source_checkbuttons: list[ttk.Checkbutton] = []
        self.stage_widgets: list[ttk.Widget] = []
        self.stage_checkbuttons: list[ttk.Checkbutton] = []
        self.date_widgets: list[ttk.Widget] = []
        self.model_widgets: list[ttk.Widget] = []
        self.post_w10_widgets: list[ttk.Widget] = []
        self.resume_widget: ttk.Widget | None = None
        self.mode_widget: ttk.Widget | None = None

        self._build_widgets()
        self._bind_traces()
        self._refresh_ui()
        self.after(200, self._drain_output_queue)

    def _build_widgets(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)

        scope_frame = ttk.LabelFrame(root, text="Alcance operativo", padding=10)
        scope_frame.pack(fill=tk.X, pady=(0, 10))
        scope_frame.columnconfigure(1, weight=1)
        scope_frame.columnconfigure(3, weight=1)

        layer_combo = self._add_combo(
            scope_frame,
            "Capa / operación",
            self.layer_var,
            tuple(LAYER_PRESETS.keys()),
            row=0,
            column=0,
            hint="Preset rápido por capa",
            readonly=True,
        )
        mode_combo = self._add_combo(
            scope_frame,
            "Mode",
            self.mode_var,
            ALLOWED_MODES,
            row=0,
            column=2,
            hint="controlled o experimental",
            readonly=True,
        )
        self.mode_widget = mode_combo

        week_entry = self._add_entry(
            scope_frame,
            "Week",
            self.week_var,
            row=1,
            column=0,
            hint="2026-W14 o 2026-03-31",
        )
        resume_entry = self._add_entry(
            scope_frame,
            "Resume Run ID",
            self.resume_var,
            row=1,
            column=2,
            hint="radar_2026W14_001",
        )
        self.resume_widget = resume_entry
        date_from_entry = self._add_entry(
            scope_frame,
            "Date From",
            self.date_from_var,
            row=2,
            column=0,
            hint="YYYY-MM-DD",
        )
        date_to_entry = self._add_entry(
            scope_frame,
            "Date To",
            self.date_to_var,
            row=2,
            column=2,
            hint="YYYY-MM-DD",
        )
        self.date_widgets.extend([week_entry, date_from_entry, date_to_entry])
        self.stage_widgets.extend([layer_combo, mode_combo, resume_entry])

        stages_frame = ttk.LabelFrame(root, text="Rango de etapas", padding=10)
        stages_frame.pack(fill=tk.X, pady=(0, 10))
        stages_frame.columnconfigure(1, weight=1)
        stages_frame.columnconfigure(3, weight=1)
        from_combo = self._add_combo(
            stages_frame,
            "From Stage",
            self.from_stage_var,
            STAGE_DISPLAY_VALUES,
            row=0,
            column=0,
            hint="Inicio efectivo del pipeline",
        )
        to_combo = self._add_combo(
            stages_frame,
            "To Stage",
            self.to_stage_var,
            STAGE_DISPLAY_VALUES,
            row=0,
            column=2,
            hint="Reporting corresponde a la etapa report",
        )
        self.stage_widgets.extend([from_combo, to_combo])

        stages_row = ttk.Frame(stages_frame)
        stages_row.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        ttk.Label(stages_row, text="Etapas específicas").pack(side=tk.LEFT, padx=(0, 12))
        for stage_name in STAGE_NAMES:
            check = ttk.Checkbutton(
                stages_row,
                text=STAGE_LABELS[stage_name],
                variable=self.stage_selection_vars[stage_name],
            )
            check.pack(side=tk.LEFT, padx=(0, 12))
            self.stage_checkbuttons.append(check)

        sources_frame = ttk.LabelFrame(root, text="Fuentes y filtros de capa", padding=10)
        sources_frame.pack(fill=tk.X, pady=(0, 10))
        header = ttk.Frame(sources_frame)
        header.pack(fill=tk.X)
        ttk.Label(
            header,
            text="Aplica a extractors, preprocessing y NLP. Si usas fechas, deben caer en una sola semana canónica por corrida.",
        ).pack(side=tk.LEFT)
        ttk.Button(header, text="Todas", command=self._select_all_sources, width=10).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(header, text="Ninguna", command=self._clear_all_sources, width=10).pack(side=tk.RIGHT)

        sources_row = ttk.Frame(sources_frame)
        sources_row.pack(fill=tk.X, pady=(8, 0))
        for source in SOURCE_NAMES:
            check = ttk.Checkbutton(sources_row, text=source, variable=self.source_vars[source])
            check.pack(side=tk.LEFT, padx=(0, 18))
            self.source_checkbuttons.append(check)

        model_frame = ttk.LabelFrame(root, text="Modelado", padding=10)
        model_frame.pack(fill=tk.X, pady=(0, 10))
        model_frame.columnconfigure(1, weight=1)
        model_frame.columnconfigure(3, weight=1)
        model_runner_entry = self._add_entry(
            model_frame,
            "Model Runner",
            self.model_runner_var,
            row=0,
            column=0,
            hint="controlled: E10 (integra E1_v5_clean + E9_v2_clean)",
        )
        model_run_id_entry = self._add_entry(
            model_frame,
            "Model Run ID",
            self.model_run_id_var,
            row=0,
            column=2,
            hint="opcional",
        )
        model_args_entry = self._add_entry(
            model_frame,
            "Model Args",
            self.model_args_var,
            row=1,
            column=0,
            hint="--horizons=1 --lags=1,2,3,4",
            columnspan=3,
        )
        self.model_widgets.extend([model_runner_entry, model_run_id_entry, model_args_entry])

        post_w10_frame = ttk.LabelFrame(root, text="Operación mínima post-W10", padding=10)
        post_w10_frame.pack(fill=tk.X, pady=(0, 10))
        post_w10_frame.columnconfigure(1, weight=1)
        post_w10_frame.columnconfigure(3, weight=1)
        post_w10_from_entry = self._add_entry(
            post_w10_frame,
            "From Week",
            self.post_w10_from_week_var,
            row=0,
            column=0,
            hint="Default: 2026-W11",
        )
        post_w10_to_entry = self._add_entry(
            post_w10_frame,
            "To Week",
            self.post_w10_to_week_var,
            row=0,
            column=2,
            hint="Vacío = última semana común",
        )
        post_w10_operation_id_entry = self._add_entry(
            post_w10_frame,
            "Operation ID",
            self.post_w10_operation_id_var,
            row=1,
            column=0,
            hint="opcional",
        )
        post_w10_modeling_python_entry = self._add_entry(
            post_w10_frame,
            "Modeling Python",
            self.post_w10_modeling_python_var,
            row=1,
            column=2,
            hint="Override opcional del entorno de modelado",
        )
        post_w10_comment_entry = self._add_entry(
            post_w10_frame,
            "Comment",
            self.post_w10_comment_var,
            row=2,
            column=0,
            hint="Comentario para el registro de emisiones",
            columnspan=3,
        )
        self.post_w10_widgets.extend(
            [
                post_w10_from_entry,
                post_w10_to_entry,
                post_w10_operation_id_entry,
                post_w10_modeling_python_entry,
                post_w10_comment_entry,
            ]
        )

        execution_frame = ttk.Frame(root)
        execution_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Checkbutton(execution_frame, text="Fail Fast", variable=self.fail_fast_var).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Checkbutton(execution_frame, text="Allow Partial", variable=self.allow_partial_var).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Checkbutton(execution_frame, text="Dry Run", variable=self.dry_run_var).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Button(execution_frame, text="Run", command=self.run_pipeline, width=12).pack(side=tk.RIGHT)
        ttk.Button(execution_frame, text="Stop", command=self.stop_pipeline, width=12).pack(side=tk.RIGHT, padx=(0, 8))
        ttk.Button(execution_frame, text="Clear Output", command=self.clear_output, width=12).pack(side=tk.RIGHT, padx=(0, 8))

        status_label = ttk.Label(root, textvariable=self.status_var, foreground="#34495e")
        status_label.pack(fill=tk.X, pady=(0, 8))

        preview_frame = ttk.LabelFrame(root, text="Command preview", padding=8)
        preview_frame.pack(fill=tk.X, pady=(0, 8))
        self.command_preview = tk.Text(preview_frame, height=4, wrap="word")
        self.command_preview.pack(fill=tk.X)
        self.command_preview.insert("1.0", "Aquí se mostrará el comando a ejecutar.")
        self.command_preview.configure(state=tk.DISABLED)

        output_frame = ttk.LabelFrame(root, text="Salida", padding=8)
        output_frame.pack(fill=tk.BOTH, expand=True)
        self.output_text = tk.Text(output_frame, wrap="word")
        self.output_text.pack(fill=tk.BOTH, expand=True)

    def _bind_traces(self) -> None:
        tracked_vars = [
            self.layer_var,
            self.week_var,
            self.date_from_var,
            self.date_to_var,
            self.resume_var,
            self.mode_var,
            self.post_w10_from_week_var,
            self.post_w10_to_week_var,
            self.post_w10_operation_id_var,
            self.post_w10_comment_var,
            self.post_w10_modeling_python_var,
            self.from_stage_var,
            self.to_stage_var,
            self.model_runner_var,
            self.model_run_id_var,
            self.model_args_var,
            self.fail_fast_var,
            self.allow_partial_var,
            self.dry_run_var,
        ]
        tracked_vars.extend(self.source_vars.values())
        tracked_vars.extend(self.stage_selection_vars.values())
        for variable in tracked_vars:
            variable.trace_add("write", self._on_form_changed)

    def _add_entry(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.StringVar,
        *,
        row: int,
        column: int,
        hint: str,
        columnspan: int = 1,
    ) -> ttk.Entry:
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", padx=(0, 6), pady=4)
        entry = ttk.Entry(parent, textvariable=variable, width=42)
        entry.grid(row=row, column=column + 1, columnspan=columnspan, sticky="ew", pady=4)
        ttk.Label(parent, text=hint, foreground="#58606a").grid(
            row=row,
            column=column + 2 + columnspan - 1,
            sticky="w",
            padx=(12, 0),
            pady=4,
        )
        return entry

    def _add_combo(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.StringVar,
        values: tuple[str, ...] | list[str],
        *,
        row: int,
        column: int,
        hint: str,
        readonly: bool = False,
    ) -> ttk.Combobox:
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", padx=(0, 6), pady=4)
        combo = ttk.Combobox(
            parent,
            textvariable=variable,
            values=values,
            state="readonly" if readonly else "normal",
            width=34,
        )
        combo.grid(row=row, column=column + 1, sticky="ew", pady=4)
        ttk.Label(parent, text=hint, foreground="#58606a").grid(
            row=row,
            column=column + 2,
            sticky="w",
            padx=(12, 0),
            pady=4,
        )
        return combo

    def _select_all_sources(self) -> None:
        for variable in self.source_vars.values():
            variable.set(True)

    def _clear_all_sources(self) -> None:
        for variable in self.source_vars.values():
            variable.set(False)

    def _on_form_changed(self, *args: object) -> None:
        self._refresh_ui()

    def _effective_stage_bounds(self) -> tuple[str, str]:
        selected = self._selected_stage_names()
        return selected[0], selected[-1]

    def _is_post_w10_operation(self) -> bool:
        return LAYER_PRESETS.get(self.layer_var.get()) == POST_W10_LAYER_KIND

    def _selected_stage_names(self) -> list[str]:
        preset = LAYER_PRESETS.get(self.layer_var.get())
        if isinstance(preset, tuple):
            from_stage, to_stage = preset
            from_idx = STAGE_NAMES.index(from_stage)
            to_idx = STAGE_NAMES.index(to_stage)
            return list(STAGE_NAMES[from_idx : to_idx + 1])
        if preset == POST_W10_LAYER_KIND:
            return []
        return [stage for stage in STAGE_NAMES if self.stage_selection_vars[stage].get()]

    def _stage_range_includes(self, stage_name: str) -> bool:
        return stage_name in self._selected_stage_names()

    def _refresh_ui(self) -> None:
        preset = LAYER_PRESETS.get(self.layer_var.get())
        post_w10_mode = preset == POST_W10_LAYER_KIND
        custom_mode = preset is None
        if isinstance(preset, tuple):
            from_label = STAGE_LABELS[preset[0]]
            to_label = STAGE_LABELS[preset[1]]
            if self.from_stage_var.get() != from_label:
                self.from_stage_var.set(from_label)
            if self.to_stage_var.get() != to_label:
                self.to_stage_var.set(to_label)
            selected = set(self._selected_stage_names())
            for stage_name, variable in self.stage_selection_vars.items():
                if variable.get() != (stage_name in selected):
                    variable.set(stage_name in selected)
        elif post_w10_mode:
            if self.mode_var.get() != ALLOWED_MODES[0]:
                self.mode_var.set(ALLOWED_MODES[0])

        stage_state = "readonly" if (custom_mode or post_w10_mode) else "disabled"
        for widget in self.stage_widgets[-2:]:
            widget.configure(state=stage_state)
        for widget in self.stage_checkbuttons:
            widget.configure(state="normal" if custom_mode else "disabled")
        if self.resume_widget is not None:
            self.resume_widget.configure(state="disabled" if post_w10_mode else "normal")
        if self.mode_widget is not None:
            self.mode_widget.configure(state="disabled" if post_w10_mode else "readonly")
        if post_w10_mode:
            if self.from_stage_var.get() not in POST_W10_STAGE_LABELS:
                self.from_stage_var.set(STAGE_LABELS["extraction"])
            if self.to_stage_var.get() not in POST_W10_STAGE_LABELS:
                self.to_stage_var.set(STAGE_LABELS["modeling"])

        selection_relevant = (not post_w10_mode) and any(
            self._stage_range_includes(stage) for stage in ("extraction", "preprocessing", "nlp")
        )
        model_relevant = (not post_w10_mode) and self._stage_range_includes("modeling")

        for widget in self.date_widgets:
            widget.configure(state="normal" if selection_relevant else "disabled")
        for widget in self.source_checkbuttons:
            widget.configure(state="normal" if (selection_relevant or post_w10_mode) else "disabled")
        for widget in self.model_widgets:
            widget.configure(state="normal" if model_relevant else "disabled")
        for widget in self.post_w10_widgets:
            widget.configure(state="normal" if post_w10_mode else "disabled")

        if post_w10_mode:
            self.status_var.set(
                "Operación post-W10 integrada. Usa From/To Stage para elegir el tramo entre extraction y modeling; si llega a modeling, ejecuta refresh congelado de E1/E9 y registro de emisiones."
            )
        elif selection_relevant:
            self.status_var.set(
                "Fuentes y fechas activas. Usa Week para una semana completa o Date From/Date To para una ventana más precisa dentro de esa semana."
            )
        elif model_relevant:
            self.status_var.set(
                "Capa de modelado activa. En controlled se usa E10 canónico (dualidad E1_v5_clean + E9_v2_clean), no E9 stacking principal."
            )
        elif self._stage_range_includes("report"):
            self.status_var.set(
                "Reporting visible como capa explícita. Hoy sigue consumiendo published/report_inputs y puede quedar como stubbed."
            )
        else:
            self.status_var.set("Operación por capa lista.")

        self._set_command_preview(self._build_command())

    def _build_command(self) -> list[str]:
        command = [OPS_PYTHON, "-u", "-m", "src.operations.run_radar_pipeline"]
        if self._is_post_w10_operation():
            command.extend(["--operation-profile", POST_W10_OPERATION_PROFILE, "--mode", ALLOWED_MODES[0]])
            from_stage = LABEL_TO_STAGE[self.from_stage_var.get()]
            to_stage = LABEL_TO_STAGE[self.to_stage_var.get()]
            from_week = self.post_w10_from_week_var.get().strip()
            to_week = self.post_w10_to_week_var.get().strip()
            operation_id = self.post_w10_operation_id_var.get().strip()
            operation_comment = self.post_w10_comment_var.get().strip()
            modeling_python = self.post_w10_modeling_python_var.get().strip()
            command.extend(["--from-stage", from_stage, "--to-stage", to_stage])
            if from_week:
                command.extend(["--operation-from-week", from_week])
            if to_week:
                command.extend(["--operation-to-week", to_week])
            if operation_id:
                command.extend(["--operation-id", operation_id])
            if operation_comment:
                command.extend(["--operation-comment", operation_comment])
            if modeling_python:
                command.extend(["--operation-modeling-python", modeling_python])
            selected_sources = [source for source, var in self.source_vars.items() if var.get()]
            if selected_sources:
                command.append("--sources")
                command.extend(selected_sources)
            command.append("--fail-fast" if self.fail_fast_var.get() else "--no-fail-fast")
            if self.dry_run_var.get():
                command.append("--dry-run")
            return command

        week_value = self.week_var.get().strip()
        if week_value:
            command.extend(["--week", week_value])

        date_from = self.date_from_var.get().strip()
        date_to = self.date_to_var.get().strip()
        if date_from:
            command.extend(["--date-from", date_from])
        if date_to:
            command.extend(["--date-to", date_to])

        resume_value = self.resume_var.get().strip()
        if resume_value:
            command.extend(["--resume-run-id", resume_value])

        command.extend(["--mode", self.mode_var.get().strip()])

        if LAYER_PRESETS.get(self.layer_var.get()) is None:
            selected_stages = self._selected_stage_names()
            if selected_stages:
                command.append("--stages")
                command.extend(selected_stages)
        else:
            from_stage, to_stage = self._effective_stage_bounds()
            command.extend(["--from-stage", from_stage, "--to-stage", to_stage])

        if any(self._stage_range_includes(stage) for stage in ("extraction", "preprocessing", "nlp")):
            selected_sources = [source for source, var in self.source_vars.items() if var.get()]
            if selected_sources:
                command.append("--sources")
                command.extend(selected_sources)

        command.append("--fail-fast" if self.fail_fast_var.get() else "--no-fail-fast")
        if self.allow_partial_var.get():
            command.append("--allow-partial")
        if self.dry_run_var.get():
            command.append("--dry-run")

        if self._stage_range_includes("modeling"):
            runner = self.model_runner_var.get().strip()
            if runner:
                command.extend(["--model-runner", runner])
            run_id = self.model_run_id_var.get().strip()
            if run_id:
                command.extend(["--model-run-id", run_id])
            for token in self.model_args_var.get().strip().split():
                command.extend(["--model-arg", token])

        return command

    def _set_command_preview(self, command: list[str]) -> None:
        self.command_preview.configure(state=tk.NORMAL)
        self.command_preview.delete("1.0", tk.END)
        self.command_preview.insert("1.0", " ".join(command))
        self.command_preview.configure(state=tk.DISABLED)

    def _validate_form(self) -> bool:
        if self._is_post_w10_operation():
            selected_sources = [source for source, var in self.source_vars.items() if var.get()]
            if not selected_sources:
                messagebox.showerror(
                    "Radar Pipeline Control",
                    "Selecciona al menos una fuente para la operación mínima post-W10.",
                )
                return False
            from_stage = LABEL_TO_STAGE[self.from_stage_var.get()]
            to_stage = LABEL_TO_STAGE[self.to_stage_var.get()]
            allowed = ("extraction", "preprocessing", "nlp", "modeling")
            if from_stage not in allowed or to_stage not in allowed:
                messagebox.showerror(
                    "Radar Pipeline Control",
                    "La operación mínima post-W10 solo soporta etapas entre Extractors y Modeling.",
                )
                return False
            if allowed.index(from_stage) > allowed.index(to_stage):
                messagebox.showerror(
                    "Radar Pipeline Control",
                    "From Stage no puede quedar después de To Stage en la operación mínima post-W10.",
                )
                return False
            return True

        resume_value = self.resume_var.get().strip()
        week_value = self.week_var.get().strip()
        date_from = self.date_from_var.get().strip()
        date_to = self.date_to_var.get().strip()
        selection_relevant = any(self._stage_range_includes(stage) for stage in ("extraction", "preprocessing", "nlp"))

        if not resume_value and not week_value and not (date_from and date_to):
            messagebox.showerror(
                "Radar Pipeline Control",
                "Debes indicar Week o bien Date From / Date To cuando no usas Resume Run ID.",
            )
            return False

        if (date_from and not date_to) or (date_to and not date_from):
            messagebox.showerror(
                "Radar Pipeline Control",
                "Date From y Date To deben proporcionarse juntos.",
            )
            return False

        if LAYER_PRESETS.get(self.layer_var.get()) is None:
            selected_stages = self._selected_stage_names()
            if not selected_stages:
                messagebox.showerror(
                    "Radar Pipeline Control",
                    "Selecciona al menos una etapa cuando usas Rango personalizado.",
                )
                return False
        else:
            from_stage, to_stage = self._effective_stage_bounds()
            if STAGE_NAMES.index(from_stage) > STAGE_NAMES.index(to_stage):
                messagebox.showerror(
                    "Radar Pipeline Control",
                    "From Stage no puede quedar después de To Stage.",
                )
                return False

        if selection_relevant:
            selected_sources = [source for source, var in self.source_vars.items() if var.get()]
            if not selected_sources:
                messagebox.showerror(
                    "Radar Pipeline Control",
                    "Selecciona al menos una fuente cuando operas extractors, preprocessing o NLP.",
                )
                return False

        if self._stage_range_includes("modeling") and not self.model_runner_var.get().strip():
            messagebox.showerror(
                "Radar Pipeline Control",
                "Model Runner no puede quedar vacío cuando la ejecución incluye modeling.",
            )
            return False
        return True

    def run_pipeline(self) -> None:
        if self.process and self.process.poll() is None:
            self.output_queue.put("Ya hay una corrida en ejecución.\n")
            return
        if not self._validate_form():
            return

        command = self._build_command()
        self._set_command_preview(command)
        self.output_queue.put(f"$ {' '.join(command)}\n")

        def worker() -> None:
            try:
                self.process = subprocess.Popen(
                    command,
                    cwd=str(ROOT_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env={**__import__("os").environ, "PYTHONUNBUFFERED": "1"},
                )
                assert self.process.stdout is not None
                for line in self.process.stdout:
                    self.output_queue.put(line)
                self.process.wait()
                self.output_queue.put(f"\n[exit_code={self.process.returncode}]\n")
            except Exception as exc:
                self.output_queue.put(f"\n[gui_worker_error={exc}]\n")
            finally:
                self.process = None

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
