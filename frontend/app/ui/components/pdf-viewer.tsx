'use client'

import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { ChangeEvent, DragEvent } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import type { ClaimField } from '@/app/ui/components/claim-table'
import api from '@/app/utils/api'

if (typeof window !== 'undefined') {
    pdfjs.GlobalWorkerOptions.workerSrc = new URL(
        'pdfjs-dist/build/pdf.worker.min.mjs',
        import.meta.url
    ).toString()
}

export interface HighlightBox {
    id: string
    fieldId: string
    page: number
    vertices: Array<{ x: number; y: number }>
}

interface OwnProps {
    src?: string
    isProcessing?: boolean
    onProcess?: () => void
    onProcessed?: (
        fields: ClaimField[],
        keyFields: ClaimField[],
        boxes: HighlightBox[],
        summary: BackendSummary | null
    ) => void
    highlightFieldId?: string | null
    highlightBoxes?: HighlightBox[]
}

interface BackendBoundingRegion {
    page: number
    polygon: number[]
}

interface BackendFormEvidence {
    confidence?: number | null
    bounding_region?: BackendBoundingRegion | null
}

interface BackendFormAnswer {
    value?: unknown
    evidences?: BackendFormEvidence[]
}

interface BackendFormField {
    text: string
    alias?: string | null
    answer?: BackendFormAnswer
}

interface BackendResponse {
    form?: BackendFormField[]
    executive_summary?: string
    confidence?: number
    conclusion?: string
}

interface BackendSummary {
    executiveSummary: string
    confidence: number | null
    conclusion: string | null
}

