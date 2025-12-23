import React from "react";
import type { TranscriptMessage } from "@/types/transcript";

interface FullTranscriptProps {
  messages: TranscriptMessage[];
}

const formatTime = (timestamp: number): string => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
};

const formatFullDateTime = (timestamp: number): string => {
  const date = new Date(timestamp);
  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export function FullTranscript({ messages }: FullTranscriptProps) {
  if (messages.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        <p>No transcript available yet.</p>
      </div>
    );
  }

  const copyToClipboard = () => {
    const transcriptText = messages
      .map((msg) => {
        const speaker = msg.is_user ? "You" : "Paradise";
        const time = formatTime(msg.timestamp);
        return `[${time}] ${speaker}: ${msg.text}`;
      })
      .join("\n");

    navigator.clipboard.writeText(transcriptText).then(() => {
      alert("Transcript copied to clipboard!");
    });
  };

  const exportAsText = () => {
    const transcriptText = messages
      .map((msg) => {
        const speaker = msg.is_user ? "You" : "Paradise";
        const time = formatFullDateTime(msg.timestamp);
        return `[${time}] ${speaker}: ${msg.text}`;
      })
      .join("\n\n");

    const blob = new Blob([transcriptText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `paradise-transcript-${new Date().toISOString().split("T")[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Full Transcript</h3>
        <div className="flex gap-2">
          <button
            onClick={copyToClipboard}
            className="px-3 py-1.5 text-sm bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
          >
            Copy
          </button>
          <button
            onClick={exportAsText}
            className="px-3 py-1.5 text-sm bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
          >
            Export
          </button>
        </div>
      </div>

      <div className="bg-muted/50 rounded-lg p-4 max-h-[600px] overflow-y-auto">
        <div className="space-y-4">
          {messages.map((msg, idx) => {
            const isNewDay =
              idx === 0 ||
              new Date(msg.timestamp).toDateString() !==
                new Date(messages[idx - 1].timestamp).toDateString();

            return (
              <React.Fragment key={msg.id}>
                {isNewDay && idx > 0 && (
                  <div className="text-center text-xs text-muted-foreground py-2 border-t border-border">
                    {new Date(msg.timestamp).toLocaleDateString([], {
                      weekday: "long",
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </div>
                )}
                {idx === 0 && (
                  <div className="text-center text-xs text-muted-foreground py-2">
                    {new Date(msg.timestamp).toLocaleDateString([], {
                      weekday: "long",
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </div>
                )}
                <div
                  className={`flex ${msg.is_user ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-lg px-4 py-2.5 ${
                      msg.is_user
                        ? "bg-primary text-primary-foreground"
                        : "bg-background border border-border text-foreground"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="text-xs font-semibold opacity-90">
                        {msg.is_user ? "You" : "Paradise"}
                      </div>
                      <div className="text-xs opacity-70 ml-2">
                        {formatTime(msg.timestamp)}
                      </div>
                    </div>
                    <div className="text-sm leading-relaxed whitespace-pre-wrap">
                      {msg.text}
                    </div>
                  </div>
                </div>
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}

