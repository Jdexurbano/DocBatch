import math
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from docbatch.validation import MEGABYTE_BYTES, normalize_batch_name
from docbatch.workflow import FIRST_PART_SUFFIX, BatchWorkflow, ProgressEvent

__all__ = [
    "DocBatchApp",
    "folder_name_preview",
    "format_completion_summary",
    "format_progress",
    "format_review_summary",
    "format_size",
    "main",
    "parse_size_limit",
    "progress_maximum",
    "should_clear_inputs",
]

KILOBYTE_BYTES = 1024
READY_BUTTON_BG = "#2e7d32"
READY_BUTTON_FG = "#ffffff"
READY_BUTTON_ACTIVE_BG = "#256628"


def folder_name_preview(batch_name: str) -> str:
    return f"{normalize_batch_name(batch_name)}{FIRST_PART_SUFFIX}"


def format_size(size_bytes: int) -> str:
    if size_bytes < KILOBYTE_BYTES:
        unit = "byte" if size_bytes == 1 else "bytes"
        return f"{size_bytes:,} {unit}"
    if size_bytes < MEGABYTE_BYTES:
        return f"{size_bytes / KILOBYTE_BYTES:.2f} KB ({size_bytes:,} bytes)"
    return f"{size_bytes / MEGABYTE_BYTES:.2f} MB ({size_bytes:,} bytes)"


def parse_size_limit(text: str) -> float:
    message = "Part-size limit must be a number of MB"
    if not isinstance(text, str):
        raise ValueError(message)
    value = text.strip()
    if value.upper().endswith("MB"):
        value = value[:-2].strip()
    try:
        limit = float(value)
    except ValueError:
        raise ValueError(message) from None
    if not math.isfinite(limit):
        raise ValueError(message)
    return limit


def format_review_summary(review) -> str:
    lines = [
        "Review summary",
        "==============",
        f"Source folder: {review.source}",
        f"Destination folder: {review.destination}",
        f"Batch name: {review.batch_name}",
        f"Part-size limit: {format_size(review.max_size_bytes)}",
        f"PDFs: {review.pdf_count}",
        f"Total size: {format_size(review.total_size_bytes)}",
        "",
        "Part folders to create:",
    ]
    lines.extend(f"  {name}" for name in review.part_names)
    if review.oversized_pdf_names:
        lines.extend(
            [
                "",
                "These PDFs exceed the Part-size limit and will be copied as-is "
                "into their own part folder:",
            ]
        )
        lines.extend(f"  {name}" for name in review.oversized_pdf_names)
    if review.overwrite_warning:
        lines.extend(["", f"Overwrite warning: {review.overwrite_warning}"])
    if review.replace_notice:
        lines.extend(["", f"Replace confirmation: {review.replace_notice}"])
    return "\n".join(lines)


def format_completion_summary(result) -> str:
    status = "Cancelled; nothing was written" if result.cancelled else "Completed"
    lines = [
        "Completion summary",
        "==================",
        f"Status: {status}",
        f"Destination folder: {result.destination}",
        f"Part folders generated: {len(result.generated_folders)}",
        f"PDFs copied: {result.copied_pdf_count}",
        f"Excel inventories written: {result.written_inventory_count}",
    ]
    if result.replaced_folders:
        lines.extend(["", "Replaced part folders: " + ", ".join(result.replaced_folders)])
    if result.generated_folders:
        lines.extend(["", "Generated folders:"])
        for folder in result.generated_folders:
            lines.append(
                f"  {folder.name} - {folder.path} - "
                f"{format_size(folder.total_size_bytes)} - {folder.pdf_count} PDF(s)"
            )
            for name in folder.oversized_pdf_names:
                lines.append(f"    Exceeds the Part-size limit: {name}")
    if result.skipped_files:
        lines.extend(["", "Skipped files:"])
        lines.extend(f"  {name}" for name in result.skipped_files)
    if result.errors:
        lines.extend(["", "Errors:"])
        lines.extend(f"  {error}" for error in result.errors)
    if result.errors and not result.cancelled:
        lines.append("")
        lines.append("This run left partial output; review the folders listed above.")
    return "\n".join(lines)


def format_progress(event) -> str:
    if event.total:
        return f"{event.message} ({event.completed}/{event.total})"
    return event.message


def progress_maximum(review) -> int:
    return max(len(review.part_names), 1)


def should_clear_inputs(result) -> bool:
    return result is not None and not result.cancelled


