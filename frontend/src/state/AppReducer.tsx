import { Action, AppState } from './AppProvider';

// Define the reducer function
export const appStateReducer = (state: AppState, action: Action): AppState => {
  switch (action.type) {
    case 'TOGGLE_CHAT_HISTORY':
      // Toggle the visibility of the chat history panel
      return { ...state, isChatHistoryOpen: !state.isChatHistoryOpen };

    case 'UPDATE_CURRENT_CHAT':
      // Update the currently active chat
      return { ...state, currentChat: action.payload };

    case 'UPDATE_CHAT_HISTORY_LOADING_STATE':
      // Update the loading state for chat history
      return { ...state, chatHistoryLoadingState: action.payload };

    case 'UPDATE_CHAT_HISTORY':
      // Update the chat history with a new or updated conversation
      if (!state.chatHistory || !state.currentChat) {
        return state;
      }
      const conversationIndex = state.chatHistory.findIndex(
        (conv) => conv.id === action.payload.id
      );
      if (conversationIndex !== -1) {
        const updatedChatHistory = [...state.chatHistory];
        updatedChatHistory[conversationIndex] = state.currentChat;
        return { ...state, chatHistory: updatedChatHistory };
      } else {
        return { ...state, chatHistory: [...state.chatHistory, action.payload] };
      }

    case 'UPDATE_CHAT_TITLE':
      // Update the title of a specific conversation
      if (!state.chatHistory) {
        return { ...state, chatHistory: [] };
      }
      const updatedChats = state.chatHistory.map((chat) => {
        if (chat.id === action.payload.id) {
          if (state.currentChat?.id === action.payload.id) {
            state.currentChat.title = action.payload.title;
          }
          // TODO: Make API call to save the new title to DB
          return { ...chat, title: action.payload.title };
        }
        return chat;
      });
      return { ...state, chatHistory: updatedChats };

    case 'DELETE_CHAT_ENTRY':
      // Delete a specific conversation from the chat history
      if (!state.chatHistory) {
        return { ...state, chatHistory: [] };
      }
      const filteredChat = state.chatHistory.filter(
        (chat) => chat.id !== action.payload
      );
      state.currentChat = null;
      // TODO: Make API call to delete the conversation from DB
      return { ...state, chatHistory: filteredChat };

    case 'DELETE_CHAT_HISTORY':
      // Clear all chat history
      // TODO: Make API call to delete all conversations from DB
      return { ...state, chatHistory: [], filteredChatHistory: [], currentChat: null };

    case 'DELETE_CURRENT_CHAT_MESSAGES':
      // Clear messages in the current conversation
      // TODO: Make API call to delete current conversation messages from DB
      if (!state.currentChat || !state.chatHistory) {
        return state;
      }
      const updatedCurrentChat = {
        ...state.currentChat,
        messages: [],
      };
      return { ...state, currentChat: updatedCurrentChat };

    case 'FETCH_CHAT_HISTORY':
      // Fetch and update chat history
      return { ...state, chatHistory: action.payload };

    case 'SET_COSMOSDB_STATUS':
      // Update the status of CosmosDB availability
      return { ...state, isCosmosDBAvailable: action.payload };

    case 'FETCH_FRONTEND_SETTINGS':
      // Fetch and update frontend settings
      return { ...state, isLoading: false, frontendSettings: action.payload };

    case 'SET_FEEDBACK_STATE':
      // Update feedback state for a specific answer
      return {
        ...state,
        feedbackState: {
          ...state.feedbackState,
          [action.payload.answerId]: action.payload.feedback,
        },
      };

    case 'SET_ANSWER_EXEC_RESULT':
      // Update execution results for a specific answer
      return {
        ...state,
        answerExecResult: {
          ...state.answerExecResult,
          [action.payload.answerId]: action.payload.exec_result,
        },
      };

    default:
      // Return the current state for unknown actions
      return state;
  }
};
