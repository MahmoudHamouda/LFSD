import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Header({ onOpenModal }) {
  const location = useLocation();
  
  const navLinks = [
    { name: 'Product', path: '/product' },
    { name: 'How It Works', path: '/how-it-works' },
    { name: 'Trust & Safety', path: '/trust-safety' },
    { name: 'Partners', path: '/partners' },
    { name: 'Insights', path: '/insights' },
    { name: 'About', path: '/about' },
  ];

  return (
    <header className="container" style={{ height: 'var(--header-height)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <Link to="/" style={{ fontSize: '1.5rem', fontWeight: '600', letterSpacing: '-0.02em', color: 'var(--color-primary)' }}>
        HELM
      </Link>
      
      <nav style={{ display: 'flex', gap: '2rem' }} className="desktop-nav">
        {navLinks.map(link => (
          <Link 
            key={link.path} 
            to={link.path}
            style={{ 
              color: location.pathname === link.path ? 'var(--color-text-main)' : 'var(--color-text-muted)',
              fontSize: '0.95rem',
              fontWeight: 500
            }}
          >
            {link.name}
          </Link>
        ))}
      </nav>

      <button onClick={onOpenModal} className="btn btn-primary" style={{ fontSize: '0.9rem', padding: '0.5rem 1.25rem' }}>
        Request access
      </button>
      
      {/* Mobile Menu could go here, omitting for MVP unless requested, sticking to core specs */}
    </header>
  );
}
