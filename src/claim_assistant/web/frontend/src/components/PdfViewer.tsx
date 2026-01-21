import { useEffect, useMemo, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";

// Configure PDF.js worker using CDN (works in both dev and production)
pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

type BoundingRegion = {
  page: number;                 // 1-based
  polygon: number[];            // [x1,y1,x2,y2,x3,y3,x4,y4]
};

type Props = {
  pdfUrl: string;
  highlight?: BoundingRegion | null;
  height?: number;              // viewer height px
};

// If your DI polygon is already normalized [0..1], set this to true.
// If it’s in PDF points/pixels, set false and we’ll need page dims conversion.
// From your earlier code it looks normalized-ish; keep true unless you confirm otherwise.
const POLYGON_IS_NORMALIZED = true;

function polygonToRect(polygon: number[]) {
  const xs = [polygon[0], polygon[2], polygon[4], polygon[6]];
  const ys = [polygon[1], polygon[3], polygon[5], polygon[7]];
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  return { minX, minY, maxX, maxY };
}

export function PdfViewer({ pdfUrl, highlight, height = 720 }: Props) {
  const [numPages, setNumPages] = useState<number>(0);
  const [loadError, setLoadError] = useState<string | null>(null);

  const activePage = highlight?.page ?? 1;

  // We render only one page (activePage) for simplicity. If you want all pages later, we can.
  const pageNumber = Math.min(Math.max(activePage, 1), Math.max(numPages || 1, 1));

  const rect = useMemo(() => {
    if (!highlight?.polygon || highlight.polygon.length !== 8) return null;
    return polygonToRect(highlight.polygon);
  }, [highlight]);

  // overlay style: we need to map DI coords to rendered page coords.
  // For normalized coords we can scale by container size.
  function overlayStyle(containerW: number, containerH: number) {
    if (!rect) return null;

    if (!POLYGON_IS_NORMALIZED) {
      // Placeholder. Needs conversion using PDF page viewport.
      return null;
    }

    const left = rect.minX * containerW;
    const top = rect.minY * containerH;
    const width = (rect.maxX - rect.minX) * containerW;
    const height = (rect.maxY - rect.minY) * containerH;

    return {
      position: "absolute" as const,
      left,
      top,
      width,
      height,
      border: "2px solid rgba(34,187,102,0.95)",
      background: "rgba(34,187,102,0.18)",
      borderRadius: 6,
      pointerEvents: "none" as const,
    };
  }

  // We need the rendered page size to position overlay; react-pdf renders a canvas.
  // We'll measure the page wrapper after render.
  const [pageBox, setPageBox] = useState<{ w: number; h: number } | null>(null);

  useEffect(() => {
    setPageBox(null);
    setLoadError(null);
  }, [pdfUrl, pageNumber]);

  return (
    <div style={{ height, overflow: "auto" }}>
      <Document
        file={pdfUrl}
        onLoadSuccess={(p: { numPages: number }) => {
          setNumPages(p.numPages);
          setLoadError(null);
        }}
        onLoadError={(error: Error) => {
          console.error("PDF load error:", error);
          setLoadError(error.message || "Failed to load PDF");
        }}
        loading={<div style={{ color: "#555" }}>Loading PDF…</div>}
        error={
          <div style={{ color: "crimson" }}>
            Failed to load PDF.
            {loadError && <div style={{ fontSize: "0.9em", marginTop: 4 }}>{loadError}</div>}
          </div>
        }
      >
        <div
          style={{ position: "relative", display: "inline-block" }}
          ref={(el) => {
            if (!el) return;
            // Find the canvas inside and read its size
            const canvas = el.querySelector("canvas");
            if (canvas && (pageBox?.w !== canvas.clientWidth || pageBox?.h !== canvas.clientHeight)) {
              setPageBox({ w: canvas.clientWidth, h: canvas.clientHeight });
            }
          }}
        >
          <Page
            pageNumber={pageNumber}
            renderTextLayer={false}
            renderAnnotationLayer={false}
            loading={<div style={{ color: "#555" }}>Rendering page…</div>}
          />

          {pageBox && rect && highlight && highlight.page === pageNumber ? (
            <div style={overlayStyle(pageBox.w, pageBox.h) ?? undefined} />
          ) : null}
        </div>
      </Document>
    </div>
  );
}
