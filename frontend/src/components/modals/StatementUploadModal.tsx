import React, { useState, useRef } from 'react';
import { uploadStatement } from '../../api/financialApi';
import styles from './ConnectionModal.module.css'; // Reuse styles for consistency

interface StatementUploadModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const StatementUploadModal: React.FC<StatementUploadModalProps> = ({ isOpen, onClose }) => {
    const [file, setFile] = useState<File | null>(null);
    const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
    const [errorMessage, setErrorMessage] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);

    if (!isOpen) return null;

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setStatus('idle');
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setStatus('uploading');
        try {
            await uploadStatement(file);
            setStatus('success');
            setTimeout(() => {
                onClose();
                setStatus('idle');
                setFile(null);
            }, 2000); // Close after success
        } catch (error) {
            setStatus('error');
            setErrorMessage('Failed to upload statement. Please try again.');
        }
    };


    return (
        <div className={styles.overlay} onClick={onClose}>
            <div className={styles.modal} onClick={e => e.stopPropagation()} style={{ maxWidth: '500px', backgroundColor: '#1E1E1E', color: '#FFFFFF' }}>
                <div className={styles.header} style={{ padding: '20px 24px', borderBottom: '1px solid #333' }}>
                    <div className={styles.titleContainer}>
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: '#E0E0E0' }}>
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                            <line x1="16" y1="13" x2="8" y2="13"></line>
                            <line x1="16" y1="17" x2="8" y2="17"></line>
                            <polyline points="10 9 9 9 8 9"></polyline>
                        </svg>
                        <h2 className={styles.title} style={{ fontSize: '18px', fontWeight: 600 }}>Upload Bank Statement</h2>
                    </div>
                    <button className={styles.closeButton} onClick={onClose}>✕</button>
                </div>

                <div className={styles.content} style={{ padding: '32px 24px' }}>
                    <p className={styles.description} style={{ color: '#AAAAAA', fontSize: '14px', marginBottom: '32px', lineHeight: '1.5' }}>
                        Upload your PDF bank statement to automatically analyze income, expenses, and recurring bills.
                    </p>

                    {status === 'success' ? (
                        <div style={{ padding: '40px 20px', textAlign: 'center' }}>
                            <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'rgba(0, 200, 83, 0.1)', color: '#00C853', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="20 6 9 17 4 12"></polyline>
                                </svg>
                            </div>
                            <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#FFF', marginBottom: '8px' }}>Upload Complete!</h3>
                            <p style={{ color: '#888', fontSize: '14px' }}>We are analyzing your transactions...</p>
                        </div>
                    ) : (
                        <div
                            style={{
                                border: '1px dashed #444',
                                borderRadius: '8px',
                                padding: '48px 20px',
                                textAlign: 'center',
                                cursor: 'pointer',
                                background: '#252525',
                                transition: 'all 0.2s',
                            }}
                            onClick={() => fileInputRef.current?.click()}
                            onMouseEnter={e => { e.currentTarget.style.borderColor = '#666'; e.currentTarget.style.background = '#2A2A2A'; }}
                            onMouseLeave={e => { e.currentTarget.style.borderColor = '#444'; e.currentTarget.style.background = '#252525'; }}
                        >
                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleFileChange}
                                style={{ display: 'none' }}
                                accept=".pdf"
                            />
                            {file ? (
                                <div>
                                    <div style={{ width: '40px', height: '40px', margin: '0 auto 12px', color: '#E0E0E0' }}>
                                        <svg width="100%" height="100%" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                            <polyline points="14 2 14 8 20 8"></polyline>
                                            <line x1="12" y1="18" x2="12" y2="12"></line>
                                            <line x1="9" y1="15" x2="15" y2="15"></line>
                                        </svg>
                                    </div>
                                    <p style={{ fontWeight: 500, color: '#FFF', marginBottom: '4px' }}>{file.name}</p>
                                    <p style={{ fontSize: '13px', color: '#888' }}>Click to replace file</p>
                                </div>
                            ) : (
                                <div>
                                    <div style={{ width: '48px', height: '48px', margin: '0 auto 16px', opacity: 0.8 }}>
                                        {/* Cloud Icon */}
                                        <svg width="100%" height="100%" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: '#E0E0E0' }}>
                                            <path d="M21.2 15c.7-1.2 1-2.5.7-3.9-.6-2-2.4-3.5-4.4-3.5h-1.2c-.5-3.2-3.2-5.6-6.4-5.6-3.7 0-6.7 2.9-6.9 6.6-.1.2-.1.5-.1.7C1.4 10.6.5 13.2 1.8 15.6c.9 1.7 2.7 2.9 4.7 2.9h12c1.4 0 2.7-.6 3.7-1.5"></path>
                                        </svg>
                                    </div>
                                    <p style={{ fontSize: '16px', color: '#FFF', fontWeight: 500 }}>
                                        Click to select PDF or drag and drop
                                    </p>
                                </div>
                            )}
                        </div>
                    )}

                    {status === 'error' && (
                        <div style={{ color: '#FF5252', marginTop: '16px', fontSize: '13px', textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="12" cy="12" r="10"></circle>
                                <line x1="12" y1="8" x2="12" y2="12"></line>
                                <line x1="12" y1="16" x2="12.01" y2="16"></line>
                            </svg>
                            {errorMessage}
                        </div>
                    )}
                </div>

                <div className={styles.footer} style={{ backgroundColor: '#1E1E1E', padding: '20px 24px', borderTop: '1px solid #333' }}>
                    <button
                        className={styles.cancelButton}
                        onClick={onClose}
                        style={{ padding: '10px 20px', borderRadius: '6px', fontSize: '14px', background: 'transparent', color: '#AAA', border: '1px solid #444', marginRight: '12px' }}
                    >
                        Cancel
                    </button>
                    {status !== 'success' && (
                        <button
                            className={styles.primaryButton}
                            onClick={handleUpload}
                            disabled={!file || status === 'uploading'}
                            style={{
                                padding: '10px 20px',
                                borderRadius: '6px',
                                fontSize: '14px',
                                fontWeight: 500,
                                background: (!file || status === 'uploading') ? '#444' : '#FFF',
                                color: (!file || status === 'uploading') ? '#888' : '#000',
                                border: 'none',
                                cursor: (!file || status === 'uploading') ? 'not-allowed' : 'pointer'
                            }}
                        >
                            {status === 'uploading' ? 'Uploading...' : 'Upload & Analyze'}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default StatementUploadModal;
