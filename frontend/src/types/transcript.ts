/**
 * Shared type definitions for transcript messages
 */

export interface TranscriptMessage {
  text: string;
  is_user: boolean;
  timestamp: number;
  id: string;
}

