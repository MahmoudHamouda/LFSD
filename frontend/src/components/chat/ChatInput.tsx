import React, { useState, useRef, useEffect } from 'react';
import styles from './ChatInput.module.css';

interface ChatInputProps {
    onSend: (message: string) => void;
    isLoading: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSend, isLoading }) => {
    const [input, setInput] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleSubmit = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || isLoading) return;
        onSend(input);
        setInput('');
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    }, [input]);

    return (
        <div className={styles.container}>
            <div className={styles.inputWrapper}>
                <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Send a message..."
                    className={styles.textarea}
                    rows={1}
                    disabled={isLoading}
                />
                <button
                    onClick={() => alert("HELM: 'I only use your heart rate data to calculate your recovery score and suggest better times for deep work. Your raw data is encrypted and never sold.'")}
                    className={styles.privacyButton} // Assuming a new style for this button
                >
                    Ask HELM about Privacy
                </button>
                <button
                    onClick={() => handleSubmit()}
                    disabled={!input.trim() || isLoading}
                    className={styles.sendButton}
                    aria-label="Send message"
                >
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                    </svg>
                </button>
            </div>
            <div className={styles.footer}>
                HELM Assistant can make mistakes. Consider checking important information.
            </div>
        </div>
    );
};

export default ChatInput;
