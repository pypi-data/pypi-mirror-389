# VLMS - Video Intelligence SDK

**Event-based video intelligence with 98% cost reduction**

Multi-source video processing SDK with intelligent frame selection, motion tracking, and VLM-powered analysis. Built for production use with RTSP, ONVIF, UDP, WebRTC, and more coming soon.

> **Note:** `pip install vlm-sdk` installs the SDK components (connectors, preprocessors, providers). The FastAPI service depends on additional packages; install them separately if you plan to run the API.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

---

## 🌟 Features

### Core SDK (`vlm`)
- **🎯 Event-based processing**: Only analyze frames with motion/activity (98% cost reduction vs frame-by-frame)
- **📹 Multi-source connectors**: RTSP, ONVIF, UDP, WebRTC, File
- **🤖 RT-DETR + ByteTrack**: Real-time object detection and motion tracking
- **🧠 Provider-agnostic VLM**: Gemini, Qwen, ObserveeVLM (Small VLM coming soon) (via env config)
- **🎨 Advanced analysis**: Timestamps, object detection, bounding boxes, range queries

### Production API (`api`)
- **⚡ FastAPI REST API**: Industry-standard multi-stream video intelligence
- **📡 Server-Sent Events (SSE)**: Real-time event streaming
- **🔐 Authentication**: API key-based auth with rate limiting
- **📊 Monitoring**: Health checks, metrics, stream management
- **🔧 Configurable**: Environment-based provider selection

---

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install vlm-sdk

# Or install from source
git clone https://github.com/observee-ai/vlm-sdk.git
cd vlm-sdk
pip install -e .
```

### SDK Usage

```python
from vlm.preprocessors import DetectorPreprocessor
from vlm.connectors import RTSPConnector
from vlm.providers.gemini import GeminiVideoService
import asyncio

# Initialize components
connector = RTSPConnector("rtsp://camera.local/stream1")
preprocessor = DetectorPreprocessor(
    confidence_threshold=0.6,
    track_objects=["person", "car"],
    min_duration=2.0  # Only events longer than 2 seconds
)

gemini = GeminiVideoService(api_key="your-gemini-key")

# Process stream
async def process():
    for frame in connector.stream_frames():
        result = preprocessor.process_frame(frame.data, frame.timestamp)

        if result['status'] == 'completed':
            # Event detected! Analyze with VLM
            upload = await gemini.upload_file(result['clip_path'])
            analysis = await gemini.query_video_with_file(
                upload['name'],
                "Describe the activity in this video"
            )
            print(f"Analysis: {analysis['response']}")

asyncio.run(process())
```

### API Server

```bash
# Set environment variables
export ADMIN_API_KEY=your-secret-key
export GEMINI_API_KEY=your-gemini-key
export VLM_PROVIDER=gemini  # or openai, anthropic

# Install SDK (from repo checkout)
pip install -e .

# Install API dependencies (required for running api.main)
pip install fastapi uvicorn[standard] pydantic python-dotenv
# or install everything we ship in Docker
pip install -r requirements.txt

# Run server
python -m api.main

# Server starts at http://localhost:8000
```

> **Note:** To accept WebRTC publishers, run [MediaMTX](https://mediamtx.org) alongside the API using the provided `mediamtx.yml` (see [docs/apiguide.md](docs/apiguide.md) for commands).

### Docker Image

```bash
# Pull the public image (linux/amd64)
docker pull observee/vlm-sdk:latest

# Run the API (set your API keys as needed)
docker run --rm -p 8000:8000 \
  -e ADMIN_API_KEY=your-secret-key \
  -e GEMINI_API_KEY=your-gemini-key \
  observee/vlm-sdk:latest
```

**Create a stream:**

```bash
curl -X POST http://localhost:8000/v1/streams/create \
  -H "X-Admin-API-Key: your-secret-key" \
  -H "X-VLM-API-Key: your-gemini-key" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "rtsp",
    "source_url": "rtsp://camera.local/stream1",
    "config": {
      "username": "admin",
      "password": "password",
      "profile": "security",
      "min_duration": 2.0
    },
    "analysis": {
      "enabled": true,
      "mode": "basic",
      "prompt": "Describe any activity or movement"
    }
  }'
```

**Listen to events (SSE):**

```bash
curl -N http://localhost:8000/v1/streams/{stream_id}/events \
  -H "X-Admin-API-Key: your-secret-key"
```

---

## 📖 Documentation

### Environment Variables

```bash
# Required
ADMIN_API_KEY=your-admin-key              # API authentication

# VLM Provider (choose one)
VLM_PROVIDER=gemini                        # gemini, openai, or anthropic
GEMINI_API_KEY=your-gemini-key            # If using Gemini
OPENAI_API_KEY=your-openai-key            # If using OpenAI
ANTHROPIC_API_KEY=your-anthropic-key      # If using Claude

