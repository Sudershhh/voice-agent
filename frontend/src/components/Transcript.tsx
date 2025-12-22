import React, { useEffect, useRef, useState } from "react";
import { Room, RoomEvent, DataPacket_Kind } from "livekit-client";

interface TranscriptMessage {
  text: string;
  is_user: boolean;
  timestamp: number;
  id: string;
}

interface TranscriptProps {
  room: Room | null;
  onMessagesChange?: (messages: TranscriptMessage[]) => void;
}

const isDuplicate = (newMsg: TranscriptMessage, existing: TranscriptMessage[]): boolean => {
  return existing.some(
    (msg) =>
      msg.text === newMsg.text &&
      msg.is_user === newMsg.is_user &&
      Math.abs(msg.timestamp - newMsg.timestamp) < 1000
  );
};

const formatTime = (timestamp: number): string => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
};

export function Transcript({ room, onMessagesChange }: TranscriptProps) {
  const [messages, setMessages] = useState<TranscriptMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!room) return;

    const handleData = (payload: Uint8Array, kind?: DataPacket_Kind) => {
      try {
        const data = JSON.parse(new TextDecoder().decode(payload));
        if (data.type === "transcript") {
          const newMessage: TranscriptMessage = {
            text: data.text,
            is_user: data.is_user,
            timestamp: Date.now(),
            id: `${Date.now()}-${Math.random()}`,
          };

          setMessages((prev) => {
            if (isDuplicate(newMessage, prev)) {
              return prev;
            }
            return [...prev, newMessage];
          });
        }
      } catch (error) {
      }
    };

    room.on(RoomEvent.DataReceived, handleData);

    return () => {
      room.off(RoomEvent.DataReceived, handleData);
    };
  }, [room, onMessagesChange]);

  useEffect(() => {
    if (onMessagesChange) {
      onMessagesChange(messages);
    }
  }, [messages, onMessagesChange]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        <p>Start speaking to see your transcript here...</p>
      </div>
    );
  }

  return (
    <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex ${msg.is_user ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-2 duration-300`}
        >
          <div
            className={`max-w-[80%] rounded-lg px-4 py-2.5 shadow-sm transition-all ${
              msg.is_user
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-foreground"
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
            <div className="text-sm leading-relaxed">{msg.text}</div>
          </div>
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
}
