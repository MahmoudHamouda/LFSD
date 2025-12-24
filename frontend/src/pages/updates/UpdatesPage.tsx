import React from 'react';

const UpdatesPage: React.FC = () => {
    return (
        <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto' }}>
            <h1>Updates & FAQ</h1>
            <div style={{ marginTop: '20px' }}>
                <h2>Frequently Asked Questions</h2>
                <details style={{ marginBottom: '10px', padding: '10px', border: '1px solid #eee', borderRadius: '4px' }}>
                    <summary style={{ fontWeight: 'bold', cursor: 'pointer' }}>How do I connect my bank?</summary>
                    <p style={{ marginTop: '10px' }}>Go to the sidebar and click "Connect your bank account".</p>
                </details>
                <details style={{ marginBottom: '10px', padding: '10px', border: '1px solid #eee', borderRadius: '4px' }}>
                    <summary style={{ fontWeight: 'bold', cursor: 'pointer' }}>Is my data secure?</summary>
                    <p style={{ marginTop: '10px' }}>Yes, we use bank-grade encryption to protect your data.</p>
                </details>
            </div>
        </div>
    );
};

export default UpdatesPage;
