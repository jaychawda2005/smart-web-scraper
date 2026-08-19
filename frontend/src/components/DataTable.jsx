import { useState } from 'react';
import SearchBar from './SearchBar';
import CopyButton from './CopyButton';
import EmptyState from './EmptyState';

export default function DataTable({ headers = [], rows = [], searchable = true }) {
  const [search, setSearch] = useState('');

  const filtered = search.trim()
    ? rows.filter(row =>
        row.some(cell => String(cell).toLowerCase().includes(search.toLowerCase()))
      )
    : rows;

  if (!rows.length) {
    return <EmptyState title="No table data found" subtitle="This table appears to be empty." />;
  }

  return (
    <div className="space-y-3">
      {searchable && (
        <SearchBar
          value={search}
          onChange={setSearch}
          placeholder="Search table…"
          count={`${filtered.length}/${rows.length}`}
        />
      )}
      <div className="overflow-x-auto rounded-lg border border-slate-800">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-900/80">
              {headers.map((h, i) => (
                <th
                  key={i}
                  className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap"
                >
                  {h || `Column ${i + 1}`}
                </th>
              ))}
              {headers.length === 0 && (
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400">Data</th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={headers.length || 1} className="px-4 py-8 text-center text-slate-500 text-sm">
                  No matching rows.
                </td>
              </tr>
            ) : (
              filtered.map((row, ri) => (
                <tr key={ri} className="hover:bg-slate-800/30 transition-colors">
                  {row.map((cell, ci) => (
                    <td key={ci} className="px-4 py-2.5 text-slate-300 max-w-xs">
                      <span className="block truncate" title={String(cell)}>{String(cell)}</span>
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {rows.length > 0 && (
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>Showing {filtered.length} of {rows.length} rows</span>
          <CopyButton
            text={[headers.join('\t'), ...filtered.map(r => r.join('\t'))].join('\n')}
            label="Copy Table"
          />
        </div>
      )}
    </div>
  );
}
