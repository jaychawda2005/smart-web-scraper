export default function ErrorState({ message, onRetry }) {
  const isBackendDown =
    message?.toLowerCase().includes('network') ||
    message?.toLowerCase().includes('connect') ||
    message?.toLowerCase().includes('econnrefused');

  return (
    <div className="card border-red-900/50 flex flex-col items-center py-12 gap-4 text-center">
      <div className="w-14 h-14 rounded-full bg-red-950/60 flex items-center justify-center text-2xl">
        ❌
      </div>
      <div>
        <p className="text-red-400 font-semibold text-lg">Scraping Failed</p>
        {isBackendDown ? (
          <p className="text-slate-400 text-sm mt-2 max-w-sm">
            Unable to connect to SmartScrape.<br />
            Please make sure the FastAPI backend is running at{' '}
            <code className="text-indigo-400 text-xs">http://127.0.0.1:8000</code>
          </p>
        ) : (
          <p className="text-slate-400 text-sm mt-2 max-w-sm">
            {message || 'An unexpected error occurred. Please try again.'}
          </p>
        )}
      </div>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary mt-2">
          Try Again
        </button>
      )}
    </div>
  );
}
