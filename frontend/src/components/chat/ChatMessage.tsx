import React, { useState, useEffect } from 'react';
import styles from './ChatMessage.module.css';
import helmH from '../../assets/brand/helm/helm_final_h.svg';
import RideOptions from './RideOptions';
import FinancialSummary from './FinancialSummary';
import TradeoffCard from './TradeoffCard';
import { bookRide } from '../../api/api';

interface ChatMessageProps {
    role: 'user' | 'assistant';
    content: string;
    onSend?: (message: string) => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ role, content, onSend }) => {
    const [parsedContent, setParsedContent] = useState<any>(null);
    const [isCollapsed, setIsCollapsed] = useState(false);

    useEffect(() => {
        if (role === 'assistant') {
            try {
                // Attempt to parse JSON content if it looks like JSON
                if (content.trim().startsWith('{') || content.trim().startsWith('[')) {
                    const parsed = JSON.parse(content);
                    setParsedContent(parsed);
                    // Collapse logic for structured content if needed, currently mostly for text
                    if (parsed.type === 'text' && parsed.text.length > 300) {
                        setIsCollapsed(true);
                    } else if (parsed.type === 'viv_advice' && parsed.text.length > 300) {
                        setIsCollapsed(true);
                    }
                } else {
                    setParsedContent({ type: 'text', text: content });
                    if (content.length > 300) setIsCollapsed(true);
                }
            } catch (e) {
                // Fallback to text if parsing fails
                setParsedContent({ type: 'text', text: content });
                if (content.length > 300) setIsCollapsed(true);
            }
        } else {
            setParsedContent({ type: 'text', text: content });
        }
    }, [content, role]);

    const renderContent = () => {
        if (!parsedContent) return <div className={styles.loading}>...</div>;

        // Helper for collapsible text
        const renderCollapsibleText = (text: string) => {
            const shouldCollapse = isCollapsed && text.length > 300;
            const displayText = shouldCollapse ? text.slice(0, 300) + '...' : text;

            return (
                <div className={styles.messageText}>
                    {displayText.split('\n').map((line, i) => (
                        <p key={i} dangerouslySetInnerHTML={{
                            __html: line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        }} />
                    ))}
                    {text.length > 300 && (
                        <button
                            className={styles.collapseToggle}
                            onClick={() => setIsCollapsed(!isCollapsed)}
                            style={{
                                background: 'transparent',
                                border: 'none',
                                color: 'var(--color-accent-blue)',
                                cursor: 'pointer',
                                fontSize: '12px',
                                padding: '4px 0',
                                marginTop: '4px',
                                fontWeight: 600
                            }}
                        >
                            {isCollapsed ? 'Show more' : 'Show less'}
                        </button>
                    )}
                </div>
            );
        };

        if (parsedContent.type === 'text') {
            return renderCollapsibleText(parsedContent.text);
        }

        if (parsedContent.type === 'mobility_options') {
            return (
                <RideOptions
                    destination={parsedContent.data.destination}
                    options={parsedContent.data.options}
                    cheapest={parsedContent.data.cheapest}
                    onBook={async (option) => {
                        if (onSend) {
                            // Send message to chat for visual feedback
                            onSend(`Book ${option.provider} ${option.type}`);
                        }

                        // Also trigger actual booking API
                        try {
                            console.log("Booking ride:", option);
                            await bookRide({
                                provider: option.provider,
                                ride_type: option.type,
                                start_location: { lat: 0, lng: 0 }, // TODO: Get real location
                                end_location: { lat: 0, lng: 0 }    // TODO: Get real location
                            });
                        } catch (e) {
                            console.error("Booking failed", e);
                        }
                    }}
                />
            );
        }

        if (parsedContent.type === 'mobility_booking_confirmed') {
            return (
                <div className={styles.bookingConfirmed}>
                    <div className={styles.confirmedHeader}>✅ Booking Confirmed</div>
                    <div className={styles.confirmedDetails}>
                        <div><strong>Driver:</strong> {parsedContent.data.driver_name} ({parsedContent.data.driver_rating}★)</div>
                        <div><strong>Vehicle:</strong> {parsedContent.data.vehicle} ({parsedContent.data.plate})</div>
                        <div><strong>ETA:</strong> {parsedContent.data.eta} mins</div>
                    </div>
                </div>
            );
        }

        if (parsedContent.type === 'mobility_cancellation_confirmed') {
            return (
                <div className={styles.bookingConfirmed} style={{ borderColor: 'var(--color-accent-red)', backgroundColor: '#fef2f2' }}>
                    <div className={styles.confirmedHeader} style={{ color: 'var(--color-accent-red)' }}>🚫 Ride Cancelled</div>
                    <div className={styles.messageText}>
                        {parsedContent.text}
                    </div>
                </div>
            );
        }

        if (parsedContent.type === 'financial_spend') {
            return (
                <FinancialSummary
                    total={parsedContent.data.total}
                    period={parsedContent.data.period}
                    breakdown={parsedContent.data.breakdown}
                    category={parsedContent.data.category}
                />
            );
        }

        if (parsedContent.type === 'financial_balance') {
            return (
                <div className={styles.balanceCard}>
                    <div className={styles.balanceTotal}>
                        <small>Total Balance</small>
                        <h2>AED {parsedContent.data.total_balance.toLocaleString()}</h2>
                    </div>
                    <div className={styles.accountList}>
                        {parsedContent.data.accounts.map((acc: any, i: number) => (
                            <div key={i} className={styles.accountItem}>
                                <span>{acc.bank} - {acc.name}</span>
                                <strong>AED {acc.balance.toLocaleString()}</strong>
                            </div>
                        ))}
                    </div>
                </div>
            );
        }

        if (parsedContent.type === 'summary' || parsedContent.type === 'booking_details') {
            return (
                <div className={styles.summaryContent}>
                    {(parsedContent.data?.bookings || parsedContent.data?.active_bookings)?.map((booking: any, i: number) => (
                        <div key={i} style={{
                            backgroundColor: 'var(--bg-secondary)',
                            borderRadius: '8px',
                            padding: '12px',
                            marginTop: '10px',
                            border: '1px solid var(--border-color)'
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                                <strong>{booking.provider} {booking.ride_type}</strong>
                                <span style={{
                                    backgroundColor: '#dcfce7',
                                    color: '#166534',
                                    padding: '2px 8px',
                                    borderRadius: '12px',
                                    fontSize: '12px'
                                }}>{booking.status || 'Confirmed'}</span>
                            </div>
                            <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                                <div>From: {booking.origin || booking.start_location}</div>
                                <div>To: {booking.destination}</div>
                                <div style={{ marginTop: '4px', color: 'var(--text-primary)' }}>⏱ {booking.eta}</div>
                                {booking.price_estimate && <div>💰 {booking.price_estimate}</div>}
                            </div>
                        </div>
                    ))}
                </div>
            );
        }

        if (parsedContent.type === 'viv_advice') {
            return (
                <div className={styles.messageWrapper}>
                    {renderCollapsibleText(parsedContent.text)}
                    {parsedContent.data?.suggested_actions && (
                        <div className={styles.suggestedActions}>
                            {parsedContent.data.suggested_actions.map((action: string, i: number) => (
                                <button key={i} className={styles.actionButton} onClick={() => onSend && onSend(action)}>
                                    {action}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            );
        }

        if (parsedContent.type === 'error') {
            return (
                <div className={styles.errorText}>{parsedContent.text}</div>
            );
        }

        if (parsedContent.type === 'tradeoff_analysis') {
            return (
                <TradeoffCard
                    title={parsedContent.data.title}
                    optionA={parsedContent.data.optionA}
                    optionB={parsedContent.data.optionB}
                    recommendation={parsedContent.data.recommendation}
                    reasoning={parsedContent.data.reasoning}
                    onSelect={(option) => {
                        if (onSend) onSend(`I choose Option ${option}`);
                    }}
                />
            );
        }

        // Fallback
        return renderCollapsibleText(content);
    };

    return (
        <div className={`${styles.messageRow} ${role === 'user' ? styles.userRow : styles.assistantRow}`}>
            <div className={styles.avatar}>
                {role === 'user' ? (
                    <div className={styles.userAvatar}>U</div>
                ) : (
                    <div className={styles.assistantAvatar}>
                        <img src={helmH} alt="AI" onError={(e) => e.currentTarget.style.display = 'none'} />
                        <span className={styles.fallbackAvatar}>AI</span>
                    </div>
                )}
            </div>
            <div className={styles.content}>
                <div className={styles.senderName}>
                    {role === 'user' ? 'You' : 'HELM Assistant'}
                </div>
                {renderContent()}
            </div>
        </div>
    );
};

export default ChatMessage;
