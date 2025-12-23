import { useVoiceAssistant, BarVisualizer } from "@livekit/components-react";
import { Transcript } from "./Transcript";
import type { TranscriptMessage } from "@/types/transcript";

interface VoiceAgentViewProps {
  onMessagesChange?: (messages: TranscriptMessage[]) => void;
}

const getStateLabel = (state: string): string => {
  switch (state) {
    case "listening":
      return "Listening";
    case "thinking":
      return "Thinking";
    case "speaking":
      return "Speaking";
    case "initializing":
      return "Initializing";
    default:
      return state;
  }
};

const getStateColor = (state: string): string => {
  switch (state) {
    case "listening":
      return "text-primary";
    case "thinking":
      return "text-secondary";
    case "speaking":
      return "text-accent";
    case "initializing":
      return "text-muted-foreground";
    default:
      return "text-foreground";
  }
};

export function VoiceAgentView({ onMessagesChange }: VoiceAgentViewProps) {
  const { state, audioTrack } = useVoiceAssistant();

  return (
    <div className="space-y-6">
      {/* Agent State and Visualizer */}
      <div className="bg-card rounded-lg border p-6">
        <div className="flex flex-col items-center justify-center space-y-4">
          {/* Audio Visualizer */}
          {audioTrack && (
            <div className="w-full max-w-md">
              <BarVisualizer trackRef={audioTrack} state={state} barCount={5} />
            </div>
          )}

          {/* State Indicator */}
          <div className="flex flex-col items-center space-y-2">
            <div
              className={`text-sm font-medium transition-colors ${getStateColor(
                state
              )}`}
            >
              {getStateLabel(state)}
            </div>
            {!audioTrack && (
              <div className="text-xs text-muted-foreground">
                Waiting for agent to connect...
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Live Transcript */}
      <div className="bg-card rounded-lg border p-6">
        <h2 className="text-xl font-semibold mb-4">Live Transcript</h2>
        <Transcript onMessagesChange={onMessagesChange} />
      </div>
    </div>
  );
}
