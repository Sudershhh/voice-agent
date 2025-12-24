import {
  useVoiceAssistant,
  useRemoteParticipants,
} from "@livekit/components-react";
import { Track } from "livekit-client";
import { Transcript } from "./Transcript";
import { PDFUpload } from "./PDFUpload";
import type { TranscriptMessage } from "@/types/transcript";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useMemo } from "react";
import {
  Plane,
  Hotel,
  UtensilsCrossed,
  BookOpen,
  Calendar,
} from "lucide-react";

interface VoiceAgentViewProps {
  onMessagesChange?: (messages: TranscriptMessage[]) => void;
  onAgentConnectionChange?: (connected: boolean) => void;
}

const capabilities = [
  {
    icon: Plane,
    title: "Flight Planning",
    description: "Find and compare flight prices",
    color: "text-primary",
  },
  {
    icon: Hotel,
    title: "Hotel Recommendations",
    description: "Search for accommodations",
    color: "text-secondary",
  },
  {
    icon: UtensilsCrossed,
    title: "Restaurant Suggestions",
    description: "Find dining options",
    color: "text-accent",
  },
  {
    icon: BookOpen,
    title: "Travel Guides",
    description: "Access information from uploaded PDFs",
    color: "text-primary",
  },
  {
    icon: Calendar,
    title: "Itinerary Planning",
    description: "Create complete day-by-day plans",
    color: "text-secondary",
  },
];

export function VoiceAgentView({
  onMessagesChange,
  onAgentConnectionChange,
}: VoiceAgentViewProps) {
  const { audioTrack } = useVoiceAssistant();
  const remoteParticipants = useRemoteParticipants();

  const hasAgentTrack = useMemo(() => {
    if (audioTrack) {
      return true;
    }

    for (const participant of remoteParticipants) {
      if (participant.isLocal) continue;

      for (const publication of participant.trackPublications.values()) {
        if (
          publication.kind === Track.Kind.Audio &&
          publication.track &&
          (publication.trackName === "agent-voice" ||
            publication.source === Track.Source.Unknown)
        ) {
          return true;
        }
      }
    }

    return false;
  }, [audioTrack, remoteParticipants]);

  const isAgentConnected = !!audioTrack || hasAgentTrack;

  useEffect(() => {
    if (onAgentConnectionChange) {
      onAgentConnectionChange(isAgentConnected);
    }
  }, [isAgentConnected, onAgentConnectionChange]);

  return (
    <div className="flex h-full w-full">
      <motion.div
        initial={{ x: -50, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="w-[40%] flex flex-col p-4 gap-4 border-r border-border bg-background"
      >
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="bg-card rounded-lg border border-border shadow-sm p-4 flex-1 min-h-0 overflow-y-auto custom-scrollbar"
        >
          <AnimatePresence mode="wait">
            {isAgentConnected ? (
              <motion.div
                key="capabilities"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4 }}
                className="h-full flex flex-col"
              >
                <div className="mb-4">
                  <h2 className="text-lg font-bold text-foreground mb-1">
                    What I Can Help With
                  </h2>
                  <p className="text-xs text-muted-foreground">
                    Paradise is your comprehensive travel planning assistant
                  </p>
                </div>
                <div className="space-y-2 flex-1 mb-6">
                  {capabilities.map((capability, index) => {
                    const Icon = capability.icon;
                    return (
                      <motion.div
                        key={capability.title}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.05 * index, duration: 0.3 }}
                        className="flex items-center gap-3 p-2.5 rounded-md bg-muted/50 hover:bg-muted transition-colors border border-transparent hover:border-border"
                      >
                        <div
                          className={`p-1.5 rounded-md bg-background ${capability.color} shrink-0`}
                        >
                          <Icon className="h-4 w-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-semibold text-foreground leading-tight">
                            {capability.title}
                          </h3>
                          <p className="text-xs text-muted-foreground leading-tight">
                            {capability.description}
                          </p>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="waiting"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="flex flex-col items-center justify-center space-y-4 h-full"
              >
                <div className="animate-pulse">
                  <div className="w-32 h-32 rounded-full bg-muted flex items-center justify-center">
                    <div className="w-16 h-16 rounded-full bg-primary/20"></div>
                  </div>
                </div>
                <div className="text-center space-y-2">
                  <div className="text-sm font-medium text-muted-foreground">
                    Waiting for agent to connect...
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Agent capabilities will appear here once connected
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="bg-card rounded-lg border border-border shadow-sm p-4"
        >
          <h2 className="text-lg font-semibold mb-3 text-foreground">
            Upload Travel PDF
          </h2>
          <PDFUpload />
        </motion.div>
      </motion.div>

      <motion.div
        initial={{ x: 50, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.4, ease: "easeOut", delay: 0.1 }}
        className="w-[60%] bg-card border-l border-border p-4 flex flex-col h-full"
      >
        <motion.h2
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="text-lg font-semibold mb-3 text-foreground"
        >
          Live Transcript
        </motion.h2>
        <div className="flex-1 min-h-0 overflow-hidden">
          <Transcript onMessagesChange={onMessagesChange} />
        </div>
      </motion.div>
    </div>
  );
}
