import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Phone, PhoneOff } from "lucide-react";

interface CallControlsProps {
  onStartCall: () => void;
  onEndCall: () => void;
  isConnected: boolean;
  isConnecting: boolean;
}

export function CallControls({
  onStartCall,
  onEndCall,
  isConnected,
  isConnecting,
}: CallControlsProps) {
  return (
    <div className="flex gap-4 items-center">
      {!isConnected ? (
        <Button
          onClick={onStartCall}
          disabled={isConnecting}
          size="lg"
          className="gap-2"
        >
          <Phone className="h-5 w-5" />
          {isConnecting ? "Connecting..." : "Start Call"}
        </Button>
      ) : (
        <Button
          onClick={onEndCall}
          variant="destructive"
          size="lg"
          className="gap-2"
        >
          <PhoneOff className="h-5 w-5" />
          End Call
        </Button>
      )}
      <div className="flex items-center gap-2">
        <div
          className={`h-3 w-3 rounded-full ${
            isConnected ? "bg-green-500" : "bg-gray-400"
          }`}
        />
        <span className="text-sm text-muted-foreground">
          {isConnected ? "Connected" : "Disconnected"}
        </span>
      </div>
    </div>
  );
}

