import React, { useRef, useState, useEffect, useContext, useLayoutEffect } from 'react';
import {
  CommandBarButton,
  IconButton,
  Dialog,
  DialogType,
  Stack,
} from '@fluentui/react';
import {
  SquareRegular,
  ShieldLockRegular,
  ErrorCircleRegular,
} from '@fluentui/react-icons';
import { AppStateContext } from '../../state/AppProvider';
import { QuestionInput } from '../../components/QuestionInput';
import { ChatMessage } from '../../api';
import styles from './Chat.module.css';

const Chat = () => {
  const appStateContext = useContext(AppStateContext);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const chatMessageStreamEnd = useRef<HTMLDivElement | null>(null);

  useLayoutEffect(() => {
    chatMessageStreamEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (question: string) => {
    setIsLoading(true);

    const newMessage: ChatMessage = {
      id: `${Date.now()}`,
      role: 'user',
      content: question,
      date: new Date().toISOString(),
    };
    setMessages([...messages, newMessage]);

    // Simulate a response from the AI
    setTimeout(() => {
      const responseMessage: ChatMessage = {
        id: `${Date.now()}`,
        role: 'assistant',
        content: `This is a response to: "${question}"`,
        date: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, responseMessage]);
      setIsLoading(false); // Corrected line
    }, 1000); // Simulating a delay
  };

  return (
    <div className={styles.chatContainer}>
      <Stack>
        <div className={styles.chatMessages}>
          {messages.map((msg) => (
            <div key={msg.id} className={styles.message}>
              <strong>{msg.role}:</strong> {msg.content}
            </div>
          ))}
          <div ref={chatMessageStreamEnd} />
        </div>
        <QuestionInput onSend={handleSend} isLoading={isLoading} />
      </Stack>
    </div>
  );
};

export default Chat;
