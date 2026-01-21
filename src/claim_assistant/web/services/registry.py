from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

SampleKind = Literal["digital", "handwritten", "unknown"]


@dataclass(frozen=True)
class FormDescriptor:
    """
    Discovered form type (e.g., state) with a form model JSON path.

    `code` is what the UI/API uses as "form_type".
    """

    code: str
    label: str
    form_model_path: Path


@dataclass(frozen=True)
class SampleDescriptor:
    """
    Discovered sample PDF that can be processed without uploading.

    `id` is a stable identifier used by the UI. In this implementation it is derived
    from relative path to avoid collisions across form codes.
    """

    id: str
    form_code: str
    kind: SampleKind
    filename: str
    path: Path


@dataclass(frozen=True)
class RegistrySnapshot:
    """
    Lightweight data transfer object for the homepage selector.
    """

    forms: list[FormDescriptor]
    samples: list[SampleDescriptor]

    def to_dict(self) -> dict[str, Any]:
        return {
            "forms": [
                {
                    "code": f.code,
                    "label": f.label,
                    "form_model_path": str(f.form_model_path),
                }
                for f in self.forms
            ],
            "samples": [
                {
                    "id": s.id,
                    "form_code": s.form_code,
                    "kind": s.kind,
                    "filename": s.filename,
                    "path": str(s.path),
                }
                for s in self.samples
            ],
        }


class ClaimFormsRegistry:
    """
    Discovers available claim form models and prepared sample PDFs.

    Assumptions (based on your repo structure):
      - Form models live under: <project_dir>/data/forms/<FORM_CODE>/form_model.json
      - Samples are PDFs under: <project_dir>/data/forms/<FORM_CODE>/*.pdf

    Notes:
      - The "digital/handwritten" label is inferred from filename heuristics:
            contains "hw" or "hand" -> handwritten
            contains "digital" or "typed" -> digital
        If no match -> "unknown"
      - This registry is used only for UX / selectors. It does not do any processing.
    """

    def __init__(
        self,
        *,
        project_dir: Path,
        forms_root_rel: Path = Path("data/forms"),
        form_model_filename: str = "form_model.json",
        include_samples: bool = True,
    ) -> None:
        self._project_dir = Path(project_dir)
        self._forms_root = self._project_dir / forms_root_rel
        self._form_model_filename = form_model_filename
        self._include_samples = include_samples

    def snapshot(self) -> RegistrySnapshot:
        forms = self._discover_forms()
        samples = self._discover_samples(forms) if self._include_samples else []
        return RegistrySnapshot(forms=forms, samples=samples)

    # -----------------------------
    # Discovery internals
    # -----------------------------
    def _discover_forms(self) -> list[FormDescriptor]:
        if not self._forms_root.exists():
            return []

        forms: list[FormDescriptor] = []
        for d in sorted(p for p in self._forms_root.iterdir() if p.is_dir()):
            form_code = d.name
            model_path = d / self._form_model_filename
            if not model_path.exists():
                continue

            forms.append(
                FormDescriptor(
                    code=form_code,
                    label=self._make_label(form_code),
                    form_model_path=model_path,
                ),
            )
        return forms

    def _discover_samples(self, forms: list[FormDescriptor]) -> list[SampleDescriptor]:
        samples: list[SampleDescriptor] = []
        form_dirs = {f.code: f.form_model_path.parent for f in forms}

        for code, dir_path in form_dirs.items():
            for pdf in sorted(dir_path.glob("*.pdf")):
                kind = self._infer_sample_kind(pdf.name)
                # Stable-ish id derived from relative path under data/forms
                rel = (
                    pdf.relative_to(self._forms_root)
                    if self._forms_root in pdf.parents
                    else pdf.name
                )
                sample_id = f"{code}:{str(rel).replace('/', '__')}"
                samples.append(
                    SampleDescriptor(
                        id=sample_id,
                        form_code=code,
                        kind=kind,
                        filename=pdf.name,
                        path=pdf,
                    ),
                )
        return samples

    @staticmethod
    def _make_label(code: str) -> str:
        # Keep it minimal; you can plug a mapping later if needed.
        return code.upper()

    @staticmethod
    def _infer_sample_kind(filename: str) -> SampleKind:
        name = filename.lower()
        if "hw" in name or "hand" in name or "handwritten" in name:
            return "handwritten"
        if "digital" in name or "typed" in name:
            return "digital"
        return "unknown"
