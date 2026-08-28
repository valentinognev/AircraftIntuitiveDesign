from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from aid.mesh_params import mesh_fields


class MeshDialog(QDialog):
    def __init__(self, ac, solver: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Wing Mesh Parameters")
        self._accepted = False
        prompts, defaults = mesh_fields(ac, solver)
        self._edits: list[QLineEdit] = []

        form = QFormLayout()
        for prompt, default in zip(prompts, defaults, strict=True):
            edit = QLineEdit(default)
            form.addRow(prompt, edit)
            self._edits.append(edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def accept(self) -> None:
        self._accepted = True
        super().accept()

    def reject(self) -> None:
        self._accepted = False
        super().reject()

    def values(self) -> tuple[str, ...] | None:
        if not self._accepted:
            return None
        return tuple(edit.text() for edit in self._edits)
