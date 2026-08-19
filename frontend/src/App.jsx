import { useState } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';

export default function App() {
  const [activeSection, setActiveSection] = useState('Dashboard');

  return (
    <div className="min-h-screen bg-slate-950">
      <Navbar activeSection={activeSection} onNavigate={setActiveSection} />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Dashboard
          activeSection={activeSection}
          onScrapeSuccess={() => {}}
        />
      </main>
      <footer className="border-t border-slate-800 mt-16 py-6 text-center text-xs text-slate-600">
        SmartScrape — Universal Web Data Extraction &amp; Analytics Platform &nbsp;·&nbsp;
        For educational use with publicly accessible webpages only.
      </footer>
    </div>
  );
}
