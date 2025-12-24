import { useState, useMemo } from "react";
import {
  SessionProvider,
  useSession,
  VoiceAssistantControlBar,
  RoomAudioRenderer,
  BarVisualizer,
  useVoiceAssistant,
} from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import { createTokenSource } from "@/lib/livekit";
import { environmentConfiguration } from "@/lib/config";
import { VoiceAgentView } from "@/components/VoiceAgentView";
import { FullTranscript } from "@/components/FullTranscript";
import { ConnectionStatus } from "@/components/ConnectionStatus";
import { HeroSection } from "@/components/HeroSection";
import type { TranscriptMessage } from "@/types/transcript";
import { Button } from "@/components/ui/button";
import { Phone } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface AppContentProps {
  session: ReturnType<typeof useSession>;
}

function AppContent({ session }: AppContentProps) {
  const [transcriptMessages, setTranscriptMessages] = useState<
    TranscriptMessage[]
  >([]);
  const [error, setError] = useState<string | null>(null);
  const [isAgentConnected, setIsAgentConnected] = useState(false);
  const { state, audioTrack } = useVoiceAssistant();

  const handleStartCall = async () => {
    try {
      setError(null);
      await session.start();
    } catch (err) {
      let errorMessage: string;

      if (err instanceof Error) {
        const errorMsg = err.message;

        if (
          errorMsg.includes("URL") ||
          errorMsg.includes("Invalid URL") ||
          errorMsg.includes("wss://") ||
          errorMsg.includes("ws://")
        ) {
          errorMessage =
            errorMsg +
            "\n\nTip: Check your backend .env file and ensure LIVEKIT_URL is set correctly (e.g., wss://your-project.livekit.cloud)";
        } else if (errorMsg.includes("Token") || errorMsg.includes("token")) {
          errorMessage =
            errorMsg +
            "\n\nTip: Verify your backend .env has LIVEKIT_API_KEY and LIVEKIT_API_SECRET configured";
        } else if (
          errorMsg.includes("Failed to fetch") ||
          errorMsg.includes("NetworkError") ||
          errorMsg.includes("fetch")
        ) {
          errorMessage =
            "Failed to connect to backend API.\n\nTip: Make sure your backend server is running on " +
            environmentConfiguration.apiUrl;
        } else {
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

  const handleMessagesChange = (messages: TranscriptMessage[]) => {
    setTranscriptMessages(messages);
  };

  const handleAgentConnectionChange = (connected: boolean) => {
    setIsAgentConnected(connected);
  };

  const connectionState = session.connectionState;
  const isConnected = connectionState === ConnectionState.Connected;
  const isConnecting =
    connectionState === ConnectionState.Connecting ||
    connectionState === ConnectionState.Reconnecting;

  return (
    <div className="min-h-screen bg-background">
      <AnimatePresence mode="wait">
        {!isConnected ? (
          <motion.div
            key="initial"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="h-screen flex flex-col overflow-hidden relative"
          >
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="absolute top-4 left-1/2 transform -translate-x-1/2 z-50 w-full max-w-2xl px-4"
                >
                  <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4 shadow-sm">
                    <p className="text-sm text-destructive whitespace-pre-line">
                      {error}
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {transcriptMessages.length === 0 ? (
              <>
                {isConnecting ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="h-screen flex items-center justify-center"
                  >
                    <div className="bg-card rounded-lg border border-border shadow-sm p-6">
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
                  </motion.div>
                ) : (
                  <HeroSection
                    onStartCall={handleStartCall}
                    isConnecting={isConnecting}
                  />
                )}
              </>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="flex-1 min-h-0 flex flex-col items-center justify-center gap-6 p-8"
              >
                <div className="w-full max-w-4xl bg-card rounded-lg border border-border shadow-lg p-6 flex flex-col h-full max-h-[70vh] overflow-hidden">
                  <FullTranscript messages={transcriptMessages} />
                </div>
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: 0.2 }}
                  className="flex justify-center"
                >
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Button
                      onClick={handleStartCall}
                      size="lg"
                      className="gap-2"
                    >
                      <Phone className="h-5 w-5" />
                      Start New Call
                    </Button>
                  </motion.div>
                </motion.div>
              </motion.div>
            )}
          </motion.div>
        ) : (
          <motion.div
            key="call"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="min-h-screen w-full"
          >
            <motion.header
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              className="bg-card border-b border-border shadow-sm p-4 flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                <h1 className="text-2xl font-bold text-foreground">Paradise</h1>
                {isAgentConnected && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3 }}
                  >
                    <ConnectionStatus
                      connectionState={session.connectionState}
                      isAgentConnected={isAgentConnected}
                    />
                  </motion.div>
                )}
              </div>
            </motion.header>

            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="bg-destructive/10 border-b border-destructive/20 p-4"
                >
                  <p className="text-sm text-destructive whitespace-pre-line">
                    {error}
                  </p>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="flex flex-col h-[calc(100vh-64px)]">
              <div className="flex-1 min-h-0">
                <VoiceAgentView
                  onMessagesChange={handleMessagesChange}
                  onAgentConnectionChange={handleAgentConnectionChange}
                />
              </div>

              <div className="border-t border-border bg-muted/30 backdrop-blur-sm">
                <div className="max-w-full mx-auto px-4 py-1.5">
                  <VoiceAssistantControlBar />
                  {audioTrack && (
                    <div className="flex justify-center items-center mt-1.5 gap-2">
                      <span className="text-xs font-medium text-muted-foreground">
                        Agent:
                      </span>
                      <BarVisualizer
                        state={state}
                        track={audioTrack}
                        barCount={12}
                        options={{ minHeight: 25, maxHeight: 100 }}
                        className="agent-visualizer"
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
            <RoomAudioRenderer />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function App() {
  const tokenSource = useMemo(() => {
    return createTokenSource();
  }, []);

  const session = useSession(tokenSource);

  return (
    <SessionProvider session={session}>
      <AppContent session={session} />
    </SessionProvider>
  );
}

export default App;
