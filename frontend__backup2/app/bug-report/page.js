"use client";

import React, { Suspense, useState, useEffect } from 'react';
import Link from 'next/link';

// Dynamically import the BugReportForm component with error boundary
const BugReportForm = React.lazy(() => import('@/components/features/BugReportForm'));

// Fallback component to show while the form is loading or if it fails
function FormLoadingFallback() {
  return (
    <div className="p-8 text-center">
      <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-white border-t-transparent"></div>
      <p className="mt-4 text-gray-300">Loading bug report form...</p>
    </div>
  );
}

function FormErrorFallback() {
  return (
    <div className="p-8 text-center">
      <div className="bg-red-500 bg-opacity-10 border border-red-300 text-red-300 rounded-md p-6 mb-6">
        <h3 className="text-lg font-medium mb-2">Error Loading Form</h3>
        <p>Sorry, there was a problem loading the bug report form.</p>
        <p className="mt-4">Please try again later or contact support directly.</p>
      </div>
      <Link 
        href="/" 
        className="px-4 py-2 bg-[#242d4f] hover:bg-[#343e60] text-white rounded transition-colors"
      >
        Return to Home
      </Link>
    </div>
  );
}

export default function BugReportPage() {
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    // Add basic error handling for the component
    const handleError = (error) => {
      console.error('Error in BugReportForm component:', error);
      setHasError(true);
    };

    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);

  return (
    <div className="p-6 bg-[#0b1021] text-white min-h-screen">
      <div className="max-w-3xl mx-auto">
        <header className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-[#6d4aff] to-[#8c5eff] bg-clip-text text-transparent">
            Bug Report Form
          </h1>
          <Link 
            href="/" 
            className="px-4 py-2 bg-[#242d4f] hover:bg-[#343e60] text-white rounded transition-colors"
          >
            Back to Home
          </Link>
        </header>
        
        <div className="bg-[#121833] p-6 rounded-xl shadow-lg">
          {hasError ? (
            <FormErrorFallback />
          ) : (
            <Suspense fallback={<FormLoadingFallback />}>
              <BugReportForm />
            </Suspense>
          )}
        </div>
        
        <div className="mt-6 text-center text-sm text-gray-400">
          <p>If you encounter any issues with this form, please email support directly at help@example.com</p>
          <div className="mt-4">
            <a
              href="/zendesk-bug-report.html"
              className="inline-block px-3 py-1 bg-[#242d4f] hover:bg-[#343e60] text-white rounded transition-colors text-sm"
            >
              Use Alternative Form
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}