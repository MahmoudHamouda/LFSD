/**
 * Auth0 Wrapper Component
 * Provides Auth0 context to the application
 */
import React, { ReactNode } from 'react';
import { Auth0Provider } from '@auth0/auth0-react';

interface Auth0WrapperProps {
    children: ReactNode;
}

export const Auth0Wrapper: React.FC<Auth0WrapperProps> = ({ children }) => {
    const domain = 'dev-lmc05ou12e7ep05p.eu.auth0.com';
    const clientId = 'VVw94DZQITVcARsNlp4JEZkyzMjsgioF';
    const audience = 'https://dev-lmc05ou12e7ep05p.eu.auth0.com/api/v2/';

    // Determine redirect URI based on environment
    const redirectUri = window.location.origin + '/callback';

    return (
        <Auth0Provider
            domain={domain}
            clientId={clientId}
            authorizationParams={{
                redirect_uri: redirectUri,
                audience: audience,
            }}
            cacheLocation="localstorage"
        >
            {children}
        </Auth0Provider>
    );
};
