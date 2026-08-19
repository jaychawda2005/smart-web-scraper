import { useState } from 'react';

const NAV_LINKS = ['Dashboard', 'Results', 'History', 'Analytics'];

export default function Navbar({ activeSection, onNavigate }) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 bg-slate-950/90 backdrop-blur border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
              </svg>
            </div>
            <span className="text-lg font-bold tracking-tight text-white">
              Smart<span className="text-indigo-400">Scrape</span>
            </span>
          </div>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map(link => (
              <button
                key={link}
                onClick={() => onNavigate(link)}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeSection === link
                    ? 'text-indigo-400 bg-indigo-950/60'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                {link}
              </button>
            ))}
          </div>

          {/* CTA + Mobile toggle */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => onNavigate('Dashboard')}
              className="hidden sm:inline-flex btn-primary"
            >
              <span>🚀</span> Start Scraping
            </button>
            <button
              className="md:hidden p-2 rounded-md text-slate-400 hover:text-slate-200"
              onClick={() => setMenuOpen(o => !o)}
              aria-label="Toggle menu"
            >
              {menuOpen ? (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="md:hidden border-t border-slate-800 py-3 space-y-1">
            {NAV_LINKS.map(link => (
              <button
                key={link}
                onClick={() => { onNavigate(link); setMenuOpen(false); }}
                className={`w-full text-left px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeSection === link
                    ? 'text-indigo-400 bg-indigo-950/60'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                {link}
              </button>
            ))}
            <div className="px-4 pt-2">
              <button onClick={() => { onNavigate('Dashboard'); setMenuOpen(false); }} className="btn-primary w-full justify-center">
                🚀 Start Scraping
              </button>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
