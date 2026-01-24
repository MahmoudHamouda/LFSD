import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Product from './pages/Product';
import HowItWorks from './pages/HowItWorks';
import TrustSafety from './pages/TrustSafety';
import Partners from './pages/Partners';
import Insights from './pages/Insights';
import About from './pages/About';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="product" element={<Product />} />
        <Route path="how-it-works" element={<HowItWorks />} />
        <Route path="trust-safety" element={<TrustSafety />} />
        <Route path="partners" element={<Partners />} />
        <Route path="insights" element={<Insights />} />
        <Route path="about" element={<About />} />
      </Route>
    </Routes>
  );
}

export default App;
