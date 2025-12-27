
export const getStoredTheme = (): 'light' | 'dark' => {
    const stored = localStorage.getItem('theme');
    if (stored === 'light' || stored === 'dark') return stored;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

export const setStoredTheme = (theme: 'light' | 'dark') => {
    localStorage.setItem('theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
};

export const initTheme = () => {
    const theme = getStoredTheme();
    document.documentElement.setAttribute('data-theme', theme);
};
