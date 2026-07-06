import { chatHistorySampleData } from '../constants/chatHistory';

import { ChatMessage, Conversation, ConversationRequest, CosmosDBHealth, CosmosDBStatus, UserInfo } from './models';

// --- Responsible-AI consent -------------------------------------------------

export interface ConsentStatus {
  purpose: string;
  has_consent: boolean;
}

export async function getConsent(purpose = 'ai_advisory'): Promise<ConsentStatus | null> {
  try {
    const res = await fetch(`/api/consent?purpose=${encodeURIComponent(purpose)}`, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function setConsent(granted: boolean, purpose = 'ai_advisory'): Promise<boolean> {
  const res = await fetch('/api/consent', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
    body: JSON.stringify({ granted, purpose }),
  });
  return res.ok;
}

export async function conversationApi(options: ConversationRequest, abortSignal: AbortSignal): Promise<Response> {
  const response = await fetch('/conversation', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: JSON.stringify({
      messages: options.messages,
    }),
    signal: abortSignal,
  });

  return response;
}

export async function getUserInfo(): Promise<UserInfo[]> {
  const response = await fetch('/.auth/me');
  if (!response.ok) {
    console.log('No identity provider found. Access to chat will be blocked.');
    return [];
  }

  const payload = await response.json();
  return payload;
}

// export const fetchChatHistoryInit = async (): Promise<Conversation[] | null> => {
export const fetchChatHistoryInit = (): Conversation[] | null => {
  // Make initial API call here

  return chatHistorySampleData;
};

export const historyList = async (offset = 0): Promise<Conversation[] | null> => {
  const response = await fetch(`/history/list?offset=${offset}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  })
    .then(async (res) => {
      const payload = await res.json();
      if (!Array.isArray(payload)) {
        console.error('There was an issue fetching your data.');
        return null;
      }
      const conversations: Conversation[] = await Promise.all(
        payload.map(async (conv: any) => {
          let convMessages: ChatMessage[] = [];
          convMessages = await historyRead(conv.id)
            .then((res) => {
              return res;
            })
            .catch((err) => {
              console.error('error fetching messages: ', err);
              return [];
            });
          const conversation: Conversation = {
            id: conv.id,
            title: conv.title,
            date: conv.createdAt,
            messages: convMessages,
          };
          return conversation;
        })
      );
      return conversations;
    })
    .catch((_err) => {
      console.error('There was an issue fetching your data.');
      return null;
    });

  return response;
};

export const historyRead = async (convId: string): Promise<ChatMessage[]> => {
  const response = await fetch('/history/read', {
    method: 'POST',
    body: JSON.stringify({
      conversation_id: convId,
    }),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
  })
    .then(async (res) => {
      if (!res) {
        return [];
      }
      const payload = await res.json();
      const messages: ChatMessage[] = [];
      if (payload?.messages) {
        payload.messages.forEach((msg: any) => {
          const message: ChatMessage = {
            id: msg.id,
            role: msg.role,
            date: msg.createdAt,
            content: msg.content,
            feedback: msg.feedback ?? undefined,
          };
          messages.push(message);
        });
      }
      return messages;
    })
    .catch((_err) => {
      console.error('There was an issue fetching your data.');
      return [];
    });
  return response;
};

export const historyGenerate = async (
  options: ConversationRequest,
  abortSignal: AbortSignal,
  convId?: string
): Promise<Response> => {
  let body;
  const payload: any = {
    messages: options.messages,
    context: options.context
  };

  if (convId) {
    payload.conversation_id = convId;
  }

  body = JSON.stringify(payload);
  const response = await fetch('/history/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: body,
    signal: abortSignal,
  })
    .then((res) => {
      return res;
    })
    .catch((_err) => {
      console.error('There was an issue fetching your data.');
      return new Response();
    });
  return response;
};

export const historyUpdate = async (messages: ChatMessage[], convId: string): Promise<Response> => {
  const response = await fetch('/history/update', {
    method: 'POST',
    body: JSON.stringify({
      conversation_id: convId,
      messages: messages,
    }),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
  })
    .then(async (res) => {
      return res;
    })
    .catch((_err) => {
      console.error('There was an issue fetching your data.');
      const errRes: Response = {
        ...new Response(),
        ok: false,
        status: 500,
      };
      return errRes;
    });
  return response;
};

export const historyDelete = async (convId: string): Promise<Response> => {
  const response = await fetch('/history/delete', {
    method: 'DELETE',
    body: JSON.stringify({
      conversation_id: convId,
    }),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
  })
    .then((res) => {
      return res;
    })
    .catch((_err) => {
      console.error('There was an issue fetching your data.');
      const errRes: Response = {
        ...new Response(),
        ok: false,
        status: 500,
      };
      return errRes;
    });
  return response;
};

export const historyDeleteAll = async (): Promise<Response> => {
  const response = await fetch('/history/delete_all', {
    method: 'DELETE',
    body: JSON.stringify({}),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
  })
    .then((res) => {
      return res;
    })
    .catch((_err) => {
      console.error('There was an issue fetching your data.');
      const errRes: Response = {
        ...new Response(),
        ok: false,
        status: 500,
      };
      return errRes;
    });
  return response;
};

export const historyClear = async (convId: string): Promise<Response> => {
  const response = await fetch('/history/clear', {
    method: 'POST',
    body: JSON.stringify({
      conversation_id: convId,
    }),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
  })
    .then((res) => {
      return res;
    })
    .catch((_err) => {
      console.error('There was an issue fetching your data.');
      const errRes: Response = {
        ...new Response(),
        ok: false,
        status: 500,
      };
      return errRes;
    });
  return response;
};

export const historyRename = async (convId: string, title: string): Promise<Response> => {
  const response = await fetch('/history/rename', {
    method: 'POST',
    body: JSON.stringify({
      conversation_id: convId,
      title: title,
    }),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
  })
    .then((res) => {
      return res;
    })
    .catch((_err) => {
      console.error('There was an issue fetching your data.');
      const errRes: Response = {
        ...new Response(),
        ok: false,
        status: 500,
      };
      return errRes;
    });
  return response;
};

export const historyEnsure = async (): Promise<CosmosDBHealth> => {
  const response = await fetch('/history/ensure', {
    method: 'GET',
  })
    .then(async (res) => {
      const respJson = await res.json();
      let formattedResponse;
      if (respJson.message) {
        formattedResponse = CosmosDBStatus.Working;
      } else {
        if (res.status === 500) {
          formattedResponse = CosmosDBStatus.NotWorking;
        } else if (res.status === 401) {
          formattedResponse = CosmosDBStatus.InvalidCredentials;
        } else if (res.status === 422) {
          formattedResponse = respJson.error;
        } else {
          formattedResponse = CosmosDBStatus.NotConfigured;
        }
      }
      if (!res.ok) {
        return {
          cosmosDB: false,
          status: formattedResponse,
        };
      } else {
        return {
          cosmosDB: true,
          status: formattedResponse,
        };
      }
    })
    .catch((err) => {
      console.error('There was an issue fetching your data.');
      return {
        cosmosDB: false,
        status: err,
      };
    });
  return response;
};

export const frontendSettings = async (): Promise<Response | null> => {
  const response = await fetch('/frontend_settings', {
    method: 'GET',
  })
    .then((res) => {
      return res.json();
    })
    .catch((_err) => {
      console.error('There was an issue fetching your data.');
      return null;
    });

  return response;
};

export const connectPartner = async (partnerId: string): Promise<Response> => {
  const response = await fetch(`/api/partners/${partnerId}/connect`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  })
    .then((res) => res)
    .catch((_err) => {
      console.error('Error connecting partner');
      return new Response(JSON.stringify({ success: false }), { status: 500 });
    });
  return response;
};

export const disconnectPartner = async (partnerId: string): Promise<Response> => {
  const response = await fetch(`/api/partners/${partnerId}/disconnect`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  })
    .then((res) => res)
    .catch((_err) => {
      console.error('Error disconnecting partner');
      return new Response(JSON.stringify({ success: false }), { status: 500 });
    });
  return response;
};

export const updatePartnerPermissions = async (partnerId: string, permissions: any): Promise<Response> => {
  const response = await fetch(`/api/partners/${partnerId}/permissions`, {
    method: 'PUT',
    body: JSON.stringify(permissions),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  })
    .then((res) => res)
    .catch((_err) => {
      console.error('Error updating permissions');
      return new Response(JSON.stringify({ success: false }), { status: 500 });
    });
  return response;
};

export const bookRide = async (bookingRequest: any): Promise<Response> => {
  const response = await fetch('/mobility/book-ride', {
    method: 'POST',
    body: JSON.stringify(bookingRequest),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
  })
    .then((res) => res)
    .catch((_err) => {
      console.error('Error booking ride');
      return new Response(JSON.stringify({ success: false }), { status: 500 });
    });
  return response;
};


export const getTimeEvents = async (): Promise<any[]> => {
  const token = localStorage.getItem('token');
  const response = await fetch('/api/time/events', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  })
    .then(async (res) => {
      if (!res.ok) {
        console.error('Failed to fetch time events');
        return [];
      }
      const payload = await res.json();
      return payload.data || [];
    })
    .catch((_err) => {
      console.error('Error fetching time events');
      return [];
    });
  return response;
};
