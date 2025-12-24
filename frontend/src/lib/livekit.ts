import { TokenSource } from "livekit-client";
import type { TokenSourceFetchOptions, TokenSourceResponseObject } from "livekit-client";
import { getApiUrl, environmentConfiguration } from "./config";

/**
 * Creates a token source for use with LiveKit's useSession hook.
 * Uses TokenSource.custom() to create a proper token source that fetches from our backend API.
 * 
 * The custom function accepts TokenSourceFetchOptions and returns TokenSourceResponseObject
 * with participantToken and url fields.
 */
export function createTokenSource() {
  return TokenSource.custom(async (options?: TokenSourceFetchOptions): Promise<TokenSourceResponseObject> => {
    const response = await fetch(
      getApiUrl(environmentConfiguration.endpoints.token),
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          identity: options?.participantIdentity || `user-${Date.now()}`,
          name: options?.participantName || "User",
          room: options?.roomName || "paradise-room",
        }),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to get LiveKit token");
    }

    const data = await response.json();
    
    if (!data.token || typeof data.token !== 'string') {
      throw new Error(
        'Invalid response: Token is missing or invalid. Check backend token generation.'
      );
    }

    if (!data.url || typeof data.url !== 'string') {
      throw new Error(
        'Invalid response: URL is missing or invalid. Check backend LIVEKIT_URL configuration in .env file.'
      );
    }

    if (!data.url.startsWith('wss://') && !data.url.startsWith('ws://')) {
      throw new Error(
        `Invalid URL format: "${data.url}". LiveKit URL must start with wss:// or ws://. ` +
        `Check your backend .env file - LIVEKIT_URL should be in format: wss://your-project.livekit.cloud`
      );
    }
    
    return {
      participantToken: data.token,
      serverUrl: data.url,
    };
  });
}

