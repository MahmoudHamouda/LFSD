import React, { createContext, ReactNode, useEffect, useReducer } from 'react';

import {
  ChatHistoryLoadingState,
  Conversation,
  CosmosDBHealth,
  Feedback,
  FrontendSettings,
  frontendSettings,
  historyEnsure,
  historyList,
} from '../api';

import { appStateReducer } from './AppReducer';

// Define the shape of the application state
export interface AppState {
  isChatHistoryOpen: boolean;
  chatHistoryLoadingState: ChatHistoryLoadingState;
  isCosmosDBAvailable: CosmosDBHealth;
  chatHistory: Conversation[] | null;
  filteredChatHistory: Conversation[] | null;
  currentChat: Conversation | null;
  frontendSettings: FrontendSettings | null;
  feedbackState: { [answerId: string]: Feedback.Neutral | Feedback.Positive | Feedback.Negative };
  isLoading: boolean;
  answerExecResult: { [answerId: string]: [] };
}

// Define the possible actions for the state
export type Action =
  | { type: 'TOGGLE_CHAT_HISTORY' }
  | { type: 'SET_COSMOSDB_STATUS'; payload: CosmosDBHealth }
  | { type: 'UPDATE_CHAT_HISTORY_LOADING_STATE'; payload: ChatHistoryLoadingState }
  | { type: 'UPDATE_CURRENT_CHAT'; payload: Conversation | null }
  | { type: 'UPDATE_FILTERED_CHAT_HISTORY'; payload: Conversation[] | null }
  | { type: 'UPDATE_CHAT_HISTORY'; payload: Conversation }
  | { type: 'UPDATE_CHAT_TITLE'; payload: Conversation }
  | { type: 'DELETE_CHAT_ENTRY'; payload: string }
  | { type: 'DELETE_CHAT_HISTORY' }
  | { type: 'DELETE_CURRENT_CHAT_MESSAGES'; payload: string }
  | { type: 'FETCH_CHAT_HISTORY'; payload: Conversation[] | null }
  | { type: 'FETCH_FRONTEND_SETTINGS'; payload: FrontendSettings | null }
  | {
      type: 'SET_FEEDBACK_STATE';
      payload: { answerId: string; feedback: Feedback.Positive | Feedback.Negative | Feedback.Neutral };
    }
  | { type: 'GET_FEEDBACK_STATE'; payload: string }
  | { type: 'SET_ANSWER_EXEC_RESULT'; payload: { answerId: string; exec_result: [] } };

// Initial state for the application
const initialState: AppState = {
  isChatHistoryOpen: false,
  chatHistoryLoadingState: 'idle',
  isCosmosDBAvailable: { status: 'unknown' },
  chatHistory: null,
  filteredChatHistory: null,
  currentChat: null,
  frontendSettings: null,
  feedbackState: {},
  isLoading: false,
  answerExecResult: {},
};

// Context for the application state
export const AppStateContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<Action>;
}>({
  state: initialState,
  dispatch: () => undefined,
});

// Provider for the application state
export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(appStateReducer, initialState);

  useEffect(() => {
    // Example: Fetch frontend settings on app initialization
    async function fetchSettings() {
      const settings = await frontendSettings();
      dispatch({ type: 'FETCH_FRONTEND_SETTINGS', payload: settings });
    }

    fetchSettings();
  }, []);

  return (
    <AppStateContext.Provider value={{ state, dispatch }}>
      {children}
    </AppStateContext.Provider>
  );
};
