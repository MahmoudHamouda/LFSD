import React, { useState, useEffect } from 'react';
import styles from './ChatMessage.module.css';

import RideOptions from './RideOptions';
import FinancialSummary from './FinancialSummary';
import TradeoffCard from './TradeoffCard';
import { bookRide } from '../../api/api';
import { z } from 'zod';
import DOMPurify from 'dompurify';

// Define Zod Schemas
const BaseSchema = z.object({
    type: z.string(),
    text: z.string().optional(),
    data: z.any().optional()
});

const MobilityOptionsSchema = BaseSchema.extend({
    type: z.literal('mobility_options'),
    data: z.object({
        destination: z.string(),
        options: z.array(z.object({
            id: z.string(),
            provider: z.string(),
            type: z.string(),
            price: z.string(),
            eta: z.string(),
            recommended: z.boolean().optional(),
            reasoning: z.string().optional()
        })),
        cheapest: z.any().optional()
    })
});

const VivAdviceSchema = BaseSchema.extend({
    type: z.literal('viv_advice'),
    data: z.object({
        suggested_actions: z.array(z.string()).optional()
    }).optional()
});

const FinancialSpendSchema = BaseSchema.extend({
    type: z.literal('financial_spend'),
    data: z.object({
        total: z.number(),
        period: z.string(),
        breakdown: z.array(z.object({
            category: z.string(),
            amount: z.number(),
            percentage: z.number()
        })),
        category: z.string().optional()
    })
});

const FinancialBalanceSchema = BaseSchema.extend({
    type: z.literal('financial_balance'),
    data: z.object({
        total_balance: z.number(),
        accounts: z.array(z.object({
            bank: z.string(),
            name: z.string(),
            balance: z.number()
        }))
    })
});

const TradeoffAnalysisSchema = BaseSchema.extend({
    type: z.literal('tradeoff_analysis'),
    data: z.object({
        title: z.string(),
        optionA: z.any(),
        optionB: z.any(),
        recommendation: z.string(),
        reasoning: z.string()
    })
});

// Union schema for all supported types
const MessageContentSchema = z.union([
    MobilityOptionsSchema,
    VivAdviceSchema,
    FinancialSpendSchema,
    FinancialBalanceSchema,
    TradeoffAnalysisSchema,
    BaseSchema // Fallback
]);