export default function AppPdfViewer({
    src,
    isProcessing = false,
    onProcess,
    onProcessed,
    highlightFieldId,
    highlightBoxes = [],
}: OwnProps) {
    const containerRef = useRef<HTMLDivElement | null>(null)
    const lastWidthRef = useRef<number | null>(null)
    const scrollRef = useRef<HTMLDivElement | null>(null)
    const wheelAccumulatorRef = useRef(0)
    const wheelResetRef = useRef<ReturnType<typeof setTimeout> | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [file, setFile] = useState<File | string | null>(src ?? null)
    const [fileName, setFileName] = useState<string | null>(null)
    const [selectedForm, setSelectedForm] = useState('FL:FL__form_dg_POL123456789.pdf')
    const [containerWidth, setContainerWidth] = useState(0)
    const [numPages, setNumPages] = useState<number | null>(null)
    const [zoom, setZoom] = useState(1)
    const [pageSizes, setPageSizes] = useState<Record<number, {
        width: number
        height: number
        viewBox?: [number, number, number, number]
    }>>({})

    useEffect(() => {
        const target = scrollRef.current
        if (!target) return
        const updateWidth = () => {
            const nextWidth = target.clientWidth ?? 0
            if (lastWidthRef.current !== nextWidth) {
                lastWidthRef.current = nextWidth
                setContainerWidth(nextWidth)
            }
        }
        updateWidth()
        const observer = new ResizeObserver(updateWidth)
        observer.observe(target)
        return () => observer.disconnect()
    }, [])

    useEffect(() => {
        if (!src) return
        setFile(src)
    }, [src])

    useEffect(() => {
        const [state, raw] = 'FL:FL__form_dg_POL123456789.pdf'.split(':')
        const fileName = raw.split('__')[1] // or raw if you prefer
        setFile(`/forms/${state}/${fileName}`)
    }, [])

    const handleFile = (nextFile: File) => {
        const isPdf =
            nextFile.type === 'application/pdf' ||
            !nextFile.type ||
            nextFile.name.toLowerCase().endsWith('.pdf')
        if (!isPdf) {
            setError('Please choose a valid PDF file.')
            return
        }

        wheelAccumulatorRef.current = 0
        if (wheelResetRef.current) {
            clearTimeout(wheelResetRef.current)
        }
        setZoom(1)
        setFile(nextFile)
        setFileName(nextFile.name)
        setSelectedForm('generic')
        setError(null)
    }

    const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
        const input = event.target
        const nextFile = input.files?.[0]
        if (nextFile) {
            handleFile(nextFile)
        }
        input.value = ''
    }

    const handleDrop = (event: DragEvent<HTMLDivElement>) => {
        event.preventDefault()
        const nextFile = event.dataTransfer.files?.[0]
        if (nextFile) {
            handleFile(nextFile)
        }
    }

    const handleProcessPdf = async () => {
        if (!file) return
        onProcess?.()

        let pdfFile: File

        if (file instanceof File) {
            pdfFile = file
        } else {
            // file is a URL string (e.g. "/forms/FL/...")
            const res = await fetch(file)
            const blob = await res.blob()
            pdfFile = new File([blob], file.split('/').pop() ?? 'form.pdf', {
                type: 'application/pdf',
            })
        }

        const formData = new FormData()
        formData.append('file', pdfFile)
        formData.append('form_id', selectedForm)

        try {
            const response = await api.post<BackendResponse>('/process', formData)
            console.log(response)
            const fields: ClaimField[] = []
            const keyFields: ClaimField[] = []
            const boxes: HighlightBox[] = []
                ; (response.data?.form ?? []).forEach((field, index) => {
                    const fieldId = field.alias ?? `field_${index}`
                    const rawValue = field.answer?.value
                    const value =
                        rawValue === null || rawValue === undefined
                            ? ''
                            : typeof rawValue === 'string'
                                ? rawValue
                                : JSON.stringify(rawValue)
                    const confidence = field.answer?.evidences?.[0]?.confidence
                    const mappedField: ClaimField = {
                        id: fieldId,
                        label: field.text,
                        value,
                        confidence:
                            typeof confidence === 'number'
                                ? `${Math.round(confidence * 100)}%`
                                : '',
                    }
                    if (field.alias) {
                        keyFields.push(mappedField)
                    } else {
                        fields.push(mappedField)
                    }

                    ; (field.answer?.evidences ?? []).forEach(
                        (evidence, evidenceIndex) => {
                            const region = evidence.bounding_region
                            if (!region || !Array.isArray(region.polygon)) return
                            if (region.polygon.length < 8) return

                            const points: Array<{ x: number; y: number }> = []
                            for (
                                let i = 0;
                                i + 1 < region.polygon.length;
                                i += 2
                            ) {
                                const x = Number(region.polygon[i])
                                const y = Number(region.polygon[i + 1])
                                if (Number.isNaN(x) || Number.isNaN(y)) continue
                                points.push({ x, y })
                            }
                            if (points.length < 4) return

                            const xs = points.map((point) => point.x)
                            const ys = points.map((point) => point.y)
                            const minX = Math.min(...xs)
                            const maxX = Math.max(...xs)
                            const minY = Math.min(...ys)
                            const maxY = Math.max(...ys)

                            boxes.push({
                                id: `${fieldId}_${evidenceIndex}`,
                                fieldId,
                                page: region.page,
                                vertices: [
                                    { x: minX, y: minY },
                                    { x: maxX, y: minY },
                                    { x: maxX, y: maxY },
                                    { x: minX, y: maxY },
                                ],
                            })
                        }
                    )
                })
            const summary: BackendSummary | null =
                response.data?.executive_summary
                    ? {
                        executiveSummary: response.data.executive_summary,
                        confidence:
                            typeof response.data.confidence === 'number'
                                ? response.data.confidence
                                : null,
                        conclusion: response.data.conclusion ?? null,
                    }
                    : null
            onProcessed?.(fields, keyFields, boxes, summary)
        } catch (error) {
            setError('Failed to process PDF.')
            onProcessed?.([], [], [], null)
        }
    }

    const selectForm = (formId: string) => {
        if (!formId) return
        if (formId === 'generic') {
            setFile(null)
            setFileName(null)
            setError(null)
            setSelectedForm(formId)
            return
        }


        const [state, raw] = formId.split(':')
        const fileName = raw.split('__')[1]

        setFile(`/forms/${state}/${fileName}`)
        // setFileName(fileName) // optional
        setSelectedForm(formId)
    }


    useEffect(() => {
        const container = scrollRef.current
        if (!container) return

        const handleWheelZoom = (event: WheelEvent) => {
            if (!event.ctrlKey) return
            event.preventDefault()
            event.stopPropagation()
            wheelAccumulatorRef.current += event.deltaY
            const threshold = 40
            const steps = Math.trunc(wheelAccumulatorRef.current / threshold)
            if (steps !== 0) {
                const stepCount = Math.max(-1, Math.min(1, steps))
                wheelAccumulatorRef.current -= stepCount * threshold
                setZoom((value) => {
                    const next = value + stepCount * -0.1
                    return Math.min(2.5, Math.max(0.5, Number(next.toFixed(2))))
                })
            }

            if (wheelResetRef.current) {
                clearTimeout(wheelResetRef.current)
            }
            wheelResetRef.current = setTimeout(() => {
                wheelAccumulatorRef.current = 0
            }, 120)
        }

        container.addEventListener('wheel', handleWheelZoom, {
            passive: false,
        })

        return () => {
            container.removeEventListener('wheel', handleWheelZoom)
            if (wheelResetRef.current) {
                clearTimeout(wheelResetRef.current)
            }
        }
    }, [])

    useLayoutEffect(() => {
        const container = scrollRef.current
        if (!container) return
        const maxScrollLeft = container.scrollWidth - container.clientWidth
        container.scrollLeft = maxScrollLeft > 0 ? maxScrollLeft / 2 : 0
    }, [zoom, containerWidth, pageSizes, numPages])

    const canProcess = Boolean(file) && !isProcessing
    const activeBoxes = highlightFieldId
        ? highlightBoxes.filter((box) => box.fieldId === highlightFieldId)
        : []

    const buildPolygonPoints = (vertices: Array<{ x: number; y: number }>) =>
        vertices.map((point) => `${point.x},${point.y}`).join(' ')

    return (
        <div className="flex h-full min-h-0 w-full flex-1 flex-col gap-4">
            {/* Modern toolbar */}
            <div className="flex flex-wrap items-center gap-4 rounded-xl border border-slate-200/60 bg-slate-50/80 backdrop-blur-sm px-4 py-3">
                <div className="flex items-center">
                    <span className="text-sm font-semibold text-slate-700">
                        Preview
                    </span>
                </div>
                <div className="flex flex-1 items-center gap-6">
                    {/* Zoom controls */}
                    <div className="flex items-center gap-2">
                        <button
                            type="button"
                            onClick={() =>
                                setZoom((value) => Math.max(0.5, value - 0.1))
                            }
                            className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 shadow-sm transition-all hover:bg-slate-50 hover:border-slate-300"
                            aria-label="Zoom out"
                        >
                            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M20 12H4" />
                            </svg>
                        </button>
                        <span className="min-w-[52px] text-center text-sm font-medium text-slate-600">
                            {Math.round(zoom * 100)}%
                        </span>
                        <button
                            type="button"
                            onClick={() =>
                                setZoom((value) => Math.min(2.5, value + 0.1))
                            }
                            className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 shadow-sm transition-all hover:bg-slate-50 hover:border-slate-300"
                            aria-label="Zoom in"
                        >
                            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                            </svg>
                        </button>
                    </div>

                    {/* Upload button */}
                    <label className="cursor-pointer inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm transition-all hover:bg-slate-50 hover:border-slate-300">
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                        </svg>
                        Upload
                        <input
                            type="file"
                            accept="application/pdf"
                            className="hidden"
                            onChange={handleFileChange}
                        />
                    </label>

                    {/* Form selector */}
                    <div className="flex items-center gap-2">
                        <span className="shrink-0 text-sm font-medium text-slate-600">
                            Form
                        </span>
                        <select
                            value={selectedForm}
                            onChange={(event) =>
                                selectForm(event.target.value)
                            }
                            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 shadow-sm transition-all hover:border-slate-300 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100"
                            aria-label="Form"
                        >
                            <option value="FL:FL__form_dg_POL123456789.pdf">Florida digital</option>
                            <option value="FL:FL__form_hw_POL987654321.pdf">Florida handwritten</option>
                            <option value="NH:NH__form_dg_SIC123456789.pdf">New Hampshire digital</option>
                            <option value="NH:NH__form_hw_POL123456789.pdf">New Hampshire handwritten</option>
                            <option value="WI:WI__form_dg_POL987654321.pdf">Wisconsin digital</option>
                            <option value="WI:WI__form_hw_POL123456789.pdf">Wisconsin handwritten</option>
                            <option value="generic">Custom</option>
                        </select>
                    </div>

                    {/* Process button */}
                    <div className="flex flex-1 items-center justify-end">
                        <button
                            type="button"
                            onClick={() => {
                                if (canProcess) {
                                    handleProcessPdf()
                                }
                            }}
                            className={`inline-flex items-center gap-2 whitespace-nowrap rounded-lg px-4 py-2 text-sm font-medium text-white shadow-sm transition-all ${canProcess
                                ? 'btn-primary'
                                : 'cursor-not-allowed bg-slate-300'
                                }`}
                            aria-disabled={!canProcess}
                        >
                            {isProcessing ? (
                                <>
                                    <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                    </svg>
                                    Processing...
                                </>
                            ) : (
                                <>
                                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                                    </svg>
                                    Process Form
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>
            {/* PDF content area */}
            <div
                ref={scrollRef}
                className="flex-1 min-h-0 overflow-auto rounded-xl border border-slate-200/60 bg-white/80 backdrop-blur-sm p-3 shadow-sm"
            >
                <div
                    ref={containerRef}
                    onDrop={handleDrop}
                    onDragOver={(event) => event.preventDefault()}
                    className="flex min-h-full min-w-max flex-col items-center gap-2 rounded-md border border-transparent p-2 text-sm text-slate-500"
                >
                    {error && (
                        <p className="text-sm text-red-600">{error}</p>
                    )}
                    {!file ? (
                        <div className="flex w-full flex-1 flex-col items-center justify-center text-center">
                            <p className="text-sm text-slate-600">
                                Drop a PDF here or upload one to preview.
                            </p>
                            <p className="text-xs text-slate-400">
                                Supported: PDF files only
                            </p>
                        </div>
                    ) : (
                        <div className="flex w-max flex-col items-center">
                            {(() => {
                                const displayName =
                                    fileName ??
                                    (typeof file === 'string'
                                        ? file.split('/').pop()
                                        : null)
                                return (
                                    <p
                                        className={`text-xs text-slate-500 ${displayName ? '' : 'invisible'}`}
                                    >
                                        {displayName ?? 'placeholder'}
                                    </p>
                                )
                            })()}
                            <Document
                                file={file}
                                onLoadSuccess={({ numPages }) => {
                                    setNumPages(numPages)
                                    setZoom(1)
                                }}
                                onLoadError={() => {
                                    setError('Failed to load PDF preview.')
                                }}
                                loading=""
                                error=""
                            >
                                {numPages &&
                                    Array.from({ length: numPages }).map(
                                        (_, index) => {
                                            const pageNumber = index + 1
                                            const size = pageSizes[pageNumber]
                                            const baseScale = 1
                                            const renderedHeight = undefined
                                            const baseGap = 24
                                            const scaledHeight = size
                                                ? size.height * zoom
                                                : undefined
                                            const scaledWidth = size
                                                ? size.width * zoom
                                                : undefined
                                            const displayScale =
                                                baseScale * zoom
                                            return (
                                                <div
                                                    key={`page_${pageNumber}`}
                                                    className="relative mx-auto"
                                                    style={
                                                        scaledHeight || scaledWidth
                                                            ? {
                                                                width: scaledWidth,
                                                                height:
                                                                    scaledHeight,
                                                                marginBottom:
                                                                    pageNumber ===
                                                                        numPages
                                                                        ? 0
                                                                        : baseGap *
                                                                        Math.max(
                                                                            1,
                                                                            zoom
                                                                        ),
                                                            }
                                                            : undefined
                                                    }
                                                >
                                                    <div
                                                        className="relative"
                                                    >
                                                        <Page
                                                            pageNumber={pageNumber}
                                                            scale={displayScale}
                                                            renderTextLayer={false}
                                                            renderAnnotationLayer={
                                                                false
                                                            }
                                                            onLoadSuccess={(
                                                                page
                                                            ) => {
                                                                const viewport =
                                                                    page.getViewport(
                                                                        {
                                                                            scale: 1,
                                                                        }
                                                                    )
                                                                setPageSizes(
                                                                    (prev) => ({
                                                                        ...prev,
                                                                        [pageNumber]:
                                                                        {
                                                                            width:
                                                                                viewport.width,
                                                                            height:
                                                                                viewport.height,
                                                                            viewBox:
                                                                                viewport.viewBox as [
                                                                                    number,
                                                                                    number,
                                                                                    number,
                                                                                    number
                                                                                ],
                                                                        },
                                                                    })
                                                                )
                                                            }}
                                                        />
                                                        {activeBoxes
                                                            .filter(
                                                                (box) =>
                                                                    box.page ===
                                                                    pageNumber
                                                            )
                                                            .map((box) => {
                                                                const maxX = Math.max(
                                                                    ...box.vertices.map(
                                                                        (point) =>
                                                                            point.x
                                                                    )
                                                                )
                                                                const maxY = Math.max(
                                                                    ...box.vertices.map(
                                                                        (point) =>
                                                                            point.y
                                                                    )
                                                                )
                                                                const isNormalized =
                                                                    maxX <= 1.5 &&
                                                                    maxY <= 1.5
                                                                const isInches =
                                                                    maxX <= 30 &&
                                                                    maxY <= 30
                                                                const isOversized =
                                                                    size &&
                                                                    (maxX >
                                                                        size.width *
                                                                        1.2 ||
                                                                        maxY >
                                                                        size.height *
                                                                        1.2)
                                                                const scaleX =
                                                                    size && isNormalized
                                                                        ? size.width
                                                                        : isInches
                                                                            ? 72
                                                                            : isOversized
                                                                                ? size.width /
                                                                                maxX
                                                                                : 1
                                                                const scaleY =
                                                                    size && isNormalized
                                                                        ? size.height
                                                                        : isInches
                                                                            ? 72
                                                                            : isOversized
                                                                                ? size.height /
                                                                                maxY
                                                                                : 1
                                                                const viewBox =
                                                                    size?.viewBox
                                                                const offsetX = viewBox
                                                                    ? -viewBox[0]
                                                                    : 0
                                                                const offsetY = viewBox
                                                                    ? -viewBox[1]
                                                                    : 0
                                                                const adjustedPoints =
                                                                    buildPolygonPoints(
                                                                        box.vertices.map(
                                                                            (
                                                                                point
                                                                            ) => ({
                                                                                x:
                                                                                    (point.x *
                                                                                        scaleX +
                                                                                        offsetX) *
                                                                                    displayScale,
                                                                                y:
                                                                                    (point.y *
                                                                                        scaleY +
                                                                                        offsetY) *
                                                                                    displayScale,
                                                                            })
                                                                        )
                                                                    )
                                                                return (
                                                                    <svg
                                                                        key={box.id}
                                                                        className="pointer-events-none absolute inset-0 h-full w-full"
                                                                    >
                                                                    <polygon
                                                                            points={
                                                                                adjustedPoints
                                                                            }
                                                                            className="fill-indigo-200/40 stroke-indigo-500"
                                                                            strokeWidth={
                                                                                2
                                                                            }
                                                                        />
                                                                    </svg>
                                                                )
                                                            })}
                                                    </div>
                                                </div>
                                            )
                                        }
                                    )}
                            </Document>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
