'use client'

import { useEffect, useState } from 'react'
import type { ChangeEvent, DragEvent } from 'react'

interface OwnProps {
    src?: string
}

export default function AppPdfViewer({ src }: OwnProps) {
    const [error, setError] = useState<string | null>(null)
    const [fileUrl, setFileUrl] = useState<string | null>(src ?? null)
    const [fileName, setFileName] = useState<string | null>(null)
    const [urlInput, setUrlInput] = useState(src ?? '')
    const [isLoading, setIsLoading] = useState(false)

    useEffect(() => {
        if (!src) return
        setFileUrl(src)
        setUrlInput(src)
    }, [src])

    useEffect(() => {
        return () => {
            if (fileUrl?.startsWith('blob:')) {
                URL.revokeObjectURL(fileUrl)
            }
        }
    }, [fileUrl])

    const handleFile = (nextFile: File) => {
        if (nextFile.type !== 'application/pdf') {
            setError('Please choose a valid PDF file.')
            return
        }

        if (fileUrl?.startsWith('blob:')) {
            URL.revokeObjectURL(fileUrl)
        }

        const nextUrl = URL.createObjectURL(nextFile)
        setFileUrl(nextUrl)
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

    const handleUrlLoad = () => {
        const nextUrl = urlInput.trim()
        if (!nextUrl) {
            setError('Please enter a PDF URL.')
            return
        }

        if (fileUrl?.startsWith('blob:')) {
            URL.revokeObjectURL(fileUrl)
        }

        setFileUrl(nextUrl)
        setFileName(null)
        setError(null)
        setIsLoading(true)
    }

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
                <div className="flex flex-1 flex-wrap items-center justify-end gap-2 text-sm">
                    <label className="cursor-pointer rounded-md border border-gray-300 bg-white px-3 py-1 text-gray-700 shadow-sm hover:bg-gray-50">
                        Upload PDF
                        <input
                            type="file"
                            accept="application/pdf"
                            className="hidden"
                            onChange={handleFileChange}
                        />
                    </label>
                    <input
                        value={urlInput}
                        onChange={(event) => setUrlInput(event.target.value)}
                        placeholder="Paste PDF URL"
                        className="min-w-[180px] flex-1 rounded-md border border-gray-300 px-3 py-1 text-sm"
                    />
                    <button
                        type="button"
                        onClick={handleUrlLoad}
                        className="rounded-md bg-blue-600 px-3 py-1 text-white hover:bg-blue-500"
                    >
                        Open URL
                    </button>
                </div>
            </div>
            <div className="flex-1 min-h-0 overflow-hidden rounded-lg bg-white p-1 shadow-sm">
                <div
                    onDrop={handleDrop}
                    onDragOver={(event) => event.preventDefault()}
                    className="flex h-full min-h-0 w-full flex-col items-center justify-center gap-2 rounded-md border border-transparent p-2 text-sm text-gray-500"
                >
                    {error && (
                        <p className="text-sm text-red-600">{error}</p>
                    )}
                    {!fileUrl ? (
                        <>
                            <p>Drop a PDF here or upload one to preview.</p>
                            <p className="text-xs text-gray-400">
                                Supported: PDF files only
                            </p>
                        </>
                    ) : (
                        <div className="flex h-full min-h-0 w-full flex-1 flex-col">
                            {fileName && (
                                <p className="text-xs text-gray-500">
                                    {fileName}
                                </p>
                            )}
                            <iframe
                                title="PDF preview"
                                src={fileUrl}
                                className="min-h-0 w-full flex-1 rounded-md border"
                                onLoad={() => setIsLoading(false)}
                            />
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
