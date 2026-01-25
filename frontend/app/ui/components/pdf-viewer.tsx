'use client'

import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { ChangeEvent, DragEvent } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
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
    highlightFieldId?: string | null
    highlightBoxes?: HighlightBox[]
}

export default function AppPdfViewer({
    src,
    isProcessing = false,
    onProcess,
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
    const [isLoading, setIsLoading] = useState(false)
    const [containerWidth, setContainerWidth] = useState(0)
    const [numPages, setNumPages] = useState<number | null>(null)
    const [zoom, setZoom] = useState(1)
    const [pageSizes, setPageSizes] = useState<Record<number, {
        width: number
        height: number
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
        setIsLoading(true)
    }, [])

    const handleFile = (nextFile: File) => {
        if (nextFile.type !== 'application/pdf') {
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
        setError(null)
        setIsLoading(true)
    }

    const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
        const nextFile = event.target.files?.[0]
        if (nextFile) {
            handleFile(nextFile)
        }
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
        formData.append('file', pdfFile)           // pdfFile is File or Blob
        formData.append('form', selectedForm)      // optional extra field

        const response = await api.post('/process', formData)

        console.log(response.data)
    }

    const selectForm = (formId: string) => {
        if (formId === 'custom') return

        console.log(file)

        const [state, raw] = formId.split(':')
        const fileName = raw.split('__')[1]

        setFile(`/forms/${state}/${fileName}`)
        // setFileName(fileName) // optional
        setSelectedForm(formId)
        setIsLoading(true)
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
        <div className="flex h-full min-h-0 w-full flex-1 flex-col">
            <div className="flex flex-wrap items-center gap-3 pb-3">
                <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-gray-700">
                        PDF Preview
                    </span>
                    {isLoading && (
                        <span className="text-xs text-gray-500">
                            Loading...
                        </span>
                    )}
                </div>
                <div className="flex flex-1 flex-wrap items-center gap-3">
                    <div className="flex flex-1 items-center gap-2 text-xs text-gray-500">
                        <button
                            type="button"
                            onClick={() =>
                                setZoom((value) => Math.max(0.5, value - 0.1))
                            }
                            className="rounded-md text-sm border border-gray-300 bg-white px-2 py-1 text-gray-700 hover:bg-gray-50"
                            aria-label="Zoom out"
                        >
                            -
                        </button>
                        <span className="min-w-[48px] text-center">
                            {Math.round(zoom * 100)}%
                        </span>
                        <button
                            type="button"
                            onClick={() =>
                                setZoom((value) => Math.min(2.5, value + 0.1))
                            }
                            className="rounded-md text-sm border border-gray-300 bg-white px-2 py-1 text-gray-700 hover:bg-gray-50"
                            aria-label="Zoom in"
                        >
                            +
                        </button>
                        <label className="cursor-pointer rounded-md text-sm border border-gray-300 bg-white px-3 py-1 text-gray-700 shadow-sm hover:bg-gray-50">
                            Upload PDF
                            <input
                                type="file"
                                accept="application/pdf"
                                className="hidden"
                                onChange={handleFileChange}
                            />
                        </label>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                        <span className="text-sm font-medium text-gray-700">
                            Claim Form
                        </span>
                        <select
                            value={selectedForm}
                            onChange={(event) =>
                                selectForm(event.target.value)
                            }
                            className="rounded-md text-sm text-left border border-gray-300 bg-white py-1 pr-9 pl-3 text-gray-700 hover:bg-gray-50"
                            aria-label="Form"
                        >
                            <option value="FL:FL__form_dg_POL123456789.pdf">Florida digital</option>
                            <option value="FL:FL__form_hw_POL987654321.pdf">Florida handwritten</option>
                            <option value="NH:NH__form_dg_SIC123456789.pdf">New Hampshire digital</option>
                            <option value="NH:NH__form_hw_POL123456789.pdf">New Hampshire handwritten</option>
                            <option value="WI:WI__form_dg_POL987654321.pdf">Wisconsin digital</option>
                            <option value="WI:WI__form_hw_POL123456789.pdf">Wisconsin handwritten</option>
                            <option value="custom">Custom</option>
                        </select>
                    </div>
                    <div className="flex flex-1 items-center justify-end gap-2 text-sm">
                        <button
                            type="button"
                            onClick={() => {
                                if (canProcess) {
                                    handleProcessPdf()
                                }
                            }}
                            className={`rounded-md text-sm px-3 py-1 text-white ${canProcess
                                ? 'bg-green-600 hover:bg-green-600'
                                : 'cursor-not-allowed bg-green-300'
                                }`}
                            aria-disabled={!canProcess}
                        >
                            {isProcessing ? 'Processing...' : 'Process PDF'}
                        </button>
                    </div>
                </div>
            </div>
            <div
                ref={scrollRef}
                className="flex-1 min-h-0 overflow-auto rounded-lg bg-white p-1 shadow-sm"
            >
                <div
                    ref={containerRef}
                    onDrop={handleDrop}
                    onDragOver={(event) => event.preventDefault()}
                    className="flex min-h-full min-w-max flex-col items-center gap-2 rounded-md border border-transparent p-2 text-sm text-gray-500"
                >
                    {error && (
                        <p className="text-sm text-red-600">{error}</p>
                    )}
                    {!file ? (
                        <div className="flex w-full flex-1 flex-col items-center justify-center text-center">
                            <p>Drop a PDF here or upload one to preview.</p>
                            <p className="text-xs text-gray-400">
                                Supported: PDF files only
                            </p>
                        </div>
                    ) : (
                        <div className="flex w-max flex-col items-center">
                            {fileName && (
                                <p className="text-xs text-gray-500">
                                    {fileName}
                                </p>
                            )}
                            <Document
                                file={file}
                                onLoadSuccess={({ numPages }) => {
                                    setNumPages(numPages)
                                    setIsLoading(false)
                                }}
                                onLoadError={() => {
                                    setError('Failed to load PDF preview.')
                                    setIsLoading(false)
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
                                                                const points =
                                                                    buildPolygonPoints(
                                                                        box.vertices.map(
                                                                            (
                                                                                point
                                                                            ) => ({
                                                                                x:
                                                                                    point.x *
                                                                                    displayScale,
                                                                                y:
                                                                                    point.y *
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
                                                                                points
                                                                            }
                                                                            className="fill-blue-200/30 stroke-blue-500"
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