# Optional: Rate Limiting
RATE_LIMIT_REQUESTS=100                    # Requests per window
RATE_LIMIT_WINDOW=60                       # Time window (seconds)
```

### Analysis Modes

**Basic** - Simple video description
```json
{
  "analysis": {
    "mode": "basic",
    "prompt": "Describe the activity"
  }
}
```

**Timestamps** - Find specific moments
```json
{
  "analysis": {
    "mode": "timestamps",
    "find_timestamps": {
      "query": "when does someone wave",
      "find_all": true,
      "confidence_threshold": 0.7
    }
  }
}
```



### Supported Connectors

| Connector | Description | Config |
|-----------|-------------|--------|
| **RTSP** | IP camera streams | `username`, `password`, `transport` (tcp/udp) |
| **ONVIF** | Auto-discovery + PTZ | `username`, `password`, `profile_index` |
| **UDP** | UDP video receiver | `host`, `port`, `buffer_size` |
| **WebRTC** | Browser streams | `signaling_url`, `ice_servers` |

### API Endpoints

```
POST   /v1/streams/create              Create stream
GET    /v1/streams/{id}/events         SSE event stream
GET    /v1/streams/{id}                Get status
DELETE /v1/streams/{id}                Stop stream
GET    /v1/streams                     List all streams
GET    /v1/streams/discover/onvif      Discover cameras
GET    /v1/streams/health              Health check
```


---

## 🏗️ Architecture

```
┌─────────────┐
│  Connector  │ (RTSP/ONVIF/UDP/WebRTC)
└──────┬──────┘
       │ Frames
       ▼
┌─────────────┐
│    RT-DETR   │ (Object detection + motion tracking)
└──────┬──────┘
       │ Events (only motion/activity)
       ▼
┌─────────────┐
│ Event Buffer│ (Collects frames during events)
└──────┬──────┘
       │ Complete Events
       ├────────────────┐
       │                │
       ▼                ▼
┌───────────┐    ┌──────────┐
│  Storage  │    │    VLM   │ (Gemini/Qwen/ObserveeVLM)
└───────────┘    └────┬─────┘
                      │
                      ▼
              ┌───────────────┐
              │ SSE / Webhooks│
              └───────────────┘
```

**Key Innovation**: Event-based processing analyzes only frames with detected motion/activity, reducing VLM API calls by 98% compared to frame-by-frame analysis.

---

## 📦 Repository Layout

```
vlm-sdk/
├── vlm/                        # Core SDK components
├── api/                        # FastAPI service (routers, services, models)
├── examples/                   # Sample scripts for RTSP/UDP/WebRTC usage
├── docs/                       # Additional documentation
├── mediamtx/                   # MediaMTX config for WebRTC/RTSP bridging
├── output/                     # Example generated clips (safe to remove)
├── pyproject.toml              # SDK packaging metadata
├── requirements.txt            # Full dependency list for API/Docker
├── Dockerfile                  # Reference container for the API
└── README.md
```

---


## 🔧 Development

```bash
# Clone repository
git clone https://github.com/observee-ai/vlm-sdk.git
cd vlm-sdk

# Install with dev dependencies
pip install -e ".[dev]"

# Include API stack if you plan to run the server locally
pip install -r requirements.txt

# Run tests
pytest tests/

# Format code
black vlm/ api/
ruff check vlm/ api/

# Run API server (development)
uvicorn api.main:app --reload
```

---

## 🎯 Use Cases

- **🏢 Security & Surveillance**: 24/7 perimeter monitoring with motion alerts
- **🏪 Retail Analytics**: Customer counting, queue analysis, behavior tracking
- **🚗 Traffic Monitoring**: Vehicle counting, flow analysis, incident detection
- **🏠 Smart Home**: Activity monitoring, intrusion detection
- **🏭 Industrial**: Safety compliance, equipment monitoring

---

## 📊 Cost Comparison

| Approach | Frames/Hour | VLM API Calls | Cost Reduction |
|----------|-------------|---------------|----------------|
| **Frame-by-frame** | 54,000 (15 FPS) | 54,000 | Baseline |
| **Event-based (VLMS)** | 54,000 | ~1,000 | **98%** ✅ |

*Example: 1-hour 15 FPS stream with 5-10 motion events*

---

## 🤝 Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

**Apache-2.0** – Permissive license suitable for commercial and open-source use.

See [LICENSE](LICENSE) for the complete text. Commercial support is available on request.

---

## 🙏 Acknowledgments

- **Ultralytics RT-DETR**: Object detection and tracking
- **FastAPI**: Modern Python web framework
- **Google Gemini**: Video understanding API
- **Qwen API**: Alternative Video Understanding API
- **ByteTrack**: Multi-object tracking algorithm


---

**Built with ❤️ for efficient video intelligence in SF**
