import React, { useEffect, useRef, useState } from "react";
import { RoomEvent, DataPacket_Kind } from "livekit-client";
import { useRoomContext } from "@livekit/components-react";
import type { TranscriptMessage } from "@/types/transcript";
import { motion, AnimatePresence } from "framer-motion";

interface TranscriptProps {
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

export function Transcript({ onMessagesChange }: TranscriptProps) {
  const room = useRoomContext();
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
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center text-muted-foreground py-8 h-full flex items-center justify-center"
      >
        <div className="space-y-2">
          <p className="text-sm">Start speaking to see your transcript here...</p>
          <p className="text-xs opacity-70">Messages will appear in real-time</p>
        </div>
      </motion.div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
        <AnimatePresence initial={false}>
          {messages.map((msg, index) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{
                duration: 0.3,
                delay: index === messages.length - 1 ? 0 : 0,
              }}
              className={`flex ${msg.is_user ? "justify-end" : "justify-start"}`}
            >
              <motion.div
                className={`transcript-message max-w-[85%] rounded-lg px-4 py-2.5 shadow-sm transition-all ${
                  msg.is_user
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-foreground border border-border"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className={`text-xs font-semibold ${
                    msg.is_user ? "opacity-90" : "opacity-80"
                  }`}>
                    {msg.is_user ? "You" : "Paradise"}
                  </div>
                  <div className={`text-xs ml-2 ${
                    msg.is_user ? "opacity-70" : "opacity-60"
                  }`}>
                    {formatTime(msg.timestamp)}
                  </div>
                </div>
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.1 }}
                  className="text-sm leading-relaxed"
                >
                  {msg.text}
                </motion.div>
              </motion.div>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
