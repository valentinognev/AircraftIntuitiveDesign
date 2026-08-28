from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from aid_gui.main_window import MainWindow


def format_io_preview(path: Path | str, *, max_lines: int = 20) -> str:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    return "\n".join(lines[:max_lines])


def apply_tornado_state(state: dict, values: dict) -> dict:
    merged = dict(state)
    merged.update(values)
    return merged


class IoPreviewDialog(QDialog):
    def __init__(self, title: str, text: str, parent: "MainWindow | None" = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        editor = QPlainTextEdit(text)
        editor.setReadOnly(True)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout = QVBoxLayout(self)
        layout.addWidget(editor)
        layout.addWidget(buttons)


def show_io_preview(parent: "MainWindow | None", title: str, text: str) -> None:
    IoPreviewDialog(title, text, parent).exec()


def show_io_file_preview(
    parent: "MainWindow | None", title: str, path: Path | str
) -> None:
    show_io_preview(parent, title, format_io_preview(path))


def prompt_tornado_state(parent: "MainWindow | None", state: dict) -> dict | None:
    dlg = QDialog(parent)
    dlg.setWindowTitle("Tornado Inputs")
    form = QFormLayout()
    edits: dict[str, QLineEdit] = {}
    for key in state:
        edit = QLineEdit(str(state[key]))
        form.addRow(str(key), edit)
        edits[key] = edit
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    layout = QVBoxLayout(dlg)
    layout.addLayout(form)
    layout.addWidget(buttons)
    if dlg.exec() != QDialog.DialogCode.Accepted:
        return None
    values = {}
    for key, edit in edits.items():
        text = edit.text().strip()
        if not text:
            continue
        try:
            if any(ch in text for ch in ".eE"):
                values[key] = float(text)
            else:
                values[key] = int(text)
        except ValueError:
            values[key] = text
    return apply_tornado_state(state, values)


def prompt_vlm_mode(parent: "MainWindow | None") -> int:
    box = QMessageBox(parent)
    box.setWindowTitle("VLM Calculation Method")
    box.setText("Analysis Method for 3-D Vortex Wake Calculations")
    freestream = box.addButton(
        "Freestream Following Wake", QMessageBox.ButtonRole.AcceptRole
    )
    fixed = box.addButton("Fixed Wake", QMessageBox.ButtonRole.AcceptRole)
    box.setDefaultButton(freestream)
    box.exec()
    if box.clickedButton() is fixed:
        return 1
    return 0
