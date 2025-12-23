import { ConnectionState } from "livekit-client";

interface ConnectionStatusProps {
  className?: string;
  connectionState: ConnectionState;
}

export function ConnectionStatus({ className, connectionState }: ConnectionStatusProps) {

  const getStatusInfo = () => {
    // connectionState can be a string or ConnectionState enum
    const state = typeof connectionState === "string" 
      ? connectionState 
      : connectionState;

    switch (state) {
      case ConnectionState.Connected:
      case "connected":
        return {
          label: "Connected",
          color: "bg-green-500",
          textColor: "text-green-600 dark:text-green-400",
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
    <div className={`flex items-center gap-2 ${className || ""}`}>
      <div
        className={`h-3 w-3 rounded-full transition-colors ${status.color}`}
      />
      <span className={`text-sm font-medium ${status.textColor}`}>
        {status.label}
      </span>
    </div>
  );
}

