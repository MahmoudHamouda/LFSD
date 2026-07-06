import React, { useState, useEffect, useRef, useCallback } from 'react';
import { historyGenerate } from '../../api/api';
import { ChatMessage as ChatMessageType } from '../../api/models';
import ChatMessage from '../../components/chat/ChatMessage';
import ChatInput from '../../components/chat/ChatInput';
import ConsentBanner from '../../components/chat/ConsentBanner';
import styles from './Chat.module.css';


import { useLocation, useNavigate } from 'react-router-dom';

const Chat = () => {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [geoLoc, setGeoLoc] = useState<{ lat: number, lng: number } | undefined>(undefined);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const location = useLocation();
  const navigate = useNavigate();
  const hasProcessedInitialMessage = useRef(false);

  // Get location on mount
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          console.log("Location acquired:", position.coords);
          setGeoLoc({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => {
          console.error("Error getting location:", error);
        }
      );
    }
  }, []);

  // URL params
  const queryParams = new URLSearchParams(location.search);
  const conversationId = queryParams.get('id');

  // Load history when conversation ID changes
  useEffect(() => {
    const loadConversation = async () => {
      if (conversationId) {
        setIsLoading(true);
        try {
          // Import dynamically or assume imported
          const data = await import('../../api/api').then(m => m.historyRead(conversationId));
          if (data && Array.isArray(data)) {
            setMessages(data);
          }
        } catch (e) {
          console.error("Failed to load conversation", e);
        } finally {
          setIsLoading(false);
        }
      } else {
        setMessages([]);
      }
    };
    loadConversation();
  }, [conversationId]);


  // Scroll to the latest message
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSend = useCallback(async (messageText: string) => {
    setIsLoading(true);

    // Create optimistic user message
    const userMessage: ChatMessageType = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText,
      date: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);

    try {
      // Call backend API
      // If we have existing messages, send them all for context, or just the new one depending on backend logic.
      // The generate endpoint usually expects the full history for context if not stateful, but here we pass full history.
      const history = [...messages, userMessage];
      const abortController = new AbortController();

      // Use the ID from URL if available, otherwise backend creates new.
      const targetConversationId = conversationId;

      const response = await historyGenerate(
        {
          messages: history, // Send full history or just new message? Check API. API seems to take full history for context.
          context: geoLoc ? { location: geoLoc } : undefined
        },
        abortController.signal,
        targetConversationId || undefined // specific logic: pass ID if exists, convert null to undefined
      );

      if (response.ok) {
        const data = await response.json();
        if (data.choices && data.choices.length > 0) {
          const aiMessage = data.choices[0].messages[0];
          setMessages(prev => [...prev, aiMessage]);

          // If we started a new chat (no ID in URL), the backend returned a conversation_id.
          // We should update the URL so a refresh keeps us here.
          if (!conversationId && data.history_metadata?.conversation_id) {
            const newId = data.history_metadata.conversation_id;
            // Update URL without reloading
            navigate(`/chat?id=${newId}`, { replace: true });
          }
        }
      } else {
        throw new Error('Failed to fetch response');
      }
    } catch (error) {
      console.error("Error generating response:", error);
      const errorMessage: ChatMessageType = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Sorry, something went wrong. Please try again.',
        date: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [messages, geoLoc, conversationId, navigate]);

  // Handle initial message from navigation state (New Chat + Initial Message)
  useEffect(() => {
    const state = location.state as { initialMessage?: string } | null;
    if (state?.initialMessage && !hasProcessedInitialMessage.current) {
      hasProcessedInitialMessage.current = true;
      // We are in a "New Chat" state effectively, so conversationId should be null/undefined.
      // If user navigated to /chat?id=123 with initialMessage, it might be ambiguous, but usually intent is new context.
      // Assuming /chat with no ID for this case.
      handleSend(state.initialMessage);
      window.history.replaceState({}, document.title);
    }
  }, [location.state, handleSend]);

  return (
    <div className={styles.container}>
      <ConsentBanner />

      <div className={styles.chatArea}>
        {messages.length === 0 ? (
          <div className={styles.welcomeContainer}>
            <h1 className={styles.welcomeTitle}>HELM</h1>
            <h2 className={styles.welcomeTitle}>How can I help you today?</h2>
          </div>
        ) : (
          <div className={styles.messageList}>
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                role={message.role as 'user' | 'assistant'}
                content={typeof message.content === 'string' ? message.content : JSON.stringify(message.content)}
                onSend={handleSend}
              />
            ))}
            {isLoading && (
              <div className={styles.loadingIndicator}>
                <span className={styles.dot}></span>
                <span className={styles.dot}></span>
                <span className={styles.dot}></span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className={styles.inputArea}>
        <ChatInput onSend={handleSend} isLoading={isLoading} />
      </div>
    </div>
  );
};

export default Chat;
