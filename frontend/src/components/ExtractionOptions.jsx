const OPTIONS = [
  { key: 'page_info', label: 'Page Information', icon: '📄' },
  { key: 'headings',  label: 'Headings',         icon: '🔤' },
  { key: 'text',      label: 'Text',              icon: '📝' },
  { key: 'links',     label: 'Links',             icon: '🔗' },
  { key: 'images',    label: 'Images',            icon: '🖼️' },
  { key: 'tables',    label: 'Tables',            icon: '📊' },
  { key: 'lists',     label: 'Lists',             icon: '📋' },
];

export default function ExtractionOptions({ options, onChange, disabled }) {
  function toggle(key) {
    onChange({ ...options, [key]: !options[key] });
  }

  function selectAll() {
    const all = {};
    OPTIONS.forEach(o => (all[o.key] = true));
    onChange(all);
  }

  function clearAll() {
    const none = {};
    OPTIONS.forEach(o => (none[o.key] = false));
    onChange(none);
  }

  const selectedCount = Object.values(options).filter(Boolean).length;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-medium text-slate-200">Extraction Options</h3>
          <p className="text-xs text-slate-500 mt-0.5">{selectedCount} of {OPTIONS.length} selected</p>
        </div>
        <div className="flex gap-2">
          <button onClick={selectAll} disabled={disabled} className="btn-ghost">Select All</button>
          <button onClick={clearAll} disabled={disabled} className="btn-ghost">Clear All</button>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {OPTIONS.map(({ key, label, icon }) => {
          const checked = !!options[key];
          return (
            <button
              key={key}
              onClick={() => toggle(key)}
              disabled={disabled}
              className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium border transition-all duration-150 text-left ${
                checked
                  ? 'bg-indigo-950/60 border-indigo-700 text-indigo-300'
                  : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-600 hover:text-slate-300'
              } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <span>{icon}</span>
              <span className="truncate">{label}</span>
              {checked && (
                <svg className="w-3.5 h-3.5 ml-auto shrink-0 text-indigo-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          );
        })}
      </div>

      {selectedCount === 0 && (
        <p className="mt-2 text-xs text-amber-400 flex items-center gap-1">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Select at least one extraction option
        </p>
      )}
    </div>
  );
}
