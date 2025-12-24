# Backend - Paradise Voice Agent

The backend consists of a LiveKit agent that handles voice communication, a LangChain agent for orchestration, RAG pipeline for knowledge retrieval, and external tool integrations.

## Overview

The backend is a Python application that runs two main processes:

1. **LiveKit Agent** (`main.py`): Connects to LiveKit Cloud and handles real-time voice communication
2. **API Server** (`api/server.py`): Provides HTTP endpoints for token generation and PDF upload

## Project Structure

```
backend/
├── agent/
│   ├── basic_agent.py      # LiveKit agent entrypoint and audio handling
│   └── langchain_agent.py  # LangChain agent setup and tool orchestration
├── rag/
│   ├── pdf_processor.py    # PDF text extraction and chunking
│   ├── retriever.py        # Pinecone vector store and retrieval logic
│   ├── document_classifier.py  # Document type and destination extraction
│   └── storage_monitor.py  # Storage quota monitoring
├── tools/
│   ├── flights.py          # SerpAPI flight price search
│   ├── places.py           # Google Places API search
│   └── airport_codes.py    # Airport code mappings
├── api/
│   ├── server.py           # FastAPI server entrypoint
│   └── upload.py           # PDF upload and token generation endpoints
├── scripts/
│   └── load_pdf.py         # Script to load PDFs into vector store
├── data/                   # Place PDF files here for processing
├── config.py               # Environment variable configuration
├── main.py                 # Agent entrypoint
└── pyproject.toml          # Python dependencies
```

## Prerequisites

- Python 3.10 or higher
- LiveKit Cloud account (or self-hosted LiveKit server)
- OpenAI API key
- Pinecone API key
- Optional: SerpAPI key (for flight prices)
- Optional: Google Places API key (for places search)

## Setup Instructions

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

### 2. Install Dependencies

Using `pyproject.toml` (recommended):
```bash
pip install -e .
```

Or using `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# LiveKit Configuration (Required)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# OpenAI Configuration (Required)
OPENAI_API_KEY=your-openai-api-key

# Pinecone Configuration (Required for RAG)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=paradise-travel-index

# Optional API Keys (for Tools)
SERPAPI_API_KEY=your-serpapi-key
GOOGLE_PLACES_API_KEY=your-google-places-key
```

**Important**: Never commit `.env` files to version control.

### 4. Initialize Pinecone Index

The index will be created automatically on first use, but you can verify it exists:

```bash
python -c "from rag.retriever import initialize_pinecone, get_or_create_index; pc = initialize_pinecone(); idx = get_or_create_index(pc, 'paradise-travel-index')"
```

## Running the Application

### Start the LiveKit Agent

```bash
python main.py dev
```

The agent will:
- Connect to LiveKit Cloud using credentials from `.env`
- Wait for users to join rooms
- Handle voice communication and process queries

### Start the API Server

In a separate terminal:

```bash
python api/server.py
```

The API server runs on `http://localhost:8000` and provides:
- `POST /api/token` - Generate LiveKit access tokens
- `POST /upload-pdf` - Upload and process PDF files
- `GET /health` - Health check
- `GET /storage-status` - Check Pinecone storage usage
- `GET /api/indexes` - List Pinecone indexes
- `GET /api/indexes/{index_name}/namespaces` - List namespaces
- `GET /api/indexes/{index_name}/stats` - Get index statistics

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LIVEKIT_URL` | Yes | LiveKit WebSocket URL (e.g., `wss://your-project.livekit.cloud`) |
| `LIVEKIT_API_KEY` | Yes | LiveKit API key |
| `LIVEKIT_API_SECRET` | Yes | LiveKit API secret |
| `OPENAI_API_KEY` | Yes | OpenAI API key for STT, TTS, embeddings, and LLM |
| `PINECONE_API_KEY` | Yes* | Pinecone API key for vector storage |
| `PINECONE_INDEX_NAME` | No | Pinecone index name (default: `paradise-travel-index`) |
| `SERPAPI_API_KEY` | No | SerpAPI key for flight price search |
| `GOOGLE_PLACES_API_KEY` | No | Google Places API key for local business search |

