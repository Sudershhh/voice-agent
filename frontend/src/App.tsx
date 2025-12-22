import { useState, useEffect } from "react";
import { CallControls } from "@/components/CallControls";
import { Transcript } from "@/components/Transcript";
import { FullTranscript } from "@/components/FullTranscript";
import { PDFUpload } from "@/components/PDFUpload";
import { LiveKitManager } from "@/lib/livekit";
import { getApiUrl, environmentConfiguration } from "@/lib/config";

interface TranscriptMessage {
  text: string;
  is_user: boolean;
  timestamp: number;
  id: string;
}

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isAgentReady, setIsAgentReady] = useState(false);
  const [transcriptMessages, setTranscriptMessages] = useState<
    TranscriptMessage[]
  >([]);
  const [liveKitManager] = useState(() => new LiveKitManager());

  useEffect(() => {
    liveKitManager.setOnConnectionChange((connected) => {
      setIsConnected(connected);
      setIsConnecting(false);
      if (!connected) {
        setIsAgentReady(false);
      }
    });

    return () => {
      liveKitManager.disconnect();
    };
  }, [liveKitManager]);

  useEffect(() => {
    if (isConnected && !isAgentReady) {
      if (transcriptMessages.length > 0) {
        setIsAgentReady(true);
        return;
      }

      const timer = setTimeout(() => {
        setIsAgentReady(true);
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, [isConnected, isAgentReady, transcriptMessages]);

  const handleStartCall = async () => {
    setIsConnecting(true);
    try {
      const tokenResponse = await fetch(
        getApiUrl(environmentConfiguration.endpoints.token),
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            identity: `user-${Date.now()}`,
            name: "User",
            room: "paradise-room",
          }),
        }
      );

      if (!tokenResponse.ok) {
        const error = await tokenResponse.json();
        throw new Error(error.detail || "Failed to get LiveKit token");
      }

      const { token, url } = await tokenResponse.json();

      const config = {
        url: url,
        token: token,
      };

      await liveKitManager.connect(config);
    } catch (error) {
      alert(
        `Failed to connect: ${
          error instanceof Error ? error.message : "Unknown error"
        }\n\nMake sure:\n1. Backend API server is running (python backend/api/server.py)\n2. Backend .env has LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET configured`
      );
      setIsConnecting(false);
    }
  };

  const handleEndCall = async () => {
    await liveKitManager.disconnect();
    setIsConnected(false);
    setIsAgentReady(false);
  };

  const handleMessagesChange = (messages: TranscriptMessage[]) => {
    setTranscriptMessages(messages);
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold">Paradise</h1>
          <p className="text-muted-foreground">
            Your AI travel planning voice agent
          </p>
        </div>

        <div className="flex justify-center">
          <CallControls
            onStartCall={handleStartCall}
            onEndCall={handleEndCall}
            isConnected={isConnected}
            isConnecting={isConnecting}
          />
        </div>

        {(isConnecting || (isConnected && !isAgentReady)) && (
          <div className="bg-card rounded-lg border p-6">
            <div className="flex flex-col items-center justify-center py-12 space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              <div className="text-center space-y-2">
                <p className="text-lg font-semibold">
                  {isConnecting
                    ? "Connecting to Paradise..."
                    : "Agent is setting up..."}
                </p>
                <p className="text-sm text-muted-foreground">
                  {isConnecting
                    ? "Establishing connection to LiveKit room..."
                    : "Paradise is getting ready to help you plan your trip..."}
                </p>
              </div>
            </div>
          </div>
        )}

        {isConnected && isAgentReady && (
          <>
            <div className="bg-card rounded-lg border p-6">
              <h2 className="text-xl font-semibold mb-4">Live Transcript</h2>
              <Transcript
                room={liveKitManager.getRoom()}
                onMessagesChange={handleMessagesChange}
              />
            </div>

            <div className="bg-card rounded-lg border p-6">
              <h2 className="text-xl font-semibold mb-4">Upload Travel PDF</h2>
              <PDFUpload />
            </div>
          </>
        )}

        {!isConnected && transcriptMessages.length > 0 && (
          <div className="bg-card rounded-lg border p-6">
            <FullTranscript messages={transcriptMessages} />
          </div>
        )}

        {!isConnected && transcriptMessages.length === 0 && (
          <div className="text-center text-sm text-muted-foreground">
            <p>Click "Start Call" to begin your conversation with Paradise.</p>
            <p className="mt-2 text-xs">
              Make sure the backend API server is running and configured with
              LiveKit credentials.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
