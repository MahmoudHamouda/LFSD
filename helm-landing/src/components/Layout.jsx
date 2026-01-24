import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Header from './Header';
import Footer from './Footer';
import RequestAccessModal from './RequestAccessModal';

export default function Layout() {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const { pathname } = useLocation();

    useEffect(() => {
        window.scrollTo(0, 0);
    }, [pathname]);

    const openModal = () => setIsModalOpen(true);
    const closeModal = () => setIsModalOpen(false);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <Header onOpenModal={openModal} />
            <main style={{ flex: 1 }}>
                <Outlet context={{ openModal }} />
            </main>
            <Footer />
            <RequestAccessModal isOpen={isModalOpen} onClose={closeModal} />
        </div>
    );
}
