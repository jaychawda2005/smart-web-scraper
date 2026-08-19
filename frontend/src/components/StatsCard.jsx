export default function StatsCard({ icon, label, value, color = 'indigo' }) {
  const colorMap = {
    indigo: 'text-indigo-400 bg-indigo-950/50',
    blue:   'text-blue-400 bg-blue-950/50',
    emerald:'text-emerald-400 bg-emerald-950/50',
    amber:  'text-amber-400 bg-amber-950/50',
    rose:   'text-rose-400 bg-rose-950/50',
    violet: 'text-violet-400 bg-violet-950/50',
    sky:    'text-sky-400 bg-sky-950/50',
  };

  return (
    <div className="card flex items-center gap-4 hover:border-slate-700 transition-colors">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg shrink-0 ${colorMap[color] ?? colorMap.indigo}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <div className="text-2xl font-bold text-slate-100 tabular-nums">{value ?? 0}</div>
        <div className="text-xs text-slate-500 mt-0.5 truncate">{label}</div>
      </div>
    </div>
  );
}
