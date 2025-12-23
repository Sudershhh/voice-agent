import { useState, useMemo } from "react";
import {
  SessionProvider,
  useSession,
  VoiceAssistantControlBar,
  RoomAudioRenderer,
} from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import { createTokenSource } from "@/lib/livekit";
import { VoiceAgentView } from "@/components/VoiceAgentView";
import { FullTranscript } from "@/components/FullTranscript";
import { PDFUpload } from "@/components/PDFUpload";
import { ConnectionStatus } from "@/components/ConnectionStatus";
import type { TranscriptMessage } from "@/types/transcript";
import { Button } from "@/components/ui/button";
import { Phone } from "lucide-react";

interface AppContentProps {
  session: ReturnType<typeof useSession>;
}

function AppContent({ session }: AppContentProps) {
  const [transcriptMessages, setTranscriptMessages] = useState<
    TranscriptMessage[]
  >([]);
  const [error, setError] = useState<string | null>(null);

  const handleStartCall = async () => {
    try {
      setError(null);
      await session.start();
    } catch (err) {
      let errorMessage: string;

      if (err instanceof Error) {
        const errorMsg = err.message;

        // Check for URL-related errors
        if (
          errorMsg.includes("URL") ||
          errorMsg.includes("Invalid URL") ||
          errorMsg.includes("wss://") ||
          errorMsg.includes("ws://")
        ) {
          errorMessage =
            errorMsg +
            "\n\n💡 Tip: Check your backend .env file and ensure LIVEKIT_URL is set correctly (e.g., wss://your-project.livekit.cloud)";
        }
        // Check for token-related errors
        else if (errorMsg.includes("Token") || errorMsg.includes("token")) {
          errorMessage =
            errorMsg +
            "\n\n💡 Tip: Verify your backend .env has LIVEKIT_API_KEY and LIVEKIT_API_SECRET configured";
        }
        // Check for network/connection errors
        else if (
          errorMsg.includes("Failed to fetch") ||
          errorMsg.includes("NetworkError") ||
          errorMsg.includes("fetch")
        ) {
          errorMessage =
            "Failed to connect to backend API.\n\n💡 Tip: Make sure your backend server is running on " +
            (import.meta.env.VITE_API_URL || "http://localhost:8000");
        }
        // Use the error message as-is for other cases
        else {
          errorMessage = errorMsg;
        }
      } else {
        errorMessage =
          "Failed to connect. Make sure:\n1. Backend API server is running\n2. Backend .env has LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET configured";
      }

      setError(errorMessage);
      console.error("Failed to start session:", err);
    }
  };

  const handleEndCall = async () => {
    try {
      await session.end();
      setTranscriptMessages([]);
    } catch (err) {
      console.error("Failed to end session:", err);
    }
  };

  const handleMessagesChange = (messages: TranscriptMessage[]) => {
    setTranscriptMessages(messages);
  };

  // Get connection state - ConnectionState is an enum
  const connectionState = session.connectionState;
  const isConnected = connectionState === ConnectionState.Connected;
  const isConnecting =
    connectionState === ConnectionState.Connecting ||
    connectionState === ConnectionState.Reconnecting;

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto p-8 space-y-8">
        {/* Header */}
        <header className="text-center space-y-2">
          <h1 className="text-4xl font-bold">Paradise</h1>
          <p className="text-muted-foreground">
            Your AI travel planning voice agent
          </p>
        </header>

        {/* Connection Controls */}
        <div className="flex flex-col items-center gap-4">
          {!isConnected && !isConnecting && (
            <Button onClick={handleStartCall} size="lg" className="gap-2">
              <Phone className="h-5 w-5" />
              Start Call
            </Button>
          )}

          {isConnected && (
            <Button
              onClick={handleEndCall}
              variant="destructive"
              size="lg"
              className="gap-2"
            >
              End Call
            </Button>
          )}

          <ConnectionStatus connectionState={session.connectionState} />
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
            <p className="text-sm text-destructive whitespace-pre-line">
              {error}
            </p>
          </div>
        )}

        {/* Loading State */}
        {isConnecting && (
          <div className="bg-card rounded-lg border p-6">
            <div className="flex flex-col items-center justify-center py-12 space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              <div className="text-center space-y-2">
                <p className="text-lg font-semibold">
                  Connecting to Paradise...
                </p>
                <p className="text-sm text-muted-foreground">
                  Establishing connection to LiveKit room...
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Main Content - Voice Agent View */}
        {isConnected && (
          <>
            <VoiceAgentView onMessagesChange={handleMessagesChange} />

            <div className="bg-card rounded-lg border p-6">
              <h2 className="text-xl font-semibold mb-4">Upload Travel PDF</h2>
              <PDFUpload />
            </div>
          </>
        )}

        {/* Full Transcript (when disconnected) */}
        {!isConnected && transcriptMessages.length > 0 && (
          <div className="bg-card rounded-lg border p-6">
            <FullTranscript messages={transcriptMessages} />
          </div>
        )}

        {/* Empty State */}
        {!isConnected && transcriptMessages.length === 0 && !isConnecting && (
          <div className="text-center text-sm text-muted-foreground py-12">
            <p>Click "Start Call" to begin your conversation with Paradise.</p>
            <p className="mt-2 text-xs">
              Make sure the backend API server is running and configured with
              LiveKit credentials.
            </p>
          </div>
        )}

        {/* Controls and Audio Renderer */}
        {isConnected && (
          <>
            <VoiceAssistantControlBar />
            <RoomAudioRenderer />
          </>
        )}
      </div>
    </div>
  );
}

function App() {
  // Create token source using TokenSource.custom() - memoize to avoid recreating on each render
  const tokenSource = useMemo(() => {
    return createTokenSource();
  }, []);

  // Create session using useSession hook with token source
  const session = useSession(tokenSource);

  return (
    <SessionProvider session={session}>
      <AppContent session={session} />
    </SessionProvider>
  );
}

export default App;