interface ChatMessageProps {
    role: 'user' | 'assistant';
    content: string;
    onSend?: (message: string) => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ role, content, onSend }) => {
    const [parsedContent, setParsedContent] = useState<any>(null);

    useEffect(() => {
        if (role === 'assistant') {
            try {
                let jsonContent = content.trim();

                // If the content is wrapped in markdown code blocks, extract the JSON part
                if (jsonContent.startsWith('```')) {
                    const startMatch = jsonContent.match(/\{/);
                    const endMatch = jsonContent.lastIndexOf('}');
                    if (startMatch && endMatch !== -1) {
                        jsonContent = jsonContent.slice(startMatch.index, endMatch + 1);
                    }
                }

                // Attempt to parse JSON content if it looks like JSON
                if (jsonContent.startsWith('{') || jsonContent.startsWith('[')) {
                    let parsed = JSON.parse(jsonContent);

                    // Handle double-encoded JSON (where 'text' itself contains a JSON string)
                    if (parsed.type === 'text' && typeof parsed.text === 'string' && (parsed.text.trim().startsWith('{') || parsed.text.trim().startsWith('['))) {
                        try {
                            const innerContent = JSON.parse(parsed.text.trim());
                            if (innerContent.type) {
                                parsed = innerContent;
                            } else if (innerContent.summary || innerContent.message_body) {
                                // Implicit "viv_advice" or "tradeoff" if it has these keys
                                parsed = {
                                    type: innerContent.intent === 'tradeoff_analysis' ? 'tradeoff_analysis' : 'viv_advice',
                                    text: innerContent.message_body || innerContent.summary || "I have analyzed your situation.",
                                    data: innerContent
                                };
                            }
                        } catch (e) {
                            // Not JSON, keep as text
                        }
                    }

                    // If it's raw AI output from the synthesizer (no 'type'), wrap it
                    if (!parsed.type && (parsed.summary || parsed.message_body)) {
                        parsed = {
                            type: parsed.intent === 'tradeoff_analysis' ? 'tradeoff_analysis' : 'viv_advice',
                            text: parsed.message_body || parsed.summary || "I have analyzed your situation.",
                            data: parsed
                        };
                    }

                    // Validate with Zod
                    const result = MessageContentSchema.safeParse(parsed);

                    if (result.success) {
                        setParsedContent(result.data);
                        setParsedContent(result.data);
                    } else {
                        console.warn("Schema validation failed, using fallback:", result.error);
                        // Fallback: If it has basic structure, use it even if schema is strict
                        if (parsed.type && (parsed.text || parsed.data)) {
                            setParsedContent(parsed);
                        } else {
                            setParsedContent({ type: 'text', text: content });
                        }
                    }
                } else {
                    setParsedContent({ type: 'text', text: content });
                    setParsedContent({ type: 'text', text: content });
                }
            } catch (e) {
                setParsedContent({ type: 'text', text: content });
                setParsedContent({ type: 'text', text: content });
            }
        } else {
            setParsedContent({ type: 'text', text: content });
        }
    }, [content, role]);

    const renderContent = () => {
        if (!parsedContent) return <div className={styles.loading}>...</div>;

        // Helper for text with sanitization
        const renderText = (text: string = "") => {
            // Tighten sanitization
            const sanitizedHtml = DOMPurify.sanitize(
                text.replace(/\n/g, '<br/>')
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>'),
                {
                    ALLOWED_TAGS: ['br', 'strong', 'em', 'p', 'b', 'i'],
                    ALLOWED_ATTR: []
                }
            );

            return (
                <div className={styles.messageText}>
                    <div dangerouslySetInnerHTML={{ __html: sanitizedHtml }} />
                </div>
            );
        };

        if (parsedContent.type === 'text') {
            return renderText(parsedContent.text);
        }

        if (parsedContent.type === 'mobility_options') {
            return (
                <RideOptions
                    destination={parsedContent.data.destination}
                    options={parsedContent.data.options}
                    cheapest={parsedContent.data.cheapest}
                    onBook={async (option: any, location: any) => {
                        if (onSend) {
                            onSend(`Book ${option.provider} ${option.type}`);
                        }

                        // Determine start location based on input type
                        let startLocation = { lat: 0, lng: 0, address: "Current Location" };

                        if (typeof location === 'string') {
                            startLocation.address = location;
                        } else {
                            startLocation = {
                                lat: location.lat,
                                lng: location.lng,
                                address: location.address || "GPS Coordinates"
                            };
                        }

                        try {
                            const destinationName = parsedContent.data.destination;
                            console.log(`Booking ${option.provider} to ${destinationName} from`, startLocation);

                            await bookRide({
                                provider: option.provider,
                                ride_type: option.type,
                                start_location: startLocation,
                                end_location: {
                                    lat: 0,
                                    lng: 0,
                                    address: destinationName
                                }
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

        if (parsedContent.type === 'schedule_event_confirmed' || parsedContent.type === 'calendar_event_created') {
            const eventStart = new Date(parsedContent.data.start || parsedContent.data.time);
            const eventEnd = parsedContent.data.end ? new Date(parsedContent.data.end) : null;

            return (
                <div className={styles.bookingConfirmed} style={{ borderColor: 'var(--color-primary)', backgroundColor: 'var(--bg-secondary)' }}>
                    <div className={styles.confirmedHeader} style={{ color: 'var(--color-primary)' }}>📅 Event Scheduled</div>
                    <div className={styles.messageText} style={{ marginBottom: '12px' }}>
                        {parsedContent.text}
                    </div>
                    <div className={styles.confirmedDetails}>
                        <div style={{ fontSize: '1.1em', fontWeight: 'bold', marginBottom: '4px' }}>
                            {parsedContent.data.summary || parsedContent.data.event}
                        </div>

                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <span>🕒</span>
                            <div>
                                <div>{eventStart.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}</div>
                                <div>
                                    {eventStart.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })}
                                    {eventEnd && ` - ${eventEnd.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })}`}
                                </div>
                            </div>
                        </div>

                        {parsedContent.data.link && (
                            <a
                                href={parsedContent.data.link}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{
                                    display: 'inline-block',
                                    marginTop: '8px',
                                    color: 'var(--color-primary)',
                                    fontSize: '0.9em'
                                }}
                            >
                                Open in Calendar ↗
                            </a>
                        )}
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
                    {renderText(parsedContent.text)}
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
        return renderText(content);
    };

    return (
        <div className={`${styles.messageRow} ${role === 'user' ? styles.userRow : styles.assistantRow}`}>
            <div className={styles.avatar}>
                {role === 'user' ? (
                    <div className={styles.userAvatar}>U</div>
                ) : (
                    <div className={styles.assistantAvatar}>
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
