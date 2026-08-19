import { useState } from 'react';

function isValidUrl(str) {
  try {
    const url = new URL(str.trim());
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch {
    return false;
  }
}

export default function UrlInput({ onScrape, loading, renderJs, onRenderJsChange }) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  function validate(val) {
    if (!val.trim()) return 'Please enter a URL.';
    if (!val.startsWith('http://') && !val.startsWith('https://'))
      return 'URL must start with http:// or https://';
    if (!isValidUrl(val)) return 'Please enter a valid URL (e.g. https://example.com)';
    return '';
  }

  function handleSubmit(e) {
    e.preventDefault();
    const err = validate(url);
    if (err) { setError(err); return; }
    setError('');
    onScrape(url.trim());
  }

  function handleChange(e) {
    setUrl(e.target.value);
    if (error) setError('');
  }

  return (
    <div className="card space-y-3">
      <label className="block text-sm font-medium text-slate-300">
        Webpage URL
      </label>
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
          </div>
          <input
            type="text"
            className={`input-base pl-9 ${error ? 'border-red-500 focus:ring-red-500' : ''}`}
            placeholder="https://example.com"
            value={url}
            onChange={handleChange}
            disabled={loading}
            aria-label="Webpage URL"
          />
        </div>
        <button
          type="submit"
          className="btn-primary whitespace-nowrap"
          disabled={loading}
        >
          {loading ? (
            <>
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              {renderJs ? 'Rendering…' : 'Analyzing…'}
            </>
          ) : (
            <><span>🚀</span> Start Scraping</>
          )}
        </button>
      </form>

      {/* Render JavaScript toggle */}
      <div className="flex items-start gap-3 pt-1">
        <div className="relative flex items-center mt-0.5">
          <input
            id="render-js-toggle"
            type="checkbox"
            checked={renderJs}
            onChange={e => onRenderJsChange(e.target.checked)}
            disabled={loading}
            className="sr-only peer"
          />
          <div
            onClick={() => !loading && onRenderJsChange(!renderJs)}
            className={`
              w-9 h-5 rounded-full cursor-pointer transition-colors duration-200 flex items-center
              ${renderJs ? 'bg-indigo-600' : 'bg-slate-700'}
              ${loading ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          >
            <div className={`
              w-3.5 h-3.5 bg-white rounded-full shadow-sm transition-transform duration-200 mx-0.5
              ${renderJs ? 'translate-x-4' : 'translate-x-0'}
            `} />
          </div>
        </div>
        <div>
          <label
            htmlFor="render-js-toggle"
            className={`text-sm font-medium cursor-pointer select-none ${
              renderJs ? 'text-indigo-300' : 'text-slate-400'
            }`}
            onClick={() => !loading && onRenderJsChange(!renderJs)}
          >
            Render JavaScript{' '}
            <span className="text-xs font-normal text-slate-500">(slower)</span>
            {renderJs && (
              <span className="ml-2 inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-indigo-900/60 text-indigo-300 border border-indigo-800/60">
                ⚡ JS MODE
              </span>
            )}
          </label>
          <p className="text-xs text-slate-600 mt-0.5">
            Enable for sites that load content dynamically (React, Vue, Angular apps). Takes 3–10 s.
          </p>
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-400 flex items-center gap-1">
          <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </p>
      )}
    </div>
  );
}
