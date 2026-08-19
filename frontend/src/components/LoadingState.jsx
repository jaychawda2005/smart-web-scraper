export default function LoadingState({ url, message }) {
  const isJsMode = !!message;
  return (
    <div className="card flex flex-col items-center py-16 gap-6">
      <div className="relative">
        <div className={`w-16 h-16 rounded-full border-4 border-slate-800 animate-spin ${
          isJsMode ? 'border-t-indigo-500' : 'border-t-indigo-500'
        }`} />
        <div className="absolute inset-0 flex items-center justify-center text-2xl">
          {isJsMode ? '⚡' : '🌐'}
        </div>
      </div>
      <div className="text-center">
        <p className="text-slate-200 font-medium text-lg">
          {message || 'Analyzing webpage…'}
        </p>
        {url && (
          <p className="text-slate-500 text-sm mt-1 max-w-md truncate">{url}</p>
        )}
        <p className="text-slate-600 text-xs mt-3">
          {isJsMode
            ? 'Launching headless browser and waiting for JavaScript to render. This takes 5–15 seconds.'
            : 'Fetching and parsing HTML content. This may take a few seconds.'}
        </p>
      </div>
    </div>
  );
}
