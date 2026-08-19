import { useState, useEffect } from 'react';
import { getHistory, deleteHistoryItem } from '../services/api';

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function ScrapeHistory({ onScrapeAgain }) {
  const [jobs, setJobs] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deletingId, setDeletingId] = useState(null);

  async function fetchHistory() {
    setLoading(true);
    setError('');
    try {
      const data = await getHistory(30);
      setJobs(data.jobs);
      setTotal(data.total);
    } catch (e) {
      setError('Could not load history. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchHistory(); }, []);

  async function handleDelete(id) {
    setDeletingId(id);
    try {
      await deleteHistoryItem(id);
      setJobs(j => j.filter(x => x.id !== id));
      setTotal(t => t - 1);
    } catch {
      /* ignore */
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">Scraping History</h2>
          <p className="text-xs text-slate-500 mt-0.5">{total} total jobs</p>
        </div>
        <button onClick={fetchHistory} className="btn-ghost" disabled={loading}>
          {loading ? '⏳' : '🔄'} Refresh
        </button>
      </div>

      {error && (
        <div className="card border-red-900/50">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12 text-slate-500 text-sm gap-2">
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          Loading history…
        </div>
      ) : jobs.length === 0 ? (
        <div className="card flex flex-col items-center py-12 text-center">
          <div className="text-4xl mb-3">📭</div>
          <p className="text-slate-400 font-medium">No scraping jobs yet</p>
          <p className="text-slate-600 text-sm mt-1">Start scraping a URL to see history here.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {jobs.map(job => (
            <div
              key={job.id}
              className="card flex flex-col sm:flex-row sm:items-center gap-3 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className={`w-2 h-2 rounded-full shrink-0 ${job.status === 'success' ? 'bg-emerald-400' : 'bg-red-400'}`} />
                <div className="min-w-0">
                  <p className="text-slate-200 text-sm font-medium truncate">
                    {job.title || job.url}
                  </p>
                  <p className="text-slate-500 text-xs truncate">{job.url}</p>
                </div>
              </div>

              <div className="flex items-center gap-4 shrink-0 pl-5 sm:pl-0">
                <div className="text-right">
                  <p className="text-slate-400 text-xs">{timeAgo(job.timestamp)}</p>
                  <p className="text-slate-600 text-xs">{job.items_found} items</p>
                </div>
                <span className={`badge ${job.status === 'success' ? 'badge-green' : 'badge-red'}`}>
                  {job.status}
                </span>
                <button
                  onClick={() => onScrapeAgain(job.url)}
                  className="btn-ghost text-indigo-400 hover:text-indigo-300"
                  title="Scrape this URL again"
                >
                  ↩ Scrape Again
                </button>
                <button
                  onClick={() => handleDelete(job.id)}
                  disabled={deletingId === job.id}
                  className="btn-ghost text-red-400 hover:text-red-300"
                  title="Delete this record"
                >
                  {deletingId === job.id ? '…' : '🗑'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
