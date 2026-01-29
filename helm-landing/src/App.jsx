import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Menu, X } from 'lucide-react';

// Pages
import Home from './pages/Home';
import HelmProduct from './pages/HelmProduct';
import Products from './pages/Products';
import Trust from './pages/Trust';
import About from './pages/About';

function App() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <Router>
      <div className="app-layout">
        <header style={{ height: 'var(--header-height)', borderBottom: '1px solid var(--color-border)', background: 'rgba(255,255,255,0.8)', backdropFilter: 'blur(10px)', position: 'sticky', top: 0, zIndex: 100 }}>
          <div className="container flex items-center justify-between" style={{ height: '100%' }}>
            <Link to="/" style={{ fontWeight: 700, fontSize: '1.25rem' }}>Helmory</Link>

            {/* Desktop Nav */}
            <nav className="desktop-nav flex items-center gap-md" style={{ display: 'none' }}>
              <style>{`@media(min-width: 768px) { .desktop-nav { display: flex !important; } .mobile-btn { display: none !important; } }`}</style>
              <Link to="/helm">HELM</Link>
              <Link to="/products">Products</Link>
              <Link to="/trust">Trust</Link>
              <Link to="/about">About</Link>
            </nav>

            <div className="desktop-nav flex items-center gap-sm">
              <a href="https://app.helmory.com/login" className="btn btn-ghost">Log in</a>
              <a href="https://app.helmory.com/signup" className="btn btn-primary">Sign up</a>
            </div>

            {/* Mobile Menu Btn */}
            <button className="mobile-btn" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
              {mobileMenuOpen ? <X /> : <Menu />}
            </button>
          </div>
        </header>

        {/* Mobile Menu Overlay */}
        {mobileMenuOpen && (
          <div style={{ position: 'fixed', inset: '80px 0 0 0', background: 'white', zIndex: 90, padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <Link to="/helm" onClick={() => setMobileMenuOpen(false)}>HELM</Link>
            <Link to="/products" onClick={() => setMobileMenuOpen(false)}>Products</Link>
            <Link to="/trust" onClick={() => setMobileMenuOpen(false)}>Trust</Link>
            <Link to="/about" onClick={() => setMobileMenuOpen(false)}>About</Link>
            <hr style={{ border: 0, borderTop: '1px solid var(--color-border)' }} />
            <a href="https://app.helmory.com/login" className="btn btn-ghost" style={{ justifyContent: 'flex-start' }}>Log in</a>
            <a href="https://app.helmory.com/signup" className="btn btn-primary">Sign up</a>
          </div>
        )}

        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/helm" element={<HelmProduct />} />
            <Route path="/products" element={<Products />} />
            <Route path="/trust" element={<Trust />} />
            <Route path="/about" element={<About />} />
            <Route path="*" element={<Home />} />
          </Routes>
        </main>

        <footer className="container section" style={{ borderTop: '1px solid var(--color-border)', marginTop: '4rem', paddingBottom: '2rem' }}>
          <div className="grid grid-cols-2 gap-lg" style={{ marginBottom: '2rem' }}>
            <div>
              <h3>Helmory</h3>
              <p style={{ fontSize: '0.875rem' }}>Consumer software for a calmer life.</p>
            </div>
            <div className="flex gap-md" style={{ alignItems: 'flex-start', flexWrap: 'wrap' }}>
              <div className="flex flex-col gap-sm">
                <strong>Company</strong>
                <Link to="/about">About</Link>
                <Link to="/trust">Trust</Link>
                <Link to="/contact">Contact</Link>
              </div>
              <div className="flex flex-col gap-sm">
                <strong>Products</strong>
                <Link to="/helm">HELM</Link>
              </div>
            </div>
          </div>
          <div style={{ fontSize: '0.875rem', color: 'var(--color-text-light)' }}>
            © {new Date().getFullYear()} Helmory, Corp.
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
