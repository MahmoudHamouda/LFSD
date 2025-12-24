import React from 'react';
import { useParams } from 'react-router-dom';

const ConnectPage: React.FC = () => {
    const { type } = useParams<{ type: string }>();

    const getTitle = () => {
        switch (type) {
            case 'bank': return 'Connect Bank Account';
            case 'statements': return 'Upload Bank Statements';
            case 'social': return 'Connect Social Accounts';
            case 'calendar': return 'Connect Calendar';
            default: return 'Connect Service';
        }
    };

    return (
        <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto' }}>
            <h1>{getTitle()}</h1>
            <p>This feature is currently under development.</p>
            <div style={{
                marginTop: '20px',
                padding: '20px',
                border: '1px dashed #ccc',
                borderRadius: '8px',
                textAlign: 'center',
                backgroundColor: '#f9f9f9'
            }}>
                Placeholder for {type} integration
            </div>
        </div>
    );
};

export default ConnectPage;
