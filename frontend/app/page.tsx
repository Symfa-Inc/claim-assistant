'use client'


import { ArrowRightIcon } from '@heroicons/react/24/outline';
import dynamic from 'next/dynamic';
import Link from 'next/link';

const AppPdfViewer = dynamic(() => import('@/app/ui/pdf-viewer/pdfviewer'), {
  ssr: false,
});

export default function Page() {
  return (
    <main className="flex h-screen flex-col">
      <header className="bg-blue-600 text-white">
        <div className="mx-auto px-4 py-4 text-2xl font-semibold">
          Claim Assistant
        </div>
      </header>
      <div className="ml-4 mr-4 flex flex-1 min-h-0 flex-col gap-4 py-4 md:flex-row">
        <div className="flex min-h-0 flex-1 items-stretch md:w-2/4 md:px-0">
          <div className="flex min-h-0 w-full flex-1 flex-col rounded-lg bg-gray-50 p-4">
            <AppPdfViewer />
          </div>
        </div>
        <div className="flex flex-col justify-center gap-6 rounded-lg bg-gray-50 md:w-2/4 md:px-10">
          <p className={`text-xl text-gray-800 md:text-3xl md:leading-normal`}>
            <strong>Welcome to Acme.</strong> This is the example for the{' '}
            <a href="https://nextjs.org/learn/" className="text-blue-500">
              Next.js Learn Course
            </a>
            , brought to you by Vercel.
          </p>
          <Link
            href="/login"
            className="flex items-center gap-5 self-start rounded-lg bg-blue-500 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-400 md:text-base"
          >
            <span>Log in</span> <ArrowRightIcon className="w-5 md:w-6" />
          </Link>
        </div>
      </div>
    </main>
  );
}
