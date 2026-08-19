import { useState, useEffect } from 'react';
import SearchBar from './SearchBar';
import CopyButton from './CopyButton';
import DataTable from './DataTable';
import EmptyState from './EmptyState';
import YoutubePanel from './YoutubePanel';

const TAG_COLORS = {
  h1: 'bg-indigo-900/50 text-indigo-300 border-indigo-800/50',
  h2: 'bg-blue-900/50 text-blue-300 border-blue-800/50',
  h3: 'bg-sky-900/50 text-sky-300 border-sky-800/50',
  h4: 'bg-teal-900/50 text-teal-300 border-teal-800/50',
  h5: 'bg-green-900/50 text-green-300 border-green-800/50',
  h6: 'bg-slate-800 text-slate-400 border-slate-700',
};

const ALL_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'];

/* ─── Overview ─────────────────────────────────────── */
function OverviewTab({ data }) {
  const pi = data.page_info;
  if (!pi) return <EmptyState title="Page info was not requested." />;
  return (
    <div className="space-y-4">
      <div className="card space-y-3">
        <h3 className="text-sm font-semibold text-slate-300">Page Details</h3>
        {[
          ['Title', pi.title || '(no title)'],
          ['URL', pi.url],
          ['HTTP Status', <span className={pi.status_code === 200 ? 'text-emerald-400' : 'text-amber-400'}>{pi.status_code}</span>],
        ].map(([label, val]) => (
          <div key={label} className="flex items-start gap-3">
            <span className="text-slate-500 text-xs w-20 shrink-0 pt-0.5">{label}</span>
            <span className="text-slate-200 text-sm break-all">{val}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Text ──────────────────────────────────────────── */
function TextTab({ items = [] }) {
  const [search, setSearch] = useState('');
  const filtered = search ? items.filter(t => t.toLowerCase().includes(search.toLowerCase())) : items;
  if (!items.length) return <EmptyState title="No text blocks extracted." subtitle="Select 'Text' in extraction options." />;
  return (
    <div className="space-y-3">
      <SearchBar value={search} onChange={setSearch} placeholder="Search text…" count={`${filtered.length}/${items.length}`} />
      {filtered.length === 0 ? (
        <EmptyState title="No matching text." action="Clear Search" onAction={() => setSearch('')} />
      ) : (
        <div className="space-y-2">
          {filtered.map((text, i) => (
            <div key={i} className="group flex items-start gap-3 p-3 bg-slate-900 rounded-lg border border-slate-800 hover:border-slate-700">
              <p className="text-slate-300 text-sm flex-1 break-words">{text}</p>
              <div className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                <CopyButton text={text} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─── Headings ──────────────────────────────────────── */
function HeadingsTab({ items = [] }) {
  const [activeFilter, setActiveFilter] = useState('all');
  if (!items.length) return <EmptyState title="No headings extracted." />;

  const presentTags = [...new Set(items.map(h => h.tag))];
  const filtered = activeFilter === 'all' ? items : items.filter(h => h.tag === activeFilter);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setActiveFilter('all')}
          className={`tab-btn ${activeFilter === 'all' ? 'tab-btn-active' : 'tab-btn-inactive'}`}
        >All ({items.length})</button>
        {ALL_TAGS.filter(t => presentTags.includes(t)).map(tag => (
          <button
            key={tag}
            onClick={() => setActiveFilter(tag)}
            className={`tab-btn ${activeFilter === tag ? 'tab-btn-active' : 'tab-btn-inactive'} uppercase text-xs`}
          >
            {tag} ({items.filter(h => h.tag === tag).length})
          </button>
        ))}
      </div>
      <div className="space-y-2">
        {filtered.map((h, i) => (
          <div key={i} className="group flex items-center gap-3 p-3 bg-slate-900 rounded-lg border border-slate-800 hover:border-slate-700">
            <span className={`badge border text-xs font-bold w-8 justify-center ${TAG_COLORS[h.tag] || TAG_COLORS.h6}`}>
              {h.tag.toUpperCase()}
            </span>
            <p className="text-slate-200 text-sm flex-1">{h.text}</p>
            <div className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
              <CopyButton text={h.text} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Links ─────────────────────────────────────────── */
function LinksTab({ items = [] }) {
  const [search, setSearch] = useState('');
  if (!items.length) return <EmptyState title="No links extracted." />;
  const filtered = search
    ? items.filter(l => l.text.toLowerCase().includes(search.toLowerCase()) || l.url.toLowerCase().includes(search.toLowerCase()))
    : items;

  return (
    <div className="space-y-3">
      <SearchBar value={search} onChange={setSearch} placeholder="Search links…" count={`${filtered.length}/${items.length}`} />
      {filtered.length === 0 ? (
        <EmptyState title="No matching links." action="Clear Search" onAction={() => setSearch('')} />
      ) : (
        <div className="space-y-2">
          {filtered.map((link, i) => (
            <div key={i} className="group flex items-center gap-3 p-3 bg-slate-900 rounded-lg border border-slate-800 hover:border-slate-700">
              <div className="w-7 h-7 rounded-md bg-slate-800 flex items-center justify-center text-sm shrink-0">🔗</div>
              <div className="flex-1 min-w-0">
                <p className="text-slate-200 text-sm font-medium truncate">{link.text}</p>
                <p className="text-slate-500 text-xs truncate mt-0.5">{link.url}</p>
              </div>
              <div className="flex gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                <CopyButton text={link.url} label="Copy URL" />
                <a
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-ghost"
                  title="Open in new tab"
                >Open ↗</a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─── Images ────────────────────────────────────────── */
function ImagesTab({ items = [] }) {
  if (!items.length) return <EmptyState title="No images extracted." />;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {items.map((img, i) => (
        <div key={i} className="group card p-3 flex flex-col gap-2 hover:border-slate-700">
          <div className="h-36 bg-slate-950 rounded-md overflow-hidden flex items-center justify-center">
            <img
              src={img.url}
              alt={img.alt || '(no alt)'}
              className="max-h-full max-w-full object-contain"
              onError={e => {
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'flex';
              }}
            />
            <div style={{ display: 'none' }} className="text-slate-600 text-xs flex-col items-center gap-1">
              <span className="text-2xl">🖼️</span>
              <span>Image unavailable</span>
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-slate-400 text-xs truncate" title={img.alt}>{img.alt || '(no alt text)'}</p>
            <p className="text-slate-600 text-xs truncate mt-0.5" title={img.url}>{img.url}</p>
          </div>
          <div className="flex gap-1">
            <CopyButton text={img.url} label="Copy URL" />
            <a href={img.url} target="_blank" rel="noopener noreferrer" className="btn-ghost">Open ↗</a>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ─── Tables ────────────────────────────────────────── */
function TablesTab({ items = [] }) {
  const [activeIdx, setActiveIdx] = useState(0);
  if (!items.length) return <EmptyState title="No tables extracted." />;
  const tbl = items[activeIdx] || items[0];
  return (
    <div className="space-y-3">
      {items.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {items.map((_, i) => (
            <button
              key={i}
              onClick={() => setActiveIdx(i)}
              className={`tab-btn whitespace-nowrap ${activeIdx === i ? 'tab-btn-active' : 'tab-btn-inactive'}`}
            >
              Table {i + 1}
            </button>
          ))}
        </div>
      )}
      <DataTable headers={tbl.headers} rows={tbl.rows} />
    </div>
  );
}

/* ─── Lists ─────────────────────────────────────────── */
function ListsTab({ items = [] }) {
  if (!items.length) return <EmptyState title="No lists extracted." />;
  return (
    <div className="space-y-4">
      {items.map((list, i) => (
        <div key={i} className="card">
          <div className="flex items-center gap-2 mb-3">
            <span className="badge badge-slate">{list.list_type === 'ordered' ? '1. Ordered' : '• Unordered'}</span>
            <span className="text-xs text-slate-500">{list.items.length} items</span>
          </div>
          {list.list_type === 'ordered' ? (
            <ol className="space-y-1.5 list-decimal list-inside">
              {list.items.map((item, j) => (
                <li key={j} className="text-slate-300 text-sm">{item}</li>
              ))}
            </ol>
          ) : (
            <ul className="space-y-1.5 list-disc list-inside">
              {list.items.map((item, j) => (
                <li key={j} className="text-slate-300 text-sm">{item}</li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
}

/* ─── Main ResultsTabs ──────────────────────────────── */
const TABS = [
  { key: 'youtube',  label: 'YouTube',     icon: '▶️' },
  { key: 'overview', label: 'Overview',    icon: '📄' },
  { key: 'text',     label: 'Text',        icon: '📝' },
  { key: 'headings', label: 'Headings',    icon: '🔤' },
  { key: 'links',    label: 'Links',       icon: '🔗' },
  { key: 'images',   label: 'Images',      icon: '🖼️' },
  { key: 'tables',   label: 'Tables',      icon: '📊' },
  { key: 'lists',    label: 'Lists',       icon: '📋' },
];

export default function ResultsTabs({ data }) {
  const [active, setActive] = useState('overview');

  function hasData(key) {
    if (key === 'overview') return !!data.page_info;
    if (key === 'youtube')  return !!data.youtube_data;
    const val = data[key];
    return Array.isArray(val) && val.length > 0;
  }

  const availableTabs = TABS.filter(t => hasData(t.key));

  // Reset active tab when data changes and current tab has no data
  useEffect(() => {
    if (!availableTabs.find(t => t.key === active) && availableTabs.length) {
      setActive(availableTabs[0].key);
    }
  }, [data]); // eslint-disable-line react-hooks/exhaustive-deps

  function countLabel(key) {
    if (key === 'overview') return '';
    const val = data[key];
    return Array.isArray(val) ? ` (${val.length})` : '';
  }

  return (
    <div className="space-y-4">
      {/* Tab bar */}
      <div className="flex gap-1 overflow-x-auto pb-1">
        {TABS.map(({ key, label, icon }) => (
          <button
            key={key}
            onClick={() => setActive(key)}
            className={`tab-btn flex items-center gap-1.5 ${active === key ? 'tab-btn-active' : 'tab-btn-inactive'} ${!hasData(key) ? 'opacity-30 cursor-not-allowed' : ''}`}
            disabled={!hasData(key)}
          >
            <span>{icon}</span>
            {label}{countLabel(key)}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {active === 'youtube'   && <YoutubePanel data={data.youtube_data} />}
        {active === 'overview'  && <OverviewTab data={data} />}
        {active === 'text'      && <TextTab items={data.text || []} />}
        {active === 'headings'  && <HeadingsTab items={data.headings || []} />}
        {active === 'links'     && <LinksTab items={data.links || []} />}
        {active === 'images'    && <ImagesTab items={data.images || []} />}
        {active === 'tables'    && <TablesTab items={data.tables || []} />}
        {active === 'lists'     && <ListsTab items={data.lists || []} />}
      </div>
    </div>
  );
}
