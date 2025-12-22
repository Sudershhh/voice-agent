# Paradise - RAG-Enabled Travel Voice Agent

An interactive travel planning voice agent that helps users plan trips using LiveKit for real-time voice communication, LangChain RAG pipeline for PDF travel knowledge retrieval, and real-time tools for flight pricing and location suggestions.

## Features

- **Real-time Voice Conversation**: Speak naturally with Paradise using WebRTC
- **Live Transcription**: See your words and Paradise's responses in real-time
- **RAG-Powered Knowledge**: Answer questions from uploaded travel PDFs
- **Flight Price Lookup**: Get real-time flight prices via SerpAPI
- **Places Search**: Find cafes, restaurants, hotels, and attractions via Google Places
- **PDF Upload**: Upload your own travel guides to enhance Paradise's knowledge

## Requirements

- Python 3.10+
- Node.js 18+
- LiveKit Cloud account (or self-hosted LiveKit server)
- OpenAI API key (for STT, embeddings, and LLM)
- Pinecone API key (for vector storage)
- Optional: SerpAPI key (for flight prices)
- Optional: Google Places API key (for places search)

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/Sudershhh/voice-agent.git
cd voice-agent
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
# Option 1: Using pyproject.toml (recommended)
pip install -e .

# Option 2: Using requirements.txt (alternative)
pip install -r requirements.txt

# Set up environment variables
# Copy .env.example to .env
# On Windows:
copy .env.example .env
# On Linux/Mac:
cp .env.example .env

# Edit .env with your API keys (see Configuration section below)
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
# Copy .env.example to .env (or create .env.example and copy it)
cp .env.example .env
# On Windows: copy .env.example .env
# Edit .env with your API keys (see Configuration section below)
```

### 4. Run the Application

**Terminal 1 - Backend Agent:**

```bash
cd backend
python main.py dev
```

**Terminal 2 - Backend API Server (Required for communicating with frontend):**

```bash
cd backend
python api/server.py
```

This server provides:

- LiveKit token generation endpoint (`/api/token`)
- PDF upload endpoint (`/upload-pdf`)

**Terminal 3 - Frontend:**

```bash
cd frontend
npm run dev
```

## Configuration

### Environment Variable Files

Both `backend/.env.example` and `frontend/.env.example` contain template environment variables with detailed comments.

**To set up:**

1. Copy `.env.example` to `.env` in each directory
2. Fill in your actual API keys and configuration values
3. Never commit `.env` files to version control

### Backend Environment Variables

Create `backend/.env` with:

```env
# LiveKit Configuration (Required)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# OpenAI Configuration (Required)
OPENAI_API_KEY=your-openai-api-key

# Pinecone Configuration (Required for RAG)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment  # Usually not needed for serverless
PINECONE_INDEX_NAME=paradise-travel-index

# Optional API Keys (for Tools)
SERPAPI_API_KEY=your-serpapi-key  # For flight prices
GOOGLE_PLACES_API_KEY=your-google-places-key  # For places search
```

### Frontend Environment Variables

**Important:** Vite requires the `VITE_` prefix for all environment variables to be accessible in the frontend code.

Create `frontend/.env` with:

```env
VITE_API_URL=http://localhost:8000
```

**Important Notes:**

- All frontend environment variables **must** start with `VITE_` prefix
- LiveKit tokens are generated server-side
- The frontend automatically fetches tokens from the backend API at `/api/token`
- The backend uses `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` from its `.env` to generate tokens securely
- Make sure the backend API server is running before starting the frontend

## Project Structure

```
voice-agent/
├── backend/
│   ├── agent/
│   │   ├── basic_agent.py      # Main LiveKit agent
│   │   └── langchain_agent.py  # LangChain agent setup
│   ├── rag/
│   │   ├── pdf_processor.py    # PDF processing
│   │   └── retriever.py        # Pinecone integration
│   ├── tools/
│   │   ├── flights.py          # Flight prices tool
│   │   └── places.py           # Places search tool
│   ├── api/
│   │   ├── upload.py           # PDF upload endpoint
│   │   └── server.py           # API server
│   ├── scripts/
│   │   └── load_pdf.py         # PDF loading script
│   ├── data/                    # Place PDFs here
│   ├── main.py                  # Agent entry point
│   └── pyproject.toml           # Dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CallControls.tsx
│   │   │   ├── Transcript.tsx
│   │   │   ├── PDFUpload.tsx
│   │   │   └── ToolResults.tsx
│   │   ├── lib/
│   │   │   └── livekit.ts       # LiveKit client
│   │   └── App.tsx
│   └── package.json
├── README.md
└── DESIGN.md                    # Detailed design document
```
