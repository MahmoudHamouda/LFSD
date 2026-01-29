import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle2, Shield } from 'lucide-react';

const Home = () => {
  return (
    <div className="home">
      {/* Hero Section */}
      <section className="section container text-center">
        <div className="hero-glow"></div>
        <h1 style={{ maxWidth: '800px', margin: '0 auto' }}>
          Helmory builds consumer software for a calmer, more capable life.
        </h1>
        <p style={{ margin: '1.5rem auto' }}>
          Productivity, personal finance, and lifestyle — designed to work together.
          We build tools that help people make better decisions and follow through with less effort.
        </p>
        <div className="flex justify-center gap-sm" style={{ marginTop: '2rem' }}>
          <Link to="/helm" className="btn btn-primary">
            Explore HELM
          </Link>
          <a href="https://app.helmory.com/login?returnTo=%2Fsignup" className="btn btn-ghost">Sign up</a>
        </div>
      </section>

      {/* Featured Service: HELM */}
      <section className="container">
        <div className="surface-1">
          <div className="grid grid-cols-2 gap-lg items-center">
            <div>
              <span style={{
                textTransform: 'uppercase',
                fontSize: '0.875rem',
                letterSpacing: '0.05em',
                color: 'var(--color-text-muted)',
                fontWeight: 600
              }}>Core Product</span>
              <h2 style={{ marginTop: '0.5rem' }}>HELM</h2>
              <p>
                It helps you understand your money, time, and choices — and turn that into clear, practical actions.
              </p>

              <ul style={{ listStyle: 'none', margin: '2rem 0' }}>
                {[
                  "See patterns without spreadsheets",
                  "Make trade-offs with less stress",
                  "Act when you're ready — not when you're pressured"
                ].map((item, i) => (
                  <li key={i} className="flex items-center gap-sm" style={{ marginBottom: '0.75rem', color: 'var(--color-text-muted)' }}>
                    <CheckCircle2 size={20} color="var(--color-text-main)" />
                    {item}
                  </li>
                ))}
              </ul>

              <Link to="/helm" className="btn btn-primary">
                See how HELM works <ArrowRight size={18} style={{ marginLeft: '0.5rem' }} />
              </Link>
            </div>

            {/* Screenshot Stack Placeholder - will replace with real image */}
            <div style={{ position: 'relative', height: '400px' }}>
              <div className="card" style={{
                position: 'absolute',
                top: 0,
                right: 0,
                width: '80%',
                height: '300px',
                zIndex: 2,
                backgroundImage: 'url(/screenshots/dashboard_mobile.png)',
                backgroundSize: 'cover',
                backgroundPosition: 'top'
              }}></div>
              <div className="card" style={{
                position: 'absolute',
                top: '40px',
                right: '40px',
                width: '80%',
                height: '300px',
                zIndex: 1,
                opacity: 0.7,
                backgroundImage: 'url(/screenshots/spending_mobile.png)',
                backgroundSize: 'cover',
                backgroundPosition: 'top'
              }}></div>
            </div>
          </div>
        </div>
      </section>

      {/* What We Build */}
      <section className="section container">
        <h2 className="text-center">What we build</h2>
        <div className="grid grid-cols-3 gap-md" style={{ marginTop: '3rem' }}>
          {[
            {
              title: "Productivity",
              desc: "Plan, prioritize, and follow through."
            },
            {
              title: "Personal Finance",
              desc: "Understand spending, habits, commitments."
            },
            {
              title: "Lifestyle Management",
              desc: "Make life logistics easier (when you choose)."
            }
          ].map((card, i) => (
            <div key={i} className="card">
              <h3>{card.title}</h3>
              <p style={{ marginBottom: 0 }}>{card.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Trust Strip */}
      <section className="container" style={{ marginBottom: '4rem' }}>
        <div className="surface-1 flex items-center justify-between" style={{ padding: '2rem 3rem' }}>
          <div className="flex items-center gap-md">
            <Shield size={32} />
            <div>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>Built with privacy, security, and restraint.</h3>
              <p style={{ marginBottom: 0, fontSize: '1rem' }}>You stay in control of your data and decisions.</p>
            </div>
          </div>
          <Link to="/trust" className="btn btn-ghost" style={{ background: 'white' }}>Read our approach</Link>
        </div>
      </section>
    </div>
  );
};

export default Home;
