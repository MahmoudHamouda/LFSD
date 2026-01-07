/**
 * Auth0 Configuration
 * Fetches Auth0 config from backend
 */

export interface Auth0Config {
  domain: string;
  clientId: string;
  audience: string;
}

let cachedConfig: Auth0Config | null = null;

export async function getAuth0Config(): Promise<Auth0Config> {
  if (cachedConfig) {
    return cachedConfig;
  }

  try {
    const response = await fetch('/api/auth/config');
    if (!response.ok) {
      throw new Error(`Failed to fetch Auth0 config: ${response.statusText}`);
    }
    
    cachedConfig = await response.json();
    return cachedConfig;
  } catch (error) {
    console.error('Error fetching Auth0 config:', error);
    // Fallback to default config
    return {
      domain: 'dev-lmc05ou12e7ep05p.eu.auth0.com',
      clientId: 'VVw94DZQITVcARsNlp4JEZkyzMjsgioF',
      audience: 'https://dev-lmc05ou12e7ep05p.eu.auth0.com/api/v2/'
    };
  }
}
