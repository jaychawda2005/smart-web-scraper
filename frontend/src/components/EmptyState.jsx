export default function EmptyState({ title, subtitle, action, onAction }) {
  return (
    <div className="flex flex-col items-center py-14 gap-4 text-center">
      <div className="w-14 h-14 rounded-full bg-slate-800 flex items-center justify-center text-2xl">
        🔍
      </div>
      <div>
        <p className="text-slate-300 font-medium">{title || 'No data found'}</p>
        {subtitle && <p className="text-slate-500 text-sm mt-1 max-w-xs">{subtitle}</p>}
      </div>
      {action && onAction && (
        <button onClick={onAction} className="btn-secondary mt-1">
          {action}
        </button>
      )}
    </div>
  );
}
