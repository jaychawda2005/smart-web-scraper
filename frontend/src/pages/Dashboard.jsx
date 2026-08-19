import { useState } from 'react';
import UrlInput from '../components/UrlInput';
import ExtractionOptions from '../components/ExtractionOptions';
import StatsCard from '../components/StatsCard';
import ResultsTabs from '../components/ResultsTabs';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import EmptyState from '../components/EmptyState';
import ScrapeHistory from '../components/ScrapeHistory';
import { ContentDistributionChart, HeadingDistributionChart } from '../components/Charts';
import { scrapeUrl, exportJson, exportCsv, exportExcel } from '../services/api';

const DEFAULT_OPTIONS = {
  page_info: true,
  headings: true,
  text: true,
  links: true,
  images: true,
  tables: true,
  lists: true,
};

const STATS = [
  { key: 'headings_count',    label: 'Headings',    icon: '🔤', color: 'indigo'  },
  { key: 'text_blocks_count', label: 'Text Blocks', icon: '📝', color: 'blue'    },
  { key: 'links_count',       label: 'Links',       icon: '🔗', color: 'sky'     },
  { key: 'images_count',      label: 'Images',      icon: '🖼️', color: 'emerald' },
  { key: 'tables_count',      label: 'Tables',      icon: '📊', color: 'amber'   },
  { key: 'lists_count',       label: 'Lists',       icon: '📋', color: 'violet'  },
];

