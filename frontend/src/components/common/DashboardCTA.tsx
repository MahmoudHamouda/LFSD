import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { redirectToProfile } from '../../utils/navigation';

interface DashboardCTAProps {
    label: string;
    targetTab: 'financial' | 'health' | 'time' | 'account';
    targetAnchor?: string;
    variant?: 'primary' | 'secondary' | 'warning' | 'ghost'; // Added styling variants
    size?: 'sm' | 'md' | 'lg';
    fullWidth?: boolean;
}

const DashboardCTA: React.FC<DashboardCTAProps> = ({
    label,
    targetTab,
    targetAnchor,
    variant = 'secondary',
    size = 'sm',
    fullWidth = false,
}) => {
    const navigate = useNavigate();

    const handleClick = () => {
        redirectToProfile(navigate, targetTab, targetAnchor);
    };

    // Base styles
    const baseStyle: React.CSSProperties = {
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '6px',
        borderRadius: 'var(--radius-md)',
        cursor: 'pointer',
        border: 'none',
        fontWeight: 500,
        transition: 'all 0.2s ease',
        width: fullWidth ? '100%' : 'auto',
    };

    // Variant styles
    const variantStyles: Record<string, React.CSSProperties> = {
        primary: {
            backgroundColor: 'var(--color-primary, #0070f3)',
            color: 'white',
        },
        secondary: {
            backgroundColor: 'var(--bg-card-hover, rgba(255, 255, 255, 0.05))',
            color: 'var(--text-secondary, #808080)',
            border: '1px solid var(--border-color, rgba(255, 255, 255, 0.1))',
        },
        warning: {
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            color: 'var(--color-trend-down, #EF4444)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
        },
        ghost: {
            backgroundColor: 'transparent',
            color: 'var(--text-secondary, #808080)',
            padding: 0,
        }
    };

    // Size styles
    const sizeStyles: Record<string, React.CSSProperties> = {
        sm: {
            padding: '6px 12px',
            fontSize: '13px',
        },
        md: {
            padding: '8px 16px',
            fontSize: '14px',
        },
        lg: {
            padding: '12px 24px',
            fontSize: '16px',
        },
    };

    if (variant === 'ghost') {
        sizeStyles.sm = { fontSize: '12px' }; // minimal styling for ghost
    }


    return (
        <button
            onClick={handleClick}
            style={{
                ...baseStyle,
                ...variantStyles[variant],
                ...sizeStyles[size],
            }}
            onMouseEnter={(e) => {
                if (variant === 'secondary') {
                    e.currentTarget.style.backgroundColor = 'var(--bg-hover, rgba(255, 255, 255, 0.1))';
                    e.currentTarget.style.color = 'var(--text-primary)';
                }
            }}
            onMouseLeave={(e) => {
                if (variant === 'secondary') {
                    e.currentTarget.style.backgroundColor = 'var(--bg-card-hover, rgba(255, 255, 255, 0.05))';
                    e.currentTarget.style.color = 'var(--text-secondary, #808080)';
                }
            }}
        >
            {label}
            {variant !== 'ghost' && <ArrowRight size={14} />}
        </button>
    );
};

export default DashboardCTA;
