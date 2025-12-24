# Frontend - Paradise Voice Agent

The frontend is a React application built with TypeScript and Vite that provides the user interface for the Paradise voice agent.

## Overview

The frontend handles:
- Real-time voice communication via LiveKit WebRTC
- Live transcript display (user and agent messages)
- PDF upload interface
- Connection status and call controls
- Visual feedback for agent capabilities

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── VoiceAgentView.tsx      # Main voice agent interface
│   │   ├── Transcript.tsx           # Real-time transcript display
│   │   ├── FullTranscript.tsx      # Full conversation transcript
│   │   ├── PDFUpload.tsx            # PDF upload component
│   │   ├── CallControls.tsx         # Call start/end controls
│   │   ├── ConnectionStatus.tsx     # Connection status indicator
│   │   ├── HeroSection.tsx          # Landing page hero
│   │   ├── ToolResults.tsx          # Tool execution results display
│   │   └── ui/                      # Reusable UI components
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       └── globe.tsx            # 3D globe visualization
│   ├── lib/
│   │   ├── livekit.ts              # LiveKit client setup
│   │   ├── config.ts               # Environment configuration
│   │   └── utils.ts                # Utility functions
│   ├── types/
│   │   └── transcript.ts           # TypeScript types
│   ├── data/
│   │   └── globe.json              # Globe data
│   ├── assets/                     # Static assets
│   ├── App.tsx                     # Main app component
│   └── main.tsx                    # App entrypoint
├── public/                         # Public assets
├── package.json                    # Dependencies
└── vite.config.ts                  # Vite configuration
```

## Prerequisites

- Node.js 18 or higher
- npm or yarn package manager
- Backend API server running (for token generation)

## Setup Instructions

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
VITE_API_URL=http://localhost:8000
```

**Important**: 
- All frontend environment variables **must** start with the `VITE_` prefix
- The frontend fetches LiveKit tokens from the backend API at `/api/token`
- The backend API server must be running before starting the frontend

### 3. Run Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173` (or the port Vite assigns).

### 4. Build for Production

```bash
npm run build
```

The production build will be in the `dist/` directory.

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Backend API URL (default: `http://localhost:8000`) |

**Note**: LiveKit connection details (URL, token) are fetched from the backend API, not configured in the frontend.

## Components

### Core Components

**App.tsx**
- Main application component
- Manages LiveKit session and connection state
- Handles transcript messages and agent connection status
- Renders hero section or voice agent view based on connection state

**VoiceAgentView.tsx**
- Main voice agent interface
- Displays agent capabilities
- Shows real-time transcript
- Provides PDF upload interface
- Manages call controls

**Transcript.tsx**
- Real-time transcript display
- Shows user and agent messages
- Auto-scrolls to latest message
- Distinguishes user vs. agent messages

**FullTranscript.tsx**
- Full conversation transcript view
- Scrollable message history
- Message timestamps

**PDFUpload.tsx**
- PDF file upload interface
- Upload progress and status
- Error handling and validation

**CallControls.tsx**
- Start/end call buttons
- Connection status display
- Audio visualizer

**ConnectionStatus.tsx**
- Visual connection status indicator
- Shows connection state (connecting, connected, disconnected)

**HeroSection.tsx**
- Landing page hero section
- Call-to-action to start conversation
- Feature highlights

### UI Components

Located in `src/components/ui/`:
- **button.tsx**: Reusable button component
- **card.tsx**: Card container component
- **globe.tsx**: 3D globe visualization using Three.js

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### TypeScript

The project uses TypeScript for type safety. Types are defined in:
- `src/types/transcript.ts` - Transcript message types
- Component props are typed inline

### Styling

- **Tailwind CSS**: Utility-first CSS framework
- **Framer Motion**: Animation library
- **Radix UI**: Accessible component primitives

### LiveKit Integration

The frontend uses `@livekit/components-react` for LiveKit integration:

- **SessionProvider**: Manages LiveKit session
- **useSession**: Hook for session state
- **useVoiceAssistant**: Hook for voice assistant functionality
- **VoiceAssistantControlBar**: Pre-built control bar component
- **RoomAudioRenderer**: Handles audio rendering

Connection flow:
1. Frontend requests token from backend API (`/api/token`)
2. Backend generates LiveKit access token
3. Frontend connects to LiveKit Cloud using token
4. Agent joins room when user connects
5. Real-time audio and transcript data flows via WebRTC and data channels

## Common Issues

**Cannot connect to LiveKit**:
- Verify backend API server is running
- Check `VITE_API_URL` is set correctly
- Verify backend has valid LiveKit credentials

**Token generation fails**:
- Ensure backend `.env` has `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET`
- Check backend API server logs for errors

**PDF upload fails**:
- Verify backend API server is running
- Check file size (max 10MB)
- Ensure backend has `PINECONE_API_KEY` configured

**No audio**:
- Check browser permissions for microphone access
- Verify LiveKit connection is established
- Check browser console for WebRTC errors

## Dependencies

Key dependencies (see `package.json` for full list):

- **React 19**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool and dev server
- **@livekit/components-react**: LiveKit React components
- **livekit-client**: LiveKit client SDK
- **framer-motion**: Animations
- **tailwindcss**: Styling
- **@react-three/fiber**: 3D rendering (for globe)
- **three-globe**: Globe visualization

## See Also

- [Main README](../README.md) - Project overview
- [Backend README](../backend/README.md) - Backend setup
- [Design Document](../DESIGN.md) - System architecture
