// ...other imports and code...

export async function conversationApi(
  options: ConversationRequest,
  abortSignal: AbortSignal
): Promise<Response | { error: string }> {
  try {
    const response = await fetch('/conversation', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ messages: options.messages }),
      signal: abortSignal,
    });
    return response;
  } catch (err: any) {
    return { error: 'Failed to fetch conversation: ' + (err?.message || err) };
  }
}

export async function getUserInfo(): Promise<UserInfo[] | { error: string }> {
  try {
    const response = await fetch('/.auth/me');
    if (!response.ok) {
      return { error: `No identity provider found. Access to chat will be blocked. (Status: ${response.status})` };
    }
    return await response.json();
  } catch (err: any) {
    return { error: 'Failed to fetch user info: ' + (err?.message || err) };
  }
}

// Repeat this structured error approach for all other exported API functions as needed.