*Required if RAG is enabled (default: enabled)

### Feature Flags

The agent automatically detects which features are available based on environment variables:

- **RAG**: Enabled if `PINECONE_API_KEY` is set
- **Tools**: Enabled if `SERPAPI_API_KEY` or `GOOGLE_PLACES_API_KEY` is set

## Architecture

### LiveKit Agent (`agent/basic_agent.py`)

**Purpose**: Handles real-time voice communication between user and agent

**Responsibilities**:
- Connects to LiveKit Cloud room when user joins
- Captures user audio track from room
- Publishes agent audio track to room
- Streams user audio to OpenAI Whisper for speech-to-text
- Receives agent text responses and synthesizes speech via OpenAI TTS
- Streams TTS audio back to user via WebRTC
- Sends transcripts (user and agent) via LiveKit data channels for frontend display
- Manages graceful shutdown and resource cleanup

**Key Components**:
- `entrypoint()`: Main function called when agent joins room
- Audio stream processing: Handles frame-by-frame audio from user
- STT event handling: Processes transcription events from Whisper
- TTS synthesis: Converts agent text to speech and streams to room

### LangChain Agent (`agent/langchain_agent.py`)

**Purpose**: Orchestrates tool selection, RAG retrieval, and response generation

**Responsibilities**:
- Creates LangChain agent executor with 3 tools (see Tools section)
- Manages conversation history across turns
- Routes user queries to appropriate tools based on intent
- Formats tool results into natural language responses
- Ensures voice-friendly output (short sentences, no markdown)

**Tool Integration**:
- **3 tools total**: `retrieve_travel_info` (RAG), `get_flight_prices` (SerpAPI), `search_places` (Google Places)
- Tool selection handled by LLM based on query intent
- Tool results passed back to LLM for response generation

**Key Functions**:
- `create_paradise_agent()`: Sets up agent with tools and RAG
- `get_agent_response()`: Processes user input and returns agent response
- `create_rag_tool()`: Wraps Pinecone retriever as LangChain tool
- `create_tools()`: Creates SerpAPI and Google Places tools

### RAG Pipeline

**Purpose**: Enables agent to answer questions from uploaded travel guide PDFs

**Components**:

1. **PDF Processing** (`rag/pdf_processor.py`):
   - Extracts text from PDF files using `pypdf`
   - Classifies document type (travel_guide, restaurant_guide, hotel_guide, etc.)
   - Extracts destination from filename or content
   - Chunks text using `RecursiveCharacterTextSplitter`:
     - Travel guides: 1500 chars per chunk, 300 char overlap
     - Restaurant/hotel guides: 800 chars per chunk, 150 char overlap
   - Detects sections (attractions, restaurants, hotels, transport, culture, tips)
   - Generates metadata for each chunk (destination, section, document title, source file)

2. **Document Classification** (`rag/document_classifier.py`):
   - Analyzes filename and content to determine document type
   - Extracts destination names (cities, countries) from filenames
   - Extracts destinations from document content using pattern matching
   - Handles multiple destinations in single query (e.g., "Zurich and Switzerland")
   - Maps cities to countries for hierarchical namespace organization

3. **Vector Storage** (`rag/retriever.py`):
   - Embeds text chunks using OpenAI `text-embedding-3-small` (1536 dimensions)
   - Stores vectors in Pinecone serverless index
   - Organizes documents by destination into hierarchical namespaces:
     - City namespace (e.g., "zurich")
     - Country namespace (e.g., "switzerland")
     - General namespace (fallback)
   - Stores metadata with each vector for filtering

4. **Retrieval** (`rag/retriever.py`):
   - Implements `FilteredRetriever` for metadata filtering
   - Searches namespaces hierarchically (city → country → general)
   - Applies metadata filters (destination, section type)
   - Returns top-k results (default: 5) with deduplication
   - Falls back to unfiltered search if no results found

