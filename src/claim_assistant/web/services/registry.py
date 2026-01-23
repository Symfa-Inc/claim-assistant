from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

SampleKind = Literal["digital", "handwritten", "unknown"]


@dataclass(frozen=True)
class SampleRef:
    id: str
    form_code: str
    kind: str
    filename: str
    path: str


@dataclass(frozen=True)
class FormRef:
    code: str
    label: str
    form_model_path: str


@dataclass(frozen=True)
class RegistrySnapshot:
    forms: list[FormRef]
    samples: list[SampleRef]

    def to_dict(self) -> dict:
        return {
            "forms": [f.__dict__ for f in self.forms],
            "samples": [s.__dict__ for s in self.samples],
        }


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


class ClaimFormsRegistry:
    """
    Discovers available form types (form_model.json) and sample PDFs under:
      PROJECT_DIR/data/forms/<FORM_CODE>/
    """

    def __init__(self, project_dir: Path) -> None:
        self._project_dir = Path(project_dir)
        self._forms_root = self._project_dir / "data" / "forms"

        self._snapshot: RegistrySnapshot | None = None
        self._sample_index: dict[str, SampleRef] = {}

    def snapshot(self, *, refresh: bool = False) -> RegistrySnapshot:
        if self._snapshot is None or refresh:
            snap = self._scan()
            self._snapshot = snap
            self._sample_index = {s.id: s for s in snap.samples}
        return self._snapshot

    def get_sample(self, sample_id: str) -> SampleRef | None:
        """
        Returns a sample by its stable id (e.g. 'FL:FL__form_hw_POL987654321.pdf').
        """
        # Ensure index is ready
        if self._snapshot is None:
            self.snapshot()
        return self._sample_index.get(sample_id)

    # -------------------------
    # internals
    # -------------------------
    def _scan(self) -> RegistrySnapshot:
        forms: list[FormRef] = []
        samples: list[SampleRef] = []

        if not self._forms_root.exists():
            return RegistrySnapshot(forms=forms, samples=samples)

        for form_dir in sorted([p for p in self._forms_root.iterdir() if p.is_dir()]):
            form_code = form_dir.name
            form_model = form_dir / "form_model.json"
            if form_model.exists():
                forms.append(
                    FormRef(
                        code=form_code,
                        label=form_code.upper(),
                        form_model_path=str(form_model),
                    ),
                )

            # samples: any "form_*.pdf" except containing "raw"
            for pdf in sorted(form_dir.glob("form_*.pdf")):
                if "raw" in pdf.name:
                    continue

                kind = self._infer_kind(pdf.name)
                sample_id = f"{form_code}:{form_code}__{pdf.name}"
                samples.append(
                    SampleRef(
                        id=sample_id,
                        form_code=form_code,
                        kind=kind,
                        filename=pdf.name,
                        path=str(pdf),
                    ),
                )

        return RegistrySnapshot(forms=forms, samples=samples)

    @staticmethod
    def _infer_kind(filename: str) -> str:
        # expects "form_{hw|dg}_*.pdf"
        stem = filename[:-4] if filename.lower().endswith(".pdf") else filename
        parts = stem.split("_")
        if len(parts) >= 3:
            t = parts[1].lower()
            if t == "hw":
                return "handwritten"
            if t == "dg":
                return "digital"
        return "unknown"

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