class DocBatchApp:
    def __init__(self):
        self.workflow = BatchWorkflow()
        self.root = tk.Tk()
        self._review = None
        self._completed_result = None
        self._events = queue.Queue()
        self._polling = False
        self._suppress_input_events = False

        self.root.title("DocBatch")
        self.root.minsize(720, 680)

        self.source_var = tk.StringVar()
        self.destination_var = tk.StringVar()
        self.batch_name_var = tk.StringVar()
        self.size_limit_var = tk.StringVar(value="25")
        self.preview_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Choose a Source folder to begin.")

        self._build_form()
        for variable in (
            self.source_var,
            self.destination_var,
            self.batch_name_var,
            self.size_limit_var,
        ):
            variable.trace_add("write", lambda *_: self._on_input_changed())

        self._update_preview()

    def _build_form(self):
        frame = ttk.Frame(self.root, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Source folder:").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(frame, textvariable=self.source_var, state="readonly").grid(
            row=0, column=1, sticky="ew", pady=3
        )
        ttk.Button(frame, text="Browse...", command=self._browse_source).grid(
            row=0, column=2, padx=(6, 0), pady=3
        )

        ttk.Label(frame, text="Destination folder:").grid(
            row=1, column=0, sticky="w", pady=3
        )
        ttk.Entry(frame, textvariable=self.destination_var, state="readonly").grid(
            row=1, column=1, sticky="ew", pady=3
        )
        ttk.Button(frame, text="Browse...", command=self._browse_destination).grid(
            row=1, column=2, padx=(6, 0), pady=3
        )

        ttk.Label(frame, text="Batch name:").grid(row=2, column=0, sticky="w", pady=3)
        ttk.Entry(frame, textvariable=self.batch_name_var).grid(
            row=2, column=1, columnspan=2, sticky="ew", pady=3
        )

        ttk.Label(frame, text="Part-size limit (MB):").grid(
            row=3, column=0, sticky="w", pady=3
        )
        ttk.Entry(frame, textvariable=self.size_limit_var, width=10).grid(
            row=3, column=1, sticky="w", pady=3
        )

        ttk.Label(frame, textvariable=self.preview_var, foreground="#334155").grid(
            row=4, column=0, columnspan=3, sticky="w", pady=(6, 10)
        )

        ttk.Button(frame, text="Review summary", command=self._review_batch).grid(
            row=5, column=0, columnspan=3, sticky="ew", pady=3
        )

        ttk.Label(frame, text="Review summary:").grid(
            row=6, column=0, columnspan=3, sticky="w"
        )
        self.review_text = ScrolledText(frame, height=11, state="disabled", wrap="word")
        self.review_text.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=(3, 8))
        frame.rowconfigure(7, weight=1)

        self.replace_var = tk.BooleanVar(value=False)
        self.replace_check = ttk.Checkbutton(
            frame,
            text="Replace conflicting Part folders",
            variable=self.replace_var,
            state="disabled",
        )
        self.replace_check.grid(row=8, column=0, columnspan=3, sticky="w", pady=3)

        self.process_button = tk.Button(
            frame, text="Process files", command=self._confirm_and_process, state="disabled"
        )
        self._process_default_colors = tuple(
            self.process_button.cget(option)
            for option in ("bg", "fg", "activebackground")
        )
        self.process_button.grid(row=9, column=0, columnspan=3, sticky="ew", pady=3)

        self.progress_bar = ttk.Progressbar(frame, mode="determinate", maximum=1, value=0)
        self.progress_bar.grid(row=10, column=0, columnspan=3, sticky="ew", pady=3)
        ttk.Label(frame, textvariable=self.status_var).grid(
            row=11, column=0, columnspan=3, sticky="w"
        )

        ttk.Label(frame, text="Completion summary:").grid(
            row=12, column=0, columnspan=3, sticky="w", pady=(10, 0)
        )
        self.completion_text = ScrolledText(frame, height=11, state="disabled", wrap="word")
        self.completion_text.grid(row=13, column=0, columnspan=3, sticky="nsew", pady=(3, 8))
        frame.rowconfigure(13, weight=1)

        self.open_button = ttk.Button(
            frame,
            text="Open destination folder",
            command=self._open_destination,
            state="disabled",
        )
        self.open_button.grid(row=14, column=0, columnspan=3, sticky="ew", pady=3)

    @staticmethod
    def _set_text(widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _set_process_ready(self, ready):
        if ready:
            self.process_button.configure(
                state="normal",
                bg=READY_BUTTON_BG,
                fg=READY_BUTTON_FG,
                activebackground=READY_BUTTON_ACTIVE_BG,
            )
            return
        default_bg, default_fg, default_active_bg = self._process_default_colors
        self.process_button.configure(
            state="disabled",
            bg=default_bg,
            fg=default_fg,
            activebackground=default_active_bg,
        )

    def _clear_batch_fields(self):
        self._suppress_input_events = True
        try:
            self.source_var.set("")
            self.destination_var.set("")
            self.batch_name_var.set("")
        finally:
            self._suppress_input_events = False
        self._update_preview()

    def _update_preview(self):
        batch_name = self.batch_name_var.get()
        self.preview_var.set(
            f"First part folder: {folder_name_preview(batch_name)}"
            if batch_name.strip()
            else f"First part folder: <ENTER BATCH NAME>{FIRST_PART_SUFFIX}"
        )

    def _on_input_changed(self):
        if self._suppress_input_events:
            return
        self._review = None
        self.replace_var.set(False)
        self.replace_check.configure(state="disabled")
        self._set_process_ready(False)
        self.open_button.configure(state="disabled")
        self._set_text(self.review_text, "")
        self._set_text(self.completion_text, "")
        self._update_preview()

    def _browse_source(self):
        selected = filedialog.askdirectory(title="Select Source folder")
        if selected:
            self.source_var.set(selected)

    def _browse_destination(self):
        selected = filedialog.askdirectory(title="Select Destination folder")
        if selected:
            self.destination_var.set(selected)

    def _review_batch(self):
        try:
            limit = parse_size_limit(self.size_limit_var.get())
            review = self.workflow.review(
                self.source_var.get(),
                self.destination_var.get(),
                self.batch_name_var.get(),
                limit,
            )
        except ValueError as exc:
            messagebox.showerror("Check the Part-size limit", str(exc))
            return
        if not review.is_valid:
            messagebox.showerror("Check the batch details", "\n".join(review.errors))
            return

        self._review = review
        self._set_text(self.review_text, format_review_summary(review))
        self.replace_var.set(False)
        self.replace_check.configure(state="normal" if review.has_conflicts else "disabled")
        self._set_process_ready(True)
        self.open_button.configure(state="disabled")
        self.progress_bar.configure(maximum=progress_maximum(review), value=0)
        self.status_var.set("Review the summary, then select Process files.")

    def _confirm_and_process(self):
        if self._review is None:
            return
        review = self._review
        replace = self.replace_var.get() and review.has_conflicts
        self._set_process_ready(False)
        self.progress_bar.configure(value=0)
        self.status_var.set("Processing started...")
        self._completed_result = None
        threading.Thread(
            target=self._run_worker,
            args=(review, replace),
            daemon=True,
        ).start()
        self._polling = True
        self.root.after(100, self._poll_events)

    def _run_worker(self, review, replace):
        try:
            self._completed_result = self.workflow.run(
                review,
                approved=True,
                replace_existing=replace,
                progress=self._events.put,
            )
        except Exception as exc:
            self._events.put(ProgressEvent("error", str(exc), 0, 0))
        finally:
            self._events.put(None)

    def _poll_events(self):
        finished = False
        while True:
            try:
                event = self._events.get_nowait()
            except queue.Empty:
                break
            if event is None:
                finished = True
                break
            self.status_var.set(format_progress(event))
            if event.stage == "error":
                messagebox.showerror("Processing failed", event.message)
            if event.total:
                self.progress_bar.configure(value=event.completed)

        if finished:
            self._polling = False
            self._show_completion()
            return
        if self._polling:
            self.root.after(100, self._poll_events)

    def _show_completion(self):
        result = self._completed_result
        if result is not None:
            self._set_text(self.completion_text, format_completion_summary(result))
            self.open_button.configure(state="normal")
            if should_clear_inputs(result):
                self._clear_batch_fields()
                self.progress_bar.configure(value=self.progress_bar.cget("maximum"))
            else:
                self.progress_bar.configure(value=0)
        self.replace_var.set(False)
        self.replace_check.configure(state="disabled")
        self._review = None
        self._set_process_ready(False)
        self.status_var.set("Processing finished.")

    def _open_destination(self):
        destination = self._completed_result.destination if self._completed_result else None
        if destination is None:
            return
        if hasattr(os, "startfile"):
            os.startfile(destination)
        else:
            messagebox.showinfo("Destination folder", str(destination))


def main():
    app = DocBatchApp()
    app.root.mainloop()


if __name__ == "__main__":
    main()
