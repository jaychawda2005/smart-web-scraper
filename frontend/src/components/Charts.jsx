import {
  BarChart, Bar, PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  XAxis, YAxis, CartesianGrid, Legend,
} from 'recharts';

const COLORS = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#f97316'];

function NoData({ message = 'Not enough data to display chart.' }) {
  return (
    <div className="flex items-center justify-center h-40 text-slate-500 text-sm">
      {message}
    </div>
  );
}

/** Content type distribution — Pie chart */
export function ContentDistributionChart({ data }) {
  const items = [
    { name: 'Headings', value: data.headings_count  || 0 },
    { name: 'Text',     value: data.text_blocks_count || 0 },
    { name: 'Links',    value: data.links_count     || 0 },
    { name: 'Images',   value: data.images_count    || 0 },
    { name: 'Tables',   value: data.tables_count    || 0 },
    { name: 'Lists',    value: data.lists_count     || 0 },
  ].filter(d => d.value > 0);

  if (items.length === 0) return <NoData />;

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-slate-200 mb-4">Content Distribution</h3>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            data={items}
            cx="50%"
            cy="50%"
            outerRadius={90}
            dataKey="value"
            nameKey="name"
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            labelLine={false}
          >
            {items.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#e2e8f0' }}
            itemStyle={{ color: '#e2e8f0' }}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Heading distribution — Bar chart */
export function HeadingDistributionChart({ headings = [] }) {
  if (!headings.length) return (
    <div className="card">
      <h3 className="text-sm font-semibold text-slate-200 mb-4">Heading Distribution</h3>
      <NoData message="No headings were extracted." />
    </div>
  );

  const counts = { h1: 0, h2: 0, h3: 0, h4: 0, h5: 0, h6: 0 };
  headings.forEach(h => {
    if (counts[h.tag] !== undefined) counts[h.tag]++;
  });

  const barData = Object.entries(counts).map(([tag, count]) => ({
    tag: tag.toUpperCase(), count,
  })).filter(d => d.count > 0);

  if (!barData.length) return (
    <div className="card">
      <h3 className="text-sm font-semibold text-slate-200 mb-4">Heading Distribution</h3>
      <NoData />
    </div>
  );

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-slate-200 mb-4">Heading Distribution</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={barData} margin={{ top: 4, right: 10, left: -20, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="tag" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
          <Tooltip
            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#e2e8f0' }}
            itemStyle={{ color: '#6366f1' }}
            cursor={{ fill: 'rgba(99,102,241,0.1)' }}
          />
          <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
