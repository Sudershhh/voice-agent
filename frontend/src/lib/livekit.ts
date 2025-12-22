import { Room, RoomEvent, RemoteParticipant, LocalParticipant, Track, RemoteAudioTrack } from "livekit-client";

export interface LiveKitConfig {
  url: string;
  token: string;
}

export class LiveKitManager {
  private room: Room | null = null;
  private onConnectionChange?: (connected: boolean) => void;
  private onTranscriptUpdate?: (transcript: string, isUser: boolean) => void;
  private audioElements: Map<string, HTMLAudioElement> = new Map();

  constructor() {
    this.room = new Room();
    this.setupEventListeners();
  }

  private setupEventListeners() {
    if (!this.room) return;

    this.room.on(RoomEvent.Connected, () => {
      this.onConnectionChange?.(true);
    });

    this.room.on(RoomEvent.Disconnected, () => {
      this.onConnectionChange?.(false);
    });

    this.room.on(RoomEvent.ParticipantConnected, (participant: RemoteParticipant) => {
    });

    this.room.on(RoomEvent.ParticipantDisconnected, (participant: RemoteParticipant) => {
    });

    this.room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
      if (track.kind === Track.Kind.Audio && participant !== this.room.localParticipant) {
        const remoteAudioTrack = track as RemoteAudioTrack;
        const audioElement = remoteAudioTrack.attach() as HTMLAudioElement;
        audioElement.autoplay = true;
        
        const trackId = `${participant.identity}-${track.sid}`;
        this.audioElements.set(trackId, audioElement);
        
        audioElement.play().catch((err) => {
        });
      } else if (track.kind === Track.Kind.Video) {
      }
    });

    this.room.on(RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
      if (!this.room) {
        return;
      }
      
      try {
        if (track.kind === Track.Kind.Audio && participant !== this.room.localParticipant) {
          const trackId = `${participant.identity}-${track.sid}`;
          const audioElement = this.audioElements.get(trackId);
          if (audioElement) {
            track.detach(audioElement);
            this.audioElements.delete(trackId);
          }
        }
      } catch (error) {
      }
    });
  }

  async connect(config: LiveKitConfig): Promise<void> {
    if (!this.room) {
      this.room = new Room();
      this.setupEventListeners();
    }

    try {
      await this.room.connect(config.url, config.token);
      
      try {
        await this.room.localParticipant.enableCameraAndMicrophone(false, true);
      } catch (error: any) {
        if (error.name === 'NotFoundError' || error.message?.includes('device not found')) {
        } else {
        }
      }
    } catch (error) {
      throw error;
    }
  }

  async disconnect(): Promise<void> {
    if (!this.room) {
      return;
    }
    
    try {
      this.audioElements.forEach((audioElement, trackId) => {
        try {
          audioElement.pause();
          audioElement.src = "";
        } catch (error) {
        }
      });
      this.audioElements.clear();
      
      if (this.room.localParticipant) {
        try {
          await this.room.localParticipant.setCameraEnabled(false);
          await this.room.localParticipant.setMicrophoneEnabled(false);
        } catch (error) {
        }
      }
      
      this.room.disconnect();
    } catch (error) {
    } finally {
      this.room = null;
    }
  }

  isConnected(): boolean {
    return this.room?.state === "connected";
  }

  getRoom(): Room | null {
    return this.room;
  }

  setOnConnectionChange(callback: (connected: boolean) => void) {
    this.onConnectionChange = callback;
  }

  setOnTranscriptUpdate(callback: (transcript: string, isUser: boolean) => void) {
    this.onTranscriptUpdate = callback;
  }
}