5. **Storage Monitoring** (`rag/storage_monitor.py`):
   - Tracks Pinecone storage usage
   - Checks quota limits (free tier: 2GB)
   - Validates upload capacity before processing PDFs
   - Provides storage status via API endpoints

### Tools

**Purpose**: Enable agent to access real-time external data

1. **Flight Prices** (`tools/flights.py`):
   - **What it does**: Searches for flight prices between cities using SerpAPI
   - **Input**: Departure city, arrival city, date(s), flight type (one-way/round-trip)
   - **Output**: Flight options with prices, airlines, departure/arrival times, layovers
   - **Validation**: Validates destinations are real cities (not countries) using Google Maps Geocoding API
   - **Limitations**: SerpAPI free tier (100 searches/month) - no caching implemented
   - **Airport Codes** (`tools/airport_codes.py`): Maps city names to IATA airport codes

2. **Places Search** (`tools/places.py`):
   - **What it does**: Searches for local businesses using Google Places API
   - **Input**: Query (hotels, restaurants, cafes, attractions), location, place type
   - **Output**: Business names, addresses, ratings, reviews, contact info
   - **Use cases**: Hotel recommendations, restaurant suggestions, attraction search
   - **Limitations**: Google Places free tier ($200/month credit, ~40K requests) - no rate limiting
   - **Max results**: Limited to 5 per query to conserve API quota

### API Server (`api/server.py` and `api/upload.py`)

**Purpose**: Provides HTTP endpoints for frontend-backend communication

**Endpoints**:
- `POST /api/token`: Generates LiveKit access tokens for frontend
- `POST /upload-pdf`: Accepts PDF uploads, processes them, and stores in Pinecone
- `GET /health`: Health check endpoint
- `GET /storage-status`: Returns Pinecone storage usage and quota status
- `GET /api/indexes`: Lists all Pinecone indexes
- `GET /api/indexes/{index_name}/namespaces`: Lists namespaces in an index
- `GET /api/indexes/{index_name}/stats`: Returns comprehensive index statistics

**PDF Upload Flow**:
1. Frontend uploads PDF file
2. Server validates file type and size (max 10MB)
3. Extracts text and metadata from PDF
4. Chunks text and generates embeddings
5. Stores vectors in Pinecone with appropriate namespace
6. Returns upload confirmation with chunk count and storage status

## Development

### Loading PDFs

Use the script to load PDFs into the vector store:

```bash
python scripts/load_pdf.py data/your-travel-guide.pdf
```

Or upload via the API:

```bash
curl -X POST http://localhost:8000/upload-pdf \
  -F "file=@data/your-travel-guide.pdf"
```

### Testing

Run tests (if available):

```bash
pytest
```

### Debugging

- Check agent logs for STT/TTS errors
- Verify Pinecone index exists and has data
- Test API endpoints with `curl` or Postman
- Check LiveKit Cloud dashboard for connection status

### Common Issues

**Agent not connecting to LiveKit**:
- Verify `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` are set correctly
- Check LiveKit Cloud dashboard for service status

**RAG not working**:
- Verify `PINECONE_API_KEY` is set
- Check that PDFs have been uploaded and indexed
- Verify index name matches `PINECONE_INDEX_NAME`

**Tool errors**:
- Verify API keys are set for tools you want to use
- Check API rate limits and quotas
- Review tool error messages in agent logs

## Dependencies

Key dependencies (see `pyproject.toml` for full list):

- `livekit-agents`: LiveKit agent framework
- `langchain`: Agent orchestration and RAG
- `langchain-openai`: OpenAI integrations
- `langchain-pinecone`: Pinecone vector store
- `pinecone-client`: Pinecone client library
- `pypdf`: PDF text extraction
- `fastapi`: API server framework
- `uvicorn`: ASGI server
- `googlemaps`: Google Places API client
- `requests`: HTTP client for SerpAPI

## See Also

- [Main README](../README.md) - Project overview
- [Frontend README](../frontend/README.md) - Frontend setup
- [Design Document](../DESIGN.md) - System architecture and design decisions