export default function Dashboard({ activeSection, onScrapeSuccess }) {
  const [options, setOptions]   = useState(DEFAULT_OPTIONS);
  const [renderJs, setRenderJs] = useState(false);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');
  const [result, setResult]     = useState(null);
  const [lastUrl, setLastUrl]   = useState('');
  const [exportLoading, setExportLoading] = useState('');

  const anySelected = Object.values(options).some(Boolean);

  async function handleScrape(url) {
    if (!anySelected) return;
    setLoading(true);
    setError('');
    setResult(null);
    setLastUrl(url);
    try {
      const data = await scrapeUrl(url, options, renderJs);
      setResult(data);
      if (onScrapeSuccess) onScrapeSuccess();
    } catch (e) {
      const msg =
        e?.response?.data?.detail ||
        e?.message ||
        'An unexpected error occurred.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  function handleScrapeAgain(url) {
    setLastUrl(url);
    handleScrape(url);
  }

  function handleClear() {
    setResult(null);
    setError('');
    setLastUrl('');
  }

  function handleExport(type) {
    setExportLoading(type);
    try {
      if (type === 'json')  exportJson();
      if (type === 'csv')   exportCsv();
      if (type === 'excel') exportExcel();
    } finally {
      setTimeout(() => setExportLoading(''), 1500);
    }
  }

  const pi = result?.page_info;

  /* ── Section: Dashboard ── */
  if (activeSection === 'Dashboard') {
    return (
      <div className="space-y-6">
        {/* Hero */}
        <div className="text-center py-8 px-4">
          <h1 className="text-3xl sm:text-4xl font-bold text-slate-100 tracking-tight">
            Smart<span className="text-indigo-400">Scrape</span>
          </h1>
          <p className="text-slate-400 mt-2 text-base max-w-xl mx-auto">
            Universal Web Data Extraction &amp; Analytics Platform
          </p>
          <p className="text-slate-300 mt-1 text-sm max-w-2xl mx-auto">
            Extract, explore, analyze and export structured data from publicly accessible webpages.
          </p>
          <p className="text-slate-600 text-xs mt-3 max-w-xl mx-auto">
            ⚠️ Only scrape webpages where automated access is permitted. SmartScrape does not
            bypass CAPTCHA, authentication, paywalls, or other access controls.
          </p>
        </div>

        {/* Input */}
        <UrlInput
          onScrape={handleScrape}
          loading={loading}
          renderJs={renderJs}
          onRenderJsChange={setRenderJs}
        />

        {/* Options */}
        <ExtractionOptions options={options} onChange={setOptions} disabled={loading} />

        {/* Status */}
        {loading && <LoadingState url={lastUrl} message={renderJs ? 'Rendering page with browser…' : undefined} />}
        {!loading && error && (
          <ErrorState message={error} onRetry={() => handleScrape(lastUrl)} />
        )}

        {/* Results */}
        {!loading && !error && result && (
          <>
            {/* Success banner */}
            <div className="flex items-center justify-between p-3 bg-emerald-950/40 border border-emerald-800/50 rounded-xl">
              <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium">
                <span>✅</span> Scraping completed successfully
                {result.render_js_used && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-indigo-900/60 text-indigo-300 border border-indigo-800/60">
                    ⚡ JS Rendered
                  </span>
                )}
              </div>
              <button onClick={handleClear} className="btn-ghost text-slate-400">
                × Clear Results
              </button>
            </div>

            {/* YouTube detected notice */}
            {result.youtube_data && (
              <div className="flex items-center gap-3 p-3 bg-red-950/30 border border-red-900/50 rounded-xl">
                <span className="text-xl">▶️</span>
                <div className="flex-1">
                  <p className="text-red-300 text-sm font-medium">YouTube video detected</p>
                  <p className="text-red-400/70 text-xs mt-0.5">
                    Rich metadata has been extracted. Click the <strong>▶️ YouTube</strong> tab below to see full video details.
                  </p>
                </div>
              </div>
            )}

            {/* Page info header */}
            {pi && (
              <div className="card">
                <div className="flex flex-col sm:flex-row sm:items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <h2 className="text-base font-semibold text-slate-100 truncate">
                      {pi.title || '(no title)'}
                    </h2>
                    <a
                      href={pi.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-400 text-sm hover:underline truncate block mt-0.5"
                    >
                      {pi.url}
                    </a>
                  </div>
                  <span className={`badge shrink-0 ${pi.status_code === 200 ? 'badge-green' : 'badge-red'}`}>
                    HTTP {pi.status_code}
                  </span>
                </div>
              </div>
            )}

            {/* Stats grid */}
            {pi && (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                {STATS.map(s => (
                  <StatsCard
                    key={s.key}
                    icon={s.icon}
                    label={s.label}
                    value={pi[s.key]}
                    color={s.color}
                  />
                ))}
              </div>
            )}

            {/* Export */}
            <div className="flex flex-wrap gap-2">
              {[
                { type: 'json',  label: '⬇ JSON',  },
                { type: 'csv',   label: '⬇ CSV',   },
                { type: 'excel', label: '⬇ Excel', },
              ].map(({ type, label }) => (
                <button
                  key={type}
                  onClick={() => handleExport(type)}
                  disabled={!!exportLoading}
                  className="btn-secondary"
                >
                  {exportLoading === type ? 'Downloading…' : label}
                </button>
              ))}
            </div>

            {/* Tabs */}
            <ResultsTabs data={result} />
          </>
        )}

        {/* Idle empty state */}
        {!loading && !error && !result && (
          <EmptyState
            title="Enter a webpage URL to get started."
            subtitle="Configure extraction options above, then click Start Scraping."
          />
        )}
      </div>
    );
  }

  /* ── Section: Results ── */
  if (activeSection === 'Results') {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-100">Results</h2>
          {result && (
            <button onClick={handleClear} className="btn-secondary">
              × Clear Results
            </button>
          )}
        </div>

        {!result ? (
          <EmptyState
            title="No results yet."
            subtitle="Go to Dashboard, enter a URL, and start scraping."
          />
        ) : (
          <>
            {pi && (
              <div className="card">
                <p className="text-sm font-medium text-slate-200">{pi.title || '(no title)'}</p>
                <p className="text-xs text-slate-500 mt-1 truncate">{pi.url}</p>
              </div>
            )}
            {pi && (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                {STATS.map(s => (
                  <StatsCard key={s.key} icon={s.icon} label={s.label} value={pi[s.key]} color={s.color} />
                ))}
              </div>
            )}
            <div className="flex flex-wrap gap-2">
              {[
                { type: 'json',  label: '⬇ JSON'  },
                { type: 'csv',   label: '⬇ CSV'   },
                { type: 'excel', label: '⬇ Excel' },
              ].map(({ type, label }) => (
                <button key={type} onClick={() => handleExport(type)} className="btn-secondary">
                  {exportLoading === type ? 'Downloading…' : label}
                </button>
              ))}
            </div>
            <ResultsTabs data={result} />
          </>
        )}
      </div>
    );
  }

  /* ── Section: History ── */
  if (activeSection === 'History') {
    return <ScrapeHistory onScrapeAgain={handleScrapeAgain} />;
  }

  /* ── Section: Analytics ── */
  if (activeSection === 'Analytics') {
    return (
      <div className="space-y-6">
        <h2 className="text-xl font-semibold text-slate-100">Analytics</h2>
        {!result ? (
          <EmptyState
            title="No data to analyze."
            subtitle="Scrape a webpage first to see analytics."
          />
        ) : (
          <>
            <p className="text-slate-500 text-sm">
              Showing analytics for:{' '}
              <span className="text-slate-300">{pi?.title || result.url}</span>
            </p>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {pi && <ContentDistributionChart data={pi} />}
              {result.headings && <HeadingDistributionChart headings={result.headings} />}
            </div>
          </>
        )}
      </div>
    );
  }

  return null;
}
