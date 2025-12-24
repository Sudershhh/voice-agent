import { ConnectionState } from "livekit-client";
import { motion } from "framer-motion";

interface ConnectionStatusProps {
  className?: string;
  connectionState: ConnectionState;
  isAgentConnected?: boolean;
}

export function ConnectionStatus({ className, connectionState, isAgentConnected }: ConnectionStatusProps) {

  const getStatusInfo = () => {
    const state = typeof connectionState === "string" 
      ? connectionState 
      : connectionState;

    if ((state === ConnectionState.Connected || state === "connected") && isAgentConnected) {
      return {
        label: "Connected",
        color: "bg-green-500",
        textColor: "text-green-600 dark:text-green-400",
      };
    }

    switch (state) {
      case ConnectionState.Connected:
      case "connected":
        return {
          label: "Connecting...",
          color: "bg-yellow-500",
          textColor: "text-yellow-600 dark:text-yellow-400",
        };
      case ConnectionState.Connecting:
      case "connecting":
        return {
          label: "Connecting",
          color: "bg-yellow-500",
          textColor: "text-yellow-600 dark:text-yellow-400",
        };
      case ConnectionState.Disconnected:
      case "disconnected":
        return {
          label: "Disconnected",
          color: "bg-gray-400",
          textColor: "text-muted-foreground",
        };
      case ConnectionState.Reconnecting:
      case "reconnecting":
        return {
          label: "Reconnecting",
          color: "bg-yellow-500 animate-pulse",
          textColor: "text-yellow-600 dark:text-yellow-400",
        };
      default:
        return {
          label: "Unknown",
          color: "bg-gray-400",
          textColor: "text-muted-foreground",
        };
    }
  };

  const status = getStatusInfo();

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.2 }}
      className={`flex items-center gap-2 ${className || ""}`}
    >
      <motion.div
        className={`h-3 w-3 rounded-full transition-colors ${status.color}`}
        animate={status.label === "Connected" ? { scale: [1, 1.2, 1] } : {}}
        transition={{ duration: 2, repeat: Infinity, repeatDelay: 1 }}
      />
      <span className={`text-sm font-medium ${status.textColor}`}>
        {status.label}
      </span>
    </motion.div>
  );
}

