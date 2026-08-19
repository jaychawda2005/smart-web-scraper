import CopyButton from './CopyButton';

/**
 * Formats seconds into h:mm:ss or m:ss
 */
function formatDuration(seconds) {
  if (!seconds) return null;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${m}:${String(s).padStart(2, '0')}`;
}

/**
 * Formats large numbers: 1800684773 → "1.8B"
 */
function formatViews(n) {
  if (!n) return '—';
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000)     return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000)         return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

/**
 * Formats an ISO date string to a readable date
 */
function formatDate(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      year: 'numeric', month: 'long', day: 'numeric',
    });
  } catch {
    return iso;
  }
}

export default function YoutubePanel({ data }) {
  if (!data) return null;

  const duration = formatDuration(data.length_seconds);

  return (
    <div className="space-y-6">
      {/* Video card */}
      <div className="card flex flex-col sm:flex-row gap-5">
        {/* Thumbnail */}
        <div className="sm:w-64 shrink-0">
          {data.thumbnail_url ? (
            <a href={data.video_url} target="_blank" rel="noopener noreferrer">
              <img
                src={data.thumbnail_url}
                alt={data.title}
                className="w-full rounded-lg object-cover border border-slate-800 hover:border-indigo-600 transition-colors"
                onError={e => { e.target.style.display = 'none'; }}
              />
            </a>
          ) : (
            <div className="w-full h-36 bg-slate-800 rounded-lg flex items-center justify-center text-4xl">
              ▶️
            </div>
          )}
          {duration && (
            <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-500">
              <span>⏱</span> {duration}
              {data.is_live && <span className="badge badge-red ml-2">🔴 LIVE</span>}
            </div>
          )}
        </div>

        {/* Details */}
        <div className="flex-1 min-w-0 space-y-3">
          <div>
            <a
              href={data.video_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-lg font-semibold text-slate-100 hover:text-indigo-400 transition-colors line-clamp-2"
            >
              {data.title}
            </a>
            <p className="text-slate-400 text-sm mt-1">{data.author}</p>
          </div>

          {/* Stats row */}
          <div className="flex flex-wrap gap-4">
            <div>
              <div className="text-2xl font-bold text-slate-100 tabular-nums">{formatViews(data.view_count)}</div>
              <div className="text-xs text-slate-500">Views</div>
            </div>
            {data.publish_date && (
              <div>
                <div className="text-sm font-semibold text-slate-200">{formatDate(data.publish_date)}</div>
                <div className="text-xs text-slate-500">Published</div>
              </div>
            )}
            {data.category && (
              <div>
                <div className="text-sm font-semibold text-slate-200">{data.category}</div>
                <div className="text-xs text-slate-500">Category</div>
              </div>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap gap-2">
            <a
              href={data.video_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary text-xs"
            >
              ▶ Watch on YouTube
            </a>
            <CopyButton text={data.video_url} label="Copy Video URL" />
          </div>
        </div>
      </div>

      {/* Description */}
      {data.description && (
        <div className="card space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-300">Description</h3>
            <CopyButton text={data.description} label="Copy" />
          </div>
          <p className="text-slate-400 text-sm whitespace-pre-line leading-relaxed max-h-64 overflow-y-auto">
            {data.description}
          </p>
        </div>
      )}

      {/* Keywords */}
      {data.keywords && data.keywords.length > 0 && (
        <div className="card space-y-3">
          <h3 className="text-sm font-semibold text-slate-300">
            Keywords <span className="text-slate-600 font-normal">({data.keywords.length})</span>
          </h3>
          <div className="flex flex-wrap gap-2">
            {data.keywords.map((kw, i) => (
              <span key={i} className="badge badge-slate text-xs">
                {kw}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Metadata table */}
      <div className="card space-y-3">
        <h3 className="text-sm font-semibold text-slate-300">Video Metadata</h3>
        <div className="divide-y divide-slate-800">
          {[
            ['Video ID',      data.video_id],
            ['Channel ID',    data.channel_id],
            ['Duration',      duration || '—'],
            ['View Count',    data.view_count?.toLocaleString() ?? '—'],
            ['Published',     formatDate(data.publish_date)],
            ['Category',      data.category || '—'],
            ['Live Content',  data.is_live ? 'Yes' : 'No'],
          ].map(([label, val]) => (
            <div key={label} className="flex items-center gap-3 py-2">
              <span className="text-slate-500 text-xs w-28 shrink-0">{label}</span>
              <span className="text-slate-300 text-sm font-mono break-all">{val}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
