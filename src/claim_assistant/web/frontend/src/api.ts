export type RegistryForm = {
  code: string;
  label: string;
  form_model_path: string;
};

export type RegistrySample = {
  id: string;        // e.g. "FL:FL__form_hw_POL987654321.pdf"
  form_code: string; // e.g. "FL"
  kind: string;      // "handwritten" | "digital" | "unknown"
  filename: string;  // e.g. "form_hw_POL987654321.pdf"
  path: string;
};

export type RegistrySnapshot = {
  forms: RegistryForm[];
  samples: RegistrySample[];
};

export type CoverageAnalysisResponse = {
  executive_summary: string;
  conclusion: "positive" | "negative" | "uncertain";
  confidence: number;
  form: any[];
  policy: any | null;
};



export async function fetchRegistry(): Promise<RegistrySnapshot> {
  const r = await fetch("/api/registry");
  if (!r.ok) throw new Error(`Registry failed: ${r.status}`);
  return r.json();
}

export async function postProcess(formType: string, file: File): Promise<CoverageAnalysisResponse> {
  const fd = new FormData();
  fd.append("form_type", formType);
  fd.append("file", file, file.name);

  const r = await fetch("/api/process", { method: "POST", body: fd });
  if (!r.ok) {
    const msg = await r.text();
    throw new Error(`Process failed: ${r.status} ${msg}`);
  }
  return r.json();
}

export type UploadResponse = {
  run_id: string;
  filename: string;
  pdf_path: string;
};

export async function uploadPdf(file: File): Promise<UploadResponse> {
  const fd = new FormData();
  fd.append("file", file, file.name);

  const r = await fetch("/api/upload", { method: "POST", body: fd });
  if (!r.ok) {
    const msg = await r.text();
    throw new Error(`Upload failed: ${r.status} ${msg}`);
  }
  return r.json();
}

export async function postProcessPath(formType: string, pdfPath: string): Promise<CoverageAnalysisResponse> {
  const r = await fetch("/api/process-path", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ form_type: formType, pdf_path: pdfPath }),
  });

  if (!r.ok) {
    const msg = await r.text();
    throw new Error(`Process failed: ${r.status} ${msg}`);
  }
  return r.json();
}

export async function processUpload(formType: string, file: File): Promise<any> {
  const fd = new FormData();
  fd.append("form_type", formType);
  fd.append("file", file);
  const r = await fetch("/api/process", { method: "POST", body: fd });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function processSample(sampleId: string): Promise<any> {
  const fd = new FormData();
  fd.append("sample_id", sampleId);
  const r = await fetch("/api/process-sample", { method: "POST", body: fd });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export function samplePdfUrl(sampleId: string): string {
  return `/api/samples/${encodeURIComponent(sampleId)}/pdf`;
}
